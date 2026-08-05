# 坦克大战 — 项目文档索引

> 给**想深入读代码 / 接手动手做修改 / 给后续 AI 接手**的人准备的入口。
> **如果你只想跑游戏 / 看玩法 / 找可调参数**：看 [根 README](../README.md) 就行。

---

## 阅读顺序

按从浅到深排列。第一次接手这个项目建议**按顺序读完前 4 章**，第 5 章按需查阅。

| 顺序 | 文档 | 用途 | 何时读 |
|:----:|------|------|--------|
| 1 | **[01-architecture.md](01-architecture.md)** | 项目全貌、状态机、模块图、主循环、数据流 | 任何修改前必读 |
| 2 | **[02-entities.md](02-entities.md)** | 坦克 / 子弹 / 道具 / 特效 / 基地的属性与状态机 | 想改 / 加 entity 时读 |
| 3 | **[03-game-loop.md](03-game-loop.md)** | 关卡运行、HUD、菜单、瓦片、关卡数据 | 想改关卡 / UI / 游戏流程时读 |
| 4 | **[04-api-reference.md](04-api-reference.md)** | 所有公开类 / 函数 / 常量的 API 速查 | 写代码时当字典查 |
| 5 | **[05-developer-guide.md](05-developer-guide.md)** | Bug 历史 / 风格约束 / 扩展点 / 踩坑清单 | 改 bug / 加功能 / 跑测试前必读 |
| 附 | **[06-feature-roadmap.md](06-feature-roadmap.md)** | 阶段 A→D 路线图 + 当前进度 | 想了解项目演进历史时读 |

---

## 1 分钟项目速览

- **类型**：2D 经典坦克大战（Battle City）单机 / 同屏双人
- **技术栈**：Python 3.10+ / pygame-ce（社区版）/ numpy（仅 BGM）
- **代码量**：约 6500 行 Python 源码
- **架构**：状态机 + 单主循环 + 模块分层（entities / game / world / utils / settings）
- **规模**：15 关（12 campaign + 2 survival + 3 BOSS）/ 9 道具 / 3 tier + 5 特殊敌人 / 8 成就
- **测试**：18 个 `test_*.py` 套件，**342 tests / ~2s**（pytest）
- **资源**：0 外部图片 / 4 个程序生成 WAV（SFX）/ 3 段 numpy 合成 BGM（0 版权风险）
- **i18n**：菜单 / HUD / 成就全抽离，运行时按 L 切中英文

---

## 章节速查

### 📐 [01-architecture.md](01-architecture.md)（架构总览）
- 项目模块图（entities / game / world / utils / i18n / data / tests / docs）
- 状态机子视图（Game + Level）
- 主循环数据流（`handle_events → update → draw`）
- 事件总线设计（publish / subscribe）
- 输入抽象层（InputMap）
- 持久化策略（atomic write / 高分 / 成就 / 录像）
- 主菜单子视图切换（H / A / R 键）

### 🚗 [02-entities.md](02-entities.md)（实体参考）
- `Tank` 坦克基类（移动 / 吸附 / 开火 / 闪红 / 受击）
- `PlayerTank` 玩家坦克（方向优先级 / 惯性滑行 / 冰面打滑）
- `EnemyTank` AI 敌人（3 tier 分级 / 瞄准策略 / 红闪机制）
- `BossTank` BOSS 坦克（10 血 / 破钢墙 / 撞墙反弹）
- `SuicideEnemy` / `StealthEnemy` / `ArmorEnemy` / `RocketEnemy` / `BounceEnemy` 5 种特殊敌人
- `Bullet` 子弹（子格破坏 / 拖尾 / 弹跳 / 加速）
- `Powerup` 9 种道具 + `Mine` 地雷 + `Base` 基地
- `Effects` 炮口闪光 + 粒子爆炸

### 🎮 [03-game-loop.md](03-game-loop.md)（游戏主循环 + 世界）
- `Game` 状态机（`MENU/PLAYING/PAUSED/LEVEL_COMPLETE/GAME_OVER/VICTORY`）
- `Level` 关卡运行（敌人生成 / 道具 / 震屏 / BOSS / 成就钩子）
- `HUD` 顶部 HUD + CJK 字体检测
- `Menu` 主菜单 / 暂停 / 通关 / 结束 / 成就 / 回放页
- `Tilemap` 17×17 网格 + 碰撞查询
- `Tile` 7 种瓦片类型（空 / 砖 / 钢 / 草 / 水 / 冰 / 基地）
- `Levels` 15 关数据 + 难度曲线
- 集成：`Achievements` / `Replay` / `Music` 三个 utils 的接入点

