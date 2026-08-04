"""道具系统。

9 种道具（经典 6 + B4 扩展 3）：
- star      ⭐ 升级（子弹加速 + 可破钢墙）
- grenade   💣 全屏敌人立即死亡
- helmet    🛡 玩家无敌 10s
- clock     ⏰ 所有敌人冻结 8s
- shovel    ⛏ 基地周围砖墙变钢墙 15s
- tank      🎖 玩家 +1 命
- magnet    🧲 8s 内所有道具飞向玩家
- laser     ⚡ 10s 内玩家子弹穿透敌人
- mine      💥 玩家位置放 3 颗地雷，敌人撞上 100px AOE 爆炸

生命周期：
- 敌人被击杀时 25% 概率掉落（红闪 100%）
- 存活 12 秒后消失
- 玩家接触时触发效果
- magnet 激活时: 存活道具向玩家飞 (powerup.update 被 Level 控制)
"""
import random
import time
import pygame
from settings import TILE


ALL_TYPES = ["star", "grenade", "helmet", "clock", "shovel", "tank",
             "magnet", "laser", "mine"]
# 道具对应的颜色（用于绘制时识别）
TYPE_COLORS = {
    "star":    (255, 220, 100),
    "grenade": (240, 100, 80),
    "helmet":  (140, 200, 255),
    "clock":   (140, 220, 180),
    "shovel":  (220, 180, 100),
    "tank":    (200, 100, 220),
    # B4: 3 个新道具
    "magnet":  (220, 120, 220),  # 紫红 - 磁铁
    "laser":   (255, 240, 100),  # 亮黄 - 激光
    "mine":    (160, 80, 60),    # 暗红棕 - 地雷
}


class PowerUp:
    """单个道具实体。"""

    LIFETIME = 12.0  # 12s 后自动消失
    MAGNET_SPEED = 200.0  # 磁铁吸引速度 (像素/秒)

    def __init__(self, x: int, y: int, ptype: str):
        self.type = ptype
        self.color = TYPE_COLORS.get(ptype, (200, 200, 200))
        self.rect = pygame.Rect(x, y, TILE, TILE)
        self.spawn_time = time.time()
        self.dead = False

    def update(self, dt: float, magnet_target: tuple | None = None):
        """magnet_target: (cx, cy) 若提供且磁铁激活中, 道具向其飞."""
        if self.dead:
            return
        # 12s 后消失
        if time.time() - self.spawn_time > self.LIFETIME:
            self.dead = True
            return
        # 磁铁吸引 (B4): 向 target 中心飞, 直到重叠即被拾取
        if magnet_target is not None:
            cx, cy = magnet_target
            dx = cx - self.rect.centerx
            dy = cy - self.rect.centery
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 1.0:
                step = self.MAGNET_SPEED * dt
                if step >= dist:
                    self.rect.center = (cx, cy)
                else:
                    self.rect.x += int(dx / dist * step)
                    self.rect.y += int(dy / dist * step)

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
        elif self.type == "magnet":
            # U 形磁铁: 两端红极, 中间白条
            pygame.draw.rect(surface, (200, 80, 80), (cx - 12, cy - 6, 8, 14))  # 左红
            pygame.draw.rect(surface, (80, 80, 200), (cx + 4, cy - 6, 8, 14))  # 右蓝
            pygame.draw.rect(surface, (240, 240, 240), (cx - 4, cy - 4, 8, 12))  # 中白
            # 顶部连接线
            pygame.draw.line(surface, (200, 80, 80), (cx - 8, cy - 6), (cx - 4, cy - 6), 2)
            pygame.draw.line(surface, (80, 80, 200), (cx + 4, cy - 6), (cx + 8, cy - 6), 2)
        elif self.type == "laser":
            # 闪电符号 (zigzag)
            pts = [
                (cx - 2, cy - 12), (cx - 6, cy - 2), (cx - 1, cy - 1),
                (cx - 3, cy + 12), (cx + 6, cy - 4), (cx + 1, cy - 5),
                (cx + 3, cy - 12),
            ]
            pygame.draw.polygon(surface, (255, 200, 50), pts)
            pygame.draw.polygon(surface, (255, 255, 200), pts, 1)
        elif self.type == "mine":
            # 球形地雷 + 引线 + 火花
            pygame.draw.circle(surface, (60, 60, 60), (cx, cy + 2), 11)
            pygame.draw.circle(surface, (140, 70, 50), (cx, cy + 2), 11, 2)
            # 引线
            pygame.draw.line(surface, (200, 200, 200), (cx, cy - 9), (cx + 4, cy - 14), 2)
            # 火花
            pygame.draw.circle(surface, (255, 200, 80), (cx + 4, cy - 14), 2)


def spawn_random_powerup(x: int, y: int) -> PowerUp:
    """在 (x, y) 位置随机生成一个道具。"""
    ptype = random.choice(ALL_TYPES)
    return PowerUp(x, y, ptype)


# math import（用于图标绘制）
import math
