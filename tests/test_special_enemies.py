"""C3 特殊敌人 5 种 (路线图 §6 阶段 C - F18) 测试.

- SuicideEnemy 自爆: 玩家距离 < 80 触发自爆, 半径 64 敌人同死
- StealthEnemy 隐形: 周期显形 0.3s / 隐行 1.7s
- ArmorEnemy 装甲: hp=3
- RocketEnemy 火箭: 子弹 2x 速 + 破钢墙
- BounceEnemy 弹跳: 子弹打墙反弹 1 次
- Level._spawn_enemy 15% 概率生成特殊敌人 (campaign 模式)
"""
import pytest
import random
import pygame

from settings import (
    TILE, GRID_W, GRID_H, MAP_X, MAP_Y, PLAYER_LIVES,
    SPECIAL_ENEMY_CHANCE, SUICIDE_BLAST_TRIGGER_RADIUS, SUICIDE_BLAST_DAMAGE_RADIUS,
    ARMOR_HP, ROCKET_SPEED_MULT, BOUNCE_COUNT, SPECIAL_COLORS,
    STEALTH_CYCLE, STEALTH_VISIBLE_FRAC, BULLET_SPEED,
)
from entities.enemy import EnemyTank
from entities.player import PlayerTank
from entities.bullet import Bullet
from entities.special import (
    SuicideEnemy, StealthEnemy, ArmorEnemy, RocketEnemy, BounceEnemy,
    SPECIAL_ENEMY_CLASSES,
)
from world.tilemap import TileMap
from world.levels import get_level
from game.level import Level
from utils import events


# ===== 1. SuicideEnemy 自爆者 =====

def test_suicide_creation():
    """SuicideEnemy 创建 + 颜色正确."""
    s = SuicideEnemy(0, 0)
    assert s.color == SPECIAL_COLORS["suicide"]
    assert isinstance(s, EnemyTank)  # 是敌人


def test_suicide_detonates_near_player():
    """玩家距离 < 80px 时自爆 (自身 dead)."""
    s = SuicideEnemy(0, 0)
    p = PlayerTank(50, 0)  # 距 (18, 18) 玩家距离 = sqrt(50^2+18^2) ≈ 53px < 80
    # 构造 tilemap + other_tanks + bullets (空)
    tilemap = TileMap.from_layout(get_level(0))
    s.update(0.01, tilemap, other_tanks=[], bullets=[], player=p, effects=[])
    assert s.dead is True


def test_suicide_does_not_detonate_far_player():
    """玩家距离 > 80px 时不自爆."""
    s = SuicideEnemy(0, 0)
    p = PlayerTank(200, 0)  # 距 (18, 18) 玩家距离 ≈ 196px > 80
    tilemap = TileMap.from_layout(get_level(0))
    s.update(0.01, tilemap, other_tanks=[], bullets=[], player=p, effects=[])
    assert s.dead is False


def test_suicide_kills_nearby_enemies():
    """自爆半径 64px 内敌人同死."""
    tilemap = TileMap.from_layout(get_level(0))
    # 自爆者 + 另一个敌人距离 30px (在 64 半径内)
    s = SuicideEnemy(0, 0)
    other = EnemyTank(30, 0)  # 距 (18, 18) = 30px < 64
    s.update(0.01, tilemap, other_tanks=[other], bullets=[], player=PlayerTank(50, 0), effects=[])
    assert s.dead is True
    assert other.dead is True


def test_suicide_spawns_explosion_effect():
    """自爆时加 Explosion 特效."""
    tilemap = TileMap.from_layout(get_level(0))
    s = SuicideEnemy(0, 0)
    effects = []
    s.update(0.01, tilemap, other_tanks=[], bullets=[],
             player=PlayerTank(50, 0), effects=effects)
    # Explosion 特效应已加
    assert any(e.__class__.__name__ == "Explosion" for e in effects)


