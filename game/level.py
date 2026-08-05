"""关卡管理器：装弹、生成敌人、追踪进度。

升级：
- 根据 level_index 读取 LEVEL_DIFFICULTY 配置
- 死亡震屏
- 死亡重生提示
- shovel 状态机
"""
import random
import pygame
from settings import (RESPAWN_INVULN, MAP_X, MAP_Y, TILE, SCORE_PER_ENEMY,
                     PLAYER_LIVES, GRID_W, GRID_H)
from settings import MAGNET_DURATION, LASER_DURATION, MINE_COUNT
from settings import SPECIAL_ENEMY_CHANCE
from world.tilemap import TileMap
from world.levels import get_level, get_level_difficulty
from entities.player import PlayerTank
from entities.enemy import EnemyTank
from entities.boss import BossTank
from game.input import P1_INPUT, P2_INPUT
from game.hud import get_font
from utils import events
from utils.sound import play


# 每个道具拾取时播放的音效（语义匹配）
POWERUP_SOUND = {
    "star":    "start",     # 升级 - 上行扫频
    "grenade": "explosion", # 全屏爆炸
    "helmet":  "hit",       # 防御 - 短促咔哒
    "clock":   "start",     # 冻结 - 钟形包络
    "shovel":  "hit",       # 加固 - 短促咔哒
    "tank":    "start",     # 加命 - 上行扫频
    # B4: 3 个新道具
    "magnet":  "start",     # 磁铁 - 上行扫频 (吸引)
    "laser":   "hit",       # 激光 - 短促咔哒 (激活)
    "mine":    "hit",       # 地雷 - 咔哒 (放置)
}


