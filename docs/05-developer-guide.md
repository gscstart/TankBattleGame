# 05 · 开发者指南

> 给后续接手的人：**怎么跑、怎么测、踩过什么坑、怎么扩展**。

---

## 1. 环境搭建

### 1.1 Python 版本

**必须 Python 3.10+**。3.14 也兼容（项目用 `pygame-ce` 解决了 wheel 问题）。

### 1.2 依赖

3 个：
- `pygame-ce >= 2.5`（社区版，3.14 兼容）
- `pytest >= 7.0`（342 tests 跑通）
- `numpy >= 1.20`（**F20** 背景音乐程序生成依赖）

```bash
pip install -r requirements.txt
```

### 1.3 启动

```bash
python main.py
```

窗口尺寸 832×684。

### 1.4 跑测试

```bash
# 全部单元测试 (342 tests)
python -m pytest tests/ -v

# 3 个脚本式测试（生成截图到 tests/screenshots/）
python tests/test_smoke.py        # 冒烟测试 (实际是 pytest)
python tests/test_visual.py       # 视觉验证
python tests/test_chinese_menu.py # 中文菜单
python tests/test_gameplay.py     # 端到端模拟
```

**无头模式**：所有测试在 conftest.py 设 `os.environ.setdefault("SDL_VIDEODRIVER", "dummy")`，可在 CI 跑（`.github/workflows/ci.yml`）。

### 1.5 重新生成音效

```bash
python tools/gen_sounds.py
```

或删除 `assets/sounds/*.wav` 后启动游戏，会自动调 `gen_sounds.main()`。

### 1.6 重新生成 BGM

**BGM 不需要文件** — `utils/music.py` 启动时自动用 `numpy` 合成 3 段 8-bit chiptune。**0 版权风险**。

---

## 2. 操作与玩法

| 按键 | 作用 |
|------|------|
| **W/A/S/D** 或 **↑/↓/←/→** | 移动 |
| **空格 / J** | 发射子弹 |
| **P** | 暂停 / 恢复 |
| **R** | GAME_OVER 后重开 |
| **Enter / Space** | 主菜单开始 |
| **1 / 2** | 1P / 2P 模式 |
| **H** | 排行榜 (B2) |
| **A** | 成就列表 (C5) |
| **R** | 回放列表 (C6) |
| **M** | 开关 BGM (F20) |
| **+ / −** | 调音量 (F20) |
| **L** | 切换中英语言 (B6) |
| **ESC** | 退出 / 重放退出 |

**目标**：守护底部中央的基地，击毁所有敌人。
**15 关全部通关** → 胜利（含 BOSS 关卡）。

---

## 3. 已修复 Bug 历史（17 项）

> 这些是 code review 阶段找到并修复的 bug。**后续修改时请确认不要回退**。

### A 阶段（基础设施）

#### Bug #1：star 升级无效
- **症状**：拾取 star 道具后子弹仍不能破钢墙
- **根因**：`Tank.shoot()` 早期用 `__import__("entities.player")` 判断身份，**升级到 2 级时也没用**
- **修复**：在 `Tank.__init__` 加 `self.is_player = False`，`PlayerTank.__init__` 末尾设 `True`；`shoot()` 用 `self.is_player` + `getattr(self, "upgrade_level", 0) >= 2` 决定 `can_break_steel`

#### Bug #2：shovel 倒计时永不结束
- **症状**：拾取 shovel 后基地墙永远不恢复
- **根因**：`Level.update()` 没检查 `_shovel_timer`，到时也没调 `_restore_shovel()`
- **修复**：`update()` 开头增加 shovel 倒计时分支，到 0 调 `_restore_shovel()`

#### Bug #3：重生后道具状态全清
- **症状**：玩家死了再复活，star 升级、invincible、frozen 状态全没了
- **根因**：`respawn_player()` 直接 `PlayerTank(x, y)` 全新实例
- **修复**：`respawn_player()` 保存旧 player 引用，把 `upgrade_level` / `invincible - 1s` / `frozen_enemies_timer` 拷到新实例

