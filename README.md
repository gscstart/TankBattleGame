# 坦克大战 Tank Battle

一款用 Python + pygame-ce 编写的经典坦克大战游戏。**纯代码绘制几何图形**，无需任何图片资源，开箱即玩。

## 特性

- 🎮 **经典玩法**：玩家守基地，击毁所有敌方坦克过关
- 🗺️ **15 个手工关卡**：12 campaign + 2 survival + 3 BOSS（地形各异，难度递增）
- 🤖 **3 tier AI 敌人 + 5 种特殊敌人**：自爆/隐形/装甲/火箭/弹跳
- 👥 **同屏双人合作**：独立生命，共享基地
- 💥 **砖块细分破坏**：子弹只破坏命中的四分之一格（经典机制）
- 🏠 **基地保护**：基地被毁立即游戏结束
- 🏆 **排行榜 + 8 个成就 + 回放录像**：完整可玩性
- ⏸️ **暂停 / 重启 / 通关** 完整流程
- 🎵 **程序生成音效 + 背景音乐**：无任何外部资源，0 版权风险
- 🎨 **纯代码几何图形**：所有坦克、子弹、瓦片、UI 全部用 pygame primitive 绘制
- 🌏 **中英双语**：菜单/HUD/成就全 i18n 抽离
- 🛠️ **基建完备**：事件总线 + 输入抽象 + pytest（340 tests）+ GitHub Actions CI

## 快速开始

### 环境要求

- Python 3.10+
- pygame-ce ≥ 2.5（社区版，对新 Python 支持更好）
- numpy ≥ 1.20（F20 背景音乐程序生成）

> **为什么要用 pygame-ce？** 标准 `pygame` 在 Python 3.14 上没有预编译 wheel，需要本地编译 C 扩展；`pygame-ce` 提供官方预编译版本，开箱即用。

