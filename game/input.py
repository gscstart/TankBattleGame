"""输入抽象层 - 玩家 → 键位映射.

为同屏双人合作 (F1) 铺路: 多个 PlayerTank 各自绑定一个 InputMap,
handle_event 先用 is_mine(key) 过滤, 自己的键才处理.

1 玩家时行为不变: P1_INPUT 包含 WASD + 方向键 alias (旧版 PlayerTank
硬编码 K_w/K_UP 双绑定, A1 决策保留 1 玩家兼容).
双打时 P1 用 P1_INPUT, P2 用 P2_INPUT, 各自独立响应.
"""
import pygame


class InputMap:
    """玩家 ID → 5 个动作的键位集. 每个动作可绑多个键 (alias).

    1 个键盘物理上只能同时被一个玩家按, 所以同一键即使在 P1/P2 都
    alias 也不会同时被两个玩家接收 (但本设计避免这种冲突: P1 和 P2
    的 input_map 用不同键).
    """
    __slots__ = ("player_id", "up_keys", "down_keys", "left_keys", "right_keys", "fire_keys")

    def __init__(self, player_id, *, up_keys=(), down_keys=(),
                 left_keys=(), right_keys=(), fire_keys=()):
        self.player_id = player_id
        self.up_keys = tuple(up_keys)
        self.down_keys = tuple(down_keys)
        self.left_keys = tuple(left_keys)
        self.right_keys = tuple(right_keys)
        self.fire_keys = tuple(fire_keys)

    def is_mine(self, key) -> bool:
        """该 key 是否属于本玩家. handle_event 用此过滤事件."""
        return (key in self.up_keys or key in self.down_keys
                or key in self.left_keys or key in self.right_keys
                or key in self.fire_keys)

    def direction_for(self, key):
        """把 pygame key 翻译为方向. 不属于本玩家返回 None.

        用于 KEYDOWN 时把键归类为 up/down/left/right (PlayerTank
        内部需要按方向名索引 keys dict).
        """
        if key in self.up_keys: return "up"
        if key in self.down_keys: return "down"
        if key in self.left_keys: return "left"
        if key in self.right_keys: return "right"
        return None

    def is_fire(self, key) -> bool:
        return key in self.fire_keys


# P1 默认: WASD + Space/J (1 玩家行为)
# 故意不 alias 方向键: A4 核心目标是 P1/P2 独立控制, 如果 P1 也响应
# 方向键, 双打时按方向键 P1 和 P2 同时响应, 违背独立原则.
# 1 玩家时只能 WASD 操作 (代价: 方向键不能用, 但物理上一个键同一时刻
# 只被一个玩家按, 不影响单玩家手感; 双打时 W/A/S/D 和方向键/Enter 不冲突).
P1_INPUT = InputMap(
    player_id=0,
    up_keys=(pygame.K_w,),
    down_keys=(pygame.K_s,),
    left_keys=(pygame.K_a,),
    right_keys=(pygame.K_d,),
    fire_keys=(pygame.K_SPACE, pygame.K_j),
)

# P2: 方向键 + Enter / RShift (右手玩家)
P2_INPUT = InputMap(
    player_id=1,
    up_keys=(pygame.K_UP,),
    down_keys=(pygame.K_DOWN,),
    left_keys=(pygame.K_LEFT,),
    right_keys=(pygame.K_RIGHT,),
    fire_keys=(pygame.K_RETURN, pygame.K_RSHIFT),
)
