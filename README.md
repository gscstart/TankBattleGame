# 坦克大战 Tank Battle

一款用 Python + pygame 编写的经典坦克大战游戏。**纯代码绘制几何图形**，无需任何图片资源，开箱即玩。

## 特性

- 🎮 **经典玩法**：玩家守基地，击毁所有敌方坦克过关
- 🗺️ **3 个手工关卡**：地形布局各异（砖块、钢墙、丛林、水域、冰面）
- 🤖 **智能 AI 敌人**：随机移动 + 主动瞄准射击 + 出生 1 秒无敌
- 💥 **砖块细分破坏**：子弹只破坏命中的四分之一格（经典机制）
- 🏠 **基地保护**：基地被毁立即游戏结束
- ⏸️ **暂停 / 重启 / 通关** 完整流程
- 🎨 **纯代码几何图形**：所有坦克、子弹、瓦片、UI 全部用 pygame primitive 绘制

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

| 按键 | 作用 |
|------|------|
| **W / A / S / D** 或 **↑ / ↓ / ← / →** | 移动坦克 |
| **空格** 或 **J** | 发射子弹 |
| **P** | 暂停 / 恢复 |
| **R** | 游戏结束后重启 |
| **ESC** | 退出 |

## 玩法

1. 你控制一辆**黄色坦克**，守护底部中央的**基地（老鹰）**
2. 红色/灰色/绿色坦克从地图**顶部 3 个生成点**出现，最多同屏 3 辆
3. 击毁所有敌人即可进入下一关（共 3 关）
4. 被打中 3 次或基地被毁 → **GAME OVER**
5. 通关全部 3 关 → **VICTORY!**

### 砖块细分机制

每个砖块由 2×2 个子格组成（每个子格 24×24 像素）。子弹只破坏命中的那一个子格，而不是整块。这个细节让游戏有了"保护基地用砖块围起来、慢慢打掉砖块引敌人进来"的策略空间。

### 瓦片类型

| 类型 | 阻挡坦克 | 阻挡子弹 | 可被破坏 |
|------|:--------:|:--------:|:--------:|
| 砖块 | ✅ | ✅ | ✅（分 4 子格）|
| 钢墙 | ✅ | ✅ | ❌ |
| 草丛 | ❌ | ❌ | ❌ |
| 水域 | ✅ | ❌ | ❌ |
| 冰面 | ❌ | ❌ | ❌ |
| 基地 | ✅ | ✅ | ✅（游戏结束）|

## 项目结构

```
TankBattleGame/
├── main.py                  # 入口
├── settings.py              # 全局常量
├── requirements.txt         # 依赖
├── utils/                   # 工具
│   ├── colors.py            # 颜色常量
│   ├── collision.py         # AABB 碰撞
│   └── draw.py              # 纯代码绘制
├── world/                   # 地图
│   ├── tile.py              # 6 种瓦片类型
│   ├── tilemap.py           # 17×17 瓦片地图
│   └── levels.py            # 3 个关卡数据
├── entities/                # 实体
│   ├── tank.py              # 坦克基类
│   ├── player.py            # 玩家坦克
│   ├── enemy.py             # AI 敌人
│   ├── bullet.py            # 子弹
│   └── base.py              # 基地（重导出）
├── game/                    # 游戏主控
│   ├── game.py              # 状态机 + 主循环
│   ├── level.py             # 关卡运行管理
│   ├── hud.py               # 顶部 HUD
│   └── menu.py              # 菜单 / 暂停 / 结束画面
└── tests/                   # 单元测试
    ├── test_smoke.py        # 模块导入 + 碰撞 + 子弹测试
    └── test_gameplay.py     # 端到端模拟 + 截图
```

## 验证

运行单元测试：

```bash
python tests/test_smoke.py
```

应输出 `ALL TESTS PASSED ✓`（15 项测试）。

运行端到端模拟 + 截图：

```bash
python tests/test_gameplay.py
```

会在当前目录生成 5 张截图（menu / level1 / paused / gameover / victory）。

## 自定义

### 添加新关卡

编辑 `world/levels.py`：

```python
LEVEL_4 = [
    ".................",  # 17 列（见 settings.GRID_W）
    ".................",
    ...
    ".......BXB.......",  # X = 基地（必填）
    ".......BBB.......",
    "........P........",  # P = 玩家出生
    "..BB.....BB..",
]
LEVELS.append(LEVEL_4)
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
| `TANK_SPEED` / `PLAYER_SPEED` / `ENEMY_SPEED` | 坦克速度 | 96 / 120 / 72 |
| `BULLET_SPEED` | 子弹速度 | 320 |
| `PLAYER_LIVES` | 玩家生命 | 3 |
| `ENEMIES_PER_LEVEL` | 每关敌人数 | 15 |
| `MAX_ENEMIES_ON_SCREEN` | 同屏最大敌人数 | 3 |
| `ENEMY_FIRE_COOLDOWN_MIN/MAX` | 敌人开火间隔 | 0.8–1.6s |
| `SCORE_PER_ENEMY` | 每敌得分 | 100 |

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

## 已知限制

- 敌人 AI 行为较简单（不寻路、不协同），后期可能太机械
- 冰面瓦片已就位但打滑效果未实现
- 无音效（pygame.mixer 可用，但未准备资源）
- 仅本地单人

## License

MIT - 自由使用、修改、分发。
