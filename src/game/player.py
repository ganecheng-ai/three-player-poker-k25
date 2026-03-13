"""
玩家模块
定义玩家类和玩家类型
"""

from enum import Enum, auto
from typing import List, Optional, Set
from dataclasses import dataclass, field
from .card import Card, sort_cards
from .rules import PlayPattern


class PlayerType(Enum):
    """玩家类型"""
    HUMAN = auto()    # 人类玩家
    AI = auto()       # AI玩家


class PlayerRole(Enum):
    """玩家角色"""
    UNKNOWN = auto()  # 未知
    FARMER = auto()   # 农民
    LANDLORD = auto() # 地主


@dataclass
class Player:
    """
    玩家类
    管理玩家的手牌、角色、分数等信息
    """

    # 基础属性
    id: int                          # 玩家ID (0, 1, 2)
    name: str                        # 玩家名称
    player_type: PlayerType = PlayerType.HUMAN
    role: PlayerRole = PlayerRole.UNKNOWN

    # 游戏状态
    hand: List[Card] = field(default_factory=list)  # 手牌
    score: int = 0                   # 当前得分
    total_score: int = 0             # 累计得分

    # 叫地主相关
    bid_score: int = 0               # 叫分（0表示不叫）

    # 统计数据
    games_played: int = 0            # 游戏场次
    games_won: int = 0               # 获胜场次

    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            self.name = f"玩家{self.id + 1}"

    def add_cards(self, cards: List[Card]) -> None:
        """
        添加手牌

        Args:
            cards: 要添加的牌
        """
        self.hand.extend(cards)
        self.hand = sort_cards(self.hand)

    def remove_cards(self, cards: List[Card]) -> bool:
        """
        移除手牌

        Args:
            cards: 要移除的牌

        Returns:
            是否成功移除
        """
        hand_set = set((c.suit, c.rank) for c in self.hand)
        for card in cards:
            if (card.suit, card.rank) not in hand_set:
                return False

        # 移除牌
        new_hand = []
        remove_set = {(c.suit, c.rank) for c in cards}
        for card in self.hand:
            if (card.suit, card.rank) not in remove_set:
                new_hand.append(card)
            else:
                remove_set.remove((card.suit, card.rank))

        self.hand = new_hand
        return True

    def has_cards(self, cards: List[Card]) -> bool:
        """
        检查是否拥有指定牌

        Args:
            cards: 要检查的牌

        Returns:
            是否全部拥有
        """
        hand_counter = {}
        for card in self.hand:
            key = (card.suit, card.rank)
            hand_counter[key] = hand_counter.get(key, 0) + 1

        for card in cards:
            key = (card.suit, card.rank)
            if hand_counter.get(key, 0) == 0:
                return False
            hand_counter[key] -= 1

        return True

    def get_card_count(self) -> int:
        """获取手牌数量"""
        return len(self.hand)

    def is_empty(self) -> bool:
        """检查手牌是否出完"""
        return len(self.hand) == 0

    def clear_hand(self) -> None:
        """清空手牌"""
        self.hand = []

    def reset_for_new_game(self) -> None:
        """重置为新游戏状态"""
        self.hand = []
        self.role = PlayerRole.UNKNOWN
        self.bid_score = 0
        self.score = 0

    def set_landlord(self) -> None:
        """设置为地主"""
        self.role = PlayerRole.LANDLORD

    def set_farmer(self) -> None:
        """设置为农民"""
        self.role = PlayerRole.FARMER

    def is_landlord(self) -> bool:
        """是否为地主"""
        return self.role == PlayerRole.LANDLORD

    def is_farmer(self) -> bool:
        """是否为农民"""
        return self.role == PlayerRole.FARMER

    def add_score(self, points: int) -> None:
        """
        增加得分

        Args:
            points: 分数（可为负数）
        """
        self.score += points
        self.total_score += points

    def win_game(self) -> None:
        """记录获胜"""
        self.games_played += 1
        self.games_won += 1

    def lose_game(self) -> None:
        """记录失败"""
        self.games_played += 1

    def get_win_rate(self) -> float:
        """
        获取胜率

        Returns:
            胜率（0.0-1.0）
        """
        if self.games_played == 0:
            return 0.0
        return self.games_won / self.games_played

    def can_play(self, pattern: PlayPattern) -> bool:
        """
        检查是否能打出指定牌型（手牌中是否有足够牌）

        Args:
            pattern: 要打的牌型

        Returns:
            是否能打出
        """
        # 实际判断需要在游戏逻辑中根据pattern详细检查
        return len(self.hand) >= len(pattern.cards)

    def __str__(self) -> str:
        role_str = "地主" if self.is_landlord() else "农民" if self.is_farmer() else "未知"
        return f"{self.name}({role_str}, {len(self.hand)}张牌)"

    def __repr__(self) -> str:
        return f"Player(id={self.id}, name={self.name}, role={self.role.name})"
