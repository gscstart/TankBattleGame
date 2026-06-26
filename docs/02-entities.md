# 02 · 实体参考（entities/）

> 所有在地图上"会动或会被打"的东西都叫实体。本章描述每个实体的字段、状态机、关键方法。

## 1. 继承关系

```
                Tank (基类)
                ├─ PlayerTank
                └─ EnemyTank

                Bullet (独立)
                PowerUp (独立)
                MuzzleFlash / Explosion / Particle (特效，独立)
                TileBase (在 world/tile.py，本质是瓦片)
```

**关键约定**：所有实体都用 `pygame.Rect` 表示碰撞盒；位置字段是 `self.rect.x/y` 而非 `self.x/y`。

---

## 2. `Tank` — 坦克基类

**文件**：`entities/tank.py`

### 2.1 类常量

| 常量 | 值 | 用途 |
|------|----|------|
| `BASE_SPEED` | 96 px/s | 默认速度（子类覆盖） |
| `SNAP_RATE` | 900 px/s | 软吸附速度，越大越快对齐 |
| `TREAD_PERIOD` | 6 px | 履带纹路周期 |
| `FIRE_COOLDOWN` | 0.5 s | 默认开火冷却（子类可覆盖） |

### 2.2 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `rect` | `pygame.Rect` | 碰撞盒，48×48 |
| `dir` | `(dx, dy)` | 当前朝向，值在 `settings.Dir` 中 |
| `color` / `dark_color` | `tuple` | 车身主色 / 履带阴影色 |
| `speed` | `float` | 实际速度（BASE_SPEED × tier 系数） |
| `cooldown` | `float` | 开火冷却计时，<= 0 才能开火 |
| `dead` | `bool` | 死亡标记（被击中后 True） |
| `flashing_time` | `float` | 剩余无敌闪烁时间（> 0 时画半透明白膜） |
| `snap_axis` | `None / 'x' / 'y'` | 软吸附进行中？ |
| `snap_target` | `int` | 吸附终点像素 |
| `tread_phase` | `float` | 履带动画相位（0-24 循环） |
| `is_player` | `bool` | 玩家标记（`PlayerTank` 在 `__init__` 末尾设 True） |
| `hit_flash_time` | `float` | 被击中闪红剩余时间（叠红膜） |
| `killed_by_powerup` | `bool` | 被道具（如 grenade）杀死时设 True，**避免双重计分** |

### 2.3 关键方法

#### `try_move(dt, dx, dy, tilemap, other_tanks) -> bool`
- **作用**：尝试移动 (dx, dy) 像素
- **流程**：先 x 后 y，每轴单独做碰撞回退
- **返回**：是否真的移动了（`True` 时 `tread_phase` 累计）
- **碰撞顺序**：地图边界 → `tilemap.rect_collides_solid` → 其他坦克

#### `try_change_direction(new_dir, tilemap, other_tanks) -> bool`
- **作用**：尝试换方向（含软吸附）
- **关键点**：
  - 垂直移动时吸附 x 轴；水平移动时吸附 y 轴
  - 试探吸附目标是否合法，带 ±2/±4/±6 微调容差
  - 失败时回退原位，返回 False
- **返回**：是否成功换向

#### `update_snap(dt)`
- 每帧调用，把吸附轴位置向 `snap_target` 推进 SNAP_RATE 像素
- 到达后 `snap_axis = None`

#### `can_move_now() -> bool`
- **守护**：吸附进行中、且吸附轴与移动方向相同 → 阻止移动
- 防止"边吸附边开火导致穿墙"

#### `shoot(bullets, effects=None) -> Bullet | None`
- 在炮口位置（边缘外 4 像素）生成 `Bullet`
- **玩家身份判断**：用 `self.is_player`，**不再用 `__import__`**（已重构）
- **能破钢墙**：`getattr(self, "breaks_steel", False)` 或玩家 `upgrade_level >= 2`
- **创建 `MuzzleFlash` 特效**（如果传了 effects）
- **播放 `fire` 音效**
- 返回创建的子弹

#### `on_hit(bullet)`
- 默认行为：`hit_flash_time = 0.3` → `dead = True`
- 玩家类有 `flashing_time > 0` 守护（无敌不被打死）
- 敌人类有 `born_invuln` 守护（出生 1 秒无敌）

#### `update_cooldown(dt)`
- 每帧调用，倒计 `cooldown` / `flashing_time` / `hit_flash_time`

#### `draw(surface)`
- 调用 `utils.draw.draw_tank()`，传入当前 `flashing` 和 `hit_flash` 标志

---

## 3. `PlayerTank` — 玩家

**文件**：`entities/player.py`

继承 `Tank`，**重写/扩展**：

### 3.1 独有字段

