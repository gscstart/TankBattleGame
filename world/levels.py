"""关卡数据。每个关卡是 13 个字符串（13x13）。

字符含义：
.  = 空地
B  = 砖块（可被破坏）
S  = 钢墙（不可破坏）
G  = 草丛
W  = 水域
I  = 冰面
P  = 玩家出生点
E  = 敌人出生点
X  = 基地（必有一处）
"""

# 关 1：经典入门，砖块围墙保护基地
LEVEL_1 = [
    ".............",
    ".BB.BB.BB.BB.",
    ".BB.BB.BB.BB.",
    ".............",
    ".BB.SSSSS.BB.",
    ".....BBB.....",
    "....BBXBB....",
    ".....BBB.....",
    "..BB.....BB..",
    "..B.......B..",
    "..B.......B..",
    "..B...P...B..",
    "..BB.....BB..",
]

# 关 2：中央水域，钢墙点缀
LEVEL_2 = [
    "SSSS.....SSSS",
    ".............",
    ".BB.BB.BB.BB.",
    ".B.........B.",
    ".B.BBGGGGB.B.",
    ".B.G.....G.B.",
    ".B.G.WWW.G.B.",
    ".B.G.W.W.G.B.",
    ".B.G.WWW.G.B.",
    ".B.G.....G.B.",
    ".B.BB...BB.B.",
    "...B.PPP.B...",
    "...B.BXB.B...",
]

# 关 3：复杂迷宫
LEVEL_3 = [
    "..S..BBB..S..",
    "...BB...BB...",
    "..B.B...B.B..",
    ".B...B.B...B.",
    "B.BB.B.B.BB.B",
    "...B.BBB.B...",
    ".B.B.....B.B.",
    "B.B.BBB.B.B.B",
    ".B.B...B.B.B.",
    "B...B.B.B...B",
    ".BB.BBB.B.BB.",
    ".B..B.P.B..B.",
    "BBBBB.BXBBBBB",
]

# 关 4：钢墙屏障 + 砖块迷宫（难度提升）
LEVEL_4 = [
    "SSSSS...SSSSS",
    "S.BB.BBB.BB.S",
    "..B.B...B.B..",
    ".BB.B.B.B.BB.",
    "S..B.BBB.B..S",
    ".BB.B...B.BB.",
    "B..B.SSS.B..B",
    ".B..B...B..B.",
    "B..B.SSS.B..B",
    ".BB.B...B.BB.",
    "S..B.BBB.B..S",
    ".BB.BBXB.BB..",
    "..B...P...B..",
]

# 关 5：水域迷宫 + 多钢墙（高难度）
LEVEL_5 = [
    "WWWW.....WWWW",
    "W.BB.SSS.BB.W",
    "W.B..WWW..B.W",
    "W.BB.WWW.BB.W",
    "W....WWW....W",
    "SSSS.....SSSS",
    ".............",
    ".BB.BB.BB.BB.",
    ".B.........B.",
    ".B.BB...BB.B.",
    "..B..BXB..B..",
    "..B...P...B..",
    "..BB.....BB..",
]

# 关 6：Boss 关 - 钢墙迷宫，敌人多
LEVEL_6 = [
    "SSSSSSSSSSSSS",
    "EBB.BB.BB.BBE",
    ".B..B.B.B..B.",
    ".BB.B.B.BB.B.",
    "....BBB......",
    ".BB.SSS.BB...",
    "..B.BXB.B....",
    ".BB.SSS.BB...",
    "....BBB......",
    ".BB.B.B.BB.B.",
    ".B..B.B.B..B.",
    ".B.......P.B.",
    ".BB.....BB...",
]

LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3, LEVEL_4, LEVEL_5, LEVEL_6]


def get_level(index: int) -> list[str]:
    """返回关卡布局字符串列表。"""
    return LEVELS[index % len(LEVELS)]


def get_level_difficulty(index: int) -> dict:
    """返回关卡难度配置 dict。"""
    from settings import LEVEL_DIFFICULTY
    return LEVEL_DIFFICULTY[index % len(LEVEL_DIFFICULTY)]


def get_total_levels() -> int:
    return len(LEVELS)
