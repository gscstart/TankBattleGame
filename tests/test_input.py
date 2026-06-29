"""InputMap + PlayerTank 输入过滤单测 (pytest 风格, A4).

零 pygame.display 依赖, 但仍需 pygame.init() (InputMap 用 pygame.K_*).
"""
import pygame
pygame.init()

from game.input import InputMap, P1_INPUT, P2_INPUT
from entities.player import PlayerTank
from settings import Dir


def test_inputmap_construction():
    """InputMap 接受 player_id + 5 动作键位元组."""
    im = InputMap(
        player_id=0,
        up_keys=(pygame.K_w,),
        down_keys=(pygame.K_s,),
        left_keys=(pygame.K_a,),
        right_keys=(pygame.K_d,),
        fire_keys=(pygame.K_SPACE,),
    )
    assert im.player_id == 0
    assert im.up_keys == (pygame.K_w,)
    # 不可变元组
    assert isinstance(im.up_keys, tuple)


def test_inputmap_is_mine():
    """is_mine 判断 key 是否在 5 个键位集内."""
    im = InputMap(player_id=0,
                  up_keys=(pygame.K_w, pygame.K_UP),
                  down_keys=(pygame.K_s,),
                  left_keys=(pygame.K_a,),
                  right_keys=(pygame.K_d,),
                  fire_keys=(pygame.K_SPACE,))
    assert im.is_mine(pygame.K_w)
    assert im.is_mine(pygame.K_UP)  # alias
    assert im.is_mine(pygame.K_s)
    assert im.is_mine(pygame.K_a)
    assert im.is_mine(pygame.K_d)
    assert im.is_mine(pygame.K_SPACE)
    # 不属于本玩家
    assert not im.is_mine(pygame.K_x)
    assert not im.is_mine(pygame.K_RETURN)
    assert not im.is_mine(pygame.K_ESCAPE)


def test_inputmap_direction_for():
    """direction_for 把 key 翻译为方向名 (up/down/left/right) 或 None."""
    im = InputMap(player_id=0,
                  up_keys=(pygame.K_w, pygame.K_UP),
                  down_keys=(pygame.K_s,),
                  left_keys=(pygame.K_a,),
                  right_keys=(pygame.K_d,),
                  fire_keys=(pygame.K_SPACE,))
    assert im.direction_for(pygame.K_w) == "up"
    assert im.direction_for(pygame.K_UP) == "up"
    assert im.direction_for(pygame.K_s) == "down"
    assert im.direction_for(pygame.K_a) == "left"
    assert im.direction_for(pygame.K_d) == "right"
    # fire 不是方向
    assert im.direction_for(pygame.K_SPACE) is None
    # 不属于本玩家
    assert im.direction_for(pygame.K_x) is None


def test_inputmap_is_fire():
    im = InputMap(player_id=0, fire_keys=(pygame.K_SPACE, pygame.K_j))
    assert im.is_fire(pygame.K_SPACE)
    assert im.is_fire(pygame.K_j)
    assert not im.is_fire(pygame.K_w)


def test_p1_input_default():
    """P1_INPUT 默认: WASD + 方向键 alias + Space/J (1 玩家兼容)."""
    assert P1_INPUT.player_id == 0
    # WASD
    assert P1_INPUT.is_mine(pygame.K_w)
    assert P1_INPUT.is_mine(pygame.K_a)
    assert P1_INPUT.is_mine(pygame.K_s)
    assert P1_INPUT.is_mine(pygame.K_d)
    # 方向键 alias (1 玩家兼容)
    assert P1_INPUT.is_mine(pygame.K_UP)
    assert P1_INPUT.is_mine(pygame.K_DOWN)
    assert P1_INPUT.is_mine(pygame.K_LEFT)
    assert P1_INPUT.is_mine(pygame.K_RIGHT)
    # fire
    assert P1_INPUT.is_mine(pygame.K_SPACE)
    assert P1_INPUT.is_mine(pygame.K_j)
    # P2 的键 P1 不响应
    assert not P1_INPUT.is_mine(pygame.K_RETURN)
    assert not P1_INPUT.is_mine(pygame.K_RSHIFT)


