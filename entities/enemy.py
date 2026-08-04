"""敌人 AI 坦克。

升级点：
- 用 line_of_sight 公共函数检查玩家/基地方向
- 主动瞄准基地
- tier 1 开火更准、tier 2 速度+25% 且子弹能破钢墙
- 红闪敌人（powerup carrier）：视觉红闪 + 被击杀时 100% 掉道具
"""
import random
import pygame
from settings import (
    Dir, ENEMY_SPEED, ENEMY_FIRE_COOLDOWN_MIN, ENEMY_FIRE_COOLDOWN_MAX,
    ENEMY_TIER_COLORS, POWERUP_CARRIER_CHANCE, POWERUP_CARRIER_COLOR,
    POWERUP_CARRIER_FLASH_PERIOD,
)
from entities.tank import Tank
from utils.collision import line_of_sight
import utils.colors as C


# tier 行为参数
TIER_FIRE_COOLDOWN = {
    0: (ENEMY_FIRE_COOLDOWN_MIN, ENEMY_FIRE_COOLDOWN_MAX),  # 0.8-1.6s
    1: (0.6, 1.2),  # 更准
    2: (0.8, 1.6),  # 但能破钢墙
}
TIER_SPEED_MULT = {0: 1.0, 1: 1.0, 2: 1.25}
TIER_BREAKS_STEEL = {0: False, 1: False, 2: True}


class EnemyTank(Tank):
    BASE_SPEED = ENEMY_SPEED

    def __init__(self, x, y, tier=0, enemy_speed=None, is_powerup_carrier=None):
        # 红闪敌人：随机决定（除非显式传 True/False 锁定），颜色用鲜红
        if is_powerup_carrier is None:
            is_powerup_carrier = random.random() < POWERUP_CARRIER_CHANCE
        self.is_powerup_carrier = is_powerup_carrier

        if self.is_powerup_carrier:
            color = POWERUP_CARRIER_COLOR
        else:
            color = ENEMY_TIER_COLORS[tier % len(ENEMY_TIER_COLORS)]
        dark = tuple(max(0, int(c * 0.6)) for c in color)
        # 速度由 tier 和关卡配置决定
        if enemy_speed is None:
            enemy_speed = ENEMY_SPEED
        speed = enemy_speed * TIER_SPEED_MULT.get(tier, 1.0)
        super().__init__(x, y, Dir.DOWN, color, dark, speed=speed)
        self.tier = tier
        self.breaks_steel = TIER_BREAKS_STEEL.get(tier, False)
        self._next_dir_time = 0.0
        self._next_fire_time = random.uniform(0.5, 1.0)
        self.born_invuln = 1.0
        self._last_dir = Dir.DOWN
        # 冻结状态（被 clock 道具影响）
        self.frozen = False
        # 红闪敌人：进入无敌闪烁循环（每帧补 flashing_time，draw_tank 会叠白膜）
        if self.is_powerup_carrier:
            self.flashing_time = POWERUP_CARRIER_FLASH_PERIOD

    def update(self, dt, tilemap, other_tanks, bullets, player, effects=None,
               base_pos=None, target_priority="player"):
        if self.dead:
            return
        self.update_cooldown(dt)
        # 红闪敌人：维持闪烁（draw_tank 看 flashing_time > 0 决定是否叠白膜）
        if self.is_powerup_carrier:
            self.flashing_time = POWERUP_CARRIER_FLASH_PERIOD
        if self.frozen:
            # 被冻结：不动、不开火
            return
        self.update_snap(dt)
        if self.born_invuln > 0:
            self.born_invuln -= dt
            self.flashing_time = self.born_invuln

        self._next_dir_time -= dt
        self._next_fire_time -= dt

        # 决定目标方向
        target_dir = self._choose_target_dir(tilemap, player, base_pos,
                                             target_priority)

        if self._next_dir_time <= 0:
            # 选择新方向
            if target_dir and random.random() < 0.55:
                new_dir = target_dir
            else:
                new_dir = random.choice(Dir.ALL)
            if self.try_change_direction(new_dir, tilemap, other_tanks):
                self._last_dir = new_dir
            else:
                for _ in range(3):
                    alt = random.choice(Dir.ALL)
                    if self.try_change_direction(alt, tilemap, other_tanks):
                        self._last_dir = alt
                        break
            self._next_dir_time = random.uniform(0.8, 1.6)

        # 移动
        moved = self.try_move(dt, self.dir[0] * self.speed * dt,
                               self.dir[1] * self.speed * dt,
                               tilemap, other_tanks)
        if not moved:
            self._next_dir_time = 0.0

        # 射击
        if self._next_fire_time <= 0:
            if self.can_shoot():
                self.shoot(bullets, effects=effects)
            # tier 1 开火更频繁
            mn, mx = TIER_FIRE_COOLDOWN.get(self.tier, (0.8, 1.6))
            self._next_fire_time = random.uniform(mn, mx)

    def _choose_target_dir(self, tilemap, player, base_pos, priority):
        """根据优先级选择目标方向。"""
        targets = []
        if priority == "base" and base_pos is not None:
            targets.append(base_pos)
        if player is not None and not player.dead:
            targets.append(player.rect.center)
        if priority == "player" and base_pos is not None:
            targets.append(base_pos)
        for target in targets:
            d = self._dir_to_target(tilemap, target)
            if d is not None:
                return d
        return None

    def _dir_to_target(self, tilemap, target_center):
        """如果目标在直线上无墙阻挡，返回应转向的方向。"""
        if target_center is None:
            return None
        if not line_of_sight(self.rect.center, target_center, tilemap):
            return None
        ex, ey = self.rect.center
        tx, ty = target_center
        if ex == tx:
            return Dir.DOWN if ty > ey else Dir.UP
        if ey == ty:
            return Dir.RIGHT if tx > ex else Dir.LEFT
        return None

    def on_hit(self, bullet):
        if self.born_invuln > 0:
            return
        self.hit_flash_time = 0.3
        super().on_hit(bullet)
