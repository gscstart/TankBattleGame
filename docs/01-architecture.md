# 01 · 架构总览

> 一份让新接手的人 5 分钟理解整个项目骨架的文档。

## 1. 顶层架构

```
                    ┌─────────────────────────────────────────┐
                    │              main.py (入口)              │
                    │           Game().run() 主循环             │
                    └──────────────────────┬──────────────────┘
                                           │
                    ┌──────────────────────▼──────────────────┐
                    │           game/game.py (Game 控制器)    │
                    │   状态机: MENU/PLAYING/PAUSED/           │
                    │     LEVEL_COMPLETE/GAME_OVER/VICTORY    │
                    │   每帧: handle_events → update → draw   │
                    │   持有: achievements, replay, music     │
                    └──────────────────────┬──────────────────┘
                                           │ self.level
                    ┌──────────────────────▼──────────────────┐
                    │        game/level.py (Level 关卡)        │
                    │   持有: tilemap, players, enemies,      │
                    │         bullets, powerups, mines, effects│
                    │   模式: campaign / survival / boss      │
                    │   关卡: 1-15 (10 camp + 2 surv + 3 BOSS) │
                    └─────────┬──────────────┬───────────────┘
                              │              │
        ┌─────────────────────┘              └────────────────────┐
        ▼                                                            ▼
  ┌────────────────────┐                                ┌────────────────────┐
  │     entities/      │                                │      world/         │
  │   tank.py (基类)   │                                │   tile.py (7 类)    │
  │   player.py        │                                │   tilemap.py        │
  │     (B5 冰面打滑)  │                                │     (17×17 grid)    │
  │   enemy.py (3 tier)│                                │   levels.py         │
  │   boss.py (C2)     │                                │     (15 关数据)     │
  │   special.py (C3)  │                                └────────────────────┘
  │     5 种特殊敌人   │
  │   bullet.py        │
  │     (C3 弹跳/加速) │
  │   powerup.py (9种) │
  │   mine.py (B4)     │
  │   effects.py       │
  │   base.py          │
  └────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  ┌─────────┐           ┌──────────┐          ┌─────────────┐
  │  utils/ │           │ i18n/    │          │   data/      │
  │  (13)   │           │ zh.json  │          │ (运行时生成) │
  │         │           │ en.json  │          │             │
  │ events  │           └──────────┘          │ highscores  │
  │ sound   │                                │ achievements│
  │ colors  │                                │ replays/    │
  │ collision│                               │ .json       │
  │ draw    │                                └─────────────┘
  │ i18n    │
  │ highscores│
  │ achievements│
  │ replay  │
  │ music   │
  │ input   │
  │ hud ... │
  └─────────┘
```

## 2. 状态机

```
              ┌──────┐
              │ MENU │ ◀─────────────────────────────┐
              └───┬──┘                               │
        Enter/H/A/R│/M  (各子菜单)                  │ Restart
                   ▼                                │
              ┌─────────┐  P (toggle)  ┌────────┐   │
              │PLAYING  │◀─────────────▶│PAUSED │   │
              └────┬────┘   P           └────────┘   │
       清完敌人    │  │基地毁/命0                     │
   (boss 全死)     ▼  ▼                              │
        ┌─────────────┐  ┌───────────┐               │
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

**菜单子视图**（state==MENU 时）：
- `main`：主菜单（默认）
- `highscores`（K_H 切换）：排行榜 top 10
- `achievements`（K_A）：8 个成就 + 解锁状态
- `replays`（K_R）：录像列表 + K_Enter 播放 / Del 删除

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
    │
    ├─ BGM 切换 (F20): state 变化时 play/pause/stop
    │
    ├─ 重放模式 (C6): ReplayPlayer.get_keys_at(frame_idx) → 覆盖 player.keys
    ├─ 录制模式 (C6): 录 player.keys → Recorder
    │
    └─→ Level.update(dt)
            │
            ├─ on_level_tick(survival 计时) → Manager
            ├─ shovel 倒计时检查 → 复原基地砖墙
            ├─ _spawn_enemy()  → 敌人数未满 + spawn 间隔到
            │   ├─ 普通: EnemyTank (3 tier)
            │   └─ 15% 概率: SpecialEnemy (C3 5 种之一)
            │
            ├─ 每个 Player.update (C1 支持多玩家)
            │   ├─ B5 冰面检测 → on_ice 标记 → 不吸附持续滑
            │   ├─ 方向优先级 → try_change_direction → 软吸附
            │   ├─ try_move(dx, dy) → AABB 碰撞
            │   └─ 按 fire → shoot() → Bullet + MuzzleFlash
            │
            ├─ 每个 Enemy.update (EnemyTank / BossTank / SpecialEnemy)
            │   ├─ C2 BossTank: 简化 AI, 沿 dir 直线移动 + 撞墙 180° 反弹
            │   ├─ C3 SuicideEnemy: 距玩家 <80px 自爆
            │   ├─ C3 StealthEnemy: 周期 2s 显形 0.3s
            │   ├─ C3 ArmorEnemy: hp=3
            │   ├─ C3 RocketEnemy: 子弹 2x 速 + 破钢墙
            │   └─ C3 BounceEnemy: 子弹反弹 1 次
            │
            ├─ 每个 Bullet.update (C3 支持 bounces_left / speed_multiplier)
            │
            ├─ 清理 dead 实体 → 触发 ENTITY_KILLED 事件
            │   ├─ C5 Manager 收到 → 可能解锁 first_blood/sharpshooter/...
            │   └─ 红闪敌人 100% 掉道具, 普通 25% 掉
            │
            ├─ 道具 + magnet 吸引
            ├─ 地雷 AOE (B4)
            ├─ 特效 (MuzzleFlash / Explosion)
            │
            ├─ 基地 destroyed? → failed = True → BASE_DESTROYED
            └─ 通关条件: campaign 全杀 / survival / boss 全 BOSS 死

Game.draw()
    ├─ self.screen.fill(BLACK)
    ├─ draw_hud(lives, score, level_index, enemies_left)
    ├─ self.level.draw(surface)
    │       └─ _draw_scene() → tilemap → 敌人 → 玩家 → 子弹
    │          → 道具 → 地雷 → 特效 → 重生提示 → 草丛
    └─ 状态遮罩（pause / complete / over / victory）
```

