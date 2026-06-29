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
| `MAP_W` / `MAP_H` | 624 | 地图像素宽/高 |
| `TILE` | 48 | 单瓦片边长（像素） |
| `GRID_W` / `GRID_H` | 13 | 网格行列数 |
| `MAP_PIXEL_W` / `MAP_PIXEL_H` | 624 | 地图像素 |
| `FPS` | 60 | 帧率上限 |

### 1.2 坦克 / 子弹

| 常量 | 值 | 含义 |
|------|----|------|
| `TANK_SIZE` | 48 | 坦克边长（= TILE） |
| `TANK_SPEED` | 96 | 坦克默认速度 |
| `PLAYER_SPEED` | 120 | 玩家速度 |
| `ENEMY_SPEED` | 72 | 敌人基础速度（tier 2 × 1.25 = 90） |
| `BULLET_SIZE` | 10 | 子弹边长 |
| `BULLET_SPEED` | 320 | 子弹速度（px/s） |
| `PLAYER_FIRE_COOLDOWN` | 0.45 | 玩家开火间隔 |
| `ENEMY_FIRE_COOLDOWN_MIN` | 0.8 | 敌人开火最小间隔 |
| `ENEMY_FIRE_COOLDOWN_MAX` | 1.6 | 敌人开火最大间隔 |

### 1.3 玩家 / 敌人 / 道具

