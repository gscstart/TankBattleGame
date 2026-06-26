# 03 · 游戏主循环与世界（game/ + world/）

> 本章讲"游戏的脚手架"：状态机、关卡运行、HUD、菜单、地图、关卡数据。
> 涉及文件：`game/game.py`、`game/level.py`、`game/hud.py`、`game/menu.py`、`world/tilemap.py`、`world/tile.py`、`world/levels.py`。

---

## 1. `Game` — 顶层控制器

**文件**：`game/game.py`

### 1.1 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `screen` | `pygame.Surface` | 832×684 主窗口 |
| `clock` | `pygame.time.Clock` | FPS 限速 |
| `running` | `bool` | 主循环开关 |
| `state` | `str` | 当前状态（`settings.State` 之一） |
| `state_time` | `float` | 当前状态持续时间（关卡完成后等 2s 用） |
| `level` | `Level \| None` | 当前关卡实例 |
| `level_index` | `int` | 当前关卡（0-5） |
| `score` | `int` | 累计分数 |
| `lives` | `int` | 玩家生命 |
| `events_buffer` | `list` | 预留（目前 `Game.handle_events` 直接转发给 `level.players`） |
| `menu_t` | `float` | 菜单时间（用于闪烁） |

### 1.2 状态机切换点

| 触发 | 新状态 | 位置 |
|------|--------|------|
| 菜单按 Enter/Space | PLAYING | `handle_events` |
| PLAYING 按 P | PAUSED | `handle_events` |
| PAUSED 按 P | PLAYING | `handle_events` |
| `level.completed == True` | LEVEL_COMPLETE | `update` |
| `level.failed == True` | GAME_OVER | `update` |
| `state_time >= 2.0` (LEVEL_COMPLETE) | PLAYING 或 VICTORY | `update` + `next_level` |
| GAME_OVER 按 R | PLAYING (重开) | `handle_events` + `restart` |

### 1.3 `start_game()` / `restart()` / `next_level()`

- `start_game()`：重置 `level_index=0` / `score=0` / `lives=3`，创建新 `Level`
- `restart()`：直接调 `start_game()`（GAME_OVER 时按 R）
- `next_level()`：`level_index += 1`，如果 >= len(LEVELS) → VICTORY，否则 PLAYING
  - **关键**：保留 `score` 和 `lives`（跨关卡累加）

### 1.4 `update(dt)`

按状态分发（PLAYING 时调 `level.update(dt)`，完成后把 `level.score` / `level.lives` 同步回 Game）。

### 1.5 `draw()`

```python
if state == MENU:        draw_menu(...)
else:
    screen.fill(BLACK)
    draw_hud(lives, score, level_index, enemies_left)
    level.draw(screen)
    # 状态遮罩
    if PAUSED:            draw_pause(...)
    elif LEVEL_COMPLETE:  draw_level_complete(...)
    elif GAME_OVER:       draw_game_over(..., victory=False)
    elif VICTORY:         draw_game_over(..., victory=True)
```

---

## 2. `Level` — 关卡运行

**文件**：`game/level.py`

### 2.1 字段

| 字段 | 说明 |
|------|------|
| `index` | 关卡编号 0-5 |
| `lives` / `score` | 透传 Game |
| `config` | 当前关卡难度配置（从 `LEVEL_DIFFICULTY` 读） |
| `tilemap` | `TileMap` 实例 |
| `player` | `PlayerTank` 实例 |
| `bullets` | 子弹列表 |
| `enemies` | 敌人列表 |
| `effects` | 特效列表（MuzzleFlash / Explosion） |
| `powerups` | 道具列表 |
| `enemies_killed` | 已杀数（用于计算下次 spawn 的 tier） |
| `enemies_to_spawn` | 待生成数 |
| `_spawn_timer` / `_spawn_idx` | 生成计时 / 上次用的生成点 |
| `completed` / `failed` | 关卡完成 / 失败标志 |
| `screen_shake_time` | 震屏剩余时间（被基地被毁触发） |
| `_shovel_backup` | shovel 道具激活前保存的瓦片 |
| `_shovel_timer` | shovel 剩余时间 |
| `_death_timer` | 玩家死亡后等待重生的时间 |

