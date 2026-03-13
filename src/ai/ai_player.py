"""
AI玩家模块
实现斗地主AI的决策逻辑
"""

import random
from typing import List, Optional, Tuple
from collections import Counter

from ..game.card import Card, CardRank
from ..game.player import Player
from ..game.rules import DoudizhuRules, PlayPattern, CardPattern
from ..game.game_state import GameState


class DoudizhuAI:
    """
    斗地主AI类
    实现AI玩家的出牌决策
    """

    # 牌型优先级（越高越优先出）
    PATTERN_PRIORITY = {
        CardPattern.SINGLE: 1,
        CardPattern.PAIR: 2,
        CardPattern.TRIPLE: 3,
        CardPattern.TRIPLE_WITH_SINGLE: 4,
        CardPattern.TRIPLE_WITH_PAIR: 5,
        CardPattern.STRAIGHT: 6,
        CardPattern.PAIR_STRAIGHT: 7,
        CardPattern.TRIPLE_STRAIGHT: 8,
        CardPattern.BOMB: 10,
        CardPattern.ROCKET: 11,
    }

    def __init__(self, player: Player, difficulty: str = "normal"):
        """
        初始化AI

        Args:
            player: AI对应的玩家对象
            difficulty: 难度级别 (easy/normal/hard)
        """
        self.player = player
        self.difficulty = difficulty

    def make_decision(self, game_state: GameState) -> List[Card]:
        """
        做出出牌决策

        Args:
            game_state: 当前游戏状态

        Returns:
            要出的牌列表，空列表表示过牌
        """
        last_play = game_state.last_play
        last_player_id = game_state.last_play_player_id

        # 第一手或自己是上一手出牌者
        if last_play is None or last_player_id == self.player.id:
            return self._choose_first_play(game_state)

        # 需要压过别人的牌
        return self._choose_response(game_state, last_play)

    def make_bid(self, game_state: GameState, current_max_bid: int) -> int:
        """
        做出叫分决策

        Args:
            game_state: 当前游戏状态
            current_max_bid: 当前最高叫分

        Returns:
            叫分（0表示不叫）
        """
        # 评估手牌强度
        strength = self._evaluate_hand_strength()

        # 根据手牌强度决定叫分
        if strength >= 90 and current_max_bid < 3:
            return 3
        elif strength >= 70 and current_max_bid < 2:
            return 2
        elif strength >= 50 and current_max_bid < 1:
            return 1

        # 随机叫分（增加变化）
        if random.random() < 0.2 and current_max_bid < 1:
            return 1

        return 0

    def _evaluate_hand_strength(self) -> int:
        """
        评估手牌强度（0-100）

        Returns:
            手牌强度分数
        """
        strength = 30  # 基础分
        hand = self.player.hand

        # 统计各点数牌数量
        rank_counts = Counter(card.value for card in hand)

        # 有王加分
        for card in hand:
            if card.rank == CardRank.JOKER_BIG:
                strength += 15
            elif card.rank == CardRank.JOKER_SMALL:
                strength += 10

        # 有2加分
        if CardRank.RANK_2 in [card.rank for card in hand]:
            strength += 5 * rank_counts.get(98, 0)

        # 有炸弹加分
        for count in rank_counts.values():
            if count == 4:
                strength += 10

        # 牌型连贯性加分
        if len(hand) >= 17:  # 初始手牌
            strength += 5

        return min(strength, 100)

    def _choose_first_play(self, game_state: GameState) -> List[Card]:
        """
        选择第一手出牌

        Args:
            game_state: 当前游戏状态

        Returns:
            要出的牌
        """
        hand = self.player.hand

        # 获取所有可能的出牌组合
        candidates = self._generate_all_plays(hand)

        # 过滤掉炸弹和火箭（保留到关键时刻）
        non_bomb_candidates = [
            (cards, pattern) for cards, pattern in candidates
            if pattern.pattern not in (CardPattern.BOMB, CardPattern.ROCKET)
        ]

        if non_bomb_candidates:
            # 优先出小牌和简单牌型
            # 按牌数和牌值排序
            sorted_candidates = sorted(
                non_bomb_candidates,
                key=lambda x: (len(x[0]), x[1].main_value)
            )
            return sorted_candidates[0][0]

        # 只能出炸弹或火箭
        if candidates:
            return candidates[0][0]

        return []

    def _choose_response(self, game_state: GameState, last_play: PlayPattern) -> List[Card]:
        """
        选择回应出牌

        Args:
            game_state: 当前游戏状态
            last_play: 上家的出牌

        Returns:
            要出的牌，空列表表示过牌
        """
        hand = self.player.hand

        # 获取所有可压过的牌
        candidates = self._generate_all_plays(hand)
        valid_candidates = [
            (cards, pattern) for cards, pattern in candidates
            if pattern.can_beat(last_play)
        ]

        if not valid_candidates:
            return []  # 过牌

        # 策略选择
        # 1. 如果是队友出的牌，尽量过
        last_player_id = game_state.last_play_player_id
        if last_player_id is not None:
            last_player = game_state.players[last_player_id]
            # 简化：随机选择是否过牌（如果是队友）
            if self.player.is_farmer() and last_player.is_farmer():
                if random.random() < 0.5:
                    return []
            elif self.player.is_landlord() and last_player.is_landlord():
                if random.random() < 0.5:
                    return []

        # 2. 选择最小的能压过的牌
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda x: (x[1].main_value, len(x[0]))
        )

        # 优先非炸弹
        non_bomb = [c for c in sorted_candidates
                    if c[1].pattern not in (CardPattern.BOMB, CardPattern.ROCKET)]

        if non_bomb:
            return non_bomb[0][0]

        # 必须使用炸弹时，根据情况决定
        # 如果手牌很少或者对方牌很少，使用炸弹
        if len(hand) <= 5:
            return sorted_candidates[0][0]

        # 否则有一定概率使用炸弹
        if random.random() < 0.3:
            return sorted_candidates[0][0]

        return []

    def _generate_all_plays(self, hand: List[Card]) -> List[Tuple[List[Card], PlayPattern]]:
        """
        生成所有可能的出牌组合

        Args:
            hand: 手牌

        Returns:
            (牌列表, 牌型)的列表
        """
        candidates = []
        rules = DoudizhuRules()

        # 单张
        for card in hand:
            pattern = rules.identify_pattern([card])
            candidates.append(([card], pattern))

        # 对子、三张、炸弹
        rank_groups = {}
        for card in hand:
            rank_groups.setdefault(card.value, []).append(card)

        for rank, cards in rank_groups.items():
            # 对子
            if len(cards) >= 2:
                pattern = rules.identify_pattern(cards[:2])
                candidates.append((cards[:2], pattern))
            # 三张
            if len(cards) >= 3:
                pattern = rules.identify_pattern(cards[:3])
                candidates.append((cards[:3], pattern))
            # 炸弹
            if len(cards) == 4:
                pattern = rules.identify_pattern(cards)
                candidates.append((cards, pattern))

        # 火箭（双王）
        jokers = [c for c in hand if c.rank in (CardRank.JOKER_SMALL, CardRank.JOKER_BIG)]
        if len(jokers) == 2:
            pattern = rules.identify_pattern(jokers)
            candidates.append((jokers, pattern))

        # 顺子（简化版，只检测部分）
        sorted_ranks = sorted(rank_groups.keys())
        for length in range(5, min(len(sorted_ranks) + 1, 13)):
            for start in range(len(sorted_ranks) - length + 1):
                seq = sorted_ranks[start:start + length]
                if seq[-1] - seq[0] == length - 1 and all(r < 15 for r in seq):
                    cards = [rank_groups[r][0] for r in seq]
                    pattern = rules.identify_pattern(cards)
                    if pattern.pattern == CardPattern.STRAIGHT:
                        candidates.append((cards, pattern))

        return candidates

    def _should_use_bomb(self, game_state: GameState) -> bool:
        """
        判断是否该使用炸弹

        Args:
            game_state: 当前游戏状态

        Returns:
            是否使用炸弹
        """
        # 如果自己是地主且农民牌很少，使用炸弹
        if self.player.is_landlord():
            for p in game_state.players:
                if p.is_farmer() and p.get_card_count() <= 2:
                    return True

        # 如果自己是农民且地打牌很少，使用炸弹
        if self.player.is_farmer():
            landlord = game_state.get_landlord()
            if landlord and landlord.get_card_count() <= 2:
                return True

        return False
