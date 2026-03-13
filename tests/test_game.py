"""
斗地主游戏测试
"""

import unittest
from src.game.card import Card, CardSuit, CardRank, create_standard_deck, sort_cards
from src.game.deck import Deck
from src.game.rules import DoudizhuRules, CardPattern, PlayPattern
from src.game.player import Player, PlayerType, PlayerRole
from src.game.game_state import GameState, GamePhase, GameResult
from src.ai.ai_player import DoudizhuAI


class TestCard(unittest.TestCase):
    """测试卡牌类"""

    def test_card_creation(self):
        """测试卡牌创建"""
        card = Card(CardSuit.SPADE, CardRank.RANK_A)
        self.assertEqual(card.suit, CardSuit.SPADE)
        self.assertEqual(card.rank, CardRank.RANK_A)
        self.assertEqual(str(card), "♠A")

    def test_card_value(self):
        """测试卡牌数值"""
        big_joker = Card(CardSuit.NONE, CardRank.JOKER_BIG)
        small_joker = Card(CardSuit.NONE, CardRank.JOKER_SMALL)
        two = Card(CardSuit.SPADE, CardRank.RANK_2)
        ace = Card(CardSuit.HEART, CardRank.RANK_A)

        self.assertGreater(big_joker.value, small_joker.value)
        self.assertGreater(small_joker.value, two.value)
        self.assertGreater(two.value, ace.value)

    def test_card_comparison(self):
        """测试卡牌比较"""
        card1 = Card(CardSuit.SPADE, CardRank.RANK_2)
        card2 = Card(CardSuit.HEART, CardRank.RANK_3)

        self.assertGreater(card1, card2)
        self.assertLess(card2, card1)

    def test_standard_deck(self):
        """测试标准牌组"""
        deck = create_standard_deck()
        self.assertEqual(len(deck), 54)

        # 检查大小王
        jokers = [c for c in deck if c.is_joker]
        self.assertEqual(len(jokers), 2)


class TestDeck(unittest.TestCase):
    """测试牌组类"""

    def test_deck_creation(self):
        """测试牌组创建"""
        deck = Deck()
        self.assertEqual(deck.remaining, 54)

    def test_shuffle(self):
        """测试洗牌"""
        deck1 = Deck()
        deck1.shuffle(seed=42)

        deck2 = Deck()
        deck2.shuffle(seed=42)

        # 相同种子应该洗出相同顺序
        self.assertEqual(deck1.peek(10), deck2.peek(10))

    def test_deal(self):
        """测试发牌"""
        deck = Deck()
        deck.shuffle()

        cards = deck.deal(5)
        self.assertEqual(len(cards), 5)
        self.assertEqual(deck.remaining, 49)

    def test_deal_for_doudizhu(self):
        """测试斗地主发牌"""
        deck = Deck()
        deck.shuffle()

        p1, p2, p3, bottom = deck.deal_for_doudizhu()

        self.assertEqual(len(p1), 17)
        self.assertEqual(len(p2), 17)
        self.assertEqual(len(p3), 17)
        self.assertEqual(len(bottom), 3)


class TestRules(unittest.TestCase):
    """测试规则类"""

    def setUp(self):
        self.rules = DoudizhuRules()

    def test_single(self):
        """测试单张"""
        card = Card(CardSuit.SPADE, CardRank.RANK_A)
        pattern = self.rules.identify_pattern([card])
        self.assertEqual(pattern.pattern, CardPattern.SINGLE)

    def test_pair(self):
        """测试对子"""
        cards = [
            Card(CardSuit.SPADE, CardRank.RANK_5),
            Card(CardSuit.HEART, CardRank.RANK_5)
        ]
        pattern = self.rules.identify_pattern(cards)
        self.assertEqual(pattern.pattern, CardPattern.PAIR)

    def test_triple(self):
        """测试三张"""
        cards = [
            Card(CardSuit.SPADE, CardRank.RANK_5),
            Card(CardSuit.HEART, CardRank.RANK_5),
            Card(CardSuit.CLUB, CardRank.RANK_5)
        ]
        pattern = self.rules.identify_pattern(cards)
        self.assertEqual(pattern.pattern, CardPattern.TRIPLE)

    def test_bomb(self):
        """测试炸弹"""
        cards = [
            Card(CardSuit.SPADE, CardRank.RANK_5),
            Card(CardSuit.HEART, CardRank.RANK_5),
            Card(CardSuit.CLUB, CardRank.RANK_5),
            Card(CardSuit.DIAMOND, CardRank.RANK_5)
        ]
        pattern = self.rules.identify_pattern(cards)
        self.assertEqual(pattern.pattern, CardPattern.BOMB)

    def test_rocket(self):
        """测试火箭"""
        cards = [
            Card(CardSuit.NONE, CardRank.JOKER_SMALL),
            Card(CardSuit.NONE, CardRank.JOKER_BIG)
        ]
        pattern = self.rules.identify_pattern(cards)
        self.assertEqual(pattern.pattern, CardPattern.ROCKET)

    def test_straight(self):
        """测试顺子"""
        cards = [
            Card(CardSuit.SPADE, CardRank.RANK_3),
            Card(CardSuit.HEART, CardRank.RANK_4),
            Card(CardSuit.CLUB, CardRank.RANK_5),
            Card(CardSuit.DIAMOND, CardRank.RANK_6),
            Card(CardSuit.SPADE, CardRank.RANK_7)
        ]
        pattern = self.rules.identify_pattern(cards)
        self.assertEqual(pattern.pattern, CardPattern.STRAIGHT)

    def test_can_beat(self):
        """测试牌型压制"""
        pattern1 = PlayPattern(CardPattern.SINGLE, [], 50, 1)
        pattern2 = PlayPattern(CardPattern.SINGLE, [], 60, 1)

        self.assertTrue(pattern2.can_beat(pattern1))
        self.assertFalse(pattern1.can_beat(pattern2))

        # 炸弹压单张
        bomb = PlayPattern(CardPattern.BOMB, [], 50, 1)
        single = PlayPattern(CardPattern.SINGLE, [], 100, 1)
        self.assertTrue(bomb.can_beat(single))
        self.assertFalse(single.can_beat(bomb))


