"""B3 生存模式（survival mode）测试。

- LEVELS / LEVEL_DIFFICULTY 含关 7 survival 配置
- Level.mode 字段正确识别
- _spawn_enemy 在 survival 模式无视 enemies_to_spawn
- 关 6 通关后 next_level 进关 7 survival 而非 VICTORY
- 关 7 (survival) 失败时 _record_highscore 写榜
- survival level 的 enemies_to_spawn = inf
"""
import pytest
import settings
from world.levels import LEVELS, get_level, get_level_difficulty, get_total_levels
from game.level import Level


# ---- 配置层 ----

def test_total_levels_is_7():
    assert get_total_levels() == 7


def test_level_7_is_survival_layout():
    layout = get_level(6)  # 0-based
    assert len(layout) == 17
    assert all(len(row) == 17 for row in layout)
    # 关 7 字符串里有 P (玩家出生)
    assert any("P" in row for row in layout)


def test_level_difficulty_7_is_survival():
    cfg = get_level_difficulty(6)
    assert cfg["mode"] == "survival"
    # survival 没有 enemy_count
    assert "enemy_count" not in cfg
    # 有 spawn_interval 和 max_on_screen
    assert cfg["spawn_interval"] > 0
    assert cfg["max_on_screen"] > 0


def test_levels_1_to_6_are_campaign():
    for i in range(6):
        cfg = get_level_difficulty(i)
        assert cfg.get("mode", "campaign") == "campaign"


# ---- Level 模式识别 ----

def test_level_campaign_default_mode():
    lv = Level(0, lives=3, score=0)
    assert lv.mode == "campaign"


def test_level_survival_mode():
    lv = Level(6, lives=3, score=0)
    assert lv.mode == "survival"


def test_level_survival_enemies_to_spawn_is_inf():
    lv = Level(6, lives=3, score=0)
    assert lv.enemies_to_spawn == float("inf")


def test_level_campaign_enemies_to_spawn_is_finite():
    lv = Level(0, lives=3, score=0)
    assert lv.enemies_to_spawn > 0
    assert lv.enemies_to_spawn != float("inf")


# ---- survival 不会自然完成 ----

def test_survival_level_never_completes_from_killing_all():
    """survival 模式杀光当前敌人后不会被标记 completed（无 enemies_to_spawn 上限）。"""
    lv = Level(6, lives=3, score=0)
    # 模拟一波敌人全部死亡
    lv.enemies = []
    lv.enemies_to_spawn = float("inf")
    # 关卡条件检查的代码（复刻 level.py:247 行的判定）
    completed = (lv.enemies_to_spawn <= 0 and len(lv.enemies) == 0 and not lv.failed)
    assert not completed, "survival should never complete from killing all"


def test_campaign_level_completes_after_killing_all():
    """campaign 模式敌人清空后会 completed。"""
    lv = Level(0, lives=3, score=0)
    lv.enemies = []
    lv.enemies_to_spawn = 0
    completed = (lv.enemies_to_spawn <= 0 and len(lv.enemies) == 0 and not lv.failed)
    assert completed


# ---- 集成测试：Game 流程 ----

def _make_game():
    """构造 Game 但不调 pygame.display.set_mode（用已有 display）。"""
    from game.game import Game
    g = Game()
    return g


def test_next_level_6_to_7_not_victory():
    """关 6 通关后 next_level 应该创建关 7 survival level，不直接 VICTORY。"""
    g = _make_game()
    g.level_index = 5  # 0-based, 在关 6 上
    g.lives = 3
    g.score = 1000
    g.next_level()
    assert g.level_index == 6
    assert g.state == "playing"
    assert g.level.mode == "survival"


def test_next_level_7_completes_to_victory(monkeypatch):
    """关 7 survival 后 next_level 触发 VICTORY。"""
    import os
    from utils import highscores
    tmp = "tests/.tmp_next_level_7_hs.json"
    if os.path.exists(tmp):
        os.remove(tmp)
    monkeypatch.setattr(highscores, "DEFAULT_PATH", tmp)
    try:
        g = _make_game()
        g.level_index = 6  # 0-based, 在关 7 survival 上
        g.lives = 3
        g.score = 5000
        g.next_level()
        assert g.level_index == 7
        assert g.state == "victory"
        # VICTORY 状态 self.level 被置 None（next_level 没创建新关）
        assert g.level is None
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def test_survival_failed_records_highscore(monkeypatch):
    """survival 失败时 _record_highscore 写榜。

    用 monkeypatch 改 highscores.DEFAULT_PATH 指向临时文件。
    """
    import os
    from utils import highscores
    tmp = "tests/.tmp_survival_failed_hs.json"
    if os.path.exists(tmp):
        os.remove(tmp)
    monkeypatch.setattr(highscores, "DEFAULT_PATH", tmp)
    try:
        g = _make_game()
        # 模拟 survival 模式失败
        g.level = Level(6, lives=0, score=12345)
        g.score = 12345
        g._record_highscore()
        # 写榜成功
        assert g.highscore_rank == 0
        # 显式传 path 读 tmp 文件，避免 load_highscores 默认读 data/highscores.json
        loaded = highscores.load_highscores(path=highscores.DEFAULT_PATH)
        assert len(loaded) == 1
        assert loaded[0]["score"] == 12345
        assert loaded[0]["level"] == 7  # 关 7 1-based
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def test_campaign_victory_records_highscore(monkeypatch):
    """6 关 campaign 通关 VICTORY 写榜，level=6。"""
    import os
    from utils import highscores
    tmp = "tests/.tmp_campaign_victory_hs.json"
    if os.path.exists(tmp):
        os.remove(tmp)
    monkeypatch.setattr(highscores, "DEFAULT_PATH", tmp)
    try:
        g = _make_game()
        g.level = Level(5, lives=3, score=9999)  # 关 6 (0-based 5)
        g.score = 9999
        g._record_highscore()
        assert g.highscore_rank == 0
        loaded = highscores.load_highscores(path=highscores.DEFAULT_PATH)
        assert loaded[0]["level"] == 6
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def test_survival_level_spawn_ignores_enemies_to_spawn():
    """_spawn_enemy 在 survival 模式无视 enemies_to_spawn 上限（不会因 inf 而跳过）。"""
    lv = Level(6, lives=3, score=0)
    lv.enemies_to_spawn = float("inf")
    lv._spawn_idx = 0
    # 不阻塞：应该成功 spawn
    result = lv._spawn_enemy()
    assert result is not None
    assert isinstance(result, type(lv.enemies[0]))
    # enemies_to_spawn 保持 inf（不递减）
    assert lv.enemies_to_spawn == float("inf")
    # survival_waves 累加
    assert lv.survival_waves == 1


def test_survival_spawn_blocked_when_all_spawn_points_taken():
    """所有出生点都被敌人占用时返回 None。"""
    lv = Level(6, lives=3, score=0)
    lv.enemies_to_spawn = float("inf")
    from entities.enemy import EnemyTank
    # 阻塞所有出生点
    for col, row in lv.tilemap.enemy_spawns:
        x, y = lv.tilemap.grid_to_world(col, row)
        lv.enemies.append(EnemyTank(x, y, tier=0, is_powerup_carrier=False))
    result = lv._spawn_enemy()
    assert result is None
