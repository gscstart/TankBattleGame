"""菜单和结束画面."""
import pygame
from settings import SCREEN_W, SCREEN_H, HUD_H
import utils.colors as C
from game.hud import get_font
import utils.i18n as i18n
t = i18n.t  # 别名, 避免与函数参数 't' 冲突


def draw_menu(surface: pygame.Surface, t: float = 0.0, num_players: int = 1):
    """主菜单画面。t 是时间（秒），用于标题闪烁。

    C1: num_players 1/2 决定模式提示.
    B6: 中文字面抽离到 i18n.t (import 别名避免与参数 't' 冲突).
    """
    surface.fill(C.MENU_BG)
    title_font = get_font(72, True)
    hint_font = get_font(20)
    small_font = get_font(16)
    title = title_font.render(i18n.t("menu.title"), True, C.MENU_TITLE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 3))

    # 副标题（闪烁）— 反映当前模式
    if int(t * 2) % 2 == 0:
        if num_players == 2:
            sub = hint_font.render(i18n.t("menu.subtitle.1p"), True, C.MENU_HINT)
        else:
            sub = hint_font.render(i18n.t("menu.subtitle.2p"), True, C.MENU_HINT)
        surface.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 3 + 100))

    # 操作说明 (i18n)
    prefix = "menu.controls.2p" if num_players == 2 else "menu.controls.1p"
    lines = [i18n.t(f"{prefix}.{i}") for i in range(5)]
    for i, line in enumerate(lines):
        text = small_font.render(line, True, C.MENU_DARK)
        surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2,
                            SCREEN_H // 2 + 40 + i * 22))

    # 模式标记
    mode_key = "menu.mode.2p" if num_players == 2 else "menu.mode.1p"
    mode_text = small_font.render(i18n.t(mode_key), True, C.MENU_TITLE)
    surface.blit(mode_text, (SCREEN_W // 2 - mode_text.get_width() // 2, SCREEN_H // 2 - 10))

    # 装饰：底部 (语言切换提示 + credits)
    lang_text = small_font.render(i18n.t("menu.lang.hint"), True, C.MENU_DARK)
    surface.blit(lang_text, (12, SCREEN_H - 40))
    credits = small_font.render(i18n.t("menu.credits"), True, C.MENU_DARK)
    surface.blit(credits, (SCREEN_W // 2 - credits.get_width() // 2, SCREEN_H - 40))


def draw_pause(surface: pygame.Surface):
    """暂停遮罩."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    title = get_font(64, True).render(i18n.t("menu.pause.title"), True, C.MENU_TITLE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 60))
    hint = get_font(20).render(i18n.t("menu.pause.hint"), True, C.MENU_HINT)
    surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 10))


def draw_level_complete(surface: pygame.Surface, level: int, score: int, t: float):
    """关卡完成画面."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    title = get_font(56, True).render(
        i18n.t("menu.level_complete.title", level=level + 1), True, (120, 230, 120))
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))
    score_text = get_font(24).render(
        i18n.t("menu.level_complete.score", score=score), True, C.MENU_HINT)
    surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, SCREEN_H // 2))
    if int(t * 2) % 2 == 0:
        hint = get_font(18).render(i18n.t("menu.level_complete.hint"), True, C.MENU_DARK)
        surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 50))


def draw_game_over(surface: pygame.Surface, score: int, victory: bool = False, t: float = 0.0):
    """游戏结束画面."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))
    title_key = "menu.victory.title" if victory else "menu.game_over.title"
    title_color = (120, 230, 120) if victory else (230, 80, 80)
    title = get_font(64, True).render(i18n.t(title_key), True, title_color)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))
    score_text = get_font(28).render(
        i18n.t("menu.game_over.score", score=score), True, C.MENU_HINT)
    surface.blit(score_text, (SCREEN_W // 2 - score_text.get_width() // 2, SCREEN_H // 2 + 10))
    if int(t * 2) % 2 == 0:
        hint = get_font(22).render(i18n.t("menu.game_over.hint"), True, C.MENU_TITLE)
        surface.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 70))


def draw_highscores(surface: pygame.Surface, scores: list, t: float = 0.0):
    """排行榜画面. scores: [{name, score, level, date}, ...]"""
    surface.fill(C.MENU_BG)
    title_font = get_font(48, True)
    row_font = get_font(20)
    small_font = get_font(16)
    # 标题
    title = title_font.render(i18n.t("menu.highscores.title"), True, C.MENU_TITLE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 50))
    if not scores:
        empty = row_font.render(i18n.t("menu.highscores.empty"), True, C.MENU_HINT)
        surface.blit(empty, (SCREEN_W // 2 - empty.get_width() // 2, SCREEN_H // 2))
    else:
        # 表头
        header = small_font.render(i18n.t("menu.highscores.header"), True, C.MENU_DARK)
        surface.blit(header, (SCREEN_W // 2 - header.get_width() // 2, 130))
        # 列表
        for i, s in enumerate(scores):
            row_str = i18n.t("menu.highscores.row",
                              rank=i + 1, name=s['name'], score=s['score'],
                              level=s['level'], date=s.get('date', ''))
            color = C.MENU_TITLE if i == 0 else C.MENU_HINT
            text = row_font.render(row_str, True, color)
            surface.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 170 + i * 32))
    # 返回提示
    if int(t * 2) % 2 == 0:
        back = small_font.render(i18n.t("menu.highscores.back"), True, C.MENU_DARK)
        surface.blit(back, (SCREEN_W // 2 - back.get_width() // 2, SCREEN_H - 40))


def draw_achievements(surface: pygame.Surface, manager, t: float = 0.0):
    """C5 成就展示页. manager: achievements.Manager 实例."""
    surface.fill(C.MENU_BG)
    title_font = get_font(40, True)
    name_font = get_font(18)
    desc_font = get_font(13)
    small_font = get_font(14)
    # 标题
    title = title_font.render(
        i18n.t("menu.achievements.title",
               unlocked=manager.unlocked_count(), total=manager.total_count()),
        True, C.MENU_TITLE)
    surface.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 30))
    # 列表
    from utils.achievements import ACHIEVEMENTS
    for i, ach in enumerate(ACHIEVEMENTS):
        unlocked = manager.is_unlocked(ach.id)
        color = ach.icon_color if unlocked else (80, 80, 80)
        y = 100 + i * 48
        # 图标方块
        pygame.draw.rect(surface, color, (60, y, 28, 28))
        if not unlocked:
            # 灰色未解锁 - 加把锁的"?"
            qmark = name_font.render("?", True, (200, 200, 200))
            surface.blit(qmark, (60 + 14 - qmark.get_width() // 2,
                                 y + 14 - qmark.get_height() // 2))
        # 名称
        name_text = name_font.render(
            i18n.t(ach.name_key), True,
            C.MENU_HINT if unlocked else C.MENU_DARK)
        surface.blit(name_text, (100, y))
        # 描述
        desc_text = desc_font.render(
            i18n.t(ach.desc_key), True, C.MENU_DARK)
        surface.blit(desc_text, (100, y + 22))
    # 返回提示
    if int(t * 2) % 2 == 0:
        back = small_font.render(i18n.t("menu.achievements.back"), True, C.MENU_DARK)
        surface.blit(back, (SCREEN_W // 2 - back.get_width() // 2, SCREEN_H - 30))