### 安装与运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动游戏
python main.py
```

打开 832×684 窗口后，从主菜单按 **回车 / 空格** 开始游戏。

## 操作说明

### 玩家 1（默认）

| 按键 | 作用 |
|------|------|
| **W / A / S / D** 或 **↑ / ↓ / ← / →** | 移动坦克 |
| **空格** 或 **J** | 发射子弹 |
| **P** | 暂停 / 恢复 |
| **R** | 游戏结束后重启 |
| **ESC** | 退出 |

### 玩家 2（同屏合作，C1 已启用）

| 按键 | 作用 |
|------|------|
| **↑ / ↓ / ← / →** | 移动坦克 |
| **Enter** 或 **右 Shift** | 发射子弹 |

### 主菜单快捷键

| 按键 | 作用 |
|------|------|
| **H** | 排行榜 |
| **A** | 成就列表 |
| **R** | 回放录像（播放通关录像）|
| **L** | 切换中/英文 |
| **M** | 开关 BGM |
| **+ / −** | 调音量 |

## 玩法

1. 你控制一辆**黄色坦克**，守护底部中央的**基地（老鹰）**
2. 红色 / 灰色 / 绿色坦克从地图**顶部 3 个生成点**出现，每关同屏 3→5 辆
3. **5 种特殊敌人** 随机出现：自爆者（橙）/ 隐形者（浅蓝紫）/ 装甲者（深灰，3 血）/ 火箭者（亮黄，2x 速 + 破钢）/ 弹跳者（亮紫，子弹反弹）
4. 击毁所有敌人即可进入下一关（共 **15 关**，敌人数 15→35、速度 72→102）
   - **关 7 / 13**：生存模式（无尽波次）
   - **关 8 / 14 / 15**：BOSS 关（紫色 10 血坦克，能破钢墙）
5. 被打中 3 次或基地被毁 → **GAME OVER**
6. 通关全部 15 关 → **VICTORY!**

### 砖块细分机制

每个砖块由 2×2 个子格组成。子弹只破坏命中的那一个子格，而不是整块。这个细节让游戏有了"保护基地用砖块围起来、慢慢打掉砖块引敌人进来"的策略空间。

### 瓦片类型

| 类型 | 阻挡坦克 | 阻挡子弹 | 可被破坏 |
|------|:--------:|:--------:|:--------:|
| 砖块 | ✅ | ✅ | ✅（分 4 子格）|
| 钢墙 | ✅ | ✅ | ❌ |
| 草丛 | ❌ | ❌ | ❌ |
| 水域 | ✅ | ❌ | ❌ |
| 冰面 | ❌ | ❌ | ❌ |
| 基地 | ✅ | ✅ | ✅（游戏结束）|

### 道具（9 种）

击毁敌人有概率掉落；拾取后立即生效：

- ⭐ 升级火力（+1 同时存在子弹）
- 🛡️ 临时护盾（4 秒无敌）
- 💣 全屏炸弹（清场所有敌人）
- ⏰ 时钟（敌人冻结 5 秒）
- 🚜 履带修复（+1 生命）
- 🧱 钢墙护体（基地周围临时生成钢墙）
- 🧲 磁铁（8 秒吸引所有道具靠近玩家）
- 🔫 激光（10 秒子弹穿透敌人）
- 💥 地雷（玩家前/中/后放 3 颗地雷，敌人触碰 100px AOE 爆炸）

## 项目结构

```
TankBattleGame/
├── main.py                  # 入口
├── settings.py              # 全局常量
├── requirements.txt         # 依赖
├── utils/                   # 工具
│   ├── colors.py            # 颜色常量
│   ├── collision.py         # AABB 碰撞
│   ├── draw.py              # 纯代码绘制
│   ├── events.py            # 事件总线（publish/subscribe）
│   ├── sound.py             # 音效管理器
│   ├── highscores.py        # B2 排行榜 (data/highscores.json)
│   ├── achievements.py      # C5 成就系统 (8 个成就 + data/achievements.json)
│   ├── replay.py            # C6 回放/录像 (录键盘序列 + data/replays/)
│   ├── music.py             # F20 背景音乐 (numpy 合成 8-bit chiptune)
│   └── i18n.py              # B6 中英文切换
├── world/                   # 地图
│   ├── tile.py              # 7 种瓦片类型
│   ├── tilemap.py           # 17×17 瓦片地图
│   └── levels.py            # 15 个关卡数据
├── entities/                # 实体
│   ├── tank.py              # 坦克基类
│   ├── player.py            # 玩家坦克 (支持 B5 冰面打滑)
│   ├── enemy.py             # AI 敌人 (3 tier + 红闪)
│   ├── boss.py              # C2 BOSS 坦克 (10 血, 破钢墙)
│   ├── special.py           # C3 5 种特殊敌人
│   ├── bullet.py            # 子弹 (支持 C3 弹跳 + 加速)
│   ├── powerup.py           # 9 种道具
│   ├── mine.py              # B4 地雷
│   ├── effects.py           # 炮口闪光 + 粒子爆炸
│   └── base.py              # 基地
├── game/                    # 游戏主控
│   ├── game.py              # 状态机 + 主循环
│   ├── level.py             # 关卡运行管理
│   ├── hud.py               # 顶部 HUD
│   ├── menu.py              # 菜单 / 暂停 / 结束 / 成就 / 回放页
│   └── input.py             # 输入抽象层（InputMap）
├── i18n/                    # 中英文字符串
│   ├── zh.json
│   └── en.json
├── data/                    # 用户运行时数据
│   ├── .gitkeep
│   ├── highscores.json      # 运行时生成
│   ├── achievements.json    # 运行时生成
│   └── replays/             # 运行时生成
├── tools/
│   └── gen_sounds.py        # 4 个 WAV 程序生成脚本
├── tests/                   # 测试套件 (340 tests)
│   ├── test_smoke.py
│   ├── test_features.py
│   ├── test_events.py
│   ├── test_input.py
│   ├── test_highscores.py
│   ├── test_red_flash_enemy.py
│   ├── test_survival_mode.py
│   ├── test_ice_slide.py
│   ├── test_powerup_expansion.py
│   ├── test_two_player.py
│   ├── test_i18n.py
│   ├── test_boss.py
│   ├── test_special_enemies.py
│   ├── test_level_expansion.py
│   ├── test_achievements.py
│   ├── test_replay.py
│   ├── test_music.py
│   ├── test_visual.py
│   ├── test_gameplay.py
│   └── test_chinese_menu.py
└── docs/                    # 项目文档
    ├── 01-architecture.md
    ├── 02-entities.md
    ├── 03-game-loop.md
    ├── 04-api-reference.md
    ├── 05-developer-guide.md
    └── 06-feature-roadmap.md
