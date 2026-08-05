"""C4 关卡扩充 6→15 (路线图 §6 阶段 C) 测试.

- LEVELS 列表从 8 关扩到 15 关
- LEVEL_DIFFICULTY 从 8 项扩到 15 项
- 新关卡类型分布: 12 campaign + 2 survival + 3 BOSS
- 新关卡布局合法 (17x17)
- 新关卡难度递增 (campaign 8 关 enemy_count 严格递增)
- get_level_difficulty 对新关卡返回正确配置
"""
import pytest

from settings import LEVEL_DIFFICULTY, GRID_W, GRID_H
from world.levels import LEVELS, get_level, get_level_difficulty, get_total_levels
from world.tilemap import TileMap


# ===== 1. 总体关卡数 =====

def test_total_levels_is_15():
    """C4: 总关数 = 15."""
    assert get_total_levels() == 15
    assert len(LEVELS) == 15
    assert len(LEVEL_DIFFICULTY) == 15


# ===== 2. 关卡模式分布 =====

def test_modes_distribution():
    """C4: 关卡模式分布 - 10 campaign + 2 survival + 3 BOSS = 15 关."""
    modes = [cfg.get("mode", "campaign") for cfg in LEVEL_DIFFICULTY]
    assert modes.count("campaign") == 10, f"expected 10 campaign, got {modes.count('campaign')}: {modes}"
    assert modes.count("survival") == 2, f"expected 2 survival, got {modes.count('survival')}: {modes}"
    assert modes.count("boss") == 3, f"expected 3 boss, got {modes.count('boss')}: {modes}"


def test_survival_levels_are_7_and_13():
    """C4: survival 关是关 7 (1-based 7, 0-based 6) 和关 13 (1-based 13, 0-based 12)."""
    assert get_level_difficulty(6).get("mode") == "survival"   # 关 7
    assert get_level_difficulty(12).get("mode") == "survival"  # 关 13


def test_boss_levels_are_8_14_15():
    """C4: BOSS 关是关 8/14/15 (0-based 7/13/14)."""
    for i in (7, 13, 14):
        assert get_level_difficulty(i).get("mode") == "boss", \
            f"level {i+1} should be boss, got {get_level_difficulty(i)}"


# ===== 3. 新增关卡布局合法 =====

def test_new_levels_layout_valid():
    """C4: 关 9-15 (0-based 8-14) 都是 17x17 合法布局."""
    for i in range(8, 15):
        layout = get_level(i)
        assert len(layout) == GRID_H, f"level {i+1}: should have {GRID_H} rows"
        for r, row in enumerate(layout):
            assert len(row) == GRID_W, f"level {i+1} row {r}: should be {GRID_W} cols, got {len(row)}: {row!r}"


def test_new_levels_have_player_spawn():
    """C4: 新增关卡都有玩家出生点 (P 字符)."""
    for i in range(8, 15):
        layout = get_level(i)
        assert any("P" in row for row in layout), \
            f"level {i+1}: should have player spawn 'P'"


def test_new_campaign_levels_have_base():
    """C4: 关 9-12 (新 campaign) 有基地 X."""
    for i in range(8, 12):  # 0-based 8-11 = 关 9-12
        layout = get_level(i)
        assert any("X" in row for row in layout), \
            f"campaign level {i+1}: should have base 'X'"


def test_new_survival_level_no_base():
    """C4: 关 13 (新 survival) 没有基地 X (B3 survival 风格)."""
    layout = get_level(12)  # 关 13
    assert not any("X" in row for row in layout), \
        f"survival level 13: should not have base 'X'"


def test_new_boss_levels_have_player_spawn():
    """C4: 关 14-15 (新 BOSS) 有玩家出生点 P (无基地, 但有玩家)."""
    for i in (13, 14):  # 0-based = 关 14, 15
        layout = get_level(i)
        assert any("P" in row for row in layout), \
            f"BOSS level {i+1}: should have player spawn 'P'"


# ===== 4. 难度递增 =====

def test_campaign_enemy_count_monotonic():
    """C4: campaign 关 (10 关) enemy_count 递增 (允许相同)."""
    campaign_indices = [i for i in range(15) if get_level_difficulty(i).get("mode", "campaign") == "campaign"]
    assert len(campaign_indices) == 10
    prev_count = -1
    for i in campaign_indices:
        cfg = get_level_difficulty(i)
        count = cfg["enemy_count"]
        assert count >= prev_count, \
            f"campaign level {i+1}: enemy_count {count} should be >= previous {prev_count}"
        prev_count = count


def test_final_campaign_harder_than_first():
    """C4: 关 12 (最终常规) enemy_count > 关 1."""
    first = get_level_difficulty(0)["enemy_count"]
    final = get_level_difficulty(11)["enemy_count"]
    assert final > first, f"level 12 enemy_count {final} should > level 1 {first}"


# ===== 5. TileMap 集成 =====

def test_new_levels_tile_map_creates():
    """C4: 新关卡能成功构造 TileMap (不抛错)."""
    for i in range(8, 15):
        layout = get_level(i)
        tm = TileMap.from_layout(layout)
        assert tm is not None
        # 所有新关卡应至少有 1 个玩家出生点
        assert tm.player_spawn is not None, f"level {i+1}: no player spawn"


# ===== 6. 回归: 老关卡不变 =====

def test_original_levels_unchanged():
    """C4: 关 1-8 (原有) 布局保持不变 (回归保护)."""
    # 检查关键特征 (不完全比对字符串, 因为重复)
    # 关 1: 经典入门, row 4 是 "....BB.S.S.BB...."
    assert "....BB.S.S.BB...." in get_level(0)
    # 关 7: survival, row 0 是 "E...........E...E"
    assert get_level(6)[0] == "E...........E...E"
    # 关 8: BOSS 房, row 5 是 ".....BBBBBBB....."
    assert get_level(7)[5] == ".....BBBBBBB....."