| 常量 | 值 | 含义 |
|------|----|------|
| `PLAYER_LIVES` | 3 | 初始生命 |
| `RESPAWN_INVULN` | 2.0 | 重生无敌时间（秒） |
| `SCORE_PER_ENEMY` | 100 | 杀敌得分 |
| `SCORE_PER_LEVEL` | 1000 | 通关得分（关索引 × 1000） |
| `ENEMIES_PER_LEVEL` | 15 | 默认每关敌人数（被 LEVEL_DIFFICULTY 覆盖） |
| `MAX_ENEMIES_ON_SCREEN` | 3 | 默认同屏上限（被 LEVEL_DIFFICULTY 覆盖） |
| `ENEMY_SPAWN_INTERVAL` | 2.0 | 默认生成间隔（被 LEVEL_DIFFICULTY 覆盖） |
| `ENEMY_SPAWN_X` | `[0, GRID_W//2, GRID_W-1] × TILE` | 默认敌人生成 X（实际未用，spawn 走 `tilemap.enemy_spawns`） |
| `ENEMY_SPAWN_Y` | `TILE * 0` | 默认敌人生成 Y（实际未用） |
| `PLAYER_SPAWN` | `(TILE*(GRID_W//2), TILE*(GRID_H-2))` | 玩家出生点（实际未用，走 `tilemap.player_spawn`） |
| `BASE_GRID` | `(GRID_W//2, GRID_H-1)` | 基地默认网格（实际未用，走 `tilemap.base_pos`） |

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
```

### 1.7 `LEVEL_DIFFICULTY` — 关卡难度表

```python
LEVEL_DIFFICULTY = [
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72, "spawn_interval": 2.0},  # 关 1
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72, "spawn_interval": 2.0},  # 关 2
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72, "spawn_interval": 2.0},  # 关 3
    {"enemy_count": 18, "max_on_screen": 4, "enemy_speed": 78, "spawn_interval": 1.8},  # 关 4
    {"enemy_count": 20, "max_on_screen": 4, "enemy_speed": 84, "spawn_interval": 1.5},  # 关 5
    {"enemy_count": 25, "max_on_screen": 5, "enemy_speed": 90, "spawn_interval": 1.2},  # 关 6
]
```

---

## 2. `utils/collision.py` — 碰撞辅助

### `aabb(a, b) -> bool`
AABB 碰撞，a 和 b 需要 `.rect` 或本身是 Rect。

### `snap_axis(value, grid, size) -> int`
吸附到格点。`value = round(value / grid) * grid`。

### `line_of_sight(start, end, tilemap) -> bool`
检查两点（中心像素）之间是否有 `blocks_bullet=True` 的瓦片阻挡。仅支持水平/垂直直线。
- `start`, `end`：`(x, y)` 像素
- `tilemap`：`TileMap` 实例
- 返回 `True` 表示视线通畅

### `grid_of(px, py) -> (col, row)` / `grid_size(px, py) -> (TILE, TILE)`
辅助函数（实际项目用 `TileMap.world_to_grid` 替代）。

---

## 3. `utils/draw.py` — 纯代码绘制

### `draw_tank(surface, rect, direction, color, dark=None, flashing=False, tread_phase=0.0, hit_flash=False)`
绘制一辆坦克（含车身、履带、炮塔、炮管、闪烁、闪红）。

### `draw_bullet(surface, rect, direction)`
绘制一颗子弹（圆 + 方向尾迹）。

### `draw_tile(surface, tile, rect)`
按 tile 类型分派：
- `TileEmpty` → 跳过
- `TileBrick` → `_draw_brick(surface, rect, subtl)`
- `TileSteel` → `_draw_steel(surface, rect)`
- `TileGrass` → `_draw_grass(surface, rect)`
- `TileWater` → `_draw_water(surface, rect)`（带时间动画）
- `TileIce` → `_draw_ice(surface, rect)`
- `TileBase` → `_draw_base(surface, rect, destroyed)`

### 内部辅助

- `_darken(color, factor) -> tuple` — 颜色 × factor
- 6 个 `_draw_xxx` 函数

---

## 4. `utils/sound.py` — 音效管理

### `play(name: str)`
播放音效。`name ∈ {"fire", "explosion", "hit", "start"}`。失败静默。

### `set_muted(muted: bool)` / `is_muted() -> bool`
静音开关。

### `is_available() -> bool`
音效系统是否可用（mixer 初始化成功 + 至少加载了一个 wav）。

### 内部

- `_ensure_mixer()`：首次调用时初始化 pygame.mixer，缺失 wav 时自动调 `gen_sounds.main()` 生成
- 模块级单例状态：`_mixer_initialized`, `_sounds`, `_muted`, `_disabled`

## 4.5 `utils/events.py` — 事件总线（v1.4 阶段 A2）

publish-subscribe 模块，单线程同步触发，异常隔离。为成就（F10）、回放（F13）、CI 钩子（F12）提供解耦的事件流。

### 事件名常量

| 常量 | 字符串 | Payload（kwargs） |
|------|--------|--------------------|
| `ENTITY_KILLED` | `"entity.killed"` | `kind`, `owner`, `x`, `y`, `score_delta` |
| `POWERUP_PICKED` | `"powerup.picked"` | `type`, `x`, `y` |
| `BASE_HIT` | `"base.hit"` | （无） |
| `BASE_DESTROYED` | `"base.destroyed"` | （无） |
| `LEVEL_COMPLETED` | `"level.completed"` | `score`, `level_index` |
| `LEVEL_FAILED` | `"level.failed"` | `reason`：`"base_destroyed"` \| `"lives_zero"` |

### `subscribe(event_name, callback) -> callable`
订阅事件，返回 `unsubscribe()` 函数。同一事件可多个订阅者；同一 callback 多次 subscribe 会被加多次。

### `publish(event_name, **kwargs) -> None`
同步触发所有订阅者。遍历时复制列表，回调内 unsubscribe 不影响本次 publish。**单个订阅者抛错被 try/except 吞掉并打印 traceback，不影响其他订阅者。**

### `clear() -> None`
清空所有订阅（测试用）。游戏正常运行时不需要调用。

### `subscriber_count(event_name) -> int`
返回某事件当前订阅者数量（测试/调试用）。

### 用法示例

```python
from utils import events
from utils.events import ENTITY_KILLED

def on_kill(kind, owner, x, y, score_delta):
    if kind == "enemy" and owner == "player":
        achievements.unlock("first_blood")

