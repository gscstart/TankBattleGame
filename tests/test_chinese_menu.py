"""生成中文菜单截图验证。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
pygame.init()
pygame.font.init()

from settings import SCREEN_W, SCREEN_H
from game.game import Game
from game.menu import (draw_menu, draw_pause, draw_level_complete,
                       draw_game_over)
from game.hud import draw_hud

# 主菜单
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
draw_menu(screen, 0.0)
pygame.image.save(screen, "tests/screenshots/cn_menu.png")
print("saved cn_menu.png")

# 暂停画面（先清屏模拟游戏中）
screen.fill((0, 0, 0))
draw_pause(screen)
pygame.image.save(screen, "tests/screenshots/cn_paused.png")
print("saved cn_paused.png")

# 关卡完成
screen.fill((0, 0, 0))
draw_level_complete(screen, 0, 1200, 0.0)
pygame.image.save(screen, "tests/screenshots/cn_level_complete.png")
print("saved cn_level_complete.png")

# 游戏失败
screen.fill((0, 0, 0))
draw_game_over(screen, 500, victory=False, t=0.0)
pygame.image.save(screen, "tests/screenshots/cn_gameover.png")
print("saved cn_gameover.png")

# 胜利
screen.fill((0, 0, 0))
draw_game_over(screen, 3000, victory=True, t=0.0)
pygame.image.save(screen, "tests/screenshots/cn_victory.png")
print("saved cn_victory.png")

pygame.quit()