class Level:
    """单个关卡的运行状态。

    C1 改造: 玩家改为 list[PlayerTank], 共享基地, 独立生命.
    self.lives 保留为汇总 (用于 Game.score/lives 显示),
    每玩家各自维护 .lives 属性.
    """

    def __init__(self, level_index: int, lives: int, score: int, num_players: int = 1,
                 achievements=None):
        self.index = level_index
        # 玩家生命用 list 维护: 每玩家 3 命, 独立计数
        # lives 参数保留向后兼容 (campaign 模式 1 玩家时 = PLAYER_LIVES)
        self.lives = lives  # 汇总 (用于 HUD 显示: P1 命数)
        self.num_players = num_players
        self.score = score
        # 读取关卡难度配置
        self.config = get_level_difficulty(level_index)
        # 模式：'campaign'（默认 6 关） 或 'survival'（无尽波次）
        self.mode = self.config.get("mode", "campaign")
        # C5: 成就管理器 (可选, 不传则不处理)
        self.achievements = achievements
        if self.achievements is not None:
            self.achievements.on_level_start(self.mode)
        self.tilemap = TileMap.from_layout(get_level(level_index))
        # C1: 创建 num_players 个玩家, P1/P2 用各自 InputMap
        # 用循环 (而不是 list comprehension) 因为 _spawn_player(1) 需要 self.players[0]
        input_maps = [P1_INPUT, P2_INPUT]
        self.players = []
        for i in range(num_players):
            im = input_maps[i] if i < len(input_maps) else P1_INPUT
            self.players.append(self._spawn_player(i, im))
        self.bullets = []
        self.enemies = []
        self.effects = []
        self.powerups = []  # 道具
        self.mines = []  # B4: 地雷
        self.enemies_killed = 0
        # survival: 无限生成；campaign: 限总敌人数；boss: 不生成普通敌人 (BOSS 自己)
        if self.mode == "survival":
            self.enemies_to_spawn = float("inf")
            self.survival_waves = 0  # 已生成的总波次（每次 _spawn_enemy 算 +1 击杀点）
        elif self.mode == "boss":
            self.enemies_to_spawn = 0  # BOSS 关不生成普通敌人
        else:
            self.enemies_to_spawn = self.config["enemy_count"]
        self._spawn_timer = 0.0
        self._spawn_idx = 0
        self.completed = False
        self.failed = False
        # 视觉反馈状态
        self.screen_shake_time = 0.0
        # Shovel 机制：保存原始砖块位置，用于结束恢复
        self._shovel_backup = None
        # C2: BOSS 关卡 - 在 (8, 7) 中央 spawn BossTank (5x5 BOSS 房间)
        if self.mode == "boss":
            boss_x, boss_y = self.tilemap.grid_to_world(8, 7)
            boss = BossTank(boss_x, boss_y)
            self.enemies.append(boss)

    def _spawn_player(self, index: int = 0, input_map=None):
        """index: 0=P1 默认出生点, 1=P2 在 P1 旁边找不重叠位置. input_map: 该玩家键位.

        P2 位置: 4 方向 (左/右/上/下) 尝试, 默认退到 (col, row+1) 下方.
        极端 P1 在 col=0/GRID_W-1 时 '左侧' 越界时退化, 用其他方向.
        """
        from game.input import P1_INPUT
        from settings import GRID_W, GRID_H
        col, row = self.tilemap.player_spawn
        if index == 1:
            # P2 找与 P0 不重叠的最近位置
            p0 = self.players[0] if self.players else None
            offsets = [(-2, 0), (2, 0), (0, -1), (0, 1), (-2, -1), (2, 1), (-2, 1), (2, -1)]
            chosen = None
            for dc, dr in offsets:
                nc, nr = col + dc, row + dr
                if not (0 <= nc < GRID_W and 0 <= nr < GRID_H):
                    continue
                # 检查是否与 P0 重叠
                x_test, y_test = self.tilemap.grid_to_world(nc, nr)
                test_rect = pygame.Rect(x_test, y_test, TILE, TILE)
                if p0 is None or not test_rect.colliderect(p0.rect):
                    chosen = (nc, nr)
                    break
            if chosen is None:
                # 兜底: 直接在 P1 下方一格 (越界时夹到 grid 内)
                chosen = (col, min(GRID_H - 1, row + 1))
            col, row = chosen
        x, y = self.tilemap.grid_to_world(col, row)
        player = PlayerTank(x, y, input_map=input_map or P1_INPUT)
        player.flashing_time = RESPAWN_INVULN
        # C1: 每玩家独立生命
        player.lives = PLAYER_LIVES
        # 玩家身份标号 (1-based, 给 HUD 用)
        player.player_id = index + 1
        return player

    def _spawn_enemy(self):
        if self.mode != "survival" and self.enemies_to_spawn <= 0:
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
                # 不与任何存活玩家重叠
                blocked = any(
                    not p.dead and spawn_rect.colliderect(p.rect)
                    for p in self.players
                )
                if not blocked:
                    tier = (self.enemies_killed) % 3
                    # C3: 普通 vs 特殊敌人 (campaign 模式才生成特殊)
                    if self.mode == "campaign" and random.random() < SPECIAL_ENEMY_CHANCE:
                        from entities.special import SPECIAL_ENEMY_CLASSES
                        cls = random.choice(SPECIAL_ENEMY_CLASSES)
                        enemy = cls(x, y, tier=tier,
                                    enemy_speed=self.config["enemy_speed"],
                                    is_powerup_carrier=False)
                    else:
                        enemy = EnemyTank(x, y, tier=tier,
                                          enemy_speed=self.config["enemy_speed"])
                    self.enemies.append(enemy)
                    if self.mode == "survival":
                        self.survival_waves += 1
                    else:
                        self.enemies_to_spawn -= 1
                    self._spawn_idx = (idx + 1) % 3
                    return enemy
        return None

    def respawn_player(self, index: int = 0):
        """index: 重生哪个玩家 (0=P1, 1=P2). C1: 独立生命, 只重生自己.

        命用完时记入 _perm_dead, update 跳过, 避免 ENTITY_KILLED 重复发布.
        """
        old = self.players[index]
        if old.lives <= 0:
            # 该玩家命用完, 永久死亡, 不再 publish
            if not hasattr(self, "_perm_dead"):
                self._perm_dead = set()
            self._perm_dead.add(index)
            death_attr = f"_death_timer_p{index}"
            if hasattr(self, death_attr):
                delattr(self, death_attr)
            return
        old.lives -= 1
        if old.lives < 0:
            old.lives = 0
        # 创建新 PlayerTank 在原出生点, 保留 input_map 和 player_id
        col, row = self.tilemap.player_spawn
        if index == 1:
            col = max(0, col - 2)
        x, y = self.tilemap.grid_to_world(col, row)
        new_player = PlayerTank(x, y, input_map=old.input_map)
        new_player.flashing_time = RESPAWN_INVULN
        new_player.lives = old.lives
        new_player.player_id = old.player_id
        # 继承旧玩家的道具/状态
        new_player.upgrade_level = old.upgrade_level
        new_player.invincible = max(0.0, old.invincible - 1.0)  # 重生减 1s
        new_player.frozen_enemies_timer = old.frozen_enemies_timer
        self.players[index] = new_player
        # 同步 self.lives (汇总, 用于 HUD)
        self.lives = self.players[0].lives
        # 注意: 不调 _restore_shovel() - 重生时 shovel 状态应保留
        # (shovel 由 _shovel_timer 自然到期恢复, 不应被重生流程打断)

    def _fail(self, reason: str):
        """统一失败入口: 同时发 LEVEL_FAILED 事件 + 设 self.failed 标志。"""
        events.publish(events.LEVEL_FAILED, reason=reason)
        self.failed = True

    def _all_players_dead(self) -> bool:
        """C1: 所有玩家都耗尽生命 (lives <= 0)."""
        return all(getattr(p, 'lives', 0) <= 0 for p in self.players)

    def _get_magnet_target(self) -> tuple | None:
        """B4: 若任一玩家有 magnet 激活中, 返回其中心 (cx, cy) 给 powerup.update 吸引.

        多个玩家激活时取最近存活玩家 (避免道具在两个玩家之间反复横跳).
        """
        alive = [p for p in self.players if not p.dead and getattr(p, 'magnet_timer', 0.0) > 0.0]
        if not alive:
            return None
        # 道具中心假设在 powerups 平均位置, 简化: 第一个玩家
        return alive[0].rect.center

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

        # 敌人生成 (boss 模式: BOSS 已 spawn 在 __init__, 不再生)
        if self.mode != "boss":
            self._spawn_timer -= dt
            if self._spawn_timer <= 0:
                spawned = self._spawn_enemy()
                if spawned is None and self.enemies_to_spawn > 0:
                    self._spawn_timer = 0.2
                else:
                    self._spawn_timer = self.config["spawn_interval"]

        # 玩家 (C1: 多玩家独立 update / 重生 / 失败检查)
        # 收集所有存活玩家作为 other_tanks (敌人不会穿过玩家)
        other_tanks = [e for e in self.enemies if not e.dead]
        perm_dead = getattr(self, "_perm_dead", set())
        for idx, p in enumerate(self.players):
            if idx in perm_dead:
                # 永久死亡玩家: 跳过 (避免重复 publish ENTITY_KILLED)
                continue
            if not p.dead:
                # other_tanks 中排除自己和死亡玩家
                p_others = [t for t in (other_tanks + self.players) if t is not p and not t.dead]
                p.update(dt, self.tilemap, p_others, self.bullets, effects=self.effects)
            else:
                p.update_cooldown(dt)
                death_attr = f"_death_timer_p{idx}"
                if not hasattr(self, death_attr):
                    setattr(self, death_attr, 1.0)
                    events.publish(events.ENTITY_KILLED, kind="player", owner="enemy",
                                   x=p.rect.centerx, y=p.rect.centery,
                                   score_delta=0, player_id=idx + 1)
                timer = getattr(self, death_attr) - dt
                if timer <= 0:
                    self.respawn_player(idx)
                    if hasattr(self, death_attr):
                        delattr(self, death_attr)
                else:
                    setattr(self, death_attr, timer)
        # 所有玩家都死 + 基地未毁 = _fail
        if self._all_players_dead() and not self.failed:
            self._fail(events.REASON_LIVES_ZERO)

        # 玩家道具状态计时 (取任一存活玩家的 frozen 状态)
        any_player_alive = any(not p.dead for p in self.players)
        if any_player_alive:
            # 冻结状态: 任一玩家激活就生效
            max_frozen = max((p.frozen_enemies_timer for p in self.players if not p.dead), default=0.0)
            for p in self.players:
                if not p.dead:
                    if p.invincible > 0:
                        p.invincible -= dt
                    # B4: magnet 倒计时
                    if getattr(p, 'magnet_timer', 0.0) > 0:
                        p.magnet_timer = max(0.0, p.magnet_timer - dt)
                    # B4: laser 倒计时
                    if getattr(p, 'laser_timer', 0.0) > 0:
                        p.laser_timer = max(0.0, p.laser_timer - dt)
            if max_frozen > 0:
                for p in self.players:
                    if not p.dead:
                        p.frozen_enemies_timer = max(0.0, p.frozen_enemies_timer - dt)
                for e in self.enemies:
                    e.frozen = True
            else:
                for e in self.enemies:
                    e.frozen = False

        # 敌人
        other_tanks = []
        for p in self.players:
            if not p.dead:
                other_tanks.append(p)
        # 基地位置（用于 AI 瞄准）
        base_pos = None
        if self.tilemap.base_tile and not self.tilemap.base_tile.destroyed:
            bc, br = self.tilemap.base_pos
            base_pos = (MAP_X + bc * TILE + TILE // 2,
                        MAP_Y + br * TILE + TILE // 2)
        # 敌人瞄准优先级：基地生命值低时倾向打基地
        priority = "base" if self.tilemap.base_tile and \
            not self.tilemap.base_tile.destroyed and random.random() < 0.4 else "player"
        # AI 目标: 选最近存活玩家
        alive_players = [p for p in self.players if not p.dead]
        ai_target = alive_players[0] if alive_players else None
        for e in self.enemies:
            if e.dead:
                continue
            e.update(dt, self.tilemap, other_tanks, self.bullets, ai_target,
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
                    # C5: BOSS 死时标记 is_boss=True 给成就系统
                    is_boss = isinstance(e, BossTank)
                    events.publish(events.ENTITY_KILLED, kind="enemy", owner="player",
                                   x=e.rect.centerx, y=e.rect.centery,
                                   score_delta=SCORE_PER_ENEMY,
                                   is_powerup_carrier=e.is_powerup_carrier,
                                   is_boss=is_boss)
                # 红闪敌人 100% 掉道具，普通敌人 25% 掉
                if e.is_powerup_carrier or random.random() < 0.25:
                    from entities.powerup import spawn_random_powerup
                    pu = spawn_random_powerup(e.rect.centerx - TILE // 2, e.rect.centery - TILE // 2)
                    self.powerups.append(pu)

        # 道具
        # B4: magnet 激活时所有道具飞向最近存活玩家
        magnet_target = self._get_magnet_target()
        for pu in self.powerups:
            pu.update(dt, magnet_target=magnet_target)
            # C1: 任一存活玩家拾取都生效, 按距离最近玩家分发效果
            for p in self.players:
                if not p.dead and pu.rect.colliderect(p.rect):
                    self._apply_powerup(pu, target_idx=self.players.index(p))
                    events.publish(events.POWERUP_PICKED, type=pu.type,
                                   x=pu.rect.centerx, y=pu.rect.centery,
                                   player_id=p.player_id)
                    pu.dead = True
                    break
        self.powerups = [pu for pu in self.powerups if not pu.dead]

        # B4: 地雷
        mine_kills = 0
        for mine in self.mines:
            mine_kills += mine.update(dt, self.enemies, self.effects, events)
        self.mines = [m for m in self.mines if not m.dead]
        # mine 击杀加分 (与 grenade 一致, killed_by_powerup=True 跳过下帧重复计分)
        if mine_kills > 0:
            self.score += mine_kills * SCORE_PER_ENEMY

        # 特效
        for fx in self.effects:
            fx.update(dt)
        self.effects = [fx for fx in self.effects if not fx.dead]

        # 基地
        if self.tilemap.base_tile and self.tilemap.base_tile.destroyed:
            if not self.failed:
                events.publish(events.BASE_DESTROYED)
                self._fail(events.REASON_BASE_DESTROYED)

        # C5: 成就系统 - 每帧 tick (survival 计时); events 已被 Manager 订阅
        if self.achievements is not None:
            self.achievements.on_level_tick(dt, self.mode)

        # 通关条件:
        # - campaign: enemies_to_spawn 用完 + 无存活敌人
        # - survival: 永不自然 completed (用 _fail)
        # - boss (C2): 所有 BOSS 都死 (BOSS 全 dead + 清理死 enemies)
        if not self.failed and not self.completed:
            if self.mode == "boss":
                # BOSS 关: 所有 BossTank 都死才 completed
                boss_alive = any(
                    isinstance(e, BossTank) and not e.dead
                    for e in self.enemies
                )
                if not boss_alive:
                    # 清理死敌人 (避免 enemies 列表残留 dead BOSS, 影响 HUD enemies_left)
                    self.enemies = [e for e in self.enemies if not e.dead]
                    events.publish(events.LEVEL_COMPLETED, score=self.score,
                                   level_index=self.index)
                    self.completed = True
            elif self.enemies_to_spawn <= 0 and len(self.enemies) == 0:
                events.publish(events.LEVEL_COMPLETED, score=self.score,
                               level_index=self.index)
                self.completed = True

    def _apply_powerup(self, pu, target_idx: int = 0):
        """道具效果分发。C1: target_idx 决定哪个玩家受益 (按距离最近)."""
        from entities.effects import MuzzleFlash
        from utils.sound import play
        # target_idx 越界兜底
        if target_idx < 0 or target_idx >= len(self.players):
            target_idx = 0
        p = self.players[target_idx]
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
            # +1 命 (C1: 加给 target 玩家)
            p.lives = getattr(p, 'lives', PLAYER_LIVES) + 1
            if target_idx == 0:
                self.lives = p.lives
        elif pu.type == "magnet":
            # B4: 8s 内磁铁吸引所有道具向玩家飞
            p.magnet_timer = MAGNET_DURATION
        elif pu.type == "laser":
            # B4: 10s 内玩家子弹穿透敌人
            p.laser_timer = LASER_DURATION
        elif pu.type == "mine":
            # B4: 在玩家位置前/中/后放 3 颗地雷
            from entities.mine import spawn_mines_around
            self.mines.extend(spawn_mines_around(p, count=MINE_COUNT))
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
        if self._shovel_backup is not None:
            for (c, r), tile in self._shovel_backup.items():
                if 0 <= r < GRID_H and 0 <= c < GRID_W:
                    self.tilemap.tiles[r][c] = tile
            self._shovel_backup = None
            self._shovel_timer = 0.0

    def _on_base_hit(self, tile):
        # 基地被命中时震屏
        self.screen_shake_time = 0.3
        play("explosion")
        events.publish(events.BASE_HIT)

    # ---- 渲染 ----
    def draw(self, surface: pygame.Surface):
        # 震屏偏移
        ox, oy = 0, 0
        if self.screen_shake_time > 0:
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
        # C1: 画所有存活玩家
        for p in self.players:
            if not p.dead:
                p.draw(surface)
        for b in self.bullets:
            b.draw(surface)
        # 道具在实体之上、草丛之下
        for pu in self.powerups:
            pu.draw(surface)
        # B4: 地雷在玩家之前画 (避免被玩家遮住)
        for mine in self.mines:
            mine.draw(surface)
        # 特效在最上层
        for fx in self.effects:
            fx.draw(surface)
        # C1: 死亡重生提示 (任一玩家)
        for idx, p in enumerate(self.players):
            if p.dead and hasattr(self, f"_death_timer_p{idx}"):
                font = get_font(20, True)
                tag = f"P{idx + 1}"
                text = font.render(f"{tag} 准备重生...", True, (255, 200, 80))
                surface.blit(text, (surface.get_width() // 2 - text.get_width() // 2,
                                    surface.get_height() // 2 + 20 + idx * 26))
        # C1: 玩家道具状态指示器 (任一存活玩家)
        for p in self.players:
            if not p.dead and p.invincible > 0:
                font = get_font(14, True)
                t = f"无敌 {p.invincible:.1f}s"
                text = font.render(t, True, (200, 230, 255))
                surface.blit(text, (p.rect.x - 6, p.rect.y - 18))
        # 草丛
        self.tilemap.draw_foreground(surface)
