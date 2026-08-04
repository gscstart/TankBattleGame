"""顶部 HUD。"""
import pygame
from settings import SCREEN_W, HUD_H, MAP_X, MAP_Y
import utils.colors as C


# 缓存找到的 CJK 字体名
_cjk_font_name: str | None = None
_cjk_searched: bool = False


def _find_cjk_font() -> str | None:
    """在系统上找一个支持中文（CJK）的字体名。找不到则返回 None。"""
    global _cjk_font_name, _cjk_searched
    if _cjk_searched:
        return _cjk_font_name
    _cjk_searched = True
    # 按优先级尝试（Windows / macOS / Linux 都能覆盖）
    candidates = [
        "microsoftyahei", "msyh",              # Windows 微软雅黑
        "microsoftjhenghei", "msjh",            # Windows 微软正黑（繁体）
        "simhei", "simsun", "simkai", "simfang",  # Windows 中易字体
        "pingfangsc", "stheiti", "songti",      # macOS
        "hiraginosansgb",                       # macOS
        "notosanscjksc", "notosanscjk",         # 跨平台
        "wenquanyimicrohei", "wenquanyizenhei", # Linux 常见
        "arialunicodems",                       # Windows Unicode
    ]
    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            _cjk_font_name = name
            return name
    return None


def get_font(size, bold=False):
    """获取支持中文（CJK）的字体，优先 CJK，回退到等宽字体。"""
    cjk = _find_cjk_font()
    if cjk:
        return pygame.font.SysFont(cjk, size, bold=bold)
    return pygame.font.SysFont("arial,simhei,notosanscjk,monospace", size, bold=bold)


def draw_hud(surface: pygame.Surface, lives: int, score: int, level: int,
             enemies_left: int, max_lives: int = 3,
             p2_lives: int | None = None):
    """绘制顶部 HUD 横条。

    C1 改造: 接受 p2_lives (None = 单人模式, 隐藏 P2 槽).
    P1 黄, P2 蓝 (从 utils.colors.P2_COLOR 取).
    """
    # 背景
    pygame.draw.rect(surface, C.HUD_BG, (0, 0, SCREEN_W, HUD_H))
    # 底边
    pygame.draw.line(surface, C.HUD_ACCENT, (0, HUD_H), (SCREEN_W, HUD_H), 2)
    label_font = get_font(14, True)
    text_color = C.HUD_TEXT
    tank_w = 14

    # ---- P1 生命 (左) ----
    p1_label = label_font.render("P1", True, C.HUD_ACCENT)
    surface.blit(p1_label, (12, 6))
    for i in range(max_lives):
        x = 12 + i * (tank_w + 3)
        y = 24
        pygame.draw.rect(surface, C.PLAYER_COLOR, (x, y, tank_w, tank_w))
        pygame.draw.rect(surface, C.PLAYER_DARK, (x, y, tank_w, tank_w), 1)
        if i < max_lives - lives:
            pygame.draw.line(surface, C.BLACK, (x, y), (x + tank_w, y + tank_w), 2)
            pygame.draw.line(surface, C.BLACK, (x + tank_w, y), (x, y + tank_w), 2)

    # ---- P2 生命 (P1 右侧, 仅双人模式) ----
    p2_x = 12 + max_lives * (tank_w + 3) + 8
    if p2_lives is not None:
        p2_color = getattr(C, 'P2_COLOR', (140, 200, 255))
        p2_dark = getattr(C, 'P2_DARK', (90, 140, 200))
        p2_label = label_font.render("P2", True, C.HUD_ACCENT)
        surface.blit(p2_label, (p2_x, 6))
        for i in range(max_lives):
            x = p2_x + i * (tank_w + 3)
            y = 24
            pygame.draw.rect(surface, p2_color, (x, y, tank_w, tank_w))
            pygame.draw.rect(surface, p2_dark, (x, y, tank_w, tank_w), 1)
            if i < max_lives - p2_lives:
                pygame.draw.line(surface, C.BLACK, (x, y), (x + tank_w, y + tank_w), 2)
                pygame.draw.line(surface, C.BLACK, (x + tank_w, y), (x, y + tank_w), 2)

    # 中：关卡
    level_text = get_font(20, True).render(f"第 {level + 1} 关", True, text_color)
    surface.blit(level_text, (SCREEN_W // 2 - level_text.get_width() // 2, 18))

    # 右上：剩余敌人
    enemies_label = label_font.render("剩余", True, C.HUD_ACCENT)
    surface.blit(enemies_label, (SCREEN_W - enemies_label.get_width() - 12, 6))
    enemies_text = get_font(20, True).render(f"{enemies_left:02d}", True, text_color)
    surface.blit(enemies_text, (SCREEN_W - enemies_text.get_width() - 12, 26))

    # 分数（居中偏左, 关卡文本下方）
    score_label = label_font.render("分数", True, C.HUD_ACCENT)
    score_label_x = SCREEN_W // 2 - 80
    surface.blit(score_label, (score_label_x, 6))
    score_text = get_font(18, True).render(f"{score:06d}", True, text_color)
    surface.blit(score_text, (score_label_x, 24))
