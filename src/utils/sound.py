"""
音效管理模块
处理游戏中的音效和背景音乐
"""

import pygame
import os
import math
from typing import Optional, Dict
from pathlib import Path

from ..utils import get_logger

logger = get_logger()


def generate_wave(frequency: float, duration: float, volume: float = 0.5,
                  sample_rate: int = 44100) -> bytes:
    """
    生成正弦波音效数据

    Args:
        frequency: 频率(Hz)
        duration: 持续时间(秒)
        volume: 音量(0.0-1.0)
        sample_rate: 采样率
    """
    num_samples = int(duration * sample_rate)
    audio_bytes = bytearray()

    for i in range(num_samples):
        t = i / sample_rate
        value = math.sin(2 * math.pi * frequency * t) * volume
        sample = int(value * 32767)
        audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))
        audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))

    return bytes(audio_bytes)


def generate_complex_sound(notes: list, duration: float, volume: float = 0.5,
                          sample_rate: int = 44100) -> bytes:
    """生成复杂音效（多音符）"""
    num_samples = int(duration * sample_rate)
    audio_bytes = bytearray()
    note_duration = duration / len(notes) if notes else duration

    for i in range(num_samples):
        t = i / sample_rate
        note_index = int(t / note_duration) if note_duration > 0 else 0
        if note_index >= len(notes):
            note_index = len(notes) - 1

        freq = notes[note_index] if note_index < len(notes) else notes[-1]
        value = math.sin(2 * math.pi * freq * t) * volume
        sample = int(value * 32767)
        audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))
        audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))

    return bytes(audio_bytes)


def generate_sweep(start_freq: float, end_freq: float, duration: float,
                   volume: float = 0.5, sample_rate: int = 44100) -> bytes:
    """生成频率扫描音效"""
    num_samples = int(duration * sample_rate)
    audio_bytes = bytearray()

    for i in range(num_samples):
        t = i / sample_rate
        freq = start_freq + (end_freq - start_freq) * (t / duration)
        value = math.sin(2 * math.pi * max(freq, 20) * t) * volume
        sample = int(value * 32767)
        audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))
        audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))

    return bytes(audio_bytes)


def generate_sound_by_type(sound_type: str) -> Optional[pygame.mixer.Sound]:
    """根据类型生成音效"""
    try:
        if sound_type == 'deal':
            data = generate_wave(800, 0.1, 0.3)
        elif sound_type == 'play':
            data = generate_wave(1200, 0.15, 0.5)
        elif sound_type == 'pass':
            data = generate_wave(400, 0.2, 0.4)
        elif sound_type == 'win':
            notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
            data = generate_complex_sound(notes, 1.0, 0.4)
        elif sound_type == 'lose':
            data = generate_sweep(400, 200, 0.8, 0.4)
        elif sound_type == 'bomb':
            # 爆炸音效 - 快速下降频率 + 噪声
            num_samples = int(0.6 * 44100)
            audio_bytes = bytearray()
            for i in range(num_samples):
                t = i / 44100
                if t < 0.1:
                    freq = 200 - t * 1000
                else:
                    freq = 100 * (1 - (t - 0.1) / 0.5)
                value = math.sin(2 * math.pi * max(freq, 20) * t) * 0.6
                # 添加噪声
                value += ((hash(i) % 100) - 50) / 2000 * (1 - t / 0.6)
                sample = int(value * 32767)
                audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))
                audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))
            data = bytes(audio_bytes)
        elif sound_type == 'rocket':
            data = generate_sweep(400, 1400, 1.0, 0.5)
        elif sound_type == 'bid':
            data = generate_wave(1000, 0.1, 0.4)
        elif sound_type == 'click':
            data = generate_wave(1500, 0.05, 0.3)
        elif sound_type == 'select':
            data = generate_wave(600, 0.08, 0.3)
        elif sound_type == 'error':
            # 错误音效 - 颤音
            num_samples = int(0.3 * 44100)
            audio_bytes = bytearray()
            for i in range(num_samples):
                t = i / 44100
                value = math.sin(2 * math.pi * 150 * t) * 0.4
                value *= 0.5 + 0.5 * math.sin(20 * math.pi * t)
                sample = int(value * 32767)
                audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))
                audio_bytes.extend(sample.to_bytes(2, 'little', signed=True))
            data = bytes(audio_bytes)
        else:
            return None

        return pygame.mixer.Sound(buffer=data)
    except Exception as e:
        logger.warning(f"生成音效 {sound_type} 失败: {e}")
        return None


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
        """加载所有音效文件，文件不存在时动态生成"""
        for sound_name, filename in self.SOUND_FILES.items():
            sound_path = self.assets_dir / filename
            try:
                if sound_path.exists():
                    self.sounds[sound_name] = pygame.mixer.Sound(str(sound_path))
                    self.sounds[sound_name].set_volume(self.volume)
                    logger.debug(f"加载音效: {sound_name}")
                else:
                    # 音效文件不存在，动态生成
                    logger.debug(f"音效文件不存在，动态生成: {sound_name}")
                    generated_sound = generate_sound_by_type(sound_name)
                    if generated_sound:
                        generated_sound.set_volume(self.volume)
                        self.sounds[sound_name] = generated_sound
                    else:
                        self.sounds[sound_name] = None
            except Exception as e:
                logger.warning(f"加载音效失败 {sound_name}: {e}，尝试动态生成")
                generated_sound = generate_sound_by_type(sound_name)
                if generated_sound:
                    generated_sound.set_volume(self.volume)
                    self.sounds[sound_name] = generated_sound
                else:
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
