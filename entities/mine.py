"""地雷实体 (B4: F7 道具扩展).

特性:
- 玩家拾取 'mine' 道具时在玩家位置前/中/后放 3 颗
- 地雷静止不动, 存在 LIFETIME 秒
- 敌人(包括坦克)碰触时爆炸, 100px AOE 范围所有敌人死亡
- 友军(玩家/玩家子弹)不受影响
- 爆炸效果: 一次性 Explosion 特判 + ENTITY_KILLED 事件
"""
import time
import math
import pygame
from settings import TILE, MINE_BLAST_RADIUS, SCORE_PER_ENEMY


class Mine:
    """单颗地雷."""

    LIFETIME = 15.0  # 地雷存活时间 (秒)

    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(int(x), int(y), TILE, TILE)
        self.spawn_time = time.time()
        self.dead = False
        self._blasted = False  # 防止一帧内重复爆炸 (AOE 多敌人)

    def update(self, dt: float, enemies: list, effects: list, events_mod) -> int:
        """检查敌人碰撞. 返回本帧 AOE 击杀数 (0 = 没爆炸, N = 杀了 N 个).

        Level.update 用返回值累加 self.score (与 grenade 一致).
        enemies: 当前所有 enemies 列表
        effects: Level.effects (追加 Explosion)
        events_mod: utils.events 模块 (发 ENTITY_KILLED 事件)
        """
        if self.dead or self._blasted:
            return 0
        # LIFETIME 到期自动消失
        if time.time() - self.spawn_time > self.LIFETIME:
            self.dead = True
            return 0
        # 敌人碰触检测
        for e in enemies:
            if e.dead or getattr(e, 'born_invuln', 0) > 0:
                continue
            if self.rect.colliderect(e.rect):
                # 触发的敌人先标记 dead, 避免 AOE 重复计分
                e.dead = True
                e.killed_by_powerup = True
                e.hit_flash_time = 0.3
                events_mod.publish(events_mod.ENTITY_KILLED, kind="enemy",
                                   owner="powerup", x=e.rect.centerx,
                                   y=e.rect.centery,
                                   score_delta=SCORE_PER_ENEMY)
                return self._blast(enemies, effects, events_mod)
        return 0

    def _blast(self, enemies, effects, events_mod) -> int:
        """AOE 爆炸, 范围内除已计的触发敌人外其他敌人死亡. 返回击杀数(含触发).

        触发敌人已在 update() 中计分 + 设 dead, 不会被此函数再次计入.
        """
        from entities.effects import Explosion
        self._blasted = True
        self.dead = True
        cx, cy = self.rect.centerx, self.rect.centery
        # 主爆炸特效 (大)
        effects.append(Explosion(cx, cy, big=True))
        # AOE 内剩余敌人死亡 (触发敌人已 dead, 跳过)
        kill_count = 1  # 触发敌人已计 1 个
        for e in enemies:
            if e.dead:
                continue
            ex, ey = e.rect.center
            if (ex - cx) ** 2 + (ey - cy) ** 2 <= MINE_BLAST_RADIUS ** 2:
                e.dead = True
                e.killed_by_powerup = True  # 避免下帧重复计分
                e.hit_flash_time = 0.3
                # 小爆炸特效
                effects.append(Explosion(ex, ey))
                events_mod.publish(events_mod.ENTITY_KILLED, kind="enemy",
                                   owner="powerup", x=ex, y=ey,
                                   score_delta=SCORE_PER_ENEMY)
                kill_count += 1
        return kill_count

    def draw(self, surface: pygame.Surface):
        if self.dead:
            return
        x, y, w, h = self.rect.x, self.rect.y, self.rect.w, self.rect.h
        cx, cy = x + w // 2, y + h // 2
        # 主体 (球)
        pygame.draw.circle(surface, (60, 60, 60), (cx, cy + 2), 11)
        pygame.draw.circle(surface, (140, 70, 50), (cx, cy + 2), 11, 2)
        # 4 个圆点 (地雷标志)
        for angle in (0, 90, 180, 270):
            rad = math.radians(angle)
            dx = int(7 * math.cos(rad))
            dy = int(7 * math.sin(rad))
            pygame.draw.circle(surface, (220, 220, 220), (cx + dx, cy + 2 + dy), 2)
        # 引线
        pygame.draw.line(surface, (200, 200, 200), (cx, cy - 9), (cx + 4, cy - 14), 2)
        # 闪烁火花 (越接近 LIFETIME 末越快闪)
        elapsed = time.time() - self.spawn_time
        if int(elapsed * 4) % 2 == 0:
            pygame.draw.circle(surface, (255, 200, 80), (cx + 4, cy - 14), 3)


def spawn_mines_around(player, count: int = 3) -> list:
    """在玩家位置前/中/后 1 格 (沿朝向方向) 放 count 颗地雷.

    count=3: 前 1, 中 (玩家当前格), 后 1.
    count=1: 仅玩家当前格.
    """
    cx, cy = player.rect.centerx, player.rect.centery
    dx, dy = player.dir
    mines = []
    if count == 1:
        offsets = [(0, 0)]
    elif count == 3:
        offsets = [(0, 0), (dx, dy), (-dx, -dy)]
    else:
        # 一般情况: 中 + (count-1)/2 前 + (count-1)/2 后
        offsets = [(0, 0)]
        for i in range(1, count // 2 + 1):
            offsets.append((dx * i, dy * i))
            offsets.append((-dx * i, -dy * i))
    for ox, oy in offsets:
        mx = cx + ox * TILE - TILE // 2
        my = cy + oy * TILE - TILE // 2
        mines.append(Mine(mx, my))
    return mines
