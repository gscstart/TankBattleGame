"""C2 BOSS 关卡 (F5) 测试.

- Tank 加 hp 字段 (默认 1), on_hit 减 hp 而非直接 dead
- BossTank 实体: hp=10, breaks_steel=True, 慢速
- BOSS 死亡 publish ENTITY_KILLED 事件 (kind=enemy, owner=player)
- 关 8 BOSS 关卡: 1 个 BOSS 出生, BOSS 死亡触发 LEVEL_COMPLETED
- BOSS 满级 (player 升级到 level 2 子弹破钢墙) 应对 BOSS 有效
"""
import pytest
import pygame

from settings import TILE, GRID_W, GRID_H, MAP_X, MAP_Y
from settings import BOSS_HP, BOSS_SPEED, BOSS_FIRE_COOLDOWN, PLAYER_LIVES
from entities.tank import Tank
from entities.boss import BossTank
from entities.bullet import Bullet
from entities.enemy import EnemyTank
from entities.player import PlayerTank
from world.tilemap import TileMap
from world.levels import LEVELS, get_level, get_level_difficulty, get_total_levels
from game.level import Level
from utils import events


# ---- Tank 基类 hp 字段 ----

def test_tank_default_hp_is_1():
    """Tank 默认 hp=1 (普通坦克一弹死亡)."""
    t = Tank(0, 0, (0, -1), (200, 100, 100), (100, 50, 50))
    assert t.hp == 1


def test_tank_on_hit_with_hp_1_dies():
    """hp=1 时一弹死."""
    t = Tank(0, 0, (0, -1), (200, 100, 100), (100, 50, 50))
    assert t.hp == 1
    bullet = Bullet(10, 10, (1, 0), owner="player")
    t.on_hit(bullet)
    assert t.dead is True


def test_tank_on_hit_with_hp_gt_1_does_not_die():
    """hp>1 时一弹只减血."""
    t = Tank(0, 0, (0, -1), (200, 100, 100), (100, 50, 50))
    t.hp = 5
    bullet = Bullet(10, 10, (1, 0), owner="player")
    t.on_hit(bullet)
    assert t.dead is False
    assert t.hp == 4


def test_tank_with_hp_5_takes_5_hits_to_die():
    """hp=5 时 5 弹才死."""
    t = Tank(0, 0, (0, -1), (200, 100, 100), (100, 50, 50))
    t.hp = 5
    for i in range(4):
        bullet = Bullet(10, 10, (1, 0), owner="player")
        t.on_hit(bullet)
        assert t.dead is False
        assert t.hp == 4 - i
    # 第 5 弹
    bullet = Bullet(10, 10, (1, 0), owner="player")
    t.on_hit(bullet)
    assert t.dead is True
    assert t.hp == 0


def test_tank_invuln_blocks_on_hit():
    """flashing_time>0 时 on_hit 无效 (保留 A 阶段无敌)."""
    t = Tank(0, 0, (0, -1), (200, 100, 100), (100, 50, 50))
    t.hp = 5
    t.flashing_time = 2.0
    bullet = Bullet(10, 10, (1, 0), owner="player")
    t.on_hit(bullet)
    assert t.dead is False
    assert t.hp == 5  # 无敌不减血


# ---- BossTank 实体 ----

def test_boss_default_hp_matches_constant():
    """BossTank 默认 hp = BOSS_HP 常量 (10)."""
    b = BossTank(0, 0)
    assert b.hp == BOSS_HP
    assert b.hp >= 5  # BOSS 至少 5 血, 不可能 1 弹死


def test_boss_color_distinct():
    """BOSS 颜色显著区别于普通敌人 (B1 红闪/tier)."""
    b = BossTank(0, 0)
    # BOSS 紫色
    assert b.color == (180, 80, 200) or b.color != (200, 100, 100)  # 不红


def test_boss_breaks_steel():
    """BOSS 子弹能破钢墙 (路线图 §3.1 关键差异)."""
    b = BossTank(0, 0)
    assert b.breaks_steel is True


def test_boss_slow_speed():
    """BOSS 速度 < 普通敌人 (路线图 §3.1 慢但血多)."""
    b = BossTank(0, 0)
    assert b.speed <= BOSS_SPEED
    # 普通敌人 ENEMY_SPEED=72, BOSS 应更慢
    assert b.speed < 72


def test_boss_survives_many_hits():
    """BOSS 至少能挨 BOSS_HP - 1 发子弹不死."""
    b = BossTank(0, 0)
    for i in range(BOSS_HP - 1):
        bullet = Bullet(10, 10, (1, 0), owner="player")
        b.on_hit(bullet)
    assert b.dead is False
    assert b.hp == 1


def test_boss_dies_at_zero_hp():
    """BOSS hp 减到 0 时 dead=True."""
    b = BossTank(0, 0)
    for i in range(BOSS_HP):
        bullet = Bullet(10, 10, (1, 0), owner="player")
        b.on_hit(bullet)
    assert b.dead is True
    assert b.hp == 0


def test_boss_can_shoot():
    """BOSS 能开火 (有 bullets list)."""
    b = BossTank(0, 0)
    b.dir = (0, 1)  # 朝下
    b.cooldown = 0
    bullets = []
    b.shoot(bullets)
    assert len(bullets) == 1
    # 子弹能破钢墙
    assert bullets[0].can_break_steel is True


# ---- 关 8 集成 ----

