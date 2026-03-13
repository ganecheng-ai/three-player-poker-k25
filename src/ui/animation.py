"""
动画模块
处理游戏中的各种动画效果
"""

import random
import pygame
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto

from ..game.card import Card
from ..utils import get_logger

logger = get_logger()


class AnimationType(Enum):
    """动画类型"""
    DEAL_CARD = auto()      # 发牌动画
    PLAY_CARD = auto()      # 出牌动画
    SELECT_CARD = auto()    # 选牌动画
    WIN_EFFECT = auto()     # 胜利特效
    BOMB_EFFECT = auto()    # 炸弹特效
    ROCKET_EFFECT = auto()  # 火箭特效


@dataclass
class Animation:
    """动画数据类"""
    type: AnimationType
    start_time: int
    duration: int
    start_pos: Tuple[int, int]
    end_pos: Tuple[int, int]
    card: Optional[Card] = None
    callback: Optional[Callable] = None
    completed: bool = False

    def get_progress(self, current_time: int) -> float:
        """获取动画进度（0.0 - 1.0）"""
        elapsed = current_time - self.start_time
        if elapsed >= self.duration:
            return 1.0
        return elapsed / self.duration

    def get_eased_progress(self, current_time: int) -> float:
        """获取缓动后的进度"""
        progress = self.get_progress(current_time)
        # 使用 ease-out 缓动函数
        return 1 - (1 - progress) ** 2

    def get_current_pos(self, current_time: int) -> Tuple[int, int]:
        """获取当前位置"""
        progress = self.get_eased_progress(current_time)
        x = int(self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * progress)
        y = int(self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * progress)
        return (x, y)

    def is_complete(self, current_time: int) -> bool:
        """检查动画是否完成"""
        return current_time - self.start_time >= self.duration

    def complete(self) -> None:
        """完成动画并执行回调"""
        if not self.completed:
            self.completed = True
            if self.callback:
                self.callback()


