"""
牌组管理模块
管理扑克牌组的洗牌、发牌等操作
"""

import random
from typing import List, Optional, Tuple
from .card import Card, create_standard_deck, sort_cards


class Deck:
    """
    牌组类
    管理一副扑克牌的生命周期
    """

    def __init__(self):
        """初始化牌组"""
        self._cards: List[Card] = []
        self._dealt_cards: List[Card] = []
        self.reset()

    def reset(self) -> None:
        """重置牌组为初始状态"""
        self._cards = create_standard_deck()
        self._dealt_cards = []

    def shuffle(self, seed: Optional[int] = None) -> None:
        """
        洗牌

        Args:
            seed: 随机种子，用于可重现的洗牌结果
        """
        if seed is not None:
            random.seed(seed)
        random.shuffle(self._cards)

    def deal(self, num_cards: int = 1) -> List[Card]:
        """
        从牌堆顶部发牌

        Args:
            num_cards: 要发的牌数

        Returns:
            发出的牌列表

        Raises:
            ValueError: 牌堆剩余牌不足
        """
        if num_cards > len(self._cards):
            raise ValueError(f"牌堆剩余牌不足，需要{num_cards}张，剩余{len(self._cards)}张")

        dealt = self._cards[-num_cards:]
        self._cards = self._cards[:-num_cards]
        self._dealt_cards.extend(dealt)
        return dealt

    def deal_one(self) -> Optional[Card]:
        """
        发一张牌

        Returns:
            发出的牌，如果牌堆为空则返回None
        """
        if not self._cards:
            return None
        card = self._cards.pop()
        self._dealt_cards.append(card)
        return card

    def deal_for_doudizhu(self) -> Tuple[List[Card], List[Card], List[Card], List[Card]]:
        """
        斗地主发牌
        每人17张，留3张作为底牌

        Returns:
            (玩家1手牌, 玩家2手牌, 玩家3手牌, 底牌)
        """
        player1 = self.deal(17)
        player2 = self.deal(17)
        player3 = self.deal(17)
        bottom = self._cards.copy()  # 剩余3张
        self._cards = []
        self._dealt_cards.extend(bottom)

        # 对每个玩家的牌进行排序
        return (
            sort_cards(player1),
            sort_cards(player2),
            sort_cards(player3),
            sort_cards(bottom)
        )

    @property
    def remaining(self) -> int:
        """返回牌堆剩余牌数"""
        return len(self._cards)

    @property
    def is_empty(self) -> bool:
        """牌堆是否为空"""
        return len(self._cards) == 0

    def peek(self, num_cards: int = 1) -> List[Card]:
        """
        查看牌堆顶部的牌（不发出）

        Args:
            num_cards: 查看的牌数

        Returns:
            顶部牌的列表
        """
        return self._cards[-num_cards:]

    def return_cards(self, cards: List[Card]) -> None:
        """
        将牌返回牌堆（放入底部）

        Args:
            cards: 要返回的牌
        """
        self._cards = cards + self._cards
        for card in cards:
            if card in self._dealt_cards:
                self._dealt_cards.remove(card)

    def get_all_cards(self) -> List[Card]:
        """获取当前牌堆所有牌"""
        return self._cards.copy()
