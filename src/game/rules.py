"""
斗地主规则模块
定义斗地主游戏中的牌型、规则和比较逻辑
"""

from enum import Enum, auto
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
from .card import Card, CardRank


class CardPattern(Enum):
    """牌型枚举"""
    INVALID = auto()           # 无效牌型
    PASS = auto()              # 不出/过
    SINGLE = auto()            # 单张
    PAIR = auto()              # 对子
    TRIPLE = auto()            # 三张
    TRIPLE_WITH_SINGLE = auto() # 三带一
    TRIPLE_WITH_PAIR = auto()   # 三带二
    STRAIGHT = auto()           # 顺子（5张及以上连续单牌）
    PAIR_STRAIGHT = auto()      # 连对（3对及以上连续对子）
    TRIPLE_STRAIGHT = auto()    # 飞机（2组及以上连续三张）
    TRIPLE_STRAIGHT_WITH_SINGLES = auto()  # 飞机带翅膀（单）
    TRIPLE_STRAIGHT_WITH_PAIRS = auto()    # 飞机带翅膀（对）
    FOUR_WITH_TWO_SINGLES = auto()         # 四带二（单）
    FOUR_WITH_TWO_PAIRS = auto()           # 四带二（对）
    BOMB = auto()              # 炸弹（四张相同）
    ROCKET = auto()            # 火箭（双王）


class PlayPattern:
    """
    出牌模式类
    表示一次出牌的牌型和相关信息
    """

    def __init__(self, pattern: CardPattern, cards: List[Card],
                 main_value: int = 0, length: int = 0):
        """
        初始化出牌模式

        Args:
            pattern: 牌型
            cards: 出的牌
            main_value: 主牌值（用于比较大小）
            length: 牌型长度（用于顺子等）
        """
        self.pattern = pattern
        self.cards = cards.copy()
        self.main_value = main_value
        self.length = length

    def __repr__(self) -> str:
        return f"PlayPattern({self.pattern.name}, {len(self.cards)} cards, value={self.main_value})"

    def can_beat(self, other: 'PlayPattern') -> bool:
        """
        判断当前牌型是否能压过另一牌型

        Args:
            other: 要比较的牌型

        Returns:
            是否能压过
        """
        # 火箭最大
        if self.pattern == CardPattern.ROCKET:
            return True
        if other.pattern == CardPattern.ROCKET:
            return False

        # 炸弹可以压过非炸弹牌型
        if self.pattern == CardPattern.BOMB:
            if other.pattern != CardPattern.BOMB:
                return True
            # 炸弹之间比较大小
            return self.main_value > other.main_value

        # 非炸弹不能压过炸弹
        if other.pattern == CardPattern.BOMB:
            return False

        # 同类型牌型比较
        if self.pattern != other.pattern:
            return False
        if self.length != other.length:
            return False

        return self.main_value > other.main_value