### 2.2 `_spawn_player()`

从 `tilemap.player_spawn` 读取位置，生成 `PlayerTank`，设 `flashing_time = RESPAWN_INVULN (2.0s)`。

### 2.3 `_spawn_enemy() -> EnemyTank | None`

**触发条件**：
- `enemies_to_spawn > 0`
- 当前同屏敌人数 `< config["max_on_screen"]`

**尝试 3 个生成点（循环 `_spawn_idx` 偏移）**：
- 该位置不能有活着的敌人（`e.dead` 跳过 → 修复 #7 后的关键点）
- 该位置不能有活着的玩家
- 通过则按 `tier = (enemies_killed) % 3` 创建 `EnemyTank`
- 速度用 `config["enemy_speed"]` × tier 倍率

### 2.4 `respawn_player()`

- `lives <= 0` → `failed = True`
- 否则创建新 `PlayerTank`，设 `flashing_time = RESPAWN_INVULN`
- **保留旧玩家的道具状态**（修复 #3）：
  - `upgrade_level` 保留
  - `invincible` 减 1s（重生稍微惩罚）
  - `frozen_enemies_timer` 保留
  - 调 `_restore_shovel()` 处理 shovel 状态

### 2.5 `update(dt)` — 一帧内的全部逻辑

```python
def update(self, dt):
    if completed or failed: return

    # 1. 屏幕震屏计时
    if screen_shake_time > 0: screen_shake_time -= dt

    # 2. Shovel 倒计时
    if _shovel_timer > 0:
        _shovel_timer -= dt
        if _shovel_timer <= 0: _restore_shovel()

    # 3. 敌人生成
    _spawn_timer -= dt
    if _spawn_timer <= 0:
        spawned = _spawn_enemy()
        if spawned is None and enemies_to_spawn > 0:
            _spawn_timer = 0.2  # 失败后快速重试
        else:
            _spawn_timer = config["spawn_interval"]

    # 4. 玩家
    if not player.dead:
        other_tanks = [e for e in enemies if not e.dead]
        player.update(dt, tilemap, other_tanks, bullets, effects=effects)
    else:
        player.update_cooldown(dt)
        if not hasattr(self, "_death_timer"):
            _death_timer = 1.0
        _death_timer -= dt
        if _death_timer <= 0:
            lives -= 1
            if lives > 0: respawn_player()
            else: failed = True
            if hasattr(self, "_death_timer"):
                del _death_timer

    # 5. 玩家道具状态计时
    if not player.dead:
        if player.invincible > 0: player.invincible -= dt
        if player.frozen_enemies_timer > 0:
            player.frozen_enemies_timer -= dt
            for e in enemies: e.frozen = True
        else:
            for e in enemies: e.frozen = False

    # 6. 敌人更新（带瞄准）
    base_pos = ... # 基地中心
    priority = "base" if random.random() < 0.4 else "player"
    for e in enemies:
        if e.dead: continue
        e.update(dt, tilemap, other_tanks, bullets, player,
                 effects=effects, base_pos=base_pos, target_priority=priority)

    # 7. 子弹
    for b in bullets: b.update(dt, tilemap, bullets, [player]+enemies,
                                _on_base_hit, effects=effects)

    # 8. 清理死亡 + 计分 + 掉道具
    bullets = [b for b in bullets if not b.dead]
    newly_dead_enemies = [e for e in enemies if e.dead]
    if newly_dead_enemies:
        enemies = [e for e in enemies if not e.dead]
        for e in newly_dead_enemies:
            if not e.killed_by_powerup:  # 修复 #5
                score += 100
                enemies_killed += 1
            if random.random() < 0.25:
                powerups.append(spawn_random_powerup(e.rect.centerx-24, e.rect.centery-24))

    # 9. 道具拾取
    for pu in powerups:
        pu.update(dt)
        if not player.dead and pu.rect.colliderect(player.rect):
            _apply_powerup(pu)
            pu.dead = True
    powerups = [pu for pu in powerups if not pu.dead]

    # 10. 特效清理
    for fx in effects: fx.update(dt)
    effects = [fx for fx in effects if not fx.dead]

    # 11. 基地状态
    if tilemap.base_tile.destroyed: failed = True

    # 12. 通关判断
    if enemies_to_spawn <= 0 and len(enemies) == 0 and not failed:
        completed = True
```