unsub = events.subscribe(ENTITY_KILLED, on_kill)
# ... 之后
unsub()  # 取消订阅
```

### 当前 `game/level.py` 触发点

| 触发位置 | 事件 | 说明 |
|----------|------|------|
| 敌人被玩家击杀（`score += 100` 后） | `ENTITY_KILLED` | 含 kind="enemy", owner="player", score_delta=100 |
| 道具拾取（`_apply_powerup` 后） | `POWERUP_PICKED` | 含 type |
| `_on_base_hit`（基地被子弹击中） | `BASE_HIT` | — |
| 基地被毁（`update` 末尾检测） | `BASE_DESTROYED` + `LEVEL_FAILED(reason="base_destroyed")` | 一起发 |
| 关卡完成（敌人全灭） | `LEVEL_COMPLETED` | 含 score, level_index |
| `respawn_player` lives 用尽 | `LEVEL_FAILED(reason="lives_zero")` | — |
| `base_destroyed()` | `LEVEL_FAILED(reason="base_destroyed")` | — |
| `update` 中 lives 耗尽 | `LEVEL_FAILED(reason="lives_zero")` | — |

---

## 5. `utils/colors.py` — 颜色常量

`BLACK`, `WHITE`, `GRAY`, `DARK_GRAY`, `LIGHT_GRAY`,
`PLAYER_COLOR/PLAYER_DARK`, `ENEMY_COLOR/ENEMY_DARK`,
`BRICK/BRICK_DARK/BRICK_LIGHT`, `STEEL/STEEL_DARK/STEEL_LIGHT`,
`GRASS/GRASS_DARK`, `WATER/WATER_LIGHT`, `ICE/ICE_LIGHT`,
`BASE_BODY/BASE_DARK/BASE_DEAD`, `BULLET_COLOR/BULLET_OUTLINE`,
`HUD_BG/HUD_TEXT/HUD_ACCENT`, `MENU_BG/MENU_TITLE/MENU_HINT/MENU_DARK`

（详细 RGB 见 `utils/colors.py`）

---

## 6. `game/game.py` — 顶层控制器

### `class Game`

```python
def __init__(self): ...         # 初始化 pygame + 状态
def run(self) -> None:          # 主循环
def handle_events(self) -> None # 输入分发
def start_game(self) -> None    # 开始新游戏
def restart(self) -> None       # 重开（= start_game）
def next_level(self) -> None    # 下一关
def update(self, dt: float) -> None  # 状态机更新
def draw(self) -> None          # 渲染
```

---

## 7. `game/level.py` — 关卡

### `class Level`

```python
def __init__(self, level_index: int, lives: int, score: int)
def _spawn_player(self) -> PlayerTank
def _spawn_enemy(self) -> EnemyTank | None
def respawn_player(self) -> None
def base_destroyed(self) -> None
def update(self, dt: float) -> None
def _apply_powerup(self, pu) -> None
def _activate_shovel(self, duration: float) -> None
def _restore_shovel(self) -> None
def _on_base_hit(self, tile) -> None
def draw(self, surface: pygame.Surface) -> None
def _draw_scene(self, surface) -> None
```

### 模块常量

```python
POWERUP_SOUND = {
    "star":    "start",
    "grenade": "explosion",
    "helmet":  "hit",
    "clock":   "start",
    "shovel":  "hit",
    "tank":    "start",
}
```

---

## 8. `game/hud.py` — HUD

### `draw_hud(surface, lives, score, level, enemies_left, max_lives=3)`
绘制顶部状态条。

### `get_font(size, bold=False) -> pygame.font.Font`
项目内统一字体入口（自动 CJK）。

### `_find_cjk_font() -> str | None`
查找系统 CJK 字体（缓存）。

---

## 9. `game/menu.py` — 菜单/结束画面

```python
def draw_menu(surface, t=0.0) -> None
def draw_pause(surface) -> None
def draw_level_complete(surface, level, score, t) -> None
def draw_game_over(surface, score, victory=False, t=0.0) -> None
```

---

## 10. `world/levels.py` — 关卡数据

### `LEVELS: list[list[str]]`
6 个关卡布局（17×17 字符串网格，见 `settings.GRID_W`/`GRID_H`）。

### `get_level(index) -> list[str]`
循环取关卡布局。

### `get_level_difficulty(index) -> dict`
循环取难度配置。

### `get_total_levels() -> int`
返回 6。

---

## 11. `world/tilemap.py` — 瓦片地图

### `class TileMap`

```python
def __init__(self, level_layout, player_spawn, base_pos, enemy_spawns)
@classmethod
def from_layout(cls, layout: list[str], char_map=None) -> TileMap
def get_tile(self, col, row) -> Tile | None
def pixel_to_grid(self, px, py) -> (col, row)
def grid_to_pixel(self, col, row) -> (px, py)
def world_to_grid(self, wx, wy) -> (col, row)
def grid_to_world(self, col, row) -> (wx, wy)
def rect_collides_solid(self, rect) -> bool
def rect_hits_brick_subcell(self, rect) -> [(tile, col, row, sub), ...]
def rect_hits_steel_or_base(self, rect) -> [(tile, col, row), ...]
def draw(self, surface) -> None
def draw_foreground(self, surface) -> None
```

### `CHAR_TO_TILE: dict`
字符 → 瓦片类映射。

---

## 12. `world/tile.py` — 瓦片类型

```python
class Tile:
    blocks_tank: bool = False
    blocks_bullet: bool = False
    destructible: bool = False
    bullet_consumed: bool = True
    def on_bullet_hit(self, bullet, sub_index=0) -> bool: ...

