# 03 · 游戏主循环与世界（game/ + world/）

> 本章讲"游戏的脚手架"：状态机、关卡运行、HUD、菜单、地图、关卡数据。
> 涉及文件：`game/game.py`、`game/level.py`、`game/hud.py`、`game/menu.py`、`world/tilemap.py`、`world/tile.py`、`world/levels.py`、`utils/achievements.py`、`utils/replay.py`、`utils/music.py`。

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
| `level_index` | `int` | 当前关卡（0-14，15 关） |
| `score` | `int` | 累计分数 |
| `lives` | `int` | 玩家生命 |
| `num_players` | `int` | **C1** 1 或 2（影响 `_spawn_player` 几次） |
| `events_buffer` | `list` | 预留（目前 `Game.handle_events` 直接转发给 `level.players`） |
| `menu_t` | `float` | 菜单时间（用于闪烁） |
| `menu_view` | `str` | **B2/C5/C6** `'main' / 'highscores' / 'achievements' / 'replays'` |
| `highscore_rank` | `int` | **B2** 通关后上榜的排名（-1 未上榜） |
| `achievements` | `Manager` | **C5** 成就管理器（订阅 events） |
| `replay_mode` | `bool` | **C6** True 表示当前在重放（而非真实游玩） |
| `replay_recorder` | `Recorder` | **C6** 录 player.keys 序列 |
| `replay_player` | `Player \| None` | **C6** 重放时从 JSON 加载 |
| `replay_frame_idx` | `int` | **C6** 当前播放到第几帧 |
| `replay_list` | `list` | **C6** 菜单回放列表缓存 |
| `replay_selected_idx` | `int` | **C6** 菜单选中索引 |
| `music` | `MusicManager` | **F20** 背景音乐管理器 |
| `_last_bgm_state` | `str` | **F20** 上一帧的 state（避免每帧切 track） |

### 1.2 状态机切换点

| 触发 | 新状态 | 位置 |
|------|--------|------|
| 菜单按 Enter/Space | PLAYING | `handle_events` |
| 菜单 K_H / K_A / K_R | MENU (子视图切换) | `handle_events` |
| 菜单 K_M | (开关 BGM) | `handle_events` |
| 菜单 + / - | (调音量) | `handle_events` |
| 菜单 K_L | (切语言 zh ↔ en) | `handle_events` |
| PLAYING 按 P | PAUSED | `handle_events` + `music.pause()` |
| PAUSED 按 P | PLAYING | `handle_events` + `music.resume()` |
| `level.completed == True` | LEVEL_COMPLETE | `update` + `_stop_recording` |
| `level.failed == True` | GAME_OVER | `update` + `_stop_recording` |
| `state_time >= 2.0` (LEVEL_COMPLETE) | PLAYING 或 VICTORY | `update` + `next_level` |
| GAME_OVER 按 R | PLAYING (重开) | `handle_events` + `restart` |
| VICTORY | (保持 VICTORY 状态) | 等玩家按键 |

### 1.3 主菜单快捷键（MENU 状态 + menu_view='main'）

| 按键 | 作用 |
|------|------|
| Enter / Space | 开始游戏 |
| 1 | 1P 模式 |
| 2 | 2P 模式（C1） |
| **H** | 切到排行榜视图（B2） |
| **A** | 切到成就视图（C5） |
| **R** | 切到回放列表视图（C6） |
| **M** | 开关 BGM（F20） |
| **+ / -** | 调音量（F20） |
| **L** | 切换中英语言（B6） |
| ESC | 退出 |

### 1.4 `start_game()` / `restart()` / `start_replay()` / `next_level()`

- `start_game()`：重置 `level_index=0` / `score=0` / `lives=3`，创建新 `Level`，**启动 Recorder**（C6）
- `restart()`：直接调 `start_game()`（GAME_OVER 时按 R）
- `start_replay(replay_path)`：**C6** 加载 `Player`，设 `replay_mode=True`，启动新 Level（不录）
- `next_level()`：`level_index += 1`，如果 >= len(LEVELS) → VICTORY + `_record_highscore` + `achievements.save()`，否则 PLAYING
  - **关键**：保留 `score` 和 `lives`（跨关卡累加）

### 1.5 `update(dt)`

按状态分发。**C5 成就** 每帧 `on_level_tick(survival 计时)`，**C6 重放** 每帧覆盖 `player.keys`，**F20 BGM** state 变化时切 track。