### 2.6 `_apply_powerup(pu)` — 道具效果分发

```python
if pu.type == "star":    player.upgrade_level = min(2, player.upgrade_level + 1)
elif pu.type == "grenade":
    # 全屏敌人立即死亡（修复 #5 避免双重计分）
    for e in enemies:
        if not e.dead:
            e.dead = True
            e.killed_by_powerup = True
            e.hit_flash_time = 0.3
            effects.append(MuzzleFlash(...))
    score += count * 100
elif pu.type == "helmet":  player.invincible = 10.0
elif pu.type == "clock":   player.frozen_enemies_timer = 8.0
elif pu.type == "shovel":  _activate_shovel(15.0)
elif pu.type == "tank":    self.lives += 1
# 每个道具播放不同音效
play(POWERUP_SOUND.get(pu.type, "hit"))
```

### 2.7 `_activate_shovel(duration)` / `_restore_shovel()`

**激活**（修复 #2）：
- 第一次激活时备份基地 8 周砖块到 `_shovel_backup`（用 dict 存瓦片对象）
- 把 8 格替换为 `TileSteel()`
- 设 `_shovel_timer = duration`（默认 15s）

**恢复**：
- 把备份的瓦片写回 `tilemap.tiles`
- 清 `_shovel_backup` 和 `_shovel_timer`

**`update()` 每帧检查 `_shovel_timer`**，到 0 就自动恢复。

### 2.8 `_on_base_hit(tile)`

基地被命中时：
- `screen_shake_time = 0.3`（震屏）
- 播放 `explosion` 音效

### 2.9 `draw(surface)` — 渲染（含震屏）

```python
ox, oy = 0, 0
if screen_shake_time > 0:
    ox = random.randint(-2, 2)
    oy = random.randint(-2, 2)

if ox or oy:
    tmp = pygame.Surface(surface.get_size())
    _draw_scene(tmp)
    surface.blit(tmp, (ox, oy))
else:
    _draw_scene(surface)
```

**`_draw_scene(surface)` 顺序**：
1. tilemap.draw（瓦片底色 + 砖/钢/水/冰/基地）
2. 每个 enemy.draw
3. player.draw（活着才画）
4. 每个 bullet.draw
5. 每个 powerup.draw
6. 每个 effect.draw
7. **死亡重生提示**（如果 `player.dead and _death_timer`）
8. **玩家无敌时间提示**（头上 `无敌 X.Xs`）
9. tilemap.draw_foreground（草丛，遮住坦克）

---

## 3. `HUD` — 顶部状态条

**文件**：`game/hud.py`

### 3.1 `get_font(size, bold=False)` — 全项目 CJK 字体入口

**机制**：
1. 调用 `_find_cjk_font()` 查系统支持的 CJK 字体
2. 找到 → `pygame.font.SysFont(name, size, bold)`
3. 找不到 → 回退到 `"arial,simhei,notosanscjk,monospace"`

**字体候选列表**（按优先级）：
```
microsoftyahei / msyh            # Windows 微软雅黑
microsoftjhenghei / msjh         # Windows 微软正黑（繁体）
simhei / simsun / simkai / simfang  # Windows 中易
pingfangsc / stheiti / songti    # macOS
hiraginosansgb                   # macOS
notosanscjksc / notosanscjk      # 跨平台
wenquanyimicrohei / wenquanyizenhei  # Linux
arialunicodems                   # Windows Unicode
```

**首次查找后缓存**（`_cjk_searched` + `_cjk_font_name`）。

### 3.2 `draw_hud(surface, lives, score, level, enemies_left, max_lives=3)`

布局（顶部 60px 高）：

```
┌──────────────────────────────────────────┐
│ 生命 [■■■]   分数 001000  第N关  剩余 12│
└──────────────────────────────────────────┘
```

- 背景 `(16, 16, 16)`，底边 2px 金色线
- 生命：3 个小坦克图标，失掉的画黑色 ×
- 关卡：正中显示 `第 N 关`（0-indexed + 1）
- 分数：`{:06d}` 6 位补零
- 剩余敌人：`{:02d}` 2 位补零