#### Bug #4：关卡 6 的 E 出生点被忽略
- **症状**：`LEVEL_6` 显式标了 `E` 在 (0,1) 和 (12,1)，但敌人都从默认 (0,0)/(6,0)/(12,0) 出
- **根因**：`from_layout` 早先直接用 `player_spawn` 默认值，忽略 `E` 标记
- **修复**：`from_layout` 收集 `E` 到 `explicit_enemy_spawns` 列表，构造时用 `explicit_enemy_spawns[:3]`

#### Bug #5：grenade 双重计分
- **症状**：吃 grenade 道具一次，所有敌人死亡 + 后续清理循环再加分一次
- **根因**：`Level.update()` 清理循环无条件 `score += 100`
- **修复**：
  - `Tank` 加 `killed_by_powerup` 标志
  - `_apply_powerup("grenade")` 立即 `e.dead = True` + `e.killed_by_powerup = True`
  - 清理循环只在 `not e.killed_by_powerup` 时计分
  - grenade 自己内部 `score += count * 100`

#### Bug #6：死代码（已删除）
- **症状**：`entities/tank.py` 早期有一行 `import utils.colors as C` 等运行时从 Tank 引 utils
- **修复**：删除无用 import

#### Bug #7：尸体阻挡出生点
- **症状**：敌人被击杀后 `self.enemies` 仍保留尸体对象，新敌人无法在同点生成
- **根因**：`_spawn_enemy()` 检查 `e.rect.colliderect(spawn_rect)` 时没跳过 `e.dead`
- **修复**：循环里加 `if e.dead: continue`（尸体不占位）

#### Bug #8：匿名 TileEmpty 类
- **症状**：子弹破钢墙时用 `type("TileEmpty", (), {})()` 匿名类，导致 `isinstance(tilemap.tiles[r][c], TileEmpty)` 失败
- **修复**：从 `world.tile` 导入真实的 `TileEmpty` 使用

#### Bug #9：玩家冷却硬编码 0.5
- **症状**：玩家开火间隔 = 0.5s，但 `settings.PLAYER_FIRE_COOLDOWN = 0.45`
- **根因**：`Tank.FIRE_COOLDOWN = 0.5` 类常量被 `PlayerTank` 继承，没重写
- **修复**：`PlayerTank.FIRE_COOLDOWN = PLAYER_FIRE_COOLDOWN`（0.45）

#### Bug #10：所有道具同音效
- **症状**：star / grenade / helmet / clock / shovel / tank 拾取时都播 "hit"
- **修复**：定义 `POWERUP_SOUND` dict（6 个 type → 4 个音效的不同映射），按 type 取

### B 阶段（可玩性）

#### Bug #11：mine 击杀应加分 (B4)
- **症状**：B4 地雷一次性炸死多个敌人只加 1 次分
- **修复**：`Level.update` 累加 `mine_kills`，结束统一加分 `score += mine_kills * SCORE_PER_ENEMY`

#### Bug #12：冰面 snap_axis 残留 (B5)
- **症状**：玩家离开冰面后仍被吸附卡住
- **根因**：`PlayerTank.update` 在 `on_ice=True` 时跳过 `update_snap(dt)`，但 `snap_axis` 仍为上次的值
- **修复**：冰面分支显式 `self.snap_axis = None`

#### Bug #13：i18n 启动加载无 fallback (B6)
- **症状**：`i18n.json` 损坏时整个 UI 显示 key 字符串（如 "menu.title"）
- **修复**：`_load_lang` 失败 → `_STRINGS = {}`，然后 fallback 到英文（`LANG = "en"`，再试中文）

### C 阶段（破除复刻感）

