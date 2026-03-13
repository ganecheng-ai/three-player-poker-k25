"""
音效管理模块
处理游戏中的音效和背景音乐
"""

import pygame
import os
from typing import Optional, Dict
from pathlib import Path

from ..utils import get_logger

logger = get_logger()


class SoundManager:
    """音效管理器类"""

    # 音效文件映射
    SOUND_FILES = {
        'deal': 'deal.wav',           # 发牌音效
        'play': 'play.wav',           # 出牌音效
        'pass': 'pass.wav',           # 过牌音效
        'win': 'win.wav',             # 胜利音效
        'lose': 'lose.wav',           # 失败音效
        'bomb': 'bomb.wav',           # 炸弹音效
        'rocket': 'rocket.wav',       # 火箭音效
        'bid': 'bid.wav',             # 叫分音效
        'click': 'click.wav',         # 点击音效
        'select': 'select.wav',       # 选牌音效
        'error': 'error.wav',         # 错误音效
    }

    def __init__(self, assets_dir: Optional[Path] = None):
        """
        初始化音效管理器

        Args:
            assets_dir: 资源目录路径
        """
        self.sounds: Dict[str, Optional[pygame.mixer.Sound]] = {}
        self.music_enabled = True
        self.sound_enabled = True
        self.volume = 0.5
        self.music_volume = 0.3

        # 设置资源目录
        if assets_dir is None:
            self.assets_dir = Path(__file__).parent.parent.parent / 'assets' / 'sounds'
        else:
            self.assets_dir = assets_dir / 'sounds'

        # 初始化音频系统
        self._init_audio()

    def _init_audio(self) -> None:
        """初始化音频系统"""
        try:
            # 初始化mixer（如果尚未初始化）
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

            # 加载所有音效
            self._load_sounds()

            logger.info("音效系统初始化完成")
        except Exception as e:
            logger.warning(f"音效系统初始化失败: {e}")
            self.sound_enabled = False
            self.music_enabled = False

    def _load_sounds(self) -> None:
        """加载所有音效文件"""
        for sound_name, filename in self.SOUND_FILES.items():
            sound_path = self.assets_dir / filename
            try:
                if sound_path.exists():
                    self.sounds[sound_name] = pygame.mixer.Sound(str(sound_path))
                    self.sounds[sound_name].set_volume(self.volume)
                    logger.debug(f"加载音效: {sound_name}")
                else:
                    # 音效文件不存在，使用占位符
                    self.sounds[sound_name] = None
                    logger.debug(f"音效文件不存在: {sound_path}")
            except Exception as e:
                logger.warning(f"加载音效失败 {sound_name}: {e}")
                self.sounds[sound_name] = None

    def play(self, sound_name: str) -> None:
        """
        播放音效

        Args:
            sound_name: 音效名称
        """
        if not self.sound_enabled:
            return

        sound = self.sounds.get(sound_name)
        if sound:
            try:
                sound.play()
            except Exception as e:
                logger.debug(f"播放音效失败: {e}")

    def play_deal(self) -> None:
        """播放发牌音效"""
        self.play('deal')

    def play_play(self) -> None:
        """播放出牌音效"""
        self.play('play')

    def play_pass(self) -> None:
        """播放过牌音效"""
        self.play('pass')

    def play_win(self) -> None:
        """播放胜利音效"""
        self.play('win')

    def play_lose(self) -> None:
        """播放失败音效"""
        self.play('lose')

    def play_bomb(self) -> None:
        """播放炸弹音效"""
        self.play('bomb')

    def play_rocket(self) -> None:
        """播放火箭音效"""
        self.play('rocket')

    def play_bid(self) -> None:
        """播放叫分音效"""
        self.play('bid')

    def play_click(self) -> None:
        """播放点击音效"""
        self.play('click')

    def play_select(self) -> None:
        """播放选牌音效"""
        self.play('select')

    def play_error(self) -> None:
        """播放错误音效"""
        self.play('error')

    def set_volume(self, volume: float) -> None:
        """
        设置音效音量

        Args:
            volume: 音量（0.0 - 1.0）
        """
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.volume)

    def set_music_volume(self, volume: float) -> None:
        """
        设置音乐音量

        Args:
            volume: 音量（0.0 - 1.0）
        """
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except:
            pass

    def enable_sound(self, enabled: bool = True) -> None:
        """启用/禁用音效"""
        self.sound_enabled = enabled

    def enable_music(self, enabled: bool = True) -> None:
        """启用/禁用背景音乐"""
        self.music_enabled = enabled
        if not enabled:
            self.stop_music()

    def play_music(self, music_name: str = 'background') -> None:
        """
        播放背景音乐

        Args:
            music_name: 音乐文件名（不含扩展名）
        """
        if not self.music_enabled:
            return

        music_path = self.assets_dir / f'{music_name}.mp3'
        if not music_path.exists():
            music_path = self.assets_dir / f'{music_name}.ogg'

        if music_path.exists():
            try:
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # 循环播放
                logger.info(f"播放背景音乐: {music_path}")
            except Exception as e:
                logger.warning(f"播放背景音乐失败: {e}")

    def stop_music(self) -> None:
        """停止背景音乐"""
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def pause_music(self) -> None:
        """暂停背景音乐"""
        try:
            pygame.mixer.music.pause()
        except:
            pass

    def resume_music(self) -> None:
        """恢复背景音乐"""
        if self.music_enabled:
            try:
                pygame.mixer.music.unpause()
            except:
                pass


# 全局音效管理器实例
_sound_manager: Optional[SoundManager] = None


def get_sound_manager() -> SoundManager:
    """获取全局音效管理器实例"""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager


def init_sound_manager(assets_dir: Optional[Path] = None) -> SoundManager:
    """初始化全局音效管理器"""
    global _sound_manager
    _sound_manager = SoundManager(assets_dir)
    return _sound_manager
