"""
游戏窗口模块
使用Pygame实现斗地主游戏界面
"""

import pygame
import sys
import os
from typing import List, Optional, Tuple, Callable, Dict
from pathlib import Path

from ..game.card import Card, CardSuit, SUIT_COLOR, RANK_DISPLAY, SUIT_DISPLAY
from ..game.player import Player, PlayerRole, PlayerType
from ..game.game_state import GameState, GamePhase, GameResult
from ..game.rules import CardPattern
from ..ai.ai_player import DoudizhuAI, AIDifficulty
from ..utils import setup_logger, get_sound_manager
from .animation import AnimationManager

# 初始化日志
logger = setup_logger()

# 颜色定义
COLORS = {
    'background': (34, 139, 34),      # 深绿色背景（桌布）
    'table': (0, 100, 0),              # 桌子颜色
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'red': (255, 0, 0),
    'gold': (255, 215, 0),
    'gray': (128, 128, 128),
    'light_gray': (200, 200, 200),
    'dark_gray': (64, 64, 64),
    'blue': (0, 0, 255),
    'button': (70, 130, 180),          # 钢青色按钮
    'button_hover': (100, 149, 237),   # 浅钢青色
    'button_active': (50, 100, 150),   # 深钢青色
    'card_back': (100, 50, 150),       # 牌背颜色
    'card_front': (255, 255, 255),     # 牌面颜色
    'selected': (255, 255, 0, 128),    # 选中效果
}

# 界面常量
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_CORNER_RADIUS = 8
CARD_SPACING = 30  # 手牌间距
CARD_SPACING_VERTICAL = 20  # 垂直间距

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

FONT_SIZE_SMALL = 18
FONT_SIZE_NORMAL = 24
FONT_SIZE_LARGE = 32
FONT_SIZE_TITLE = 48


class Button:
    """按钮类"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, callback: Callable, font_size: int = FONT_SIZE_NORMAL):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.font_size = font_size
        self.hovered = False
        self.active = True

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """绘制按钮"""
        if not self.active:
            color = COLORS['gray']
        elif self.hovered:
            color = COLORS['button_hover']
        else:
            color = COLORS['button']

        # 绘制按钮背景
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['black'], self.rect, 2, border_radius=8)

        # 绘制文字
        text_color = COLORS['white'] if self.active else COLORS['dark_gray']
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件，返回是否触发回调"""
        if not self.active:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True

        return False


