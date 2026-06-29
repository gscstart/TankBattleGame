"""关卡管理器：装弹、生成敌人、追踪进度。

升级：
- 根据 level_index 读取 LEVEL_DIFFICULTY 配置
- 死亡震屏
- 死亡重生提示
- shovel 状态机
"""
import random
import pygame
from settings import RESPAWN_INVULN, MAP_X, MAP_Y, TILE, SCORE_PER_ENEMY
from world.tilemap import TileMap
from world.levels import get_level, get_level_difficulty
from entities.player import PlayerTank
from entities.enemy import EnemyTank
from utils import events


# 每个道具拾取时播放的音效（语义匹配）
POWERUP_SOUND = {
    "star":    "start",     # 升级 - 上行扫频
    "grenade": "explosion", # 全屏爆炸
    "helmet":  "hit",       # 防御 - 短促咔哒
    "clock":   "start",     # 冻结 - 钟形包络
    "shovel":  "hit",       # 加固 - 短促咔哒
    "tank":    "start",     # 加命 - 上行扫频
}


class Level:
    """单个关卡的运行状态。"""

    def __init__(self, level_index: int, lives: int, score: int):
        self.index = level_index
        self.lives = lives
        self.score = score
        # 读取关卡难度配置
        self.config = get_level_difficulty(level_index)
        self.tilemap = TileMap.from_layout(get_level(level_index))
        self.players = [self._spawn_player()]
        self.bullets = []
        self.enemies = []
        self.effects = []
        self.powerups = []  # 道具
        self.enemies_killed = 0
        self.enemies_to_spawn = self.config["enemy_count"]
        self._spawn_timer = 0.0
        self._spawn_idx = 0
        self.completed = False
        self.failed = False
        # 视觉反馈状态
        self.screen_shake_time = 0.0
        # Shovel 机制：保存原始砖块位置，用于结束恢复
        self._shovel_backup = None

    def _spawn_player(self):
        col, row = self.tilemap.player_spawn
        x, y = self.tilemap.grid_to_world(col, row)
        player = PlayerTank(x, y)
        player.flashing_time = RESPAWN_INVULN
        return player

    def _spawn_enemy(self):
        if self.enemies_to_spawn <= 0:
            return None
        if len(self.enemies) >= self.config["max_on_screen"]:
            return None
        for i in range(3):
            idx = (self._spawn_idx + i) % 3
            if idx >= len(self.tilemap.enemy_spawns):
                continue
            col, row = self.tilemap.enemy_spawns[idx]
            x, y = self.tilemap.grid_to_world(col, row)
            spawn_rect = pygame.Rect(x, y, TILE, TILE)
            for e in self.enemies:
                if e.dead:  # 尸体不算占用
                    continue
                if spawn_rect.colliderect(e.rect):
                    break
            else:
                if not spawn_rect.colliderect(self.players[0].rect):
                    tier = (self.enemies_killed) % 3
                    enemy = EnemyTank(x, y, tier=tier,
                                      enemy_speed=self.config["enemy_speed"])
                    self.enemies.append(enemy)
                    self.enemies_to_spawn -= 1
                    self._spawn_idx = (idx + 1) % 3
                    return enemy
        return None

    def respawn_player(self):
        if self.lives <= 0:
            self._fail(events.REASON_LIVES_ZERO)
            return
        col, row = self.tilemap.player_spawn
        x, y = self.tilemap.grid_to_world(col, row)
        # 保留道具状态再重生
        old = self.players[0]
        self.players = [PlayerTank(x, y)]
        self.players[0].flashing_time = RESPAWN_INVULN
        # 继承旧玩家的道具/状态
        self.players[0].upgrade_level = old.upgrade_level
        self.players[0].invincible = max(0.0, old.invincible - 1.0)  # 重生减 1s
        self.players[0].frozen_enemies_timer = old.frozen_enemies_timer
        # 恢复 shovel 状态
        self._restore_shovel()

    def _fail(self, reason: str):
        """统一失败入口: 同时发 LEVEL_FAILED 事件 + 设 self.failed 标志。"""
        events.publish(events.LEVEL_FAILED, reason=reason)
        self.failed = True

    def base_destroyed(self):
        self._fail(events.REASON_BASE_DESTROYED)

    def update(self, dt: float):
        if self.completed or self.failed:
            return

        # 屏幕震屏计时
        if self.screen_shake_time > 0:
            self.screen_shake_time -= dt

        # Shovel 倒计时
        if getattr(self, "_shovel_timer", 0.0) > 0:
            self._shovel_timer -= dt
            if self._shovel_timer <= 0:
                self._restore_shovel()

        # 敌人生成
        self._spawn_timer -= dt
        if self._spawn_timer <= 0:
            spawned = self._spawn_enemy()
            if spawned is None and self.enemies_to_spawn > 0:
                self._spawn_timer = 0.2
            else:
                self._spawn_timer = self.config["spawn_interval"]

        # 玩家
        if not self.players[0].dead:
            other_tanks = [e for e in self.enemies if not e.dead]
            self.players[0].update(dt, self.tilemap, other_tanks, self.bullets,
                               effects=self.effects)
        else:
            self.players[0].update_cooldown(dt)
            if not hasattr(self, "_death_timer"):
                self._death_timer = 1.0
                # 玩家死亡首帧 publish (供成就/回放订阅)
                events.publish(events.ENTITY_KILLED, kind="player", owner="enemy",
                               x=self.players[0].rect.centerx,
                               y=self.players[0].rect.centery,
                               score_delta=0)
            self._death_timer -= dt
            if self._death_timer <= 0:
                self.lives -= 1
                if self.lives > 0:
                    self.respawn_player()
                else:
                    self._fail(events.REASON_LIVES_ZERO)
                if hasattr(self, "_death_timer"):
                    del self._death_timer

        # 玩家道具状态计时
        if not self.players[0].dead:
            if self.players[0].invincible > 0:
                self.players[0].invincible -= dt
            if self.players[0].frozen_enemies_timer > 0:
                self.players[0].frozen_enemies_timer -= dt
                # 冻结所有敌人
                for e in self.enemies:
                    e.frozen = True
            else:
                for e in self.enemies:
                    e.frozen = False

        # 敌人
        other_tanks = []
        if not self.players[0].dead:
            other_tanks.extend(self.players)
        # 基地位置（用于 AI 瞄准）
        base_pos = None
        if self.tilemap.base_tile and not self.tilemap.base_tile.destroyed:
            bc, br = self.tilemap.base_pos
            base_pos = (MAP_X + bc * TILE + TILE // 2,
                        MAP_Y + br * TILE + TILE // 2)
        # 敌人瞄准优先级：基地生命值低时倾向打基地
        priority = "base" if self.tilemap.base_tile and \
            not self.tilemap.base_tile.destroyed and random.random() < 0.4 else "player"
        for e in self.enemies:
            if e.dead:
                continue
            e.update(dt, self.tilemap, other_tanks, self.bullets, self.players[0],
                     effects=self.effects, base_pos=base_pos,
                     target_priority=priority)

        # 子弹
        for b in self.bullets:
            b.update(dt, self.tilemap, self.bullets,
                     self.players + self.enemies,
                     self._on_base_hit, effects=self.effects)

        # 清理死亡
        self.bullets = [b for b in self.bullets if not b.dead]
        newly_dead_enemies = [e for e in self.enemies if e.dead]
        if newly_dead_enemies:
            self.enemies = [e for e in self.enemies if not e.dead]
            for e in newly_dead_enemies:
                # 道具击杀的敌人不计分（已在 _apply_powerup 中加过），但仍掉落道具
                if not e.killed_by_powerup:
                    self.score += SCORE_PER_ENEMY
                    self.enemies_killed += 1
                    events.publish(events.ENTITY_KILLED, kind="enemy", owner="player",
                                   x=e.rect.centerx, y=e.rect.centery, score_delta=SCORE_PER_ENEMY)
                # 25% 概率掉落道具
                if random.random() < 0.25:
                    from entities.powerup import spawn_random_powerup
                    pu = spawn_random_powerup(e.rect.centerx - TILE // 2, e.rect.centery - TILE // 2)
                    self.powerups.append(pu)

        # 道具
        for pu in self.powerups:
            pu.update(dt)
            # 检测玩家拾取
            if not self.players[0].dead and pu.rect.colliderect(self.players[0].rect):
                self._apply_powerup(pu)
                events.publish(events.POWERUP_PICKED, type=pu.type,
                               x=pu.rect.centerx, y=pu.rect.centery)
                pu.dead = True
        self.powerups = [pu for pu in self.powerups if not pu.dead]

        # 特效
        for fx in self.effects:
            fx.update(dt)
        self.effects = [fx for fx in self.effects if not fx.dead]

        # 基地
        if self.tilemap.base_tile and self.tilemap.base_tile.destroyed:
            events.publish(events.BASE_DESTROYED)
            self._fail(events.REASON_BASE_DESTROYED)

        # 通关
        if self.enemies_to_spawn <= 0 and len(self.enemies) == 0 and not self.failed:
            events.publish(events.LEVEL_COMPLETED, score=self.score, level_index=self.index)
            self.completed = True

    def _apply_powerup(self, pu):
        """道具效果分发。"""
        from entities.effects import MuzzleFlash
        from utils.sound import play
        p = self.players[0]
        if pu.type == "star":
            # 升级（最多 2 级）
            p.upgrade_level = min(2, p.upgrade_level + 1)
        elif pu.type == "grenade":
            # 全屏敌人立即死亡（标记 killed_by_powerup 避免下帧重复计分）
            count = 0
            for e in self.enemies:
                if not e.dead:
                    e.dead = True
                    e.killed_by_powerup = True
                    e.hit_flash_time = 0.3
                    self.effects.append(MuzzleFlash(e.rect.centerx, e.rect.centery,
                                                    (0, 0), (255, 200, 100)))
                    events.publish(events.ENTITY_KILLED, kind="enemy", owner="powerup",
                                   x=e.rect.centerx, y=e.rect.centery, score_delta=SCORE_PER_ENEMY)
                    count += 1
            self.score += count * SCORE_PER_ENEMY
        elif pu.type == "helmet":
            # 10s 无敌
            p.invincible = 10.0
        elif pu.type == "clock":
            # 8s 敌人冻结
            p.frozen_enemies_timer = 8.0
        elif pu.type == "shovel":
            # 15s 基地砖墙变钢墙
            self._activate_shovel(15.0)
        elif pu.type == "tank":
            # +1 命
            self.lives += 1
        # 每个道具播放不同音效
        play(POWERUP_SOUND.get(pu.type, "hit"))

    def _activate_shovel(self, duration: float):
        """将基地周围 8 格砖块临时变为钢墙。"""
        from world.tile import TileSteel
        from settings import GRID_W, GRID_H
        if not self.tilemap.base_tile:
            return
        bx, by = self.tilemap.base_pos
        # 仅第一次激活时备份原始瓦片（保留首次的砖块供恢复）
        if self._shovel_backup is None:
            backup = {}
            for dc, dr in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
                c, r = bx + dc, by + dr
                if 0 <= r < GRID_H and 0 <= c < GRID_W:
                    backup[(c, r)] = self.tilemap.tiles[r][c]
            self._shovel_backup = backup
        # 替换为钢墙
        for c, r in self._shovel_backup:
            if 0 <= r < GRID_H and 0 <= c < GRID_W:
                self.tilemap.tiles[r][c] = TileSteel()
        # 倒计时
        self._shovel_timer = duration

    def _restore_shovel(self):
        """恢复 shovel 备份。"""
        from settings import GRID_W, GRID_H
        if self._shovel_backup is not None:
            for (c, r), tile in self._shovel_backup.items():
                if 0 <= r < GRID_H and 0 <= c < GRID_W:
                    self.tilemap.tiles[r][c] = tile
            self._shovel_backup = None
            self._shovel_timer = 0.0

    def _on_base_hit(self, tile):
        # 基地被命中时震屏
        self.screen_shake_time = 0.3
        from utils.sound import play
        play("explosion")
        events.publish(events.BASE_HIT)

    # ---- 渲染 ----
    def draw(self, surface: pygame.Surface):
        # 震屏偏移
        ox, oy = 0, 0
        if self.screen_shake_time > 0:
            import random
            ox = random.randint(-2, 2)
            oy = random.randint(-2, 2)
        # 画到临时 surface 以支持偏移
        if ox or oy:
            tmp = pygame.Surface(surface.get_size())
            self._draw_scene(tmp)
            surface.blit(tmp, (ox, oy))
        else:
            self._draw_scene(surface)

    def _draw_scene(self, surface):
        self.tilemap.draw(surface)
        for e in self.enemies:
            e.draw(surface)
        if not self.players[0].dead:
            self.players[0].draw(surface)
        for b in self.bullets:
            b.draw(surface)
        # 道具在实体之上、草丛之下
        for pu in self.powerups:
            pu.draw(surface)
        # 特效在最上层
        for fx in self.effects:
            fx.draw(surface)
        # 死亡重生提示
        if self.players[0].dead and hasattr(self, "_death_timer"):
            from game.hud import get_font
            font = get_font(28, True)
            text = font.render("准备重生...", True, (255, 200, 80))
            surface.blit(text, (surface.get_width() // 2 - text.get_width() // 2,
                                surface.get_height() // 2 + 30))
        # 玩家道具状态指示器
        if not self.players[0].dead and self.players[0].invincible > 0:
            from game.hud import get_font
            font = get_font(16, True)
            t = f"无敌 {self.players[0].invincible:.1f}s"
            text = font.render(t, True, (200, 230, 255))
            surface.blit(text, (self.players[0].rect.x - 10, self.players[0].rect.y - 22))
        # 草丛
        self.tilemap.draw_foreground(surface)
