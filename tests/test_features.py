"""新功能单元测试 (pytest 风格): 6 关数据 + 道具 + AI tier + 视觉 + 音效 + 字体 + 回归."""
import time

import pytest
import pygame

from settings import (SCREEN_W, SCREEN_H, FPS, TILE, GRID_W, GRID_H,
                       PLAYER_LIVES, Dir, MAP_X, MAP_Y, LEVEL_DIFFICULTY)
from world.tilemap import TileMap
from world.levels import (LEVELS, LEVEL_6, get_level, get_level_difficulty,
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


def _fake_event(type, key):
    """构造一个假的 pygame.Event。"""
    return pygame.event.Event(type, {"key": key, "mod": 0, "unicode": "", "scancode": 0})


# ---- 1. 关卡数据完整性 ----
def test_level_data_integrity():
    # B3: 现在 7 关 (6 关 campaign + 关 7 survival)
    assert get_total_levels() == 7, f"7 levels, got {get_total_levels()}"
    for i, lvl in enumerate(LEVELS):
        assert len(lvl) == GRID_H, f"level {i+1}: {GRID_H} rows, got {len(lvl)}"
        for r, row in enumerate(lvl):
            assert len(row) == GRID_W, f"level {i+1} row {r}: {GRID_W} cols, got {len(row)}: {row!r}"
        # 关 7 是 survival 模式，没有基地 (B3)
        if i < 6:
            assert any("X" in row for row in lvl), f"level {i+1}: has base 'X'"
        assert any("P" in row for row in lvl), f"level {i+1}: has player 'P'"
        tm = TileMap.from_layout(lvl)
        assert len(tm.enemy_spawns) >= 2, f"level {i+1}: >=2 enemy spawns, got {len(tm.enemy_spawns)}"


# ---- 2. 难度递增 ----
def test_difficulty_progression():
    # B3: 现在 7 关 (6 关 campaign + 关 7 survival, survival 不参与递增)
    assert len(LEVEL_DIFFICULTY) == 7, f"7 difficulty levels, got {len(LEVEL_DIFFICULTY)}"
    # 只对 campaign 6 关检查 enemy_count 递增
    for i in range(1, 6):
        prev = LEVEL_DIFFICULTY[i - 1]
        cur = LEVEL_DIFFICULTY[i]
        assert cur["enemy_count"] >= prev["enemy_count"], \
            f"level {i+1} enemy_count >= previous: {cur['enemy_count']} >= {prev['enemy_count']}"
        if i >= 3:
            assert cur["enemy_speed"] > prev["enemy_speed"], \
                f"level {i+1} enemy_speed > previous: {cur['enemy_speed']} > {prev['enemy_speed']}"
    # survival 关 enemy_speed 应 >= 关 6 campaign
    assert LEVEL_DIFFICULTY[6]["enemy_speed"] >= LEVEL_DIFFICULTY[5]["enemy_speed"], \
        "survival should be at least as fast as final campaign"


# ---- 3. 道具系统 ----
def test_powerup_basics():
    pu = PowerUp(100, 100, "star")
    assert pu.type == "star"
    assert pu.rect.x == 100 and pu.rect.y == 100
    assert not pu.dead


def test_powerup_lifetime():
    pu = PowerUp(0, 0, "star")
    pu.spawn_time = time.time() - 13
    pu.update(0.016)
    assert pu.dead, "powerup dies after 12s"


def test_powerup_types():
    assert len(ALL_TYPES) == 6, f"6 powerup types: {ALL_TYPES}"
    valid = {"star", "grenade", "helmet", "clock", "shovel", "tank"}
    for t in ALL_TYPES:
        assert t in valid, f"valid type: {t}"


def test_spawn_random_powerup():
    pu = spawn_random_powerup(200, 200)
    assert pu.type in ALL_TYPES


def test_powerup_player_collision():
    pu = PowerUp(200, 200, "star")
    p = PlayerTank(200, 200)
    assert pu.rect.colliderect(p.rect)


# ---- 4. 敌人 AI tier 差异 ----
def test_enemy_tier_steel():
    e0 = EnemyTank(100, 100, tier=0)
    e1 = EnemyTank(100, 100, tier=1)
    e2 = EnemyTank(100, 100, tier=2)
    assert not e0.breaks_steel
    assert not e1.breaks_steel
    assert e2.breaks_steel


def test_enemy_tier_speed():
    e0 = EnemyTank(100, 100, tier=0)
    e1 = EnemyTank(100, 100, tier=1)
    e2 = EnemyTank(100, 100, tier=2)
    assert e0.speed == 72
    assert e1.speed == 72
    assert abs(e2.speed - 90) < 0.1


def test_enemy_tier_misc():
    e0 = EnemyTank(100, 100, tier=0)
    assert e0.born_invuln > 0
    assert not e0.frozen


# ---- 5. 子弹破钢墙 ----
def _empty_with_tile(row, col, ch):
    """构造一个空旷关卡, (row, col) 放指定瓦片."""
    lay = ["." * GRID_W for _ in range(GRID_H)]
    lay[row] = lay[row][:col] + ch + lay[row][col + 1:]
    return lay


def test_bullet_normal_vs_steel():
    mid = GRID_W // 2
    layout = _empty_with_tile(5, mid, "S")
    tilemap = TileMap.from_layout(layout)
    b = Bullet(MAP_X + mid * TILE, MAP_Y + 5 * TILE + TILE, Dir.UP, "player")
    for _ in range(int(FPS * 0.5)):
        b.update(1/60, tilemap, [b], [], lambda t: None)
        if b.dead: break
    assert b.dead, "normal bullet consumed by steel"
    assert isinstance(tilemap.tiles[5][mid], TileSteel), "steel intact"


def test_bullet_strong_breaks_steel():
    mid = GRID_W // 2
    layout = _empty_with_tile(5, mid, "S")
    tilemap = TileMap.from_layout(layout)
    b = Bullet(MAP_X + mid * TILE, MAP_Y + 5 * TILE + TILE, Dir.UP, "player")
    b.can_break_steel = True
    for _ in range(int(FPS * 0.5)):
        b.update(1/60, tilemap, [b], [], lambda t: None)
        if b.dead: break
    assert b.dead
    assert not isinstance(tilemap.tiles[5][mid], TileSteel)


def test_player_level_breaks_steel():
    mid = GRID_W // 2
    layout = _empty_with_tile(5, mid, "S")

    p = PlayerTank(MAP_X + mid * TILE, MAP_Y + 7 * TILE)
    p.upgrade_level = 2
    p_bullets = []
    p.shoot(p_bullets)
    assert p_bullets[-1].can_break_steel, "level 2 bullet breaks steel"

    p0 = PlayerTank(MAP_X + mid * TILE, MAP_Y + 7 * TILE)
    p0_bullets = []
    p0.shoot(p0_bullets)
    assert not p0_bullets[-1].can_break_steel, "level 0 bullet cannot break steel"


# ---- 5.5 砖块跨子格命中回归 ----
def test_brick_cross_subcell_x():
    """子弹 rect 跨 sub 0/sub 1 列边界, 修复后枚举所有覆盖子格."""
    mid_x = MAP_X + 5 * TILE + TILE // 2
    brick_y = MAP_Y + 5 * TILE
    layout = _empty_with_tile(5, 5, "B")
    tm = TileMap.from_layout(layout)
    brick = tm.tiles[5][5]
    brick.subtl = 0b0010  # 只有 sub 1 活

    # 子弹 rect 起步 (304, 240, 8, 8): 跨 sub 0/1 列 (x=308 边界)
    b = Bullet(mid_x, brick_y + 4, Dir.UP, "player")
    for _ in range(int(FPS * 0.3)):
        b.update(1/60, tm, [b], [], lambda t: None)
        if b.dead: break
    assert brick.subtl == 0, f"sub 1 hit via cross-subcell x, got {bin(brick.subtl)}"
    assert b.dead


def test_brick_cross_subcell_y():
    """子弹 rect 跨 sub 2/sub 3 行边界."""
    mid_x = MAP_X + 5 * TILE + TILE // 2
    brick_y = MAP_Y + 5 * TILE
    layout = _empty_with_tile(5, 5, "B")
    tm = TileMap.from_layout(layout)
    brick = tm.tiles[5][5]
    brick.subtl = 0b1000  # 只有 sub 3 活

    # 子弹 rect 起步 (304, 270, 8, 8): 跨 sub 2/3 行
    b = Bullet(mid_x, brick_y + 30, Dir.UP, "player")
    for _ in range(int(FPS * 0.3)):
        b.update(1/60, tm, [b], [], lambda t: None)
        if b.dead: break
    assert brick.subtl == 0, f"sub 3 hit via cross-subcell y, got {bin(brick.subtl)}"
    assert b.dead


# ---- 6. line_of_sight ----
def test_line_of_sight():
    layout = ["." * GRID_W for _ in range(GRID_H)]
    tilemap = TileMap.from_layout(layout)
    m = GRID_W // 2
    assert line_of_sight((MAP_X + m * TILE + TILE // 2, MAP_Y + 0),
                        (MAP_X + m * TILE + TILE // 2, MAP_Y + (GRID_H - 1) * TILE),
                        tilemap), "vertical sight clear"
    assert line_of_sight((MAP_X + 0, MAP_Y + m * TILE + TILE // 2),
                        (MAP_X + (GRID_W - 1) * TILE, MAP_Y + m * TILE + TILE // 2),
                        tilemap), "horizontal sight clear"
    assert not line_of_sight((MAP_X + m * TILE, MAP_Y + m * TILE),
                            (MAP_X + (m + 2) * TILE, MAP_Y + (m + 2) * TILE),
                            tilemap), "diagonal returns False"
    # 砖块阻挡
    layout[5] = layout[5][:m] + "B" + layout[5][m + 1:]
    tilemap = TileMap.from_layout(layout)
    assert not line_of_sight((MAP_X + m * TILE + TILE // 2, MAP_Y + 0),
                            (MAP_X + m * TILE + TILE // 2, MAP_Y + (GRID_H - 1) * TILE),
                            tilemap), "brick blocks sight"


# ---- 7. MuzzleFlash / Explosion ----
def test_muzzle_flash_lifecycle():
    fx = MuzzleFlash(100, 100, Dir.UP, (255, 200, 100))
    assert not fx.dead
    fx.update(0.5)
    assert fx.dead, "MuzzleFlash dies after 0.1s"


def test_explosion_lifecycle():
    exp = Explosion(100, 100, big=True)
    assert len(exp.particles) == 14, f"14 particles, got {len(exp.particles)}"
    exp.update(2.0)
    assert exp.dead
    assert len(exp.particles) == 0


def test_particle_physics():
    p = Particle(0, 0, 100, 0, (255, 0, 0), 1.0)
    p.update(0.5)
    assert p.x > 0, f"Particle moves: x={p.x}"


# ---- 8. 子弹拖尾 ----
def test_bullet_trail():
    b = Bullet(100, 100, Dir.UP, "player")
    tilemap = TileMap.from_layout(["." * GRID_W for _ in range(GRID_H)])
    for _ in range(10):
        b.update(1/60, tilemap, [b], [], lambda t: None)
        if b.dead: break
    assert len(b.trail) <= 6, f"trail capped at 6, got {len(b.trail)}"
    assert len(b.trail) > 0


# ---- 9. 软吸附 ----
def test_soft_snap():
    t = Tank(100, 100, Dir.DOWN, (200, 200, 200), (100, 100, 100))
    t.rect.x = MAP_X + 5 * TILE + 14
    tilemap = TileMap.from_layout(["." * GRID_W for _ in range(GRID_H)])
    t.try_change_direction(Dir.RIGHT, tilemap, [])
    assert t.snap_axis is not None, f"snap_axis set: {t.snap_axis}"
    for _ in range(20):
        t.update_snap(1/60)
    assert t.snap_axis is None, f"snap_axis cleared: {t.snap_axis}"


# ---- 10. 履带 phase ----
def test_tread_phase():
    t = Tank(MAP_X + 6 * TILE, MAP_Y + 6 * TILE, Dir.UP, (200, 200, 200), (100, 100, 100))
    tilemap = TileMap.from_layout(["." * GRID_W for _ in range(GRID_H)])
    t.try_change_direction(Dir.UP, tilemap, [])
    phase0 = t.tread_phase
    for _ in range(10):
        t.try_move(1/60, 0, -5, tilemap, [])
    assert t.tread_phase > phase0, f"tread_phase increased: {phase0} -> {t.tread_phase}"


# ---- 11. 方向优先级 ----
def test_direction_priority():
    p = PlayerTank(MAP_X + 6 * TILE, MAP_Y + 6 * TILE)
    p.handle_event(_fake_event(pygame.KEYDOWN, pygame.K_w))
    assert p.keys["up"]
    p._time = 0.5
    p.handle_event(_fake_event(pygame.KEYDOWN, pygame.K_d))
    assert p.key_press_time["right"] > p.key_press_time["up"]
    assert p._active_direction() == Dir.RIGHT, f"active dir: {p._active_direction()}"


# ---- 12. 惯性滑行 ----
def test_inertia_slide():
    p = PlayerTank(MAP_X + 6 * TILE, MAP_Y + 6 * TILE)
    p.keys["up"] = True
    p._time += 0.016
    tilemap = TileMap.from_layout(["." * GRID_W for _ in range(GRID_H)])
    bullets = []
    p.update(0.1, tilemap, [], bullets, effects=[])
    assert p.slide_timer > 0, f"slide_timer: {p.slide_timer}"
    p.keys["up"] = False
    p._time += 0.016
    prev_y = p.rect.y
    p.update(0.05, tilemap, [], bullets, effects=[])
    assert p.rect.y < prev_y or p.slide_timer > 0, "inertia continues after release"


# ---- 13. CJK 字体 ----
def test_cjk_font():
    from game.hud import _find_cjk_font
    font_name = _find_cjk_font()
    assert font_name is not None, f"CJK font found: {font_name}"
    f = _get_font(20, True)
    s = f.render("坦克大战", True, (255, 255, 255))
    assert s.get_width() > 30, f"Chinese text renders, width={s.get_width()}"


def _get_font(size, bold=False):
    from game.hud import get_font as _gf
    return _gf(size, bold)


# ---- 14. 音效 ----
def test_sound_system():
    assert is_available(), "Sound system available"
    set_muted(True)
    assert is_muted()
    play("fire")
    set_muted(False)
    for name in ("fire", "explosion", "hit", "start"):
        play(name)
    # 通过: 不抛错即 OK


# ---- 15. is_player 标记 ----
def test_is_player_flag():
    p = PlayerTank(100, 100)
    e = EnemyTank(100, 100)
    assert p.is_player
    assert not e.is_player
    p_bullets, e_bullets = [], []
    b1 = p.shoot(p_bullets)
    b2 = e.shoot(e_bullets)
    assert b1.owner == "player"
    assert b2.owner == "enemy"


# ---- 16. Bug 修复回归 ----
def test_regression_shovel_timer():
    from game.level import Level
    lvl = Level(0, 3, 0)
    lvl._activate_shovel(2.0)
    assert lvl._shovel_timer == 2.0
    for _ in range(int(60 * 1.5)):
        lvl.update(1/60)
    assert 0 < lvl._shovel_timer < 1.0, f"timer: {lvl._shovel_timer}"
    for _ in range(int(60 * 1.0)):
        lvl.update(1/60)
    assert lvl._shovel_backup is None, "backup cleared after timer expires"


def test_regression_respawn_preserves_state():
    from game.level import Level
    lvl = Level(0, 3, 0)
    lvl.players[0].upgrade_level = 2
    lvl.players[0].invincible = 5.0
    lvl.players[0].frozen_enemies_timer = 6.0
    lvl.players[0].dead = True
    lvl._death_timer = 0.05
    lvl.update(0.1)
    assert lvl.players[0].upgrade_level == 2
    assert lvl.players[0].invincible > 0
    assert 5.0 < lvl.players[0].frozen_enemies_timer <= 6.0


def test_regression_grenade_no_double_score():
    from game.level import Level
    from entities.powerup import PowerUp
    lvl = Level(0, 3, 0)
    for i in range(3):
        e = EnemyTank(lvl.tilemap.grid_to_world(0, 0)[0] + i * 100,
                      lvl.tilemap.grid_to_world(0, 0)[1], tier=0)
        e.born_invuln = 0
        lvl.enemies.append(e)
    lvl.effects = []
    initial = lvl.score
    lvl._apply_powerup(PowerUp(0, 0, "grenade"))
    for _ in range(5):
        lvl.update(1/60)
    assert lvl.score - initial == 300, f"score delta: {lvl.score - initial}"


def test_regression_level6_enemy_spawns():
    tm6 = TileMap.from_layout(LEVEL_6)
    assert (0, 1) in tm6.enemy_spawns, f"{(0, 1)} not in {tm6.enemy_spawns}"
    assert (GRID_W - 1, 1) in tm6.enemy_spawns, f"({GRID_W - 1}, 1) not in {tm6.enemy_spawns}"
    assert len(tm6.enemy_spawns) == 2


def test_regression_dead_enemy_does_not_block_spawn():
    from game.level import Level
    lvl = Level(0, 3, 0)
    lvl.enemies_to_spawn = 5
    lvl._spawn_timer = 0.0
    x, y = lvl.tilemap.grid_to_world(*lvl.tilemap.enemy_spawns[0])
    dead_e = EnemyTank(x, y, tier=0)
    dead_e.dead = True
    lvl.enemies.append(dead_e)
    lvl._spawn_idx = 0
    result = lvl._spawn_enemy()
    assert result is not None


def test_regression_tile_empty_real_class():
    from world.tile import TileEmpty
    assert TileEmpty.__name__ == "TileEmpty"
    _m = GRID_W // 2
    tm = TileMap.from_layout(["." * GRID_W for _ in range(GRID_H)])
    tm.tiles[5][_m] = TileSteel()
    b = Bullet(MAP_X + _m * TILE, MAP_Y + 6 * TILE + TILE, Dir.UP, "player")
    b.can_break_steel = True
    for _ in range(int(FPS * 0.5)):
        b.update(1/60, tm, [b], [], lambda t: None)
        if b.dead: break
    assert isinstance(tm.tiles[5][_m], TileEmpty), \
        f"after steel-break: {type(tm.tiles[5][_m]).__name__}"


def test_regression_player_uses_setting_cooldown():
    from settings import PLAYER_FIRE_COOLDOWN
    p = PlayerTank(0, 0)
    bullets = []
    p.shoot(bullets)
    assert p.cooldown == PLAYER_FIRE_COOLDOWN


def test_regression_powerup_distinct_sounds():
    from game.level import POWERUP_SOUND
    assert len(POWERUP_SOUND) == 6
    assert len(set(POWERUP_SOUND.values())) >= 2, \
        f"distinct sounds: {set(POWERUP_SOUND.values())}"