PLAYING 状态：
```python
self.level.update(dt)
self.score = self.level.score
self.lives = self.level.lives
if self.level.completed:
    self.score += self.level_index * 1000   # 通关奖励
    self.state = State.LEVEL_COMPLETE
    self._stop_recording(result="completed")
elif self.level.failed:
    self.state = State.GAME_OVER
    self._stop_recording(result="failed")
    if self.level.mode == "survival":
        self._record_highscore()              # B3 生存模式失败也上榜
```

### 1.6 `draw()`

```python
if state == MENU:
    if menu_view == 'highscores':  draw_highscores(...)
    elif menu_view == 'achievements': draw_achievements(...)
    elif menu_view == 'replays':    draw_replay_list(...)
    else:                            draw_menu(...)
else:
    screen.fill(BLACK)
    draw_hud(lives, score, level_index, enemies_left, p2_lives)
    level.draw(screen)
    # 状态遮罩
    if PAUSED:            draw_pause(...)
    elif LEVEL_COMPLETE:  draw_level_complete(...)
    elif GAME_OVER:       draw_game_over(..., victory=False) + 上榜提示
    elif VICTORY:         draw_game_over(..., victory=True) + 上榜提示
```

### 1.7 `_record_highscore()` (B2/B3)

通关 / 生存失败时调 `highscores.add_score(score, level_no, "YOU")`，失败兜底（OSError 不抛）。

### 1.8 `_stop_recording()` (C6)

关卡结束/失败时调：
- replay_mode 时跳过
- 成功通关才存（失败不存）→ `Recorder.save(f"replay_L{n}_{score}_{ts}")`

---

## 2. `Level` — 关卡运行

**文件**：`game/level.py`

### 2.1 字段

| 字段 | 说明 |
|------|------|
| `index` | 关卡编号 0-14 |
| `lives` / `score` | 透传 Game |
| `config` | 当前关卡难度配置（从 `LEVEL_DIFFICULTY` 读） |
| `mode` | `'campaign' / 'survival' / 'boss'`（从 config 读） |
| `achievements` | **C5** Manager 引用（可选，不传则不处理） |
| `tilemap` | `TileMap` 实例 |
| `players` | **C1** 玩家列表（1-2 个 `PlayerTank`） |
| `bullets` | 子弹列表 |
| `enemies` | 敌人列表 |
| `effects` | 特效列表 |
| `powerups` | 道具列表 |
| `mines` | **B4** 地雷列表 |
| `enemies_killed` | 已杀数（用于计算下次 spawn 的 tier） |
| `enemies_to_spawn` | 待生成数（survival/boss 为 0/特殊值） |
| `_spawn_timer` / `_spawn_idx` | 生成计时 / 上次用的生成点 |
| `completed` / `failed` | 关卡完成 / 失败标志 |
| `screen_shake_time` | 震屏剩余时间 |
| `_shovel_backup` | shovel 道具激活前保存的瓦片 |
| `_shovel_timer` | shovel 剩余时间 |
| `_perm_dead` | **C1** 永久死亡玩家索引集合（避免重复发事件） |
| `_death_timer_p0/1` | **C1** 玩家死亡后等待重生的时间 |

### 2.2 模式（从 `LEVEL_DIFFICULTY[i].mode` 读）

| mode | enemy_count | 行为 | 关卡 |
|------|-------------|------|------|
| `campaign`（默认）| 15-35 | 杀够数 + 无存活敌人 → completed | 1-6, 9-12 |
| `survival` | inf | 永不自然完成，靠 `failed`（玩家全死）| 7, 13 |
| `boss` | 0 | **C2** BOSS 全死 → completed | 8, 14, 15 |

### 2.3 `_spawn_player(index, input_map)`

`index: 0=P1, 1=P2`。P2 在 P1 旁边 8 方向找不重叠位置。设 `flashing_time = RESPAWN_INVULN`。

### 2.4 `_spawn_enemy() -> EnemyTank | None`

**触发条件**：
- `enemies_to_spawn > 0`（survival 无限 / boss=0 / campaign 有限）
- 当前同屏敌人数 `< config["max_on_screen"]`

**C3 特殊敌人**（campaign 模式 15% 概率）：
```python
if self.mode == "campaign" and random.random() < SPECIAL_ENEMY_CHANCE:
    cls = random.choice(SPECIAL_ENEMY_CLASSES)
    enemy = cls(x, y, tier=tier, enemy_speed=..., is_powerup_carrier=False)
else:
    enemy = EnemyTank(x, y, tier=tier, enemy_speed=...)
```

**C2 BOSS 关**：跳过 spawn 计时（BOSS 在 `__init__` 已 spawn）。

### 2.5 `respawn_player(index)`

