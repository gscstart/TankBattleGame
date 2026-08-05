"""玩家坦克。

改进点：
- 方向优先级：记录每个方向键的最后按下时间，取最近按下的方向（支持 W+D 等组合）
- 软吸附：方向切换时不会瞬间跳到格点，而是在约 50ms 内平滑移动过去
- 惯性滑行：松开方向键后，坦克继续沿最后方向移动一小段时间
"""
import pygame
from settings import Dir, PLAYER_SPEED, PLAYER_FIRE_COOLDOWN, TILE
from entities.tank import Tank
from game.input import P1_INPUT
import utils.colors as C


class PlayerTank(Tank):
    BASE_SPEED = PLAYER_SPEED
    FIRE_COOLDOWN = PLAYER_FIRE_COOLDOWN  # 0.45s
    SLIDE_DURATION = 0.10  # 松开方向键后惯性滑行时间

    def __init__(self, x, y, input_map=None):
        super().__init__(x, y, Dir.UP, C.PLAYER_COLOR, C.PLAYER_DARK)
        self.is_player = True  # 标记玩家身份
        # 玩家键位映射 (A4: 同屏双人合作时, P1/P2 各持一份 InputMap,
        # handle_event 用 is_mine 过滤事件, 1 玩家默认 P1_INPUT 兼容)
        self.input_map = input_map if input_map is not None else P1_INPUT
        self.cooldown = 0.0
        self.flashing_time = 0.0
        # 道具状态
        self.upgrade_level = 0  # 0=基础, 1=子弹加速, 2=子弹加速+破钢墙
        self.invincible = 0.0  # 剩余无敌时间
        self.frozen_enemies_timer = 0.0  # 敌人冻结剩余时间
        self.keys = {
            "up": False, "down": False, "left": False, "right": False,
            "fire": False,
        }
        # B4: 道具状态计时器 (magnet 吸引 / laser 穿透)
        self.magnet_timer = 0.0
        self.laser_timer = 0.0
        # B5: 冰面打滑 - 当前是否在冰面 TileIce 上
        self.on_ice = False
        # 各方向键最后按下的时间（用于决定"最近按下优先"）
        # 默认值 0.0：保证测试或外部设置 keys 时也能被 _active_direction 选中
        self.key_press_time = {
            "up": 0.0, "down": 0.0, "left": 0.0, "right": 0.0,
        }
        # 滑行定时器
        self.slide_timer = 0.0
        # 滑行期间使用的方向（保持最后一次有效方向）
        self.slide_dir = self.dir
        # 累计游戏时间（用于按键时间比较）
        self._time = 0.0

    def handle_event(self, event):
        """处理 KEYDOWN/KEYUP 事件。同时记录按下时间。

        A4 改造: 先用 input_map.is_mine 过滤, 自己的键才处理. 多个
        PlayerTank 各自响应自己的键, 1 玩家默认 P1_INPUT 兼容旧版.
        """
        if not self.input_map.is_mine(event.key):
            return
        if event.type == pygame.KEYDOWN:
            direction = self.input_map.direction_for(event.key)
            if direction is not None:
                self.keys[direction] = True
                self.key_press_time[direction] = self._time
            elif self.input_map.is_fire(event.key):
                self.keys["fire"] = True
        elif event.type == pygame.KEYUP:
            direction = self.input_map.direction_for(event.key)
            if direction is not None:
                self.keys[direction] = False
            elif self.input_map.is_fire(event.key):
                self.keys["fire"] = False

    def _active_direction(self):
        """返回当前应朝向的方向：最近按下的方向键。

        解决 W+D 这种组合时方向死锁的问题。
        """
        best_dir = None
        best_time = -1.0
        for name, d in (("up", Dir.UP), ("down", Dir.DOWN),
                        ("left", Dir.LEFT), ("right", Dir.RIGHT)):
            if self.keys[name] and self.key_press_time[name] > best_time:
                best_time = self.key_press_time[name]
                best_dir = d
        return best_dir

    def update(self, dt, tilemap, other_tanks, bullets, effects=None):
        if self.dead:
            return
        self._time += dt
        self.update_cooldown(dt)
        # B5: 冰面跳过吸附 (玩家保持滑动状态, 不强制对齐格点)
        # 同时清 snap_axis, 避免 on_ice 残留导致滑出冰面后无法吸附
        if not self.on_ice:
            self.update_snap(dt)
        else:
            self.snap_axis = None  # 冰面不吸附, 清残留
        # B5: 检测当前是否在冰面 TileIce 上 (用中心点)
        from world.tile import TileIce
        from settings import MAP_X, MAP_Y, GRID_W, GRID_H
        cx, cy = self.rect.centerx, self.rect.centery
        gx = (cx - MAP_X) // TILE
        gy = (cy - MAP_Y) // TILE
        if 0 <= gx < GRID_W and 0 <= gy < GRID_H:
            self.on_ice = isinstance(tilemap.tiles[gy][gx], TileIce)
        else:
            self.on_ice = False

        # 1) 决定目标方向（最近按下的方向）
        active = self._active_direction()

        # 2) 转向 + 移动 / 滑行
        if active is not None:
            # 有方向键按下：尝试转向并移动
            if self.try_change_direction(active, tilemap, other_tanks):
                self.slide_dir = self.dir
            else:
                # 转向失败（如撞墙），继续按原方向移动
                pass
            self.slide_timer = self.SLIDE_DURATION
            # 移动
            self.try_move(dt, self.dir[0] * self.speed * dt,
                          self.dir[1] * self.speed * dt,
                          tilemap, other_tanks)
        else:
            # 无方向键按下：惯性滑行
            # B5: 冰面不衰减 slide_timer, 持续滑动 (无摩擦)
            if not self.on_ice:
                self.slide_timer = max(0.0, self.slide_timer - dt)
            if self.slide_timer > 0:
                # 保持 slide_dir 朝向移动
                self.try_move(dt, self.slide_dir[0] * self.speed * dt,
                              self.slide_dir[1] * self.speed * dt,
                              tilemap, other_tanks)
            else:
                # 滑行结束，恢复对齐（吸附到格点以方便后续变向）
                if self.snap_axis is None:
                    if self.dir[0] == 0:
                        # 当前垂直移动，对齐 x
                        target = round(self.rect.x / TILE) * TILE
                        if target != self.rect.x:
                            self.snap_axis = 'x'
                            self.snap_target = target
                    else:
                        target = round(self.rect.y / TILE) * TILE
                        if target != self.rect.y:
                            self.snap_axis = 'y'
                            self.snap_target = target

        # 3) 射击（按下时只触发一次：发完即清 fire）
        if self.keys["fire"]:
            if self.can_shoot():
                self.shoot(bullets, effects=effects)
                self.keys["fire"] = False