| 字段 | 默认 | 说明 |
|------|------|------|
| `keys` | dict 4 项 | 4 个方向键 + fire 的当前按下状态 |
| `key_press_time` | dict 4 项 | 各方向键最后按下时间（`self._time`） |
| `_time` | 0.0 | 玩家本地累计时间（用于 `key_press_time` 比较） |
| `slide_timer` | 0.0 | 惯性滑行剩余时间（SLIDE_DURATION=0.1s） |
| `slide_dir` | self.dir | 滑行期间使用的方向 |
| `upgrade_level` | 0 | 0=基础，1=子弹加速，2=可破钢墙 |
| `invincible` | 0.0 | 剩余无敌时间（helmet 道具给 10s） |
| `frozen_enemies_timer` | 0.0 | 敌人冻结剩余时间（clock 道具给 8s） |

### 3.2 `handle_event(event)`
- 处理 KEYDOWN / KEYUP
- 方向键按下时记录 `key_press_time[name] = self._time`
- fire 键按下设 `keys["fire"] = True`

### 3.3 `_active_direction() -> (dx, dy) | None`
- **核心**：返回最近按下的方向键对应的方向
- **解决 W+D 同时按下的方向死锁**

### 3.4 `update(dt, tilemap, other_tanks, bullets, effects=None)`

主循环（按顺序）：
1. `_time += dt`、倒计各种 timer
2. `update_snap(dt)` — 推进软吸附
3. 取 `active = _active_direction()`
4. **有方向键按下**：
   - `try_change_direction(active, ...)` → 成功则 `slide_dir = self.dir`
   - `slide_timer = SLIDE_DURATION`
   - `try_move(dx*speed*dt, dy*speed*dt, ...)`
5. **无方向键按下**：
   - `slide_timer -= dt`
   - `> 0` → 继续按 `slide_dir` 滑行
   - `= 0` → 重新吸附到格点（方便后续变向）
6. **fire 按下且能开火**：`shoot()` 后清 `keys["fire"]`（只触发一次）

---

## 4. `EnemyTank` — AI 敌人

**文件**：`entities/enemy.py`

继承 `Tank`。

### 4.1 Tier 系统（关键）

| Tier | 颜色 | 速度 | 破钢墙 | 开火冷却 |
|------|------|------|--------|----------|
| 0 | 灰 `(180,180,180)` | 100% | ❌ | 0.8~1.6s |
| 1 | 红 `(220,110,110)` | 100% | ❌ | 0.6~1.2s（更准） |
| 2 | 绿 `(110,200,110)` | 125% | ✅ | 0.8~1.6s |

**配置表**（修改 tier 行为改这里）：
```python
TIER_FIRE_COOLDOWN = {0: (0.8, 1.6), 1: (0.6, 1.2), 2: (0.8, 1.6)}
TIER_SPEED_MULT    = {0: 1.0, 1: 1.0, 2: 1.25}
TIER_BREAKS_STEEL  = {0: False, 1: False, 2: True}
```

**生成时的 tier 循环**：`tier = (self.enemies_killed) % 3`（在 `Level._spawn_enemy` 中）

### 4.2 独有字段

| 字段 | 默认 | 说明 |
|------|------|------|
| `tier` | 参数 | 0/1/2 |
| `breaks_steel` | 按 tier | 子弹能否破钢墙 |
| `_next_dir_time` | 0 | 下次选方向的倒计时 |
| `_next_fire_time` | random 0.5~1.0 | 下次开火倒计时 |
| `born_invuln` | 1.0 | 出生后 1 秒无敌（闪白） |
| `_last_dir` | DOWN | 上次方向 |
| `frozen` | False | 被 clock 道具冻结（不动、不开火） |

### 4.3 `update(dt, tilemap, other_tanks, bullets, player, effects, base_pos, target_priority)`

主循环（按顺序）：
1. `update_cooldown(dt)`
2. **如果 `frozen`**：return（不动、不开火）
3. `update_snap(dt)` + 倒计 `born_invuln`（闪白）
4. 倒计 `_next_dir_time` / `_next_fire_time`
5. `target_dir = _choose_target_dir(...)` — 决定"瞄准方向"
6. **如果 `_next_dir_time <= 0`**：
   - 55% 概率选 `target_dir`（瞄准），45% 随机
   - 失败 3 次随机重试
   - 间隔 0.8~1.6s
7. `try_move(...)` — 撞墙时强制下次立即选方向
8. **如果 `_next_fire_time <= 0`**：`shoot()`，按 tier 选下次冷却

### 4.4 `_choose_target_dir(tilemap, player, base_pos, priority) -> (dx, dy) | None`

**目标优先级逻辑**：
- `priority == "base"`：基地优先（如果存在）
- `priority == "player"`：玩家优先
- 两个目标都加入候选列表，**先成功瞄准的返回**

每个目标用 `_dir_to_target()` 检查直线视线 → `line_of_sight()` 无墙阻挡时返回方向。

### 4.5 `on_hit(bullet)`
- `born_invuln > 0` 时忽略
- 否则 `hit_flash_time = 0.3`，调用 `super().on_hit(bullet)` 设 `dead=True`

---

## 5. `Bullet` — 子弹

**文件**：`entities/bullet.py`