class Slider:
    """滑块组件（用于音量调节）"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 min_value: float = 0.0, max_value: float = 1.0,
                 initial_value: float = 0.5, callback: Optional[Callable] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.callback = callback
        self.dragging = False
        self.track_height = 8
        self.handle_radius = 12

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """绘制滑块"""
        center_y = self.rect.centery

        # 绘制轨道背景
        track_rect = pygame.Rect(
            self.rect.x, center_y - self.track_height // 2,
            self.rect.width, self.track_height
        )
        pygame.draw.rect(screen, COLORS['dark_gray'], track_rect, border_radius=4)

        # 绘制已填充部分
        fill_width = int(self.rect.width * self.value)
        fill_rect = pygame.Rect(
            self.rect.x, center_y - self.track_height // 2,
            fill_width, self.track_height
        )
        pygame.draw.rect(screen, COLORS['button'], fill_rect, border_radius=4)

        # 绘制滑块手柄
        handle_x = self.rect.x + fill_width
        pygame.draw.circle(screen, COLORS['white'], (handle_x, center_y), self.handle_radius)
        pygame.draw.circle(screen, COLORS['button'], (handle_x, center_y), self.handle_radius - 2, 2)

        # 显示当前值
        value_text = f"{int(self.value * 100)}%"
        value_surface = font.render(value_text, True, COLORS['white'])
        value_rect = value_surface.get_rect(left=self.rect.right + 10, centery=center_y)
        screen.blit(value_surface, value_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self._update_value(event.pos[0])
                return True

        return False

    def _update_value(self, mouse_x: int) -> None:
        """根据鼠标位置更新值"""
        relative_x = mouse_x - self.rect.x
        new_value = relative_x / self.rect.width
        self.value = max(self.min_value, min(self.max_value, new_value))
        if self.callback:
            self.callback(self.value)


class Selector:
    """选择器组件（用于难度选择等）"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 options: List[str], initial_index: int = 0,
                 callback: Optional[Callable] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = initial_index
        self.callback = callback
        self.button_width = 40
        self.text_area = pygame.Rect(
            x + self.button_width, y,
            width - self.button_width * 2, height
        )

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """绘制选择器"""
        # 左按钮
        left_btn = pygame.Rect(self.rect.x, self.rect.y, self.button_width, self.rect.height)
        pygame.draw.rect(screen, COLORS['button'], left_btn, border_radius=4)
        pygame.draw.rect(screen, COLORS['black'], left_btn, 2, border_radius=4)
        left_text = font.render("<", True, COLORS['white'])
        left_rect = left_text.get_rect(center=left_btn.center)
        screen.blit(left_text, left_rect)

        # 右按钮
        right_btn = pygame.Rect(
            self.rect.right - self.button_width, self.rect.y,
            self.button_width, self.rect.height
        )
        pygame.draw.rect(screen, COLORS['button'], right_btn, border_radius=4)
        pygame.draw.rect(screen, COLORS['black'], right_btn, 2, border_radius=4)
        right_text = font.render(">", True, COLORS['white'])
        right_rect = right_text.get_rect(center=right_btn.center)
        screen.blit(right_text, right_rect)

        # 文本区域
        pygame.draw.rect(screen, COLORS['dark_gray'], self.text_area)
        pygame.draw.rect(screen, COLORS['black'], self.text_area, 2)
        current_text = self.options[self.selected_index]
        text_surface = font.render(current_text, True, COLORS['white'])
        text_rect = text_surface.get_rect(center=self.text_area.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理事件"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 左按钮
            left_btn = pygame.Rect(self.rect.x, self.rect.y, self.button_width, self.rect.height)
            if left_btn.collidepoint(event.pos):
                self.selected_index = (self.selected_index - 1) % len(self.options)
                if self.callback:
                    self.callback(self.selected_index)
                return True

            # 右按钮
            right_btn = pygame.Rect(
                self.rect.right - self.button_width, self.rect.y,
                self.button_width, self.rect.height
            )
            if right_btn.collidepoint(event.pos):
                self.selected_index = (self.selected_index + 1) % len(self.options)
                if self.callback:
                    self.callback(self.selected_index)
                return True

        return False


class CardSprite:
    """卡牌精灵类"""

    def __init__(self, card: Card, x: int, y: int, face_up: bool = True):
        self.card = card
        self.x = x
        self.y = y
        self.face_up = face_up
        self.selected = False
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)

    def update_position(self, x: int, y: int) -> None:
        """更新位置"""
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y

    def draw(self, screen: pygame.Surface, font: pygame.font.Font,
             suit_font: pygame.font.Font) -> None:
        """绘制卡牌"""
        # 选中效果（向上偏移）
        y_offset = -15 if self.selected else 0
        draw_rect = pygame.Rect(self.x, self.y + y_offset, CARD_WIDTH, CARD_HEIGHT)

        if self.face_up:
            # 绘制牌面
            pygame.draw.rect(screen, COLORS['card_front'], draw_rect, border_radius=CARD_CORNER_RADIUS)
            pygame.draw.rect(screen, COLORS['black'], draw_rect, 2, border_radius=CARD_CORNER_RADIUS)

            # 绘制花色和点数
            color = COLORS['red'] if self.card.is_red else COLORS['black']

            # 左上角
            rank_text = RANK_DISPLAY[self.card.rank]
            rank_surface = font.render(rank_text, True, color)
            screen.blit(rank_surface, (draw_rect.x + 5, draw_rect.y + 5))

            suit_surface = suit_font.render(SUIT_DISPLAY[self.card.suit], True, color)
            screen.blit(suit_surface, (draw_rect.x + 5, draw_rect.y + 30))

            # 中心大花色
            big_suit = suit_font.render(SUIT_DISPLAY[self.card.suit], True, color)
            big_rect = big_suit.get_rect(center=(draw_rect.centerx, draw_rect.centery))
            screen.blit(big_suit, big_rect)

            # 右下角（旋转）
            small_rank = font.render(rank_text, True, color)
            small_rank = pygame.transform.rotate(small_rank, 180)
            screen.blit(small_rank, (draw_rect.right - 25, draw_rect.bottom - 50))

            small_suit = suit_font.render(SUIT_DISPLAY[self.card.suit], True, color)
            small_suit = pygame.transform.rotate(small_suit, 180)
            screen.blit(small_suit, (draw_rect.right - 25, draw_rect.bottom - 25))
        else:
            # 绘制牌背
            pygame.draw.rect(screen, COLORS['card_back'], draw_rect, border_radius=CARD_CORNER_RADIUS)
            pygame.draw.rect(screen, COLORS['black'], draw_rect, 2, border_radius=CARD_CORNER_RADIUS)

            # 牌背图案
            pattern_rect = draw_rect.inflate(-10, -10)
            pygame.draw.rect(screen, (80, 40, 120), pattern_rect, border_radius=4)

            # 装饰图案
            center_x, center_y = draw_rect.center
            pygame.draw.circle(screen, (120, 60, 160), (center_x, center_y), 20)
            pygame.draw.circle(screen, (60, 30, 100), (center_x, center_y), 15)

        # 选中高亮
        if self.selected:
            highlight = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
            highlight.fill(COLORS['selected'])
            screen.blit(highlight, (draw_rect.x, draw_rect.y))

    def toggle_selection(self) -> None:
        """切换选中状态"""
        self.selected = not self.selected

    def set_selected(self, selected: bool) -> None:
        """设置选中状态"""
        self.selected = selected


