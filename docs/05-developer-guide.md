# 05 · 开发者指南

> 给后续接手的人：**怎么跑、怎么测、踩过什么坑、怎么扩展**。

---

## 1. 环境搭建

### 1.1 Python 版本

**必须 Python 3.10+**。3.14 也兼容（项目用 `pygame-ce` 解决了 wheel 问题）。

### 1.2 依赖

只一个：`pygame-ce >= 2.5`

```bash
pip install -r requirements.txt
```

**为什么用 pygame-ce 而不是 pygame？**
- 标准 pygame 在 Python 3.14 上没有预编译 wheel，需要本地编译 C 扩展
- pygame-ce 是社区维护的分支，提供官方预编译版本，开箱即用
- API 完全兼容

### 1.3 启动

```bash
python main.py
```

窗口尺寸 832×684。

### 1.4 跑测试

```bash
python tests/test_smoke.py        # 15 项冒烟测试
python tests/test_features.py     # 15 功能 + 7 回归测试
python tests/test_gameplay.py     # 端到端模拟 + 截图
python tests/test_visual.py       # 视觉验证
python tests/test_chinese_menu.py # 中文菜单
```

**无头模式**：所有测试在文件开头设置 `os.environ.setdefault("SDL_VIDEODRIVER", "dummy")`，可在 CI 上跑。

### 1.5 重新生成音效

```bash
python tools/gen_sounds.py
```

或删除 `assets/sounds/*.wav` 后启动游戏，会自动调 `gen_sounds.main()`。

---

## 2. 操作与玩法

| 按键 | 作用 |
|------|------|
| **W/A/S/D** 或 **↑/↓/←/→** | 移动 |
| **空格 / J** | 发射子弹 |
| **P** | 暂停 / 恢复 |
| **R** | GAME_OVER 后重开 |
| **Enter / Space** | 主菜单开始 |
| **ESC** | 退出 |

**目标**：守护底部中央的基地，击毁所有敌人。
**6 关全部通关** → 胜利。

---

## 3. 已修复 Bug 历史（10 项）

> 这些是 code review 阶段找到并修复的 bug。**后续修改时请确认不要回退**。

### Bug #1：star 升级无效
- **症状**：拾取 star 道具后子弹仍不能破钢墙
- **根因**：`Tank.shoot()` 早期用 `__import__("entities.player")` 判断身份，**升级到 2 级时也没用**
- **修复**：在 `Tank.__init__` 加 `self.is_player = False`，`PlayerTank.__init__` 末尾设 `True`；`shoot()` 用 `self.is_player` + `getattr(self, "upgrade_level", 0) >= 2` 决定 `can_break_steel`

### Bug #2：shovel 倒计时永不结束
- **症状**：拾取 shovel 后基地墙永远不恢复
- **根因**：`Level.update()` 没检查 `_shovel_timer`，到时也没调 `_restore_shovel()`
- **修复**：`update()` 开头增加 shovel 倒计时分支，到 0 调 `_restore_shovel()`

### Bug #3：重生后道具状态全清
- **症状**：玩家死了再复活，star 升级、invincible、frozen 状态全没了
- **根因**：`respawn_player()` 直接 `PlayerTank(x, y)` 全新实例
- **修复**：`respawn_player()` 保存旧 player 引用，把 `upgrade_level` / `invincible - 1s` / `frozen_enemies_timer` 拷到新实例

### Bug #4：关卡 6 的 E 出生点被忽略
- **症状**：`LEVEL_6` 显式标了 `E` 在 (0,1) 和 (12,1)，但敌人都从默认 (0,0)/(6,0)/(12,0) 出
- **根因**：`from_layout` 早先直接用 `player_spawn` 默认值，忽略 `E` 标记
- **修复**：`from_layout` 收集 `E` 到 `explicit_enemy_spawns` 列表，构造时用 `explicit_enemy_spawns[:3]`（**这正是修复 #4 的核心**）

### Bug #5：grenade 双重计分
- **症状**：吃 grenade 道具一次，所有敌人死亡 + 后续清理循环再加分一次
- **根因**：`Level.update()` 清理循环无条件 `score += 100`
- **修复**：
  - `Tank` 加 `killed_by_powerup` 标志
  - `_apply_powerup("grenade")` 立即 `e.dead = True` + `e.killed_by_powerup = True`
  - 清理循环只在 `not e.killed_by_powerup` 时计分
  - grenade 自己内部 `score += count * 100`

### Bug #6：死代码（已删除）
- **症状**：`entities/tank.py` 早期有一行 `import utils.colors as C` 等运行时从 Tank 引 utils（间接调用）
- **修复**：删除无用 import

