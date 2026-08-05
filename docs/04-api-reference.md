# 04 · API 参考

> 所有公开的类、函数、常量速查。文件路径以 `TankBattleGame/` 为根。

---

## 1. `settings.py` — 全局常量

### 1.1 屏幕与地图

| 常量 | 值 | 含义 |
|------|----|------|
| `SCREEN_W` | 832 | 屏幕宽 |
| `SCREEN_H` | 684 | 屏幕高（HUD 60 + 地图 624） |
| `HUD_H` | 60 | 顶部 HUD 区高 |
| `MAP_X` | 104 | 地图左上角 X（水平居中） |
| `MAP_Y` | 60 | 地图左上角 Y（HUD 下方） |
| `TILE` | 36 | 单瓦片边长（**A 阶段是 48，C3 改为 36**） |
| `GRID_W` / `GRID_H` | 17 | 网格行列数 |
| `MAP_PIXEL_W` / `MAP_PIXEL_H` | 612 | 地图像素 |
| `FPS` | 60 | 帧率上限 |

### 1.2 坦克 / 子弹

| 常量 | 值 | 含义 |
|------|----|------|
| `TANK_SIZE` | 36 | 坦克边长（= TILE） |
| `TANK_SPEED` | 96 | 坦克默认速度 |
| `PLAYER_SPEED` | 120 | 玩家速度 |
| `ENEMY_SPEED` | 72 | 敌人基础速度（tier 2 × 1.25 = 90） |
| `BULLET_SIZE` | 8 | 子弹边长 |
| `BULLET_SPEED` | 320 | 子弹速度（px/s） |
| `PLAYER_FIRE_COOLDOWN` | 0.45 | 玩家开火间隔 |
| `ENEMY_FIRE_COOLDOWN_MIN/MAX` | 0.8 / 1.6 | 敌人开火间隔 |

### 1.3 玩家 / 敌人 / 道具

| 常量 | 值 | 含义 |
|------|----|------|
| `PLAYER_LIVES` | 3 | 初始生命 |
| `RESPAWN_INVULN` | 2.0 | 重生无敌时间（秒） |
| `SCORE_PER_ENEMY` | 100 | 杀敌得分 |
| `SCORE_PER_LEVEL` | 1000 | 通关得分（关索引 × 1000） |
| `P2_ENABLED_DEFAULT` | True | **C1** 菜单默认进 2P 模式 |

### 1.4 状态

```python
class State:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    LEVEL_COMPLETE = "level_complete"
    GAME_OVER = "game_over"
    VICTORY = "victory"
```

### 1.5 方向

```python
class Dir:
    UP    = (0, -1)
    DOWN  = (0, 1)
    LEFT  = (-1, 0)
    RIGHT = (1, 0)
    ALL   = [UP, DOWN, LEFT, RIGHT]
    NAMES = {UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT"}
```

### 1.6 敌人 tier 颜色

```python
ENEMY_TIER_COLORS = [
    (180, 180, 180),  # 灰 - tier 0
    (220, 110, 110),  # 红 - tier 1
    (110, 200, 110),  # 绿 - tier 2
]
POWERUP_CARRIER_COLOR = (255, 60, 60)  # **B1** 红闪敌人
```

### 1.7 `LEVEL_DIFFICULTY` — 关卡难度表 (15 项)

