# 01 · 架构总览

> 一份让新接手的人 5 分钟理解整个项目骨架的文档。

## 1. 顶层架构

```
            ┌─────────────────────────────────────────────┐
            │              main.py (入口)                 │
            │           Game().run() 主循环                │
            └──────────────────────┬──────────────────────┘
                                   │
            ┌──────────────────────▼──────────────────────┐
            │           game/game.py (Game 控制器)         │
            │   状态机: MENU/PLAYING/PAUSED/              │
            │          LEVEL_COMPLETE/GAME_OVER/VICTORY    │
            │   每帧: handle_events → update → draw        │
            └──────────────────────┬──────────────────────┘
                                   │ self.level
            ┌──────────────────────▼──────────────────────┐
            │        game/level.py (Level 关卡)           │
            │   持有: tilemap, player, enemies, bullets,  │
            │         powerups, effects                    │
            │   负责: 敌人生成、道具、震屏、重生、计分    │
            └──────────────────────┬──────────────────────┘
                                   │
        ┌──────────┬──────────┬───┴────┬──────────┬──────────┐
        ▼          ▼          ▼        ▼          ▼          ▼
   entities/    world/    entities/  entities/  entities/  entities/
   player.py   tilemap.py enemy.py  bullet.py  powerup.py effects.py
        │          │
        ▼          ▼
   entities/   world/
   tank.py     tile.py        utils/   settings.py
   (基类)      (7 瓦片类)    (collision, draw, sound, colors)
```

## 2. 状态机

```
              ┌──────┐
              │ MENU │ ◀────────────────────┐
              └───┬──┘                      │
            Enter│Space                      │ Restart
                  ▼                          │
              ┌─────────┐  P (toggle)  ┌────────┐
              │PLAYING  │◀─────────────▶│PAUSED │
              └────┬────┘   P           └────────┘
       清完敌人    │  │基地毁/命0
                  ▼  ▼
        ┌─────────────┐  ┌───────────┐
        │LEVEL_COMPLETE│  │ GAME_OVER │ ── R ──▶ MENU (重开)
        └──────┬──────┘  └───────────┘
        2 秒后 │
               ▼
        next_level()
               │
        ┌──────┴──────┐
        │  最后一关?  │
        └──┬───────┬──┘
        Yes│      No
           ▼      ▼
     ┌─────────┐ (回到 PLAYING)
     │VICTORY  │
     └─────────┘
```

**状态转换的实现位置**：`game/game.py` 的 `Game.update()` 状态分发。

## 3. 主循环

```python
# game/game.py: Game.run()
def run(self):
    last = time.time()
    while self.running:
        now = time.time()
        dt = min(0.1, now - last)         # 1. 防暂停后大 dt 跳变
        last = now
        self.clock.tick(FPS)              # 2. 限速 60 FPS
        self.handle_events()              # 3. 收集输入（QUIT/ESC/R/P/玩家键）
        self.update(dt)                   # 4. 状态机更新
        self.draw()                       # 5. 渲染（HUD → level.draw）
        pygame.display.flip()             # 6. 翻页
```

**关键点**：
- `dt` 用 `time.time()` 计算（不用 `clock.tick()` 自带 ms）→ 暂停后恢复不会跳变
- `dt` 上限 0.1 秒 → 即使卡顿也不会让敌人瞬移
- `clock.tick(FPS)` 仍然在用 → 限制帧率上限

## 4. 一帧的数据流（PLAYING 状态）

```
Game.update(dt)
    └─→ Level.update(dt)
            │
            ├─ shovel 倒计时检查 → 复原基地砖墙
            ├─ _spawn_enemy()  → 敌人数未满 + spawn 间隔到 → 新 EnemyTank
            │
            ├─ Player.update(dt, tilemap, other_tanks, bullets, effects)
            │       │
            │       ├─ 方向优先级 → try_change_direction → 软吸附
            │       ├─ try_move(dx, dy) → AABB 碰撞
            │       └─ 按 fire → shoot() → Bullet + MuzzleFlash
            │
            ├─ 每 Enemy.update(dt, ..., player, base_pos, target_priority)
            │       ├─ 检查 _choose_target_dir → line_of_sight
            │       ├─ 每 0.8~1.6s 选新方向（55% 概率优先瞄准）
            │       ├─ try_move
            │       └─ 每 cooldown 秒开火
            │
            ├─ 每 Bullet.update(dt, tilemap, bullets, tanks, base_callback)
            │       └─ 移动 + 碰撞检查（砖/钢/基地/坦克/子弹）
            │
            ├─ 清理 dead 实体
            │   └─ 新死亡的敌人: 25% 概率掉 PowerUp
            │
            ├─ 每 PowerUp.update + 拾取检测
            │   └─ _apply_powerup() → 影响 player 状态 / 全屏爆炸 / shovel
            │
            ├─ 每 Effect.update
            │
            ├─ 基地 destroyed? → failed = True
            └─ 敌人全灭 + 全部生成完? → completed = True

Game.draw()
    ├─ self.screen.fill(BLACK)
    ├─ draw_hud(...)
    ├─ self.level.draw(surface)
    │       └─ _draw_scene() → tilemap → 敌人 → 玩家 → 子弹 → 道具 → 特效 → 草丛
    └─ 状态遮罩（pause / complete / over / victory）
```

