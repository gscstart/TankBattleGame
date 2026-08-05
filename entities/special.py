"""C3 特殊敌人 5 种 (路线图 §6 阶段 C - F18).

设计原则 (按 karpathy Simplicity):
- 5 个 EnemyTank 子类, 每个只覆写差异点
- 颜色/行为参数全部从 settings 读取, 方便平衡
- 不引入新基类, 不破坏 A 阶段架构

类型:
1. SuicideEnemy 自爆者 - 靠近玩家 80px 自爆, 半径 64px 敌人同死
2. StealthEnemy 隐形者 - 周期 2s 显形 0.3s, 隐行期不画
3. ArmorEnemy 装甲者 - hp=3 (普通 1)
4. RocketEnemy 火箭者 - 子弹 2x 速 + 破钢墙
5. BounceEnemy 弹跳者 - 子弹打墙反弹 1 次

Bullet 配套改造 (entities/bullet.py):
- bounces_left: 弹跳剩余次数
- speed_multiplier: 子弹速度倍率 (火箭 2.0)
"""
import math
import pygame
from settings import (
    SPECIAL_COLORS, SUICIDE_BLAST_TRIGGER_RADIUS, SUICIDE_BLAST_DAMAGE_RADIUS,
    STEALTH_CYCLE, STEALTH_VISIBLE_FRAC, ARMOR_HP, ROCKET_SPEED_MULT, BOUNCE_COUNT,
)
from entities.enemy import EnemyTank
from entities.bullet import Bullet
from utils import events


def _make_dark(color):
    """按 color 计算 dark_color (主色 * 0.6)."""
    return tuple(max(0, int(c * 0.6)) for c in color)


# === 1. 自爆者 ===
class SuicideEnemy(EnemyTank):
    """靠近玩家触发自爆, 自身 + 半径内敌人同死."""

    def __init__(self, x, y, tier=0, enemy_speed=None, is_powerup_carrier=False):
        color = SPECIAL_COLORS["suicide"]
        super().__init__(x, y, tier=tier, enemy_speed=enemy_speed,
                         is_powerup_carrier=is_powerup_carrier)
        # 强制覆盖颜色
        self.color = color
        self.dark_color = _make_dark(color)

    def update(self, dt, tilemap, other_tanks, bullets, player, effects=None,
               base_pos=None, target_priority="player"):
        # 先按父类走完整 AI
        super().update(dt, tilemap, other_tanks, bullets, player, effects=effects,
                       base_pos=base_pos, target_priority=target_priority)
        if self.dead:
            return
        # 检查自爆触发条件: 玩家存活 + 距离 < 触发半径
        if player is None or player.dead:
            return
        dx = self.rect.centerx - player.rect.centerx
        dy = self.rect.centery - player.rect.centery
        if dx * dx + dy * dy < SUICIDE_BLAST_TRIGGER_RADIUS ** 2:
            self._detonate(tilemap, other_tanks, effects)

    def _detonate(self, tilemap, other_tanks, effects):
        """自爆: 自身死 + 半径内敌人死 + Explosion 视觉.

        自杀式不重复计分: self.killed_by_powerup=True 让 level.update 末尾的
        "清理死亡"块跳过自爆者 (避免重复加分 + 重复 publish ENTITY_KILLED).
        范围 64px 内其他敌人仍按"玩家击杀"走正常路径 (计分 + 事件).
        """
        self.dead = True
        self.hit_flash_time = 0.0
        self.killed_by_powerup = True  # C3 review: 避免 level 重复计分/发事件
        # 范围内其他敌人死 (走 level 正常 "玩家击杀" 路径)
        cx, cy = self.rect.center
        for other in other_tanks:
            if other is self or other.dead:
                continue
            odx = other.rect.centerx - cx
            ody = other.rect.centery - cy
            if odx * odx + ody * ody < SUICIDE_BLAST_DAMAGE_RADIUS ** 2:
                other.dead = True
                other.hit_flash_time = 0.3
        # 大爆炸视觉
        if effects is not None:
            from entities.effects import Explosion
            effects.append(Explosion(cx, cy, big=True))
        # 音效
        from utils.sound import play
        play("explosion")
        # 事件 (自己发一次, owner=powerup 表示"被自爆者波及", 不计分)
        events.publish(events.ENTITY_KILLED, kind="enemy", owner="powerup",
                       x=cx, y=cy, score_delta=0)