```

## 验证

### 单元测试（pytest，340 tests / ~2.5s）

```bash
pip install pytest
pytest tests/ -v
```

### 脚本式测试（生成截图到 tests/screenshots/）

```bash
python tests/test_visual.py        # 视觉验证（炮口闪光 / 子弹拖尾 / 履带 / 爆炸）
python tests/test_gameplay.py      # 端到端模拟（菜单 / 关卡 / 暂停 / 结束）
python tests/test_chinese_menu.py  # 中文菜单 / 暂停 / 通关 / 胜利 / 失败
```

> 截图统一输出到 `tests/screenshots/`，**已被 `.gitignore` 忽略**。

## 自定义

### 添加新关卡

编辑 `world/levels.py`：

```python
LEVEL_7 = [
    ".................",  # 17 列（见 settings.GRID_W）
    ".................",
    ...
    ".......BXB.......",  # X = 基地（必填）
    ".......BBB.......",
    "........P........",  # P = 玩家出生
    ".................",
]
LEVELS.append(LEVEL_7)
```

字符含义：

- `.` 空地
- `B` 砖块
- `S` 钢墙
- `G` 草丛
- `W` 水域
- `I` 冰面
- `P` 玩家出生点
- `E` 敌人出生点（可放多个，系统取前 3 个）
- `X` 基地（必填一处）

### 调整游戏参数

所有可调参数都在 `settings.py`：

| 常量 | 含义 | 默认 |
|------|------|------|
| `TILE` / `GRID_W` / `GRID_H` | 地图尺寸 | 36 / 17 / 17 |
| `TANK_SPEED` / `PLAYER_SPEED` / `ENEMY_SPEED` | 坦克速度 | 96 / 120 / 72 |
| `BULLET_SPEED` | 子弹速度 | 320 |
| `PLAYER_LIVES` | 玩家生命 | 3 |
| `ENEMIES_PER_LEVEL` | 每关敌人数 | 15 |
| `MAX_ENEMIES_ON_SCREEN` | 同屏最大敌人数 | 3 |
| `ENEMY_FIRE_COOLDOWN_MIN/MAX` | 敌人开火间隔 | 0.8–1.6s |
| `SCORE_PER_ENEMY` | 每敌得分 | 100 |
| `LEVEL_DIFFICULTY` | 各关难度（敌人数/速度/同屏上限） | 15 项 |

## 架构说明

### 状态机

```
MENU  ──Enter──▶  PLAYING  ──P──▶  PAUSED  ──P──▶  PLAYING
                     │
                     ├── 清完敌人 ──▶  LEVEL_COMPLETE  ──2s──▶  PLAYING (next level)
                     │
                     ├── 基地被毁 / 生命归零 ──▶  GAME_OVER  ──R──▶  PLAYING
                     │
                     └── 打完最后一关 ──▶  VICTORY
```

### 主循环

```python
while running:
    dt = clock.tick(60) / 1000
    handle_events()   # 退出 / 暂停 / 玩家按键
    update(dt)        # 状态机分发
    draw()            # 清屏 → 地图 → 实体 → HUD → 遮罩
    display.flip()
```

### 方向吸附

坦克在改变方向时，会在垂直于新方向的轴上自动吸附到 36 像素格点，允许通过窄道：

```python
def try_change_direction(self, new_dir, ...):
    if new_dir[0] == 0:  # 垂直移动
        self.rect.x = round(self.rect.x / TILE) * TILE
    else:  # 水平移动
        self.rect.y = round(self.rect.y / TILE) * TILE
    if not self._collides(...):
        self.dir = new_dir
        return True
    return False
```

## 路线图

参见 [`docs/06-feature-roadmap.md`](docs/06-feature-roadmap.md)。

- ✅ **阶段 A（基础设施）**：refactor / 事件总线 / pytest / 输入抽象（4/4）
- ✅ **阶段 B（可玩性）**：红闪敌人 / 排行榜 / 生存模式 / 道具扩充 / 冰面打滑 / i18n（6/6）
- ✅ **阶段 C（破除复刻感）**：双人合作 / BOSS / 5 种特殊敌人 / 15 关 / 成就 / 回放（6/6）
- 🔜 **阶段 D（长线可选）**：关卡编辑器 / RL 训练接口 / 手柄+键位重映射（已完成 F20 背景音乐）

## 已知限制

- 敌人 AI 行为较简单（不寻路、不协同），后期可能太机械
- BOSS 撞墙反弹 180° 是简化设计，BOSS 在 5×5 房间内来回直线移动
- 重放不录随机种子，重放时敌人位置/行为有偏差（但玩家按键序列一致）
- 资源透明：所有视觉 / 音效 / 音乐均无外部素材依赖（程序合成）

## License

MIT - 自由使用、修改、分发。