---

## 4. `Menu` — 菜单/暂停/结束画面

**文件**：`game/menu.py`

### 4.1 函数

| 函数 | 用途 | 视觉 |
|------|------|------|
| `draw_menu(surface, t)` | 主菜单 | "坦克大战" 大标题（72px 金）+ 闪烁"按回车或空格开始游戏" + 操作说明 |
| `draw_pause(surface)` | 暂停遮罩 | 半透明黑 + "已暂停"（64px） + "按 P 继续" |
| `draw_level_complete(surface, level, score, t)` | 通关 | 半透明黑 + `第 N 关 通关！` + 当前分数 |
| `draw_game_over(surface, score, victory, t)` | 结束 | "胜 利！" 或 "游戏结束" + 最终分数 + 闪烁"按 R 重开" |

**`t` 参数**：用于副标题闪烁（`int(t*2) % 2 == 0` 时显示）。

---

## 5. `TileMap` — 17×17 瓦片地图

**文件**：`world/tilemap.py`

### 5.1 字段

| 字段 | 说明 |
|------|------|
| `tiles` | `list[list[Tile]]`，`GRID_W` 行 `GRID_H` 列（当前 17×17） |
| `player_spawn` | `(col, row)` 玩家出生点（来自 'P'） |
| `base_pos` | `(col, row)` 基地位置（来自 'X'） |
| `base_tile` | `TileBase` 实例（`_find_base()` 找到） |
| `enemy_spawns` | `[(col, row), ...]` 敌人生成点 |

### 5.2 `from_layout(layout, char_map=None)` 类方法

输入 `GRID_H` 个字符串（每行 `GRID_W` 字符，当前 17×17），输出 `TileMap`。

**字符 → 瓦片映射**：
```python
CHAR_TO_TILE = {
    ".": TileEmpty, "B": TileBrick, "S": TileSteel,
    "G": TileGrass, "W": TileWater, "I": TileIce,
    # P / E / X 在 from_layout 里特判
}
```

**特判**：
- `P` → 玩家出生点 + 替换为空地
- `E` → 收集到 `explicit_enemy_spawns` + 替换为空地
- `X` → 基地位置 + 放 `TileBase()`

**默认敌人生成点**（如果关卡没标 E）：`[(0,0), (6,0), (12,0)]`

### 5.3 坐标转换

| 方法 | 输入 | 输出 |
|------|------|------|
| `world_to_grid(wx, wy)` | 世界像素 | `(col, row)` |
| `grid_to_world(col, row)` | `(col, row)` | `(wx, wy)` 像素 |
| `grid_to_pixel(col, row)` | `(col, row)` | `(px, py)` 屏幕像素 |

`MAP_X = 110`, `MAP_Y = 60`, `TILE = 36`（来自 `settings.py`，17×17 网格）。

### 5.4 碰撞查询

| 方法 | 用途 |
|------|------|
| `rect_collides_solid(rect)` | 矩形 vs 地图"实体"（砖/钢/基地/水/边界外） |
| `rect_hits_brick_subcell(rect)` | 矩形 vs 砖块子格（返回子格索引） |
| `rect_hits_steel_or_base(rect)` | 矩形 vs 钢墙或基地 |

**子格索引规则**（修复 #8 后用真实 `TileEmpty`）：
```python
sub_index = sub_r * 2 + sub_c   # 0=左上 1=右上 2=左下 3=右下
```

### 5.5 渲染

| 方法 | 用途 |
|------|------|
| `draw(surface)` | 画底色 + 全部瓦片（除空地） |
| `draw_foreground(surface)` | 单独画草丛（在坦克之上，遮住） |

---

## 6. `Tile` — 瓦片类型

**文件**：`world/tile.py`

### 6.1 类层级

```
Tile（基类）
├─ TileEmpty    # 空地
├─ TileBrick    # 砖块（4 子格可破坏）
├─ TileSteel    # 钢墙
├─ TileGrass    # 草丛
├─ TileWater    # 水域
├─ TileIce      # 冰面（暂未实现打滑）
└─ TileBase     # 基地
```

### 6.2 关键属性（基类）

