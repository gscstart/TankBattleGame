"""音效管理器。

特性：
- 懒加载：首次调用 play() 时初始化 pygame.mixer
- 静音切换：muted 全局开关
- 程序生成 wav：若 assets/sounds 缺失，自动调用 gen_sounds 工具
- 失败容错：任何异常都不影响游戏运行

调用：
    from utils.sound import play
    play("fire")
"""
import os
import sys

_mixer_initialized = False
_sounds: dict = {}
_muted = False
_disabled = False  # mixer 初始化失败则禁用


def _ensure_mixer():
    """确保 mixer 已初始化，必要时生成 wav。"""
    global _mixer_initialized, _disabled
    if _mixer_initialized or _disabled:
        return
    try:
        import pygame
        # 检查 wav 文件是否存在
        sound_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")
        fire_path = os.path.join(sound_dir, "fire.wav")
        if not os.path.exists(fire_path):
            # 自动生成
            print("[sound] assets/sounds 缺失，自动生成...")
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools"))
                import gen_sounds
                gen_sounds.main()
            except Exception as e:
                print(f"[sound] 自动生成失败: {e}，音效将禁用")
                _disabled = True
                return
        pygame.mixer.init()
        pygame.mixer.set_num_channels(8)
        for name in ("fire", "explosion", "hit", "start"):
            path = os.path.join(sound_dir, f"{name}.wav")
            if os.path.exists(path):
                try:
                    _sounds[name] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"[sound] 加载 {name} 失败: {e}")
        _mixer_initialized = True
    except Exception as e:
        print(f"[sound] mixer 初始化失败: {e}，音效将禁用")
        _disabled = True


def play(name: str):
    """播放音效。name: fire / explosion / hit / start。失败时静默忽略。"""
    if _muted or _disabled:
        return
    try:
        _ensure_mixer()
        snd = _sounds.get(name)
        if snd is not None:
            snd.play()
    except Exception:
        pass  # 静默失败，不影响游戏


def set_muted(muted: bool):
    """切换静音。"""
    global _muted
    _muted = muted


def is_muted() -> bool:
    return _muted


def is_available() -> bool:
    """是否启用了音效。"""
    _ensure_mixer()
    return not _disabled and len(_sounds) > 0
