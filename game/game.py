"""游戏主控制器：状态机 + 主循环。"""
import pygame
import time
from settings import State, SCREEN_W, SCREEN_H, FPS, PLAYER_LIVES
from game.level import Level
from game.hud import draw_hud, get_font
from game.menu import (draw_menu, draw_pause, draw_level_complete,
                       draw_game_over, draw_highscores)
from utils import highscores
from world.levels import LEVELS


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tank Battle")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = State.MENU
        self.state_time = 0.0  # 状态持续时间
        # 关卡相关
        self.level: Level | None = None
        self.level_index = 0
        self.score = 0
        self.lives = PLAYER_LIVES
        # 玩家事件缓存（在 PLAYING 时传递给 player）
        self.events_buffer = []
        # 菜单/结束画面时间
        self.menu_t = 0.0
        # 菜单子视图：'main' / 'highscores'
        self.menu_view = 'main'
        # 通关上榜后的提示（VICTORY 状态下显示用）
        self.highscore_rank = -1  # -1 表示未上榜

    def run(self):
        last = time.time()
        while self.running:
            now = time.time()
            dt = min(0.1, now - last)  # 防止暂停后的大 dt
            last = now
            self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                # 全局：R 键重启
                if event.key == pygame.K_r and self.state == State.GAME_OVER:
                    self.restart()
                    return
            # 状态分发
            if self.state == State.MENU:
                if event.type == pygame.KEYDOWN:
                    if self.menu_view == 'main':
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.start_game()
                        elif event.key == pygame.K_h:
                            # 切到排行榜视图
                            self.menu_view = 'highscores'
                            self.menu_t = 0.0
                    elif self.menu_view == 'highscores':
                        if event.key in (pygame.K_h, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                            # 返回主菜单
                            self.menu_view = 'main'
                            self.menu_t = 0.0
            elif self.state == State.PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.state = State.PAUSED
                    self.state_time = 0.0
                    return
                if self.level and self.level.players:
                    for p in self.level.players:
                        p.handle_event(event)
            elif self.state == State.PAUSED:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.state = State.PLAYING
                    self.state_time = 0.0
            elif self.state in (State.LEVEL_COMPLETE, State.GAME_OVER, State.VICTORY):
                # 任何键在 GAME_OVER 时由 R 键处理
                pass

    def start_game(self):
        self.level_index = 0
        self.score = 0
        self.lives = PLAYER_LIVES
        self.level = Level(self.level_index, self.lives, self.score)
        self.state = State.PLAYING
        self.state_time = 0.0

    def restart(self):
        self.start_game()

    def next_level(self):
        self.level_index += 1
        if self.level_index >= len(LEVELS):
            self.state = State.VICTORY
            self.state_time = 0.0
            # 通关联机尝试上榜（B2 排行榜）
            self._record_highscore()
            return
        # 关卡完成保留当前 score 和 lives
        self.level = Level(self.level_index, self.lives, self.score)
        self.state = State.PLAYING
        self.state_time = 0.0

    def _record_highscore(self):
        """通关时尝试把分数写入排行榜。失败兜底（I/O 错误不阻塞游戏）。"""
        try:
            rank, _ = highscores.add_score(
                self.score, len(LEVELS), name="YOU"
            )
            self.highscore_rank = rank
        except OSError:
            self.highscore_rank = -1

    def update(self, dt: float):
        self.state_time += dt
        if self.state == State.MENU:
            self.menu_t += dt
            if self.menu_view == 'highscores':
                # 排行榜视图不需要 update
                pass
        elif self.state == State.PLAYING:
            if self.level:
                self.level.update(dt)
                # 同步 score 和 lives
                self.score = self.level.score
                self.lives = self.level.lives
                if self.level.completed:
                    self.score += self.level_index * 1000
                    self.state = State.LEVEL_COMPLETE
                    self.state_time = 0.0
                elif self.level.failed:
                    self.state = State.GAME_OVER
                    self.state_time = 0.0
        elif self.state == State.LEVEL_COMPLETE:
            # 2 秒后进入下一关
            if self.state_time >= 2.0:
                self.next_level()
        elif self.state == State.GAME_OVER or self.state == State.VICTORY:
            self.menu_t += dt

    def draw(self):
        if self.state == State.MENU:
            if self.menu_view == 'highscores':
                scores = highscores.load_highscores()
                draw_highscores(self.screen, scores, self.menu_t)
            else:
                draw_menu(self.screen, self.menu_t)
        else:
            # 黑色背景
            self.screen.fill((0, 0, 0))
            if self.level:
                # HUD
                enemies_left = (self.level.enemies_to_spawn
                                + len(self.level.enemies))
                draw_hud(self.screen, self.lives, self.score,
                         self.level_index, enemies_left)
                # 地图和实体
                self.level.draw(self.screen)
            # 遮罩
            if self.state == State.PAUSED:
                draw_pause(self.screen)
            elif self.state == State.LEVEL_COMPLETE:
                draw_level_complete(self.screen, self.level_index, self.score,
                                    self.state_time)
            elif self.state == State.GAME_OVER:
                draw_game_over(self.screen, self.score, victory=False, t=self.menu_t)
            elif self.state == State.VICTORY:
                draw_game_over(self.screen, self.score, victory=True, t=self.menu_t)
                # 上榜提示
                if self.highscore_rank >= 0:
                    hs_text = get_font(20).render(
                        f"恭喜上榜！第 {self.highscore_rank + 1} 名  -  H 键查看",
                        True, (255, 220, 100)
                    )
                    self.screen.blit(hs_text,
                                     (SCREEN_W // 2 - hs_text.get_width() // 2,
                                      SCREEN_H // 2 + 110))