#### Bug #14：SuicideEnemy 重复计分 (C3 review)
- **症状**：自爆者自杀后被算 2 次 ENTITY_KILLED + 100 分（自爆 + 清理块）
- **根因**：`SuicideEnemy._detonate` 内部 publish 事件，level 清理块也 publish
- **修复**：自爆者设 `self.killed_by_powerup = True` 让 level 跳过，self publish 改 `owner=powerup` 表达"自杀"

#### Bug #15：BOSS.update 签名不一致 (C2 review, **真 crash**)
- **症状**：BOSS 关 `lv.update()` 立即抛 `TypeError: BossTank.update() got multiple values for argument 'effects'`
- **根因**：`BossTank.update` 第 5 个位置参数是 `effects`，`EnemyTank.update` 是 `player`。`level.py` 通用调用 `e.update(..., ai_target, effects=self.effects, ...)` 把 `ai_target` 误传 `effects`
- **C2 review 漏掉**：当时测试 `boss.dead = True; lv.update(0.01)` 让 BOSS.update 早退 `if self.dead: return`，**没真执行 update 逻辑**
- **修复**：`BossTank.update` 签名改成 `(dt, tilemap, other_tanks, bullets, player, effects=None, ...)`，与 EnemyTank 对齐
- **Regression test**：`test_boss_full_update_loop_does_not_crash` 跑 60 帧完整 update

### Review 清理

#### Bug #16：18 个 dead imports
- **症状**：AST 扫描发现 18 个未使用的 import
- **详情**：boss.py (pygame, TANK_SIZE) / effects.py (TANK_SIZE) / enemy.py (pygame, utils.colors) / player.py (RESPAWN_INVULN) / special.py (math, Bullet) / tank.py (math, Dir) / hud.py (MAP_X, MAP_Y) / menu.py (HUD_H) / draw.py (4 常量 + math) / music.py (math) / settings.py (Enum)
- **修复**：review 阶段批量删除

#### Bug #17：3 个 BossTank 局部 import 重复
- **症状**：`game/level.py` 有 3 处 `from entities.boss import BossTank` 局部 import
- **修复**：提到顶部一次

---

## 4. 风格约束（来自代码 review）

> 改代码时**务必保持**：

1. **不用 `__import__` 黑魔法**。需要判别身份用 `self.is_player` 标记
2. **import 在文件顶部**。**严禁** 局部 import（除了循环依赖回避）。`from entities.boss import BossTank` 应该在 `level.py` 顶部
3. **新瓦片类型在 `world/tile.py` 改 4 个属性**：`blocks_tank` / `blocks_bullet` / `destructible` / `bullet_consumed`
4. **新道具类型**改 4 处：`powerup.ALL_TYPES`、`powerup.TYPE_COLORS`、`powerup._draw_icon`、`Level._apply_powerup`、`Level.POWERUP_SOUND`
5. **新关卡**改 `world/levels.py` 末尾追加 + `settings.LEVEL_DIFFICULTY` 同步加一行
6. **新增可调参数**放 `settings.py`，**别在文件里散落 magic number**
7. **音效失败必须静默**（`utils/sound.py` 内部全 try/except），不要让声音问题阻塞游戏
8. **CJK 字体走 `get_font()`**，别在文件里直接 `pygame.font.SysFont("simhei", ...)`（不同平台不通用）
9. **新事件名加 `events.py` 常量**。订阅者接收 `**kwargs`，命名见各事件常量下注释
10. **持久化走 `_atomic_write`**（临时文件 + rename）避免半写损坏
11. **成就 / 回放 / 排行榜模块用 JSON + 损坏 fallback** 到空结构，不抛异常
12. **新特殊敌人继承 `EnemyTank`**，只覆写差异点（`__init__` 强制颜色 + 特色方法），不引入新基类
13. **新 Boss / Enemy / Player update 签名第 5 个位置参数必须是 `player`**（跟 `EnemyTank` 对齐），否则 `level.py` 通用调用会传错
14. **BGM 不携带音乐文件**，全部 `numpy` 合成方波 + ADSR

