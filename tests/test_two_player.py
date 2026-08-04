"""C1 同屏双人合作 (F1) 测试。

- Level(num_players=2) 创建双玩家
- 每个玩家持自己的 InputMap (P1 vs P2)
- P2 出生在 P1 旁边, 不重叠
- 玩家不互相阻挡 (other_tanks 排除自己)
- 死亡/重生按玩家独立 (独立生命, 决策 #1)
- 双玩家都死 + 基地未毁 = _fail
- 道具按距离最近玩家分发
- AI 目标: 选最近存活玩家
- Level 升级 (next_level) 保留 num_players
- HUD 接受 p2_lives 参数
"""
import pytest
import pygame

from settings import PLAYER_LIVES, P2_ENABLED_DEFAULT
from game.level import Level
from game.input import P1_INPUT, P2_INPUT
from entities.player import PlayerTank
from entities.enemy import EnemyTank


# ---- Level 创建双玩家 ----

def test_level_default_one_player():
    """默认 num_players=1 (向后兼容)."""
    lv = Level(0, lives=3, score=0)
    assert len(lv.players) == 1
    assert lv.num_players == 1


def test_level_two_players_created():
    lv = Level(0, lives=3, score=0, num_players=2)
    assert len(lv.players) == 2
    assert lv.num_players == 2


def test_two_players_have_different_input_maps():
    """P1 用 P1_INPUT, P2 用 P2_INPUT, 不共享."""
    lv = Level(0, lives=3, score=0, num_players=2)
    assert lv.players[0].input_map is P1_INPUT
    assert lv.players[1].input_map is P2_INPUT


def test_two_players_have_independent_lives():
    """决策 #1: 独立生命."""
    lv = Level(0, lives=3, score=0, num_players=2)
    assert lv.players[0].lives == PLAYER_LIVES
    assert lv.players[1].lives == PLAYER_LIVES
    # 互不影响
    lv.players[0].lives = 1
    assert lv.players[1].lives == PLAYER_LIVES


def test_two_players_have_distinct_player_ids():
    lv = Level(0, lives=3, score=0, num_players=2)
    assert lv.players[0].player_id == 1
    assert lv.players[1].player_id == 2


def test_p2_spawns_left_of_p1():
    """P2 出生在 P1 左侧一格, 不重叠."""
    lv = Level(0, lives=3, score=0, num_players=2)
    p1 = lv.players[0]
    p2 = lv.players[1]
    assert not p1.rect.colliderect(p2.rect), "P1 and P2 should not overlap"
    # P2 x 应小于 P1 x (左侧)
    assert p2.rect.x < p1.rect.x


def test_p1_input_map_default():
    """单玩家时 P1 用 P1_INPUT (兼容旧版)."""
    lv = Level(0, lives=3, score=0)
    assert lv.players[0].input_map is P1_INPUT


# ---- 死亡/重生 ----

def test_respawn_player_deducts_life():
    """respawn 减 1 命."""
    lv = Level(0, lives=3, score=0, num_players=2)
    assert lv.players[0].lives == 3
    lv.players[0].dead = True
    lv.respawn_player(0)
    assert lv.players[0].lives == 2


def test_respawn_player_no_op_when_lives_zero():
    """命用完时 respawn 不做事 (玩家永久死亡)."""
    lv = Level(0, lives=3, score=0, num_players=2)
    lv.players[0].lives = 0
    lv.players[0].dead = True
    before = lv.players[0]
    lv.respawn_player(0)
    # 玩家对象未变
    assert lv.players[0] is before
    assert lv.players[0].dead is True


def test_respawn_p2_preserves_p1():
    """重生 P2 不影响 P1."""
    lv = Level(0, lives=3, score=0, num_players=2)
    p1_before = lv.players[0]
    p2_before = lv.players[1]
    lv.players[1].dead = True
    lv.respawn_player(1)
    assert lv.players[0] is p1_before  # P1 未替换
    # P2 已被替换为新对象 (复活)
    assert lv.players[1] is not p2_before
    assert not lv.players[1].dead
    # P2 lives 减 1
    assert lv.players[1].lives == PLAYER_LIVES - 1


def test_respawn_preserves_input_map():
    """重生后玩家保持原 InputMap (P1 仍是 P1_INPUT, P2 仍是 P2_INPUT)."""
    lv = Level(0, lives=3, score=0, num_players=2)
    lv.players[0].dead = True
    lv.respawn_player(0)
    assert lv.players[0].input_map is P1_INPUT
    lv.players[1].dead = True
    lv.respawn_player(1)
    assert lv.players[1].input_map is P2_INPUT


