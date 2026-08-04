"""B4 道具扩充 (F7) 测试.

- ALL_TYPES 9 个 (经典 6 + magnet/laser/mine)
- magnet 道具向玩家飞
- laser 子弹穿透敌人不消失
- mine 放 3 颗, 敌人碰触 AOE 爆炸
- _apply_powerup 三个新分支
"""
import random
import pytest
import pygame
from unittest.mock import patch

import settings
from entities.powerup import PowerUp, ALL_TYPES, TYPE_COLORS, spawn_random_powerup
from entities.bullet import Bullet
from entities.mine import Mine, spawn_mines_around
from entities.enemy import EnemyTank
from entities.player import PlayerTank
from game.level import Level


# ---- ALL_TYPES / TYPE_COLORS 完整性 ----

def test_all_types_has_9():
    """B4: 9 种道具 (经典 6 + 3)."""
    assert len(ALL_TYPES) == 9
    assert "magnet" in ALL_TYPES
    assert "laser" in ALL_TYPES
    assert "mine" in ALL_TYPES


def test_type_colors_has_9():
    for t in ALL_TYPES:
        assert t in TYPE_COLORS, f"{t} missing color"


def test_spawn_random_includes_new_types():
    """spawn_random_powerup 随机选, 包含新 3 种."""
    from collections import Counter
    random.seed(0)
    counts = Counter()
    for _ in range(300):
        pu = spawn_random_powerup(0, 0)
        counts[pu.type] += 1
    # 9 个 type 都应至少出现 1 次 (概率 1/9 * 300 ≈ 33)
    for t in ALL_TYPES:
        assert counts[t] > 0, f"{t} never spawned in 300 samples"


# ---- PowerUp.update magnet_target 参数 ----

def test_powerup_update_without_magnet_no_movement():
    """无 magnet_target 时, 道具位置不变 (除自然 LIFETIME 到期外)."""
    pu = PowerUp(100, 100, "star")
    initial_x, initial_y = pu.rect.x, pu.rect.y
    pu.update(0.1, magnet_target=None)
    assert pu.rect.x == initial_x
    assert pu.rect.y == initial_y


def test_powerup_update_with_magnet_moves_toward_target():
    """给 magnet_target 时, 道具向其中心飞."""
    pu = PowerUp(100, 100, "star")
    initial_x, initial_y = pu.rect.x, pu.rect.y
    # 目标在 (300, 100), 道具向右飞
    pu.update(0.1, magnet_target=(300, 100))
    assert pu.rect.x > initial_x, f"should move right: {pu.rect.x} > {initial_x}"


def test_powerup_reaches_magnet_target():
    """道具飞足够长时间到达 magnet_target."""
    pu = PowerUp(0, 0, "star")
    target = (200, 0)
    for _ in range(20):
        pu.update(0.1, magnet_target=target)
    # 应到达或非常接近
    assert abs(pu.rect.centerx - 200) < 5, f"centerx={pu.rect.centerx}"


# ---- _apply_powerup: magnet ----

def test_apply_magnet_sets_timer():
    """_apply_powerup('magnet') 给玩家设 magnet_timer."""
    lv = Level(0, lives=3, score=0, num_players=1)
    pu = PowerUp(0, 0, "magnet")
    assert lv.players[0].magnet_timer == 0.0
    lv._apply_powerup(pu, target_idx=0)
    assert lv.players[0].magnet_timer == settings.MAGNET_DURATION


def test_magnet_timer_decrements_in_update():
    """update 倒数 magnet_timer."""
    lv = Level(0, lives=3, score=0, num_players=1)
    lv.players[0].magnet_timer = 5.0
    lv.update(0.1)
    assert lv.players[0].magnet_timer < 5.0


def test_magnet_attracts_powerups_via_level_update():
    """Level.update 给活跃 powerup 传 magnet_target."""
    lv = Level(0, lives=3, score=0, num_players=1)
    # 玩家在固定位置
    lv.players[0].rect.x = 200
    lv.players[0].rect.y = 200
    # 放一个远距离 powerup
    pu = PowerUp(0, 0, "star")
    initial_x = pu.rect.x
    lv.powerups.append(pu)
    # 激活 magnet
    lv._apply_powerup(PowerUp(0, 0, "magnet"), target_idx=0)
    # 跑 update
    lv.update(0.1)
    # powerup 应向玩家移动
    assert pu.rect.x > initial_x, f"powerup not attracted: {pu.rect.x}"


# ---- _apply_powerup: laser ----

def test_apply_laser_sets_timer():
    """_apply_powerup('laser') 给玩家设 laser_timer."""
    lv = Level(0, lives=3, score=0, num_players=1)
    pu = PowerUp(0, 0, "laser")
    assert lv.players[0].laser_timer == 0.0
    lv._apply_powerup(pu, target_idx=0)
    assert lv.players[0].laser_timer == settings.LASER_DURATION


def test_laser_bullet_pierces_enemies():
    """laser 子弹击中敌人不 dead, 继续飞."""
    # 子弹起点放在地图内 (MAP_X=110), 敌人靠右
    bullet = Bullet(130, 200, pygame.Vector2(1, 0), owner="player")
    bullet.is_laser = True
    enemy = EnemyTank(150, 200, tier=0, is_powerup_carrier=False)
    enemy.born_invuln = 0  # 关无敌
    from world.tilemap import TileMap
    tilemap = TileMap.from_layout(["." * 17 for _ in range(17)])
    tilemap.tiles = [[None] * 17 for _ in range(17)]
    bullet.update(0.1, tilemap, [bullet], [enemy], lambda t: None)
    assert enemy.dead, "laser should kill enemy"
    assert not bullet.dead, "laser should NOT be dead after piercing"