- `lives <= 0` → `_perm_dead.add(index)`，**不重复发 ENTITY_KILLED**
- 否则 `lives -= 1`（先减 1 再生成新 player）
- 创建新 `PlayerTank`，设 `flashing_time = RESPAWN_INVULN`
- **保留旧玩家的道具状态**：
  - `upgrade_level` 保留
  - `invincible` 减 1s（重生稍微惩罚）
  - `frozen_enemies_timer` 保留
  - `magnet_timer` / `laser_timer` 保留

### 2.6 `update(dt)` — 一帧内的全部逻辑

```python
def update(self, dt):
    if completed or failed: return

    # 0. C5 成就: 每帧 tick (survival 计时)
    if self.achievements:
        self.achievements.on_level_tick(dt, self.mode)

    # 1. 屏幕震屏计时
    if screen_shake_time > 0: screen_shake_time -= dt

    # 2. Shovel 倒计时
    if _shovel_timer > 0:
        _shovel_timer -= dt
        if _shovel_timer <= 0: _restore_shovel()

    # 3. 敌人生成 (boss 模式跳过)
    if self.mode != "boss":
        _spawn_timer -= dt
        if _spawn_timer <= 0:
            spawned = _spawn_enemy()
            if spawned is None and enemies_to_spawn > 0:
                _spawn_timer = 0.2  # 失败后快速重试
            else:
                _spawn_timer = config["spawn_interval"]

    # 4. 玩家 (C1 多玩家)
    other_tanks = [e for e in enemies if not e.dead]
    for idx, p in enumerate(players):
        if idx in _perm_dead: continue
        if not p.dead:
            p_others = [t for t in (other_tanks + players) if t is not p and not t.dead]
            p.update(dt, tilemap, p_others, bullets, effects=effects)
        else:
            p.update_cooldown(dt)
            # 死亡后等 1s 重生
            ...

    # 5. 所有玩家都死 + 基地未毁 → failed
    if _all_players_dead() and not failed:
        _fail(REASON_LIVES_ZERO)

    # 6. 玩家道具状态计时
    for p in players:
        if not p.dead:
            if p.invincible > 0: p.invincible -= dt
            if p.magnet_timer > 0: p.magnet_timer -= dt
            if p.laser_timer > 0: p.laser_timer -= dt
    if any frozen_enemies_timer > 0: for e in enemies: e.frozen = True
    else: for e in enemies: e.frozen = False

    # 7. 敌人更新（带瞄准 / C3 5 种 / C2 BOSS）
    base_pos = ...
    priority = "base" if random.random() < 0.4 else "player"
    for e in enemies:
        if e.dead: continue
        e.update(dt, tilemap, other_tanks, bullets, ai_target,
                 effects=effects, base_pos=base_pos, target_priority=priority)

    # 8. 子弹 (C3 bounces / speed_multiplier)
    for b in bullets:
        b.update(dt, tilemap, bullets, players+enemies, _on_base_hit, effects=effects)

    # 9. 清理死亡 + 计分 + 掉道具
    bullets = [b for b in bullets if not b.dead]
    newly_dead_enemies = [e for e in enemies if e.dead]
    if newly_dead_enemies:
        enemies = [e for e in enemies if not e.dead]
        for e in newly_dead_enemies:
            if not e.killed_by_powerup:  # C3 自爆/grenade 跳过
                score += 100
                enemies_killed += 1
                # C5: BOSS 死时 is_boss=True
                is_boss = isinstance(e, BossTank)
                events.publish(ENTITY_KILLED, kind="enemy", owner="player",
                               ..., is_boss=is_boss)
            # 25% 掉道具 (红闪 100%)
            if e.is_powerup_carrier or random.random() < 0.25:
                powerups.append(spawn_random_powerup(...))

    # 10. 道具 (B4 magnet 吸引)
    magnet_target = _get_magnet_target()
    for pu in powerups:
        pu.update(dt, magnet_target=magnet_target)
        for p in players:
            if not p.dead and pu.rect.colliderect(p.rect):
                _apply_powerup(pu, target_idx=players.index(p))
                events.publish(POWERUP_PICKED, type=pu.type, ...)
                pu.dead = True
                break

    # 11. B4 地雷 AOE
    mine_kills = 0
    for mine in mines:
        mine_kills += mine.update(dt, enemies, effects, events)
    mines = [m for m in mines if not m.dead]
    if mine_kills > 0:
        score += mine_kills * 100

    # 12. 特效清理

    # 13. 基地 destroyed? → failed
    if tilemap.base_tile and tilemap.base_tile.destroyed:
        if not failed:
            events.publish(BASE_DESTROYED)
            _fail(REASON_BASE_DESTROYED)

    # 14. 通关判断
    if not failed and not completed:
        if mode == "boss":
            boss_alive = any(isinstance(e, BossTank) and not e.dead for e in enemies)
            if not boss_alive:
                enemies = [e for e in enemies if not e.dead]
                events.publish(LEVEL_COMPLETED, score=score, level_index=index)
                completed = True
        elif enemies_to_spawn <= 0 and len(enemies) == 0:
            events.publish(LEVEL_COMPLETED, score=score, level_index=index)
            completed = True
```