## 5. 模块依赖图

```
                            ┌─────────────┐
                            │ settings.py │ ←── 所有模块都引
                            └──────┬──────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
          utils/*              world/*              entities/*
              │                    │                    │
              └────────────────────┴────────────────────┘
                                   │
                                   ▼
                               game/*
                                   │
                                   ▼
                              main.py
```

**重要**：模块之间**单向依赖**，没有循环 import。`game/level.py` 在文件内函数级导入 `entities.powerup`、`entities.effects` 等，避免顶层循环。

**事件总线**（`utils/events.py`）解耦：Level 只 publish 事件，Achievements Manager / Sound / 等订阅，各做各事。

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

**C3 扩展**：Bullet 加 `bounces_left`（弹跳次数）和 `speed_multiplier`（速度倍率，火箭 2.0）。

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

### 6.5 程序生成音效 + 音乐（F20）

没有外部资源：
- **音效**：`tools/gen_sounds.py` 用 `wave + struct + math` 生成 4 个 WAV
- **音乐**：`utils/music.py` 用 `numpy` 合成 3 段 8-bit chiptune（菜单/游戏/胜利）
- `utils/sound.py` 启动时如果发现 wav 缺失会自动调用生成器
- **任何异常都被 try/except 吞掉，音效/音乐失败不影响游戏**

### 6.6 CJK 字体自动检测

`game/hud.py: _find_cjk_font()` 在 Windows / macOS / Linux 上按优先级列表查找，找不到回退到等宽字体（中文显示为豆腐块但不会崩）。`get_font()` 是项目内统一入口。

### 6.7 事件总线（pub-sub）

为成就（F10）、回放（F13）、CI 钩子（F12） 提供解耦的事件流：

```python
from utils import events
events.subscribe(events.ENTITY_KILLED, my_handler)
events.publish(events.ENTITY_KILLED, kind="enemy", owner="player", ...)
```

**约定**：
- 模块级单例
- 事件名用点分命名空间: `'entity.killed'`, `'powerup.picked'`
- 订阅者接收 `**kwargs`
- 单个订阅者抛错被 try/except 吞掉, 打印 traceback, 不影响其他订阅者
- 测试用 `events.clear()` 重置

### 6.8 多玩家独立 InputMap（C1）

每个玩家绑定一个 `InputMap`（P1=P1_INPUT, P2=P2_INPUT），各自响应自己的键。P1 和 P2 用不同键避免冲突（同屏双人合作）。

### 6.9 持久化（JSON + 原子写）

排行榜 / 成就 / 回放 都用 JSON 持久化到 `data/`：

- `data/highscores.json` — 排行榜 top 10
- `data/achievements.json` — 8 个成就解锁状态
- `data/replays/<name>.json` — 录像文件

**写策略**：`_atomic_write()` 先写临时文件再 rename，避免半写损坏。

### 6.10 状态机菜单子视图

`self.menu_view` 字段支持 `'main' / 'highscores' / 'achievements' / 'replays'`，主菜单按 K_H/A/R 切换子视图（K_M 切 BGM），`draw()` 根据 menu_view 调不同的 draw_* 函数。
