"""B5 冰面打滑 (F19) 测试.

PlayerTank 在冰面 TileIce 上时:
- 松开方向键仍继续滑动 (slide_timer 不衰减)
- update_snap 跳过吸附
- 离开冰面后恢复正常 (slide_timer 衰减到 0, 吸附对齐)

不在冰面:
- 行为不变 (slide_timer 0.1s 衰减)
"""
import pytest
import pygame

from settings import TILE, GRID_W, GRID_H, MAP_X, MAP_Y
from world.tilemap import TileMap
from world.tile import TileIce, TileEmpty
from entities.player import PlayerTank


def _make_tilemap_with_ice(ice_cells: list) -> TileMap:
    """构造 tilemap, 全部 TileEmpty, 指定格放 TileIce."""
    grid = [[TileEmpty() for _ in range(GRID_W)] for _ in range(GRID_H)]
    for col, row in ice_cells:
        grid[row][col] = TileIce()
    # 用 from_layout: 把 ice_cells 转成 layout 字符串
    layout = []
    for r in range(GRID_H):
        row_chars = []
        for c in range(GRID_W):
            if (c, r) in ice_cells:
                row_chars.append('I')
            elif c == 8 and r == 15:
                row_chars.append('P')
            else:
                row_chars.append('.')
        layout.append("".join(row_chars))
    return TileMap.from_layout(layout)


def _place_player_on_tile(player: PlayerTank, col: int, row: int):
    """把玩家 rect 放到 (col, row) 格子的世界坐标."""
    player.rect.x = MAP_X + col * TILE
    player.rect.y = MAP_Y + row * TILE


# ---- PlayerTank.on_ice 字段 ----

def test_player_has_on_ice_field():
    """PlayerTank 应有 on_ice 字段 (默认 False)."""
    p = PlayerTank(0, 0)
    assert hasattr(p, 'on_ice')
    assert p.on_ice is False


# ---- 冰面检测 ----

def test_on_ice_detected_when_on_ice_tile():
    """玩家在 TileIce 上时 on_ice=True."""
    tilemap = _make_tilemap_with_ice([(8, 15)])
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)
    p.update(0.1, tilemap, [], [])
    assert p.on_ice is True


def test_on_ice_false_on_empty_tile():
    """玩家在 TileEmpty 上时 on_ice=False."""
    tilemap = _make_tilemap_with_ice([])  # 全部空
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)
    p.update(0.1, tilemap, [], [])
    assert p.on_ice is False


# ---- 冰面滑行 (核心) ----

def test_player_slides_on_ice_when_keys_released():
    """B5: 玩家在冰面 + 松键 -> 仍继续滑动, 位置改变."""
    tilemap = _make_tilemap_with_ice([(8, 15)])
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)
    # 先按 UP 键设置方向并滑动
    p.keys["up"] = True
    p.key_press_time["up"] = 0.001
    p.update(0.05, tilemap, [], [])
    initial_y = p.rect.y
    initial_x = p.rect.x
    # 松开 UP 键 (模拟玩家松手)
    p.keys["up"] = False
    # 跑若干帧, 玩家仍应按 slide_dir (UP) 滑动
    for _ in range(5):
        p.update(0.05, tilemap, [], [])
    # 在冰面: y 应继续减少 (向上滑)
    assert p.rect.y < initial_y, \
        f"on ice, player should keep sliding UP, y={p.rect.y} initial={initial_y}"


def test_player_stops_on_normal_ground_when_keys_released():
    """B5 回归: 玩家不在冰面 + 松键 -> slide_timer 衰减, 0.1s 后停止 (不吸附但不再移动)."""
    tilemap = _make_tilemap_with_ice([])  # 全部空
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)
    # 先按 UP 键
    p.keys["up"] = True
    p.key_press_time["up"] = 0.001
    p.update(0.05, tilemap, [], [])
    # 松开 UP
    p.keys["up"] = False
    # 跑 0.05s (slide_timer 应 0.1 - 0.05 = 0.05, 还在滑)
    p.update(0.05, tilemap, [], [])
    mid_y = p.rect.y
    # 再跑 0.2s (slide_timer < 0, 不再按 slide_dir 移动, 除非有键)
    p.update(0.2, tilemap, [], [])
    # 第二次 mid_y 后应不再按 slide_dir 移动, y 不变 (除非吸附)
    assert p.rect.y == mid_y, \
        f"after slide_timer expires, y should not change, mid_y={mid_y} now={p.rect.y}"