```python
LEVEL_DIFFICULTY = [
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 1
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 2
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 3
    {"enemy_count": 18, "max_on_screen": 4, "enemy_speed": 78,  "spawn_interval": 1.8},  # 关 4
    {"enemy_count": 20, "max_on_screen": 4, "enemy_speed": 84,  "spawn_interval": 1.5},  # 关 5
    {"enemy_count": 25, "max_on_screen": 5, "enemy_speed": 90,  "spawn_interval": 1.2},  # 关 6
    {"mode": "survival", "max_on_screen": 5, "enemy_speed": 96,  "spawn_interval": 0.8},  # 关 7 B3
    {"mode": "boss", "boss_count": 1, "enemy_speed": 60},  # 关 8 C2 BOSS
    # C4 新增 4 关 campaign
    {"enemy_count": 28, "max_on_screen": 4, "enemy_speed": 84,  "spawn_interval": 1.5},  # 关 9 冰面
    {"enemy_count": 30, "max_on_screen": 4, "enemy_speed": 88,  "spawn_interval": 1.4},  # 关 10 密室
    {"enemy_count": 32, "max_on_screen": 4, "enemy_speed": 90,  "spawn_interval": 1.3},  # 关 11 钢墙
    {"enemy_count": 35, "max_on_screen": 5, "enemy_speed": 92,  "spawn_interval": 1.1},  # 关 12 终极常规
    # C4 生存 II
    {"mode": "survival", "max_on_screen": 6, "enemy_speed": 102, "spawn_interval": 0.6},  # 关 13
    # C4 BOSS 关
    {"mode": "boss", "boss_count": 1, "enemy_speed": 60},  # 关 14 BOSS II
    {"mode": "boss", "boss_count": 1, "enemy_speed": 60},  # 关 15 终极 BOSS
]
```

### 1.8 道具时长 (B4)

```python
MAGNET_DURATION = 8.0      # 磁铁持续时间
LASER_DURATION = 10.0      # 激光持续时间
MINE_COUNT = 3             # 一次放几颗地雷
MINE_BLAST_RADIUS = 100    # 地雷爆炸 AOE 像素范围
MINE_BLAST_DAMAGE = True   # 地雷对敌人一击必杀
```

### 1.9 C2 BOSS 常量

```python
BOSS_HP = 10
BOSS_SPEED = 60
BOSS_FIRE_COOLDOWN = 1.5
BOSS_COLOR = (180, 80, 200)  # 紫色
```

### 1.10 C3 特殊敌人

```python
SPECIAL_ENEMY_CHANCE = 0.15      # campaign 模式生成特殊敌人的概率
SUICIDE_BLAST_TRIGGER_RADIUS = 80   # 自爆触发半径
SUICIDE_BLAST_DAMAGE_RADIUS = 64    # 自爆伤害半径
STEALTH_CYCLE = 2.0           # 隐形周期
STEALTH_VISIBLE_FRAC = 0.15   # 显形时长占比
ARMOR_HP = 3                  # 装甲血量
ROCKET_SPEED_MULT = 2.0       # 火箭速度倍率
BOUNCE_COUNT = 1              # 弹跳次数
SPECIAL_COLORS = {
    "suicide": (255, 100, 0), "stealth": (150, 150, 220),
    "armor": (80, 80, 80),   "rocket": (220, 200, 60),
    "bounce": (200, 80, 200),
}
```

### 1.11 F20 背景音乐

```python
MUSIC_ENABLED = True
MUSIC_VOLUME = 0.35
MUSIC_SAMPLE_RATE = 22050
```

---

## 2. `utils/collision.py` — 碰撞辅助

### `aabb(a, b) -> bool`
AABB 碰撞，a 和 b 需要 `.rect` 或本身是 Rect。

### `snap_axis(value, grid, size) -> int`
吸附到格点。`value = round(value / grid) * grid`。

### `line_of_sight(start, end, tilemap) -> bool`
检查两点（中心像素）之间是否有 `blocks_bullet=True` 的瓦片阻挡。仅支持水平/垂直直线。

---

## 3. `utils/draw.py` — 纯代码绘制

### `draw_tank(surface, rect, direction, color, dark=None, flashing=False, tread_phase=0.0, hit_flash=False)`
绘制一辆坦克（含车身、履带、炮塔、炮管、闪烁、闪红）。

### `draw_bullet(surface, rect, direction)`
绘制一颗子弹（圆 + 方向尾迹）。

### `draw_tile(surface, tile, rect)`
按 tile 类型分派：Empty / Brick / Steel / Grass / Water / **Ice (B5)** / Base。

### 内部辅助

- `_darken(color, factor)` — 颜色 × factor
- 7 个 `_draw_xxx` 函数

---

## 4. `utils/sound.py` — 音效管理