def test_suicide_no_double_score():
    """C3 review: 自爆者自杀不重复加分 (避免 level 末尾"清理死亡"块重复计分)."""
    events.clear()
    received = []
    events.subscribe(events.ENTITY_KILLED, lambda **kw: received.append(kw))

    lv = Level(0, lives=PLAYER_LIVES, score=0)
    # 玩家在 col=8 row=14, 自爆者放 col=6 row=14 (距玩家 72px < 80 触发半径)
    p_cx, p_cy = lv.players[0].rect.center
    # 反推 col/row: col=6 row=14 的中心 (p_cx - 2*TILE, p_cy)
    s = SuicideEnemy(p_cx - 2 * TILE, p_cy - TILE // 2)
    lv.enemies.append(s)
    initial_score = lv.score

    # 模拟玩家靠近自爆者 (s.update 内自爆)
    s.update(0.01, lv.tilemap, other_tanks=[], bullets=[],
             player=lv.players[0], effects=lv.effects)
    # 触发 level.update 一帧 (清理 dead 敌人 + 发事件)
    lv.update(0.01)

    # 自爆者应只发一次 ENTITY_KILLED (owner=powerup, score=0)
    suicide_kills = [r for r in received
                     if r.get("kind") == "enemy" and r.get("owner") == "powerup"]
    assert len(suicide_kills) == 1, f"expected 1 self-kill event, got {len(suicide_kills)}: {received}"
    # 自爆者自杀不加分
    assert lv.score == initial_score, f"suicide self should not add score, got {lv.score}"
    events.clear()


# ===== 2. StealthEnemy 隐形者 =====

def test_stealth_creation():
    """StealthEnemy 创建 + 颜色正确."""
    s = StealthEnemy(0, 0)
    assert s.color == SPECIAL_COLORS["stealth"]
    assert isinstance(s, EnemyTank)


def test_stealth_initial_phase_randomized():
    """StealthEnemy 初始相位随机 (避免一群同步显形)."""
    random.seed(42)
    s1 = StealthEnemy(0, 0)
    s2 = StealthEnemy(0, 0)
    # 两次创建相位不同 (高概率, 因为 random.uniform)
    assert s1.stealth_phase != s2.stealth_phase


def test_stealth_toggles_visibility():
    """StealthEnemy 周期切换显形/隐行."""
    s = StealthEnemy(0, 0)
    # 强制 phase=0.0 -> 显形期
    s.stealth_phase = 0.0
    assert s.is_visible is True
    # phase 在显形窗口外 (1.0s) -> 隐行
    s.stealth_phase = STEALTH_CYCLE * 0.5
    assert s.is_visible is False
    # phase 跨过周期 -> 重新显形
    s.stealth_phase = STEALTH_CYCLE + 0.1
    assert s.is_visible is True


def test_stealth_invisible_does_not_draw():
    """隐行期 draw() 不画 (不抛错)."""
    s = StealthEnemy(0, 0)
    s.stealth_phase = STEALTH_CYCLE * 0.5  # 隐行期 (cycle 中间)
    assert s.is_visible is False
    surface = pygame.Surface((100, 100))
    # 应该直接 return 不抛错
    s.draw(surface)


def test_stealth_visible_draws():
    """显形期 draw() 调父类 (不抛错)."""
    s = StealthEnemy(0, 0)
    s.stealth_phase = 0.0  # 显形期
    assert s.is_visible is True
    surface = pygame.Surface((100, 100))
    s.draw(surface)


def test_stealth_phase_advances_in_update():
    """update 时 stealth_phase 推进."""
    s = StealthEnemy(0, 0)
    initial = s.stealth_phase
    tilemap = TileMap.from_layout(get_level(0))
    s.update(0.1, tilemap, other_tanks=[], bullets=[],
             player=PlayerTank(500, 0), effects=[])
    assert s.stealth_phase != initial


# ===== 3. ArmorEnemy 装甲者 =====

def test_armor_creation():
    """ArmorEnemy 创建 + 颜色正确."""
    a = ArmorEnemy(0, 0)
    assert a.color == SPECIAL_COLORS["armor"]
    assert isinstance(a, EnemyTank)


def test_armor_has_3_hp():
    """ArmorEnemy hp=3."""
    a = ArmorEnemy(0, 0)
    assert a.hp == ARMOR_HP
    assert a.hp == 3


def test_armor_takes_3_hits_to_die():
    """ArmorEnemy 3 弹才死."""
    a = ArmorEnemy(0, 0)
    # 绕开 born_invuln
    a.born_invuln = 0.0
    for i in range(2):
        b = Bullet(10, 10, (1, 0), owner="player")
        a.on_hit(b)
        assert a.dead is False
        assert a.hp == ARMOR_HP - 1 - i
    # 第 3 弹死
    b = Bullet(10, 10, (1, 0), owner="player")
    a.on_hit(b)
    assert a.dead is True
    assert a.hp == 0


# ===== 4. RocketEnemy 火箭者 =====

def test_rocket_creation():
    """RocketEnemy 创建 + 颜色正确."""
    r = RocketEnemy(0, 0)
    assert r.color == SPECIAL_COLORS["rocket"]
    assert isinstance(r, EnemyTank)


def test_rocket_bullet_2x_speed():
    """RocketEnemy 子弹 speed_multiplier=2."""
    r = RocketEnemy(0, 0)
    r.cooldown = 0  # 绕开冷却
    r.dir = (0, 1)
    bullets = []
    r.shoot(bullets)
    assert len(bullets) == 1
    assert bullets[0].speed_multiplier == ROCKET_SPEED_MULT
    assert bullets[0].speed_multiplier == 2.0


def test_rocket_bullet_breaks_steel():
    """RocketEnemy 子弹能破钢墙."""
    r = RocketEnemy(0, 0)
    r.cooldown = 0
    r.dir = (0, 1)
    bullets = []
    r.shoot(bullets)
    assert bullets[0].can_break_steel is True


# ===== 5. BounceEnemy 弹跳者 =====

def test_bounce_creation():
    """BounceEnemy 创建 + 颜色正确."""
    b = BounceEnemy(0, 0)
    assert b.color == SPECIAL_COLORS["bounce"]
    assert isinstance(b, EnemyTank)


def test_bounce_bullet_bounces_left_1():
    """BounceEnemy 子弹 bounces_left=1."""
    b = BounceEnemy(0, 0)
    b.cooldown = 0
    b.dir = (0, 1)
    bullets = []
    b.shoot(bullets)
    assert bullets[0].bounces_left == BOUNCE_COUNT
    assert bullets[0].bounces_left == 1


def test_bullet_bounces_once_on_wall():
    """bounces_left=1 子弹撞墙反弹 1 次."""
    # 把 bullet 直接放在地图右边界外, 让边界检测立即触发
    b = Bullet(MAP_X + GRID_W * TILE + 5, MAP_Y + TILE, (1, 0), owner="enemy")
    b.bounces_left = 1
    tilemap = TileMap.from_layout(get_level(0))
    b.update(0.01, tilemap, [], [], lambda t: None, effects=[])
    # 反弹了
    assert b.bounces_left == 0
    # 方向反了
    assert b.direction == (-1, 0)
    # bullet 修正回地图内
    assert b.rect.left < MAP_X + GRID_W * TILE


def test_bullet_no_bounce_dies_on_wall():
    """bounces_left=0 子弹撞墙立即死."""
    b = Bullet(MAP_X + GRID_W * TILE + 5, MAP_Y + TILE, (1, 0), owner="enemy")
    b.bounces_left = 0
    tilemap = TileMap.from_layout(get_level(0))
    b.update(0.01, tilemap, [], [], lambda t: None, effects=[])
    assert b.dead is True


def test_bullet_default_no_bounce():
    """普通子弹 bounces_left=0 (默认不弹)."""
    b = Bullet(10, 10, (1, 0), owner="player")
    assert b.bounces_left == 0
    assert b.speed_multiplier == 1.0


# ===== 6. Level 集成 =====

def test_level_spawns_special_enemy_with_seed():
    """campaign 模式 _spawn_enemy 会偶尔生成特殊敌人 (用 random.seed 命中)."""
    random.seed(1)  # seed=1 期望 ~4/15 命中特殊敌人
    lv = Level(0, lives=PLAYER_LIVES, score=0)  # 关 1 = campaign
    assert lv.mode == "campaign"
    # 反复 _spawn_enemy 直到 enemies_to_spawn=0 或撞上不可生成 (出生点被占) 退避.
    # 限制 max_iter 避免 _spawn_enemy 在所有出生点被占时死循环.
    found = set()
    max_iter = 200
    i = 0
    while lv.enemies_to_spawn > 0 and i < max_iter:
        e = lv._spawn_enemy()
        i += 1
        if e is not None:
            for cls in SPECIAL_ENEMY_CLASSES:
                if isinstance(e, cls):
                    found.add(cls.__name__)
    # 至少出现 1 种特殊敌人 (15% 概率, 期望 ~2-3 个)
    assert len(found) >= 1, f"expected at least 1 special enemy, found {found}"


def test_level_survival_mode_no_special():
    """survival 模式不生成特殊敌人 (保持稳定节奏)."""
    from settings import LEVEL_DIFFICULTY
    # 关 7 是 survival
    lv = Level(6, lives=PLAYER_LIVES, score=0)  # 0-based 6 = 关 7
    assert lv.mode == "survival"
    # 尝试 spawn 多次
    for _ in range(20):
        e = lv._spawn_enemy()
        if e is None:
            break
        # 必须是普通 EnemyTank
        assert type(e) is EnemyTank, f"survival got {type(e).__name__}"


def test_special_enemy_classes_count():
    """特殊敌人必须有 5 个类."""
    assert len(SPECIAL_ENEMY_CLASSES) == 5
    expected = {SuicideEnemy, StealthEnemy, ArmorEnemy, RocketEnemy, BounceEnemy}
    assert set(SPECIAL_ENEMY_CLASSES) == expected
