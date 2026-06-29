"""端到端逻辑测试 (pytest 风格): 关卡创建/移动/子弹/碰撞/AI/重生/关卡切换.

注意: 测试使用简化关卡布局 (无墙壁), 确保子弹/坦克能稳定到达目标.
conftest.py 负责 dummy SDL env + pygame init + display set_mode.
"""
import pygame

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
from entities.player import PlayerTank
from entities.enemy import EnemyTank
import world.tile as wt


def make_empty_level():
    """构建一个空旷关卡 (仅基地 + 玩家 + 3 个出生点), 用于隔离测试.

    随 GRID_W/GRID_H 自适应: 玩家在底部中央 (col=mid, row=GRID_H-2),
    基地正下方 (row=GRID_H-1), 敌人在顶部左/中/右.
    """
    layout = ["." * GRID_W for _ in range(GRID_H)]
    mid = GRID_W // 2
    layout[GRID_H - 2] = layout[GRID_H - 2][:mid] + "P" + layout[GRID_H - 2][mid + 1:]
    layout[GRID_H - 1] = layout[GRID_H - 1][:mid] + "X" + layout[GRID_H - 1][mid + 1:]
    assert len(layout[GRID_H - 1]) == GRID_W
    e_cols = [0, mid, GRID_W - 1]
    row0 = list("." * GRID_W)
    for c in e_cols:
        row0[c] = "E"
    layout[0] = "".join(row0)
    assert len(layout[0]) == GRID_W
    return layout


# ---- 1. 关卡创建 ----
def test_level_creation():
    level = Level(0, PLAYER_LIVES, 0)
    assert level.tilemap is not None
    assert level.players[0] is not None
    assert not level.players[0].dead
    assert level.enemies_to_spawn == ENEMIES_PER_LEVEL
    assert level.lives == PLAYER_LIVES


# ---- 2. 地图绘制 ----
def test_map_drawing():
    level = Level(0, PLAYER_LIVES, 0)
    screen = pygame.display.get_surface()  # conftest 已 set_mode
    level.tilemap.draw(screen)
    level.draw(screen)
    pygame.display.flip()


# ---- 3. HUD ----
def test_hud():
    screen = pygame.display.get_surface()
    draw_hud(screen, 2, 500, 0, 10, max_lives=PLAYER_LIVES)
    pygame.display.flip()


# ---- 4. 菜单 ----
def test_menu_screens():
    screen = pygame.display.get_surface()
    draw_menu(screen, 0.0)
    draw_pause(screen)
    draw_level_complete(screen, 0, 100, 0.0)
    draw_game_over(screen, 500, victory=False, t=0.0)
    draw_game_over(screen, 1500, victory=True, t=0.0)
    pygame.display.flip()


# ---- 5. 玩家移动 + 子弹 ----
def test_player_movement_and_shooting():
    level = Level(0, PLAYER_LIVES, 0)
    start_y = level.players[0].rect.y
    level.players[0].keys["up"] = True
    level.players[0].update(0.1, level.tilemap, [], level.bullets)
    level.players[0].keys["up"] = False
    assert level.players[0].rect.y < start_y or level.players[0].rect.y != start_y, \
        f"player moved: {start_y} -> {level.players[0].rect.y}"
    assert level.players[0].dir == Dir.UP

    level.players[0].keys["fire"] = True
    level.players[0].update(0.1, level.tilemap, [], level.bullets)
    assert len(level.bullets) >= 1, f"bullet created: {len(level.bullets)}"


# ---- 6. 砖块碰撞 ----
def test_collision_with_brick_in_real_level():
    level = Level(0, PLAYER_LIVES, 0)
    brick_pos = None
    for r in range(GRID_H):
        for c in range(GRID_W):
            if isinstance(level.tilemap.tiles[r][c], wt.TileBrick):
                brick_pos = (c, r)
                break
        if brick_pos:
            break
    assert brick_pos is not None, "found a brick"
    col, row = brick_pos
    level.players[0].rect.x, level.players[0].rect.y = level.tilemap.grid_to_world(col, row)
    level.players[0].rect.x -= TILE
    old_x = level.players[0].rect.x
    moved = level.players[0].try_move(0.1, TILE, 0, level.tilemap, [])
    assert level.players[0].rect.x == old_x or not moved, "player blocked by brick"


# ---- 7. 子弹打砖块 ----
def test_bullet_destroys_brick_subcell():
    layout = make_empty_level()
    layout[5] = layout[5][:6] + "B" + layout[5][7:]
    tilemap = TileMap.from_layout(layout)
    bx, by = tilemap.grid_to_world(6, 5)
    bullet = Bullet(bx, by + TILE, Dir.UP, "player")
    level = Level(0, PLAYER_LIVES, 0)
    for _ in range(int(FPS * 0.5)):
        bullet.update(1/60, tilemap, [bullet], [level.players[0]], lambda t: None)
        if bullet.dead:
            break
    brick = tilemap.tiles[5][6]
    assert isinstance(brick, wt.TileBrick)
    assert brick.subtl != 0b1111, f"brick subcell destroyed: {bin(brick.subtl)}"


