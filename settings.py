"""坦克大战游戏全局常量。"""
from enum import Enum

# 屏幕尺寸
SCREEN_W = 832
# SCREEN_H 在下面由 HUD_H + MAP_PIXEL_H 推导

# 地图区域（顶部留 HUD）
HUD_H = 60
MAP_Y = HUD_H
# 实际网格：17×17（决策 #5 方案 C，见 docs/06-feature-roadmap.md §11）
TILE = 36
GRID_W = 17
GRID_H = 17
# 地图像素区域
MAP_PIXEL_W = GRID_W * TILE  # 17 * 36 = 612
MAP_PIXEL_H = GRID_H * TILE  # 17 * 36 = 612
# 重新计算屏幕高度
SCREEN_H = HUD_H + MAP_PIXEL_H  # 60 + 612 = 672

# 地图绘制水平居中
MAP_X = (SCREEN_W - MAP_PIXEL_W) // 2  # (832 - 612) / 2 = 110

# 坦克（= 1 个瓦片，方便整格碰撞）
TANK_SIZE = 36  # 单个瓦片大小 = 坦克大小
TANK_SPEED = 96  # 像素/秒
PLAYER_SPEED = 120
ENEMY_SPEED = 72

# 子弹（等比缩：原 10/48 → 36 缩放 ≈ 8）
BULLET_SIZE = 8
BULLET_SPEED = 320  # 像素/秒
PLAYER_FIRE_COOLDOWN = 0.45  # 秒
ENEMY_FIRE_COOLDOWN_MIN = 0.8
ENEMY_FIRE_COOLDOWN_MAX = 1.6

# 玩家
PLAYER_LIVES = 3
RESPAWN_INVULN = 2.0  # 出生后无敌时间
SCORE_PER_ENEMY = 100
SCORE_PER_LEVEL = 1000

# 敌人
ENEMIES_PER_LEVEL = 15
MAX_ENEMIES_ON_SCREEN = 3
ENEMY_SPAWN_INTERVAL = 2.0  # 秒，敌人间隔

# 敌人生成点（地图顶部 3 个固定位置：左 / 中 / 右）
ENEMY_SPAWN_X = [TILE * 0, TILE * (GRID_W // 2), TILE * (GRID_W - 1)]
ENEMY_SPAWN_Y = TILE * 0

# 玩家出生点（底部中央列，基地上方一行）
PLAYER_SPAWN = (TILE * (GRID_W // 2), TILE * (GRID_H - 2))

# 基地位置（地图底部中央）
BASE_GRID = (GRID_W // 2, GRID_H - 1)  # (col, row)

# 状态
class State:
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    LEVEL_COMPLETE = "level_complete"
    GAME_OVER = "game_over"
    VICTORY = "victory"

# 方向
class Dir:
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    ALL = [UP, DOWN, LEFT, RIGHT]
    NAMES = {UP: "UP", DOWN: "DOWN", LEFT: "LEFT", RIGHT: "RIGHT"}

# FPS
FPS = 60

# 等级
ENEMY_TIER_COLORS = [
    (180, 180, 180),  # 灰 - 基础
    (220, 110, 110),  # 红
    (110, 200, 110),  # 绿
]

# 关卡难度配置（按 index 索引，越界循环）
# enemy_count: 该关总敌人数
# max_on_screen: 同屏最多敌人数
# enemy_speed: 敌人速度
# spawn_interval: 敌人生成间隔（秒）
LEVEL_DIFFICULTY = [
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 1
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 2
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 3
    {"enemy_count": 18, "max_on_screen": 4, "enemy_speed": 78,  "spawn_interval": 1.8},  # 关 4
    {"enemy_count": 20, "max_on_screen": 4, "enemy_speed": 84,  "spawn_interval": 1.5},  # 关 5
    {"enemy_count": 25, "max_on_screen": 5, "enemy_speed": 90,  "spawn_interval": 1.2},  # 关 6
]
