"""成就系统 (C5 - F10).

设计原则 (按 karpathy Simplicity):
- 成就定义 8 个, 全部基于现有事件 (ENTITY_KILLED/POWERUP_PICKED/LEVEL_COMPLETED)
- 不改 Tank/PlayerTank 基类 (避免 adjacent code 改动)
- 持久化 JSON (data/achievements.json), 跟 highscores 同样模式
- 解锁 publish ACHIEVEMENT_UNLOCKED 事件, UI 监听显示

8 个成就 (按难易度):
  一次性 (跨会话持久化):
    1. first_blood       - 首次击杀敌人
    2. boss_slayer       - 击杀 BOSS
    3. powerup_collector - 累计拾取 10 个道具 (跨关)
    4. collector         - 拾取 5 种不同道具 (跨关)
    5. legend            - 通关关 15 (终极 BOSS)
  关卡级 (本关重置):
    6. sharpshooter      - 连续 5 发子弹命中敌人 (被打断就重置)
    7. pacifist          - 一关不击毁任何敌人通关
    8. survivor          - 生存模式撑过 60 秒

未实现 (因需要"玩家受伤"事件, 改基类 adjacent code 风险):
    - untouchable (一关无伤通关)
    - iron_wall (5 秒不受击)
"""
import json
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

from utils import events


# ---- 配置 ----
DEFAULT_PATH = "data/achievements.json"


# ---- 成就定义 ----
@dataclass(frozen=True)
class Achievement:
    id: str
    name_key: str          # i18n key
    desc_key: str
    icon_color: tuple      # (r, g, b)


ACHIEVEMENTS = [
    Achievement("first_blood",       "ach.first_blood.name",       "ach.first_blood.desc",       (200, 60, 60)),
    Achievement("boss_slayer",       "ach.boss_slayer.name",       "ach.boss_slayer.desc",       (180, 80, 200)),
    Achievement("powerup_collector", "ach.powerup_collector.name", "ach.powerup_collector.desc", (220, 200, 60)),
    Achievement("collector",         "ach.collector.name",         "ach.collector.desc",         (100, 200, 100)),
    Achievement("legend",            "ach.legend.name",            "ach.legend.desc",            (255, 200, 100)),
    Achievement("sharpshooter",      "ach.sharpshooter.name",      "ach.sharpshooter.desc",      (200, 200, 200)),
    Achievement("pacifist",          "ach.pacifist.name",          "ach.pacifist.desc",          (180, 180, 100)),
    Achievement("survivor",          "ach.survivor.name",          "ach.survivor.desc",          (100, 220, 180)),
]


def get_achievement(aid: str) -> Optional[Achievement]:
    """通过 id 查 Achievement 定义."""
    for a in ACHIEVEMENTS:
        if a.id == aid:
            return a
    return None


# ---- 持久化 ----
def _read_raw(path: str) -> dict:
    """读取成就 JSON, 缺失/损坏返回空结构."""
    if not os.path.exists(path):
        return {"unlocked": [], "unlock_times": {}, "powerup_total": 0, "powerup_types": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"unlocked": [], "unlock_times": {}, "powerup_total": 0, "powerup_types": []}
    if not isinstance(data, dict):
        return {"unlocked": [], "unlock_times": {}, "powerup_total": 0, "powerup_types": []}
    return {
        "unlocked": data.get("unlocked", []) if isinstance(data.get("unlocked"), list) else [],
        "unlock_times": data.get("unlock_times", {}) if isinstance(data.get("unlock_times"), dict) else {},
        "powerup_total": int(data.get("powerup_total", 0)),
        "powerup_types": data.get("powerup_types", []) if isinstance(data.get("powerup_types"), list) else [],
    }


