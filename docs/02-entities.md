# 02 · 实体参考（entities/）

> 所有在地图上"会动或会被打"的东西都叫实体。本章描述每个实体的字段、状态机、关键方法。

## 1. 继承关系

```
                Tank (基类)
                ├─ PlayerTank
                ├─ EnemyTank
                │   └─ SuicideEnemy / StealthEnemy / ArmorEnemy
                │      / RocketEnemy / BounceEnemy  (C3 5 种特殊敌人)
                └─ BossTank  (C2)

                Bullet (独立)
                PowerUp (独立, 9 种)
                Mine (B4 独立)
                MuzzleFlash / Explosion / Particle (特效, 独立)
                TileBase (在 world/tile.py, 本质是瓦片)
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
| `killed_by_powerup` | `bool` | 被道具（如 grenade / 自爆）杀死时设 True，**避免双重计分** |
| `hp` | `int` | **C2 加**: 多血坦克（默认 1，BOSS=10，装甲=3） |
| `breaks_steel` | `bool` | 子弹能否破钢墙（tier 2 敌人 / 玩家 2 级 / BOSS） |

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

#### `on_hit(bullet)` — **C2 重构：减血路径**
- 玩家有 `flashing_time > 0` 守护（无敌不被打死）
- 敌人类有 `born_invuln` 守护（出生 1 秒无敌）
- 否则 `hit_flash_time = 0.3` → `hp -= 1` → `hp <= 0` 时 `dead = True`
- BOSS/装甲通过 `hp > 1` 实现多血

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
| `keys` | dict 5 项 | 4 方向 + fire 的当前按下状态（C6 回放时每帧覆盖）|
| `key_press_time` | dict 4 项 | 各方向键最后按下时间（`self._time`） |
| `_time` | 0.0 | 玩家本地累计时间（用于 `key_press_time` 比较） |
| `slide_timer` | 0.0 | 惯性滑行剩余时间（SLIDE_DURATION=0.1s） |
| `slide_dir` | self.dir | 滑行期间使用的方向 |
| `upgrade_level` | 0 | 0=基础，1=子弹加速，2=可破钢墙 |
| `invincible` | 0.0 | 剩余无敌时间（helmet 道具给 10s） |
| `frozen_enemies_timer` | 0.0 | 敌人冻结剩余时间（clock 道具给 8s） |
| `lives` | PLAYER_LIVES (3) | **C1**: 每玩家独立命数 |
| `player_id` | 1/2 | **C1**: HUD 显示用 |
| `input_map` | InputMap | **C1**: P1_INPUT / P2_INPUT |
| `magnet_timer` | 0.0 | **B4**: 磁铁吸引持续 8s |
| `laser_timer` | 0.0 | **B4**: 激光穿透持续 10s |
| `on_ice` | False | **B5**: 当前是否在冰面 TileIce 上 |

### 3.2 `handle_event(event)`
- 处理 KEYDOWN / KEYUP
- 方向键按下时记录 `key_press_time[name] = self._time`
- fire 键按下设 `keys["fire"] = True`
- **C1**: `is_mine(key)` 过滤，多玩家时只响应自己的键

### 3.3 `_active_direction() -> (dx, dy) | None`
- **核心**：返回最近按下的方向键对应的方向
- **解决 W+D 同时按下的方向死锁**

### 3.4 `update(dt, tilemap, other_tanks, bullets, effects=None)`

主循环（按顺序）：
1. `_time += dt`、倒计各种 timer（cooldown / magnet / laser / invincible / frozen）
2. **B5 冰面检测**（用中心点查 tilemap 瓦片类型）→ `on_ice` 标记
3. `update_snap(dt)`（**B5 冰面时跳过**） — 推进软吸附
4. 取 `active = _active_direction()`
5. **有方向键按下**：
   - `try_change_direction(active, ...)` → 成功则 `slide_dir = self.dir`
   - `slide_timer = SLIDE_DURATION`
   - `try_move(dx*speed*dt, dy*speed*dt, ...)`
6. **无方向键按下**：
   - **B5 冰面**: `slide_timer` 不衰减（无摩擦）
   - 普通: `slide_timer -= dt`
   - `> 0` → 继续按 `slide_dir` 滑行
   - `= 0` → 重新吸附到格点（方便后续变向）
7. **fire 按下且能开火**：`shoot()` 后清 `keys["fire"]`（只触发一次）

**B5 关键设计**：冰面 (`TileIce`) 上 `on_ice=True`，`update_snap` 跳过，惯性滑行 `slide_timer` 不衰减 → 持续滑行无摩擦。

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
| `is_powerup_carrier` | bool | **B1 红闪敌人**: 100% 掉道具，颜色鲜红，闪白 |

### 4.3 `update(dt, tilemap, other_tanks, bullets, player, effects, base_pos, target_priority)`

**重要：第 5 个位置参数是 `player`（不是 effects）** — 这是 C2 BOSS review 修正的关键。

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
- 否则 `hit_flash_time = 0.3`，调用 `super().on_hit(bullet)` → `hp -= 1` → `hp <= 0` 时 `dead=True`

---

## 5. `BossTank` — BOSS 坦克 (C2)

**文件**：`entities/boss.py`

继承 `Tank`，**简化 AI**（路线图 §3.1：不分多阶段、单一 BOSS）。

### 5.1 独有字段

| 字段 | 值 | 说明 |
|------|----|------|
| `hp` | BOSS_HP (10) | 多血 |
| `breaks_steel` | True | 子弹破钢墙 |
| `flashing_time` | 0.0 | 出生不闪白（一直显眼） |
| `is_powerup_carrier` | False | 跟 EnemyTank 一致（无道具掉） |
| `FIRE_COOLDOWN` | BOSS_FIRE_COOLDOWN (1.5s) | 覆写基类 |

### 5.2 简化 AI

**不调用 `_choose_target_dir`**（不像 EnemyTank 智能瞄准）：

```python
def update(self, dt, tilemap, other_tanks, bullets, player,
           effects=None, base_pos=None, target_priority="player"):
    if self.dead: return
    self.update_cooldown(dt)
    if self.frozen: return
    self.update_snap(dt)
    # 沿 dir 直线移动
    moved = self.try_move(dt, ...)
    if not moved:
        # 撞墙/坦克: 180° 反弹
        self.dir = (-self.dir[0], -self.dir[1])
    # 射击
    if self.cooldown <= 0 and self.can_shoot():
        self.shoot(bullets, effects=effects)
