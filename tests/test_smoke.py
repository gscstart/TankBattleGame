"""端到端逻辑测试：实例化关卡、模拟运行、检测关键行为。

注意：测试使用简化关卡布局（无墙壁），确保子弹/坦克能稳定到达目标。
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
pygame.init()

from settings import (SCREEN_W, SCREEN_H, FPS, TILE, GRID_W, GRID_H,
                       PLAYER_LIVES, ENEMIES_PER_LEVEL, MAX_ENEMIES_ON_SCREEN,
                       Dir, BULLET_SPEED, PLAYER_SPEED, MAP_X, MAP_Y)
from world.tilemap import TileMap
from world.tile import TileEmpty, TileBase
from world.levels import LEVELS
from game.level import Level
from game.hud import draw_hud
from game.menu import (draw_menu, draw_pause, draw_level_complete,
                       draw_game_over)
from entities.bullet import Bullet
import utils.collision as coll
import world.tile as wt
import entities.enemy as ee

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)
        print("FAIL:", msg)
    else:
        print("OK  :", msg)


def make_empty_level():
    """构建一个空旷的关卡（仅基地 + 玩家 + 3 个出生点），用于隔离测试。

    随 GRID_W/GRID_H 自适应：玩家在底部中央 (col=mid, row=GRID_H-2)，
    基地正下方 (row=GRID_H-1)，敌人在顶部左/中/右。
    """
    layout = ["." * GRID_W for _ in range(GRID_H)]
    mid = GRID_W // 2
    # 玩家在底部中央（基地上方一行）
    layout[GRID_H - 2] = layout[GRID_H - 2][:mid] + "P" + layout[GRID_H - 2][mid + 1:]
    # 基地在玩家正下方
    layout[GRID_H - 1] = layout[GRID_H - 1][:mid] + "X" + layout[GRID_H - 1][mid + 1:]
    assert len(layout[GRID_H - 1]) == GRID_W, f"row len {len(layout[GRID_H-1])}"
    # 3 个敌人在顶部：左 / 中 / 右（与 tilemap 默认出生点一致）
    e_cols = [0, mid, GRID_W - 1]
    row0_chars = list("." * GRID_W)
    for c in e_cols:
        row0_chars[c] = "E"
    layout[0] = "".join(row0_chars)
    assert len(layout[0]) == GRID_W, f"row 0 length {len(layout[0])}: {layout[0]!r}"
    return layout


# 1. 关卡创建（用真实关卡）
print("\n=== Test 1: Level creation ===")
level = Level(0, PLAYER_LIVES, 0)
check(level.tilemap is not None, "tilemap created")
check(level.player is not None, "player spawned")
check(not level.player.dead, "player alive")
check(level.enemies_to_spawn == ENEMIES_PER_LEVEL, f"enemies to spawn = {ENEMIES_PER_LEVEL}")
check(level.lives == PLAYER_LIVES, f"lives = {PLAYER_LIVES}")

# 2. 地图绘制
print("\n=== Test 2: Map drawing ===")
level.tilemap.draw(screen)
level.draw(screen)
pygame.display.flip()
check(True, "map and entities drawn without error")

# 3. HUD
print("\n=== Test 3: HUD ===")
draw_hud(screen, 2, 500, 0, 10, max_lives=PLAYER_LIVES)
pygame.display.flip()
check(True, "HUD drawn")

# 4. 菜单
print("\n=== Test 4: Menu screens ===")
draw_menu(screen, 0.0)
draw_pause(screen)
draw_level_complete(screen, 0, 100, 0.0)
draw_game_over(screen, 500, victory=False, t=0.0)
draw_game_over(screen, 1500, victory=True, t=0.0)
pygame.display.flip()
check(True, "all menu screens drawn")

# 5. 玩家移动 + 子弹
print("\n=== Test 5: Player movement and shooting ===")
level2 = Level(0, PLAYER_LIVES, 0)
start_x, start_y = level2.player.rect.x, level2.player.rect.y
level2.player.keys["up"] = True
level2.player.update(0.1, level2.tilemap, [], level2.bullets)
level2.player.keys["up"] = False
check(level2.player.rect.y < start_y or level2.player.rect.y != start_y,
      f"player moved up: {start_y} -> {level2.player.rect.y}")
check(level2.player.dir == Dir.UP, f"player dir is UP")

level2.player.keys["fire"] = True
level2.player.update(0.1, level2.tilemap, [], level2.bullets)
check(len(level2.bullets) >= 1, f"bullet created: {len(level2.bullets)} bullets")

# 6. 碰撞检测（真实关卡中的砖块）
print("\n=== Test 6: Collision with brick in real level ===")
level3 = Level(0, PLAYER_LIVES, 0)
brick_pos = None
for r in range(GRID_H):
    for c in range(GRID_W):
        if isinstance(level3.tilemap.tiles[r][c], wt.TileBrick):
            brick_pos = (c, r)
            break
    if brick_pos:
        break
check(brick_pos is not None, f"found a brick at {brick_pos}")
col, row = brick_pos
level3.player.rect.x, level3.player.rect.y = level3.tilemap.grid_to_world(col, row)
level3.player.rect.x -= TILE
old_x = level3.player.rect.x
moved = level3.player.try_move(0.1, TILE, 0, level3.tilemap, [])
check(level3.player.rect.x == old_x or not moved, "player blocked by brick")

# 7. 子弹打砖块 - 用空旷关卡，子弹从下方飞到上方命中砖块
print("\n=== Test 7: Bullet destroys brick subcell (clear path) ===")
layout = make_empty_level()
# 在第 5 行 col 6 放一个砖块
layout[5] = layout[5][:6] + "B" + layout[5][7:]
tilemap = TileMap.from_layout(layout)
# 子弹从砖块正下方生成，向上飞
bx, by = tilemap.grid_to_world(6, 5)
bullet = Bullet(bx, by + TILE, Dir.UP, "player")
# 跑若干帧
for _ in range(int(FPS * 0.5)):
    bullet.update(1/60, tilemap, [bullet], [level.player] + [], lambda t: None)
    if bullet.dead:
        break
brick_tile = tilemap.tiles[5][6]
check(isinstance(brick_tile, wt.TileBrick), "still a brick")
check(brick_tile.subtl != 0b1111, f"brick subcell destroyed: subtl={bin(brick_tile.subtl)}")

# 8. 敌人 AI（真实关卡）
print("\n=== Test 8: Enemy AI in real level ===")
level5 = Level(0, PLAYER_LIVES, 0)
level5._spawn_timer = 0.0
for i in range(int(FPS * 3)):
    level5.update(1.0 / FPS)
    if level5.enemies:
        break
check(len(level5.enemies) >= 1, f"enemies spawned: {len(level5.enemies)}")
# 跑更多帧让敌人开火
for i in range(int(FPS * 3)):
    level5.update(1.0 / FPS)
enemy_fired = any(b.owner == "enemy" for b in level5.bullets)
check(enemy_fired, f"enemy fired bullet (bullets: {len(level5.bullets)})")

# 9. 子弹打坦克 - 用空旷关卡确保无障碍
print("\n=== Test 9: Bullet hits tank (clear path) ===")
layout = make_empty_level()
tilemap = TileMap.from_layout(layout)
enemy = ee.EnemyTank(MAP_X + 4*TILE, MAP_Y + 4*TILE, tier=0)
enemy.born_invuln = 0  # 移除出生无敌
enemy.flashing_time = 0
# 玩家位置（远离战场）
player = __import__("entities.player", fromlist=["PlayerTank"]).PlayerTank(MAP_X + 8*TILE, MAP_Y + 8*TILE)
# 在敌人正下方生成向上飞的玩家子弹
b = Bullet(enemy.rect.centerx, enemy.rect.centery + 30, Dir.UP, "player")
bullets = [b]
all_tanks = [player, enemy]
# 跑半秒
for _ in range(int(FPS * 0.5)):
    b.update(1/60, tilemap, bullets, all_tanks, lambda t: None)
    if b.dead:
        break
check(b.dead, f"bullet consumed (dead={b.dead})")
check(enemy.dead, f"enemy killed (dead={enemy.dead})")

# 10. 基地被毁 - 用空旷关卡，子弹从基地正上方
print("\n=== Test 10: Base destruction (clear path) ===")
layout = make_empty_level()
tilemap = TileMap.from_layout(layout)
base_pos = tilemap.base_pos
bx, by = tilemap.grid_to_world(*base_pos)
# 从基地正上方飞下来的子弹
b = Bullet(bx, by - TILE, Dir.DOWN, "enemy")
for _ in range(int(FPS * 0.5)):
    b.update(1/60, tilemap, [b], [], lambda t: None)
    if b.dead:
        break
check(tilemap.base_tile.destroyed, f"base destroyed: {tilemap.base_tile.destroyed}")

# 11. 玩家重生
print("\n=== Test 11: Player respawn ===")
level8 = Level(0, PLAYER_LIVES, 0)
level8.player.dead = True
level8._death_timer = 0.1
level8.update(0.2)
check(level8.player is not None and not level8.player.dead, "player respawned")
check(level8.lives == PLAYER_LIVES - 1, f"lives decremented: {level8.lives}")

# 12. 关卡切换
print("\n=== Test 12: Level transition ===")
level9 = Level(0, PLAYER_LIVES, 0)
level9.enemies_to_spawn = 0
level9.enemies = []
level9.update(0.1)
check(level9.completed, "level marked completed")
from game.game import Game
g = Game.__new__(Game)
g.level = level9
g.level_index = 0
g.score = 1000
g.lives = 3
import settings as S
g.state = S.State.LEVEL_COMPLETE
g.state_time = 3.0
g.next_level()
check(g.state == S.State.PLAYING, f"game state = PLAYING: {g.state}")
check(g.level_index == 1, f"level index advanced: {g.level_index}")

# 13. 钢墙不能被普通子弹打坏
print("\n=== Test 13: Steel wall blocks bullets ===")
layout = make_empty_level()
layout[5] = layout[5][:6] + "S" + layout[5][7:]
tilemap = TileMap.from_layout(layout)
bx, by = tilemap.grid_to_world(6, 5)
b = Bullet(bx, by + TILE, Dir.UP, "player")
for _ in range(int(FPS * 0.5)):
    b.update(1/60, tilemap, [b], [], lambda t: None)
    if b.dead:
        break
check(b.dead, "bullet consumed by steel")
steel = tilemap.tiles[5][6]
check(isinstance(steel, wt.TileSteel) and not getattr(steel, "destroyed", False),
      "steel still intact")

# 14. 水域阻挡坦克
print("\n=== Test 14: Water blocks tanks ===")
layout = make_empty_level()
layout[5] = layout[5][:6] + "W" + layout[5][7:]
tilemap = TileMap.from_layout(layout)
player = __import__("entities.player", fromlist=["PlayerTank"]).PlayerTank(MAP_X + 6*TILE, MAP_Y + 6*TILE)
# 移动玩家到水域下面
player.rect.x, player.rect.y = MAP_X + 6*TILE, MAP_Y + 6*TILE
# 尝试向上进入水域
old_y = player.rect.y
player.try_change_direction(Dir.UP, tilemap, [])
moved = player.try_move(0.1, 0, -TILE, tilemap, [])
check(not moved, "player blocked by water")

# 15. 子弹相撞
print("\n=== Test 15: Bullets collide and destroy each other ===")
layout = make_empty_level()
tilemap = TileMap.from_layout(layout)
b1 = Bullet(MAP_X + 4*TILE, MAP_Y + 6*TILE, Dir.UP, "player")
b2 = Bullet(MAP_X + 4*TILE, MAP_Y + 5*TILE, Dir.DOWN, "enemy")
bullets = [b1, b2]
for _ in range(int(FPS * 0.1)):
    b1.update(1/60, tilemap, bullets, [], lambda t: None)
    b2.update(1/60, tilemap, bullets, [], lambda t: None)
    if b1.dead and b2.dead:
        break
check(b1.dead and b2.dead, f"both bullets destroyed: b1={b1.dead}, b2={b2.dead}")

print("\n" + "=" * 50)
if errors:
    print(f"FAILED: {len(errors)} test(s)")
    for e in errors:
        print("  -", e)
else:
    print("ALL TESTS PASSED ✓")
print("=" * 50)

pygame.quit()
exit(1 if errors else 0)
