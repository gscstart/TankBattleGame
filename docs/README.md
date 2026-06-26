# 坦克大战 (Tank Battle) — 文档

> 面向后续维护 / 接手开发 AI 的完整项目文档。
> **开始阅读顺序**：先看 `01-architecture.md`（项目大局），再按需查阅具体章节。

## 目录

| 文档 | 用途 | 适合谁 |
|------|------|--------|
| **[01-architecture.md](01-architecture.md)** | 项目全貌、状态机、模块图、主循环、数据流 | 第一次接手项目的人 / 任何后续修改前必读 |
| **[02-entities.md](02-entities.md)** | 坦克、子弹、道具、特效、基地的属性与状态 | 想改 / 加 entity 类型时读 |
| **[03-game-loop.md](03-game-loop.md)** | 关卡、HUD、菜单、瓦片、关卡数据 | 想改关卡 / UI / 游戏流程时读 |
| **[04-api-reference.md](04-api-reference.md)** | 所有公开类、函数、常量的 API 速查 | 写代码时当字典查 |
| **[05-developer-guide.md](05-developer-guide.md)** | Bug 历史、测试、环境、扩展点、踩坑清单 | 改 bug / 加功能 / 跑测试前必读 |

## 1 分钟项目概览

- **类型**：2D 经典坦克大战（Battle City）单机游戏
- **技术栈**：Python 3.10+ / pygame-ce（社区版，对新 Python 支持更好）
- **代码量**：约 3500 行（Python 源码），完全用代码绘制几何图形，**无任何图片资源**
- **架构**：状态机 + 单主循环 + 模块分层（entities / game / world / utils / settings）
- **6 关**：难度递增（敌人数 15→25，速度 72→90，同屏 3→5）
- **测试**：3 个测试套件，覆盖冒烟、功能、回归
- **音效**：程序化生成 4 个 WAV（无需素材）

## 文件树

```
TankBattleGame/
├── main.py                  # 入口（11 行）
├── settings.py              # 全局常量（屏幕尺寸/速度/关卡难度/方向/状态）
├── requirements.txt         # pygame-ce
├── entities/                # 游戏实体
│   ├── tank.py              # 坦克基类（移动、吸附、开火、闪红）
│   ├── player.py            # 玩家坦克（方向优先级、惯性滑行）
│   ├── enemy.py             # AI 敌人（tier 0/1/2 差异、瞄准基地）
│   ├── bullet.py            # 子弹（子格破坏、拖尾、爆炸）
│   ├── powerup.py           # 6 种道具
│   ├── effects.py           # 炮口闪光 + 粒子爆炸
│   └── base.py              # 基地（重导出 TileBase）
├── world/                   # 地图系统
│   ├── tile.py              # 7 种瓦片（空/砖/钢/草/水/冰/基地）
│   ├── tilemap.py           # 17×17 网格 + 碰撞查询
│   └── levels.py            # 6 个关卡数据
├── game/                    # 游戏控制
│   ├── game.py              # 状态机 + 主循环
│   ├── level.py             # 关卡运行（敌人生成、道具、震屏）
│   ├── hud.py               # 顶部 HUD + CJK 字体检测
│   └── menu.py              # 主菜单/暂停/通关/结束画面
├── utils/                   # 工具
│   ├── collision.py         # AABB + line_of_sight
│   ├── draw.py              # 纯代码绘制所有视觉
│   ├── sound.py             # 音效管理器（懒加载）
│   └── colors.py            # 颜色常量
├── assets/sounds/           # 4 个程序生成的 WAV
├── tools/gen_sounds.py      # 音效生成脚本
├── tests/                   # 3 个测试套件
│   ├── test_smoke.py        # 15 项冒烟测试
│   ├── test_features.py     # 15 项功能 + 7 项回归测试
│   ├── test_gameplay.py     # 端到端模拟 + 截图
│   ├── test_visual.py       # 视觉验证
│   └── test_chinese_menu.py # 中文菜单验证
└── docs/                    # ← 你在这里
```

## 快速开始

```bash
pip install -r requirements.txt
python main.py          # 启动游戏
python tests/test_smoke.py     # 跑冒烟测试
python tests/test_features.py  # 跑功能测试
```

## 给后续 AI 的建议

1. **改 entity 行为前**：先看 `02-entities.md` 了解状态字段（很多 bug 都源于改一处忘另一处）。
2. **改关卡前**：先看 `03-game-loop.md` 的"关卡数据格式"小节（17×17 字符串网格）。
3. **修复 bug 前**：先看 `05-developer-guide.md` 的"已修复 Bug 历史"（不要重复踩坑）。
4. **新增功能时**：参考"扩展点"小节（已设计好的挂钩点）。
5. **常量调整**：所有可调参数在 `settings.py`，详见 `04-api-reference.md` 的 settings 章节。