### 2.7 `_apply_powerup(pu, target_idx)` — 道具效果分发

9 种道具对应 9 个分支：
- `star` / `grenade` / `helmet` / `clock` / `shovel` / `tank` （A 阶段）
- `magnet` → `p.magnet_timer = MAGNET_DURATION` (B4)
- `laser` → `p.laser_timer = LASER_DURATION` (B4)
- `mine` → `mines.extend(spawn_mines_around(p, count=MINE_COUNT))` (B4)

`target_idx` **C1**: 多玩家时按距离最近玩家分发效果。

### 2.8 `_get_magnet_target()` (B4)

返回磁铁激活中的最近存活玩家中心坐标，给 `PowerUp.update` 吸引。

### 2.9 `_activate_shovel(duration)` / `_restore_shovel()`

保存基地周围 8 格瓦片 → 替换为钢墙 → 倒计时 `duration` → 到时恢复。

---

## 3. `HUD` — 顶部状态条

**文件**：`game/hud.py`

绘制 P1/P2 命数 + 分数 + 关卡号 + 剩余敌人 + CJK 字体。

- `_find_cjk_font()`：Windows/macOS/Linux 按优先级找 CJK 字体
- `get_font(size, bold=False)`：项目内统一入口
- `draw_hud(surface, lives, score, level_index, enemies_left, p2_lives=None)`：画顶部 60px 高
  - **C1** 双人时画 P1/P2 两个命数

---

## 4. `Menu` — 菜单 / 结束画面

**文件**：`game/menu.py`

### 4.1 5 个 draw 函数

| 函数 | 用途 | 触发 |
|------|------|------|
| `draw_menu(surface, t, num_players)` | 主菜单（标题 + 控件提示 + 模式标记）| MENU 状态 |
| `draw_pause(surface)` | 暂停遮罩 | PAUSED 状态 |
| `draw_level_complete(surface, level, score, t)` | 通关画面 | LEVEL_COMPLETE |
| `draw_game_over(surface, score, victory, t)` | 结束画面（v 标志区分 VICTORY）| GAME_OVER / VICTORY |
| `draw_highscores(surface, scores, t)` | **B2** 排行榜 top 10 | menu_view='highscores' |
| `draw_achievements(surface, manager, t)` | **C5** 8 个成就 + 解锁状态 | menu_view='achievements' |
| `draw_replay_list(surface, replays, selected_idx, t)` | **C6** 回放列表 | menu_view='replays' |

### 4.2 国际化 (B6)

所有菜单文字通过 `utils/i18n.t("key")` 查表，i18n key 在 `i18n/zh.json` 和 `i18n/en.json`。K_L 切语言。

---

## 5. `TileMap` — 地图

**文件**：`world/tilemap.py`

### 5.1 字段

| 字段 | 说明 |
|------|------|
| `tiles` | `[[Tile, ...], ...]` 17×17 二维数组 |
| `player_spawn` | `(col, row)` 从 P 字符读 |
| `enemy_spawns` | `[(col, row), ...]` 从 E 字符读（前 3 个有效）|
| `base_tile` | 基地 `TileBase` 实例（从 X 字符读）|
| `base_pos` | 基地的 (col, row) |

### 5.2 `from_layout(layout: list[str]) -> TileMap`（classmethod）

解析 17 字符串布局：
- `.` → `TileEmpty`
- `B` → `TileBrick` (subtl=0b1111, 4 子格完整)
- `S` → `TileSteel`
- `G` → `TileGrass`
- `W` → `TileWater`
- `I` → `TileIce`（**B5** 冰面）
- `P` → 玩家出生点
- `E` → 敌人出生点
- `X` → 基地

### 5.3 碰撞方法

| 方法 | 返回 |
|------|------|
| `rect_collides_solid(rect) -> bool` | 砖/钢/水/基地（阻挡坦克）|
| `rect_hits_brick_subcell(rect) -> [(tile, c, r, sub)]` | 砖块子格（4 子格位掩码）|
| `rect_hits_steel_or_base(rect) -> [(tile, c, r)]` | 钢墙 + 基地 |

---

## 6. `Tile` — 7 种瓦片

**文件**：`world/tile.py`

