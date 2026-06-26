"""特效系统：炮口闪光、爆炸粒子。

所有特效都是短命的（< 1 秒），由 Level 统一管理。
"""
import math
import random
import pygame
from settings import TANK_SIZE


class MuzzleFlash:
    """炮口闪光。持续 3-4 帧后消失。"""

    def __init__(self, x, y, direction, owner_color):
        """
        x, y: 炮口位置（炮管最外端）
        direction: 子弹方向
        owner_color: 坦克颜色（闪光用同色调）
        """
        self.x = x
        self.y = y
        self.direction = direction
        self.color = owner_color
        self.life = 0.10  # 100ms
        self.max_life = 0.10
        self.dead = False

    def update(self, dt: float):
        self.life -= dt
        if self.life <= 0:
            self.dead = True

    def draw(self, surface: pygame.Surface):
        if self.dead:
            return
        t = self.life / self.max_life  # 1.0 → 0.0
        # 闪光主体：4-射线星形 + 中心圆
        cx, cy = int(self.x), int(self.y)
        # 中心亮白圆
        r_inner = max(2, int(6 * t))
        pygame.draw.circle(surface, (255, 255, 220), (cx, cy), r_inner)
        # 中层：坦克颜色
        r_mid = max(2, int(10 * t))
        s = pygame.Surface((r_mid * 2 + 2, r_mid * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, int(220 * t)),
                           (r_mid + 1, r_mid + 1), r_mid)
        surface.blit(s, (cx - r_mid - 1, cy - r_mid - 1))
        # 外层：橙色光晕
        r_out = max(3, int(16 * t))
        s2 = pygame.Surface((r_out * 2 + 2, r_out * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s2, (255, 180, 60, int(120 * t)),
                           (r_out + 1, r_out + 1), r_out)
        surface.blit(s2, (cx - r_out - 1, cy - r_out - 1))
        # 沿方向拉长一道"火光"
        dx, dy = self.direction
        flash_len = int(18 * t)
        for i in range(1, 4):
            ox = cx + dx * flash_len * i / 3
            oy = cy + dy * flash_len * i / 3
            r = max(1, int(4 * t * (1 - i / 4)))
            pygame.draw.circle(surface, (255, 220, 120), (int(ox), int(oy)), r)


class Particle:
    """单颗粒子。被 Explosion 使用。"""

    def __init__(self, x, y, vx, vy, color, life):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = random.randint(3, 6)

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        # 阻力
        self.vx *= 0.92
        self.vy *= 0.92
        # 重力（轻微）
        self.vy += 60 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        if self.life <= 0:
            return
        t = self.life / self.max_life
        r = max(1, int(self.size * t))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)


class Explosion:
    """爆炸：8-15 颗粒子向四周扩散，0.4-0.6 秒寿命。"""

    def __init__(self, x, y, big=False):
        self.particles = []
        n = 14 if big else 10
        # 颜色方案：橙黄白
        palette = [
            (255, 220, 100),
            (255, 180, 60),
            (255, 120, 40),
            (255, 240, 180),
            (220, 80, 40),
        ]
        for _ in range(n):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(80, 220) * (1.4 if big else 1.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(palette)
            life = random.uniform(0.35, 0.55)
            self.particles.append(Particle(x, y, vx, vy, color, life))
        # 中心一道闪光
        self.flash_life = 0.08
        self.x = x
        self.y = y
        self.dead = False

    def update(self, dt: float):
        self.particles = [p for p in self.particles if p.update(dt)]
        self.flash_life -= dt
        if self.flash_life <= 0 and not self.particles:
            self.dead = True

    def draw(self, surface: pygame.Surface):
        if self.dead:
            return
        # 中心瞬时闪光
        if self.flash_life > 0:
            t = self.flash_life / 0.08
            r = int(20 * t)
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 240, 200, int(200 * t)),
                               (r + 1, r + 1), r)
            surface.blit(s, (int(self.x) - r - 1, int(self.y) - r - 1))
        for p in self.particles:
            p.draw(surface)
