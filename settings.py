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

# 双人合作 (C1: F1 同屏双人 co-op)
# - 决策 #1: 独立生命 (每玩家 3 命, 互不影响)
# - 共享基地 (任一玩家被打中基地都算基地被毁)
# - 共享分数
# - 失败条件: 双玩家都死 OR 基地被毁
P2_ENABLED_DEFAULT = True  # 菜单默认进 2P 模式 (可手动切 1P)

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

# 红闪敌人（powerup carrier）：身上发红光，被击杀时 100% 掉落道具
POWERUP_CARRIER_CHANCE = 0.20  # 每个敌人有 20% 概率成为红闪敌人
POWERUP_CARRIER_COLOR = (255, 60, 60)  # 鲜红，区别于 tier 颜色
POWERUP_CARRIER_FLASH_PERIOD = 0.10  # 闪烁周期（秒），值越小越快

# 道具时长常量 (B4: magnet/laser/mine 扩展)
MAGNET_DURATION = 8.0      # 磁铁持续时间 (秒)
LASER_DURATION = 10.0      # 激光持续时间 (秒)
MINE_COUNT = 3             # 一次放几颗地雷
MINE_BLAST_RADIUS = 100    # 地雷爆炸 AOE 像素范围
MINE_BLAST_DAMAGE = True   # 地雷对敌人一击必杀 (与 grenade 一致)

# 关卡难度配置（按 index 索引，越界循环）
# enemy_count: 该关总敌人数（survival/boss 模式无此字段）
# max_on_screen: 同屏最多敌人数
# enemy_speed: 敌人速度
# spawn_interval: 敌人生成间隔（秒）
# mode: 'campaign' (默认) 或 'survival'（无尽波次）或 'boss'（BOSS 关卡）
# boss_count: boss 模式专属, BOSS 数量
LEVEL_DIFFICULTY = [
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 1
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 2
    {"enemy_count": 15, "max_on_screen": 3, "enemy_speed": 72,  "spawn_interval": 2.0},  # 关 3
    {"enemy_count": 18, "max_on_screen": 4, "enemy_speed": 78,  "spawn_interval": 1.8},  # 关 4
    {"enemy_count": 20, "max_on_screen": 4, "enemy_speed": 84,  "spawn_interval": 1.5},  # 关 5
    {"enemy_count": 25, "max_on_screen": 5, "enemy_speed": 90,  "spawn_interval": 1.2},  # 关 6
    {"mode": "survival", "max_on_screen": 5, "enemy_speed": 96,  "spawn_interval": 0.8},  # 关 7 生存模式
    {"mode": "boss", "boss_count": 1, "enemy_speed": 60},  # 关 8 BOSS 关卡 (enemy_speed 占位, BOSS 用 BOSS_SPEED)
    # C4: 关 9-12 常规关 (4 个新布局, 难度递增)
    {"enemy_count": 28, "max_on_screen": 4, "enemy_speed": 84,  "spawn_interval": 1.5},  # 关 9 冰面
    {"enemy_count": 30, "max_on_screen": 4, "enemy_speed": 88,  "spawn_interval": 1.4},  # 关 10 密室
    {"enemy_count": 32, "max_on_screen": 4, "enemy_speed": 90,  "spawn_interval": 1.3},  # 关 11 钢墙
    {"enemy_count": 35, "max_on_screen": 5, "enemy_speed": 92,  "spawn_interval": 1.1},  # 关 12 终极常规
    # C4: 关 13 生存 II (节奏更紧张)
    {"mode": "survival", "max_on_screen": 6, "enemy_speed": 102, "spawn_interval": 0.6},  # 关 13 生存 II
    # C4: 关 14-15 BOSS 关 (2 个新 BOSS 房)
    {"mode": "boss", "boss_count": 1, "enemy_speed": 60},  # 关 14 BOSS II (钢墙保护)
    {"mode": "boss", "boss_count": 1, "enemy_speed": 60},  # 关 15 终极 BOSS
]

# C2: BOSS 关卡常量 (路线图 §7 风险点 - 暴露常量方便平衡)
BOSS_HP = 10  # BOSS 血量
BOSS_SPEED = 60  # BOSS 速度 (比普通敌人慢, 但能扛)
BOSS_FIRE_COOLDOWN = 1.5  # BOSS 开火冷却 (秒)
BOSS_COLOR = (180, 80, 200)  # 紫色, 区别于 tier 颜色

# C3: 特殊敌人 5 种 (路线图 §6 阶段 C)
# 普通敌人生成时, 概率替换为下列 5 种之一.
SPECIAL_ENEMY_CHANCE = 0.15  # 15% 概率生成特殊敌人
SUICIDE_BLAST_TRIGGER_RADIUS = 80   # 自爆触发半径 (像素, 距玩家)
SUICIDE_BLAST_DAMAGE_RADIUS = 64    # 自爆伤害半径 (像素, 周围敌人)
STEALTH_CYCLE = 2.0          # 隐形周期 (秒)
STEALTH_VISIBLE_FRAC = 0.15  # 显形时长占比 (~0.3s)
ARMOR_HP = 3                 # 装甲敌人血量
ROCKET_SPEED_MULT = 2.0      # 火箭子弹速度倍率
BOUNCE_COUNT = 1             # 弹跳子弹反弹次数

# C3: 5 种特殊敌人颜色 (路线图 §6 阶段 C - 颜色显著区别于 tier)
SPECIAL_COLORS = {
    "suicide": (255, 100, 0),   # 橙 - 自爆
    "stealth": (150, 150, 220), # 浅蓝紫 - 隐形
    "armor":   (80, 80, 80),    # 深灰 - 装甲
    "rocket":  (220, 200, 60),  # 亮黄 - 火箭
    "bounce":  (200, 80, 200),  # 亮紫 - 弹跳
}

# F20: 背景音乐 (路线图 §6 阶段 D)
# 程序生成的 8-bit chiptune BGM, 0 版权风险
# 3 段: menu (轻松) / game (紧张) / victory (欢快)
MUSIC_ENABLED = True           # 总开关 (K_M 切)
MUSIC_VOLUME = 0.35            # 默认音量 (0.0 - 1.0, 不超过 0.5 避免吵)
MUSIC_SAMPLE_RATE = 22050      # 8-bit 风格 (降低内存 + 复古音色)