```python
play(name: str)         # 播放 fire/explosion/hit/start
set_muted(muted)        # 静音开关
is_muted() -> bool
is_available() -> bool  # mixer OK + 至少加载了一个 wav
```

启动时 wav 缺失自动调 `gen_sounds.main()` 生成。**所有失败静默不抛**。

---

## 5. `utils/events.py` — 事件总线 (A2)

```python
subscribe(event_name, callback) -> callable  # 返回 unsubscribe()
publish(event_name, **kwargs)
clear()                                     # 测试用
subscriber_count(event_name) -> int
```

| 常量 | 字符串 | Payload（kwargs） | 触发位置 |
|------|--------|--------------------|----------|
| `ENTITY_KILLED` | `"entity.killed"` | `kind`, `owner`, `x`, `y`, `score_delta`, **C2 `is_boss`** | Level 敌人被击杀 |
| `POWERUP_PICKED` | `"powerup.picked"` | `type`, `x`, `y` | Level 道具拾取 |
| `BASE_HIT` | `"base.hit"` | （无） | 基地被子弹击中 |
| `BASE_DESTROYED` | `"base.destroyed"` | （无） | 基地被毁 |
| `LEVEL_COMPLETED` | `"level.completed"` | `score`, `level_index` | 关卡完成 |
| `LEVEL_FAILED` | `"level.failed"` | `reason`: `"base_destroyed"` \| `"lives_zero"` | 关卡失败 |
| `ACHIEVEMENT_UNLOCKED` | **C5** `"achievement.unlocked"` | `id: str` | 成就解锁 |

`LEVEL_FAILED.reason` 取值常量：
- `REASON_BASE_DESTROYED = "base_destroyed"`
- `REASON_LIVES_ZERO = "lives_zero"`

---

## 6. `utils/i18n.py` — 国际化 (B6)

```python
t(key, **kwargs) -> str     # 查表 + format 占位符
set_lang(lang: str) -> bool # 切换语言, 返回是否成功
get_lang() -> str           # 当前语言 (zh/en)
reload()                     # 重载 (开发用)
available_langs() -> list   # 列出 i18n/ 下所有语言文件
```

字符串在 `i18n/zh.json` + `i18n/en.json`。K_L 切语言。

---

## 7. `utils/highscores.py` — 排行榜 (B2)

```python
DEFAULT_PATH = "data/highscores.json"
MAX_ENTRIES = 10

add_score(score, level, name="YOU", path=DEFAULT_PATH) -> (rank, scores)
load_highscores(path=DEFAULT_PATH) -> list
qualifies(score, scores) -> bool
reset_for_test(path=DEFAULT_PATH)
```

JSON 格式：`{"scores": [{name, score, level, date}, ...]}`，按 score 降序，**原子写**（临时文件 + rename）。

---

## 8. `utils/achievements.py` — 成就系统 (C5)

```python
@dataclass(frozen=True)
class Achievement:
    id: str
    name_key: str         # i18n key, e.g. "ach.first_blood.name"
    desc_key: str
    icon_color: tuple

ACHIEVEMENTS: list[Achievement]   # 8 个
get_achievement(aid: str) -> Achievement | None

class Manager:
    def __init__(path=DEFAULT_PATH)         # 自动订阅 events
    def save()                               # 持久化
    def on_level_start(mode)                 # 关卡开始 (重置 LevelState)
    def on_level_tick(dt, mode)             # 每帧 (survival 计时)
    def on_player_damaged(now)               # 玩家受伤 (untouchable/iron_wall 用)
    def on_survival_tick(dt)                 # survival 模式单独接口
    def process_event(name, **kwargs)        # 手动分发 (备用)
    def is_unlocked(aid) -> bool
    def unlocked_count() -> int
    def total_count() -> int
    def clear_recent()                       # 清空本会话新解锁
    def close()                              # 取消订阅 (cleanup)
```

8 个成就：
- **一次性**（跨会话）：first_blood / boss_slayer / powerup_collector / collector / legend
- **关卡级**（本关重置）：sharpshooter / pacifist / survivor

