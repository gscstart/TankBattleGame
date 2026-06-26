"""瓦片地图。13x13 网格。"""
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
    """13x13 网格地图。"""

    def __init__(self, level_layout, player_spawn, base_pos, enemy_spawns):
        """
        level_layout: list[list[Tile]]，13x13
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
        player_spawn = (6, 12)
        base_pos = (6, 12)
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
        # 关卡没有标 E 时使用默认 3 个顶部出生点
        if not explicit_enemy_spawns:
            explicit_enemy_spawns = [(0, 0), (6, 0), (12, 0)]
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
        """返回矩形覆盖的砖块子格列表 [(tile, col, row, sub_index), ...]。"""
        hits = []
        left, top = self.world_to_grid(rect.left, rect.top)
        right, bottom = self.world_to_grid(rect.right - 1, rect.bottom - 1)
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                tile = self.get_tile(c, r)
                if isinstance(tile, TileBrick) and tile.alive:
                    # 计算子格索引
                    local_x = rect.x - (MAP_X + c * TILE)
                    local_y = rect.y - (MAP_Y + r * TILE)
                    # 子格大小 24
                    sub_size = TILE // 2
                    sub_c = 0 if local_x < sub_size else 1
                    sub_r = 0 if local_y < sub_size else 1
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