def test_level_8_exists():
    """关 8 BOSS 关卡已加入 LEVELS."""
    assert get_total_levels() >= 8, f"expected >= 8 levels, got {len(LEVELS)}"


def test_level_8_is_boss_mode():
    """关 8 LEVEL_DIFFICULTY mode='boss'."""
    cfg = get_level_difficulty(7)  # 0-based index 7 = 关 8
    assert cfg.get("mode") == "boss"
    assert cfg.get("boss_count", 0) >= 1


def test_level_8_spawns_boss():
    """关 8 创建 Level 时, enemies 列表含 1 个 BossTank (模式 boss 时不生成普通敌人)."""
    lv = Level(7, lives=PLAYER_LIVES, score=0)  # 0-based 7 = 关 8
    assert lv.mode == "boss"
    # 1 个 BOSS
    boss_count = sum(1 for e in lv.enemies if isinstance(e, BossTank))
    assert boss_count == 1


def test_boss_kill_completes_level():
    """BOSS 死亡触发 level.completed=True (不是 base_destroyed 路径)."""
    lv = Level(7, lives=PLAYER_LIVES, score=0)
    # 找 BOSS
    bosses = [e for e in lv.enemies if isinstance(e, BossTank)]
    assert len(bosses) == 1
    boss = bosses[0]
    # 杀 BOSS
    while not boss.dead:
        bullet = Bullet(10, 10, (1, 0), owner="player")
        boss.on_hit(bullet)
    # level.update 应检测到 BOSS 死亡 -> completed
    # 先清掉死敌人 (level.update 末尾会清)
    lv.enemies = [e for e in lv.enemies if not e.dead]
    lv.update(0.01)
    assert lv.completed is True
    assert lv.failed is False


def test_boss_kill_publishes_entity_killed():
    """BOSS 死亡 publish ENTITY_KILLED 事件 (owner=player)."""
    events.clear()
    received = []
    events.subscribe(events.ENTITY_KILLED, lambda **kw: received.append(kw))

    lv = Level(7, lives=PLAYER_LIVES, score=0)
    boss = next(e for e in lv.enemies if isinstance(e, BossTank))
    # 杀 BOSS (但 BOSS 仍在 self.enemies 列表, 让 level.update 处理清理+publish)
    while not boss.dead:
        bullet = Bullet(10, 10, (1, 0), owner="player")
        boss.on_hit(bullet)
    lv.update(0.01)
    # 应收到 BOSS 死亡事件 (level.update 末尾"清理死亡"块 publish)
    boss_kills = [r for r in received if r.get("kind") == "enemy"]
    assert len(boss_kills) >= 1
    events.clear()


def test_boss_kill_does_not_destroy_base():
    """BOSS 死 = 通关 (不是 base 被毁)."""
    events.clear()
    received = []
    events.subscribe(events.BASE_DESTROYED, lambda **kw: received.append(kw))
    lv = Level(7, lives=PLAYER_LIVES, score=0)
    boss = next(e for e in lv.enemies if isinstance(e, BossTank))
    while not boss.dead:
        bullet = Bullet(10, 10, (1, 0), owner="player")
        boss.on_hit(bullet)
    lv.enemies = [e for e in lv.enemies if not e.dead]
    lv.update(0.01)
    # BASE_DESTROYED 不应发
    assert len(received) == 0
    # BOSS 模式没基地, level.failed 应 False
    assert lv.failed is False
    events.clear()


# ---- 边界: BOSS 关不生成普通敌人 ----

def test_boss_level_no_normal_enemies():
    """BOSS 关不生成普通敌人 (enemies_to_spawn=0)."""
    lv = Level(7, lives=PLAYER_LIVES, score=0)
    # 不应有非 BOSS 的敌人
    non_boss = [e for e in lv.enemies if not isinstance(e, BossTank)]
    assert len(non_boss) == 0
    # enemies_to_spawn 应为 0
    assert lv.enemies_to_spawn == 0


def test_boss_update_signature_matches_enemy():
    """review fix: BOSS.update 签名跟 EnemyTank 对齐, 不然 level.py 通用调用会 crash.

    BossTank.update 跟 EnemyTank.update 第 5 个位置参数都是 player
    (BOSS 不直接用 player, 但保留签名一致避免 level.py 误传).
    """
    import inspect
    boss_sig = inspect.signature(BossTank.update)
    enemy_sig = inspect.signature(EnemyTank.update)
    boss_params = list(boss_sig.parameters.keys())
    enemy_params = list(enemy_sig.parameters.keys())
    # 前 5 个参数名应该一致 (self, dt, tilemap, other_tanks, bullets, player)
    assert boss_params[:6] == enemy_params[:6], \
        f"BossTank.update 签名 {boss_params[:6]} 应跟 EnemyTank {enemy_params[:6]} 对齐"


def test_boss_full_update_loop_does_not_crash():
    """regression: 完整 BOSS update loop 不抛 TypeError (C2 review 漏掉, 因 BOSS dead 早退).

    跑 60 帧 (1 秒) 看 BOSS 真活着时 update 正常, 玩家也能正常 update.
    """
    lv = Level(7, lives=PLAYER_LIVES, score=0)
    boss = next(e for e in lv.enemies if isinstance(e, BossTank))
    # BOSS 必须活着 (避免 if dead: return 早退)
    assert not boss.dead
    # 跑 60 帧不抛错
    tilemap = lv.tilemap
    for _ in range(60):
        lv.update(0.01)