JSON 格式：`{"unlocked": [...], "unlock_times": {...}, "powerup_total": int, "powerup_types": [...]}`。

---

## 9. `utils/replay.py` — 回放/录像 (C6)

```python
KEY_NAMES = ("up", "down", "left", "right", "fire")  # 5 个动作
DEFAULT_DIR = "data/replays"

class Recorder:
    def __init__(level_index, num_players=1)
    def start()                          # 启动录制
    def stop(final_score=0, result="completed")
    def is_recording() -> bool
    def record_frame(keys: dict)         # 每帧: {up, down, left, right, fire}
    def save(name: str, directory=DEFAULT_DIR) -> str
    def to_dict() -> dict

class Player:
    def load(path: str) -> bool
    def get_keys_at(frame_idx: int) -> dict   # 越界返回全 False

def list_replays(directory=DEFAULT_DIR) -> list
def delete_replay(path: str)
def reset_for_test(directory=DEFAULT_DIR)
```

JSON 格式：`{"name, date, level_index, num_players, frames: [{5 keys}], total_frames, final_score, result"}`。

**限制**：不录 random 种子，重放时敌人位置/行为有偏差（但玩家按键序列一致）。

---

## 10. `utils/music.py` — 背景音乐 (F20)

```python
MUSIC_SAMPLE_RATE = 22050
NOTE_FREQ: dict[str, float]   # C3-C5 频率表 (Hz)

# 程序生成 (3 段, 8-bit chiptune 方波 + ADSR)
generate_menu_bgm() -> pygame.mixer.Sound
generate_game_bgm() -> pygame.mixer.Sound
generate_victory_bgm() -> pygame.mixer.Sound

class MusicManager:
    def __init__(volume=MUSIC_VOLUME)
    def set_enabled(enabled: bool)         # 关闭时停, 开启恢复
    def is_enabled() -> bool
    def set_volume(volume: float)          # [0, 1], 钳制
    def get_volume() -> float
    def play_track(name: str, loops=-1)     # menu/game/victory
    def stop()                              # 保留 current_track (便于 set_enabled 恢复)
    def pause()                             # 暂停 (K_P 调)
    def resume()                            # 恢复
    def current_track() -> str | None
    def is_playing() -> bool                # 考虑 was_playing_before_pause

def track_for_state(state: str) -> str | None
# "menu" -> "menu", "playing" -> "game", "victory" -> "victory"
# "paused" / "level_complete" / "game_over" -> None
```

**0 版权风险** — 不携带任何音乐文件，全部 `numpy` 程序合成。

---

## 11. `game/game.py` — 顶层控制器

### `class Game`

```python
def __init__(self): ...           # 初始化 pygame + 状态 + achievements + music
def run(self) -> None             # 主循环
def handle_events(self) -> None  # 输入分发 (含 K_H/A/R/M/+/- 快捷键)
def start_game(self) -> None      # 开始新游戏 + 启动 Recorder
def restart(self) -> None         # = start_game
def start_replay(path) -> bool    # C6 从回放文件启动
def next_level(self) -> None      # 下一关 / VICTORY
def update(self, dt) -> None      # 状态机 + 成就 + 回放 + BGM
def draw(self) -> None            # 渲染 (含子视图路由)
def _record_highscore(self)       # B2 上榜 (try/except 兜底)
def _stop_recording(self, result) # C6 停止录制
```

### 主菜单快捷键

| 按键 | 作用 |
|------|------|
| Enter/Space | 开始 |
| 1/2 | 1P/2P 模式 |
| H | 排行榜 (B2) |
| A | 成就 (C5) |
| R | 回放列表 (C6) |
| M | 开关 BGM (F20) |
| +/- | 音量 (F20) |
| L | 中英切换 (B6) |
| ESC | 退出 |

---

## 12. `game/level.py` — 关卡

### `class Level`