### Bug #7：尸体阻挡出生点
- **症状**：敌人被击杀后 `self.enemies` 仍保留尸体对象，新敌人无法在同点生成
- **根因**：`_spawn_enemy()` 检查 `e.rect.colliderect(spawn_rect)` 时没跳过 `e.dead`
- **修复**：循环里加 `if e.dead: continue`（尸体不占位）

### Bug #8：匿名 TileEmpty 类
- **症状**：子弹破钢墙时用 `type("TileEmpty", (), {})()` 匿名类，导致 `isinstance(tilemap.tiles[r][c], TileEmpty)` 失败
- **根因**：`Bullet.update()` 早期 `tilemap.tiles[r][c] = type("TileEmpty", (), {})()`
- **修复**：从 `world.tile` 导入真实的 `TileEmpty` 使用

### Bug #9：玩家冷却硬编码 0.5
- **症状**：玩家开火间隔 = 0.5s，但 `settings.PLAYER_FIRE_COOLDOWN = 0.45`
- **根因**：`Tank.FIRE_COOLDOWN = 0.5` 类常量被 `PlayerTank` 继承，没重写
- **修复**：`PlayerTank.FIRE_COOLDOWN = PLAYER_FIRE_COOLDOWN`（0.45）

### Bug #10：所有道具同音效
- **症状**：star / grenade / helmet / clock / shovel / tank 拾取时都播 "hit"
- **根因**：`Level._apply_powerup` 末尾 `play("hit")` 写死
- **修复**：定义 `POWERUP_SOUND` dict（6 个 type → 4 个音效的不同映射），按 type 取

---

## 4. 风格约束（来自代码 review）

> 改代码时**务必保持**：

1. **不用 `__import__` 黑魔法**。需要判别身份用 `self.is_player` 标记
2. **import 在文件顶部**。`entities/powerup.py` 末尾的 `import math` 是历史遗留
3. **新瓦片类型在 `world/tile.py` 改 4 个属性**：`blocks_tank` / `blocks_bullet` / `destructible` / `bullet_consumed`
4. **新道具类型**改 3 处：`powerup.ALL_TYPES`、`powerup.TYPE_COLORS`、`powerup._draw_icon`、`Level._apply_powerup`、`Level.POWERUP_SOUND`
5. **新关卡**改 `world/levels.py` 末尾追加 + `settings.LEVEL_DIFFICULTY` 同步加一行
6. **新增可调参数**放 `settings.py`，**别在文件里散落 magic number**
7. **音效失败必须静默**（`utils/sound.py` 内部全 try/except），不要让声音问题阻塞游戏
8. **CJK 字体走 `get_font()`**，别在文件里直接 `pygame.font.SysFont("simhei", ...)`（不同平台不通用）

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

### 5.3 新增瓦片类型
- `world/tile.py` 加新类（继承 Tile）
- `world/tilemap.py` `CHAR_TO_TILE` 加字符
- `utils/draw.py` `draw_tile` 加 isinstance 分支 + `_draw_xxx` 函数

### 5.4 新增关卡
- `world/levels.py` 追加 `LEVEL_7 = [...]`，加进 `LEVELS` 列表
- `settings.LEVEL_DIFFICULTY` 追加对应配置

### 5.5 新增关卡后行为
- 改 `Level.__init__` 读 config + 调相应系统
- 改 `Level.update` 流程
- 改 `Level.draw` 视觉

### 5.6 新增游戏状态
- `settings.State` 加新字符串
- `Game.handle_events` / `Game.update` / `Game.draw` 各加一个分支
- `game/menu.py` 加新画面的 `draw_xxx` 函数

### 5.7 改玩家控制
- `entities/player.py` `handle_event` 加新键监听
- `PlayerTank.update` 加新行为

### 5.8 改 AI 行为
- `entities/enemy.py` `_choose_target_dir` / `_dir_to_target` / `update` 都是入口
- 改瞄准规则时同步改 `Line.of_sight` 的"目标"参数

### 5.9 改子弹
- `entities/bullet.py` `update` 的检查顺序就是钩子点
- 子步数 = `max(1, max(|dx|,|dy|)/2) + 1`，调这个改穿透行为

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
| 加新关卡长度不是 13×13 | 渲染错位 + 测试 fail | 用 `"." * 13` 模板构造 |
| 改 `LEVEL_DIFFICULTY` 长度小于 `len(LEVELS)` | 越界 IndexError | 保证 `len(LEVEL_DIFFICULTY) >= len(LEVELS)` |
| 改 `Key.press_time` 默认值 -1.0 | 旧测试无法触发方向 | 默认 0.0（已修） |
| 改 `Bullet.update` 不用子步 | 高速穿透薄墙 | 必须子步 |
| 改 `MuzzleFlash.draw` 不叠坦克颜色 | 视觉失真 | 用 owner_color |
| 改 `PowerUp.update` 用 dt 而不是 time.time() | 帧率敏感 | 用绝对时间 |

