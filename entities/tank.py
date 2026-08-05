"""坦克基类。"""
import pygame
from settings import TANK_SIZE, MAP_X, MAP_Y, GRID_W, GRID_H, TILE


def snap_to_grid(value: int, size: int = TANK_SIZE) -> int:
    """将位置吸附到 TILE 边界。"""
    return round(value / TILE) * TILE


class Tank:
    """坦克基类。"""
    BASE_SPEED = 96  # 像素/秒
    SNAP_RATE = 900  # 软吸附速度（像素/秒）—— 越大越快对齐
    TREAD_PERIOD = 6  # 履带纹路周期（像素）
    FIRE_COOLDOWN = 0.5  # 默认开火冷却（子类可覆盖）

    def __init__(self, x, y, direction, color, dark_color, speed=None):
        self.rect = pygame.Rect(int(x), int(y), TANK_SIZE, TANK_SIZE)
        self.dir = direction
        self.color = color
        self.dark_color = dark_color
        self.speed = speed if speed is not None else self.BASE_SPEED
        self.cooldown = 0.0
        self.dead = False
        self.flashing_time = 0.0  # 剩余无敌闪烁时间
        # 软吸附状态：'x' / 'y' / None
        self.snap_axis = None
        self.snap_target = 0
        # 履带动画：累计移动距离
        self.tread_phase = 0.0
        # 玩家标记（由 PlayerTank 在 __init__ 末尾设为 True）
        self.is_player = False
        # 被击中闪红时间
        self.hit_flash_time = 0.0
        # 道具击杀标记（被 grenade 等道具杀死时设为 True，避免双重计分）
        self.killed_by_powerup = False
        # C2: HP (默认 1, BOSS 等多血坦克覆盖)
        self.hp = 1

    # ---- 移动与旋转 ----
    def try_move(self, dt: float, dx: float, dy: float, tilemap, other_tanks) -> bool:
        """尝试移动 (dx, dy) 像素。返回是否真的移动了。"""
        if self.can_move_now() is False:
            return False
        old_x, old_y = self.rect.x, self.rect.y
        self.rect.x += dx
        if self._collides(tilemap, other_tanks):
            self.rect.x = old_x
        self.rect.y += dy
        if self._collides(tilemap, other_tanks):
            self.rect.y = old_y
        moved = (self.rect.x != old_x) or (self.rect.y != old_y)
        if moved:
            primary = max(abs(dx), abs(dy))
            if primary > 0:
                self.tread_phase = (self.tread_phase + primary) % (self.TREAD_PERIOD * 4)
        return moved

    def can_move_now(self) -> bool:
        """如果正在软吸附，且吸附轴与移动方向相同，阻止移动。"""
        if self.snap_axis is None:
            return True
        if self.snap_axis == 'x' and self.dir[0] != 0:
            return False
        if self.snap_axis == 'y' and self.dir[1] != 0:
            return False
        return True

    def try_change_direction(self, new_dir, tilemap, other_tanks) -> bool:
        """尝试改变方向。软吸附：不在 1 帧内跳到格点，而是在 ~50ms 内平滑移动过去。"""
        if new_dir == self.dir:
            self.snap_axis = None  # 取消任何进行中的吸附
            return True
        # 决定吸附轴
        if new_dir[0] == 0:  # 垂直移动 → 吸附 x
            axis = 'x'
            target = snap_to_grid(self.rect.x)
        else:  # 水平移动 → 吸附 y
            axis = 'y'
            target = snap_to_grid(self.rect.y)
        # 试探吸附目标是否合法（带微调容差）
        old_x, old_y = self.rect.x, self.rect.y
        if axis == 'x':
            self.rect.x = target
        else:
            self.rect.y = target
        if self._collides(tilemap, other_tanks):
            # 尝试 ±2/±4 像素微调（细粒度碰撞容差）
            for adj in (-2, 2, -4, 4, -6, 6):
                if axis == 'x':
                    self.rect.x = target + adj
                else:
                    self.rect.y = target + adj
                if not self._collides(tilemap, other_tanks):
                    target = target + adj
                    break
            else:
                self.rect.x, self.rect.y = old_x, old_y
                return False
        # 软吸附：记录目标
        self.snap_axis = axis
        self.snap_target = target
        self.dir = new_dir
        return True

    def update_snap(self, dt: float):
        """每帧调用：把吸附轴的位置向 snap_target 推进。"""
        if self.snap_axis is None:
            return
        cur = self.rect.x if self.snap_axis == 'x' else self.rect.y
        diff = self.snap_target - cur
        step = self.SNAP_RATE * dt
        if abs(diff) <= step:
            # 到达目标
            if self.snap_axis == 'x':
                self.rect.x = self.snap_target
            else:
                self.rect.y = self.snap_target
            self.snap_axis = None
        else:
            new_pos = cur + (step if diff > 0 else -step)
            if self.snap_axis == 'x':
                self.rect.x = int(new_pos)
            else:
                self.rect.y = int(new_pos)

    def _collides(self, tilemap, other_tanks) -> bool:
        # 地图边界
        if (self.rect.left < MAP_X or self.rect.right > MAP_X + GRID_W * TILE
                or self.rect.top < MAP_Y or self.rect.bottom > MAP_Y + GRID_H * TILE):
            return True
        if tilemap.rect_collides_solid(self.rect):
            return True
        for other in other_tanks:
            if other is self or other.dead:
                continue
            if self.rect.colliderect(other.rect):
                return True
        return False

    # ---- 子弹 ----
    def can_shoot(self) -> bool:
        return self.cooldown <= 0.0 and not self.dead

    def shoot(self, bullets, effects=None):
        """在炮口位置生成子弹。可选地同时创建炮口闪光特效。"""
        if not self.can_shoot():
            return None
        cx, cy = self.rect.centerx, self.rect.centery
        # 子弹从炮管最外端（边缘外 4 像素）出现
        offset = TANK_SIZE // 2 + 4
        bx = cx + self.dir[0] * offset
        by = cy + self.dir[1] * offset
        from entities.bullet import Bullet
        owner = "player" if self.is_player else "enemy"
        bullet = Bullet(bx, by, self.dir, owner)
        # 子弹能破钢墙：tier 2 敌人 或 玩家升级到 2 级
        can_break = getattr(self, "breaks_steel", False)
        if not can_break and self.is_player:
            can_break = getattr(self, "upgrade_level", 0) >= 2
        if can_break:
            bullet.can_break_steel = True
        # B4: 玩家在 laser 激活期间射击, 子弹穿透敌人不消失
        if self.is_player and getattr(self, "laser_timer", 0.0) > 0.0:
            bullet.is_laser = True
        bullets.append(bullet)
        # 炮口闪光
        if effects is not None:
            from entities.effects import MuzzleFlash
            fx = cx + self.dir[0] * (TANK_SIZE // 2 + 2)
            fy = cy + self.dir[1] * (TANK_SIZE // 2 + 2)
            effects.append(MuzzleFlash(fx, fy, self.dir, self.color))
        # 音效
        from utils.sound import play
        play("fire")
        self.cooldown = self.FIRE_COOLDOWN
        return bullet

    def update_cooldown(self, dt: float):
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.flashing_time > 0:
            self.flashing_time -= dt
        if self.hit_flash_time > 0:
            self.hit_flash_time -= dt

    def on_hit(self, bullet):
        """被子弹命中。子类可重写。

        C2 改造: 减血, hp<=0 才 dead (BOSS 等多血坦克).
        """
        if self.flashing_time > 0:
            return  # 无敌
        self.hit_flash_time = 0.3
        self.hp -= 1
        if self.hp <= 0:
            self.dead = True

    # ---- 渲染 ----
    def draw(self, surface: pygame.Surface):
        from utils.draw import draw_tank
        draw_tank(surface, self.rect, self.dir, self.color, self.dark_color,
                  flashing=self.flashing_time > 0,
                  tread_phase=self.tread_phase,
                  hit_flash=self.hit_flash_time > 0)