def test_player_ice_slide_does_not_snap_to_grid():
    """冰面 update_snap 应跳过吸附 (玩家位置不强制对齐到 TILE 边界)."""
    tilemap = _make_tilemap_with_ice([(8, 15)])
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)
    p.keys["up"] = True
    p.key_press_time["up"] = 0.001
    # 跑 1 帧让玩家启动
    p.update(0.05, tilemap, [], [])
    # 松开, 在冰面应继续滑不吸附
    p.keys["up"] = False
    p.update(0.05, tilemap, [], [])
    # 玩家 y 应是 MAP_Y + 15*TILE - 一些像素 (不在格点)
    expected_grid_y = MAP_Y + 15 * TILE
    # y 应小于 expected_grid_y (向上滑)
    assert p.rect.y < expected_grid_y, \
        f"on ice, y should not be snapped to grid, y={p.rect.y}"


def test_player_leaves_ice_stops_normally():
    """玩家从冰面走到非冰面后, 松键应正常停止."""
    tilemap = _make_tilemap_with_ice([(8, 15)])  # 只 (8,15) 是冰
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)  # 冰面
    p.keys["up"] = True
    p.key_press_time["up"] = 0.001
    p.update(0.05, tilemap, [], [])
    # 强制把玩家移到非冰面格子 (8, 14) - 但格子不能被砖块占
    # 我们手动改 rect 到 (8, 14) 跳过物理
    p.rect.x = MAP_X + 8 * TILE
    p.rect.y = MAP_Y + 14 * TILE
    # 此时 on_ice 应 False
    p.keys["up"] = False
    p.update(0.05, tilemap, [], [])
    assert p.on_ice is False, f"on non-ice tile, on_ice should be False"


# ---- 行为可玩性 ----

def test_ice_direction_can_still_be_changed():
    """B5: 冰面仍可转向 (玩家按 D 从 UP 改 RIGHT 应成功)."""
    tilemap = _make_tilemap_with_ice([(8, 15)])
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)
    p.keys["up"] = True
    p.key_press_time["up"] = 0.001
    p.update(0.05, tilemap, [], [])
    # 改方向为 RIGHT
    p.keys["right"] = True
    p.key_press_time["right"] = 0.01
    p.update(0.05, tilemap, [], [])
    # 方向应改变 (RIGHT 占上风因为 key_press_time 更大)
    assert p.dir == (1, 0), f"on ice, should still be able to change direction, dir={p.dir}"


# ---- Bug B5: 冰面 snap_axis 残留, 离开冰面后不吸附 ----

def test_player_snaps_to_grid_after_leaving_ice():
    """玩家从冰面滑到非冰面 + 松键 + 滑行结束 -> snap_axis 流程能正常进入.

    BUG 之前: on_ice 期间 update_snap 被跳过, snap_axis 残留非 None.
    滑出冰面后松键进入吸附分支, 'if self.snap_axis is None' 永远 False,
    玩家永远停在非格点, 后续变向困难.
    修后: on_ice 时清 snap_axis, 离开冰面后吸附分支能正常触发.
    """
    # (8, 15) 是冰面, (8, 14) 是空地. 玩家从 (8, 15) 向上滑, 出冰面后松键
    tilemap = _make_tilemap_with_ice([(8, 15)])
    p = PlayerTank(0, 0)
    _place_player_on_tile(p, 8, 15)
    p.keys["up"] = True
    p.key_press_time["up"] = 0.001
    # 滑足够长时间确保离开冰面
    for _ in range(30):
        p.update(0.05, tilemap, [], [])
    if p.on_ice:
        for _ in range(30):
            p.update(0.05, tilemap, [], [])
    assert p.on_ice is False, \
        f"expected to leave ice: y={p.rect.y} center y={p.rect.centery}"
    # 松开 UP
    p.keys["up"] = False
    # 跑足够长时间让 slide_timer 衰减到 0 并进入吸附分支
    for _ in range(30):
        p.update(0.05, tilemap, [], [])
    # 吸附分支: dir[0]==0 (UP 移动) 应对齐 x (与移动方向垂直的轴)
    # 之前 bug: snap_axis 残留, 永远不进吸附分支, x 一直非格点
    expected_x = round(p.rect.x / TILE) * TILE
    assert p.rect.x == expected_x, \
        f"after leaving ice + slide ends, x should snap to grid ({expected_x}), got {p.rect.x}"