class TileEmpty(Tile): pass
class TileBrick(Tile):
    subtl: int  # 4 位掩码
    @property
    def alive(self) -> bool
    def on_bullet_hit(self, bullet, sub_index=0) -> bool
    def blocks_tank_now(self) -> bool
class TileSteel(Tile): ...
class TileGrass(Tile): ...
class TileWater(Tile): ...
class TileIce(Tile): ...
class TileBase(Tile):
    destroyed: bool
    def on_bullet_hit(self, bullet, sub_index=0) -> bool
```

---

## 13. `entities/tank.py` — 坦克基类

### `class Tank`

```python
BASE_SPEED = 96
SNAP_RATE = 900
TREAD_PERIOD = 6
FIRE_COOLDOWN = 0.5

def __init__(self, x, y, direction, color, dark_color, speed=None)
def try_move(self, dt, dx, dy, tilemap, other_tanks) -> bool
def can_move_now(self) -> bool
def try_change_direction(self, new_dir, tilemap, other_tanks) -> bool
def update_snap(self, dt) -> None
def _collides(self, tilemap, other_tanks) -> bool
def can_shoot(self) -> bool
def shoot(self, bullets, effects=None) -> Bullet | None
def update_cooldown(self, dt) -> None
def on_hit(self, bullet) -> None
def draw(self, surface) -> None
```

### `snap_to_grid(value, size=TANK_SIZE) -> int`
模块级辅助：吸附到 TILE 边界。

---

## 13.5 `game/input.py` — 输入抽象层（v1.6 阶段 A4）

把"玩家 → 键位"做成数据, 1 玩家时 `P1_INPUT` 兼容旧行为, 双打时 `P2_INPUT` 独立控制。

### `class InputMap`

```python
class InputMap(player_id, *, up_keys=(), down_keys=(),
               left_keys=(), right_keys=(), fire_keys=())
```

玩家 ID + 5 个动作的键位元组（每个动作可绑多个键 alias）。

### 方法

| 方法 | 说明 |
|------|------|
| `is_mine(key) -> bool` | 该 key 是否属于本玩家 (5 个键位集内) |
| `direction_for(key) -> str \| None` | 把 key 翻译为 `"up"` / `"down"` / `"left"` / `"right"`, 不属于返回 None |
| `is_fire(key) -> bool` | 该 key 是否在 fire 键位集 |

### 全局常量

| 常量 | 键位 |
|------|------|
| `P1_INPUT` | `up=(K_w, K_UP)`, `down=(K_s, K_DOWN)`, `left=(K_a, K_LEFT)`, `right=(K_d, K_RIGHT)`, `fire=(K_SPACE, K_j)` |
| `P2_INPUT` | `up=(K_UP,)`, `down=(K_DOWN,)`, `left=(K_LEFT,)`, `right=(K_RIGHT,)`, `fire=(K_RETURN, K_RSHIFT)` |

`P1_INPUT` 包含方向键 alias 保持 1 玩家兼容（A1 决策），`P2_INPUT` 不响应 WASD 防止冲突。

### `PlayerTank.__init__` 新增参数

```python
PlayerTank(x, y, input_map=None)
```

- 不传 → `input_map=P1_INPUT`（兼容旧调用）
- 双打时 `Game.start_game` 创建 P2 时传 `P2_INPUT`

### `PlayerTank.handle_event` 行为

`handle_event` 先用 `self.input_map.is_mine(event.key)` 过滤事件，**自己的键才处理**。同一事件传给多个 PlayerTank 时，各自按自己的 input_map 决定是否响应——A1 review 标记的"P2 共享 P1 键位"问题通过此抽象解决。

## 14. `entities/player.py` — 玩家

### `class PlayerTank(Tank)`

```python
BASE_SPEED = PLAYER_SPEED    # 120
FIRE_COOLDOWN = PLAYER_FIRE_COOLDOWN  # 0.45
SLIDE_DURATION = 0.10