def test_p2_input():
    """P2_INPUT: 方向键 + Enter/RShift, 不响应 WASD."""
    assert P2_INPUT.player_id == 1
    # 方向键
    assert P2_INPUT.is_mine(pygame.K_UP)
    assert P2_INPUT.is_mine(pygame.K_DOWN)
    assert P2_INPUT.is_mine(pygame.K_LEFT)
    assert P2_INPUT.is_mine(pygame.K_RIGHT)
    # fire
    assert P2_INPUT.is_mine(pygame.K_RETURN)
    assert P2_INPUT.is_mine(pygame.K_RSHIFT)
    # P1 专属键 P2 不响应
    assert not P2_INPUT.is_mine(pygame.K_w)
    assert not P2_INPUT.is_mine(pygame.K_a)
    assert not P2_INPUT.is_mine(pygame.K_s)
    assert not P2_INPUT.is_mine(pygame.K_d)
    assert not P2_INPUT.is_mine(pygame.K_SPACE)
    assert not P2_INPUT.is_mine(pygame.K_j)


def test_player_default_uses_p1():
    """不传 input_map 时, PlayerTank 默认 P1_INPUT (兼容旧调用)."""
    p = PlayerTank(100, 100)
    assert p.input_map is P1_INPUT
    # 模拟按 K_w → keys["up"] = True
    p.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_w, "mod": 0, "unicode": "", "scancode": 0}))
    assert p.keys["up"] is True
    # 按 K_UP (方向键 alias) 也能响应
    p.handle_event(pygame.event.Event(pygame.KEYUP, {"key": pygame.K_UP, "mod": 0, "unicode": "", "scancode": 0}))
    assert p.keys["up"] is False


def test_player_p2_ignores_p1_keys():
    """P2 玩家 (P2_INPUT) 按 P1 的 K_w 不会响应."""
    from game.input import P2_INPUT
    p = PlayerTank(100, 100, input_map=P2_INPUT)
    # P2 按 K_w → 不是 P2 的键, 忽略
    p.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_w, "mod": 0, "unicode": "", "scancode": 0}))
    assert p.keys["up"] is False
    # P2 按 K_UP → P2 的键
    p.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP, "mod": 0, "unicode": "", "scancode": 0}))
    assert p.keys["up"] is True


def test_p1_and_p2_independent():
    """核心: P1 和 P2 同时按不同键, 各自响应 (Game.handle_events 遍历分发场景)."""
    from game.input import P1_INPUT, P2_INPUT
    p1 = PlayerTank(100, 100, input_map=P1_INPUT)
    p2 = PlayerTank(400, 100, input_map=P2_INPUT)
    # 模拟 Game.handle_events: 把同一 KEYDOWN 分发给两个 player
    # P1 按 K_w, P2 按 K_UP (同一时刻同一方向)
    ev_w = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_w, "mod": 0, "unicode": "", "scancode": 0})
    ev_up = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP, "mod": 0, "unicode": "", "scancode": 0})
    p1.handle_event(ev_w)
    p1.handle_event(ev_up)
    p2.handle_event(ev_w)   # P2 收到 P1 的 K_w, 忽略
    p2.handle_event(ev_up)   # P2 收到自己的 K_UP
    # P1 收到 W 和 UP, 都接受
    assert p1.keys["up"] is True
    # P2 只收到 UP, K_w 被忽略
    assert p2.keys["up"] is True  # K_UP 触发
    # 验证 P2 没把 K_w 当成 fire 或其他 (key 状态对比)
    # P2 keys["fire"] 必须是 False
    assert p2.keys["fire"] is False


def test_player_direction_priority_with_inputmap():
    """方向优先级 (A1 决策) 在 input_map 抽象下仍工作: 按 P1 的 K_d 后按 K_w, 最近按的 (W) 胜出."""
    p = PlayerTank(100, 100)  # 默认 P1_INPUT
    # 按 K_d
    p.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_d, "mod": 0, "unicode": "", "scancode": 0}))
    p._time = 0.5
    # 按 K_w
    p.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_w, "mod": 0, "unicode": "", "scancode": 0}))
    active = p._active_direction()
    assert active == Dir.UP, f"most recent (W) wins, got {active}"
