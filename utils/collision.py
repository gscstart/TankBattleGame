"""碰撞检测辅助。"""

def aabb(a, b) -> bool:
    """AABB 碰撞，两个对象需要 .x/.y/.w/.h 或 .rect。"""
    ar = a.rect if hasattr(a, "rect") else a
    br = b.rect if hasattr(b, "rect") else b
    return (
        ar.x < br.x + br.w
        and ar.x + ar.w > br.x
        and ar.y < br.y + br.h
        and ar.y + ar.h > br.y
    )


def snap_axis(value: int, grid: int, size: int) -> int:
    """将位置吸附到格点（坦克对齐到 48 像素边界）。"""
    return round(value / grid) * grid


def grid_of(px: int, py: int) -> tuple:
    """像素坐标 → 网格坐标 (col, row)。"""
    return (px // grid_size(px, py)[0], py // grid_size(px, py)[1])


def grid_size(px, py) -> tuple:
    from settings import TILE
    return (TILE, TILE)


def line_of_sight(start: tuple, end: tuple, tilemap) -> bool:
    """检查两点之间是否有"挡子弹"的瓦片。

    start, end: (x, y) 中心点像素坐标
    tilemap: TileMap 实例
    返回 True 表示中间无阻挡（视线通畅）。
    """
    from settings import TILE
    sx, sy = start
    ex, ey = end
    if sx == ex:
        # 垂直方向
        step = 1 if ey > sy else -1
        col, start_row = tilemap.world_to_grid(sx, sy)
        _, end_row = tilemap.world_to_grid(ex, ey)
        for row in range(start_row + step, end_row + step, step):
            tile = tilemap.get_tile(col, row)
            if tile is None:
                return False
            if getattr(tile, "blocks_bullet", False) and not getattr(tile, "destroyed", False):
                return False
        return True
    if sy == ey:
        # 水平方向
        step = 1 if ex > sx else -1
        start_col, row = tilemap.world_to_grid(sx, sy)
        end_col, _ = tilemap.world_to_grid(ex, ey)
        for col in range(start_col + step, end_col + step, step):
            tile = tilemap.get_tile(col, row)
            if tile is None:
                return False
            if getattr(tile, "blocks_bullet", False) and not getattr(tile, "destroyed", False):
                return False
        return True
    # 非直线：直接返回 False（只能用于同一直线检测）
    return False
