"""瓦片类型定义。

每种瓦片有 4 个关键属性：
- blocks_tank: 是否阻挡坦克
- blocks_bullet: 是否阻挡子弹
- destructible: 是否可被子弹破坏
- damageable: 子弹进入此瓦片时是否消失（与 blocks_bullet 略有不同：草丛是 blocks_bullet=False）
"""
from __future__ import annotations


class Tile:
    """瓦片基类。"""
    blocks_tank: bool = False
    blocks_bullet: bool = False
    destructible: bool = False
    bullet_consumed: bool = True  # 子弹命中后是否被消耗（草丛不消耗）

    def on_bullet_hit(self, bullet, sub_index: int = 0) -> bool:
        """子弹命中。返回 True 表示子弹应被销毁。
        sub_index: 0=左上 1=右上 2=左下 3=右下（仅砖块使用）。
        """
        return self.bullet_consumed


class TileEmpty(Tile):
    """空地。"""
    pass


class TileBrick(Tile):
    """砖块。4 个子格可独立破坏。"""
    blocks_tank = True
    blocks_bullet = True
    destructible = True
    bullet_consumed = True

    def __init__(self):
        self.subtl = 0b1111  # 4 个子格全在

    @property
    def alive(self) -> bool:
        return self.subtl != 0

    def on_bullet_hit(self, bullet, sub_index: int = 0) -> bool:
        # 强力子弹（如果有）可以打掉钢铁，这里普通子弹
        self.subtl &= ~(1 << sub_index)
        return True

    def blocks_tank_now(self) -> bool:
        """砖块只要还有子格存在，就阻挡坦克。"""
        return self.alive


class TileSteel(Tile):
    """钢墙。普通子弹打不穿。"""
    blocks_tank = True
    blocks_bullet = True
    destructible = False
    bullet_consumed = True

    def on_bullet_hit(self, bullet, sub_index: int = 0) -> bool:
        # 普通子弹撞墙消失但不破坏
        return True


class TileGrass(Tile):
    """草丛。坦克可以穿过，子弹可以穿过（不消耗、不阻挡）。"""
    blocks_tank = False
    blocks_bullet = False
    destructible = False
    bullet_consumed = False


class TileWater(Tile):
    """水域。阻挡坦克但不阻挡子弹。"""
    blocks_tank = True
    blocks_bullet = False
    destructible = False
    bullet_consumed = False


class TileIce(Tile):
    """冰面。坦克打滑（未来扩展），现在仅是装饰。"""
    blocks_tank = False
    blocks_bullet = False
    destructible = False
    bullet_consumed = False


class TileBase(Tile):
    """基地/老鹰。被击中游戏失败。"""
    blocks_tank = True
    blocks_bullet = True
    destructible = True
    bullet_consumed = True

    def __init__(self):
        self.destroyed = False

    def on_bullet_hit(self, bullet, sub_index: int = 0) -> bool:
        self.destroyed = True
        return True
