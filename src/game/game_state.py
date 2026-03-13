"""
游戏状态管理模块
管理斗地主游戏的完整流程和状态
"""

import random
from enum import Enum, auto
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field

from .card import Card
from .deck import Deck
from .player import Player, PlayerType, PlayerRole
from .rules import DoudizhuRules, PlayPattern, CardPattern


class GamePhase(Enum):
    """游戏阶段"""
    WAITING = auto()        # 等待开始
    DEALING = auto()        # 发牌中
    BIDDING = auto()        # 叫分阶段
    PLAYING = auto()        # 出牌阶段
    ENDED = auto()          # 游戏结束


class GameResult(Enum):
    """游戏结果"""
    ONGOING = auto()        # 进行中
    LANDLORD_WIN = auto()   # 地主胜利
    FARMERS_WIN = auto()    # 农民胜利


@dataclass
class PlayRecord:
    """出牌记录"""
    player_id: int
    cards: List[Card]
    pattern: PlayPattern
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class GameState:
    """
    游戏状态类
    管理斗地主游戏的完整流程
    """

    def __init__(self, players: Optional[List[Player]] = None):
        """
        初始化游戏状态

        Args:
            players: 玩家列表，如果为None则创建3个AI玩家
        """
        self.deck = Deck()
        self.phase = GamePhase.WAITING
        self.result = GameResult.ONGOING

        # 玩家
        if players is None:
            self.players = [
                Player(id=0, name="玩家", player_type=PlayerType.HUMAN),
                Player(id=1, name="电脑1", player_type=PlayerType.AI),
                Player(id=2, name="电脑2", player_type=PlayerType.AI),
            ]
        else:
            self.players = players

        # 游戏数据
        self.landlord_id: Optional[int] = None
        self.current_player_id: int = 0
        self.bottom_cards: List[Card] = []

        # 出牌记录
        self.play_history: List[PlayRecord] = []
        self.last_play: Optional[PlayPattern] = None
        self.last_play_player_id: Optional[int] = None
        self.consecutive_passes: int = 0

        # 计分
        self.base_score: int = 1
        self.multiple: int = 1

        # 游戏统计
        self.round_count: int = 0

    def start_new_game(self, seed: Optional[int] = None) -> None:
        """
        开始新游戏

        Args:
            seed: 随机种子
        """
        # 重置状态
        self.phase = GamePhase.DEALING
        self.result = GameResult.ONGOING
        self.landlord_id = None
        self.play_history = []
        self.last_play = None
        self.last_play_player_id = None
        self.consecutive_passes = 0
        self.multiple = 1
        self.round_count = 0

        # 重置玩家
        for player in self.players:
            player.reset_for_new_game()

        # 洗牌发牌
        self.deck.reset()
        self.deck.shuffle(seed)

        hands = self.deck.deal_for_doudizhu()
        for i, player in enumerate(self.players):
            player.add_cards(hands[i])
        self.bottom_cards = hands[3]

        # 随机选择第一个叫分的玩家
        self.current_player_id = random.randint(0, 2)
        self.phase = GamePhase.BIDDING

    def bid(self, player_id: int, score: int) -> bool:
        """
        玩家叫分

        Args:
            player_id: 玩家ID
            score: 叫分（0表示不叫，1-3分）

        Returns:
            是否叫分成功
        """
        if self.phase != GamePhase.BIDDING:
            return False
        if player_id != self.current_player_id:
            return False
        if score < 0 or score > 3:
            return False

        player = self.players[player_id]
        player.bid_score = score

        # 如果叫了3分，直接成为地主
        if score == 3:
            self._set_landlord(player_id)
            return True

        # 轮到下一位
        self.current_player_id = (self.current_player_id + 1) % 3

        # 检查叫分是否结束
        if self._is_bidding_complete():
            self._finalize_bidding()

        return True

    def _is_bidding_complete(self) -> bool:
        """检查叫分是否完成"""
        # 所有玩家都叫过分
        if all(p.bid_score >= 0 for p in self.players):
            # 检查是否有人叫分
            max_bid = max(p.bid_score for p in self.players)
            if max_bid == 0:
                # 都没叫，重新发牌
                return True
            # 找到最高叫分者
            return sum(1 for p in self.players if p.bid_score == max_bid) == 1
        return False

    def _finalize_bidding(self) -> None:
        """完成叫分阶段"""
        max_bid = max(p.bid_score for p in self.players)

        if max_bid == 0:
            # 没人叫分，重新发牌
            self.start_new_game()
            return

        # 找到最高叫分者作为地主
        for i, player in enumerate(self.players):
            if player.bid_score == max_bid:
                self._set_landlord(i)
                break

    def _set_landlord(self, player_id: int) -> None:
        """
        设置地主

        Args:
            player_id: 地主玩家ID
        """
        self.landlord_id = player_id
        self.base_score = self.players[player_id].bid_score

        # 设置角色
        for i, player in enumerate(self.players):
            if i == player_id:
                player.set_landlord()
                # 地主获得底牌
                player.add_cards(self.bottom_cards)
            else:
                player.set_farmer()

        # 游戏进入出牌阶段，地主先出
        self.phase = GamePhase.PLAYING
        self.current_player_id = player_id

    def play_cards(self, player_id: int, cards: List[Card]) -> Tuple[bool, str]:
        """
        玩家出牌

        Args:
            player_id: 玩家ID
            cards: 出的牌

        Returns:
            (是否成功, 错误信息)
        """
        if self.phase != GamePhase.PLAYING:
            return False, "游戏不在出牌阶段"

        if player_id != self.current_player_id:
            return False, "不是该玩家的回合"

        player = self.players[player_id]

        # 检查是否过牌
        if not cards:
            return self._pass_turn(player_id)

        # 检查手牌
        if not player.has_cards(cards):
            return False, "手牌中没有这些牌"

        # 检查牌型
        pattern = DoudizhuRules.identify_pattern(cards)
        if pattern.pattern == CardPattern.INVALID:
            return False, "无效的牌型"

        # 检查是否能压过上家
        if self.last_play and self.last_play_player_id != player_id:
            if not pattern.can_beat(self.last_play):
                return False, "无法压过上家的牌"

        # 执行出牌
        player.remove_cards(cards)
        self.last_play = pattern
        self.last_play_player_id = player_id
        self.consecutive_passes = 0

        # 记录出牌
        record = PlayRecord(player_id, cards, pattern)
        self.play_history.append(record)

        # 检查炸弹和火箭，加倍
        if pattern.pattern in (CardPattern.BOMB, CardPattern.ROCKET):
            self.multiple *= 2

        # 检查游戏结束
        if player.is_empty():
            self._end_game(player_id)
            return True, ""

        # 轮到下一位
        self.current_player_id = (self.current_player_id + 1) % 3

        return True, ""

    def _pass_turn(self, player_id: int) -> Tuple[bool, str]:
        """
        玩家过牌

        Args:
            player_id: 玩家ID

        Returns:
            (是否成功, 错误信息)
        """
        # 第一手不能过
        if self.last_play is None or self.last_play_player_id == player_id:
            return False, "第一手不能过牌"

        self.consecutive_passes += 1

        # 如果连续两人过牌，新一轮开始
        if self.consecutive_passes >= 2:
            self.last_play = None
            self.last_play_player_id = None
            self.consecutive_passes = 0
            self.round_count += 1

        # 轮到下一位
        self.current_player_id = (self.current_player_id + 1) % 3

        return True, "过牌"

    def _end_game(self, winner_id: int) -> None:
        """
        结束游戏

        Args:
            winner_id: 获胜玩家ID
        """
        self.phase = GamePhase.ENDED

        winner = self.players[winner_id]

        # 计算得分
        score = self.base_score * self.multiple

        if winner.is_landlord():
            self.result = GameResult.LANDLORD_WIN
            # 地主胜利，获得2倍农民的基础分
            winner.add_score(score * 2)
            for player in self.players:
                if player.is_farmer():
                    player.add_score(-score)
        else:
            self.result = GameResult.FARMERS_WIN
            # 农民胜利，地主支付2倍
            for player in self.players:
                if player.is_landlord():
                    player.add_score(-score * 2)
                else:
                    player.add_score(score)

        # 更新胜负统计
        for player in self.players:
            if (player.is_landlord() and self.result == GameResult.LANDLORD_WIN) or \
               (player.is_farmer() and self.result == GameResult.FARMERS_WIN):
                player.win_game()
            else:
                player.lose_game()

    def get_current_player(self) -> Player:
        """获取当前玩家"""
        return self.players[self.current_player_id]

    def get_landlord(self) -> Optional[Player]:
        """获取地主玩家"""
        if self.landlord_id is not None:
            return self.players[self.landlord_id]
        return None

    def get_valid_plays(self, player_id: int) -> List[List[Card]]:
        """
        获取玩家所有可出的牌组合

        Args:
            player_id: 玩家ID

        Returns:
            可出的牌组合列表
        """
        player = self.players[player_id]
        valid_plays = []

        # 过牌选项
        if self.last_play and self.last_play_player_id != player_id:
            valid_plays.append([])

        # 这里需要更复杂的逻辑来找出所有可出的牌型
        # 简化处理：暂时只返回一些基本组合
        hand = player.hand

        # 遍历所有可能的出牌组合（实际游戏中需要优化）
        # 这里提供一个简化的版本
        if self.last_play is None or self.last_play_player_id == player_id:
            # 任意出
            for card in hand:
                valid_plays.append([card])
        else:
            # 需要压过
            for card in hand:
                pattern = DoudizhuRules.identify_pattern([card])
                if pattern.can_beat(self.last_play):
                    valid_plays.append([card])

        return valid_plays

    def is_game_over(self) -> bool:
        """游戏是否结束"""
        return self.phase == GamePhase.ENDED

    def get_game_result(self) -> Dict:
        """
        获取游戏结果

        Returns:
            游戏结果字典
        """
        return {
            'result': self.result,
            'landlord_id': self.landlord_id,
            'scores': {p.id: p.score for p in self.players},
            'final_hands': {p.id: len(p.hand) for p in self.players},
        }
