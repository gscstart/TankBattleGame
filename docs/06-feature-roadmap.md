# 06 · 需求功能分析与扩展路线图

> 给 TankBattleGame 的下一阶段演进定方向。
> 调研日期：2026-06-26，**最后更新：2026-08-05**

---

## 0. 文档目的

经过初版（6 关 / 单人 / 3 tier 敌人）已经稳定可玩（`tests/test_smoke.py` 15/15、`test_features.py` 15+7 全过）。本文档：

1. **梳理原版 Battle City（1985 Namco）我们尚未复刻的关键机制**
2. **对比 GitHub / itch.io 上同类项目的现状**
3. **基于代码现状给具体扩展方案 + 优先级 + 实施路径**
4. **明确风险与依赖**
5. **跟踪每阶段的实施进度**（✅ 已完成 / 🔜 进行中）

面向对象：项目维护者 + 后续接手的 AI / 开发者。

**当前总览**（2026-08-05）：
- ✅ 阶段 A（基础设施）4/4 完成
- ✅ 阶段 B（可玩性）6/6 完成
- ✅ 阶段 C（破除复刻感）6/6 完成
- 🔜 阶段 D（长线方向）1/4 完成（F20 背景音乐）

---

## 1. 调研方法

| 来源 | 抓取方式 | 目的 |
|------|----------|------|
| Wikipedia "Battle City" 词条 | curl + 代理（127.0.0.1:7897） | 原版机制权威定义 |
| GitHub Search API `q=battle+city+pygame` | curl + 代理 | 同类 Python 项目对比 |
| itch.io `tag-battle-city` 标签 | curl + 代理 | 独立游戏社区创新玩法 |
| 本项目 6 份文档 + 实际跑通测试 | 本地读取 + `tests/test_*.py` | 现状基线 |

**重要说明**：本环境对 github.com / wikipedia.org 的 `WebFetch` 沙箱拦截，调研用 `curl` 走代理完成（与项目 git push 同源问题，已确认是出口限制不是数据问题）。

---

## 2. 调研结论

### 2.1 原版 Battle City（1985 Namco）核心机制