# === 2. 隐形者 ===
class StealthEnemy(EnemyTank):
    """周期显形/隐行. 隐行期 draw() 不画 (被子弹仍正常受击)."""

    def __init__(self, x, y, tier=0, enemy_speed=None, is_powerup_carrier=False):
        color = SPECIAL_COLORS["stealth"]
        super().__init__(x, y, tier=tier, enemy_speed=enemy_speed,
                         is_powerup_carrier=is_powerup_carrier)
        # 强制覆盖颜色 (避免被 tier/is_powerup_carrier 覆盖)
        self.color = color
        self.dark_color = _make_dark(color)
        # 显形/隐行状态
        self.stealth_phase = 0.0
        self._init_stealth_phase()

    def _init_stealth_phase(self):
        # 初始时随机相位, 避免一群隐形敌人同步显形
        import random
        self.stealth_phase = random.uniform(0.0, STEALTH_CYCLE)

    @property
    def is_visible(self) -> bool:
        """当前是否在显形期."""
        return (self.stealth_phase % STEALTH_CYCLE) < (STEALTH_CYCLE * STEALTH_VISIBLE_FRAC)

    def update(self, dt, tilemap, other_tanks, bullets, player, effects=None,
               base_pos=None, target_priority="player"):
        super().update(dt, tilemap, other_tanks, bullets, player, effects=effects,
                       base_pos=base_pos, target_priority=target_priority)
        if not self.dead:
            self.stealth_phase = (self.stealth_phase + dt) % (STEALTH_CYCLE * 100)

    def draw(self, surface: pygame.Surface):
        if not self.is_visible:
            return  # C3: 隐行期不画
        super().draw(surface)


# === 3. 装甲者 ===
class ArmorEnemy(EnemyTank):
    """hp=3 (普通敌人 hp=1). 其他行为与普通敌人一致."""

    def __init__(self, x, y, tier=0, enemy_speed=None, is_powerup_carrier=False):
        color = SPECIAL_COLORS["armor"]
        super().__init__(x, y, tier=tier, enemy_speed=enemy_speed,
                         is_powerup_carrier=is_powerup_carrier)
        # 强制覆盖颜色
        self.color = color
        self.dark_color = _make_dark(color)
        # C3: 多血
        self.hp = ARMOR_HP


# === 4. 火箭者 ===
class RocketEnemy(EnemyTank):
    """子弹 2x 速 + 破钢墙."""

    def __init__(self, x, y, tier=0, enemy_speed=None, is_powerup_carrier=False):
        color = SPECIAL_COLORS["rocket"]
        super().__init__(x, y, tier=tier, enemy_speed=enemy_speed,
                         is_powerup_carrier=is_powerup_carrier)
        # 强制覆盖颜色
        self.color = color
        self.dark_color = _make_dark(color)
        # 子弹加速
        self.rocket_speed_mult = ROCKET_SPEED_MULT

    def shoot(self, bullets, effects=None):
        """覆写 shoot 让子弹加速 + 破钢墙."""
        # 先调父类 shoot 生成 bullet
        # 重用 EnemyTank 没用覆写, 走 Tank.shoot
        bullet = super().shoot(bullets, effects=effects)
        if bullet is not None:
            bullet.speed_multiplier = self.rocket_speed_mult
            bullet.can_break_steel = True
        return bullet


# === 5. 弹跳者 ===
class BounceEnemy(EnemyTank):
    """子弹打墙反弹 1 次."""

    def __init__(self, x, y, tier=0, enemy_speed=None, is_powerup_carrier=False):
        color = SPECIAL_COLORS["bounce"]
        super().__init__(x, y, tier=tier, enemy_speed=enemy_speed,
                         is_powerup_carrier=is_powerup_carrier)
        # 强制覆盖颜色
        self.color = color
        self.dark_color = _make_dark(color)

    def shoot(self, bullets, effects=None):
        bullet = super().shoot(bullets, effects=effects)
        if bullet is not None:
            bullet.bounces_left = BOUNCE_COUNT
        return bullet


# === 工厂 ===
SPECIAL_ENEMY_CLASSES = [
    SuicideEnemy,
    StealthEnemy,
    ArmorEnemy,
    RocketEnemy,
    BounceEnemy,
]
