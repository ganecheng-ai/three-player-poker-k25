"""
AI玩家模块
实现斗地主AI的决策逻辑
"""

import random
from typing import List, Optional, Tuple, Dict, Set
from collections import Counter
from enum import IntEnum

from ..game.card import Card, CardRank
from ..game.player import Player
from ..game.rules import DoudizhuRules, PlayPattern, CardPattern
from ..game.game_state import GameState


class AIDifficulty(IntEnum):
    """AI难度级别"""
    EASY = 0
    NORMAL = 1
    HARD = 2


class DoudizhuAI:
    """
    斗地主AI类
    实现AI玩家的出牌决策
    """

    # 牌型优先级（越高越优先保留）
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

    def __init__(self, player: Player, difficulty: AIDifficulty = AIDifficulty.NORMAL):
        """
        初始化AI

        Args:
            player: AI对应的玩家对象
            difficulty: 难度级别 (easy/normal/hard)
        """
        self.player = player
        self.difficulty = difficulty
        self.seen_cards: Set[Card] = set()  # 已见的牌（记忆功能）
        self.played_patterns: List[CardPattern] = []  # 记录已出牌型

    def reset_memory(self) -> None:
        """重置记忆"""
        self.seen_cards.clear()
        self.played_patterns.clear()

    def remember_played_cards(self, cards: List[Card]) -> None:
        """记住已出的牌"""
        self.seen_cards.update(cards)

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

        if not hand:
            return strength

        # 统计各点数牌数量
        rank_counts = Counter(card.value for card in hand)

        # 有王加分
        has_big_joker = False
        has_small_joker = False
        for card in hand:
            if card.rank == CardRank.JOKER_BIG:
                strength += 15
                has_big_joker = True
            elif card.rank == CardRank.JOKER_SMALL:
                strength += 10
                has_small_joker = True

        # 火箭（双王）额外加分
        if has_big_joker and has_small_joker:
            strength += 10

        # 有2加分（每张2加5分）
        num_twos = rank_counts.get(98, 0)  # 2的牌值是98
        strength += 5 * num_twos

        # 有炸弹加分
        bomb_count = 0
        for count in rank_counts.values():
            if count == 4:
                strength += 15
                bomb_count += 1

        # 多个炸弹额外加分
        if bomb_count >= 2:
            strength += 10

        # 有顺子加分（手牌中有连续5张以上）
        sorted_values = sorted(rank_counts.keys())
        straight_length = 1
        max_straight = 1
        for i in range(1, len(sorted_values)):
            if sorted_values[i] - sorted_values[i-1] == 1 and sorted_values[i] < 15:  # 2和王不计入顺子
                straight_length += 1
                max_straight = max(max_straight, straight_length)
            else:
                straight_length = 1
        if max_straight >= 5:
            strength += 5 * (max_straight - 4)

        # 大牌数量加分
        high_cards = sum(1 for card in hand if card.value >= 70)  # 2、王等大牌
        strength += 2 * high_cards

        # 牌型完整性（有对子、三张等组合）
        pairs = sum(1 for count in rank_counts.values() if count >= 2)
        triples = sum(1 for count in rank_counts.values() if count >= 3)
        strength += pairs * 2 + triples * 3

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

        if not candidates:
            return []

        # 过滤掉炸弹和火箭（保留到关键时刻）
        non_bomb_candidates = [
            (cards, pattern) for cards, pattern in candidates
            if pattern.pattern not in (CardPattern.BOMB, CardPattern.ROCKET)
        ]

        if non_bomb_candidates:
            # 策略：优先出难以组合的小牌
            # 1. 分析手牌结构
            hand_analysis = self._analyze_hand_structure(hand)

            # 2. 优先出孤牌（没有对子、三张的牌）
            orphan_cards = hand_analysis.get('orphan_cards', [])
            if orphan_cards:
                # 出最小的孤牌
                smallest_orphan = min(orphan_cards, key=lambda c: c.value)
                return [smallest_orphan]

            # 3. 优先出小牌型的组合
            # 按牌型和牌值排序：先出小牌值，再出简单牌型
            def sort_key(item):
                cards, pattern = item
                # 牌型复杂度（数值越小越简单）
                complexity = self.PATTERN_PRIORITY.get(pattern.pattern, 5)
                # 主要牌值
                main_value = pattern.main_value
                # 卡牌数量（越少越好）
                num_cards = len(cards)
                return (main_value, complexity, num_cards)

            sorted_candidates = sorted(non_bomb_candidates, key=sort_key)

            # 根据难度选择
            if self.difficulty == AIDifficulty.HARD:
                # 困难模式：更智能的选择
                return self._smart_first_play(sorted_candidates, hand_analysis)
            else:
                return sorted_candidates[0][0]

        # 只能出炸弹或火箭
        if candidates:
            # 选择最小的炸弹
            bombs = [(c, p) for c, p in candidates if p.pattern == CardPattern.BOMB]
            if bombs:
                return min(bombs, key=lambda x: x[1].main_value)[0]
            # 出火箭
            rockets = [(c, p) for c, p in candidates if p.pattern == CardPattern.ROCKET]
            if rockets:
                return rockets[0][0]
            return candidates[0][0]

        return []

    def _analyze_hand_structure(self, hand: List[Card]) -> Dict:
        """
        分析手牌结构

        Args:
            hand: 手牌

        Returns:
            手牌结构分析结果
        """
        rank_counts = Counter(card.value for card in hand)

        # 找孤牌（没有对子、三张的牌）
        orphan_cards = [card for card in hand if rank_counts[card.value] == 1]

        # 找对子
        pairs = [[card for card in hand if card.value == rank]
                 for rank, count in rank_counts.items() if count == 2]

        # 找三张
        triples = [[card for card in hand if card.value == rank]
                   for rank, count in rank_counts.items() if count == 3]

        # 找炸弹
        bombs = [[card for card in hand if card.value == rank]
                 for rank, count in rank_counts.items() if count == 4]

        return {
            'orphan_cards': orphan_cards,
            'pairs': pairs,
            'triples': triples,
            'bombs': bombs,
            'rank_counts': rank_counts,
        }

    def _smart_first_play(self, candidates: List[Tuple[List[Card], PlayPattern]],
                          hand_analysis: Dict) -> List[Card]:
        """
        智能选择第一手出牌（困难模式）

        Args:
            candidates: 候选出牌
            hand_analysis: 手牌分析

        Returns:
            选择的牌
        """
        if not candidates:
            return []

        # 策略：优先出能带走的牌（例如三带一中的单牌）
        triples = hand_analysis.get('triples', [])
        orphan_cards = hand_analysis.get('orphan_cards', [])

        # 如果有三张和孤牌，优先出三带一
        if triples and orphan_cards:
            for cards, pattern in candidates:
                if pattern.pattern == CardPattern.TRIPLE_WITH_SINGLE:
                    return cards

        # 如果有多个对子，考虑出连对
        pairs = hand_analysis.get('pairs', [])
        if len(pairs) >= 3:
            # 检查是否有连对
            for cards, pattern in candidates:
                if pattern.pattern == CardPattern.PAIR_STRAIGHT:
                    return cards

        # 默认出最小的牌型
        return candidates[0][0]

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
        last_player_id = game_state.last_play_player_id

        # 获取所有可压过的牌
        candidates = self._generate_all_plays(hand)
        valid_candidates = [
            (cards, pattern) for cards, pattern in candidates
            if pattern.can_beat(last_play)
        ]

        if not valid_candidates:
            return []  # 过牌

        # 策略选择
        # 1. 判断是否是队友出的牌
        is_teammate = False
        if last_player_id is not None:
            last_player = game_state.players[last_player_id]
            if self.player.is_farmer() and last_player.is_farmer():
                is_teammate = True
            elif self.player.is_landlord() and last_player.is_landlord():
                is_teammate = True

        # 2. 如果是队友出的牌且牌不大，考虑过牌让队友继续出
        if is_teammate:
            # 根据难度决定是否压队友的牌
            if self.difficulty == AIDifficulty.EASY:
                # 简单模式：经常放过
                if random.random() < 0.7:
                    return []
            elif self.difficulty == AIDifficulty.NORMAL:
                # 普通模式：有时放过
                if random.random() < 0.5 and last_play.main_value < 60:
                    return []
            else:
                # 困难模式：只有队友出大牌时才放过
                if random.random() < 0.3 and last_play.main_value < 50:
                    return []

        # 3. 排序：按牌值从小到大，优先非炸弹
        def sort_key(item):
            cards, pattern = item
            is_bomb = pattern.pattern in (CardPattern.BOMB, CardPattern.ROCKET)
            return (is_bomb, pattern.main_value, len(cards))

        sorted_candidates = sorted(valid_candidates, key=sort_key)

        # 4. 获取非炸弹选项
        non_bomb = [c for c in sorted_candidates
                    if c[1].pattern not in (CardPattern.BOMB, CardPattern.ROCKET)]

        # 5. 判断是否该压牌
        if non_bomb:
            # 检查对手剩余牌数
            opponent_low_cards = False
            for p in game_state.players:
                if p.id != self.player.id:
                    # 对手牌很少，应该尽量压
                    if (self.player.is_landlord() and p.is_farmer() and p.get_card_count() <= 2) or \
                       (self.player.is_farmer() and p.is_landlord() and p.get_card_count() <= 2):
                        opponent_low_cards = True
                        break

            if opponent_low_cards:
                # 对手快赢了，必须压
                return non_bomb[0][0]

            # 正常情况：选择最小的能压过的牌
            return non_bomb[0][0]

        # 6. 必须使用炸弹时，根据情况决定
        # 如果手牌很少或者对方牌很少，使用炸弹
        if len(hand) <= 5:
            return sorted_candidates[0][0]

        # 对手牌很少，使用炸弹阻止
        for p in game_state.players:
            if p.id != self.player.id and p.get_card_count() <= 2:
                return sorted_candidates[0][0]

        # 否则有一定概率使用炸弹（根据难度）
        bomb_probability = 0.3
        if self.difficulty == AIDifficulty.EASY:
            bomb_probability = 0.2
        elif self.difficulty == AIDifficulty.HARD:
            bomb_probability = 0.5

        if random.random() < bomb_probability:
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

        # 单张
        for card in hand:
            pattern = DoudizhuRules.identify_pattern([card])
            candidates.append(([card], pattern))

        # 对子、三张、炸弹
        rank_groups = {}
        for card in hand:
            rank_groups.setdefault(card.value, []).append(card)

        for rank, cards in rank_groups.items():
            # 对子
            if len(cards) >= 2:
                pattern = DoudizhuRules.identify_pattern(cards[:2])
                candidates.append((cards[:2], pattern))
            # 三张
            if len(cards) >= 3:
                pattern = DoudizhuRules.identify_pattern(cards[:3])
                candidates.append((cards[:3], pattern))
            # 炸弹
            if len(cards) == 4:
                pattern = DoudizhuRules.identify_pattern(cards)
                candidates.append((cards, pattern))

        # 火箭（双王）
        jokers = [c for c in hand if c.rank in (CardRank.JOKER_SMALL, CardRank.JOKER_BIG)]
        if len(jokers) == 2:
            pattern = DoudizhuRules.identify_pattern(jokers)
            candidates.append((jokers, pattern))

        # 顺子（简化版，只检测部分）
        sorted_ranks = sorted(rank_groups.keys())
        for length in range(5, min(len(sorted_ranks) + 1, 13)):
            for start in range(len(sorted_ranks) - length + 1):
                seq = sorted_ranks[start:start + length]
                if seq[-1] - seq[0] == length - 1 and all(r < 15 for r in seq):
                    cards = [rank_groups[r][0] for r in seq]
                    pattern = DoudizhuRules.identify_pattern(cards)
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