class AnimationManager:
    """动画管理器"""

    def __init__(self):
        """初始化动画管理器"""
        self.animations: List[Animation] = []
        self.particles: List[dict] = []  # 粒子效果

    def add_animation(self, anim_type: AnimationType,
                      start_pos: Tuple[int, int],
                      end_pos: Tuple[int, int],
                      duration: int = 300,
                      card: Optional[Card] = None,
                      callback: Optional[Callable] = None) -> Animation:
        """
        添加动画

        Args:
            anim_type: 动画类型
            start_pos: 起始位置
            end_pos: 结束位置
            duration: 持续时间（毫秒）
            card: 关联的卡牌
            callback: 完成回调

        Returns:
            创建的动画对象
        """
        anim = Animation(
            type=anim_type,
            start_time=pygame.time.get_ticks(),
            duration=duration,
            start_pos=start_pos,
            end_pos=end_pos,
            card=card,
            callback=callback
        )
        self.animations.append(anim)
        logger.debug(f"添加动画: {anim_type.name}, 持续时间: {duration}ms")
        return anim

    def add_deal_animation(self, start_pos: Tuple[int, int],
                           end_pos: Tuple[int, int],
                           card: Optional[Card] = None,
                           callback: Optional[Callable] = None) -> Animation:
        """添加发牌动画"""
        return self.add_animation(
            AnimationType.DEAL_CARD, start_pos, end_pos,
            duration=200, card=card, callback=callback
        )

    def add_play_animation(self, start_pos: Tuple[int, int],
                           end_pos: Tuple[int, int],
                           card: Card,
                           callback: Optional[Callable] = None) -> Animation:
        """添加出牌动画"""
        return self.add_animation(
            AnimationType.PLAY_CARD, start_pos, end_pos,
            duration=250, card=card, callback=callback
        )

    def add_bomb_effect(self, center_pos: Tuple[int, int]) -> None:
        """添加炸弹特效"""
        # 创建粒子效果
        for _ in range(20):
            self.particles.append({
                'pos': list(center_pos),
                'vel': [random.randint(-10, 10), random.randint(-15, -5)],
                'color': (255, random.randint(100, 200), 0),
                'size': random.randint(5, 15),
                'life': 30
            })
        logger.debug(f"添加炸弹特效: {center_pos}")

    def add_rocket_effect(self, start_pos: Tuple[int, int],
                          end_pos: Tuple[int, int]) -> None:
        """添加火箭特效"""
        # 创建尾迹粒子
        for i in range(10):
            t = i / 10
            x = int(start_pos[0] + (end_pos[0] - start_pos[0]) * t)
            y = int(start_pos[1] + (end_pos[1] - start_pos[1]) * t)
            self.particles.append({
                'pos': [x, y],
                'vel': [random.randint(-2, 2), random.randint(-5, -2)],
                'color': (255, 255, random.randint(100, 200)),
                'size': random.randint(8, 20),
                'life': 40
            })
        logger.debug(f"添加火箭特效")

    def update(self) -> None:
        """更新所有动画"""
        current_time = pygame.time.get_ticks()

        # 更新动画
        completed_anims = []
        for anim in self.animations:
            if anim.is_complete(current_time):
                anim.complete()
                completed_anims.append(anim)

        # 移除完成的动画
        for anim in completed_anims:
            self.animations.remove(anim)

        # 更新粒子
        for particle in self.particles[:]:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            particle['vel'][1] += 0.5  # 重力
            particle['life'] -= 1

            if particle['life'] <= 0:
                self.particles.remove(particle)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font,
             suit_font: pygame.font.Font) -> None:
        """绘制所有动画"""
        current_time = pygame.time.get_ticks()

        # 绘制动画卡牌
        for anim in self.animations:
            if anim.card:
                pos = anim.get_current_pos(current_time)
                # 绘制移动中的卡牌
                self._draw_animated_card(screen, anim.card, pos, font, suit_font)

        # 绘制粒子效果
        for particle in self.particles:
            alpha = min(255, particle['life'] * 8)
            color = (*particle['color'][:3], alpha)
            pygame.draw.circle(screen, color[:3],
                               (int(particle['pos'][0]), int(particle['pos'][1])),
                             particle['size'])

    def _draw_animated_card(self, screen: pygame.Surface, card: Card,
                            pos: Tuple[int, int], font: pygame.font.Font,
                            suit_font: pygame.font.Font) -> None:
        """绘制动画中的卡牌"""
        from ..ui.game_window import CARD_WIDTH, CARD_HEIGHT, CARD_CORNER_RADIUS
        from ..ui.game_window import RANK_DISPLAY, SUIT_DISPLAY, COLORS

        rect = pygame.Rect(pos[0], pos[1], CARD_WIDTH, CARD_HEIGHT)

        # 绘制阴影
        shadow_rect = rect.move(3, 3)
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=CARD_CORNER_RADIUS)

        # 绘制牌面
        pygame.draw.rect(screen, COLORS['card_front'], rect, border_radius=CARD_CORNER_RADIUS)
        pygame.draw.rect(screen, COLORS['black'], rect, 2, border_radius=CARD_CORNER_RADIUS)

        # 绘制花色和点数
        color = COLORS['red'] if card.is_red else COLORS['black']

        rank_text = RANK_DISPLAY[card.rank]
        rank_surface = font.render(rank_text, True, color)
        screen.blit(rank_surface, (rect.x + 5, rect.y + 5))

        suit_surface = suit_font.render(SUIT_DISPLAY[card.suit], True, color)
        screen.blit(suit_surface, (rect.x + 5, rect.y + 30))

    def is_animating(self) -> bool:
        """检查是否有正在进行的动画"""
        return len(self.animations) > 0 or len(self.particles) > 0

    def clear(self) -> None:
        """清除所有动画"""
        self.animations.clear()
        self.particles.clear()

    def wait_for_completion(self, timeout: int = 5000) -> bool:
        """
        等待所有动画完成

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            是否在超时前完成
        """
        start_time = pygame.time.get_ticks()
        while self.is_animating():
            if pygame.time.get_ticks() - start_time > timeout:
                return False
            self.update()
            pygame.time.delay(10)
        return True