## 5. 模块依赖图

```
                ┌─────────────┐
                │ settings.py │ ←── 所有模块都引
                └──────┬──────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   utils/*          world/*         entities/*
       │               │               │
       └───────────────┴───────────────┘
                       │
                       ▼
                   game/*
                       │
                       ▼
                  main.py
```

**重要**：模块之间**单向依赖**，没有循环 import。`game/level.py` 在文件内函数级导入 `entities.powerup`、`entities.effects` 等，避免顶层循环。

## 6. 关键设计决策

### 6.1 软吸附（Soft Snap）

坦克改变方向时不能瞬间跳到 36 像素格点（视觉突兀），而是在 ~50ms 内平滑移动：

```python
# entities/tank.py: Tank.try_change_direction
# 1. 决定吸附轴（垂直移动 → 吸附 x）
# 2. 试探吸附目标是否合法（带 ±2/±4/±6 微调容差）
# 3. 记录 snap_axis + snap_target
# 4. 每帧 update_snap(dt) 推进 SNAP_RATE 像素
```

**坑**：吸附进行中（snap_axis != None）时，对该轴的移动应被阻止，由 `can_move_now()` 守护。

### 6.2 子弹子系统

`Bullet` 不是 Sprite，是纯数据类。每帧把"上一帧中心位置"追加进 `trail`，画时用渐变小圆渲染 → 拖尾效果。`update` 用子步（steps=max(1, ...)）让高速子弹不穿透薄墙。

### 6.3 砖块子格破坏

经典 Battle City 机制：每个砖块 = 2×2 子格（24px）。子弹只破坏命中的那一格，用位掩码 `subtl`（4 bit）记录：

```python
# world/tilemap.py: rect_hits_brick_subcell
sub_index = sub_r * 2 + sub_c    # 0=左上 1=右上 2=左下 3=右下
if tile.subtl & (1 << sub_index):
    hits.append((tile, c, r, sub_index))
```

### 6.4 is_player 标记

代替早期用 `__import__("entities.player")` 黑魔法动态判别身份。`Tank.__init__` 设 `is_player=False`，`PlayerTank.__init__` 末尾设 `True`。`Tank.shoot()` 用它决定 bullet owner 字符串。

### 6.5 程序生成音效

没有外部资源。`tools/gen_sounds.py` 用 `wave + struct + math` 生成 4 个 WAV。`utils/sound.py` 启动时如果发现 wav 缺失会自动调用生成器。**任何异常都被 try/except 吞掉，音效失败不影响游戏**。

### 6.6 CJK 字体自动检测

`game/hud.py: _find_cjk_font()` 在 Windows / macOS / Linux 上按优先级列表查找，找不到回退到等宽字体（中文显示为豆腐块但不会崩）。`get_font()` 是项目内统一入口。

## 7. 渲染顺序（z 序）

```
1. 清屏（黑色）
2. HUD 背景
3. 地图瓦片（tilemap.draw）
4. 敌人
5. 玩家
6. 子弹
7. 道具（闪烁 4 Hz）
8. 特效（炮口闪光、爆炸粒子）
9. 草丛（tilemap.draw_foreground，最后画，遮住坦克）
10. 状态遮罩（暂停/通关/结束）
```

**为什么草丛最后画**：坦克"钻进"草丛只露炮管，是 Battle City 经典视觉。`tilemap.draw_foreground()` 单独画草丛层。

## 8. 关键文件清单

| 想改什么 | 看哪里 |
|---------|--------|
| 屏幕尺寸 / 帧率 | `settings.py` SCREEN_W/H, FPS |
| 坦克速度 / 子弹速度 / 生命 | `settings.py` TANK_SPEED 等 |
| 玩家开火冷却 | `settings.py` PLAYER_FIRE_COOLDOWN |
| 敌人 tier 行为 | `entities/enemy.py` TIER_FIRE_COOLDOWN 等 dict |
| 道具类型 / 效果 | `entities/powerup.py` ALL_TYPES + `game/level.py` _apply_powerup |
| 关卡难度 | `settings.py` LEVEL_DIFFICULTY |
| 关卡布局 | `world/levels.py` LEVEL_1~6 |
| 瓦片规则 | `world/tile.py` |
| 视觉效果（颜色） | `utils/colors.py` |
| 音效 | `utils/sound.py` + `tools/gen_sounds.py` |
| 菜单文案 | `game/menu.py` |
| 状态机 | `game/game.py` |
| 主循环 | `game/game.py` Game.run() |
