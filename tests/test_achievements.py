"""C5 成就系统 (F10) 测试.

覆盖:
- 8 个成就定义
- Manager 持久化 (load/save/round-trip)
- 触发: first_blood / boss_slayer / powerup_collector / collector / legend /
        sharpshooter / pacifist / survivor
- 关卡级状态重置 (sharpshooter / pacifist 计数)
- 事件: ACHIEVEMENT_UNLOCKED
- Level 集成: 传 manager 后 on_level_start 调 + update 分发
- 幂等 (重复 unlock 不重复发事件)
"""
import os
import pytest
import tempfile
import shutil

from settings import PLAYER_LIVES
from utils import events
from utils import achievements as ach
from game.level import Level
from entities.enemy import EnemyTank
from entities.boss import BossTank
from entities.bullet import Bullet
from world.levels import get_level
from world.tilemap import TileMap


# ---- 测试夹具 ----
@pytest.fixture
def tmp_ach_path():
    """每个测试一个临时目录 + 成就文件路径 (隔离)."""
    d = tempfile.mkdtemp(prefix="ach_test_")
    yield os.path.join(d, "achievements.json")
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_events():
    """每个测试前后清空事件订阅 (避免跨测污染)."""
    events.clear()
    yield
    events.clear()


@pytest.fixture
def manager(tmp_ach_path):
    """每个测试一个新 Manager, 用临时文件."""
    return ach.Manager(path=tmp_ach_path)


# ===== 1. 成就定义 =====

def test_achievements_count_is_8():
    """C5: 8 个成就定义."""
    assert len(ach.ACHIEVEMENTS) == 8


def test_achievements_have_unique_ids():
    """所有成就 id 唯一."""
    ids = [a.id for a in ach.ACHIEVEMENTS]
    assert len(set(ids)) == len(ids), f"duplicate ids: {ids}"


def test_get_achievement_lookup():
    """通过 id 查 Achievement 定义."""
    a = ach.get_achievement("first_blood")
    assert a is not None
    assert a.id == "first_blood"
    assert a.name_key == "ach.first_blood.name"


def test_get_achievement_unknown_returns_none():
    """未知 id 返回 None."""
    assert ach.get_achievement("not_a_real_achievement") is None


# ===== 2. 持久化 =====

def test_manager_load_empty_file(tmp_ach_path):
    """无文件/损坏文件时 Manager 加载空数据 (不抛错)."""
    # 无文件
    m = ach.Manager(path=tmp_ach_path)
    assert m.unlocked == set()
    assert m.powerup_total == 0
    assert m.powerup_types == set()


def test_manager_save_load_roundtrip(manager, tmp_ach_path):
    """保存后重新加载, 数据一致."""
    manager._unlock("first_blood")
    manager._unlock("sharpshooter")
    manager.powerup_total = 5
    manager.powerup_types.add("star")
    manager.powerup_types.add("shield")
    manager.save()

    m2 = ach.Manager(path=tmp_ach_path)
    assert m2.is_unlocked("first_blood")
    assert m2.is_unlocked("sharpshooter")
    assert m2.powerup_total == 5
    assert m2.powerup_types == {"star", "shield"}


