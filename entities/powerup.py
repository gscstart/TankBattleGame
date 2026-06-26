"""道具系统。

6 种道具（经典 Battle City）：
- star      ⭐ 升级（子弹加速 + 可破钢墙）
- grenade   💣 全屏敌人立即死亡
- helmet    🛡 玩家无敌 10s
- clock     ⏰ 所有敌人冻结 8s
- shovel    ⛏ 基地周围砖墙变钢墙 15s
- tank      🎖 玩家 +1 命

生命周期：
- 敌人被击杀时 25% 概率掉落
- 存活 12 秒后消失
- 玩家接触时触发效果
"""
import random
import time
import pygame
from settings import TILE


ALL_TYPES = ["star", "grenade", "helmet", "clock", "shovel", "tank"]
# 道具对应的颜色（用于绘制时识别）
TYPE_COLORS = {
    "star":    (255, 220, 100),
    "grenade": (240, 100, 80),
    "helmet":  (140, 200, 255),
    "clock":   (140, 220, 180),
    "shovel":  (220, 180, 100),
    "tank":    (200, 100, 220),
}


class PowerUp:
    """单个道具实体。"""

    LIFETIME = 12.0  # 12s 后自动消失

    def __init__(self, x: int, y: int, ptype: str):
        self.type = ptype
        self.color = TYPE_COLORS.get(ptype, (200, 200, 200))
        self.rect = pygame.Rect(x, y, TILE, TILE)
        self.spawn_time = time.time()
        self.dead = False

    def update(self, dt: float):
        if self.dead:
            return
        # 12s 后消失
        if time.time() - self.spawn_time > self.LIFETIME:
            self.dead = True

    def draw(self, surface: pygame.Surface):
        if self.dead:
            return
        # 闪烁效果（每秒闪 4 次）
        elapsed = time.time() - self.spawn_time
        if int(elapsed * 4) % 2 == 0:
            return
        # 画底框
        x, y, w, h = self.rect.x, self.rect.y, self.rect.w, self.rect.h
        pygame.draw.rect(surface, (30, 30, 30), (x, y, w, h))
        pygame.draw.rect(surface, self.color, (x + 2, y + 2, w - 4, h - 4))
        # 画图标
        self._draw_icon(surface, x, y, w, h)

    def _draw_icon(self, surface: pygame.Surface, x: int, y: int, w: int, h: int):
        """画道具对应的图形。"""
        cx, cy = x + w // 2, y + h // 2
        if self.type == "star":
            # 5 角星
            points = []
            for i in range(10):
                angle = -math.pi / 2 + i * math.pi / 5
                r = 14 if i % 2 == 0 else 6
                points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            pygame.draw.polygon(surface, (255, 255, 255), points)
        elif self.type == "grenade":
            # 红圆 + 灰顶
            pygame.draw.circle(surface, (60, 60, 60), (cx, y + 8), 4)
            pygame.draw.circle(surface, (240, 100, 80), (cx, cy + 4), 12)
            pygame.draw.line(surface, (60, 60, 60), (cx, y + 4), (cx + 4, y + 8), 2)
        elif self.type == "helmet":
            # 倒 U 形头盔
            pygame.draw.arc(surface, (255, 255, 255),
                            (cx - 14, cy - 8, 28, 24), 0, math.pi, 4)
            pygame.draw.rect(surface, (255, 255, 255), (cx - 14, cy + 4, 28, 4))
        elif self.type == "clock":
            # 圆 + 12/3/6/9 标记
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 14, 2)
            pygame.draw.line(surface, (255, 255, 255), (cx, cy), (cx, cy - 8), 2)
            pygame.draw.line(surface, (255, 255, 255), (cx, cy), (cx + 6, cy), 2)
        elif self.type == "shovel":
            # 铲子
            pygame.draw.rect(surface, (180, 140, 80), (cx - 2, cy - 10, 4, 12))
            pygame.draw.polygon(surface, (180, 140, 80),
                                [(cx - 8, cy + 2), (cx + 8, cy + 2),
                                 (cx + 4, cy + 12), (cx - 4, cy + 12)])
        elif self.type == "tank":
            # 小坦克
            pygame.draw.rect(surface, (255, 255, 255), (cx - 12, cy - 8, 24, 16))
            pygame.draw.rect(surface, (255, 255, 255), (cx - 3, cy - 14, 6, 8))


def spawn_random_powerup(x: int, y: int) -> PowerUp:
    """在 (x, y) 位置随机生成一个道具。"""
    ptype = random.choice(ALL_TYPES)
    return PowerUp(x, y, ptype)


# math import（用于图标绘制）
import math