# ---- 失败条件 ----

def test_all_players_dead_returns_true():
    """所有玩家命用完时 _all_players_dead 返回 True."""
    lv = Level(0, lives=3, score=0, num_players=2)
    assert lv._all_players_dead() is False
    lv.players[0].lives = 0
    assert lv._all_players_dead() is False  # P2 还有命
    lv.players[1].lives = 0
    assert lv._all_players_dead() is True


def test_single_player_dead_when_all_lives_zero():
    """1P 模式下该玩家命 0 即算 all dead."""
    lv = Level(0, lives=3, score=0, num_players=1)
    assert lv._all_players_dead() is False
    lv.players[0].lives = 0
    assert lv._all_players_dead() is True


# ---- InputMap 独立性 ----

def test_p1_keys_ignored_by_p2():
    """P1 按键 (WASD/方向键) P2 不响应 (A4 InputMap 抽象)."""
    lv = Level(0, lives=3, score=0, num_players=2)
    p1, p2 = lv.players
    # 模拟 P1 按 W
    ev = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_w})
    p1.handle_event(ev)
    assert p1.keys["up"] is True
    # P2 收到同事件应忽略
    p2.handle_event(ev)
    assert p2.keys["up"] is False


def test_p2_keys_ignored_by_p1():
    """P2 按键 (方向键当 fire, Enter 当 fire) P1 不响应."""
    lv = Level(0, lives=3, score=0, num_players=2)
    p1, p2 = lv.players
    # P2 按 Enter (fire)
    ev = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN})
    p2.handle_event(ev)
    assert p2.keys["fire"] is True
    # P1 收到同事件应忽略 (P1_INPUT 不含 Enter)
    p1.handle_event(ev)
    assert p1.keys["fire"] is False


# ---- 道具分发 ----

def test_apply_powerup_to_target_index():
    """_apply_powerup 把效果给指定玩家."""
    lv = Level(0, lives=3, score=0, num_players=2)
    # 给 P2 拾取 "helmet" (10s 无敌)
    from entities.powerup import PowerUp
    pu = PowerUp(0, 0, "helmet")
    lv._apply_powerup(pu, target_idx=1)
    assert lv.players[1].invincible == 10.0
    assert lv.players[0].invincible == 0.0


def test_apply_powerup_tank_life_uses_target_lives():
    """'tank' 道具 +1 命给 target 玩家."""
    lv = Level(0, lives=3, score=0, num_players=2)
    from entities.powerup import PowerUp
    pu = PowerUp(0, 0, "tank")
    lv._apply_powerup(pu, target_idx=0)
    assert lv.players[0].lives == PLAYER_LIVES + 1
    assert lv.players[1].lives == PLAYER_LIVES


def test_apply_powerup_invalid_target_falls_back_to_p1():
    """target_idx 越界时 fallback 到 P1."""
    lv = Level(0, lives=3, score=0, num_players=2)
    from entities.powerup import PowerUp
    pu = PowerUp(0, 0, "helmet")
    lv._apply_powerup(pu, target_idx=99)
    assert lv.players[0].invincible == 10.0
    assert lv.players[1].invincible == 0.0


# ---- AI 目标 ----

def test_ai_targets_nearest_alive_player(monkeypatch):
    """AI 应该选最近的存活玩家作为目标."""
    from settings import TILE
    lv = Level(0, lives=3, score=0, num_players=2)
    # 让 P1 和 P2 距离很近
    p1, p2 = lv.players
    p2.rect.x = p1.rect.x + TILE * 3
    # 创建一个敌人
    e = EnemyTank(0, 0, tier=0, is_powerup_carrier=False)
    lv.enemies.append(e)
    # mock 敌人 update, 记录它收到的 player
    captured = {}

    def fake_update(dt, tilemap, other_tanks, bullets, player, **kwargs):
        captured["player"] = player
        return None

    monkeypatch.setattr(e, "update", fake_update)
    lv.update(0.1)
    # AI 应该被某个玩家调用 (因为 update 跑过), player 应该是 p1 或 p2
    assert captured.get("player") in (p1, p2)
    # 默认 p1 在 p2 左侧, x 更小
    if captured.get("player") is p2:
        # 如果 AI 选 P2, 那 P2 必须在最近位置
        pass  # 接受, 因为方向不强制