def test_manager_save_load_invalid_id_ignored(tmp_ach_path):
    """JSON 里有未知 id 时, 加载时过滤 (防御外部篡改)."""
    import json
    data = {
        "unlocked": ["first_blood", "fake_achievement"],
        "unlock_times": {"first_blood": 123.0, "fake_achievement": 456.0},
        "powerup_total": 0,
        "powerup_types": []
    }
    with open(tmp_ach_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    m = ach.Manager(path=tmp_ach_path)
    assert m.is_unlocked("first_blood")
    assert not m.is_unlocked("fake_achievement")
    assert "fake_achievement" not in m.unlock_times


def test_manager_save_load_corrupted_file(tmp_ach_path):
    """损坏 JSON 加载时 fallback (不抛错)."""
    with open(tmp_ach_path, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    m = ach.Manager(path=tmp_ach_path)
    assert m.unlocked == set()


# ===== 3. 触发: first_blood / boss_slayer =====

def test_first_blood_on_first_kill(manager):
    """击杀第一个敌人 -> first_blood 解锁."""
    manager._on_entity_killed(kind="enemy", owner="player")
    assert manager.is_unlocked("first_blood")


def test_first_blood_idempotent(manager):
    """first_blood 解锁一次后再触发不重复发事件."""
    received = []
    events.subscribe(events.ACHIEVEMENT_UNLOCKED, lambda **kw: received.append(kw))
    manager._on_entity_killed(kind="enemy", owner="player")
    manager._on_entity_killed(kind="enemy", owner="player")
    first_blood_unlocks = [r for r in received if r.get("id") == "first_blood"]
    assert len(first_blood_unlocks) == 1


def test_first_blood_not_triggered_by_powerup_owner(manager):
    """owner=powerup (grenade/自爆) 不触发 first_blood."""
    manager._on_entity_killed(kind="enemy", owner="powerup")
    assert not manager.is_unlocked("first_blood")


def test_boss_slayer_on_boss_kill(manager):
    """BOSS 击杀 -> boss_slayer."""
    manager._on_entity_killed(kind="enemy", owner="player", is_boss=True)
    assert manager.is_unlocked("boss_slayer")


def test_boss_slayer_not_on_normal_enemy(manager):
    """非 BOSS 击杀不触发 boss_slayer."""
    manager._on_entity_killed(kind="enemy", owner="player", is_boss=False)
    assert not manager.is_unlocked("boss_slayer")


# ===== 4. 触发: powerup_collector / collector =====

def test_powerup_collector_at_10(manager):
    """累计 10 道具 -> powerup_collector."""
    for i in range(10):
        manager._on_powerup_picked(type="star")
    assert manager.is_unlocked("powerup_collector")


def test_powerup_collector_not_at_9(manager):
    """累计 9 道具不触发."""
    for i in range(9):
        manager._on_powerup_picked(type="star")
    assert not manager.is_unlocked("powerup_collector")


def test_collector_at_5_different_types(manager):
    """5 种不同道具 -> collector."""
    for t in ("star", "shield", "grenade", "clock", "shovel"):
        manager._on_powerup_picked(type=t)
    assert manager.is_unlocked("collector")


def test_collector_not_at_4_types(manager):
    """4 种不同道具不触发."""
    for t in ("star", "shield", "grenade", "clock"):
        manager._on_powerup_picked(type=t)
    assert not manager.is_unlocked("collector")


# ===== 5. 触发: sharpshooter / pacifist (关卡级) =====

def test_sharpshooter_at_5_consecutive(manager):
    """连续 5 次击杀 -> sharpshooter."""
    manager.on_level_start("campaign")
    for _ in range(5):
        manager._on_entity_killed(kind="enemy", owner="player")
    assert manager.is_unlocked("sharpshooter")


def test_sharpshooter_not_at_4(manager):
    """4 次不触发."""
    manager.on_level_start("campaign")
    for _ in range(4):
        manager._on_entity_killed(kind="enemy", owner="player")
    assert not manager.is_unlocked("sharpshooter")


def test_sharpshooter_resets_per_level(manager):
    """关卡开始时 consecutive_hits 重置."""
    manager.on_level_start("campaign")
    for _ in range(4):
        manager._on_entity_killed(kind="enemy", owner="player")
    # 重新开始关卡 -> 计数清零
    manager.on_level_start("campaign")
    for _ in range(4):
        manager._on_entity_killed(kind="enemy", owner="player")
    assert not manager.is_unlocked("sharpshooter")


def test_pacifist_on_clean_level_completion(manager):
    """关卡不击毁敌人通关 -> pacifist."""
    manager.on_level_start("campaign")
    manager._on_level_completed(level_index=0)
    assert manager.is_unlocked("pacifist")


def test_pacifist_not_when_killed_one(manager):
    """击毁 1 个敌人后通关不触发 pacifist."""
    manager.on_level_start("campaign")
    manager._on_entity_killed(kind="enemy", owner="player")
    manager._on_level_completed(level_index=0)
    assert not manager.is_unlocked("pacifist")


def test_pacifist_resets_per_level(manager):
    """关卡重置 enemies_killed_in_level."""
    manager.on_level_start("campaign")
    manager._on_entity_killed(kind="enemy", owner="player")
    manager._on_level_completed(level_index=0)
    assert not manager.is_unlocked("pacifist")
    # 下一关不杀
    manager.on_level_start("campaign")
    manager._on_level_completed(level_index=1)
    assert manager.is_unlocked("pacifist")


# ===== 6. 触发: legend / survivor =====

def test_legend_on_level_15(manager):
    """通关关 15 (0-based 14) -> legend."""
    manager.on_level_start("campaign")
    manager._on_level_completed(level_index=14)
    assert manager.is_unlocked("legend")


def test_legend_not_on_other_level(manager):
    """通关关 14 (0-based 13) 不触发 legend."""
    manager.on_level_start("campaign")
    manager._on_level_completed(level_index=13)
    assert not manager.is_unlocked("legend")


def test_survivor_at_60_seconds(manager):
    """生存模式撑过 60s -> survivor."""
    manager.on_level_start("survival")
    manager.on_level_tick(dt=30.0, mode="survival")
    assert not manager.is_unlocked("survivor")
    manager.on_level_tick(dt=30.1, mode="survival")
    assert manager.is_unlocked("survivor")


def test_survivor_only_in_survival_mode(manager):
    """campaign 模式计时不触发 survivor."""
    manager.on_level_start("campaign")
    manager.on_level_tick(dt=100.0, mode="campaign")
    assert not manager.is_unlocked("survivor")


# ===== 7. 事件分发 =====

def test_unlock_publishes_event(manager):
    """解锁时 publish ACHIEVEMENT_UNLOCKED 事件."""
    received = []
    events.subscribe(events.ACHIEVEMENT_UNLOCKED, lambda **kw: received.append(kw))
    manager._unlock("first_blood")
    assert len(received) == 1
    assert received[0]["id"] == "first_blood"


def test_unlock_idempotent_no_event(manager):
    """已解锁再 unlock 不重复发事件."""
    received = []
    events.subscribe(events.ACHIEVEMENT_UNLOCKED, lambda **kw: received.append(kw))
    manager._unlock("first_blood")
    manager._unlock("first_blood")
    assert len(received) == 1


def test_unlock_unknown_id_no_event(manager):
    """未知 id unlock 不发事件也不抛错."""
    received = []
    events.subscribe(events.ACHIEVEMENT_UNLOCKED, lambda **kw: received.append(kw))
    result = manager._unlock("not_a_real_achievement")
    assert result is False
    assert len(received) == 0


# ===== 8. 事件订阅 =====

def test_manager_subscribes_to_events(manager):
    """Manager __init__ 自动订阅 ENTITY_KILLED/POWERUP_PICKED/LEVEL_COMPLETED."""
    assert events.subscriber_count(events.ENTITY_KILLED) >= 1
    assert events.subscriber_count(events.POWERUP_PICKED) >= 1
    assert events.subscriber_count(events.LEVEL_COMPLETED) >= 1


def test_manager_close_unsubscribes(manager):
    """close() 取消订阅 (清理)."""
    initial = events.subscriber_count(events.ENTITY_KILLED)
    manager.close()
    assert events.subscriber_count(events.ENTITY_KILLED) == initial - 1


# ===== 9. Level 集成 =====

def test_level_with_manager(manager):
    """Level 接受 manager 参数 + on_level_start 触发."""
    lv = Level(0, lives=PLAYER_LIVES, score=0, achievements=manager)
    assert lv.achievements is manager


def test_level_without_manager():
    """Level 不传 manager 也能工作 (向后兼容)."""
    lv = Level(0, lives=PLAYER_LIVES, score=0)
    assert lv.achievements is None


def test_level_kill_enemy_unlocks_first_blood_via_event(manager):
    """Level 内击杀敌人通过 events 发布, manager 收到并解锁 first_blood."""
    lv = Level(0, lives=PLAYER_LIVES, score=0, achievements=manager)
    # 制造一个敌人 + 子弹让玩家击杀
    e = EnemyTank(MAP_X_TEST := 100, 100)
    lv.enemies.append(e)
    # 跳过出生占位检测, 直接让 e 死亡
    e.dead = True
    lv.update(0.01)
    # manager 应收到 ENTITY_KILLED -> first_blood 解锁
    assert manager.is_unlocked("first_blood")


def test_level_boss_kill_unlocks_boss_slayer(manager):
    """BOSS 死 (通过 ENTITY_KILLED 事件) -> boss_slayer."""
    lv = Level(7, lives=PLAYER_LIVES, score=0, achievements=manager)
    boss = next(e for e in lv.enemies if isinstance(e, BossTank))
    boss.dead = True
    lv.update(0.01)
    assert manager.is_unlocked("boss_slayer")


# ===== 10. 查询 API =====

def test_unlocked_count(manager):
    """unlocked_count 反映 unlocked set 大小."""
    assert manager.unlocked_count() == 0
    manager._unlock("first_blood")
    assert manager.unlocked_count() == 1
    manager._unlock("boss_slayer")
    assert manager.unlocked_count() == 2


def test_total_count(manager):
    """total_count 反映 ACHIEVEMENTS 长度."""
    assert manager.total_count() == 8


def test_recent_unlocks(manager):
    """recent_unlocks 记录本会话新解锁的 id."""
    manager._unlock("first_blood")
    manager._unlock("sharpshooter")
    assert "first_blood" in manager.recent_unlocks
    assert "sharpshooter" in manager.recent_unlocks
    manager.clear_recent()
    assert manager.recent_unlocks == []


# ===== 11. reset_for_test 工具 =====

def test_reset_for_test(tmp_ach_path):
    """reset_for_test 删除文件 (测试间隔离)."""
    with open(tmp_ach_path, "w") as f:
        f.write("{}")
    assert os.path.exists(tmp_ach_path)
    ach.reset_for_test(path=tmp_ach_path)
    assert not os.path.exists(tmp_ach_path)
