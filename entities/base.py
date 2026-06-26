"""基地/老鹰。包装在世界地图的 TileBase 中。"""
# 基地本质是 TileBase，已在世界地图中。这里只导出常量。
from world.tile import TileBase

# 重新导出便于 entities 包内引用
__all__ = ["TileBase"]
