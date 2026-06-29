# TankBattleGame — AI 接手指南

> 这是 Python + pygame-ce 坦克大战游戏。**新 AI 接手时必读**。

## 第一步：阅读文档

按顺序读 `docs/` 目录下的 6 份文档：

1. **`docs/README.md`** — 项目总览 + 阅读顺序
2. **`docs/01-architecture.md`** — 架构：状态机、主循环、模块图
3. **`docs/02-entities.md`** — 实体：Tank / Player / Enemy / Bullet / PowerUp / Effects
4. **`docs/03-game-loop.md`** — 主循环：Game / Level / HUD / Menu / TileMap / Levels
5. **`docs/04-api-reference.md`** — API 速查：所有类、方法、常量
6. **`docs/05-developer-guide.md`** — 开发指南：**10 项已修 Bug**、风格约束、扩展点、踩坑清单

读完后，**用 3-5 句话向用户总结你理解的项目结构**，再听下一步需求。

## 第二步：跑测试确认环境

```bash
python tests/test_smoke.py        # 冒烟测试（15 项）— 仍可单独跑
python tests/test_features.py     # 功能 + 回归测试（35 项）— 仍可单独跑
python tests/test_events.py       # 事件总线单测（9 项）— 仍可单独跑
# 推荐: pytest 一次性跑全部 (59 tests, ~1.5s)
pytest tests/ -v
# pytest 自动发现 test_*.py 中的 def test_xxx() 函数, 收集
# 3 个脚本式测试 (test_visual, test_gameplay, test_chinese_menu)
# 不被 pytest 收集, 需单独跑 (CI 中由 .github/workflows/ci.yml 触发)
# 注: conftest.py 有 autouse session fixture 初始化 pygame,
# 所以即使 test_events 也跑 pygame.init() (1.5s 内全部跑完)
```

如果失败，先排查环境问题再继续。

## 关键约束

- **Python 3.10+** / **pygame-ce**（不是 pygame）
- **无任何图片资源**，所有视觉用 `utils/draw.py` 纯代码绘制
- **6 关**，难度从 `world/levels.py` + `settings.LEVEL_DIFFICULTY` 配
- **音效自动生成**（`tools/gen_sounds.py`），无需素材
- **CJK 字体**用 `game/hud.get_font()`，别自己 `SysFont`

## 修改前必读

**改任何东西前**先查 `docs/05-developer-guide.md`：
- 第 3 节：10 项已修 Bug —— 不要回退
- 第 4 节：风格约束 —— 必须保持
- 第 5 节：扩展点 —— 优先用已有挂钩
- 第 6 节：踩坑清单 —— 13 条具体坑

## 提交前清单

- [ ] `pytest tests/ -v` 通过 (69 tests, ~1.5s)
- [ ] 脚本式测试单独跑通 (`test_visual.py` / `test_gameplay.py` / `test_chinese_menu.py`)
- [ ] 没回退已修 Bug
- [ ] 没引入 magic number
- [ ] 新瓦片/道具/关卡/事件都改了对应的 dict/常量/触发点
- [ ] 音效失败有 try/except

## 快速开始

```bash
pip install -r requirements.txt
python main.py                 # 启动游戏
pytest tests/ -v               # 跑测试 (59 tests)
```

---

**入口文件**：`main.py`（11 行）→ `game/game.py: Game.run()` 主循环