---

## 5. 扩展点

> 想加功能时，**优先用以下已有的挂钩点**，不要绕开。

### 5.1 新增敌人 tier
- `entities/enemy.py` 加 `TIER_FIRE_COOLDOWN[tier]` / `TIER_SPEED_MULT[tier]` / `TIER_BREAKS_STEEL[tier]` / `settings.ENEMY_TIER_COLORS[tier]`
- 改 `Level._spawn_enemy` 的 `tier = (self.enemies_killed) % N` 中的 N

### 5.2 新增道具
- `entities/powerup.py` 加新 type 到 `ALL_TYPES`、`TYPE_COLORS`、`_draw_icon` 增 elif
- `game/level.py` `_apply_powerup` 加 elif 分支
- `game/level.py` `POWERUP_SOUND` 加映射
- `i18n/zh.json` + `i18n/en.json` 加 key

### 5.3 新增瓦片类型
- `world/tile.py` 加新类（继承 Tile）
- `world/tilemap.py` `CHAR_TO_TILE` 加字符
- `utils/draw.py` `draw_tile` 加 isinstance 分支 + `_draw_xxx` 函数

### 5.4 新增关卡
- `world/levels.py` 追加 `LEVEL_16 = [...]`，加进 `LEVELS` 列表
- `settings.LEVEL_DIFFICULTY` 追加对应配置
- 长度严格 17×17（`GRID_W`×`GRID_H`）

### 5.5 新增关卡模式
- `settings.LEVEL_DIFFICULTY[i]["mode"]` 加新值（如 "puzzle"/"race"）
- `Level.__init__` 读 config + 调相应系统
- `Level.update` 处理新流程
- `Level.update` 末尾"通关条件"块加分支

### 5.6 新增游戏状态
- `settings.State` 加新字符串
- `Game.handle_events` / `Game.update` / `Game.draw` 各加一个分支
- `game/menu.py` 加新画面的 `draw_xxx` 函数
- 加 i18n key

### 5.7 新增成就 (C5)
- `utils/achievements.py` `ACHIEVEMENTS` 列表加新 `Achievement`
- 选择已有触发器（ENTITY_KILLED/POWERUP_PICKED/LEVEL_COMPLETED），
  或加新的"关卡级状态"在 `Manager.on_level_*` 钩子里
- 加 i18n key (`ach.xxx.name` / `ach.xxx.desc`)

### 5.8 新增菜单子视图
- `game/menu.py` 加 `draw_xxx` 函数
- `Game.draw()` 在 `state == MENU` 加 elif
- `Game.handle_events` 在 `menu_view == 'main'` 加新快捷键
- `i18n` 加 key

### 5.9 新增 BOSS
- `entities/boss.py` 加新 boss 类（继承 `BossTank` 或 `Tank`）
- `settings.BOSS_*` 加常量
- `Level._spawn_enemy` 跳过 spawn（已在 `__init__` 手动 spawn）
- `Level.update` 末尾"通关条件" BOSS 分支加新类型判断

### 5.10 新增特殊敌人 (C3)
- `entities/special.py` 加新类（继承 `EnemyTank`，只覆写差异点）
- 加到 `SPECIAL_ENEMY_CLASSES` 列表
- `settings.SPECIAL_COLORS` / `settings.SPECIAL_ENEMY_CHANCE` 加配置
- 如果有行为常量（如自爆半径）加到 `settings`

### 5.11 新增 BGM 段 (F20)
- `utils/music.py` 加新旋律列表（如 `MENU_MELODY_2`）
- `generate_xxx_bgm()` 加新生成函数
- `MusicManager.__init__` `self._tracks` 加新键
- `track_for_state` 加新映射
- `settings.MUSIC_*` 加配置

### 5.12 改玩家控制
- `entities/player.py` `handle_event` 加新键监听
- `PlayerTank.update` 加新行为

