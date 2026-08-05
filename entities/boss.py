"""C2 BOSS 实体 (F5 BOSS 关卡).

特性:
- 继承 Tank 基类, hp=BOSS_HP (默认 10)
- 子弹能破钢墙 (breaks_steel=True, 路线图 §3.1)
- 比普通敌人慢 (BOSS_SPEED=60, 普通 72)
- 行为简化: 朝最近存活玩家直线移动 + 周期性开火
- hp 减到 0 才死 (走 Tank.on_hit 减血路径)

设计决策 (按 karpathy Simplicity):
- 不分多阶段 (路线图 §7 风险建议暴露 BOSS_HP 常量, 调平衡即可)
- 不分多 BOSS
- 简单 AI: 朝最近玩家方向移动 + 1.5s 冷却开火
- 触发关卡完成: level.update 检测 BOSS 全死 -> completed
"""
from settings import (
    BOSS_HP, BOSS_SPEED, BOSS_FIRE_COOLDOWN, BOSS_COLOR, Dir,
)
from entities.tank import Tank


class BossTank(Tank):
    """BOSS 坦克 - 高血量能破钢墙."""

    # 覆盖基类的开火冷却
    FIRE_COOLDOWN = BOSS_FIRE_COOLDOWN

    def __init__(self, x, y, color=None, dark_color=None):
        """x, y: 出生世界坐标 (像素). 颜色默认 BOSS_COLOR."""
        if color is None:
            color = BOSS_COLOR
        if dark_color is None:
            dark_color = tuple(max(0, int(c * 0.6)) for c in color)
        # BOSS 朝下 (默认向玩家方向)
        super().__init__(x, y, Dir.DOWN, color, dark_color, speed=BOSS_SPEED)
        # C2: 多血
        self.hp = BOSS_HP
        # BOSS 子弹能破钢墙
        self.breaks_steel = True
        # 不闪红出生 (BOSS 一直显眼)
        self.flashing_time = 0.0
        # level.update 末尾 publish ENTITY_KILLED 用, 默认 False (与 EnemyTank 一致)
        self.is_powerup_carrier = False

    def update(self, dt, tilemap, other_tanks, bullets, player,
               effects=None, base_pos=None, target_priority="player"):
        """BOSS 简化 AI: 周期性朝 dir 方向开火 + 缓慢直线移动.

        BOSS 不做方向智能 (不像 EnemyTank 用 _choose_target_dir),
        简化: 默认 dir 不变, 玩家可以预测子弹方向.
        签名跟 EnemyTank 对齐 (player 第 5 位), 让 level.py 通用调用.
        """
        if self.dead:
            return
        self.update_cooldown(dt)
        if self.frozen:
            return
        self.update_snap(dt)

        # 移动: 沿 dir 方向 (boss 朝下, 玩家在上方)
        moved = self.try_move(dt, self.dir[0] * self.speed * dt,
                              self.dir[1] * self.speed * dt,
                              tilemap, other_tanks)
        if not moved:
            # 撞墙/坦克: 反弹 (180° 转向, 简单 AI)
            self.dir = (-self.dir[0], -self.dir[1])

        # 射击: cooldown 倒数
        if self.cooldown <= 0 and self.can_shoot():
            self.shoot(bullets, effects=effects)
        # self.cooldown 已在 shoot 内重置为 FIRE_COOLDOWN