| 类 | 阻挡坦克 | 阻挡子弹 | 可被破坏 | 备注 |
|----|:--------:|:--------:|:--------:|------|
| `TileEmpty` | ❌ | ❌ | — | 空地 |
| `TileBrick` | ✅ | ✅ | ✅（分 4 子格）| `subtl` 4 bit 位掩码 |
| `TileSteel` | ✅ | ✅ | 子弹 `can_break_steel=True` | |
| `TileGrass` | ❌ | ❌ | ❌ | 草丛，坦克可藏 |
| `TileWater` | ✅ | ❌ | ❌ | 水域 |
| `TileIce` | ❌ | ❌ | ❌ | **B5** 冰面，PlayerTank.on_ice=True → 持续滑行 |
| `TileBase` | ✅ | ✅ | ✅（游戏结束）| 基地 / 老鹰 |

---

## 7. `Levels` — 15 关数据

**文件**：`world/levels.py`

15 关列表 `LEVELS = [LEVEL_1, ..., LEVEL_15]`：
- 关 1-6：经典 campaign（6 关，A 阶段）
- 关 7：survival（B3）
- 关 8：BOSS（C2）
- **关 9-12**：campaign 新 4 关（C4 冰面/密室/钢墙/终极常规）
- **关 13**：survival II（C4）
- **关 14**：BOSS II（C4 钢墙保护）
- **关 15**：终极 BOSS（C4 草丛掩护）

**辅助函数**：
- `get_level(index)` → `LEVELS[index % len(LEVELS)]`
- `get_level_difficulty(index)` → `LEVEL_DIFFICULTY[index % len(...)]`
- `get_total_levels()` → `len(LEVELS)`

---

## 8. 集成：成就 / 回放 / 音乐

### 8.1 成就系统 (C5)

**Manager** 在 `Game.__init__` 创建，自动订阅 3 个事件（ENTITY_KILLED / POWERUP_PICKED / LEVEL_COMPLETED）。Level 通过 `on_level_start/tick` 推关卡级状态。

8 个成就：
- **一次性**（跨会话）：first_blood / boss_slayer / powerup_collector / collector / legend
- **关卡级**（本关重置）：sharpshooter / pacifist / survivor

未实现（需改 Tank.on_hit 加"玩家受伤"事件，超出当前 review 范围）：untouchable / iron_wall。

### 8.2 回放/录像 (C6)

**正常游玩**：
- `Game.start_game()` 启动 `Recorder`
- 每帧 `recorder.record_frame(player.keys)`
- 关卡结束 → `_stop_recording` → 成功通关时 `save(f"replay_L{n}_{score}_{ts}.json")`

**重放**：
- `Game.start_replay(path)` 设 `replay_mode=True`
- 每帧 `replay_player.get_keys_at(frame_idx)` 覆盖 `player.keys`
- `handle_events` 重放时禁用真实键盘（仅 ESC 退出）

**限制**：不录 random 种子，重放时敌人位置/行为有偏差（但玩家按键序列一致）。

### 8.3 背景音乐 (F20)

**MusicManager** 在 `Game.__init__` 创建，启动时程序合成 3 段 8-bit chiptune：
- `menu`：C 大调 4 音符上行（轻松）
- `game`：A 小调 8 音符（紧张）
- `victory`：C 大调 4 音符欢快（短，不循环）

**state → track 映射**（`track_for_state`）：
- `MENU` → `menu`
- `PLAYING` → `game`
- `VICTORY` → `victory`
- `PAUSED` / `LEVEL_COMPLETE` / `GAME_OVER` → `None`（不切，由 K_P pause 单独处理）

**K_P 暂停时**：`music.pause()`（保留 track），K_P 恢复时 `music.resume()`。
**K_M 开关 BGM**：`music.set_enabled(not music.is_enabled())`。
**+/- 音量**：`music.set_volume(volume + 0.1)` / `music.set_volume(volume - 0.1)`。

---

## 9. 持久化

| 模块 | 文件 | 格式 | 写策略 |
|------|------|------|--------|
| `utils.highscores` | `data/highscores.json` | `{"scores": [{name, score, level, date}, ...]}` | `_atomic_write` (临时文件 + rename) |
| `utils.achievements` | `data/achievements.json` | `{"unlocked": [...], "unlock_times": {...}, "powerup_total": int, "powerup_types": [...]}` | 同上 |
| `utils.replay` | `data/replays/<name>.json` | `{"name, date, level_index, num_players, frames: [{5 keys}], ...}` | 同上 |

**所有损坏 JSON 加载时 fallback 到空结构**，不抛异常。
**所有写失败**（`OSError`）被 try/except 吞掉，调用方记录。