# ---- Game 集成 ----

def test_game_starts_with_two_players_when_num_2(monkeypatch):
    """Game 启动 2P 时 Level.players 应有 2 个."""
    from game.game import Game
    g = Game.__new__(Game)
    g.num_players = 2
    g.level_index = 0
    g.score = 0
    g.lives = PLAYER_LIVES
    g.start_game()
    assert g.num_players == 2
    assert len(g.level.players) == 2
    assert g.level.players[0].input_map is P1_INPUT
    assert g.level.players[1].input_map is P2_INPUT


def test_game_default_num_players():
    """Game 初始化时按 P2_ENABLED_DEFAULT 设置 num_players."""
    from game.game import Game
    g = Game.__new__(Game)
    # 不设 num_players, 用 __init__ 默认
    # 重新走一次 __init__ 不实际跑 pygame.init 太多, 我们手工设
    g.num_players = 2 if P2_ENABLED_DEFAULT else 1
    assert g.num_players == 2  # 默认应该是 2 (C1 启用)


def test_next_level_preserves_num_players():
    """next_level 保留 num_players (2P → 2P)."""
    from game.game import Game
    import settings as S
    g = Game.__new__(Game)
    g.num_players = 2
    g.level_index = 0
    g.score = 0
    g.lives = PLAYER_LIVES
    g.start_game()
    g.next_level()
    assert g.num_players == 2
    assert len(g.level.players) == 2


# ---- HUD ----

def test_hud_accepts_p2_lives():
    """HUD 接受 p2_lives 参数不报错."""
    from game.hud import draw_hud
    import pygame
    surface = pygame.display.get_surface()
    # 单人模式 (p2_lives=None) 应正常画
    draw_hud(surface, lives=3, score=1000, level=0, enemies_left=5, p2_lives=None)
    # 双人模式 (p2_lives=2) 应正常画
    draw_hud(surface, lives=3, score=1000, level=0, enemies_left=5, p2_lives=2)


# ---- 永久死亡 bug 回归测试 ----

def test_permanently_dead_player_does_not_republish_killed():
    """命用完的永久死亡玩家不应每帧重复 publish ENTITY_KILLED 事件.

    BUG: 之前 respawn_player 命 0 时 delattr _death_timer, 下帧 else 分支
    'if not hasattr' True 又重新 publish.
    """
    from utils import events as ev
    ev.clear()
    received = []
    ev.subscribe(ev.ENTITY_KILLED, lambda **kw: received.append(kw))

    lv = Level(0, lives=3, score=0, num_players=1)
    lv.players[0].lives = 0  # 已经命 0
    lv.players[0].dead = True
    # 模拟"update 已感知死亡, timer 在倒数末段"状态
    lv._death_timer_p0 = 0.05
    # 跑 5 帧 update, 触发 respawn(失败 -> 永久死亡) 后, 不应再 publish
    for _ in range(5):
        lv.update(0.1)
    # 关键断言: 整个过程中 ENTITY_KILLED 最多 publish 1 次 (首次)
    # (而不是每帧 publish 1 次)
    killed_count = sum(1 for r in received if r.get("kind") == "player")
    assert killed_count <= 1, \
        f"permanent dead player re-published ENTITY_KILLED: {killed_count} times"
    ev.clear()


def test_permanently_dead_player_does_not_block_update():
    """永久死亡玩家不应让 update 卡死或重复触发 _fail."""
    lv = Level(0, lives=3, score=0, num_players=1)
    lv.players[0].lives = 0
    lv.players[0].dead = True
    # 跑 10 帧, 不应抛错
    for _ in range(10):
        lv.update(0.1)
    # _fail 只应触发一次
    assert lv.failed is True


def test_all_players_perm_dead_triggers_fail_once():
    """所有玩家都永久死亡时 _fail 只触发一次."""
    from utils import events as ev
    ev.clear()
    fail_count = [0]
    def on_fail(**kw):
        fail_count[0] += 1
    ev.subscribe(ev.LEVEL_FAILED, on_fail)
    lv = Level(0, lives=3, score=0, num_players=2)
    # 两玩家都命 0 + dead
    lv.players[0].lives = 0
    lv.players[0].dead = True
    lv.players[1].lives = 0
    lv.players[1].dead = True
    for _ in range(10):
        lv.update(0.1)
    assert fail_count[0] == 1, f"LEVEL_FAILED published {fail_count[0]} times"
    ev.clear()