def __init__(self, x, y)
def handle_event(self, event) -> None
def _active_direction(self) -> (dx, dy) | None
def update(self, dt, tilemap, other_tanks, bullets, effects=None) -> None
```

**独有字段**：`keys`, `key_press_time`, `_time`, `slide_timer`, `slide_dir`, `upgrade_level`, `invincible`, `frozen_enemies_timer`

---

## 15. `entities/enemy.py` — 敌人

### `class EnemyTank(Tank)`

```python
BASE_SPEED = ENEMY_SPEED    # 72

def __init__(self, x, y, tier=0, enemy_speed=None)
def update(self, dt, tilemap, other_tanks, bullets, player, effects=None,
           base_pos=None, target_priority="player") -> None
def _choose_target_dir(self, tilemap, player, base_pos, priority) -> (dx, dy) | None
def _dir_to_target(self, tilemap, target_center) -> (dx, dy) | None
def on_hit(self, bullet) -> None
```

### 模块常量

```python
TIER_FIRE_COOLDOWN = {0: (0.8, 1.6), 1: (0.6, 1.2), 2: (0.8, 1.6)}
TIER_SPEED_MULT    = {0: 1.0, 1: 1.0, 2: 1.25}
TIER_BREAKS_STEEL  = {0: False, 1: False, 2: True}
```

---

## 16. `entities/bullet.py` — 子弹

### `class Bullet`

```python
TRAIL_LEN = 6

def __init__(self, x, y, direction, owner)
def update(self, dt, tilemap, bullets, tanks, base_callback, effects=None) -> None
def _spawn_explosion(self, effects, scale=1.0, big=False) -> None
def draw(self, surface) -> None
```

**字段**：`direction`, `owner`, `rect`, `dead`, `can_break_steel`, `trail`, `size`

---

## 17. `entities/powerup.py` — 道具

### `class PowerUp`

```python
LIFETIME = 12.0

def __init__(self, x: int, y: int, ptype: str)
def update(self, dt) -> None
def draw(self, surface) -> None
def _draw_icon(self, surface, x, y, w, h) -> None
```

### 模块级

```python
ALL_TYPES = ["star", "grenade", "helmet", "clock", "shovel", "tank"]
TYPE_COLORS = {...}  # 各 type 对应颜色
def spawn_random_powerup(x, y) -> PowerUp
```

---

## 18. `entities/effects.py` — 特效

### `class MuzzleFlash`

```python
def __init__(self, x, y, direction, owner_color)
def update(self, dt) -> None
def draw(self, surface) -> None
```

### `class Particle`

```python
def __init__(self, x, y, vx, vy, color, life)
def update(self, dt) -> bool  # 返回是否还活着
def draw(self, surface) -> None
```

### `class Explosion`

```python
def __init__(self, x, y, big=False)
def update(self, dt) -> None
def draw(self, surface) -> None
```

---

## 19. `entities/base.py` — 基地（重导出）

```python
from world.tile import TileBase
__all__ = ["TileBase"]
```

---

## 20. `main.py` — 入口

```python
from game.game import Game
def main(): Game().run()
if __name__ == "__main__": main()
```

---

## 21. `tools/gen_sounds.py` — 音效生成

```python
def make_fire() -> list[int]      # 300Hz->100Hz 短扫频 0.08s
def make_explosion() -> list[int] # 200Hz->40Hz + 噪声 0.3s
def make_hit() -> list[int]       # 短促咔哒 0.04s
def make_start() -> list[int]     # 上行扫频 0.2s
def main() -> None                # 生成到 assets/sounds/
```

---

## 22. 测试套件

| 文件 | 测试项 | 关键依赖 |
|------|--------|----------|
| `tests/test_smoke.py` | 15 项 | pygame + Level 真实实例 |
| `tests/test_features.py` | 15 功能 + 7 回归 | 6 关数据/道具/AI tier/视觉/音效/CJK |
| `tests/test_gameplay.py` | 端到端模拟 | 5s 模拟 + 截图 |
| `tests/test_visual.py` | 视觉验证 | 截图 |
| `tests/test_chinese_menu.py` | 中文菜单 | CJK 字体 |

**统一设置**：`os.environ.setdefault("SDL_VIDEODRIVER", "dummy")` → 无头模式。

---

## 23. 资产

| 文件 | 生成方式 |
|------|----------|
| `assets/sounds/fire.wav` | `tools/gen_sounds.py` 启动时自动生成（缺失时） |
| `assets/sounds/explosion.wav` | 同上 |
| `assets/sounds/hit.wav` | 同上 |
| `assets/sounds/start.wav` | 同上 |

**无需任何图片素材**。