### 5.13 改 AI 行为
- `entities/enemy.py` `_choose_target_dir` / `_dir_to_target` / `update` 都是入口
- 改瞄准规则时同步改 `line_of_sight` 的"目标"参数

### 5.14 改子弹
- `entities/bullet.py` `update` 的检查顺序就是钩子点
- 子步数 = `max(1, max(|dx|,|dy|)/2) + 1`，调这个改穿透行为
- **C3 弹跳**：撞墙/砖块/钢墙处加 `bounces_left > 0` 分支 + `_bounce()` 反向
- **C3 加速**：`Tank.shoot` 后 `bullet.speed_multiplier = ...`

---

## 6. 常见踩坑清单

> 改这些地方前请三思。

| 坑 | 后果 | 怎么避免 |
|----|------|----------|
| 改 `Tank.__init__` 没考虑 `is_player` 默认值 | 玩家不再 is_player | 默认 False，PlayerTank 设 True |
| 改 `tilemap.tiles[r][c] = ...` 用匿名类 | isinstance 失败 | 用真实 `TileEmpty` / `TileSteel` |
| 改 `FIRE_COOLDOWN` 在 `Tank` 类而不在 `PlayerTank` | 玩家变 0.5s | 玩家类重写 |
| 改 `_shovel_backup` 不备份原瓦片 | shovel 结束后基地墙消失 | 一定要先备份再替换 |
| 改 `Level.update` 的清理循环没看 `killed_by_powerup` | grenade 双重计分 | 必有该判断 |
| 改 `_spawn_enemy` 不跳过 `e.dead` | 尸体挡出生点 | 必有 `if e.dead: continue` |
| 改 `_on_base_hit` 不震屏 | 基地被毁无反馈 | 设 `screen_shake_time = 0.3` |
| 加新瓦片不改 4 个 `blocks_xxx` 属性 | AI 穿墙/撞墙错乱 | 4 个属性全设 |
| 加新关卡长度不是 17×17（`GRID_W`×`GRID_H`）| 渲染错位 + 测试 fail | 用 `"." * GRID_W` 模板构造 |
| 改 `LEVEL_DIFFICULTY` 长度小于 `len(LEVELS)` | 越界 IndexError | 保证 `len(LEVEL_DIFFICULTY) >= len(LEVELS)` |
| 改 `Bullet.update` 不用子步 | 高速穿透薄墙 | 必须子步 |
| 改 `MuzzleFlash.draw` 不叠坦克颜色 | 视觉失真 | 用 owner_color |
| 改 `PowerUp.update` 用 dt 而不是 time.time() | 帧率敏感 | 用绝对时间 |
| **C2 BOSS** 子类 update 签名不一致 | `TypeError: got multiple values for argument 'effects'` | 第 5 个位置参数必须是 `player` |
| **C3 自爆** 没设 `killed_by_powerup=True` | 自杀后重复计分 + 重复 publish 事件 | `self.dead = True` 后立即 `self.killed_by_powerup = True` |
| **C5 成就** Manager 忘记 `events.clear()` 后再创建 | 测试间订阅污染 | 每个测试 `events.clear()` + 新建 Manager |
| **C6 回放** 录制的 keys 没通过 `dict(keys)` 拷贝 | 重放时 keys 引用导致玩家 keys 被改 | `self.level.players[0].keys = dict(keys)` |
| **F20 BGM** 在 `Level.update` 末尾切 track | 切换抖动 | 仅在 `Game.update` 末尾 `if state != self._last_bgm_state` 时切 |

---

## 7. 性能注意事项

