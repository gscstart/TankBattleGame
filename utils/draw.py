"""纯代码绘制所有视觉元素。坦克、子弹、瓦片都在这里。"""
import pygame
import math
from settings import TILE, TANK_SIZE, BULLET_SIZE, ENEMY_TIER_COLORS
import utils.colors as C


# ---------------------------------------------------------------------------
# 坦克
# ---------------------------------------------------------------------------

def draw_tank(surface: pygame.Surface, rect: pygame.Rect, direction: tuple,
              color: tuple, dark: tuple | None = None, flashing: bool = False,
              tread_phase: float = 0.0, hit_flash: bool = False):
    """绘制一辆坦克（48×48），含车身、履带、炮塔、炮管。

    direction: settings.Dir.UP/DOWN/LEFT/RIGHT
    color: 车身主色
    dark: 履带/阴影颜色，自动根据主色加深
    flashing: 玩家重生无敌期间，闪烁效果
    tread_phase: 履带动画相位（0-24），随移动累计，让履带纹路滚动
    """
    if dark is None:
        dark = _darken(color, 0.6)

    x, y, w, h = rect.x, rect.y, rect.w, rect.h

    # 无敌闪烁：始终画坦克，闪烁时叠白膜（不再 return 跳过坦克）
    is_flashing_frame = flashing and (pygame.time.get_ticks() // 80) % 2 == 0

    # 履带动画偏移（0..5 像素循环）
    tread_off = int(tread_phase) % 6
    # 履带（两个长条）
    track_w = 8
    if direction[0] == 0:  # 垂直
        # 左右履带
        pygame.draw.rect(surface, dark, (x, y, track_w, h))
        pygame.draw.rect(surface, dark, (x + w - track_w, y, track_w, h))
        # 履带纹路（每 6 像素一段，加上动画偏移制造滚动感）
        for i in range(-6, h + 6, 6):
            ty = y + i + tread_off
            if ty < y - 3 or ty + 3 > y + h:
                continue
            pygame.draw.rect(surface, _darken(dark, 0.7),
                             (x, ty, track_w, 3))
            pygame.draw.rect(surface, _darken(dark, 0.7),
                             (x + w - track_w, ty, track_w, 3))
        # 车身
        body = pygame.Rect(x + track_w, y, w - 2 * track_w, h)
        pygame.draw.rect(surface, color, body)
        pygame.draw.rect(surface, _darken(color, 0.7), body, 1)
        # 炮塔（中心圆）
        cx, cy = x + w // 2, y + h // 2
        pygame.draw.circle(surface, color, (cx, cy), w // 3)
        pygame.draw.circle(surface, _darken(color, 0.7), (cx, cy), w // 3, 1)
        # 炮管
        if direction[1] < 0:  # UP
            pygame.draw.rect(surface, dark, (cx - 3, y, 6, h // 2))
        else:  # DOWN
            pygame.draw.rect(surface, dark, (cx - 3, cy, 6, h // 2))
    else:  # 水平
        # 上下履带
        pygame.draw.rect(surface, dark, (x, y, w, track_w))
        pygame.draw.rect(surface, dark, (x, y + h - track_w, w, track_w))
        # 履带纹路
        for i in range(-6, w + 6, 6):
            tx = x + i + tread_off
            if tx < x - 3 or tx + 3 > x + w:
                continue
            pygame.draw.rect(surface, _darken(dark, 0.7),
                             (tx, y, 3, track_w))
            pygame.draw.rect(surface, _darken(dark, 0.7),
                             (tx, y + h - track_w, 3, track_w))
        # 车身
        body = pygame.Rect(x, y + track_w, w, h - 2 * track_w)
        pygame.draw.rect(surface, color, body)
        pygame.draw.rect(surface, _darken(color, 0.7), body, 1)
        # 炮塔
        cx, cy = x + w // 2, y + h // 2
        pygame.draw.circle(surface, color, (cx, cy), h // 3)
        pygame.draw.circle(surface, _darken(color, 0.7), (cx, cy), h // 3, 1)
        # 炮管
        if direction[0] < 0:  # LEFT
            pygame.draw.rect(surface, dark, (x, cy - 3, w // 2, 6))
        else:  # RIGHT
            pygame.draw.rect(surface, dark, (cx, cy - 3, w // 2, 6))

    # 闪烁效果：叠白膜
    if is_flashing_frame:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((255, 255, 255, 110))
        surface.blit(s, (x, y))

    # 被击中闪红
    if hit_flash:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((255, 60, 60, 180))
        surface.blit(s, (x, y))


def _darken(color: tuple, factor: float) -> tuple:
    return (max(0, int(color[0] * factor)),
            max(0, int(color[1] * factor)),
            max(0, int(color[2] * factor)))


# ---------------------------------------------------------------------------
# 子弹
# ---------------------------------------------------------------------------

def draw_bullet(surface: pygame.Surface, rect: pygame.Rect, direction: tuple):
    """绘制一颗子弹。"""
    cx, cy = rect.centerx, rect.centery
    r = rect.w // 2
    pygame.draw.circle(surface, C.BULLET_COLOR, (cx, cy), r)
    pygame.draw.circle(surface, C.BULLET_OUTLINE, (cx, cy), r, 1)
    # 方向小尾迹
    if direction[0] != 0:
        # 水平飞行
        sx = cx + direction[0] * (r + 2)
        pygame.draw.rect(surface, C.BULLET_OUTLINE, (sx, cy - 1, 3, 3))
    else:
        sy = cy + direction[1] * (r + 2)
        pygame.draw.rect(surface, C.BULLET_OUTLINE, (cx - 1, sy, 3, 3))


# ---------------------------------------------------------------------------
# 瓦片
# ---------------------------------------------------------------------------

def draw_tile(surface: pygame.Surface, tile, rect: pygame.Rect):
    """根据 tile 类别分派绘制。"""
    from world.tile import (TileEmpty, TileBrick, TileSteel, TileGrass,
                            TileWater, TileIce, TileBase)
    if isinstance(tile, TileEmpty):
        return
    elif isinstance(tile, TileBrick):
        _draw_brick(surface, rect, tile.subtl)
    elif isinstance(tile, TileSteel):
        _draw_steel(surface, rect)
    elif isinstance(tile, TileGrass):
        _draw_grass(surface, rect)
    elif isinstance(tile, TileWater):
        _draw_water(surface, rect)
    elif isinstance(tile, TileIce):
        _draw_ice(surface, rect)
    elif isinstance(tile, TileBase):
        _draw_base(surface, rect, tile.destroyed)


def _draw_brick(surface, rect, subtl: int):
    """subtl 是 4 位位掩码，从 LSB 起：左上、右上、左下、右下。"""
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    half = w // 2
    # 背景底色（用 BRICK_DARK 显示空洞）
    pygame.draw.rect(surface, (20, 20, 20), rect)
    sub_rects = [
        (x, y, half, half),                  # 左上
        (x + half, y, w - half, half),       # 右上
        (x, y + half, half, h - half),       # 左下
        (x + half, y + half, w - half, h - half),  # 右下
    ]
    for i, sr in enumerate(sub_rects):
        if subtl & (1 << i):
            pygame.draw.rect(surface, C.BRICK, sr)
            # 砖块纹理
            pygame.draw.rect(surface, C.BRICK_DARK, sr, 1)
            cx = sr[0] + sr[2] // 2
            cy = sr[1] + sr[3] // 2
            pygame.draw.line(surface, C.BRICK_DARK, (cx, sr[1]), (cx, sr[1] + sr[3] - 1))
            pygame.draw.line(surface, C.BRICK_DARK, (sr[0], cy), (sr[0] + sr[2] - 1, cy))


def _draw_steel(surface, rect):
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    half = w // 2
    q1 = pygame.Rect(x, y, half, half)
    q2 = pygame.Rect(x + half, y, w - half, half)
    q3 = pygame.Rect(x, y + half, half, h - half)
    q4 = pygame.Rect(x + half, y + half, w - half, h - half)
    pygame.draw.rect(surface, C.STEEL_LIGHT, q1)
    pygame.draw.rect(surface, C.STEEL_DARK, q2)
    pygame.draw.rect(surface, C.STEEL_DARK, q3)
    pygame.draw.rect(surface, C.STEEL_LIGHT, q4)
    pygame.draw.rect(surface, C.BLACK, rect, 1)


def _draw_grass(surface, rect):
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    pygame.draw.rect(surface, C.GRASS, rect)
    # 草丛竖条
    for i in range(6):
        sx = x + (i * w) // 6 + 4
        pygame.draw.line(surface, C.GRASS_DARK, (sx, y + 4), (sx, y + h - 4), 2)
    pygame.draw.rect(surface, C.GRASS_DARK, rect, 1)


def _draw_water(surface, rect):
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    pygame.draw.rect(surface, C.WATER, rect)
    # 水波（根据时间偏移做轻微动画）
    t = pygame.time.get_ticks() // 300
    for i in range(3):
        yy = y + 8 + i * (h // 3) + (t % 2) * 2
        pygame.draw.line(surface, C.WATER_LIGHT, (x + 4, yy), (x + w - 4, yy), 2)
    pygame.draw.rect(surface, C.WATER_LIGHT, rect, 1)


def _draw_ice(surface, rect):
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    pygame.draw.rect(surface, C.ICE, rect)
    # 高光
    pygame.draw.line(surface, C.ICE_LIGHT, (x + 4, y + 4), (x + w - 8, y + 4), 2)
    pygame.draw.line(surface, C.ICE_LIGHT, (x + 4, y + 4), (x + 4, y + h - 8), 2)
    pygame.draw.rect(surface, (180, 220, 255), rect, 1)


def _draw_base(surface, rect, destroyed: bool):
    """基地/老鹰：简化几何（房子+鹰头）。"""
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    if destroyed:
        # 残骸
        pygame.draw.rect(surface, C.BASE_DEAD, rect)
        pygame.draw.line(surface, C.BLACK, (x, y), (x + w, y + h), 2)
        pygame.draw.line(surface, C.BLACK, (x + w, y), (x, y + h), 2)
        return
    # 底座
    base_h = h // 3
    pygame.draw.rect(surface, C.BASE_BODY, (x, y + h - base_h, w, base_h))
    pygame.draw.rect(surface, C.BASE_DARK, (x, y + h - base_h, w, base_h), 1)
    # 鹰身（梯形 + 三角）
    cx = x + w // 2
    body_top = y + h - base_h
    pygame.draw.polygon(surface, C.BASE_BODY, [
        (x + 8, body_top),
        (x + w - 8, body_top),
        (cx + 6, y + 4),
        (cx - 6, y + 4),
    ])
    # 鹰头（圆）
    head_r = 7
    pygame.draw.circle(surface, C.BASE_BODY, (cx, y + 8), head_r)
    pygame.draw.circle(surface, C.BASE_DARK, (cx, y + 8), head_r, 1)
    # 鹰眼
    pygame.draw.circle(surface, C.BLACK, (cx - 3, y + 7), 1)
    pygame.draw.circle(surface, C.BLACK, (cx + 3, y + 7), 1)
    # 鹰嘴
    pygame.draw.polygon(surface, (240, 180, 60),
                        [(cx - 2, y + 9), (cx + 2, y + 9), (cx, y + 13)])
    # 翅膀横线
    pygame.draw.line(surface, C.BASE_DARK,
                     (x + 6, body_top - 4), (x + w - 6, body_top - 4), 2)