```python
def __init__(self, level_index, lives, score, num_players=1, achievements=None)
def _spawn_player(self, index=0, input_map=None) -> PlayerTank
def _spawn_enemy(self) -> EnemyTank | None    # C3 15% 概率特殊
def respawn_player(self, index=0) -> None
def base_destroyed(self) -> None
def update(self, dt) -> None                   # 一帧所有逻辑
def _apply_powerup(self, pu, target_idx=0)    # C1 多玩家分发
def _get_magnet_target() -> tuple | None       # B4 magnet 吸引
def _activate_shovel(self, duration)           # 钢墙保护基地
def _restore_shovel(self)
def _on_base_hit(self, tile)                   # 基地被击中震屏
def draw(self, surface)
def _draw_scene(self, surface)
def _all_players_dead(self) -> bool            # C1
```

### 模块常量

```python
POWERUP_SOUND = {
    "star": "start", "grenade": "explosion", "helmet": "hit",
    "clock": "start", "shovel": "hit", "tank": "start",
    "magnet": "start", "laser": "hit", "mine": "hit",  # B4
}
```

### 关卡模式

| mode | enemy_count | 行为 | 关卡 |
|------|-------------|------|------|
| `campaign`（默认） | 15-35 | 杀够 + 无存活 → completed | 1-6, 9-12 |
| `survival` | inf | 永不自然完成，靠 failed | 7, 13 |
| `boss` | 0 | BOSS 全死 → completed | 8, 14, 15 |

---

## 13. `game/hud.py` — HUD

```python
draw_hud(surface, lives, score, level, enemies_left, p2_lives=None)
get_font(size, bold=False) -> pygame.font.Font
_find_cjk_font() -> str | None    # 缓存
```

---

## 14. `game/menu.py` — 菜单/结束画面

```python
draw_menu(surface, t, num_players)        # 主菜单
draw_pause(surface)                       # 暂停遮罩
draw_level_complete(surface, level, score, t)
draw_game_over(surface, score, victory, t)
draw_highscores(surface, scores, t)        # B2
draw_achievements(surface, manager, t)     # C5
draw_replay_list(surface, replays, sel, t)  # C6
```

---

## 15. `game/input.py` — 输入抽象

```python
class InputMap:
    __slots__ = ("player_id", "up_keys", "down_keys", "left_keys", "right_keys", "fire_keys")
    def __init__(self, player_id, *, up_keys=(), down_keys=(), left_keys=(), right_keys=(), fire_keys=())
    def is_mine(key) -> bool
    def direction_for(key) -> str | None     # "up" / "down" / ...
    def is_fire(key) -> bool

P1_INPUT = InputMap(0, up=(K_w,), down=(K_s,), left=(K_a,), right=(K_d,), fire=(K_SPACE, K_j))
P2_INPUT = InputMap(1, up=(K_UP,), down=(K_DOWN,), left=(K_LEFT,), right=(K_RIGHT,), fire=(K_RETURN, K_RSHIFT))
```

---

## 16. `entities/tank.py` — 坦克基类

```python
class Tank:
    BASE_SPEED = 96
    SNAP_RATE = 900
    TREAD_PERIOD = 6
    FIRE_COOLDOWN = 0.5

    def __init__(self, x, y, direction, color, dark_color, speed=None)
    def try_move(self, dt, dx, dy, tilemap, other_tanks) -> bool
    def try_change_direction(self, new_dir, tilemap, other_tanks) -> bool
    def update_snap(self, dt)
    def can_move_now(self) -> bool
    def shoot(self, bullets, effects=None) -> Bullet | None
    def on_hit(self, bullet)                 # hp -= 1, hp<=0 -> dead
    def update_cooldown(self, dt)
    def draw(self, surface)
```