class GameWindow:
    """游戏窗口类"""

    def __init__(self):
        """初始化游戏窗口"""
        pygame.init()
        pygame.display.set_caption("斗地主 - Doudizhu")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60

        # 游戏状态
        self.game_state: Optional[GameState] = None
        self.ai_players: Dict[int, DoudizhuAI] = {}

        # 界面元素
        self.card_sprites: Dict[int, List[CardSprite]] = {}
        self.played_card_sprites: List[CardSprite] = []
        self.buttons: List[Button] = []

        # 字体
        self._init_fonts()

        # 游戏阶段
        self.current_scene = "menu"  # menu, game, bidding, result, settings

        # 设置选项
        self.ai_difficulty = AIDifficulty.NORMAL
        self.sound_volume = 0.5
        self.music_volume = 0.3

        # UI组件
        self.sliders: List[Slider] = []
        self.selectors: List[Selector] = []

        # 音效管理器
        self.sound_manager = get_sound_manager()
        self.sound_manager.play_music('background')

        # 动画管理器
        self.anim_manager = AnimationManager()

        # 动画
        self.animation_queue = []
        self.last_action_time = 0
        self.ai_delay = 1000  # AI思考延迟（毫秒）

    def _init_fonts(self) -> None:
        """初始化字体"""
        # 尝试使用中文字体
        chinese_fonts = [
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        font_path = None
        for path in chinese_fonts:
            if os.path.exists(path):
                font_path = path
                break

        try:
            if font_path:
                self.font = pygame.font.Font(font_path, FONT_SIZE_NORMAL)
                self.font_small = pygame.font.Font(font_path, FONT_SIZE_SMALL)
                self.font_large = pygame.font.Font(font_path, FONT_SIZE_LARGE)
                self.font_title = pygame.font.Font(font_path, FONT_SIZE_TITLE)
            else:
                self.font = pygame.font.SysFont("simhei", FONT_SIZE_NORMAL)
                self.font_small = pygame.font.SysFont("simhei", FONT_SIZE_SMALL)
                self.font_large = pygame.font.SysFont("simhei", FONT_SIZE_LARGE)
                self.font_title = pygame.font.SysFont("simhei", FONT_SIZE_TITLE)
        except:
            self.font = pygame.font.Font(None, FONT_SIZE_NORMAL)
            self.font_small = pygame.font.Font(None, FONT_SIZE_SMALL)
            self.font_large = pygame.font.Font(None, FONT_SIZE_LARGE)
            self.font_title = pygame.font.Font(None, FONT_SIZE_TITLE)

        # 花色字体
        self.suit_font = pygame.font.Font(None, 36)
        self.suit_font_large = pygame.font.Font(None, 48)

    def run(self) -> None:
        """运行游戏主循环"""
        logger.info("游戏启动")

        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(self.fps)

        pygame.quit()
        logger.info("游戏退出")

    def _handle_events(self) -> None:
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.current_scene == "settings":
                        self.current_scene = "menu"
                    elif self.current_scene == "game":
                        self.current_scene = "menu"
                    elif self.current_scene == "menu":
                        self.running = False
                    return

            # 场景特定事件处理
            if self.current_scene == "menu":
                self._handle_menu_events(event)
            elif self.current_scene == "settings":
                self._handle_settings_events(event)
            elif self.current_scene in ("game", "bidding"):
                self._handle_game_events(event)

            # 按钮事件
            for button in self.buttons:
                button.handle_event(event)

            # 滑块事件
            for slider in self.sliders:
                slider.handle_event(event)

            # 选择器事件
            for selector in self.selectors:
                selector.handle_event(event)

    def _handle_menu_events(self, event: pygame.event.Event) -> None:
        """处理菜单事件"""
        pass

    def _handle_game_events(self, event: pygame.event.Event) -> None:
        """处理游戏事件"""
        if not self.game_state:
            return

        # 只在玩家回合处理点击
        current_player = self.game_state.get_current_player()
        if current_player.player_type != PlayerType.HUMAN:  # AI玩家
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 检查是否点击了手牌
            if 0 in self.card_sprites:
                for sprite in self.card_sprites[0]:
                    if sprite.rect.collidepoint(event.pos):
                        sprite.toggle_selection()
                        # 播放选牌音效
                        self.sound_manager.play_select()
                        logger.debug(f"选中/取消选中: {sprite.card}")
                        break

    def _update(self) -> None:
        """更新游戏状态"""
        # 更新动画
        self.anim_manager.update()

        if self.current_scene == "game" and self.game_state:
            self._update_game()

    def _update_game(self) -> None:
        """更新游戏逻辑"""
        current_time = pygame.time.get_ticks()

        # 检查是否需要AI行动
        if current_time - self.last_action_time < self.ai_delay:
            return

        current_player = self.game_state.get_current_player()

        if self.game_state.phase == GamePhase.BIDDING:
            if current_player.player_type != PlayerType.HUMAN:  # AI
                ai = self.ai_players.get(current_player.id)
                if ai:
                    bid = ai.make_bid(self.game_state, self.game_state.base_score)
                    self.game_state.bid(current_player.id, bid)
                    # 播放音效
                    if bid > 0:
                        self.sound_manager.play_bid()
                    logger.info(f"AI {current_player.name} 叫分: {bid}")
                    self.last_action_time = current_time

                    if self.game_state.phase == GamePhase.PLAYING:
                        self._on_bidding_complete()

        elif self.game_state.phase == GamePhase.PLAYING:
            if current_player.player_type != PlayerType.HUMAN:  # AI
                ai = self.ai_players.get(current_player.id)
                if ai:
                    cards = ai.make_decision(self.game_state)
                    success, msg = self.game_state.play_cards(current_player.id, cards)
                    if success:
                        # 播放音效
                        if cards:
                            self.sound_manager.play_play()
                            # 检查炸弹和火箭
                            last_play = self.game_state.last_play
                            if last_play:
                                if last_play.pattern == CardPattern.BOMB:
                                    self.sound_manager.play_bomb()
                                elif last_play.pattern == CardPattern.ROCKET:
                                    self.sound_manager.play_rocket()
                        else:
                            self.sound_manager.play_pass()
                        logger.info(f"AI {current_player.name} 出牌: {[str(c) for c in cards] if cards else '过'}")
                        self._update_played_cards()
                        self.last_action_time = current_time

                        if self.game_state.is_game_over():
                            self._on_game_over()

    def _draw(self) -> None:
        """绘制画面"""
        # 清屏
        self.screen.fill(COLORS['background'])

        if self.current_scene == "menu":
            self._draw_menu()
        elif self.current_scene == "settings":
            self._draw_settings()
        elif self.current_scene == "game":
            self._draw_game()
        elif self.current_scene == "bidding":
            self._draw_bidding()
        elif self.current_scene == "result":
            self._draw_result()

        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen, self.font)

        # 绘制滑块
        for slider in self.sliders:
            slider.draw(self.screen, self.font)

        # 绘制选择器
        for selector in self.selectors:
            selector.draw(self.screen, self.font)

        # 绘制动画
        self.anim_manager.draw(self.screen, self.font, self.suit_font)

        pygame.display.flip()

    def _draw_menu(self) -> None:
        """绘制主菜单"""
        # 标题
        title = self.font_title.render("斗 地 主", True, COLORS['gold'])
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # 副标题
        subtitle = self.font.render("经典三人扑克游戏", True, COLORS['white'])
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 280))
        self.screen.blit(subtitle, subtitle_rect)

        # 按钮
        self.buttons = []

        start_btn = Button(
            WINDOW_WIDTH // 2 - 100, 380, 200, 50,
            "开始游戏", self._start_new_game
        )
        self.buttons.append(start_btn)

        settings_btn = Button(
            WINDOW_WIDTH // 2 - 100, 450, 200, 50,
            "游戏设置", self._open_settings
        )
        self.buttons.append(settings_btn)

        exit_btn = Button(
            WINDOW_WIDTH // 2 - 100, 520, 200, 50,
            "退出游戏", lambda: setattr(self, 'running', False)
        )
        self.buttons.append(exit_btn)

        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen, self.font)

    def _draw_game(self) -> None:
        """绘制游戏界面"""
        if not self.game_state:
            return

        # 绘制玩家信息
        self._draw_players_info()

        # 绘制底牌区域
        self._draw_bottom_cards()

        # 绘制出牌区域
        self._draw_played_cards()

        # 绘制玩家手牌
        self._draw_player_hand()

        # 绘制操作按钮
        self._draw_action_buttons()

    def _draw_players_info(self) -> None:
        """绘制玩家信息"""
        for player in self.game_state.players:
            # 计算位置
            if player.id == 0:  # 下方（玩家）
                pos = (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50)
            elif player.id == 1:  # 左侧（AI）
                pos = (100, WINDOW_HEIGHT // 2)
            else:  # 右侧（AI）
                pos = (WINDOW_WIDTH - 100, WINDOW_HEIGHT // 2)

            # 角色标识
            role_text = "地主" if player.is_landlord() else "农民"
            if not player.is_landlord() and not player.is_farmer():
                role_text = "等待"

            role_color = COLORS['gold'] if player.is_landlord() else COLORS['white']
            role_surface = self.font.render(role_text, True, role_color)
            role_rect = role_surface.get_rect(center=pos)
            self.screen.blit(role_surface, role_rect)

            # 玩家名
            name_surface = self.font_small.render(player.name, True, COLORS['white'])
            name_rect = name_surface.get_rect(center=(pos[0], pos[1] + 25))
            self.screen.blit(name_surface, name_rect)

            # 剩余牌数
            if player.id != 0:  # AI玩家显示剩余牌数
                count_text = f"{player.get_card_count()}张"
                count_surface = self.font.render(count_text, True, COLORS['gold'])
                count_rect = count_surface.get_rect(center=(pos[0], pos[1] + 50))
                self.screen.blit(count_surface, count_rect)

            # 当前回合指示
            if self.game_state.current_player_id == player.id:
                indicator = self.font.render("◆", True, COLORS['red'])
                indicator_rect = indicator.get_rect(center=(pos[0], pos[1] - 30))
                self.screen.blit(indicator, indicator_rect)

    def _draw_bottom_cards(self) -> None:
        """绘制底牌"""
        if not self.game_state.bottom_cards:
            return

        # 底牌位置
        start_x = WINDOW_WIDTH // 2 - (3 * CARD_WIDTH + 2 * 10) // 2
        y = 80

        # 标签
        label = self.font.render("底牌", True, COLORS['gold'])
        self.screen.blit(label, (start_x, y - 30))

        for i, card in enumerate(self.game_state.bottom_cards):
            face_up = self.game_state.landlord_id is not None
            sprite = CardSprite(card, start_x + i * (CARD_WIDTH + 10), y, face_up)
            sprite.draw(self.screen, self.font, self.suit_font)

    def _draw_played_cards(self) -> None:
        """绘制已出的牌"""
        if not self.game_state.last_play or not self.game_state.last_play.cards:
            return

        cards = self.game_state.last_play.cards
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2 - 50

        # 计算起始位置
        total_width = len(cards) * CARD_SPACING + (CARD_WIDTH - CARD_SPACING)
        start_x = center_x - total_width // 2

        for i, card in enumerate(cards):
            sprite = CardSprite(card, start_x + i * CARD_SPACING, center_y, True)
            sprite.draw(self.screen, self.font, self.suit_font)

        # 显示出牌者
        if self.game_state.last_play_player_id is not None:
            player = self.game_state.players[self.game_state.last_play_player_id]
            text = f"{player.name} 出牌"
            surface = self.font.render(text, True, COLORS['gold'])
            rect = surface.get_rect(center=(center_x, center_y + CARD_HEIGHT + 30))
            self.screen.blit(surface, rect)

    def _draw_player_hand(self) -> None:
        """绘制玩家手牌"""
        if not self.game_state or not self.game_state.players:
            return

        player = self.game_state.players[0]
        hand = player.hand

        if not hand:
            return

        # 计算手牌位置
        total_width = len(hand) * CARD_SPACING + (CARD_WIDTH - CARD_SPACING)
        start_x = WINDOW_WIDTH // 2 - total_width // 2
        y = WINDOW_HEIGHT - CARD_HEIGHT - 30

        # 更新或创建卡牌精灵
        self.card_sprites[0] = []
        for i, card in enumerate(hand):
            x = start_x + i * CARD_SPACING
            sprite = CardSprite(card, x, y, True)

            # 恢复选中状态
            if card in [s.card for s in self.card_sprites.get(0, []) if s.selected]:
                sprite.selected = True

            self.card_sprites[0].append(sprite)
            sprite.draw(self.screen, self.font, self.suit_font)

    def _draw_action_buttons(self) -> None:
        """绘制操作按钮"""
        if not self.game_state:
            return

        current_player = self.game_state.get_current_player()
        if current_player.id != 0:  # 不是玩家回合
            self.buttons = []
            return

        # 清空旧按钮
        self.buttons = []

        # 出牌按钮
        def play_callback():
            if 0 not in self.card_sprites:
                return
            selected = [s.card for s in self.card_sprites[0] if s.selected]
            if selected:
                success, msg = self.game_state.play_cards(0, selected)
                if success:
                    # 播放出牌音效
                    self.sound_manager.play_play()
                    # 检查炸弹和火箭
                    last_play = self.game_state.last_play
                    if last_play:
                        if last_play.pattern == CardPattern.BOMB:
                            self.sound_manager.play_bomb()
                        elif last_play.pattern == CardPattern.ROCKET:
                            self.sound_manager.play_rocket()
                    # 清除选中状态
                    for s in self.card_sprites[0]:
                        s.set_selected(False)
                    self._update_played_cards()
                    if self.game_state.is_game_over():
                        self._on_game_over()
                else:
                    self.sound_manager.play_error()
                    logger.warning(f"出牌失败: {msg}")

        play_btn = Button(WINDOW_WIDTH // 2 - 160, WINDOW_HEIGHT - 180, 100, 40,
                          "出牌", play_callback)
        self.buttons.append(play_btn)

        # 过牌按钮
        def pass_callback():
            success, msg = self.game_state.play_cards(0, [])
            if success:
                self.sound_manager.play_pass()
                for s in self.card_sprites[0]:
                    s.set_selected(False)
                self._update_played_cards()

        pass_btn = Button(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT - 180, 100, 40,
                          "过牌", pass_callback)
        # 第一手不能过
        pass_btn.active = (self.game_state.last_play is not None and
                          self.game_state.last_play_player_id != 0)
        self.buttons.append(pass_btn)

        # 提示按钮（简化版）
        def hint_callback():
            # 取消所有选择
            for s in self.card_sprites[0]:
                s.set_selected(False)
            # 选择最小的单牌
            if self.card_sprites[0]:
                self.card_sprites[0][-1].set_selected(True)

        hint_btn = Button(WINDOW_WIDTH // 2 + 60, WINDOW_HEIGHT - 180, 100, 40,
                          "提示", hint_callback)
        self.buttons.append(hint_btn)

        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen, self.font)

    def _draw_bidding(self) -> None:
        """绘制叫分界面"""
        self._draw_game()  # 先绘制游戏背景

        # 绘制叫分对话框
        dialog_rect = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 - 100, 400, 200)
        pygame.draw.rect(self.screen, COLORS['dark_gray'], dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS['gold'], dialog_rect, 3, border_radius=10)

        # 标题
        title = self.font_large.render("叫 地 主", True, COLORS['gold'])
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
        self.screen.blit(title, title_rect)

        # 当前玩家
        current = self.game_state.get_current_player()
        text = f"轮到 {current.name}"
        surface = self.font.render(text, True, COLORS['white'])
        rect = surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        self.screen.blit(surface, rect)

        # 叫分按钮
        self.buttons = []
        for i, score in enumerate([1, 2, 3]):
            def make_bid(s):
                return lambda: self._do_bid(s)

            btn = Button(WINDOW_WIDTH // 2 - 150 + i * 100, WINDOW_HEIGHT // 2 + 20, 80, 40,
                         f"{score}分", make_bid(score))
            # 只能叫比当前高的分
            btn.active = score > self.game_state.base_score
            self.buttons.append(btn)

        # 不叫按钮
        pass_btn = Button(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 + 70, 100, 40,
                          "不叫", lambda: self._do_bid(0))
        self.buttons.append(pass_btn)

        for button in self.buttons:
            button.draw(self.screen, self.font)

    def _draw_result(self) -> None:
        """绘制游戏结果"""
        if not self.game_state:
            return

        result = self.game_state.result

        # 结果面板
        panel_rect = pygame.Rect(WINDOW_WIDTH // 2 - 250, WINDOW_HEIGHT // 2 - 200, 500, 400)
        pygame.draw.rect(self.screen, COLORS['dark_gray'], panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, COLORS['gold'], panel_rect, 4, border_radius=15)

        # 标题
        if result == GameResult.LANDLORD_WIN:
            title_text = "地主胜利"
            title_color = COLORS['gold']
        else:
            title_text = "农民胜利"
            title_color = COLORS['red']

        title = self.font_title.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 140))
        self.screen.blit(title, title_rect)

        # 玩家得分
        y_offset = WINDOW_HEIGHT // 2 - 60
        for player in self.game_state.players:
            role = "地主" if player.is_landlord() else "农民"
            score_text = f"{player.name} ({role}): {player.score:+,d}分"
            color = COLORS['gold'] if player.score > 0 else COLORS['white']
            surface = self.font.render(score_text, True, color)
            rect = surface.get_rect(center=(WINDOW_WIDTH // 2, y_offset))
            self.screen.blit(surface, rect)
            y_offset += 50

        # 按钮
        self.buttons = []

        again_btn = Button(WINDOW_WIDTH // 2 - 110, WINDOW_HEIGHT // 2 + 100, 100, 45,
                           "再来一局", self._start_new_game)
        self.buttons.append(again_btn)

        menu_btn = Button(WINDOW_WIDTH // 2 + 10, WINDOW_HEIGHT // 2 + 100, 100, 45,
                          "主菜单", lambda: setattr(self, 'current_scene', 'menu'))
        self.buttons.append(menu_btn)

        for button in self.buttons:
            button.draw(self.screen, self.font)

    def _handle_settings_events(self, event: pygame.event.Event) -> None:
        """处理设置界面事件"""
        pass

    def _open_settings(self) -> None:
        """打开设置界面"""
        self.sound_manager.play_click()
        self.current_scene = "settings"

        # 初始化设置UI组件
        self._init_settings_ui()

    def _init_settings_ui(self) -> None:
        """初始化设置界面UI"""
        self.buttons = []
        self.sliders = []
        self.selectors = []

        center_x = WINDOW_WIDTH // 2
        start_y = 250

        # 音效音量滑块
        def on_sound_volume_change(value):
            self.sound_volume = value
            self.sound_manager.set_volume(value)

        sound_slider = Slider(
            center_x - 150, start_y, 300, 40,
            min_value=0.0, max_value=1.0,
            initial_value=self.sound_volume,
            callback=on_sound_volume_change
        )
        self.sliders.append(sound_slider)

        # 音乐音量滑块
        def on_music_volume_change(value):
            self.music_volume = value
            self.sound_manager.set_music_volume(value)

        music_slider = Slider(
            center_x - 150, start_y + 70, 300, 40,
            min_value=0.0, max_value=1.0,
            initial_value=self.music_volume,
            callback=on_music_volume_change
        )
        self.sliders.append(music_slider)

        # AI难度选择器
        difficulty_options = ["简单", "普通", "困难"]
        initial_difficulty = self.ai_difficulty.value

        def on_difficulty_change(index):
            self.ai_difficulty = AIDifficulty(index)

        difficulty_selector = Selector(
            center_x - 150, start_y + 140, 300, 40,
            options=difficulty_options,
            initial_index=initial_difficulty,
            callback=on_difficulty_change
        )
        self.selectors.append(difficulty_selector)

        # 返回按钮
        back_btn = Button(
            center_x - 100, start_y + 220, 200, 50,
            "返回主菜单", lambda: setattr(self, 'current_scene', 'menu')
        )
        self.buttons.append(back_btn)

    def _draw_settings(self) -> None:
        """绘制设置界面"""
        # 标题
        title = self.font_title.render("游 戏 设 置", True, COLORS['gold'])
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        # 绘制标签
        center_x = WINDOW_WIDTH // 2
        start_y = 250

        # 音效音量标签
        sound_label = self.font.render("音效音量", True, COLORS['white'])
        sound_label_rect = sound_label.get_rect(
            center=(center_x, start_y - 25)
        )
        self.screen.blit(sound_label, sound_label_rect)

        # 音乐音量标签
        music_label = self.font.render("音乐音量", True, COLORS['white'])
        music_label_rect = music_label.get_rect(
            center=(center_x, start_y + 45)
        )
        self.screen.blit(music_label, music_label_rect)

        # AI难度标签
        difficulty_label = self.font.render("AI难度", True, COLORS['white'])
        difficulty_label_rect = difficulty_label.get_rect(
            center=(center_x, start_y + 115)
        )
        self.screen.blit(difficulty_label, difficulty_label_rect)

        # 绘制UI组件（按钮、滑块、选择器）
        for button in self.buttons:
            button.draw(self.screen, self.font)

        for slider in self.sliders:
            slider.draw(self.screen, self.font)

        for selector in self.selectors:
            selector.draw(self.screen, self.font)

    def _start_new_game(self) -> None:
        """开始新游戏"""
        logger.info("开始新游戏")

        # 播放点击音效
        self.sound_manager.play_click()

        # 创建游戏状态
        self.game_state = GameState()

        # 创建AI
        for i in range(1, 3):
            self.ai_players[i] = DoudizhuAI(self.game_state.players[i], difficulty=self.ai_difficulty)

        # 开始游戏
        self.game_state.start_new_game()

        # 播放发牌音效
        self.sound_manager.play_deal()

        # 初始化卡牌精灵
        self.card_sprites = {}

        # 切换到叫分或游戏阶段
        if self.game_state.phase == GamePhase.BIDDING:
            self.current_scene = "bidding"
        else:
            self.current_scene = "game"

        self.last_action_time = pygame.time.get_ticks()

    def _do_bid(self, score: int) -> None:
        """执行叫分"""
        if not self.game_state:
            return

        # 播放点击音效
        self.sound_manager.play_click()

        current_id = self.game_state.current_player_id
        success = self.game_state.bid(current_id, score)

        if success:
            logger.info(f"玩家 {current_id} 叫分: {score}")
            # 播放叫分音效
            if score > 0:
                self.sound_manager.play_bid()

            if self.game_state.phase == GamePhase.PLAYING:
                self._on_bidding_complete()
            else:
                # 检查是否轮到玩家
                if self.game_state.current_player_id == 0:
                    pass  # 保持bidding场景

    def _on_bidding_complete(self) -> None:
        """叫分完成"""
        logger.info("叫分结束，地主确定")
        self.current_scene = "game"
        self.last_action_time = pygame.time.get_ticks()

    def _on_game_over(self) -> None:
        """游戏结束"""
        logger.info("游戏结束")

        # 播放胜利或失败音效
        if self.game_state.result == GameResult.LANDLORD_WIN:
            if self.game_state.players[0].is_landlord():
                self.sound_manager.play_win()
            else:
                self.sound_manager.play_lose()
        else:  # FARMERS_WIN
            if self.game_state.players[0].is_farmer():
                self.sound_manager.play_win()
            else:
                self.sound_manager.play_lose()

        self.current_scene = "result"

    def _update_played_cards(self) -> None:
        """更新已出牌显示"""
        pass  # 在_draw_played_cards中实时绘制


def main():
    """主函数"""
    try:
        window = GameWindow()
        window.run()
    except Exception as e:
        logger.exception(f"游戏运行错误: {e}")
        raise


if __name__ == "__main__":
    main()