class TestPlayer(unittest.TestCase):
    """测试玩家类"""

    def setUp(self):
        self.player = Player(id=0, name="测试玩家")

    def test_add_cards(self):
        """测试添加手牌"""
        cards = [
            Card(CardSuit.SPADE, CardRank.RANK_A),
            Card(CardSuit.HEART, CardRank.RANK_K)
        ]
        self.player.add_cards(cards)
        self.assertEqual(self.player.get_card_count(), 2)

    def test_remove_cards(self):
        """测试移除手牌"""
        cards = [
            Card(CardSuit.SPADE, CardRank.RANK_A),
            Card(CardSuit.HEART, CardRank.RANK_K)
        ]
        self.player.add_cards(cards)
        success = self.player.remove_cards([cards[0]])
        self.assertTrue(success)
        self.assertEqual(self.player.get_card_count(), 1)

    def test_has_cards(self):
        """测试检查手牌"""
        cards = [
            Card(CardSuit.SPADE, CardRank.RANK_A)
        ]
        self.player.add_cards(cards)
        self.assertTrue(self.player.has_cards(cards))

    def test_role(self):
        """测试角色设置"""
        self.player.set_landlord()
        self.assertTrue(self.player.is_landlord())
        self.assertFalse(self.player.is_farmer())

        self.player.set_farmer()
        self.assertTrue(self.player.is_farmer())
        self.assertFalse(self.player.is_landlord())


class TestGameState(unittest.TestCase):
    """测试游戏状态类"""

    def setUp(self):
        self.game = GameState()

    def test_start_game(self):
        """测试开始游戏"""
        self.game.start_new_game(seed=42)

        self.assertEqual(self.game.phase, GamePhase.BIDDING)
        self.assertEqual(len(self.game.players), 3)

        for player in self.game.players:
            self.assertEqual(player.get_card_count(), 17)

    def test_bid(self):
        """测试叫分"""
        self.game.start_new_game(seed=42)
        current_id = self.game.current_player_id

        success = self.game.bid(current_id, 1)
        self.assertTrue(success)
        self.assertEqual(self.game.players[current_id].bid_score, 1)

    def test_play_cards(self):
        """测试出牌"""
        self.game.start_new_game(seed=42)
        # 直接设置地主（跳过叫分）
        self.game._set_landlord(0)

        # 出单张
        player = self.game.players[0]
        card = player.hand[0]
        success, msg = self.game.play_cards(0, [card])
        self.assertTrue(success, msg)


class TestAI(unittest.TestCase):
    """测试AI类"""

    def setUp(self):
        self.game = GameState()
        self.game.start_new_game(seed=42)
        self.ai = DoudizhuAI(self.game.players[1])

    def test_evaluate_hand(self):
        """测试手牌评估"""
        strength = self.ai._evaluate_hand_strength()
        self.assertGreaterEqual(strength, 0)
        self.assertLessEqual(strength, 100)

    def test_make_bid(self):
        """测试叫分决策"""
        bid = self.ai.make_bid(self.game, 0)
        self.assertIn(bid, [0, 1, 2, 3])

    def test_make_decision(self):
        """测试出牌决策"""
        cards = self.ai.make_decision(self.game)
        # 可以是出牌或过牌
        self.assertIsInstance(cards, list)


if __name__ == '__main__':
    unittest.main()