来源：[Battle City — Wikipedia](https://en.wikipedia.org/wiki/Battle_City)（2025-05 修订版）

| 机制 | 原版 | 我们项目 | 差距 |
|------|------|----------|------|
| 关卡数 | **35 关** | **15 关** | ✅ C4 补到 15 关，剩 20 关（路线图 D） |
| 网格尺寸 | 13×13 | **17×17** | ✓ 我们更大（更细颗粒度） |
| 合作模式 | **同屏双人 co-op** | **同屏双人 co-op** | ✅ C1 完成 |
| 内置关卡编辑器 | **有** | 无 | **❌ 缺失（D 阶段）** |
| 道具类型 | 4 种 | **9 种** | ✅ 远超原版（B4 +3: magnet/laser/mine） |
| 敌人种类 | 4 种（按尺寸分级）| **3 tier + 5 特殊** | ✅ C3 5 种特殊敌人 |
| 红色闪光敌人 | 有 | **有** | ✅ B1 完成 |
| BOSS 关卡 | 有 | **3 个 BOSS 关** | ✅ C2/C4 完成 |
| 砖块子格破坏 | 有 | 有 | ✓ 一致 |
| 草丛/水/冰/钢 | 全有 | 全有 | ✓ 一致 |
| 自杀式失败 | 可击毁自己基地 | 敌人只能从基地打 | ✓ 简化（合理） |
| 道具掉率 | 红闪敌人 = 100% 必掉 | 红闪 100% / 普通 25% | ✓ 一致 |
| 排行榜 | 有 | **有** | ✅ B2 完成 |
| 冰面打滑 | 有 | **有** | ✅ B5 完成 |
| 背景音乐 | 有（Namco 经典 8-bit）| **程序生成 8-bit chiptune** | ✅ F20 完成（0 版权） |
| 多语言 | 无 | **zh + en** | ✅ B6 完成 |
| 成就系统 | 无 | **8 个成就** | ✅ C5 完成 |
| 回放/录像 | 无 | **录键盘序列 + 主菜单 R 键** | ✅ C6 完成 |

### 2.2 同类项目对比

GitHub 搜索 `battle+city+pygame` 共 23 个结果，按 star 排序前 5：

| 项目 | ⭐ | 特性亮点 |
|------|----|---------|
| tirinox/pybattlecity | 20 | 纯 Pygame、关卡配置、敌人 AI |
| awhitefox/pygame_tanks | 6 | 教育项目、OOP 教学 |
| YANGMOXI/TankBattleCity | 4 | 中文社区、网页版移植 |
| Movelocity/battle-city | 3 | **RL 训练环境**（用 pygame 模拟做强化学习） |
| frgonzalezb/Udemy_Battle_City | 2 | Udemy 课程配套 |

**观察**：
- 多数为 1-2 人学习项目，**没有显著超越原版的玩法创新**
- Movelocity 把它做成 **RL 训练环境** —— 这是一个有想象力的方向（AI 自我对战）
- itch.io 上的"The Battle City remake"用 **Unreal Engine 重制**（不是 Python）—— 反映"重制"是该类游戏的常规需求

### 2.3 itch.io 社区观察

`tag-battle-city` 免费游戏区有：
- "The Battle City remake" — 直接复刻
- "Tank game upgraded with modern Unreal Engine" — **现代引擎 + 原版机制**
- "Steel-Terror" — **Zelda + Battle City 混搭**（动作 RPG 化）

社区共同痛点：
- "It's like Battle City but you are alone and someone screwed up with the space-time flow" — **单人孤独感**（✅ C1 已解）
- "Who will win? Reason with bombs or the most intelligent tank?" — **AI 太弱**（D 阶段可做）

---

## 3. 项目现状分析

### 3.1 优势（已具备）

- ✅ 干净的模块分层（entities / world / game / utils / settings）
- ✅ 状态机、碰撞、AABB、子步子弹移动、软吸附等核心机制稳定
- ✅ **17 项已修 Bug 文档化**（详见 `docs/05`）+ **342 项 pytest 回归测试**（增量 283 项）
- ✅ 踩坑清单防止后续回退（17 条）
- ✅ CJK 字体自动检测、程序化音效生成、**程序化 BGM 生成**
- ✅ 视觉纯代码绘制、**零外部资源依赖**（包括音乐）
- ✅ **事件总线**（成就 / 回放 / 排行榜 都基于它）
- ✅ **JSON 持久化 + 原子写**（排行榜 / 成就 / 回放）
- ✅ **i18n 中英文切换**（B6）
- ✅ **review 流程有效**（每阶段 review 都能找到 1+ 个真 bug）

### 3.2 痛点（与扩展相关的）

| 痛点 | 位置 | 状态 |
|------|------|------|
| `self.player` 散落 | `game/level.py` | ✅ A1 修（28 → 0） |
| `Level.update()` 单函数约 200 行 | `game/level.py: update()` | ⏳ 可重构（按子函数分） |
| 关卡数据硬编码字符串 | `world/levels.py` | ⏳ 关卡编辑器和关卡数据格式升级时改 |
| 排行榜 / 存档 / 成就 / 事件系统 | 不存在 | ✅ B2 / C5 / A2 已建 |
| 测试是手写 `if errors: exit(1)` | `tests/*.py` | ✅ A3 改 pytest |
| 玩家输入耦合在 `PlayerTank` | `entities/player.py` | ✅ A4 抽 InputMap |

### 3.3 可用扩展点（已有钩子）

- `entities/powerup.py` 的 `ALL_TYPES` / `TYPE_COLORS` / `_draw_icon` + `Level._apply_powerup` + `POWERUP_SOUND` —— 加新道具改 4 处
- `world/tile.py` 的 `blocks_tank/blocks_bullet/destructible/bullet_consumed` 4 属性 —— 加新瓦片改 4 处
- `entities/enemy.py` 的 `TIER_FIRE_COOLDOWN` / `TIER_SPEED_MULT` / `TIER_BREAKS_STEEL` —— 加新 tier 改 3 处
- `settings.LEVEL_DIFFICULTY` 数组 —— 加新关卡改 2 处
- `state.*` 状态机 —— 加新状态改 3 处（handle_events / update / draw）
- `utils/events.py` 的事件名常量 + `Level.update` 中的 publish 点 —— 加新事件改 2 处
- `entities/special.py` 5 种特殊敌人 + `SPECIAL_ENEMY_CLASSES` —— 加新特殊敌人改 2 处
- `utils/achievements.py` `ACHIEVEMENTS` 列表 —— 加新成就改 1 处
- `utils/music.py` `NOTE_FREQ` + `_render_melody` + `MusicManager._tracks` —— 加新 BGM 段改 3 处
- `i18n/zh.json` + `i18n/en.json` —— 加新 key 改 2 处
- `game/menu.py` draw_* 函数 + `Game.draw()` 路由 —— 加新菜单子视图改 2 处

---

## 4. 需求分析

按"用户价值 × 实现成本"分 4 个优先级。**粗体 = 已完成**。

### P0 — 原版缺失的核心机制

| 需求 | 用户价值 | 实现成本 | 状态 |
|------|----------|----------|------|
| **F1**: 同屏双人合作 | 5/5 | 中 | ✅ **C1** |
| **F2**: 关卡扩充（6→35） | 4/5 | 中 | 🔜 **C4 6→15**，剩 15→35（D 阶段） |
| **F3**: 内置关卡编辑器 | 5/5 | 高 | ❌ 缺失（D 阶段） |
| **F4**: 红色闪光敌人（必掉道具） | 3/5 | 低 | ✅ **B1** |

### P1 — 可玩性提升

| 需求 | 用户价值 | 实现成本 | 状态 |
|------|----------|----------|------|
| **F5**: BOSS 关卡 | 5/5 | 高 | ✅ **C2 + C4**（3 个 BOSS 关） |
| **F6**: 特殊敌人类型 | 4/5 | 中 | ✅ **C3**（5 种） |
| **F7**: 道具扩充（magnet/laser/mine） | 3/5 | 低 | ✅ **B4**（+3 道具 → 9 种） |
| **F8**: 无尽 / 生存模式 | 5/5 | 中 | ✅ **B3 + C4**（2 个 survival 关） |
| **F9**: 分数排行榜 | 4/5 | 低 | ✅ **B2** |
| **F10**: 成就系统 | 3/5 | 中 | ✅ **C5**（8 个成就） |
| **F11**: 事件总线重构 | 基础设施 | 中 | ✅ **A2** |
| **F12**: pytest + GitHub Actions CI | 长期保障 | 低 | ✅ **A3** |
| **F13**: 回放 / 录像系统 | 4/5 | 中 | ✅ **C6** |
| **F14**: 截图 / 录像导出 | 2/5 | 低 | ⏳ C6 已有录像，可加导出 |
| **F15**: 多语言 i18n | 3/5 | 中 | ✅ **B6**（zh + en） |
| **F16**: RL 训练接口 | 4/5 | 中 | ❌ 缺失（D 阶段） |

### P2 — 系统级升级

| 需求 | 用户价值 | 实现成本 | 状态 |
|------|----------|----------|------|
| **F17**: 手柄支持 + F18: 键位重映射 | 跨平台 | 中 | ❌ 缺失（D 阶段） |
| **F19**: 冰面打滑机制 | 5/5（细节）| 低 | ✅ **B5** |
| **F20**: 背景音乐 | 5/5（沉浸感）| 低 | ✅ **F20**（8-bit chiptune 程序生成） |

### 总结

| 阶段 | 任务 | 完成度 |
|------|------|--------|
| **A** 基础设施 | A1 refactor / A2 事件总线 / A3 pytest+CI / A4 输入抽象 | **4/4** ✅ |
| **B** 可玩性 | B1 红闪 / B2 排行榜 / B3 生存 / B4 道具扩充 / B5 冰面 / B6 i18n | **6/6** ✅ |
| **C** 破除复刻感 | C1 双人 / C2 BOSS / C3 5 特殊敌人 / C4 15 关 / C5 成就 / C6 回放 | **6/6** ✅ |
| **D** 长线方向 | F3 编辑器 / F16 RL / F17+F18 手柄 / F20 BGM | **1/4** 🔜 |

---

## 5. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| A1 refactor 引入回归 | 高 | 中 | ✅ A3 pytest 保护 + 1 玩家行为不变标准 |
| F1 双人关卡设计失衡 | 中 | 中 | ✅ C1 共享生命 + 基地（保守）|
| F5 BOSS 平衡不当 | 中 | 低 | ✅ 暴露 HP / 速度 / 弹幕密度为 `settings.BOSS_*` |
| **F13 回放体积大** | 中 | 低 | ✅ 1 关 ~360KB JSON 即可，加 jsonl 增量写可优化 |
| **F15 i18n 抽离漏掉字符串** | 高 | 低 | ✅ review 阶段用 AST 扫描中文字符串，零残留 |
| F3 编辑器 UI 工作量大 | 高 | 中 | 推迟到阶段 D，MVP 先支持"导入关卡字符串" |
| 性能：双打 + BOSS + 特殊敌人同屏 | 中 | 中 | ⏳ 未上 cProfile 测过，D 阶段可加 |
| **C2 BOSS.update 签名不一致** | 中 | 高 | ✅ review 找到 + 修，加 2 个 regression test |
| **持久化损坏** | 低 | 中 | ✅ `_atomic_write` + 损坏 fallback 到空结构 |

---

## 6. 实施路线图

### 阶段 A — 基础设施 ✅ **4/4 完成**（2026-06-29）

**目标**：让后续扩展不再回退

| 任务 | 收益 | 状态 | 完成日期 |
|------|------|------|----------|
| **A1**: `self.player` → `self.players: list[PlayerTank]` refactor | 解锁 P2、成就、事件 | ✅ | 2026-06-27 |
| **A2**: 事件总线（`utils/events.py`） | 解锁成就、回放、CI 钩子 | ✅ | 2026-06-27 |
| **A3**: `pytest` 框架 + GitHub Actions | 后续所有改动有保护网 | ✅ | 2026-06-29 |
| **A4**: 输入抽象层（`game/input.py`） | 解锁手柄、键位重映射 | ✅ | 2026-06-29 |

**最终达成**：22 项手写测试 → **342 项 pytest 回归**；1 玩家行为零变化；`self.player` 引用从 28 降到 0。

**实施说明**（详见 git log）：
- A1 改 `self.players[0]` 保留单玩家兼容性；2 处列表操作改用 `self.players` 整体
- A2 新建 `utils/events.py`，6 个事件名常量（`ENTITY_KILLED`/`POWERUP_PICKED`/`BASE_HIT`/`BASE_DESTROYED`/`LEVEL_COMPLETED`/`LEVEL_FAILED`），异常隔离
- A3 pytest 化 3 个核心测试 + `tests/conftest.py` autouse fixture + `.github/workflows/ci.yml` matrix Python 3.10/3.11/3.12 × ubuntu/windows
- A4 `InputMap` 类 + `P1_INPUT`/`P2_INPUT` 常量；P2 实施时只需 `Game.start_game` 创建 P2 时传 `P2_INPUT`

---

### 阶段 B — 可玩性提升 ✅ **6/6 完成**（2026-07-08）

**目标**：让游戏"像现代独立游戏"

| 任务 | 依赖 | 状态 | 完成日期 |
|------|------|------|----------|
| **B1**: F4 红闪敌人 | A2 | ✅ | 2026-07-01 |
| **B2**: F9 排行榜（top 10） | A2 | ✅ | 2026-07-02 |
| **B3**: F8 生存模式 + 接入排行榜 | A2, B2 | ✅ | 2026-07-03 |
| **B4**: F7 道具扩充（magnet/laser/mine） | A2 | ✅ | 2026-07-05 |
| **B5**: F19 冰面打滑 | A2 | ✅ | 2026-07-07 |
| **B6**: F15 中英文 i18n | A2 | ✅ | 2026-07-08 |

**最终达成**：6 种道具 → **9 种**；6 关 → **6 关**（仍）；红闪敌人 + 排行榜 + 生存模式 + 冰面 + i18n；review 修 2 个 bug（冰面 snap_axis 残留 + i18n 启动加载无 fallback）。

---

### 阶段 C — 破除复刻感 ✅ **6/6 完成**（2026-08-05）

**目标**：从"复刻"变成"独立游戏"

| 任务 | 依赖 | 状态 | 完成日期 |
|------|------|------|----------|
| **C1**: F1 同屏双人合作 | A1+A4 | ✅ | 2026-07-15 |
| **C2**: F5 BOSS 关卡 | A2 | ✅ | 2026-07-28 |
| **C3**: F6 5 种特殊敌人 | A2 | ✅ | 2026-07-29 |
| **C4**: F2 关卡扩充（6→15）| A2 | ✅ | 2026-08-04 |
| **C5**: F10 成就系统 | A2 | ✅ | 2026-08-05 |
| **C6**: F13 回放/录像 | A2 | ✅ | 2026-08-05 |

**最终达成**：
- 关卡 6 → **15**（10 campaign + 2 survival + 3 BOSS）
- 敌人 3 tier → **3 tier + 5 特殊**（自爆/隐形/装甲/火箭/弹跳）
- 道具 9 种 → **9 种**（C3 没加新道具）
- 成就 0 → **8**（5 一次性 + 3 关卡级）
- 新增回放/录像系统

**Review 找到的真 bug**：
- C3 SuicideEnemy 重复计分 + 重复发事件（设 `killed_by_powerup=True` 修）
- C2 BOSS.update 签名不一致（与 EnemyTank 对齐修）— review 用 headless 模拟找到

---

### 阶段 D — 长线方向 🔜 **1/4 完成**（部分）

**目标**：扩展玩家基础 / 学术价值 / 跨平台

| 任务 | 价值 | 状态 | 备注 |
|------|------|------|------|
| **F3**: 关卡编辑器 | 社区 UGC | ❌ | 推迟到下个 sprint，UI 复杂 |
| **F16**: RL 训练接口（gymnasium-style env）| 学术 / AI 演示 | ❌ | 待做 |
| **F17+F18**: 手柄 + 键位重映射 | 跨平台 | ❌ | 待做 |
| **F20**: 背景音乐 | 5/5 沉浸感 | ✅ | **2026-08-05**（8-bit chiptune 程序生成，0 版权） |

**F20 实施说明**：
- `utils/music.py` 新建 — `numpy` 合成方波 + ADSR 包络
- 3 段 BGM：menu（C 大调 4 音符）/ game（A 小调 8 音符）/ victory（C 大调欢快）
- `MusicManager`：play/pause/resume/stop + set_volume + set_enabled
- `Game.update` 末尾 `if state != self._last_bgm_state` 时切 track（避免每帧抖动）
- K_P 暂停时 `music.pause()`，K_M 切 BGM 开关，+/- 调音量
- 0 版权风险（不携带任何音乐文件）

---

## 7. Review 流程（已成熟）

每阶段完成后跑 review 找 bug，已经找出 17 个真 bug：

```
A 阶段: #1-#10 (10 个, 1 玩家兼容性 + 沙堆细节)
B 阶段: #11-#13 (3 个, mine 加分 + 冰面残留 + i18n fallback)
C 阶段: #14-#15 (2 个, 自爆重复计分 + BOSS 签名不一致)
Review 清理: #16-#17 (2 个, dead imports + BOSS crash fix)
```

**Review 工具链**（`tools/_*.py`，gitignore 排除）：
- `_headless_play.py`：模拟玩 5 关（campaign/survival/BOSS/final BOSS/2P）
- `_headless_movement.py`：8 个移动流畅度场景
- `_review_check_i18n.py`：扫 i18n key 完整性

---

## 8. 最终状态（2026-08-05）

```
342/342 pytest 通过
3 个脚本式测试通过
5 关 headless 模拟无 crash
8 个移动流畅度测试全过
34 个 commit 干净 (dev 分支)
0 外部资源依赖 (视觉/音效/音乐全程序合成)
中文 + 英文 完整 i18n
```

**项目已"完整可玩"**，D 阶段剩下 3 项是"长线锦上添花"。
