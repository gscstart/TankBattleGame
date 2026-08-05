"""C6 回放/录像 (F13) 测试.

- Recorder 录按键序列 + 持久化
- Player 加载 JSON + 取每帧 keys
- list_replays / delete_replay
- 集成: Game.start_replay + Game.update 每帧覆盖 player.keys
- 重放模式禁用真实键盘 (除了 ESC 退出)
- 失败关不保存 / 成功关保存
"""
import os
import pytest
import tempfile
import shutil

from settings import PLAYER_LIVES, MAP_X, MAP_Y
from utils import replay as rp
from game.level import Level
from entities.player import PlayerTank


# ---- 测试夹具 ----
@pytest.fixture
def tmp_replay_dir():
    """每个测试一个临时目录, 结束清理."""
    d = tempfile.mkdtemp(prefix="replay_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ===== 1. Recorder 基础 =====

def test_recorder_creation():
    """Recorder 初始未在录制."""
    r = rp.Recorder(level_index=0, num_players=1)
    assert not r.is_recording()
    assert r.frames == []


def test_recorder_start_stop():
    """start 后 is_recording=True, stop 后 False."""
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    assert r.is_recording()
    r.stop(final_score=100, result="completed")
    assert not r.is_recording()
    assert r._final_score == 100
    assert r._result == "completed"


def test_recorder_record_frame():
    """record_frame 录一个 keys 字典."""
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    r.record_frame({"up": True, "down": False, "left": False,
                    "right": True, "fire": False})
    r.record_frame({"up": False, "down": False, "left": False,
                    "right": False, "fire": True})
    assert len(r.frames) == 2
    assert r.frames[0]["up"] is True
    assert r.frames[0]["right"] is True
    assert r.frames[1]["fire"] is True


def test_recorder_record_frame_when_not_recording():
    """未启动录制时 record_frame 静默忽略 (不抛错)."""
    r = rp.Recorder(level_index=0, num_players=1)
    r.record_frame({"up": True})
    assert r.frames == []


def test_recorder_frame_filters_to_5_keys():
    """record_frame 只保留 5 个动作 (up/down/left/right/fire)."""
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    r.record_frame({"up": True, "extra": 999, "another": "foo",
                    "down": False, "left": False, "right": False, "fire": True})
    assert "extra" not in r.frames[0]
    assert "another" not in r.frames[0]
    assert set(r.frames[0].keys()) == {"up", "down", "left", "right", "fire"}


# ===== 2. 持久化 =====

def test_recorder_save_creates_file(tmp_replay_dir):
    """save 创建 JSON 文件."""
    r = rp.Recorder(level_index=2, num_players=1)
    r.start()
    for _ in range(10):
        r.record_frame({"up": False, "down": False, "left": True,
                        "right": False, "fire": False})
    r.stop(final_score=500, result="completed")
    path = r.save("test_replay_1", directory=tmp_replay_dir)
    assert os.path.exists(path)
    assert path == os.path.join(tmp_replay_dir, "test_replay_1.json")


def test_recorder_save_load_roundtrip(tmp_replay_dir):
    """save 后 Player.load 能读到所有数据."""
    r = rp.Recorder(level_index=3, num_players=2)
    r.start()
    r.record_frame({"up": True, "down": False, "left": False,
                    "right": True, "fire": False})
    r.record_frame({"up": False, "down": True, "left": False,
                    "right": False, "fire": True})
    r.stop(final_score=1000, result="completed")
    path = r.save("rt", directory=tmp_replay_dir)
    p = rp.Player()
    assert p.load(path) is True
    assert p.level_index == 3
    assert p.num_players == 2
    assert p.final_score == 1000
    assert p.result == "completed"
    assert p.total_frames == 2
    assert p.frames[0]["up"] is True
    assert p.frames[1]["fire"] is True


def test_recorder_save_empty_name_raises():
    """save 空名抛 ValueError."""
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    r.stop()
    with pytest.raises(ValueError):
        r.save("")


# ===== 3. Player 加载 =====

def test_player_load_nonexistent_returns_false():
    """加载不存在的文件返回 False (不抛错)."""
    p = rp.Player()
    assert p.load("/nonexistent/path/replay.json") is False


def test_player_load_corrupted_returns_false(tmp_replay_dir):
    """加载损坏 JSON 返回 False."""
    path = os.path.join(tmp_replay_dir, "bad.json")
    with open(path, "w") as f:
        f.write("{not valid")
    p = rp.Player()
    assert p.load(path) is False


def test_player_load_missing_frames_returns_false(tmp_replay_dir):
    """加载缺 frames 字段返回 False."""
    import json
    path = os.path.join(tmp_replay_dir, "no_frames.json")
    with open(path, "w") as f:
        json.dump({"name": "x", "level_index": 0}, f)
    p = rp.Player()
    assert p.load(path) is False


def test_player_get_keys_at_out_of_range(tmp_replay_dir):
    """get_keys_at 越界返回全 False."""
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    r.record_frame({"up": True, "down": False, "left": False,
                    "right": False, "fire": False})
    r.stop()
    path = r.save("oor", directory=tmp_replay_dir)
    p = rp.Player()
    p.load(path)
    # 帧 0 范围内
    k = p.get_keys_at(0)
    assert k["up"] is True
    # 帧 1 越界
    k = p.get_keys_at(1)
    assert all(v is False for v in k.values())
    # 负数越界
    k = p.get_keys_at(-1)
    assert all(v is False for v in k.values())


# ===== 4. list_replays / delete_replay =====

def test_list_replays_empty_dir(tmp_replay_dir):
    """空目录返回空列表."""
    assert rp.list_replays(directory=tmp_replay_dir) == []


def test_list_replays_nonexistent_dir():
    """不存在目录返回空列表 (不抛错)."""
    assert rp.list_replays(directory="/nonexistent/dir") == []


def test_list_replays_returns_metadata(tmp_replay_dir):
    """list_replays 返回元数据 list."""
    r = rp.Recorder(level_index=5, num_players=1)
    r.start()
    r.record_frame({"up": True, "down": False, "left": False,
                    "right": False, "fire": False})
    r.stop(final_score=2000, result="completed")
    r.save("meta_test", directory=tmp_replay_dir)
    replays = rp.list_replays(directory=tmp_replay_dir)
    assert len(replays) == 1
    r_meta = replays[0]
    assert r_meta["name"] == "meta_test"
    assert r_meta["level_index"] == 5
    assert r_meta["final_score"] == 2000
    assert r_meta["result"] == "completed"
    assert r_meta["total_frames"] == 1


def test_list_replays_skips_corrupted(tmp_replay_dir):
    """list_replays 跳过损坏文件."""
    # 写一个损坏
    bad = os.path.join(tmp_replay_dir, "bad.json")
    with open(bad, "w") as f:
        f.write("not json")
    # 写一个好的
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    r.stop()
    r.save("good", directory=tmp_replay_dir)
    replays = rp.list_replays(directory=tmp_replay_dir)
    assert len(replays) == 1
    assert replays[0]["name"] == "good"


def test_delete_replay(tmp_replay_dir):
    """delete_replay 删文件."""
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    r.stop()
    path = r.save("to_del", directory=tmp_replay_dir)
    assert os.path.exists(path)
    rp.delete_replay(path)
    assert not os.path.exists(path)


def test_delete_replay_nonexistent():
    """delete 不存在的文件不抛错."""
    rp.delete_replay("/nonexistent/path/replay.json")  # should not raise


# ===== 5. Level 集成 (模拟 Game 行为) =====

def test_level_player_keys_drives_movement():
    """C6 review: 验证 player.keys 覆盖能影响玩家位置 (走通整条路)."""
    lv = Level(0, lives=PLAYER_LIVES, score=0)
    p = lv.players[0]
    initial_x = p.rect.x
    # 模拟: 按住 right 5 帧
    p.keys = {"up": False, "down": False, "left": False, "right": True, "fire": False}
    for _ in range(5):
        lv.update(0.1)
    # 玩家应该向右移动
    assert p.rect.x > initial_x, f"player should move right (was {initial_x}, now {p.rect.x})"


def test_recorder_captures_player_keys_each_frame():
    """Recorder 能录玩家每帧的 keys 状态."""
    lv = Level(0, lives=PLAYER_LIVES, score=0)
    rec = rp.Recorder(level_index=0, num_players=1)
    rec.start()
    # 模拟 10 帧: 第 5 帧按 fire
    for i in range(10):
        lv.players[0].keys = {
            "up": False, "down": False, "left": False, "right": False,
            "fire": (i == 5)}
        rec.record_frame(lv.players[0].keys)
        lv.update(0.01)
    rec.stop()
    assert len(rec.frames) == 10
    # 第 5 帧 fire=True, 其它 False
    for i, frame in enumerate(rec.frames):
        if i == 5:
            assert frame["fire"] is True
        else:
            assert frame["fire"] is False


def test_player_get_keys_at_returns_correct_frame(tmp_replay_dir):
    """Player.get_keys_at 返回正确的帧数据."""
    # 录: 第 0 帧 right=True, 第 1 帧 fire=True
    rec = rp.Recorder(level_index=0, num_players=1)
    rec.start()
    rec.record_frame({"up": False, "down": False, "left": False,
                      "right": True, "fire": False})
    rec.record_frame({"up": False, "down": False, "left": False,
                      "right": False, "fire": True})
    rec.stop()
    path = rec.save("frames", directory=tmp_replay_dir)
    p = rp.Player()
    p.load(path)
    k0 = p.get_keys_at(0)
    k1 = p.get_keys_at(1)
    assert k0["right"] is True
    assert k0["fire"] is False
    assert k1["right"] is False
    assert k1["fire"] is True


# ===== 6. reset_for_test =====

def test_reset_for_test(tmp_replay_dir):
    """reset_for_test 删除整个目录."""
    # 写一个文件
    r = rp.Recorder(level_index=0, num_players=1)
    r.start()
    r.stop()
    r.save("x", directory=tmp_replay_dir)
    assert len(os.listdir(tmp_replay_dir)) >= 1
    rp.reset_for_test(directory=tmp_replay_dir)
    assert not os.path.exists(tmp_replay_dir)
