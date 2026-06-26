"""视觉验证：截取多张图展示新效果（炮口闪光、拖尾、爆炸、履带动画）。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import random

pygame.init()
pygame.font.init()

from settings import SCREEN_W, SCREEN_H, FPS, TILE, MAP_X, MAP_Y, Dir, GRID_W, GRID_H
from game.level import Level
from entities.bullet import Bullet
from entities.effects import MuzzleFlash, Explosion
import entities.enemy as ee
import world.tile as wt
from world.tilemap import TileMap


def make_empty_level():
    layout = ["." * GRID_W for _ in range(GRID_H)]
    _mid = GRID_W // 2
    layout[GRID_H - 2] = layout[GRID_H - 2][:_mid] + "P" + layout[GRID_H - 2][_mid+1:]
    layout[GRID_H - 2] = layout[GRID_H - 2][:_mid] + "X" + layout[GRID_H - 2][_mid+1:]
    row0 = list("." * GRID_W)
    for c in (0, _mid, GRID_W - 1):
        row0[c] = "E"
    layout[0] = "".join(row0)
    return layout


screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))


# --- 图 1：MuzzleFlash 特写 ---
print("Capturing muzzle flash...")
layout = make_empty_level()
tilemap = TileMap.from_layout(layout)
# 在空地上画一辆坦克 + 炮口闪光
player_x = MAP_X + 6 * TILE
player_y = MAP_Y + 6 * TILE
# 画坦克（手动，因为是空测试）
from utils.draw import draw_tank
player_rect = pygame.Rect(player_x, player_y, TILE, TILE)
# 画几个 MuzzleFlash
effects = []
fx = MuzzleFlash(player_x + 24, player_y + 0, Dir.UP, (220, 200, 80))
fx.life = 0.08  # 还新鲜
effects.append(fx)

# 画背景
tilemap.draw(screen)
# 画坦克
draw_tank(screen, player_rect, Dir.UP, (220, 200, 80), (140, 120, 40))
# 画闪光
for e in effects:
    e.draw(screen)
pygame.image.save(screen, "visual_muzzle_flash.png")
print("  saved visual_muzzle_flash.png")

# --- 图 2：子弹拖尾 ---
print("Capturing bullet trail...")
level = Level(0, 3, 0)
# 立即让玩家朝上开火
level.player.keys["up"] = True
level.player.keys["fire"] = True
# 跑 10 帧让子弹飞起来
for _ in range(10):
    level.update(1.0 / FPS)
# 此时应该有 1 颗子弹带拖尾
level.draw(screen)
# 覆盖 HUD
from game.hud import draw_hud
draw_hud(screen, 3, 0, 0, 15)
pygame.image.save(screen, "visual_bullet_trail.png")
print(f"  saved visual_bullet_trail.png (bullets: {len(level.bullets)}, "
      f"trail len: {len(level.bullets[0].trail) if level.bullets else 0})")

# --- 图 3：爆炸粒子 ---
print("Capturing explosion...")
level2 = Level(0, 3, 0)
# 强制触发一个爆炸
level2.effects.append(Explosion(MAP_X + 6 * TILE + 24, MAP_Y + 6 * TILE + 24, big=True))
# 跑 2 帧让粒子散开
for _ in range(3):
    for fx in level2.effects:
        fx.update(1.0 / FPS)
# 画
level2.draw(screen)
draw_hud(screen, 3, 0, 0, 15)
pygame.image.save(screen, "visual_explosion.png")
print(f"  saved visual_explosion.png (particles: {len(level2.effects[0].particles) if level2.effects else 0})")

# --- 图 4：完整关卡中的移动 + 开火 ---
print("Capturing full gameplay scene with effects...")
level3 = Level(0, 3, 0)
# 模拟 2 秒玩家操作
random.seed(7)
for i in range(int(FPS * 2)):
    # 移动 + 频繁开火
    if i % 20 < 8:
        level3.player.keys["up"] = True
        level3.player.keys["fire"] = True
    elif i % 20 < 14:
        level3.player.keys["left"] = True
        level3.player.keys["fire"] = True
    else:
        level3.player.keys["up"] = False
        level3.player.keys["left"] = False
        level3.player.keys["fire"] = False
    level3.update(1.0 / FPS)
level3.draw(screen)
draw_hud(screen, level3.lives, level3.score, level3.index, level3.enemies_to_spawn + len(level3.enemies))
pygame.image.save(screen, "visual_full_scene.png")
print(f"  saved visual_full_scene.png (effects: {len(level3.effects)}, "
      f"enemies: {len(level3.enemies)}, bullets: {len(level3.bullets)})")

# --- 图 5：履带动画对比 ---
print("Capturing tread animation...")
level4 = Level(0, 3, 0)
# 强制让玩家移动一段距离
level4.player.snap_axis = None
for i in range(20):
    level4.player.keys["up"] = True
    level4.player.update(1.0 / FPS, level4.tilemap, [], level4.bullets)
level4.draw(screen)
draw_hud(screen, 3, 0, 0, 15)
pygame.image.save(screen, "visual_treads.png")
print(f"  saved visual_treads.png (tread_phase: {level4.player.tread_phase:.1f})")

# --- 图 6：方向变向的瞬间（软吸附）---
print("Capturing mid-snap...")
level5 = Level(0, 3, 0)
# 把玩家放在非格点位置模拟变向
level5.player.rect.x = MAP_X + 5 * TILE + 14  # 不在格点
level5.player.dir = Dir.UP
# 触发变向到 RIGHT
level5.player.try_change_direction(Dir.RIGHT, level5.tilemap, [])
# 跑 1 帧看吸附过程
level5.player.update_snap(0.02)  # 20ms
# 此时 rect.x 应该介于起始和目标之间
print(f"  snap_axis: {level5.player.snap_axis}, "
      f"target: {level5.player.snap_target}, "
      f"x: {level5.player.rect.x}")
level5.draw(screen)
draw_hud(screen, 3, 0, 0, 15)
pygame.image.save(screen, "visual_snap_midway.png")
print("  saved visual_snap_midway.png")

print("\nAll visual screenshots generated")
print(f"Files: visual_*.png in {os.getcwd()}")

pygame.quit()