| 属性 | 含义 |
|------|------|
| `blocks_tank` | 是否阻挡坦克 |
| `blocks_bullet` | 是否阻挡子弹（line_of_sight 用） |
| `destructible` | 是否可被破坏 |
| `bullet_consumed` | 子弹命中后是否被消耗（草丛不消耗） |

### 6.3 各瓦片属性对照

| 类型 | blocks_tank | blocks_bullet | destructible | bullet_consumed | 备注 |
|------|:-----------:|:-------------:|:------------:|:---------------:|------|
| Empty | ❌ | ❌ | ❌ | - | - |
| Brick | ✅ | ✅ | ✅ | ✅ | `subtl` 4 位掩码 |
| Steel | ✅ | ✅ | ❌ | ✅ | 玩家 2 级可破 |
| Grass | ❌ | ❌ | ❌ | ❌ | 坦克和子弹都穿过 |
| Water | ✅ | ❌ | ❌ | ❌ | 阻坦克不阻子弹 |
| Ice | ❌ | ❌ | ❌ | ❌ | 装饰用（未来打滑） |
| Base | ✅ | ✅ | ✅ | ✅ | `destroyed` 标志 |

### 6.4 砖块子格机制

```python
class TileBrick(Tile):
    def __init__(self):
        self.subtl = 0b1111  # 4 个子格全在

    @property
    def alive(self) -> bool:
        return self.subtl != 0

    def on_bullet_hit(self, bullet, sub_index=0) -> bool:
        self.subtl &= ~(1 << sub_index)  # 清除命中子格
        return True

    def blocks_tank_now(self) -> bool:
        """只要还有子格，就阻挡坦克。"""
        return self.alive
```

**绘制**（`utils/draw._draw_brick`）：按 `subtl` 位掩码画 4 个子格，被打掉的画背景色。

---

## 7. `Levels` — 关卡数据

**文件**：`world/levels.py`

### 7.1 数据格式

每个关卡是 `list[str]`，17 行 × 17 列（**必须严格 `GRID_W`×`GRID_H`，测试会检查**）。

```python
LEVEL_1 = [
    ".............",  # 13 个 .
    ".BB.BB.BB.BB.",  # B = 砖块, S = 钢墙
    ...
    "....BBXBB....",  # X = 基地（必填）
    ...
    "..B...P...B..",  # P = 玩家出生
    ...
]
LEVELS = [LEVEL_1, ..., LEVEL_6]
```

### 7.2 字符含义

| 字符 | 含义 |
|------|------|
| `.` | 空地 |
| `B` | 砖块（2×2 子格可独立破坏） |
| `S` | 钢墙 |
| `G` | 草丛 |
| `W` | 水域 |
| `I` | 冰面 |
| `P` | 玩家出生点（必填 1 个） |
| `E` | 敌人出生点（可填 0-3 个，未填则用默认 3 个） |
| `X` | 基地（必填 1 个） |

### 7.3 6 关设计

| 关 | 主题 | 难度 |
|----|------|------|
| 1 | 砖块围墙保护基地 | 入门 |
| 2 | 中央水域，钢墙点缀 | 砖+水+钢 |
| 3 | 复杂迷宫 | S+复杂 B |
| 4 | 钢墙屏障 + 砖块迷宫 | 难度提升 |
| 5 | 水域迷宫 + 多钢墙 | 高难度 |
| 6 | BOSS 关 - 钢墙迷宫 + 25 敌人 | 极难（仅 2 个自定义 E 出生点） |

### 7.4 难度配置（来自 `settings.LEVEL_DIFFICULTY`）

| 关 | enemy_count | max_on_screen | enemy_speed | spawn_interval |
|----|-------------|---------------|-------------|----------------|
| 1 | 15 | 3 | 72 | 2.0s |
| 2 | 15 | 3 | 72 | 2.0s |
| 3 | 15 | 3 | 72 | 2.0s |
| 4 | 18 | 4 | 78 | 1.8s |
| 5 | 20 | 4 | 84 | 1.5s |
| 6 | 25 | 5 | 90 | 1.2s |

### 7.5 公共函数

```python
get_level(index) -> list[str]              # 循环取关（index % len）
get_level_difficulty(index) -> dict        # 循环取配置
get_total_levels() -> int                  # 6
```