- **Bullet.update 是热点**：每帧每个子弹都跑。子步数 = `max(1, max(|dx|,|dy|)/2) + 1`，每帧最多约 5 步
- **Tilemap.rect_collides_solid**：扫描 rect 覆盖的所有格子。同屏坦克数 + 子弹数 × 频率 = 几百次/帧
- **音效 lazy init**：首次 `play()` 才初始化 mixer，不会卡启动
- **音效资源**：程序生成 4 个 WAV 总共 < 0.5 秒音频，启动时一次性生成
- **BGM 资源**：3 段 8-bit chiptune 启动时一次性合成（numpy），~2-6 秒音频每段
- **关卡数据**：纯字符串，无运行时解码开销
- **回放数据**：1 关 60fps × 60s = 3600 帧 × 5 bool ≈ 100 字节/帧 = 360KB/关

### 7.1 已知性能风险（路线图 §7）

- **双打 + BOSS + 5 特殊敌人同屏** 可能掉帧
- 未用 cProfile 实测过

### 7.2 优化候选

- `Bullet.update` 用 cProfile 找热点
- `Tilemap.rect_collides_solid` 缓存查询
- 子弹批量碰撞检测

---

## 8. 测试约定

### 8.1 测试组织

```
tests/
├── conftest.py                     # SDL dummy + pygame init
├── test_smoke.py / test_features.py # 核心冒烟 (A 阶段)
├── test_events.py                  # 事件总线 (A2)
├── test_input.py                   # 输入抽象 (A4)
├── test_highscores.py              # B2
├── test_red_flash_enemy.py          # B1
├── test_survival_mode.py           # B3
├── test_ice_slide.py               # B5
├── test_powerup_expansion.py       # B4
├── test_two_player.py              # C1
├── test_i18n.py                    # B6
├── test_boss.py                    # C2
├── test_special_enemies.py         # C3
├── test_level_expansion.py         # C4
├── test_achievements.py            # C5
├── test_replay.py                  # C6
├── test_music.py                   # F20
├── test_visual.py / test_gameplay.py / test_chinese_menu.py  # 脚本式 (生成截图)
```

### 8.2 命名

测试文件：`tests/test_*.py`
测试函数：标准 pytest 风格 `def test_xxx():`

### 8.3 模板

```python
import os
import pytest
import tempfile

from settings import PLAYER_LIVES
from game.level import Level

@pytest.fixture
def tmp_file():
    d = tempfile.mkdtemp(prefix="test_")
    yield os.path.join(d, "data.json")
    shutil.rmtree(d, ignore_errors=True)

def test_something(manager, tmp_ach_path):
    """一句话描述测试目的."""
    # 准备
    lv = Level(0, lives=PLAYER_LIVES, score=0)
    # 执行
    # ...
    # 断言
    assert ...
```

### 8.4 测试覆盖

- **状态一致性**：`dead` 但 `hp > 0` → bug
- **事件触发**：订阅 events，验证 publish 时机
- **持久化**：用临时目录，写读 round-trip + 损坏 fallback
- **回归**：每次新功能加 1-2 个 test 防回退

---

## 9. 发布流程（推荐）

```bash
# 1. 跑全测
python -m pytest tests/ -v

# 2. 跑脚本测试
python tests/test_visual.py
python tests/test_chinese_menu.py
python tests/test_gameplay.py

# 3. Headless 模拟玩（手动跑 review 工具）
PYTHONPATH=. python tools/_headless_play.py
PYTHONPATH=. python tools/_headless_movement.py

# 4. 看 git status，确认无遗留
git status

# 5. commit + push
git add -A
git commit -m "..."
git push origin dev
```

### 9.1 Review 检查清单

每次 commit 前确认：
- [ ] 全测过（`pytest`）
- [ ] 无 dead import（AST 扫描）
- [ ] 无 hardcoded 中文（应走 `i18n.t`）
- [ ] 无 magic number（应走 `settings`）
- [ ] 加新成就/新 BGM/新 BOSS 同步加 i18n key
- [ ] 加新关卡同步 `LEVEL_DIFFICULTY`
- [ ] 涉及子类的 update 签名与 `EnemyTank` 对齐（第 5 个位置参数是 `player`）
