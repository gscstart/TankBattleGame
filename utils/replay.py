"""回放/录像 (C6 - F13).

设计原则 (按 karpathy Simplicity):
- 只录键盘输入 (5 个动作的 bool 状态), 不录视频/状态/随机种子
- 重放时玩家操作跟原版一致, 但敌人行为可能因 random 有偏差
- JSON 持久化, 1 关 1 文件
- 主菜单 R 键进入回放列表

数据格式 (data/replays/<name>.json):
{
  "name": str,
  "date": str (ISO),
  "level_index": int,        # 0-based 关卡号
  "num_players": int,        # 1/2
  "frames": [
    {"up": bool, "down": bool, "left": bool, "right": bool, "fire": bool},
    ...
  ],
  "total_frames": int,
  "final_score": int,
  "result": "completed" | "failed"
}

限制 (按 karpathy 不修相邻代码):
- Level 创建时 random 序列不录 -> 重放时敌人位置/行为有偏差
- 只录"按下/松开"产生的 keys 状态, 不录鼠标 / ESC / 暂停
"""
import json
import os
import tempfile
from datetime import date, datetime
from typing import Optional


# ---- 配置 ----
DEFAULT_DIR = "data/replays"
# 5 个动作的 keys 状态 (顺序固定, 方便压缩)
KEY_NAMES = ("up", "down", "left", "right", "fire")


# ---- 单关录制 ----
class Recorder:
    """单关录制器. 在 Level 创建时 start, 每帧 record_frame, 关卡结束 save.

    用法:
        rec = Recorder(level_index=0, num_players=1)
        rec.start()
        for frame in range(...):
            ...
            rec.record_frame(player.keys)
        rec.stop(final_score=500, result="completed")
        rec.save("replay1")
    """

    def __init__(self, level_index: int, num_players: int = 1):
        self.level_index = level_index
        self.num_players = num_players
        self.frames: list[dict] = []
        self._recording = False
        self._start_time: Optional[str] = None
        self._final_score = 0
        self._result = "completed"

    def start(self):
        """开始录制. 重复 start 不影响 (幂等)."""
        if not self._recording:
            self._recording = True
            self._start_time = datetime.now().isoformat()
            self.frames = []

    def stop(self, final_score: int = 0, result: str = "completed"):
        """停止录制. 写最终 score + result."""
        self._recording = False
        self._final_score = final_score
        self._result = result

    def is_recording(self) -> bool:
        return self._recording

    def record_frame(self, keys: dict):
        """记录一帧的按键状态. keys = {"up": bool, "down": bool, "left": bool, "right": bool, "fire": bool}."""
        if not self._recording:
            return
        # 只保留 5 个动作 (过滤其他字段)
        self.frames.append({k: bool(keys.get(k, False)) for k in KEY_NAMES})

    def to_dict(self) -> dict:
        """序列化为 dict (供 save 用)."""
        return {
            "name": "",  # 由 save() 填
            "date": self._start_time or "",
            "level_index": self.level_index,
            "num_players": self.num_players,
            "frames": self.frames,
            "total_frames": len(self.frames),
            "final_score": self._final_score,
            "result": self._result,
        }

    def save(self, name: str, directory: str = DEFAULT_DIR) -> str:
        """保存到 <directory>/<name>.json. 返回文件路径."""
        if not name:
            raise ValueError("name must be non-empty")
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"{name}.json")
        data = self.to_dict()
        data["name"] = name
        # 原子写
        fd, tmp = tempfile.mkstemp(prefix=".replay_", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            if os.path.exists(path):
                os.remove(path)
            os.rename(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        return path


# ---- 重放 ----
class Player:
    """从 JSON 文件加载回放, 提供 get_keys_at(frame_idx) 接口.

    用法:
        p = Player()
        p.load("data/replays/replay1.json")
        for frame in range(p.total_frames):
            keys = p.get_keys_at(frame)
            player.keys = keys  # 覆盖
            ...
    """

    def __init__(self):
        self.frames: list[dict] = []
        self.total_frames: int = 0
        self.level_index: int = 0
        self.num_players: int = 1
        self.name: str = ""
        self.date: str = ""
        self.final_score: int = 0
        self.result: str = "completed"
        self._path: str = ""

    def load(self, path: str) -> bool:
        """从 JSON 加载. 成功 True, 失败 False (不抛错)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return False
        if not isinstance(data, dict) or "frames" not in data:
            return False
        frames = data["frames"]
        if not isinstance(frames, list):
            return False
        # 过滤无效 frames (非 dict / 缺字段)
        valid = []
        for f in frames:
            if not isinstance(f, dict):
                continue
            valid.append({k: bool(f.get(k, False)) for k in KEY_NAMES})
        self.frames = valid
        self.total_frames = len(valid)
        self.level_index = int(data.get("level_index", 0))
        self.num_players = int(data.get("num_players", 1))
        self.name = str(data.get("name", ""))
        self.date = str(data.get("date", ""))
        self.final_score = int(data.get("final_score", 0))
        self.result = str(data.get("result", "completed"))
        self._path = path
        return True

    def get_keys_at(self, frame_idx: int) -> dict:
        """返回第 frame_idx 帧的 keys. 越界返回全 False."""
        if 0 <= frame_idx < len(self.frames):
            return dict(self.frames[frame_idx])
        return {k: False for k in KEY_NAMES}


# ---- 文件列表 ----
def list_replays(directory: str = DEFAULT_DIR) -> list:
    """列出目录下所有回放 (按文件修改时间倒序).

    返回 [{name, path, mtime, level_index, final_score, result, total_frames}, ...]
    """
    if not os.path.isdir(directory):
        return []
    out = []
    for fname in os.listdir(directory):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(directory, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        out.append({
            "name": data.get("name", fname[:-5]),
            "path": path,
            "mtime": os.path.getmtime(path),
            "level_index": int(data.get("level_index", 0)),
            "final_score": int(data.get("final_score", 0)),
            "result": str(data.get("result", "completed")),
            "total_frames": int(data.get("total_frames", 0)),
        })
    out.sort(key=lambda r: r["mtime"], reverse=True)
    return out


def delete_replay(path: str):
    """删除一个回放文件. 不存在不抛错."""
    if os.path.exists(path):
        os.remove(path)


def reset_for_test(directory: str = DEFAULT_DIR):
    """测试用: 删除整个回放目录."""
    import shutil
    if os.path.isdir(directory):
        shutil.rmtree(directory, ignore_errors=True)
