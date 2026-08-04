# 坦克大战 Tank Battle

一款用 Python + pygame-ce 编写的经典坦克大战游戏。**纯代码绘制几何图形**，无需任何图片资源，开箱即玩。

## 特性

- 🎮 **经典玩法**：玩家守基地，击毁所有敌方坦克过关
- 🗺️ **6 个手工关卡**：地形布局各异（砖块、钢墙、丛林、水域、冰面），难度递增
- 🤖 **3 tier 智能 AI 敌人**：随机移动 + 主动瞄准射击 + 出生 1 秒无敌 + 视觉红闪
- 💥 **砖块细分破坏**：子弹只破坏命中的四分之一格（经典机制）
- 🏠 **基地保护**：基地被毁立即游戏结束
- ⏸️ **暂停 / 重启 / 通关** 完整流程
- 🎵 **程序生成音效**：4 个 WAV 脚本生成，无外部资源
- 🎨 **纯代码几何图形**：所有坦克、子弹、瓦片、UI 全部用 pygame primitive 绘制
- 🛠️ **基建完备**：事件总线 + 输入抽象 + pytest（69 tests）+ GitHub Actions CI

## 快速开始

### 环境要求

- Python 3.10+
- pygame-ce ≥ 2.5（社区版，对新 Python 支持更好）

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

### 玩家 2（同屏合作，待 C1 启用）

| 按键 | 作用 |
|------|------|
| **↑ / ↓ / ← / →** | 移动坦克 |
| **Enter** 或 **右 Shift** | 发射子弹 |

> 输入抽象层 `game/input.py` 已就位，A4 阶段完成，P2 启用只需在 `Game.start_game` 实例化第二个玩家并传 `P2_INPUT`（参见 `docs/06-feature-roadmap.md` §阶段 C / C1）。

## 玩法

1. 你控制一辆**黄色坦克**，守护底部中央的**基地（老鹰）**
2. 红色 / 灰色 / 绿色坦克从地图**顶部 3 个生成点**出现，每关同屏 3→5 辆
3. 击毁所有敌人即可进入下一关（共 **6 关**，敌人数 15→25、速度 72→90）
4. 被打中 3 次或基地被毁 → **GAME OVER**
5. 通关全部 6 关 → **VICTORY!**

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

### 道具（6 种）

击毁敌人有概率掉落；拾取后立即生效：

- ⭐ 升级火力（+1 同时存在子弹）
- 🛡️ 临时护盾（4 秒无敌）
- 💣 全屏炸弹（清场所有敌人）
- ⏰ 时钟（敌人冻结 5 秒）
- 🚜 履带修复（+1 生命）
- 🧱 钢墙护体（基地周围临时生成钢墙）

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
│   └── sound.py             # 音效管理器
├── world/                   # 地图
│   ├── tile.py              # 7 种瓦片类型
│   ├── tilemap.py           # 17×17 瓦片地图
│   └── levels.py            # 6 个关卡数据
├── entities/                # 实体
│   ├── tank.py              # 坦克基类
│   ├── player.py            # 玩家坦克
│   ├── enemy.py             # AI 敌人
│   ├── bullet.py            # 子弹
│   ├── powerup.py           # 6 种道具
│   ├── effects.py           # 炮口闪光 + 粒子爆炸
│   └── base.py              # 基地
├── game/                    # 游戏主控
│   ├── game.py              # 状态机 + 主循环
│   ├── level.py             # 关卡运行管理
│   ├── hud.py               # 顶部 HUD
│   ├── menu.py              # 菜单 / 暂停 / 结束画面
│   └── input.py             # 输入抽象层（InputMap）
├── tools/
│   └── gen_sounds.py        # 4 个 WAV 程序生成脚本
├── tests/                   # 测试套件
│   ├── test_smoke.py        # 15 项冒烟测试
│   ├── test_features.py     # 15 项功能 + 7 项回归
│   ├── test_events.py       # 9 项事件总线单测
│   ├── test_input.py        # 10 项输入抽象单测
│   ├── test_visual.py       # 视觉验证
│   ├── test_gameplay.py     # 端到端模拟 + 截图
│   └── test_chinese_menu.py # 中文菜单验证
└── docs/                    # 项目文档
    ├── README.md            # 文档总览
    ├── 01-architecture.md   # 架构
    ├── 02-entities.md       # 实体详解
    ├── 03-game-loop.md      # 主循环 / 关卡 / 菜单
    ├── 04-api-reference.md  # API 速查
    ├── 05-developer-guide.md # Bug 历史 / 风格 / 扩展点 / 踩坑
    └── 06-feature-roadmap.md # 未来规划（阶段 A 已完成）
```

## 验证

### 单元测试（pytest，69 tests / ~2s）

```bash
pip install pytest
pytest tests/ -v
```

### 脚本式测试（生成截图）

```bash
python tests/test_visual.py        # 视觉验证（生成 visual_*.png）
python tests/test_gameplay.py      # 端到端模拟（生成 screenshot_*.png）
python tests/test_chinese_menu.py  # 中文菜单（生成 cn_*.png）
```

> 截图默认输出到仓库根目录，**已被 `.gitignore` 忽略**。

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
| `LEVEL_DIFFICULTY` | 各关难度（敌人数/速度/同屏上限） | 6 项 |

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

- ✅ **阶段 A（基础设施）**：refactor / 事件总线 / pytest / 输入抽象（全部完成）
- 🔜 **阶段 B（可玩性）**：红闪敌人 / 排行榜 / 生存模式 / i18n
- 🔜 **阶段 C（破除复刻感）**：双人合作 / BOSS / 特殊敌人 / 15 关
- 📋 **阶段 D（长线）**：关卡编辑器 / RL 接口 / 手柄 / 背景音乐

## 已知限制

- 敌人 AI 行为较简单（不寻路、不协同），后期可能太机械
- 冰面瓦片已就位但打滑效果未实现（路线图 B5）
- 无背景音乐（路线图 D / F20）
- 同屏双人合作**基础设施已就位，待 C1 启用**
- 资源透明：所有视觉 / 音效均无外部素材依赖

## License

MIT - 自由使用、修改、分发。