### 5.1 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `direction` | `(dx, dy)` | 飞行方向 |
| `owner` | `"player" / "enemy"` | 谁发射的（用于音效、计分归属） |
| `rect` | `pygame.Rect` | 10×10 碰撞盒 |
| `dead` | `bool` | 是否已销毁 |
| `can_break_steel` | `bool` | 能否破钢墙（默认 False，tier 2 敌人 / 玩家 2 级时 True） |
| `trail` | `[(x, y), ...]` | 拖尾位置（最多 6 帧） |

### 5.2 `update(dt, tilemap, bullets, tanks, base_callback, effects=None)`

**移动策略**：用**子步**（`steps = max(1, max(|dx|,|dy|)/2) + 1`）避免高速穿透薄墙。

每步检查顺序（命中即返回）：
1. 地图外 → 小爆炸 + dead
2. 砖块子格 → `tile.on_bullet_hit(self, sub)` + hit 音 + 爆炸 + dead
3. 钢墙或基地：
   - 钢墙 + `can_break_steel` → 替换为 `TileEmpty()` + dead
   - 钢墙普通 → `tile.on_bullet_hit()` + 爆炸 + dead
   - 基地 → `base_callback(tile)` + 大爆炸 + dead
4. 其他子弹 → 双方 dead
5. 坦克 → `tank.on_hit(self)` + 大爆炸 + dead

### 5.3 `draw(surface)`
- 先画拖尾（6 个渐变小圆）
- 再画主体（圆 + 方向小尾迹）

### 5.4 `_spawn_explosion(effects, scale, big=False)`
- 在子弹中心 + 飞行方向偏移 4 像素处创建 `Explosion`

---

## 6. `PowerUp` — 道具

**文件**：`entities/powerup.py`

### 6.1 6 种类型

| type | 效果 | 持续 | 颜色 | 图标 |
|------|------|------|------|------|
| `star` | 升级（最多 2 级） | 永久（除非死亡） | `(255,220,100)` 金 | 5 角星 |
| `grenade` | 全屏敌人立即死亡 + 得分 | 瞬间 | `(240,100,80)` 红 | 圆+顶 |
| `helmet` | 玩家无敌 | 10s | `(140,200,255)` 蓝 | 倒 U |
| `clock` | 敌人冻结 | 8s | `(140,220,180)` 绿 | 钟 |
| `shovel` | 基地周围 8 格变钢墙 | 15s | `(220,180,100)` 黄 | 铲 |
| `tank` | 玩家 +1 命 | 永久 | `(200,100,220)` 紫 | 坦克 |

**掉落规则**：敌人被击杀时 25% 概率（`Level.update()`）
**生命周期**：存活 12s 后自动消失

### 6.2 字段

| 字段 | 说明 |
|------|------|
| `type` | 类型字符串 |
| `color` | 主色（从 `TYPE_COLORS` 查） |
| `rect` | 48×48 碰撞盒 |
| `spawn_time` | `time.time()` |
| `dead` | 标记 |

### 6.3 关键方法

- `update(dt)`：超过 12s 设 `dead=True`
- `draw(surface)`：每秒闪 4 次（`int(elapsed*4) % 2 == 0` 时绘制）
- `_draw_icon(...)`：按 type 画不同图形
- `spawn_random_powerup(x, y)`（模块级函数）：随机选类型创建

**道具分发逻辑**在 `Level._apply_powerup(pu)`。

### 6.4 ⚠️ 已修复 Bug

`powerup.py` 末尾的 `import math` 写在了模块最下面（不在 import 区域）—— 风格小瑕疵，不影响功能。如果重排请提到文件顶部。

---

## 7. `MuzzleFlash` / `Explosion` / `Particle` — 特效

**文件**：`entities/effects.py`

### 7.1 `MuzzleFlash`

**生命周期**：`life=0.10s`，每帧 `update(dt)` 减，超时 `dead=True`。

**绘制**：4 层叠加（中心白圆 + 主色圆 + 橙色光晕 + 沿方向的火光粒子）。

### 7.2 `Particle`

**生命周期**：`life` 由构造传入（0.35~0.55s）。
**物理**：`x += vx*dt`、阻力 `vx *= 0.92`、轻微重力 `vy += 60*dt`。
**绘制**：半径随 `t = life/max_life` 衰减。

### 7.3 `Explosion`

**结构**：1 个 `flash_life=0.08s` 的中心闪光 + 10/14 颗粒子（`big=True` 时 14 颗）。
**结束条件**：`flash_life <= 0` 且所有粒子 `dead`。

---

## 8. `TileBase` — 基地

**文件**：`entities/base.py`（仅重导出 `TileBase`）
**真正定义**：`world/tile.py`

`TileBase.destroyed: bool`，被子弹命中后设为 True。`Level.update()` 每帧检查 `tilemap.base_tile.destroyed` → 设 `failed=True`。

**绘制**（`utils/draw._draw_base`）：未毁 = 房子 + 鹰头 + 眼睛 + 嘴；已毁 = 残骸 + 黑色 × 斜线。