def test_normal_bullet_dies_on_enemy_hit():
    """非 laser 子弹击中敌人应 dead (回归)."""
    bullet = Bullet(130, 200, pygame.Vector2(1, 0), owner="player")
    assert bullet.is_laser is False
    enemy = EnemyTank(150, 200, tier=0, is_powerup_carrier=False)
    enemy.born_invuln = 0  # 关无敌
    from world.tilemap import TileMap
    tilemap = TileMap.from_layout(["." * 17 for _ in range(17)])
    tilemap.tiles = [[None] * 17 for _ in range(17)]
    bullet.update(0.1, tilemap, [bullet], [enemy], lambda t: None)
    assert enemy.dead
    assert bullet.dead, "normal bullet should die on hit"


def test_player_shoot_during_laser_makes_laser_bullet():
    """玩家 laser 激活时 shoot, 子弹 is_laser=True."""
    lv = Level(0, lives=3, score=0, num_players=1)
    lv.players[0].laser_timer = 5.0
    lv.players[0].shoot(lv.bullets)
    assert len(lv.bullets) == 1
    assert lv.bullets[0].is_laser is True


def test_player_shoot_without_laser_makes_normal_bullet():
    """玩家 laser 未激活时 shoot, 子弹 is_laser=False (回归)."""
    lv = Level(0, lives=3, score=0, num_players=1)
    lv.players[0].laser_timer = 0.0
    lv.players[0].shoot(lv.bullets)
    assert lv.bullets[0].is_laser is False


# ---- _apply_powerup: mine ----

def test_apply_mine_spawns_3_mines():
    """_apply_powerup('mine') 在玩家位置放 3 颗地雷."""
    lv = Level(0, lives=3, score=0, num_players=1)
    pu = PowerUp(0, 0, "mine")
    assert len(lv.mines) == 0
    lv._apply_powerup(pu, target_idx=0)
    assert len(lv.mines) == 3


def test_spawn_mines_around_count_3():
    """spawn_mines_around(p, count=3) 返回 3 颗, 沿朝向方向."""
    p = PlayerTank(0, 0)
    p.dir = (0, 1)  # 朝下
    mines = spawn_mines_around(p, count=3)
    assert len(mines) == 3
    # 中 (玩家当前格) + 前 (下方) + 后 (上方)
    cy = mines[0].rect.centery
    assert mines[1].rect.centery > cy, "forward mine should be south"
    assert mines[2].rect.centery < cy, "backward mine should be north"


def test_spawn_mines_around_count_1():
    p = PlayerTank(100, 100)
    mines = spawn_mines_around(p, count=1)
    assert len(mines) == 1


def test_mine_collision_with_enemy_triggers_blast():
    """敌人碰触地雷触发爆炸, AOE 内敌人死亡."""
    lv = Level(0, lives=3, score=0, num_players=1)
    # 在固定位置放一颗地雷
    mine = Mine(100, 100)
    lv.mines.append(mine)
    # 放一个会撞上地雷的敌人
    enemy = EnemyTank(100, 100, tier=0, is_powerup_carrier=False)
    enemy.born_invuln = 0  # 关掉无敌
    lv.enemies.append(enemy)
    # 跑 update
    lv.update(0.1)
    # 敌人死了
    assert enemy.dead
    # 地雷 dead
    assert mine.dead
    # 爆炸特效被添加
    assert any(getattr(fx, 'big', False) for fx in lv.effects) or len(lv.effects) > 0


def test_mine_blast_kills_enemies_in_radius():
    """AOE 内所有敌人都死."""
    lv = Level(0, lives=3, score=0, num_players=1)
    mine = Mine(200, 200)
    lv.mines.append(mine)
    # 周围 3 个敌人
    e1 = EnemyTank(220, 200, tier=0, is_powerup_carrier=False)  # 近
    e1.born_invuln = 0
    e2 = EnemyTank(250, 250, tier=0, is_powerup_carrier=False)  # 50px 内
    e2.born_invuln = 0
    e3 = EnemyTank(500, 500, tier=0, is_powerup_carrier=False)  # 远 (>100)
    e3.born_invuln = 0
    lv.enemies.extend([e1, e2, e3])
    # 触发爆炸: e1 直接碰地雷
    mine.update(0.1, lv.enemies, lv.effects, __import__('utils.events', fromlist=['events']))
    assert e1.dead
    assert e2.dead
    assert not e3.dead  # 太远, 不死


def test_mine_collision_publishes_entity_killed():
    """地雷爆炸 publish ENTITY_KILLED 事件."""
    from utils import events as ev
    ev.clear()
    received = []
    ev.subscribe(ev.ENTITY_KILLED, lambda **kw: received.append(kw))

    lv = Level(0, lives=3, score=0, num_players=1)
    mine = Mine(100, 100)
    lv.mines.append(mine)
    enemy = EnemyTank(100, 100, tier=0, is_powerup_carrier=False)
    enemy.born_invuln = 0
    lv.enemies.append(enemy)
    lv.update(0.1)
    # 至少 1 个 ENTITY_KILLED (enemy 死亡)
    assert any(r.get("owner") == "powerup" for r in received)
    ev.clear()


def test_mine_lifetime_expires():
    """地雷 LIFETIME 到期自动消失 (不爆炸)."""
    mine = Mine(0, 0)
    mine.spawn_time = mine.spawn_time - 100  # 100s 前 spawn
    # update 返回 False (不爆炸)
    result = mine.update(0.1, [], [], __import__('utils.events', fromlist=['events']))
    assert result is False
    assert mine.dead
