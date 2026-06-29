"""pytest 共享 fixture: dummy SDL 环境 + pygame 初始化.

autouse=True + scope="session" 保证所有测试自动获得:
- 无头 SDL (无显示器/音频设备也能跑)
- pygame 子系统初始化 (font/mixer/display)

音频设备缺失时 mixer.init() 可能失败, 用 try/except 容错.
"""
import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def _dummy_sdl_env():
    """设置无头 SDL 环境变量 (必须在 import pygame 前)."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(autouse=True, scope="session")
def _pygame_init():
    """初始化 pygame 子系统, 创建 display surface, 测试结束清理."""
    import pygame
    pygame.init()  # init 所有子系统 (含 font + mixer)
    try:
        pygame.mixer.init()
    except Exception:
        # 无音频设备的 CI 环境 (如 GitHub Actions linux runner) mixer.init 失败
        # 测试代码已用 try/except 兜底音效调用, 不会传播错误
        pass
    # 创建 display surface (draw_hud/draw_menu 等需要非 None surface)
    from settings import SCREEN_W, SCREEN_H
    pygame.display.set_mode((SCREEN_W, SCREEN_H))
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _clear_event_bus():
    """每个测试前后清空 utils.events 全局订阅, 避免测试间串扰."""
    from utils import events
    events.clear()
    yield
    events.clear()