### 📚 [04-api-reference.md](04-api-reference.md)（API 速查）
- `settings.py` 全局常量
- `entities/` 全部公开类
- `game/` 状态机 + 关卡 API
- `utils/` 工具（事件 / 颜色 / 碰撞 / 音效 / 排行榜 / 成就 / 回放 / 音乐 / i18n）
- 事件触发点（13 个事件常量 + 触发位置）

### 🛠 [05-developer-guide.md](05-developer-guide.md)（开发者指南）
- **已修复 Bug 历史**（17 个，含 BOSS 签名不一致 / C3 自爆双重计分 / 冰面 snap_axis 残留 / i18n 启动 fallback 等）
- 14 条代码风格约束
- 14 个扩展点（已设计好的挂钩位）
- 17 条踩坑清单
- 测试运行（pytest 342 + 3 个脚本式）
- 调试工具（headless 模拟）

### 🗺 [06-feature-roadmap.md](06-feature-roadmap.md)（路线图）
- 调研方法论（为什么这么做 / 借鉴了什么）
- 跟原版 Battle City 的特性对比
- 阶段 A→D 实施进度跟踪（A 4/4 ✅ / B 6/6 ✅ / C 6/6 ✅ / D 1/4 🔜）
- D 阶段待办：F3 关卡编辑器 / F16 RL 训练接口 / F17+18 手柄+键位重映射

---

## 文件树（docs 视角）

docs 章节交叉引用的核心文件：

```
TankBattleGame/
├── main.py                       # 入口
├── settings.py                   # 全局常量（关卡难度/速度/状态/颜色）
├── requirements.txt              # pygame-ce + numpy
│
├── entities/                     # 02 详
│   ├── tank.py · player.py · enemy.py
│   ├── boss.py · special.py      # C2 / C3
│   ├── bullet.py · powerup.py
│   ├── mine.py · effects.py · base.py
│
├── game/                         # 03 详
│   ├── game.py · level.py
│   ├── hud.py · menu.py · input.py
│
├── world/                        # 03 详
│   ├── tile.py · tilemap.py · levels.py
│
├── utils/                        # 04 详
│   ├── events.py · collision.py · colors.py
│   ├── sound.py                  # 4 个 WAV
│   ├── highscores.py             # B2
│   ├── achievements.py           # C5
│   ├── replay.py                 # C6
│   ├── music.py                  # F20
│   ├── i18n.py · draw.py
│
├── i18n/                         # zh.json · en.json
├── data/                         # 运行时：highscores / achievements / replays
├── tools/                        # gen_sounds.py (WAV fallback)
└── tests/                        # 18 个 test_*.py + conftest.py + screenshots/
```

---

## 快速上手

```bash
pip install -r requirements.txt
python main.py                # 启动游戏

pytest tests/ -v              # 跑 342 个测试
python tests/test_visual.py        # 视觉验证 + 截图
python tests/test_gameplay.py      # 端到端模拟
python tests/test_chinese_menu.py  # 中文菜单验证
```

---

## 给后续 AI 的建议

1. **改 entity 行为前**：先看 `02-entities.md` 了解状态字段（很多 bug 都源于改一处忘另一处）。
2. **改关卡 / 道具 / 敌人前**：先看 `05-developer-guide.md` 的"已修复 Bug 历史"和"踩坑清单"（不要重复踩坑）。
3. **修复 bug 前**：先 grep 整个项目搜索相似模式（很多 bug 是"一类型 N 处"，改一处忘改）。
4. **新增功能时**：参考"扩展点"小节（已设计好的挂钩点 + 事件订阅位）。
5. **常量调整**：所有可调参数在 `settings.py`，详见 `04-api-reference.md`。
6. **不要主动"美化"相邻代码**：遵循 karpathy 的 surgical change 原则——只动必要的，**不修 A 阶段遗留 bug 除非被问到**。
7. **保持测试绿**：每次功能改动必须跑 `pytest tests/ -q`（< 3s）+ 至少 1 个 headless 模拟场景。

---

最后更新：2026-08-05