class DoudizhuRules:
    """
    斗地主规则类
    提供牌型判断、大小比较等功能
    """

    @staticmethod
    def identify_pattern(cards: List[Card]) -> PlayPattern:
        """
        识别牌型

        Args:
            cards: 要识别的牌列表

        Returns:
            出牌模式对象
        """
        if not cards:
            return PlayPattern(CardPattern.PASS, [])

        n = len(cards)

        # 统计各点数的牌数量
        rank_counts: Dict[int, int] = Counter(card.value for card in cards)
        unique_ranks = sorted(rank_counts.keys(), reverse=True)

        # 火箭（双王）
        if n == 2:
            ranks = [card.rank for card in cards]
            if CardRank.JOKER_SMALL in ranks and CardRank.JOKER_BIG in ranks:
                return PlayPattern(CardPattern.ROCKET, cards, 100, 1)

        # 单张
        if n == 1:
            return PlayPattern(CardPattern.SINGLE, cards, cards[0].value, 1)

        # 对子
        if n == 2 and len(unique_ranks) == 1:
            return PlayPattern(CardPattern.PAIR, cards, unique_ranks[0], 1)

        # 三张
        if n == 3 and len(unique_ranks) == 1:
            return PlayPattern(CardPattern.TRIPLE, cards, unique_ranks[0], 1)

        # 三带一
        if n == 4:
            counts = sorted(rank_counts.values())
            if counts == [1, 3]:
                main_val = [v for v, c in rank_counts.items() if c == 3][0]
                return PlayPattern(CardPattern.TRIPLE_WITH_SINGLE, cards, main_val, 1)

        # 三带二
        if n == 5:
            counts = sorted(rank_counts.values())
            if counts == [2, 3]:
                main_val = [v for v, c in rank_counts.items() if c == 3][0]
                return PlayPattern(CardPattern.TRIPLE_WITH_PAIR, cards, main_val, 1)

        # 炸弹
        if n == 4 and len(unique_ranks) == 1:
            return PlayPattern(CardPattern.BOMB, cards, unique_ranks[0], 1)

        # 四带二
        if n == 6:
            counts = sorted(rank_counts.values())
            if 4 in counts:
                main_val = [v for v, c in rank_counts.items() if c == 4][0]
                if counts == [1, 1, 4]:
                    return PlayPattern(CardPattern.FOUR_WITH_TWO_SINGLES, cards, main_val, 1)

        if n == 8:
            counts = sorted(rank_counts.values())
            if counts == [2, 2, 4]:
                main_val = [v for v, c in rank_counts.items() if c == 4][0]
                return PlayPattern(CardPattern.FOUR_WITH_TWO_PAIRS, cards, main_val, 1)

        # 顺子（5张及以上连续单牌）
        if n >= 5:
            # 顺子不能包含2和王
            if all(v < 15 for v in unique_ranks) and len(unique_ranks) == n:
                if max(unique_ranks) - min(unique_ranks) == n - 1:
                    return PlayPattern(CardPattern.STRAIGHT, cards, max(unique_ranks), n)

        # 连对（3对及以上连续对子）
        if n >= 6 and n % 2 == 0:
            pair_count = n // 2
            if all(c == 2 for c in rank_counts.values()):
                if all(v < 15 for v in unique_ranks) and len(unique_ranks) == pair_count:
                    if max(unique_ranks) - min(unique_ranks) == pair_count - 1:
                        return PlayPattern(CardPattern.PAIR_STRAIGHT, cards, max(unique_ranks), pair_count)

        # 飞机（连续三张）
        if n >= 6 and n % 3 == 0:
            triple_count = n // 3
            if all(c == 3 for c in rank_counts.values()):
                if all(v < 15 for v in unique_ranks) and len(unique_ranks) == triple_count:
                    if max(unique_ranks) - min(unique_ranks) == triple_count - 1:
                        return PlayPattern(CardPattern.TRIPLE_STRAIGHT, cards, max(unique_ranks), triple_count)

        # 飞机带翅膀（单牌）
        if n >= 8:
            triple_values = [v for v, c in rank_counts.items() if c == 3]
            if len(triple_values) >= 2:
                triple_values.sort(reverse=True)
                # 检查连续
                for length in range(len(triple_values), 1, -1):
                    for start in range(len(triple_values) - length + 1):
                        seq = triple_values[start:start+length]
                        if max(seq) - min(seq) == length - 1 and all(v < 15 for v in seq):
                            # 检查翅膀数量
                            wing_count = n - length * 3
                            if wing_count == length:
                                return PlayPattern(CardPattern.TRIPLE_STRAIGHT_WITH_SINGLES,
                                                   cards, max(seq), length)

        # 飞机带翅膀（对子）
        if n >= 10 and n % 5 == 0:
            triple_values = [v for v, c in rank_counts.items() if c == 3]
            pair_values = [v for v, c in rank_counts.items() if c == 2]
            if len(triple_values) >= 2:
                triple_values.sort(reverse=True)
                for length in range(len(triple_values), 1, -1):
                    for start in range(len(triple_values) - length + 1):
                        seq = triple_values[start:start+length]
                        if max(seq) - min(seq) == length - 1 and all(v < 15 for v in seq):
                            if len(pair_values) == length:
                                return PlayPattern(CardPattern.TRIPLE_STRAIGHT_WITH_PAIRS,
                                                   cards, max(seq), length)

        return PlayPattern(CardPattern.INVALID, cards, 0, 0)

    @staticmethod
    def is_valid_play(cards: List[Card], last_play: Optional[PlayPattern] = None) -> bool:
        """
        判断出牌是否有效

        Args:
            cards: 要出的牌
            last_play: 上一次出牌（None表示任意出）

        Returns:
            是否有效
        """
        pattern = DoudizhuRules.identify_pattern(cards)

        # 无效牌型
        if pattern.pattern == CardPattern.INVALID:
            return False

        # 第一次出牌或新一轮
        if last_play is None or last_play.pattern == CardPattern.PASS:
            return pattern.pattern != CardPattern.PASS

        # 比较牌型
        return pattern.can_beat(last_play)

    @staticmethod
    def get_card_value(card: Card) -> int:
        """获取牌值（用于排序和比较）"""
        return card.value

    @staticmethod
    def sort_by_frequency(cards: List[Card]) -> List[Card]:
        """
        按点数频率排序（频率高的在前，便于找三带、飞机等）

        Args:
            cards: 手牌

        Returns:
            排序后的牌
        """
        rank_counts: Dict[int, int] = Counter(card.value for card in cards)
        return sorted(cards, key=lambda c: (rank_counts[c.value], c.value), reverse=True)
