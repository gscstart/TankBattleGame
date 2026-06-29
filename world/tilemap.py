"""瓦片地图。网格尺寸由 settings.GRID_W / GRID_H 决定（当前 17×17）。"""
from __future__ import annotations
import pygame
from settings import TILE, GRID_W, GRID_H, MAP_X, MAP_Y
from world.tile import (TileEmpty, TileBrick, TileSteel, TileGrass,
                        TileWater, TileIce, TileBase)


# 字符 → 瓦片映射
CHAR_TO_TILE = {
    ".": TileEmpty,
    "B": TileBrick,
    "S": TileSteel,
    "G": TileGrass,
    "W": TileWater,
    "I": TileIce,
    # 特殊位置（E 敌方出生 / P 玩家出生 / X 基地）在 levels 中处理
}


class TileMap:
    """网格地图（GRID_W × GRID_H）。"""

    def __init__(self, level_layout, player_spawn, base_pos, enemy_spawns):
        """
        level_layout: list[list[Tile]]，GRID_W × GRID_H
        player_spawn: (col, row)
        base_pos: (col, row)
        enemy_spawns: list[(col, row)]
        """
        self.tiles = level_layout
        self.player_spawn = player_spawn
        self.base_pos = base_pos
        self.base_tile = None  # 在 build() 中指向对应 TileBase
        self.enemy_spawns = enemy_spawns
        # 默认出生点为地图标记位置；player_spawn/enemy_spawns 已被替换为空地
        self._find_base()

    @classmethod
    def from_layout(cls, layout: list[str], char_map=None):
        """从字符串网格构建地图。char_map 字符→瓦片类或函数。"""
        if char_map is None:
            char_map = CHAR_TO_TILE
        grid = [[None] * GRID_W for _ in range(GRID_H)]
        # 默认值随网格尺寸变化（居中底部），见 settings.GRID_W/GRID_H
        mid = GRID_W // 2
        player_spawn = (mid, GRID_H - 2)
        base_pos = (mid, GRID_H - 1)
        explicit_enemy_spawns = []  # 收集关卡中显式标 E 的位置
        for row, line in enumerate(layout):
            for col, ch in enumerate(line):
                if ch in char_map:
                    grid[row][col] = char_map[ch]()
                elif ch == "P":
                    player_spawn = (col, row)
                    grid[row][col] = TileEmpty()
                elif ch == "E":
                    explicit_enemy_spawns.append((col, row))
                    grid[row][col] = TileEmpty()
                elif ch == "X":
                    base_pos = (col, row)
                    grid[row][col] = TileBase()
                else:
                    grid[row][col] = TileEmpty()
        # 关卡没有标 E 时使用默认 3 个顶部出生点（左/中/右）
        if not explicit_enemy_spawns:
            explicit_enemy_spawns = [(0, 0), (mid, 0), (GRID_W - 1, 0)]
        return cls(grid, player_spawn, base_pos, explicit_enemy_spawns[:3])

    def _find_base(self):
        for row in range(GRID_H):
            for col in range(GRID_W):
                if isinstance(self.tiles[row][col], TileBase):
                    self.base_tile = self.tiles[row][col]
                    self.base_pos = (col, row)
                    return

    def get_tile(self, col, row):
        if 0 <= col < GRID_W and 0 <= row < GRID_H:
            return self.tiles[row][col]
        return None

    def pixel_to_grid(self, px, py):
        return (px // TILE, py // TILE)

    def grid_to_pixel(self, col, row):
        return (MAP_X + col * TILE, MAP_Y + row * TILE)

    def world_to_grid(self, wx, wy):
        """世界坐标（地图左上角 = (0,0)）→ 网格坐标。"""
        return ((wx - MAP_X) // TILE, (wy - MAP_Y) // TILE)

    def grid_to_world(self, col, row):
        return (MAP_X + col * TILE, MAP_Y + row * TILE)

    # ---- 碰撞查询 ----
    def rect_collides_solid(self, rect: pygame.Rect) -> bool:
        """矩形与地图的'实体'碰撞（砖、钢、基地、水、地图外）。"""
        # 检查矩形覆盖的所有格子
        left, top = self.world_to_grid(rect.left, rect.top)
        right, bottom = self.world_to_grid(rect.right - 1, rect.bottom - 1)
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                tile = self.get_tile(c, r)
                if tile is None:
                    return True  # 地图外
                if isinstance(tile, TileBase):
                    if not tile.destroyed:
                        return True
                elif hasattr(tile, "blocks_tank_now") and tile.blocks_tank_now():
                    return True
                elif getattr(tile, "blocks_tank", False):
                    return True
        return False

    def rect_hits_brick_subcell(self, rect: pygame.Rect):
        """返回矩形覆盖的砖块子格列表 [(tile, col, row, sub_index), ...]。

        枚举 rect 实际覆盖的所有子格（AABB 范围），而非只看 rect.left/top
        单点所在的子格。否则半碎砖块场景下，子弹 rect 跨越死/活子格边界时
        会漏掉"对面"的活子格，导致子弹穿透不命中（玩家从已死子格位置
        开火打不到对侧活子格，无法清理剩余砖块）。
        """
        hits = []
        left, top = self.world_to_grid(rect.left, rect.top)
        right, bottom = self.world_to_grid(rect.right - 1, rect.bottom - 1)
        sub_size = TILE // 2
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                tile = self.get_tile(c, r)
                if not (isinstance(tile, TileBrick) and tile.alive):
                    continue
                # rect 相对砖块 (col, row) 左上角的局部像素
                lx = rect.x - (MAP_X + c * TILE)
                ly = rect.y - (MAP_Y + r * TILE)
                # rect 覆盖的子格列范围 [c_start, c_end] (0=左, 1=右)
                c_start = 0 if lx < sub_size else 1
                c_end = 0 if lx + rect.width - 1 < sub_size else 1
                r_start = 0 if ly < sub_size else 1
                r_end = 0 if ly + rect.height - 1 < sub_size else 1
                for sub_r in range(r_start, r_end + 1):
                    for sub_c in range(c_start, c_end + 1):
                        sub_index = sub_r * 2 + sub_c
                        if tile.subtl & (1 << sub_index):
                            hits.append((tile, c, r, sub_index))
        return hits

    def rect_hits_steel_or_base(self, rect: pygame.Rect):
        """返回矩形覆盖的钢墙/基地 [(tile, col, row), ...]。"""
        hits = []
        left, top = self.world_to_grid(rect.left, rect.top)
        right, bottom = self.world_to_grid(rect.right - 1, rect.bottom - 1)
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                tile = self.get_tile(c, r)
                if isinstance(tile, TileSteel):
                    hits.append((tile, c, r))
                elif isinstance(tile, TileBase) and not tile.destroyed:
                    hits.append((tile, c, r))
        return hits

    # ---- 渲染 ----
    def draw(self, surface: pygame.Surface):
        # 底色
        bg_rect = pygame.Rect(MAP_X, MAP_Y, GRID_W * TILE, GRID_H * TILE)
        pygame.draw.rect(surface, (0, 0, 0), bg_rect)
        # 瓦片
        for r in range(GRID_H):
            for c in range(GRID_W):
                tile = self.tiles[r][c]
                if tile.__class__.__name__ == "TileEmpty":
                    continue
                rect = pygame.Rect(MAP_X + c * TILE, MAP_Y + r * TILE, TILE, TILE)
                # 通过 utils.draw 渲染
                from utils.draw import draw_tile
                draw_tile(surface, tile, rect)

    def draw_foreground(self, surface: pygame.Surface):
        """在坦克之后再画的层（草丛）。"""
        for r in range(GRID_H):
            for c in range(GRID_W):
                tile = self.tiles[r][c]
                if isinstance(tile, TileGrass):
                    rect = pygame.Rect(MAP_X + c * TILE, MAP_Y + r * TILE, TILE, TILE)
                    from utils.draw import draw_tile
                    draw_tile(surface, tile, rect)