### 关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `rect` | `pygame.Rect` | 碰撞盒 |
| `dir` | `(dx, dy)` | 当前朝向 |
| `color` / `dark_color` | `tuple` | 车身主色 / 履带阴影 |
| `speed` | `float` | 实际速度 |
| `cooldown` | `float` | 开火冷却 |
| `dead` | `bool` | 死亡标记 |
| `flashing_time` | `float` | 无敌闪烁 |
| `snap_axis` | `None / 'x' / 'y'` | 软吸附进行中 |
| `snap_target` | `int` | 吸附终点 |
| `tread_phase` | `float` | 履带动画 |
| `is_player` | `bool` | 玩家标记 |
| `hit_flash_time` | `float` | 被击中闪红 |
| `killed_by_powerup` | `bool` | 避免双重计分 |
| `hp` | `int` | **C2** 多血（默认 1，BOSS=10，装甲=3） |
| `breaks_steel` | `bool` | 子弹破钢墙 |

---

## 17. `entities/player.py` — 玩家

```python
class PlayerTank(Tank):
    BASE_SPEED = PLAYER_SPEED
    FIRE_COOLDOWN = PLAYER_FIRE_COOLDOWN
    SLIDE_DURATION = 0.10

    def __init__(self, x, y, input_map=None)
    def handle_event(self, event)
    def _active_direction(self) -> tuple | None
    def update(self, dt, tilemap, other_tanks, bullets, effects=None)
    def draw(self, surface)
```

**独有字段**：`keys`, `key_press_time`, `_time`, `slide_timer`, `slide_dir`, `upgrade_level`, `invincible`, `frozen_enemies_timer`, `lives` (C1), `player_id` (C1), `input_map` (C1), `magnet_timer` (B4), `laser_timer` (B4), **`on_ice` (B5)**。

**B5 冰面**：每帧检测中心点瓦片类型 → `on_ice=True` 时 `update_snap` 跳过 + 滑行 `slide_timer` 不衰减。

---

## 18. `entities/enemy.py` — AI 敌人

```python
class EnemyTank(Tank):
    BASE_SPEED = ENEMY_SPEED

    def __init__(self, x, y, tier=0, enemy_speed=None, is_powerup_carrier=None)
    def update(self, dt, tilemap, other_tanks, bullets, player, effects=None,
               base_pos=None, target_priority="player")
    def on_hit(self, bullet)
    def _choose_target_dir(self, tilemap, player, base_pos, priority) -> tuple | None
    def _dir_to_target(self, tilemap, target_center) -> tuple | None
```

**第 5 个位置参数是 `player`（不是 effects）** — C2 review 修过的关键。

**Tier 系统**：
- tier 0 灰 / tier 1 红 / tier 2 绿
- tier 2 速度 × 1.25 + 破钢墙
- tier 1 开火更准

**B1 红闪敌人**：`is_powerup_carrier=True` → 100% 掉道具 + 鲜红色 + 闪白。

---

## 19. `entities/boss.py` — BOSS (C2)

```python
class BossTank(Tank):
    FIRE_COOLDOWN = BOSS_FIRE_COOLDOWN

    def __init__(self, x, y, color=None, dark_color=None)
    def update(self, dt, tilemap, other_tanks, bullets, player,
               effects=None, base_pos=None, target_priority="player")
```

**简化 AI**：沿 `self.dir` 直线移动 + 撞墙 180° 反弹 + 1.5s 周期开火。hp=BOSS_HP (10)，破钢墙。

**签名约定**：第 5 个位置参数是 `player`（跟 EnemyTank 对齐），让 `Level.update` 通用调用。

---

## 20. `entities/special.py` — 5 种特殊敌人 (C3)

```python
class SuicideEnemy(EnemyTank):    # 距玩家 <80px 自爆
class StealthEnemy(EnemyTank):    # 周期 2s 显形 0.3s
class ArmorEnemy(EnemyTank):      # hp=3
class RocketEnemy(EnemyTank):     # 子弹 2x 速 + 破钢墙
class BounceEnemy(EnemyTank):     # 子弹反弹 1 次

SPECIAL_ENEMY_CLASSES = [SuicideEnemy, StealthEnemy, ArmorEnemy, RocketEnemy, BounceEnemy]
```

每个都覆写 `__init__` 强制颜色（避免被 tier 覆盖），5% 概率在 campaign 模式生成。

---

## 21. `entities/bullet.py` — 子弹

