"""模拟玩家操作，验证完整游戏流程无崩溃。"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import random

from settings import SCREEN_W, SCREEN_H, FPS
from game.game import Game

# 手动驱动 Game（不调用 game.run()，而是模拟事件和时间）
random.seed(42)
g = Game()
g.state = "playing"  # 直接进入游戏

# 进入第 1 关
g.start_game()

# 模拟 5 秒玩家操作（每秒 60 帧）
print("Simulating 5s gameplay...")
total_frames = FPS * 5
for i in range(total_frames):
    # 模拟按键（每 30 帧切换按键）
    if i % 30 < 15:
        g.level.player.keys["up"] = True
        g.level.player.keys["left"] = False
    else:
        g.level.player.keys["up"] = False
        g.level.player.keys["left"] = True
    # 每 20 帧射击
    if i % 20 == 0:
        g.level.player.keys["fire"] = True
    else:
        g.level.player.keys["fire"] = False
    # 偶尔按 P 暂停/恢复
    if i == 100:
        # 模拟 P 键（手动切到暂停）
        g.state = "paused"
    if i == 120:
        g.state = "playing"
    # 推进 1 帧
    g.update(1.0 / FPS)
    g.draw()
    pygame.display.flip()

# 保存截图
pygame.image.save(g.screen, "screenshot_level1.png")
print(f"Saved screenshot_level1.png ({SCREEN_W}x{SCREEN_H})")
print(f"After 5s: score={g.score}, lives={g.lives}, enemies_left={g.level.enemies_to_spawn + len(g.level.enemies)}")
print(f"  state={g.state}, level_index={g.level_index}")
print(f"  player pos={g.level.player.rect.x}, {g.level.player.rect.y}, dir={g.level.player.dir}")
print(f"  bullets={len(g.level.bullets)}, enemies={len(g.level.enemies)}")

# 截一张菜单图
g.state = "menu"
g.menu_t = 0.5
g.draw()
pygame.image.save(g.screen, "screenshot_menu.png")
print("Saved screenshot_menu.png")

# 截一张暂停图
g.start_game()
g.update(0.1)
g.state = "paused"
g.draw()
pygame.image.save(g.screen, "screenshot_paused.png")
print("Saved screenshot_paused.png")

# 截一张 GAME OVER 图
g.state = "game_over"
g.menu_t = 1.0
g.draw()
pygame.image.save(g.screen, "screenshot_gameover.png")
print("Saved screenshot_gameover.png")

# 截一张胜利图
g.state = "victory"
g.menu_t = 0.5
g.draw()
pygame.image.save(g.screen, "screenshot_victory.png")
print("Saved screenshot_victory.png")

print("\nAll gameplay simulation completed without crash")
pygame.quit()
