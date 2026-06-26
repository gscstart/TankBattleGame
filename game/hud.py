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
             enemies_left: int, max_lives: int = 3):
    """绘制顶部 HUD 横条。"""
    # 背景
    pygame.draw.rect(surface, C.HUD_BG, (0, 0, SCREEN_W, HUD_H))
    # 底边
    pygame.draw.line(surface, C.HUD_ACCENT, (0, HUD_H), (SCREEN_W, HUD_H), 2)
    # 玩家生命（小坦克图标）
    label_font = get_font(16, True)
    text_color = C.HUD_TEXT

    # 左：生命
    lives_label = label_font.render("生命", True, C.HUD_ACCENT)
    surface.blit(lives_label, (12, 8))
    tank_w = 16
    for i in range(max_lives):
        x = 12 + i * (tank_w + 4)
        y = 28
        # 简化的坦克图标（黄方块+炮管）
        pygame.draw.rect(surface, C.PLAYER_COLOR, (x, y, tank_w, tank_w))
        pygame.draw.rect(surface, C.PLAYER_DARK, (x, y, tank_w, tank_w), 1)
        if i < max_lives - lives:
            # 失去的生命打叉
            pygame.draw.line(surface, C.BLACK, (x, y), (x + tank_w, y + tank_w), 2)
            pygame.draw.line(surface, C.BLACK, (x + tank_w, y), (x, y + tank_w), 2)

    # 中：关卡
    level_text = get_font(20, True).render(f"第 {level + 1} 关", True, text_color)
    surface.blit(level_text, (SCREEN_W // 2 - level_text.get_width() // 2, 18))

    # 右上：剩余敌人
    enemies_label = label_font.render("剩余", True, C.HUD_ACCENT)
    surface.blit(enemies_label, (SCREEN_W - enemies_label.get_width() - 12, 8))
    enemies_text = get_font(20, True).render(f"{enemies_left:02d}", True, text_color)
    surface.blit(enemies_text, (SCREEN_W - enemies_text.get_width() - 12, 28))

    # 左中：分数（在生命下方）
    score_label = label_font.render("分数", True, C.HUD_ACCENT)
    surface.blit(score_label, (90, 8))
    score_text = get_font(20, True).render(f"{score:06d}", True, text_color)
    surface.blit(score_text, (90, 28))