```python
class Bullet:
    TRAIL_LEN = 6

    def __init__(self, x, y, direction, owner)
    def update(self, dt, tilemap, bullets, tanks, base_callback, effects=None)
    def _spawn_explosion(self, effects, scale, big=False)
    def _bounce(self)                          # C3 弹跳内部
    def draw(self, surface)
```

**关键字段**：`direction`, `owner` ("player"/"enemy"), `rect`, `dead`, `can_break_steel`, `is_laser` (B4), **`bounces_left` (C3)**, **`speed_multiplier` (C3)**, `trail`。

---

## 22. `entities/powerup.py` — 道具 (9 种)

```python
class PowerUp:
    def __init__(self, x, y, type)
    def update(self, dt, magnet_target=None)  # B4 magnet 吸引
    def draw(self, surface)

def spawn_random_powerup(x, y) -> PowerUp
```

9 种 type：`star` / `grenade` / `helmet` / `clock` / `shovel` / `tank` / **B4 `magnet`** / **B4 `laser`** / **B4 `mine`**。

---

## 23. `entities/mine.py` — 地雷 (B4)

```python
class Mine:
    def __init__(self, x, y, lifetime=10.0)
    def update(self, dt, enemies, effects, events) -> int  # 返回击杀数
    def draw(self, surface)

def spawn_mines_around(player, count=3) -> list[Mine]
```

---

## 24. `entities/effects.py` — 特效

```python
class MuzzleFlash:
    def __init__(self, x, y, direction, color)
    def update(self, dt)
    def draw(self, surface)

class Explosion:
    def __init__(self, x, y, big=False)

class Particle: ...   # Explosion 内部用
```

---

## 25. `world/tilemap.py` — 地图

```python
class TileMap:
    def __init__(self, tiles, player_spawn, enemy_spawns, base_tile, base_pos)
    @classmethod
    def from_layout(cls, layout: list[str]) -> TileMap
    def rect_collides_solid(self, rect) -> bool
    def rect_hits_brick_subcell(self, rect) -> list
    def rect_hits_steel_or_base(self, rect) -> list
    def draw(self, surface)
    def draw_foreground(self, surface)        # 草丛层
    def world_to_grid(self, x, y) -> (col, row)
    def grid_to_world(self, col, row) -> (x, y)
```

### 布局字符

| 字符 | 含义 |
|------|------|
| `.` | TileEmpty 空地 |
| `B` | TileBrick 砖块 |
| `S` | TileSteel 钢墙 |
| `G` | TileGrass 草丛 |
| `W` | TileWater 水域 |
| `I` | **B5** TileIce 冰面 |
| `P` | 玩家出生点 |
| `E` | 敌人出生点（最多 3 个有效）|
| `X` | 基地（关 7/13/8/14/15 不用） |

---

## 26. `world/levels.py` — 15 关数据

```python
LEVELS = [LEVEL_1, ..., LEVEL_15]   # 15 项

def get_level(index: int) -> list[str]      # index % len(LEVELS)
def get_level_difficulty(index: int) -> dict
def get_total_levels() -> int               # 15
```

---

## 27. 公开事件触发点（速查）

| 模块 | 事件 | Payload |
|------|------|---------|
| Level 敌人被玩家击杀 | `ENTITY_KILLED` | kind=enemy, owner=player, x, y, score_delta=100, **C2 is_boss** |
| Level 自爆者自爆 | `ENTITY_KILLED` | kind=enemy, owner=powerup, score_delta=0 |
| Level 玩家拾取道具 | `POWERUP_PICKED` | type, x, y, **C1 player_id** |
| Level 基地被子弹击中 | `BASE_HIT` | — |
| Level 基地被毁 | `BASE_DESTROYED` + `LEVEL_FAILED(reason="base_destroyed")` | — |
| Level 通关 | `LEVEL_COMPLETED` | score, level_index |
| Level lives 用尽 | `LEVEL_FAILED(reason="lives_zero")` | — |
| Game GAME_OVER 时 | `LEVEL_FAILED` | — |
| **C5** Manager 解锁成就 | `ACHIEVEMENT_UNLOCKED` | id |