---

## 7. 性能注意事项

- **Bullet.update 是热点**：每帧每个子弹都跑。子步数 = `max(1, max(|dx|,|dy|)/2) + 1`，每帧最多约 5 步
- **Tilemap.rect_collides_solid**：扫描 rect 覆盖的所有格子。同屏坦克数 + 子弹数 × 频率 = 几百次/帧
- **音效 lazy init**：首次 `play()` 才初始化 mixer，不会卡启动
- **音效资源**：程序生成 4 个 WAV 总共 < 0.5 秒音频，启动时一次性生成
- **关卡数据**：纯字符串，无运行时解码开销

---

## 8. 测试约定

### 8.1 命名

测试文件：`tests/test_*.py`
测试函数：直接在模块顶层顺序执行（不用 pytest），用 `check(cond, msg)` 收集错误

### 8.2 模板

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # 无头模式

import pygame
pygame.init()
# 如果需要字体/音效
# pygame.font.init()
# pygame.mixer.init()

errors = []
def check(cond, msg):
    if not cond: errors.append(msg); print("FAIL:", msg)
    else: print("OK  :", msg)

# ... 测试代码 ...

if errors: exit(1)
```

### 8.3 回归测试原则

> 每个已修复 Bug 都应有对应测试。

当前 7 项回归测试（`tests/test_features.py` 末尾）：
- #2 shovel 倒计时
- #3 重生保留道具
- #5 grenade 单次计分
- #4 关卡 6 自定义 E 点
- #7 尸体不挡 spawn
- #8 真实 TileEmpty
- #9 玩家冷却 = PLAYER_FIRE_COOLDOWN
- #10 6 种道具不同音效

---

## 9. 调试技巧

### 9.1 慢放

改 `game/game.py: Game.run`：
```python
self.clock.tick(FPS // 4)  # 1/4 速
```

### 9.2 看碰撞盒

临时在 `Level._draw_scene` 末尾加：
```python
for e in self.enemies:
    pygame.draw.rect(surface, (255, 0, 0), e.rect, 1)
for b in self.bullets:
    pygame.draw.rect(surface, (0, 255, 0), b.rect, 1)
```

### 9.3 跳过菜单

```python
# game/game.py Game.__init__ 末尾
self.start_game()
```

### 9.4 锁血

```python
# entities/tank.py Tank.on_hit 开头
self.flashing_time = 999  # 长时间无敌
```

### 9.5 单关测试

```python
# 直接构造 Level(5, ...) 即跳到关 6
level = Level(5, 3, 0)
```

### 9.6 强制掉指定道具

```python
# 替换随机逻辑
level.powerups.append(PowerUp(player.rect.x, player.rect.y, "grenade"))
```

---

## 10. 未来可能的方向（建议）

按实现成本从低到高：

1. **冰面打滑**：现在 `TileIce.blocks_tank=False` 走过去了，可以加"切方向不立刻停"
2. **音效切换**：现在 4 个 WAV 永远相同，可以加暂停专属 / 通关专属
3. **分数排行榜**：本地文件存 top 10
4. **网络对战**：现在 `Bullet.owner` 已经是字符串，加个 socket 协议就能联机
5. **编辑器**：拖拽关卡布局，所见即所得生成 `LEVEL_X = [...]` 字符串
6. **AI 强化**：现在用 `line_of_sight + random`，可换 BFS 寻路 + 协同
7. **存档**：记录每关最高分到 JSON
8. **粒子优化**：Explosion 14 颗太多时掉帧，可以加对象池
9. **国际化**：现在中文硬编码在 `hud.py` / `menu.py`，抽出 i18n 字典
10. **Web 版**：用 pygbag 打包成 WebAssembly

---

## 11. 提交代码前检查清单

- [ ] `python tests/test_smoke.py` 通过
- [ ] `python tests/test_features.py` 通过
- [ ] 没回退已修复 Bug（参考第 3 节）
- [ ] 没引入新 magic number（移到 `settings.py`）
- [ ] 新增的可视元素走 `utils/draw.py`
- [ ] 新增的关卡长度 = 13×13
- [ ] 新增的瓦片设置 4 个 `blocks_xxx` 属性
- [ ] 新增的音效失败有 try/except 兜底
- [ ] 改 AI / 玩家逻辑时检查敌人 `born_invuln` / 玩家 `flashing_time` 守护
- [ ] 改实体 `update` 时检查是否需要更新 `effects` / 道具 / 子弹列表