# ---- 8. 敌人 AI ----
def test_enemy_ai_in_real_level():
    level = Level(0, PLAYER_LIVES, 0)
    level._spawn_timer = 0.0
    for _ in range(int(FPS * 3)):
        level.update(1.0 / FPS)
        if level.enemies:
            break
    assert len(level.enemies) >= 1, f"enemies spawned: {len(level.enemies)}"
    for _ in range(int(FPS * 3)):
        level.update(1.0 / FPS)
    enemy_fired = any(b.owner == "enemy" for b in level.bullets)
    assert enemy_fired, f"enemy fired (bullets: {len(level.bullets)})"


# ---- 9. 子弹打坦克 ----
def test_bullet_hits_tank():
    layout = make_empty_level()
    tilemap = TileMap.from_layout(layout)
    enemy = EnemyTank(MAP_X + 4 * TILE, MAP_Y + 4 * TILE, tier=0)
    enemy.born_invuln = 0
    enemy.flashing_time = 0
    player = PlayerTank(MAP_X + 8 * TILE, MAP_Y + 8 * TILE)
    b = Bullet(enemy.rect.centerx, enemy.rect.centery + 30, Dir.UP, "player")
    bullets = [b]
    tanks = [player, enemy]
    for _ in range(int(FPS * 0.5)):
        b.update(1/60, tilemap, bullets, tanks, lambda t: None)
        if b.dead:
            break
    assert b.dead, f"bullet consumed (dead={b.dead})"
    assert enemy.dead, f"enemy killed (dead={enemy.dead})"


# ---- 10. 基地被毁 ----
def test_base_destruction():
    layout = make_empty_level()
    tilemap = TileMap.from_layout(layout)
    base_pos = tilemap.base_pos
    bx, by = tilemap.grid_to_world(*base_pos)
    b = Bullet(bx, by - TILE, Dir.DOWN, "enemy")
    for _ in range(int(FPS * 0.5)):
        b.update(1/60, tilemap, [b], [], lambda t: None)
        if b.dead:
            break
    assert tilemap.base_tile.destroyed, f"base destroyed: {tilemap.base_tile.destroyed}"


# ---- 11. 玩家重生 ----
def test_player_respawn():
    level = Level(0, PLAYER_LIVES, 0)
    level.players[0].dead = True
    level._death_timer = 0.1
    level.update(0.2)
    assert level.players[0] is not None and not level.players[0].dead, "player respawned"
    assert level.lives == PLAYER_LIVES - 1, f"lives: {level.lives}"


# ---- 12. 关卡切换 ----
def test_level_transition():
    from game.game import Game
    import settings as S
    level = Level(0, PLAYER_LIVES, 0)
    level.enemies_to_spawn = 0
    level.enemies = []
    level.update(0.1)
    assert level.completed, "level marked completed"
    g = Game.__new__(Game)
    g.level = level
    g.level_index = 0
    g.score = 1000
    g.lives = 3
    g.state = S.State.LEVEL_COMPLETE
    g.state_time = 3.0
    g.next_level()
    assert g.state == S.State.PLAYING, f"state: {g.state}"
    assert g.level_index == 1, f"level_index: {g.level_index}"


# ---- 13. 钢墙不能被打坏 ----
def test_steel_wall_blocks_bullets():
    layout = make_empty_level()
    layout[5] = layout[5][:6] + "S" + layout[5][7:]
    tilemap = TileMap.from_layout(layout)
    bx, by = tilemap.grid_to_world(6, 5)
    b = Bullet(bx, by + TILE, Dir.UP, "player")
    for _ in range(int(FPS * 0.5)):
        b.update(1/60, tilemap, [b], [], lambda t: None)
        if b.dead:
            break
    assert b.dead, "bullet consumed by steel"
    steel = tilemap.tiles[5][6]
    assert isinstance(steel, wt.TileSteel) and not getattr(steel, "destroyed", False)


# ---- 14. 水域阻挡坦克 ----
def test_water_blocks_tanks():
    layout = make_empty_level()
    layout[5] = layout[5][:6] + "W" + layout[5][7:]
    tilemap = TileMap.from_layout(layout)
    player = PlayerTank(MAP_X + 6 * TILE, MAP_Y + 6 * TILE)
    player.try_change_direction(Dir.UP, tilemap, [])
    moved = player.try_move(0.1, 0, -TILE, tilemap, [])
    assert not moved, "player blocked by water"


# ---- 15. 子弹相撞 ----
def test_bullets_collide():
    layout = make_empty_level()
    tilemap = TileMap.from_layout(layout)
    b1 = Bullet(MAP_X + 4 * TILE, MAP_Y + 6 * TILE, Dir.UP, "player")
    b2 = Bullet(MAP_X + 4 * TILE, MAP_Y + 5 * TILE, Dir.DOWN, "enemy")
    bullets = [b1, b2]
    for _ in range(int(FPS * 0.1)):
        b1.update(1/60, tilemap, bullets, [], lambda t: None)
        b2.update(1/60, tilemap, bullets, [], lambda t: None)
        if b1.dead and b2.dead:
            break
    assert b1.dead and b2.dead, f"both bullets destroyed: b1={b1.dead}, b2={b2.dead}"