```

**签名约定**：第 5 个位置参数是 `player`（**跟 EnemyTank 对齐**），让 `Level.update` 通用调用 `e.update(..., ai_target, effects=self.effects, ...)` 时不会参数错位（C2 review 修过的真 bug）。

### 5.3 关卡生成

由 `Level.__init__` 在 `mode == "boss"` 时手动 spawn 在 `(8, 7)` 中心位置，**不通过 K 字符走 tile layout**。`Level.update` 末尾检测 BOSS 全死 → `LEVEL_COMPLETED`。

---

## 6. C3 特殊敌人 5 种

**文件**：`entities/special.py`

每个都是 `EnemyTank` 子类，**只覆写差异点**（karpathy Simplicity）。`Level._spawn_enemy` 在 campaign 模式 `random.random() < SPECIAL_ENEMY_CHANCE` (15%) 时生成。

### 6.1 `SuicideEnemy` 自爆者

- **颜色**：`SPECIAL_COLORS["suicide"]` (255, 100, 0) 橙
- **行为**：距玩家 < 80px 触发自爆
  - `self.dead = True` + `killed_by_powerup = True`（**避免双重计分**）
  - 范围内 64px 敌人 `dead = True`
  - 大 Explosion + 音效
  - publish `ENTITY_KILLED` `owner=powerup`（表达"被自爆者波及"）
- **C3 review 修过的真 bug**：`_detonate` 内部 publish + level 末尾"清理死亡"块也 publish → 重复加分 100 + 重复发事件。设 `killed_by_powerup=True` 让 level 跳过。

### 6.2 `StealthEnemy` 隐形者

- **颜色**：`SPECIAL_COLORS["stealth"]` (150, 150, 220) 浅蓝紫
- **行为**：周期 2s，0.3s 显形 + 1.7s 隐行
  - `stealth_phase` 初始随机（避免一群同步显形）
  - `is_visible = (stealth_phase % STEALTH_CYCLE) < (STEALTH_CYCLE * STEALTH_VISIBLE_FRAC)`
  - `update` 推 `stealth_phase += dt`（不 mod，避免精度漂移）
  - `draw` 覆写：隐行期直接 `return`（不画）
- **被子弹仍正常受击**（不挡子弹）

### 6.3 `ArmorEnemy` 装甲者

- **颜色**：`SPECIAL_COLORS["armor"]` (80, 80, 80) 深灰
- **行为**：`hp = ARMOR_HP` (3)
- 其他行为与普通敌人一致

### 6.4 `RocketEnemy` 火箭者

- **颜色**：`SPECIAL_COLORS["rocket"]` (220, 200, 60) 亮黄
- **行为**：`shoot` 覆写，让子弹 `speed_multiplier=2.0` + `can_break_steel=True`

### 6.5 `BounceEnemy` 弹跳者

- **颜色**：`SPECIAL_COLORS["bounce"]` (200, 80, 200) 亮紫
- **行为**：`shoot` 覆写让子弹 `bounces_left = BOUNCE_COUNT` (1)，撞墙/砖块/钢墙反弹一次（但基地不反弹）

### 6.6 工厂

```python
SPECIAL_ENEMY_CLASSES = [SuicideEnemy, StealthEnemy, ArmorEnemy,
                         RocketEnemy, BounceEnemy]
