"""菜单和结束画面。"""
import pygame
from settings import SCREEN_W, SCREEN_H, HUD_H
import utils.colors as C
from game.hud import get_font


def draw_menu(surface: pygame.Surface, t: float = 0.0):
    """主菜单画面。t 是时间（秒），用于标题闪烁。"""
    surface.fill(C.MENU_BG)
    title_font = get_font(72, True)
    hint_font = get_font(20)
    small_font = get_font(16)
    title = title_font.render("坦克大战", True, C.MENU_TITLE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 3))

    # 副标题（闪烁）
    if int(t * 2) % 2 == 0:
        sub = hint_font.render("按回车或空格开始游戏", True, C.MENU_HINT)
        surface.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 3 + 100))

    # 操作说明
    lines = [
        "WASD / 方向键 ： 移  动",
        "空格 / J      ： 发  射",
        "P             ： 暂  停",
        "R             ： 重  开",
    ]
    for i, line in enumerate(lines):
        text = small_font.render(line, True, C.MENU_DARK)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2,
                            SCREEN_H // 2 + 60 + i * 24))

    # 装饰：底部
    credits = small_font.render("Battle City 致敬作品  -  pygame-ce", True, C.MENU_DARK)
    surface.blit(credits, (SCREEN_W // 2 - credits.get_width() // 2, SCREEN_H - 40))


def draw_pause(surface: pygame.Surface):
    """暂停遮罩。"""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    title = get_font(64, True).render("已暂停", True, C.MENU_TITLE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 60))
    hint = get_font(20).render("按 P 继续", True, C.MENU_HINT)
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 10))


def draw_level_complete(surface: pygame.Surface, level: int, score: int, t: float):
    """关卡完成画面。"""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    title = get_font(56, True).render(f"第 {level + 1} 关 通关！", True, (120, 230, 120))
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))
    score_text = get_font(24).render(f"分  数：{score:06d}", True, C.MENU_HINT)
    surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, SCREEN_H // 2))
    if int(t * 2) % 2 == 0:
        hint = get_font(18).render("正在进入下一关...", True, C.MENU_DARK)
        surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 50))


def draw_game_over(surface: pygame.Surface, score: int, victory: bool = False, t: float = 0.0):
    """游戏结束画面。"""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))
    if victory:
        title = get_font(64, True).render("胜  利！", True, (120, 230, 120))
    else:
        title = get_font(64, True).render("游戏结束", True, (230, 80, 80))
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))
    score_text = get_font(28).render(f"最终分数：{score:06d}", True, C.MENU_HINT)
    surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, SCREEN_H // 2 + 10))
    if int(t * 2) % 2 == 0:
        hint = get_font(22).render("按 R 重开  /  ESC 退出", True, C.MENU_TITLE)
        surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 70))
