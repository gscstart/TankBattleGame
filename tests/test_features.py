"""新功能单元测试：覆盖 6 关数据完整性 + 道具 + AI tier + 视觉反馈 + 音效 + 字体。

原有 15 个测试在 test_smoke.py。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
pygame.init()
pygame.font.init()
pygame.mixer.init()  # 必须在 play 之前

from settings import (SCREEN_W, SCREEN_H, FPS, TILE, GRID_W, GRID_H,
                       PLAYER_LIVES, Dir, MAP_X, MAP_Y, LEVEL_DIFFICULTY)
from world.tilemap import TileMap
from world.levels import (LEVELS, get_level, get_level_difficulty,
                          get_total_levels)
from world.tile import (TileEmpty, TileBrick, TileSteel, TileGrass,
                        TileWater, TileIce, TileBase)
from entities.bullet import Bullet
from entities.tank import Tank
from entities.player import PlayerTank
from entities.enemy import EnemyTank
from entities.effects import MuzzleFlash, Explosion, Particle
from entities.powerup import PowerUp, spawn_random_powerup, ALL_TYPES
from utils.collision import line_of_sight
from utils.sound import play, is_available, set_muted, is_muted

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)
        print("FAIL:", msg)
    else:
        print("OK  :", msg)


def _fake_event(type, key):
    """构造一个假的 pygame.Event。"""
    e = pygame.event.Event(type, {"key": key, "mod": 0, "unicode": "", "scancode": 0})
    return e


def get_font(size, bold=False):
    from game.hud import get_font as _gf
    return _gf(size, bold)


# ---- 1. 关卡数据完整性 ----
print("\n=== Test 1: Level data integrity ===")
check(get_total_levels() == 6, f"6 levels, got {get_total_levels()}")
for i, lvl in enumerate(LEVELS):
    check(len(lvl) == GRID_H, f"level {i+1}: {GRID_H} rows, got {len(lvl)}")
    for r, row in enumerate(lvl):
        check(len(row) == GRID_W, f"level {i+1} row {r}: {GRID_W} cols, got {len(row)}: {row!r}")
    # 至少 1 个基地
    has_base = any("X" in row for row in lvl)
    check(has_base, f"level {i+1}: has base 'X'")
    # 至少 1 个玩家
    has_player = any("P" in row for row in lvl)
    check(has_player, f"level {i+1}: has player 'P'")
    # 敌人出生点：要么在 level data 中标 E，要么使用默认 3 个
    tm = TileMap.from_layout(lvl)
    check(len(tm.enemy_spawns) >= 2, f"level {i+1}: >=2 enemy spawns, got {len(tm.enemy_spawns)}")


# ---- 2. 难度递增 ----
print("\n=== Test 2: Difficulty progression ===")
check(len(LEVEL_DIFFICULTY) == 6, "6 difficulty levels")
for i in range(1, len(LEVEL_DIFFICULTY)):
    prev = LEVEL_DIFFICULTY[i - 1]
    cur = LEVEL_DIFFICULTY[i]
    # 敌人数递增（关 1-3 相同可接受）
    check(cur["enemy_count"] >= prev["enemy_count"],
          f"level {i+1} enemy_count >= previous: {cur['enemy_count']} >= {prev['enemy_count']}")
    # 后 3 关速度递增
    if i >= 3:
        check(cur["enemy_speed"] > prev["enemy_speed"],
              f"level {i+1} enemy_speed > previous: {cur['enemy_speed']} > {prev['enemy_speed']}")


# ---- 3. 道具系统 ----
print("\n=== Test 3: PowerUp system ===")
pu = PowerUp(100, 100, "star")
check(pu.type == "star", "powerup type set")
check(pu.rect.x == 100 and pu.rect.y == 100, "powerup position set")
check(not pu.dead, "powerup alive on init")
# 12s 寿命
import time as time_module
pu.spawn_time = time_module.time() - 13
pu.update(0.016)
check(pu.dead, "powerup dies after 12s")

# 6 种类型
check(len(ALL_TYPES) == 6, f"6 powerup types: {ALL_TYPES}")
for t in ALL_TYPES:
    check(t in ["star", "grenade", "helmet", "clock", "shovel", "tank"],
          f"valid type: {t}")

# 随机生成
pu = spawn_random_powerup(200, 200)
check(pu.type in ALL_TYPES, "spawn_random_powerup returns valid type")

# 拾取逻辑
pu = PowerUp(200, 200, "star")
level = Level(0, 3, 0) if False else None  # 避免创建 Level（依赖太多）
# 简化：直接测试 rect 碰撞
p = PlayerTank(200, 200)
check(pu.rect.colliderect(p.rect), "powerup collides with player at same position")


# ---- 4. 敌人 AI tier 差异 ----
print("\n=== Test 4: Enemy AI tier behavior ===")
e0 = EnemyTank(100, 100, tier=0)
e1 = EnemyTank(100, 100, tier=1)
e2 = EnemyTank(100, 100, tier=2)
check(not e0.breaks_steel, "tier 0 cannot break steel")
check(not e1.breaks_steel, "tier 1 cannot break steel")
check(e2.breaks_steel, "tier 2 can break steel")
check(e0.speed == 72, f"tier 0 speed = 72, got {e0.speed}")
check(e1.speed == 72, f"tier 1 speed = 72, got {e1.speed}")
check(abs(e2.speed - 90) < 0.1, f"tier 2 speed = 90, got {e2.speed}")
# 出生无敌
check(e0.born_invuln > 0, "tier 0 born invuln > 0")
# 冻结状态字段
check(not e0.frozen, "frozen field exists and defaults to False")


# ---- 5. 子弹破钢墙 ----
print("\n=== Test 5: Bullet breaks steel ===")
# 空地关卡，col=mid, row=5 放钢墙（mid 随 GRID_W 自适应）
_mid = GRID_W // 2
def _empty_with_tile(row, col, ch):
    lay = ["." * GRID_W for _ in range(GRID_H)]
    lay[row] = lay[row][:col] + ch + lay[row][col+1:]
    return lay
layout = _empty_with_tile(5, _mid, "S")
tilemap = TileMap.from_layout(layout)
# 不能破的子弹
b_normal = Bullet(MAP_X + _mid * TILE, MAP_Y + 5 * TILE + TILE, Dir.UP, "player")
for _ in range(int(FPS * 0.5)):
    b_normal.update(1/60, tilemap, [b_normal], [], lambda t: None)
    if b_normal.dead: break
check(b_normal.dead, "normal bullet consumed by steel")
check(isinstance(tilemap.tiles[5][_mid], TileSteel), "steel intact after normal bullet")

# 能破的子弹（直接设 can_break_steel）
b_strong = Bullet(MAP_X + _mid * TILE, MAP_Y + 5 * TILE + TILE, Dir.UP, "player")
b_strong.can_break_steel = True
for _ in range(int(FPS * 0.5)):
    b_strong.update(1/60, tilemap, [b_strong], [], lambda t: None)
    if b_strong.dead: break
check(b_strong.dead, "strong bullet consumed")
check(not isinstance(tilemap.tiles[5][_mid], TileSteel), "steel destroyed by strong bullet")

# 玩家升级到 2 级后子弹能破钢墙
tilemap2 = TileMap.from_layout(layout)
p = PlayerTank(MAP_X + _mid*TILE, MAP_Y + 7*TILE)
p.upgrade_level = 2
p_bullets = []
p.shoot(p_bullets)  # 玩家开火，upgrade_level=2 应让 can_break_steel=True
check(p_bullets[-1].can_break_steel, "player level 2 bullet can_break_steel = True")
# 玩家升级 0 级时不能破
p0 = PlayerTank(MAP_X + _mid*TILE, MAP_Y + 7*TILE)
p0_bullets = []
p0.shoot(p0_bullets)
check(not p0_bullets[-1].can_break_steel, "player level 0 bullet cannot break steel")


# ---- 6. line_of_sight 公共函数 ----
print("\n=== Test 6: line_of_sight() ===")
# 空旷关卡
layout = ["." * GRID_W for _ in range(GRID_H)]
tilemap = TileMap.from_layout(layout)
_m = GRID_W // 2  # 中列
# 在地图区域内取点（沿垂直线）
check(line_of_sight((MAP_X + _m*TILE + TILE//2, MAP_Y + 0),
                    (MAP_X + _m*TILE + TILE//2, MAP_Y + (GRID_H-1)*TILE),
                    tilemap), "vertical sight clear")
check(line_of_sight((MAP_X + 0, MAP_Y + _m*TILE + TILE//2),
                    (MAP_X + (GRID_W-1)*TILE, MAP_Y + _m*TILE + TILE//2),
                    tilemap), "horizontal sight clear")
check(not line_of_sight((MAP_X + _m*TILE, MAP_Y + _m*TILE),
                        (MAP_X + (_m+2)*TILE, MAP_Y + (_m+2)*TILE),
                        tilemap), "diagonal returns False")
# 有砖块阻挡
layout[5] = layout[5][:_m] + "B" + layout[5][_m+1:]
tilemap = TileMap.from_layout(layout)
check(not line_of_sight((MAP_X + _m*TILE + TILE//2, MAP_Y + 0),
                         (MAP_X + _m*TILE + TILE//2, MAP_Y + (GRID_H-1)*TILE),
                         tilemap), "brick blocks sight")


# ---- 7. MuzzleFlash / Explosion ----
print("\n=== Test 7: Effects lifecycle ===")
fx = MuzzleFlash(100, 100, Dir.UP, (255, 200, 100))
check(not fx.dead, "MuzzleFlash alive on init")
fx.update(0.5)  # 远超 0.1s 寿命
check(fx.dead, "MuzzleFlash dies after 0.1s")

exp = Explosion(100, 100, big=True)
check(len(exp.particles) == 14, f"Explosion big: 14 particles, got {len(exp.particles)}")
exp.update(2.0)  # 远超寿命
check(exp.dead, "Explosion dies after particles fade")
check(len(exp.particles) == 0, "All particles removed after explosion dies")

# Particle 物理
p = Particle(0, 0, 100, 0, (255, 0, 0), 1.0)
p.update(0.5)
check(p.x > 0, f"Particle moves: x={p.x}")


# ---- 8. 子弹拖尾 ----
print("\n=== Test 8: Bullet trail ===")
b = Bullet(100, 100, Dir.UP, "player")
tilemap = TileMap.from_layout(["." * GRID_W for _ in range(GRID_H)])
for _ in range(10):
    b.update(1/60, tilemap, [b], [], lambda t: None)
    if b.dead: break
check(len(b.trail) <= 6, f"trail capped at 6, got {len(b.trail)}")
check(len(b.trail) > 0, f"trail populated: {len(b.trail)}")


# ---- 9. 软吸附 ----
print("\n=== Test 9: Soft snap ===")
t = Tank(100, 100, Dir.DOWN, (200, 200, 200), (100, 100, 100))
# 把坦克放到非格点位置
t.rect.x = MAP_X + 5 * TILE + 14
t.try_change_direction(Dir.RIGHT, tilemap, [])
check(t.snap_axis is not None, f"snap_axis set: {t.snap_axis}")
# 跑足够时间，吸附完成
for _ in range(20):
    t.update_snap(1/60)
check(t.snap_axis is None, f"snap_axis cleared: {t.snap_axis}")


# ---- 10. 履带 phase 累加 ----
print("\n=== Test 10: Tread phase ===")
t = Tank(MAP_X + 6*TILE, MAP_Y + 6*TILE, Dir.UP, (200, 200, 200), (100, 100, 100))
t.try_change_direction(Dir.UP, tilemap, [])
phase0 = t.tread_phase
for _ in range(10):
    t.try_move(1/60, 0, -5, tilemap, [])
check(t.tread_phase > phase0, f"tread_phase increased: {phase0} -> {t.tread_phase}")


# ---- 11. 方向优先级 ----
print("\n=== Test 11: Direction priority ===")
p = PlayerTank(MAP_X + 6*TILE, MAP_Y + 6*TILE)
# 模拟按 W
p.handle_event(_fake_event(pygame.KEYDOWN, pygame.K_w))
check(p.keys["up"], "up key tracked")
# 模拟按 D (更新 press_time)
p._time = 0.5
p.handle_event(_fake_event(pygame.KEYDOWN, pygame.K_d))
check(p.key_press_time["right"] > p.key_press_time["up"], "right pressed later")
# _active_direction 应返回 D
active = p._active_direction()
check(active == Dir.RIGHT, f"active dir = RIGHT (most recent), got {active}")


# ---- 12. 惯性滑行 ----
print("\n=== Test 12: Inertia/slide ===")
p = PlayerTank(MAP_X + 6*TILE, MAP_Y + 6*TILE)
p.keys["up"] = True
p._time += 0.016
bullets = []
p.update(0.1, tilemap, [], bullets, effects=[])
check(p.slide_timer > 0, f"slide_timer set: {p.slide_timer}")
# 松开键后 0.1s 内仍移动
p.keys["up"] = False
p._time += 0.016
prev_y = p.rect.y
p.update(0.05, tilemap, [], bullets, effects=[])
check(p.rect.y < prev_y or p.slide_timer > 0, "inertia continues after release")


# ---- 13. CJK 字体检测 ----
print("\n=== Test 13: CJK font detection ===")
from game.hud import _find_cjk_font
font_name = _find_cjk_font()
check(font_name is not None, f"Found CJK font: {font_name}")
# 测试中文渲染
f = get_font(20, True)
s = f.render("坦克大战", True, (255, 255, 255))
check(s.get_width() > 30, f"Chinese text renders, width={s.get_width()}")


# ---- 14. 音效 ----
print("\n=== Test 14: Sound system ===")
check(is_available(), "Sound system available")
set_muted(True)
check(is_muted(), "Muted state set")
play("fire")  # 不应抛错
set_muted(False)
play("fire")
play("explosion")
play("hit")
play("start")
print("OK  : play() all 4 sounds without error")


# ---- 15. 玩家 is_player 标记 ----
print("\n=== Test 15: is_player flag ===")
p = PlayerTank(100, 100)
e = EnemyTank(100, 100)
check(p.is_player, "PlayerTank.is_player = True")
check(not e.is_player, "EnemyTank.is_player = False")
# shoot 不再用 __import__
p_bullets, e_bullets = [], []
b1 = p.shoot(p_bullets)
b2 = e.shoot(e_bullets)
check(b1.owner == "player", f"player bullet owner = 'player', got {b1.owner}")
check(b2.owner == "enemy", f"enemy bullet owner = 'enemy', got {b2.owner}")


def _fake_event(type, key):
    """构造一个假的 pygame.Event。"""
    e = pygame.event.Event(type, {"key": key, "mod": 0, "unicode": "", "scancode": 0})
    return e


# ---- 总结 ----
print("\n" + "=" * 50)
if errors:
    print(f"FAILED: {len(errors)} test(s)")
    for e in errors:
        print("  -", e)
else:
    print("ALL FEATURE TESTS PASSED ✓")
print("=" * 50)

# ---- 16. Bug 修复回归测试 ----
print("\n=== Test 16: Bug fix regression ===")

# #2: shovel 倒计时
from game.level import Level
shovel_lvl = Level(0, 3, 0)
shovel_lvl._activate_shovel(2.0)
check(shovel_lvl._shovel_timer == 2.0, f"shovel timer set: {shovel_lvl._shovel_timer}")
# 跑 1.5s，timer 应剩 0.5s
for _ in range(int(60 * 1.5)):
    shovel_lvl.update(1/60)
check(shovel_lvl._shovel_timer < 1.0 and shovel_lvl._shovel_timer > 0,
      f"shovel timer ticks down: {shovel_lvl._shovel_timer}")
# 再跑 1s，应到时复原
for _ in range(int(60 * 1.0)):
    shovel_lvl.update(1/60)
check(shovel_lvl._shovel_backup is None, "shovel backup cleared after timer expires")

# #3: 重生保留道具状态
respawn_lvl = Level(0, 3, 0)
respawn_lvl.player.upgrade_level = 2
respawn_lvl.player.invincible = 5.0
respawn_lvl.player.frozen_enemies_timer = 6.0
respawn_lvl.player.dead = True
respawn_lvl._death_timer = 0.05
respawn_lvl.update(0.1)
check(respawn_lvl.player.upgrade_level == 2, f"upgrade_level preserved: {respawn_lvl.player.upgrade_level}")
check(respawn_lvl.player.invincible > 0, f"invincible preserved: {respawn_lvl.player.invincible}")
# frozen_enemies_timer 在 update 中会正常递减（设计如此），0.1s 后应剩约 5.9s
check(5.0 < respawn_lvl.player.frozen_enemies_timer <= 6.0,
      f"frozen_enemies_timer preserved (5.x s after 0.1s): {respawn_lvl.player.frozen_enemies_timer}")

# #5: grenade 不双重计分
from entities.enemy import EnemyTank
grenade_lvl = Level(0, 3, 0)
# 强制 3 个敌人
for i in range(3):
    e = EnemyTank(grenade_lvl.tilemap.grid_to_world(0, 0)[0] + i*100,
                  grenade_lvl.tilemap.grid_to_world(0, 0)[1], tier=0)
    e.born_invuln = 0
    grenade_lvl.enemies.append(e)
grenade_lvl.effects = []
initial_score = grenade_lvl.score
from entities.powerup import PowerUp
pu = PowerUp(0, 0, "grenade")
grenade_lvl._apply_powerup(pu)
score_after_apply = grenade_lvl.score
# 跑几帧让清理循环执行
for _ in range(5):
    grenade_lvl.update(1/60)
score_final = grenade_lvl.score
check(score_final - initial_score == 300, f"grenade awards 300 once (3 enemies * 100), got {score_final - initial_score}")

# #4: 关卡自定义 E 出生点（17×17：关 6 E 在 (0,1) 和 (16,1)）
from world.levels import LEVEL_6
from world.tilemap import TileMap
tm6 = TileMap.from_layout(LEVEL_6)
check((0, 1) in tm6.enemy_spawns, f"Level 6 has (0, 1) spawn: {tm6.enemy_spawns}")
check((GRID_W - 1, 1) in tm6.enemy_spawns, f"Level 6 has ({GRID_W-1}, 1) spawn: {tm6.enemy_spawns}")
check(len(tm6.enemy_spawns) == 2, f"Level 6 has 2 spawns: {tm6.enemy_spawns}")

# #7: 尸体不挡 spawn
spawn_lvl = Level(0, 3, 0)
spawn_lvl.enemies_to_spawn = 5
spawn_lvl._spawn_timer = 0.0
# 手动放一个"死亡"敌人在第一个出生点
from settings import TILE
x, y = spawn_lvl.tilemap.grid_to_world(*spawn_lvl.tilemap.enemy_spawns[0])
dead_e = EnemyTank(x, y, tier=0)
dead_e.dead = True
spawn_lvl.enemies.append(dead_e)
# 调用 _spawn_enemy
spawn_lvl._spawn_idx = 0
result = spawn_lvl._spawn_enemy()
check(result is not None, f"spawn succeeds even with dead enemy at spawn point: {result}")

# #8: 匿名 TileEmpty 替换为真实类
from world.tile import TileEmpty
check(TileEmpty.__name__ == "TileEmpty", "TileEmpty is a real class")
# 再触发钢墙破坏
_m8 = GRID_W // 2
tm8 = TileMap.from_layout(["." * GRID_W for _ in range(GRID_H)])
tm8.tiles[5][_m8] = TileSteel()
from entities.bullet import Bullet
b8 = Bullet(MAP_X + _m8*TILE, MAP_Y + 6*TILE + TILE, Dir.UP, "player")
b8.can_break_steel = True
for _ in range(int(FPS * 0.5)):
    b8.update(1/60, tm8, [b8], [], lambda t: None)
    if b8.dead: break
check(isinstance(tm8.tiles[5][_m8], TileEmpty),
      f"after steel-break, tile is real TileEmpty: {type(tm8.tiles[5][_m8]).__name__}")

# #9: 玩家冷却用 PLAYER_FIRE_COOLDOWN
from settings import PLAYER_FIRE_COOLDOWN
p9 = PlayerTank(0, 0)
p9_bullets = []
p9.shoot(p9_bullets)
check(p9.cooldown == PLAYER_FIRE_COOLDOWN,
      f"player cooldown = PLAYER_FIRE_COOLDOWN ({PLAYER_FIRE_COOLDOWN}): got {p9.cooldown}")

# #10: 道具不同音效
from game.level import POWERUP_SOUND
check(len(POWERUP_SOUND) == 6, f"6 powerup sounds: {len(POWERUP_SOUND)}")
# 至少 2 种不同音效被使用
check(len(set(POWERUP_SOUND.values())) >= 2,
      f"powerups use >=2 distinct sounds: {set(POWERUP_SOUND.values())}")


print("\n" + "=" * 50)
if errors:
    print(f"FAILED: {len(errors)} test(s)")
    for e in errors:
        print("  -", e)
    exit(1)
else:
    print("ALL FEATURE TESTS PASSED ✓ (including regression tests)")
print("=" * 50)

pygame.quit()
