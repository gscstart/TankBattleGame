"""排行榜：JSON 持久化 top N 分数。

设计：
- data/highscores.json 存列表，按 score 降序，最多 MAX_ENTRIES 条
- 损坏/缺失文件兜底为空列表，不抛异常
- add_score 原子：插入并写回，文件失败抛 IOError
- 无玩家输入名字 UI，B2 简化用 'YOU' 占位（F10 成就做名字时再扩展）
"""
import json
import os
import tempfile
from datetime import date

# ---- 配置 ----
DEFAULT_PATH = "data/highscores.json"
MAX_ENTRIES = 10  # 排行榜容量


def _today() -> str:
    return date.today().isoformat()


def _read_raw(path: str) -> dict:
    """读取原始 JSON，文件不存在/损坏返回空结构。"""
    if not os.path.exists(path):
        return {"scores": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"scores": []}
    if not isinstance(data, dict) or "scores" not in data:
        return {"scores": []}
    if not isinstance(data["scores"], list):
        return {"scores": []}
    return data


def load_highscores(path: str = DEFAULT_PATH) -> list:
    """读排行榜。返回按 score 降序的列表，每项含 name/score/level/date。"""
    data = _read_raw(path)
    scores = data["scores"]
    # 过滤掉非法项（dict 缺字段 / 类型不对）
    valid = []
    for s in scores:
        if (isinstance(s, dict)
                and isinstance(s.get("name"), str)
                and isinstance(s.get("score"), int)
                and isinstance(s.get("level"), int)):
            valid.append(s)
    valid.sort(key=lambda x: x["score"], reverse=True)
    return valid[:MAX_ENTRIES]


def qualifies(score: int, scores: list) -> bool:
    """判断分数是否进 top N（空榜或低于榜尾都算）。"""
    if len(scores) < MAX_ENTRIES:
        return True
    return score > scores[-1]["score"]


def _insert_sorted(scores: list, entry: dict) -> list:
    """按 score 降序插入 entry，返回新列表（不修改原列表）。"""
    new_list = list(scores) + [entry]
    new_list.sort(key=lambda x: x["score"], reverse=True)
    return new_list[:MAX_ENTRIES]


def _atomic_write(path: str, data: dict):
    """原子写 JSON：先写临时文件再 rename，避免半写。"""
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    # 写到同目录临时文件，再 rename
    fd, tmp = tempfile.mkstemp(prefix=".hs_", suffix=".tmp", dir=directory or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Windows 下 rename 可能跨盘失败；先 remove 再 rename 兜底
        if os.path.exists(path):
            os.remove(path)
        os.rename(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def add_score(score: int, level: int, name: str = "YOU",
              path: str = DEFAULT_PATH) -> tuple:
    """尝试把分数加入排行榜。

    返回 (rank, scores): rank 是 0-based 排位，未上榜时 rank=-1；scores 是更新后的列表。
    """
    if not isinstance(score, int) or score < 0:
        raise ValueError("score must be a non-negative int")
    scores = load_highscores(path)
    if not qualifies(score, scores):
        return (-1, scores)
    entry = {"name": name, "score": score, "level": level, "date": _today()}
    new_scores = _insert_sorted(scores, entry)
    _atomic_write(path, {"scores": new_scores})
    # 找 rank
    for i, s in enumerate(new_scores):
        if s is entry or (s == entry):
            return (i, new_scores)
    return (0, new_scores)  # fallback


def reset_for_test(path: str = DEFAULT_PATH):
    """测试用：删除排行榜文件。"""
    if os.path.exists(path):
        os.remove(path)