```

---

## 7. `Bullet` — 子弹

**文件**：`entities/bullet.py`

### 7.1 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `direction` | `(dx, dy)` | 飞行方向 |
| `owner` | `"player" / "enemy"` | 谁发射的（用于音效、计分归属） |
| `rect` | `pygame.Rect` | 8×8 碰撞盒 |
| `dead` | `bool` | 是否已销毁 |
| `can_break_steel` | `bool` | 能否破钢墙 |
| `is_laser` | `bool` | **B4** 激光模式 - 穿透敌人不消失 |
| `bounces_left` | `int` | **C3** 弹跳剩余次数（撞墙/砖块/钢墙） |
| `speed_multiplier` | `float` | **C3** 速度倍率（火箭 2.0） |
| `trail` | `[(x, y), ...]` | 拖尾位置（最多 6 帧） |

### 7.2 `update(dt, tilemap, bullets, tanks, base_callback, effects=None)`

**移动策略**：用**子步**（`steps = max(1, max(|dx|,|dy|)/2) + 1`）避免高速穿透薄墙。
**速度**：`speed = BULLET_SPEED * speed_multiplier`（C3 火箭加速）

每步检查顺序（命中即返回）：
1. **C3 弹跳**: 地图外 + `bounces_left > 0` → 反向 + 扣减 + 修正位置
2. **C3 弹跳**: 砖块子格 + `bounces_left > 0` → 反向
3. **C3 弹跳**: 钢墙/非基地 + `bounces_left > 0` → 反向
4. 地图外 → 小爆炸 + dead
5. 砖块子格 → `tile.on_bullet_hit(self, sub)` + hit 音 + 爆炸 + dead
6. 钢墙或基地：
   - 钢墙 + `can_break_steel` → 替换为 `TileEmpty()` + dead
   - 钢墙普通 → `tile.on_bullet_hit()` + 爆炸 + dead
   - 基地 → `base_callback(tile)` + 大爆炸 + dead
7. 其他子弹 → 双方 dead
8. 坦克 → `tank.on_hit(self)` + 大爆炸 + dead（**B4 激光** 不 dead，继续飞行）

### 7.3 `_bounce()` (C3 弹跳内部方法)
- 扣减 `bounces_left`
- 单轴方向取反
- `clamp_ip` 修正位置到地图内

### 7.4 `draw(surface)`
- 先画拖尾（6 个渐变小圆）
- 再画主体（圆 + 方向小尾迹）

### 7.5 `_spawn_explosion(effects, scale, big=False)`
- 在子弹中心 + 飞行方向偏移 4 像素处创建 `Explosion`

---

## 8. `PowerUp` — 道具 (9 种)

**文件**：`entities/powerup.py`

### 8.1 类型

| type | 效果 | 持续 | 颜色 | 来源阶段 |
|------|------|------|------|----------|
| `star` | 升级（最多 2 级） | 永久（除非死亡） | `(255,220,100)` 金 | A |
| `grenade` | 全屏敌人立即死亡 + 得分 | 瞬间 | `(240,100,80)` 红 | A |
| `helmet` | 玩家无敌 | 10s | `(140,200,255)` 蓝 | A |
| `clock` | 敌人冻结 | 8s | `(140,220,180)` 绿 | A |
| `shovel` | 基地周围 8 格变钢墙 | 15s | `(220,180,100)` 黄 | A |
| `tank` | 玩家 +1 命 | 永久 | `(200,100,220)` 紫 | A |
| `magnet` | 吸引所有道具 | 8s | — | **B4** |
| `laser` | 子弹穿透敌人 | 10s | — | **B4** |
| `mine` | 放 3 颗地雷 | 永久 | — | **B4** |

**掉落规则**：敌人被击杀时 25% 概率（`Level.update()`），红闪敌人 100%。
**生命周期**：存活 12s 后自动消失

### 8.2 字段

| 字段 | 说明 |
|------|------|
| `type` | 类型字符串 |
| `color` | 主色 |
| `rect` | 48×48 碰撞盒 |
| `spawn_time` | `time.time()` |
| `dead` | 标记 |

### 8.3 关键方法

- `update(dt, magnet_target=None)`: **B4 magnet 吸引**，超过 12s 设 `dead=True`
- `draw(surface)`: 每秒闪 4 次
- `_draw_icon(...)`: 按 type 画不同图形
- `spawn_random_powerup(x, y)`（模块级函数）：随机选类型创建

**道具分发逻辑**在 `Level._apply_powerup(pu)`。

---

## 9. `Mine` — 地雷 (B4)

**文件**：`entities/mine.py`

### 9.1 行为

- 玩家拾取 `mine` 道具时在玩家前/中/后放 3 颗
- 静止不动，存活 `LIFETIME` 秒
- 敌人（含特殊敌人）碰触时爆炸：100px AOE 范围所有敌人死
- 友军（玩家/玩家子弹）不受影响

### 9.2 字段

| 字段 | 说明 |
|------|------|
| `rect` | 36×36 碰撞盒 |
| `lifetime` | 存活时间 |
| `dead` | 标记 |

### 9.3 `update(dt, enemies, effects, events) -> int`
- 倒计 lifetime
- 检测每个 enemy.rect 是否与 mine.rect 重叠
- 命中：enemy.dead=True + publish `ENTITY_KILLED` + 100px AOE 内其他敌人死
- 返回击杀数（给 level 加分用）

---

## 10. `MuzzleFlash` / `Explosion` / `Particle` — 特效

**文件**：`entities/effects.py`

### 10.1 `MuzzleFlash`
- **生命周期**：`life=0.10s`，每帧 `update(dt)` 减
- **绘制**：4 层叠加（中心白圆 + 主色圆 + 橙色光晕 + 沿方向的火光粒子）

### 10.2 `Particle`
- **生命周期**：`life` 由构造传入（0.35~0.55s）
- **物理**：`x += vx*dt`、阻力 `vx *= 0.92`、轻微重力 `vy += 60*dt`
- **绘制**：半径随 `t = life/max_life` 衰减

### 10.3 `Explosion`
- **结构**：1 个 `flash_life=0.08s` 的中心闪光 + 10/14 颗粒子（`big=True` 时 14 颗）
- **结束条件**：`flash_life <= 0` 且所有粒子 `dead`

---

## 11. `TileBase` — 基地

**文件**：`entities/base.py`（仅重导出 `TileBase`）
**真正定义**：`world/tile.py`

`TileBase.destroyed: bool`，被子弹命中后设为 True。`Level.update()` 每帧检查 `tilemap.base_tile.destroyed` → 设 `failed=True`。

---

## 12. 实体关系与事件流

| 实体 | 谁调用 update | 谁发 ENTITY_KILLED | 备注 |
|------|---------------|---------------------|------|
| PlayerTank | Level | 死亡时 (kind=player) | C1 多玩家 |
| EnemyTank | Level | 玩家击杀 (kind=enemy, owner=player) | |
| SpecialEnemy | Level | 同上 | C3 5 种 |
| BossTank | Level | 同上 + **is_boss=True** | C2 |
| Bullet | Level | 命中时 publish (走 Tank.on_hit) | |
| Mine | Level | 命中时 | B4, 给 level 加分 |
| PowerUp | Level | 拾取时 (POWERUP_PICKED) | |
| Effect | Level | — | 自动 dead |
| TileBase | 子弹命中 | — | failed=True |

**所有事件走 `utils/events.py` 事件总线**（`subscribe` / `publish`），让成就 / 排行榜 / BGM 各自订阅。
