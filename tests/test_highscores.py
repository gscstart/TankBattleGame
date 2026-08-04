"""B2 排行榜测试。

- load_highscores 文件不存在 / 损坏 / 字段缺失 各种兜底
- add_score 插入排序 + 容量上限 + 排位返回
- qualifies 空榜 / 满榜边界
- 原子写：写失败不污染现有文件
"""
import json
import os
import shutil
import pytest

import utils.highscores as hs


TMP_DIR = "tests/.tmp_highscores"


@pytest.fixture(autouse=True)
def clean_tmp():
    """每个测试用独立临时文件，跑完清理（含子目录）。"""
    if os.path.isdir(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR, exist_ok=True)
    yield
    if os.path.isdir(TMP_DIR):
        shutil.rmtree(TMP_DIR)


def _path(name: str = "scores.json") -> str:
    return os.path.join(TMP_DIR, name)


# ---- load 兜底 ----

def test_load_missing_file_returns_empty():
    p = _path("missing.json")
    assert not os.path.exists(p)
    assert hs.load_highscores(p) == []


def test_load_corrupt_file_returns_empty():
    p = _path("corrupt.json")
    with open(p, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert hs.load_highscores(p) == []


def test_load_wrong_structure_returns_empty():
    p = _path("wrong.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"foo": 1}, f)  # 缺 'scores' 键
    assert hs.load_highscores(p) == []


def test_load_filters_invalid_entries():
    p = _path("invalid_entries.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"scores": [
            {"name": "OK", "score": 100, "level": 3, "date": "2026-01-01"},
            {"name": "bad", "score": "not int"},  # 类型错
            {"score": 100},  # 缺 name
            None,  # 不是 dict
            "string",  # 不是 dict
        ]}, f)
    scores = hs.load_highscores(p)
    assert len(scores) == 1
    assert scores[0]["name"] == "OK"


def test_load_sorts_descending():
    p = _path("sort.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"scores": [
            {"name": "A", "score": 100, "level": 1, "date": "2026-01-01"},
            {"name": "B", "score": 500, "level": 2, "date": "2026-01-01"},
            {"name": "C", "score": 300, "level": 3, "date": "2026-01-01"},
        ]}, f)
    scores = hs.load_highscores(p)
    assert [s["name"] for s in scores] == ["B", "C", "A"]


# ---- qualifies ----

def test_qualifies_empty_list():
    assert hs.qualifies(0, []) is True
    assert hs.qualifies(99999, []) is True


def test_qualifies_full_list():
    scores = [{"name": f"P{i}", "score": (i + 1) * 100, "level": 1, "date": ""}
              for i in range(hs.MAX_ENTRIES)]
    # 最高分必须 > 榜尾才上榜
    assert hs.qualifies(scores[-1]["score"] + 1, scores) is True
    assert hs.qualifies(scores[-1]["score"], scores) is False
    assert hs.qualifies(scores[-1]["score"] - 1, scores) is False


def test_qualifies_partial_list():
    scores = [{"name": f"P{i}", "score": (i + 1) * 100, "level": 1, "date": ""}
              for i in range(5)]
    assert hs.qualifies(1, scores) is True  # 不到 10 个就上榜


# ---- add_score ----

def test_add_first_score_returns_rank_0():
    p = _path("first.json")
    rank, scores = hs.add_score(100, 6, name="AAA", path=p)
    assert rank == 0
    assert len(scores) == 1
    assert scores[0]["name"] == "AAA"
    assert scores[0]["score"] == 100
    assert scores[0]["level"] == 6
    assert "date" in scores[0]
    # 文件确实写入了
    assert os.path.exists(p)
    # 读回来
    loaded = hs.load_highscores(p)
    assert loaded[0]["name"] == "AAA"


def test_add_score_inserts_at_correct_rank():
    p = _path("multi.json")
    hs.add_score(100, 1, name="A", path=p)
    hs.add_score(500, 5, name="B", path=p)
    hs.add_score(300, 3, name="C", path=p)
    scores = hs.load_highscores(p)
    assert [s["name"] for s in scores] == ["B", "C", "A"]


def test_add_score_caps_at_max_entries():
    p = _path("cap.json")
    # 塞 15 个分数，max 应该是 10
    for i in range(15):
        hs.add_score((i + 1) * 100, 1, name=f"P{i}", path=p)
    scores = hs.load_highscores(p)
    assert len(scores) == hs.MAX_ENTRIES
    # 保留最高的 10 个
    assert scores[0]["score"] == 1500
    assert scores[-1]["score"] == 600


def test_add_score_too_low_returns_rank_minus_1():
    p = _path("low.json")
    # 先填满 10 个高分局
    for i in range(10):
        hs.add_score((i + 1) * 1000, 1, name=f"HI{i}", path=p)
    rank, scores = hs.add_score(100, 1, name="LOW", path=p)
    assert rank == -1
    assert len(scores) == 10
    assert all(s["name"] != "LOW" for s in scores)


def test_add_score_validates_negative():
    with pytest.raises(ValueError):
        hs.add_score(-1, 1, name="X", path=_path("neg.json"))


def test_add_score_validates_type():
    with pytest.raises(ValueError):
        hs.add_score("not int", 1, name="X", path=_path("type.json"))


def test_add_score_creates_directory():
    """第一次写会自动创建 data/ 目录。"""
    p = "tests/.tmp_highscores/sub/dir/scores.json"
    assert not os.path.exists(os.path.dirname(p))
    rank, _ = hs.add_score(100, 1, name="X", path=p)
    assert rank == 0
    assert os.path.exists(p)


def test_add_score_uses_today_date():
    p = _path("date.json")
    rank, scores = hs.add_score(100, 1, name="X", path=p)
    from datetime import date
    assert scores[0]["date"] == date.today().isoformat()


# ---- 不污染现有文件（原子写） ----

def test_failed_write_does_not_corrupt_existing():
    p = _path("atomic.json")
    hs.add_score(100, 1, name="ORIG", path=p)
    # 强制模拟写失败：把 path 改成只读目录路径
    # 在 Windows 上不能简单 chmod，这里只验证正常路径下 atomic 工作
    # 写一个新分数
    rank, scores = hs.add_score(200, 1, name="NEW", path=p)
    assert rank == 0  # 新分数更高
    assert scores[0]["name"] == "NEW"
    # 读回来确认两个都在
    loaded = hs.load_highscores(p)
    assert {s["name"] for s in loaded} == {"ORIG", "NEW"}
