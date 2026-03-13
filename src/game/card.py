"""
扑克牌定义模块
定义扑克牌的基本属性和操作
"""

from enum import IntEnum
from typing import List, Tuple, Optional
from dataclasses import dataclass


class CardSuit(IntEnum):
    """扑克牌花色"""
    NONE = 0    # 无花色（用于大小王）
    SPADE = 1   # 黑桃 ♠
    HEART = 2   # 红桃 ♥
    CLUB = 3    # 梅花 ♣
    DIAMOND = 4 # 方块 ♦


class CardRank(IntEnum):
    """扑克牌点数"""
    JOKER_SMALL = 0   # 小王
    JOKER_BIG = 1     # 大王
    RANK_2 = 2
    RANK_3 = 3
    RANK_4 = 4
    RANK_5 = 5
    RANK_6 = 6
    RANK_7 = 7
    RANK_8 = 8
    RANK_9 = 9
    RANK_10 = 10
    RANK_J = 11
    RANK_Q = 12
    RANK_K = 13
    RANK_A = 14


# 点数显示映射
RANK_DISPLAY = {
    CardRank.JOKER_SMALL: "小王",
    CardRank.JOKER_BIG: "大王",
    CardRank.RANK_2: "2",
    CardRank.RANK_3: "3",
    CardRank.RANK_4: "4",
    CardRank.RANK_5: "5",
    CardRank.RANK_6: "6",
    CardRank.RANK_7: "7",
    CardRank.RANK_8: "8",
    CardRank.RANK_9: "9",
    CardRank.RANK_10: "10",
    CardRank.RANK_J: "J",
    CardRank.RANK_Q: "Q",
    CardRank.RANK_K: "K",
    CardRank.RANK_A: "A",
}

# 花色显示映射
SUIT_DISPLAY = {
    CardSuit.NONE: "",
    CardSuit.SPADE: "♠",
    CardSuit.HEART: "♥",
    CardSuit.CLUB: "♣",
    CardSuit.DIAMOND: "♦",
}

# 花色颜色（True表示红色，False表示黑色）
SUIT_COLOR = {
    CardSuit.NONE: True,     # 王显示为红色
    CardSuit.SPADE: False,
    CardSuit.HEART: True,
    CardSuit.CLUB: False,
    CardSuit.DIAMOND: True,
}


@dataclass(frozen=True)
class Card:
    """
    扑克牌类
    使用不可变数据类，便于作为字典键使用
    """
    suit: CardSuit
    rank: CardRank

    def __str__(self) -> str:
        """返回牌的字符串表示"""
        return f"{SUIT_DISPLAY[self.suit]}{RANK_DISPLAY[self.rank]}"

    def __repr__(self) -> str:
        return f"Card({self.suit.name}, {self.rank.name})"

    @property
    def is_red(self) -> bool:
        """是否为红色牌"""
        return SUIT_COLOR[self.suit]

    @property
    def is_black(self) -> bool:
        """是否为黑色牌"""
        return not SUIT_COLOR[self.suit]

    @property
    def is_joker(self) -> bool:
        """是否为王牌（大小王）"""
        return self.rank in (CardRank.JOKER_SMALL, CardRank.JOKER_BIG)

    @property
    def value(self) -> int:
        """
        返回牌的数值，用于比较大小
        斗地主中：大王 > 小王 > 2 > A > K > Q > J > 10 > ... > 3
        """
        if self.rank == CardRank.JOKER_BIG:
            return 100
        elif self.rank == CardRank.JOKER_SMALL:
            return 99
        elif self.rank == CardRank.RANK_2:
            return 98
        else:
            return self.rank.value

    def __lt__(self, other: 'Card') -> bool:
        """比较两张牌的大小"""
        if not isinstance(other, Card):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: 'Card') -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: 'Card') -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: 'Card') -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.value >= other.value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self) -> int:
        """使Card可作为字典键"""
        return hash((self.suit, self.rank))

    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """
        从字符串创建卡牌
        格式: "♠A", "小王", "大王" 等
        """
        if card_str == "小王":
            return cls(CardSuit.NONE, CardRank.JOKER_SMALL)
        elif card_str == "大王":
            return cls(CardSuit.NONE, CardRank.JOKER_BIG)

        # 解析花色
        suit_char = card_str[0]
        suit_map = {
            '♠': CardSuit.SPADE,
            '♥': CardSuit.HEART,
            '♣': CardSuit.CLUB,
            '♦': CardSuit.DIAMOND,
        }
        suit = suit_map.get(suit_char, CardSuit.SPADE)

        # 解析点数
        rank_str = card_str[1:]
        rank_map = {
            '2': CardRank.RANK_2, '3': CardRank.RANK_3, '4': CardRank.RANK_4,
            '5': CardRank.RANK_5, '6': CardRank.RANK_6, '7': CardRank.RANK_7,
            '8': CardRank.RANK_8, '9': CardRank.RANK_9, '10': CardRank.RANK_10,
            'J': CardRank.RANK_J, 'Q': CardRank.RANK_Q, 'K': CardRank.RANK_K,
            'A': CardRank.RANK_A,
        }
        rank = rank_map.get(rank_str, CardRank.RANK_3)

        return cls(suit, rank)


def create_standard_deck() -> List[Card]:
    """
    创建一副标准的斗地主牌组（54张）
    包含：52张普通牌 + 2张王牌
    """
    deck = []

    # 添加普通牌（每种花色13张）
    for suit in [CardSuit.SPADE, CardSuit.HEART, CardSuit.CLUB, CardSuit.DIAMOND]:
        for rank in range(CardRank.RANK_3, CardRank.RANK_A + 1):
            deck.append(Card(suit, CardRank(rank)))
        deck.append(Card(suit, CardRank.RANK_2))

    # 添加王牌
    deck.append(Card(CardSuit.NONE, CardRank.JOKER_SMALL))
    deck.append(Card(CardSuit.NONE, CardRank.JOKER_BIG))

    return deck


def sort_cards(cards: List[Card], reverse: bool = True) -> List[Card]:
    """
    对卡牌进行排序

    Args:
        cards: 要排序的卡牌列表
        reverse: 是否降序（默认True，大牌在前）

    Returns:
        排序后的卡牌列表
    """
    return sorted(cards, key=lambda c: c.value, reverse=reverse)


def cards_to_string(cards: List[Card]) -> str:
    """将卡牌列表转换为字符串"""
    return ' '.join(str(card) for card in cards)