def _atomic_write(path: str, data: dict):
    """原子写 JSON: 临时文件 + rename."""
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ach_", suffix=".tmp", dir=directory or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        if os.path.exists(path):
            os.remove(path)
        os.rename(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# ---- 关卡级运行时 ----
class LevelState:
    """每关新建, 关卡结束丢弃."""
    def __init__(self, mode: str = "campaign"):
        self.consecutive_hits = 0           # sharpshooter 计数
        self.enemies_killed_in_level = 0    # pacifist 计数
        self.survival_elapsed = 0.0         # survivor 计时


# ---- Manager ----
class Manager:
    """成就管理器 - 跨关持久化 + 本关运行时.

    用法:
        m = Manager()                          # 启动时加载
        m.on_level_start(level)                # 关卡开始
        m.on_level_tick(dt, mode)              # 每帧
        m.process_event("entity.killed", ...)  # 关卡 update 末尾分发
        m.save()                               # 关卡结束或退出
    """

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        data = _read_raw(path)
        valid_ids = {a.id for a in ACHIEVEMENTS}
        self.unlocked: set[str] = {a for a in data["unlocked"] if a in valid_ids}
        self.unlock_times: dict[str, float] = {
            k: float(v) for k, v in data["unlock_times"].items() if k in valid_ids
        }
        # 跨关累计
        self.powerup_total: int = int(data["powerup_total"])
        self.powerup_types: set[str] = set(data["powerup_types"])
        # 本关状态
        self.state = LevelState()
        # 本会话刚解锁的 (UI 提示)
        self.recent_unlocks: list[str] = []
        # 订阅 events (C5: 简化 - manager 全局订阅, level 不用 dispatch)
        self._unsubs = [
            events.subscribe(events.ENTITY_KILLED,
                             lambda **kw: self._on_entity_killed(**kw)),
            events.subscribe(events.POWERUP_PICKED,
                             lambda **kw: self._on_powerup_picked(**kw)),
            events.subscribe(events.LEVEL_COMPLETED,
                             lambda **kw: self._on_level_completed(**kw)),
        ]

    def save(self):
        """保存到 JSON. 失败抛 IOError."""
        _atomic_write(self.path, {
            "unlocked": sorted(self.unlocked),
            "unlock_times": {k: self.unlock_times[k] for k in sorted(self.unlock_times)},
            "powerup_total": self.powerup_total,
            "powerup_types": sorted(self.powerup_types),
        })

    def on_level_start(self, mode: str):
        """关卡开始时重置 LevelState."""
        self.state = LevelState(mode=mode)

    def on_level_tick(self, dt: float, mode: str):
        """关卡每帧调用 - survival 计时."""
        if mode == "survival":
            self.state.survival_elapsed += dt
            if self.state.survival_elapsed >= 60.0:
                self._unlock("survivor")

    def process_event(self, event_name: str, **kwargs):
        if event_name == events.ENTITY_KILLED:
            self._on_entity_killed(**kwargs)
        elif event_name == events.POWERUP_PICKED:
            self._on_powerup_picked(**kwargs)
        elif event_name == events.LEVEL_COMPLETED:
            self._on_level_completed(**kwargs)

    def _unlock(self, aid: str) -> bool:
        """解锁一个成就 (idempotent). True 表示本次新解锁."""
        if aid in self.unlocked:
            return False
        if get_achievement(aid) is None:
            return False
        self.unlocked.add(aid)
        self.unlock_times[aid] = time.time()
        self.recent_unlocks.append(aid)
        events.publish(events.ACHIEVEMENT_UNLOCKED, id=aid)
        return True

    def _on_entity_killed(self, kind: str, owner: str, **kwargs):
        if kind != "enemy":
            return
        if owner == "powerup":
            # 自爆/grenade 不算玩家命中 (避免 pacifist 误判)
            return
        # 1. 首次击杀
        self._unlock("first_blood")
        # 6. sharpshooter: 连续命中
        self.state.consecutive_hits += 1
        if self.state.consecutive_hits >= 5:
            self._unlock("sharpshooter")
        # 2. boss_slayer
        if kwargs.get("is_boss"):
            self._unlock("boss_slayer")
        # 7. pacifist 计数
        self.state.enemies_killed_in_level += 1

    def _on_powerup_picked(self, type: str, **kwargs):
        # 3. powerup_collector
        self.powerup_total += 1
        if self.powerup_total >= 10:
            self._unlock("powerup_collector")
        # 4. collector
        self.powerup_types.add(type)
        if len(self.powerup_types) >= 5:
            self._unlock("collector")

    def _on_level_completed(self, level_index: int, **kwargs):
        # 7. pacifist
        if self.state.enemies_killed_in_level == 0:
            self._unlock("pacifist")
        # 5. legend
        if level_index == 14:  # 0-based 关 15
            self._unlock("legend")

    # ---- 查询 ----
    def is_unlocked(self, aid: str) -> bool:
        return aid in self.unlocked

    def unlocked_count(self) -> int:
        return len(self.unlocked)

    def total_count(self) -> int:
        return len(ACHIEVEMENTS)

    def clear_recent(self):
        """清空 recent_unlocks (UI 展示完调用)."""
        self.recent_unlocks = []

    def close(self):
        """取消订阅 (测试清理 / Game 退出时调用)."""
        for u in self._unsubs:
            u()
        self._unsubs = []


def reset_for_test(path: str = DEFAULT_PATH):
    """测试用: 删除成就文件."""
    if os.path.exists(path):
        os.remove(path)
