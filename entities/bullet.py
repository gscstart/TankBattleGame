"""子弹实体。

改进：
- 拖尾效果：记录前 N 帧位置，画渐变
- 命中爆炸：撞到瓦片/坦克时创建 Explosion 特效
"""
import pygame
from settings import BULLET_SIZE, BULLET_SPEED, MAP_X, MAP_Y, GRID_W, GRID_H, TILE
from world.tile import TileBase, TileSteel, TileEmpty


class Bullet:
    """一颗飞行中的子弹。"""

    TRAIL_LEN = 6  # 拖尾保留帧数

    def __init__(self, x, y, direction, owner):
        self.direction = direction
        self.owner = owner
        self.size = BULLET_SIZE
        self.rect = pygame.Rect(
            int(x - BULLET_SIZE // 2),
            int(y - BULLET_SIZE // 2),
            BULLET_SIZE,
            BULLET_SIZE,
        )
        self.dead = False
        self.can_break_steel = False  # 默认不能破钢墙
        # 拖尾：最近几帧的中心位置 [(x, y), ...]
        self.trail = []

    def update(self, dt: float, tilemap, bullets, tanks, base_callback, effects=None):
        if self.dead:
            return
        # 记录当前位置到拖尾
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > self.TRAIL_LEN:
            self.trail.pop(0)

        # 飞行
        speed = BULLET_SPEED
        dx = self.direction[0] * speed * dt
        dy = self.direction[1] * speed * dt
        steps = max(1, int(max(abs(dx), abs(dy)) / 2) + 1)
        step_dx = dx / steps
        step_dy = dy / steps
        for _ in range(steps):
            self.rect.x += step_dx
            self.rect.y += step_dy
            # 地图边界
            if (self.rect.right < MAP_X or self.rect.left >= MAP_X + GRID_W * TILE
                    or self.rect.bottom < MAP_Y or self.rect.top >= MAP_Y + GRID_H * TILE):
                self._spawn_explosion(effects, scale=0.6)
                self.dead = True
                return
            # 砖块
            hits = tilemap.rect_hits_brick_subcell(self.rect)
            if hits:
                tile, c, r, sub = hits[0]
                tile.on_bullet_hit(self, sub)
                from utils.sound import play
                play("hit")
                self._spawn_explosion(effects, scale=0.7)
                self.dead = True
                return
            # 钢墙 / 基地
            hits2 = tilemap.rect_hits_steel_or_base(self.rect)
            if hits2:
                tile, c, r = hits2[0]
                if isinstance(tile, TileSteel) and self.can_break_steel:
                    # 玩家升级后能破钢墙：变回空地
                    tilemap.tiles[r][c] = TileEmpty()
                    from utils.sound import play
                    play("hit")
                    self._spawn_explosion(effects, scale=0.8)
                else:
                    tile.on_bullet_hit(self)
                    if isinstance(tile, TileBase):
                        base_callback(tile)
                        self._spawn_explosion(effects, scale=1.2, big=True)
                    else:
                        self._spawn_explosion(effects, scale=0.7)
                self.dead = True
                return
            # 其他子弹
            for other in bullets:
                if other is self or other.dead:
                    continue
                if self.rect.colliderect(other.rect):
                    self._spawn_explosion(effects, scale=0.5)
                    self.dead = True
                    other.dead = True
                    return
            # 坦克
            for tank in tanks:
                if tank.dead:
                    continue
                if self.rect.colliderect(tank.rect):
                    from utils.sound import play
                    play("explosion")
                    self._spawn_explosion(effects, scale=1.0, big=True)
                    self.dead = True
                    tank.on_hit(self)
                    return

    def _spawn_explosion(self, effects, scale=1.0, big=False):
        if effects is None:
            return
        from entities.effects import Explosion
        # 爆炸位置：子弹中心
        x, y = self.rect.centerx, self.rect.centery
        # 缩放爆炸位置（向飞行方向偏移一点，看起来像击中点）
        x += self.direction[0] * 4
        y += self.direction[1] * 4
        effects.append(Explosion(x, y, big=big))

    def draw(self, surface: pygame.Surface):
        if self.dead:
            return
        from utils.draw import draw_bullet
        # 拖尾
        for i, (tx, ty) in enumerate(self.trail[:-1]):
            t = (i + 1) / max(1, len(self.trail))
            r = max(1, int(5 * t))
            alpha = int(140 * t)
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 230, 140, alpha), (r + 1, r + 1), r)
            surface.blit(s, (tx - r - 1, ty - r - 1))
        # 主体
        draw_bullet(surface, self.rect, self.direction)
