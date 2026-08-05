"""背景音乐 (F20 - 路线图 §6 阶段 D).

设计原则 (按 karpathy Simplicity):
- 不携带音乐文件 (规避版权)
- 程序生成 8-bit chiptune 风格 BGM (numpy 合成方波 + 短 ADSR)
- 3 段: menu (轻松 C 大调) / game (紧张 A 小调) / victory (欢快 C 大调)
- MusicManager 控制 play/stop/pause/resume + state 切换

依赖: numpy (声音生成), pygame.mixer (回放)
"""
import numpy as np
import pygame
import math

from settings import MUSIC_SAMPLE_RATE, MUSIC_VOLUME, MUSIC_ENABLED


# ---- 音符频率表 (等程, A4=440Hz) ----
# 12-TET: f = 440 * 2^((n-69)/12)  (n = MIDI 编号)
# 这里直接给出常用八度的频率 Hz
NOTE_FREQ = {
    "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00, "A3": 220.00, "B3": 246.94,
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77,
    "REST": 0.0,
}


# ---- 合成辅助 ----
def _square_wave(freq: float, duration: float) -> np.ndarray:
    """生成方波. freq=0 (REST) 返回静音."""
    n = int(MUSIC_SAMPLE_RATE * duration)
    if n <= 0 or freq <= 0:
        return np.zeros(n, dtype=np.int16)
    t = np.arange(n) / MUSIC_SAMPLE_RATE
    # 方波: sign(sin)
    wave = np.sign(np.sin(2 * np.pi * freq * t)).astype(np.int16)
    return wave


def _adsr_envelope(duration: float, attack: float = 0.01,
                   decay: float = 0.05, sustain_level: float = 0.7) -> np.ndarray:
    """ADSR 包络 (简化: A+D+S+R)."""
    n = int(MUSIC_SAMPLE_RATE * duration)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    a_n = int(MUSIC_SAMPLE_RATE * attack)
    d_n = int(MUSIC_SAMPLE_RATE * decay)
    r_n = n - a_n - d_n
    if r_n < 0:
        r_n = 0
    env = np.zeros(n, dtype=np.float32)
    # Attack: 0 -> 1
    if a_n > 0:
        env[:a_n] = np.linspace(0, 1, a_n)
    # Decay: 1 -> sustain_level
    if d_n > 0:
        env[a_n:a_n + d_n] = np.linspace(1, sustain_level, d_n)
    # Sustain: sustain_level -> 0 (缓慢衰减)
    if r_n > 0:
        env[a_n + d_n:] = np.linspace(sustain_level, 0, r_n) ** 0.7
    return env


def _note_freq(note_name: str) -> float:
    """查表 (e.g. 'C4' -> 261.63). 未知返回 0 (rest)."""
    return NOTE_FREQ.get(note_name, 0.0)


def _render_melody(notes: list, note_dur: float, loop_count: int = 1) -> np.ndarray:
    """渲染旋律. notes = [(note_name, duration_multiplier), ...]
    duration_multiplier 是 note_dur 的倍数 (1.0 = 一个单位)."""
    if not notes:
        return np.zeros(0, dtype=np.int16)
    parts = []
    for name, mult in notes:
        dur = note_dur * mult
        freq = _note_freq(name)
        wave = _square_wave(freq, dur)
        env = _adsr_envelope(dur)
        # 应用包络 + 音量 (int16 范围 -32767 ~ 32767, 用 0.5 振幅避免过载)
        if len(wave) == len(env):
            parts.append((wave.astype(np.float32) * env * 0.5).astype(np.int16))
        else:
            parts.append(wave * int(0.5 * 32767 / 32767))
    one_loop = np.concatenate(parts) if parts else np.zeros(0, dtype=np.int16)
    if loop_count <= 1:
        return one_loop
    return np.tile(one_loop, loop_count)


def _to_stereo_sound(mono: np.ndarray) -> pygame.mixer.Sound:
    """mono int16 numpy -> pygame.mixer.Sound (stereo)."""
    if len(mono) == 0:
        # 静音 fallback (1 sample 静音, 避免 pygame 报错)
        mono = np.zeros(1, dtype=np.int16)
    # 复制为 2D stereo (samples, 2)
    stereo = np.column_stack([mono, mono])
    # pygame.sndarray 需要 C-contiguous
    stereo = np.ascontiguousarray(stereo)
    sound = pygame.sndarray.make_sound(stereo)
    return sound


# ---- 3 段 BGM 旋律 ----
# 菜单: C 大调 4 音符上行循环 (轻松)
MENU_MELODY = [
    ("C4", 1.0), ("E4", 1.0), ("G4", 1.0), ("E4", 1.0),
    ("G4", 1.0), ("E4", 1.0), ("C4", 1.0), ("REST", 1.0),
]

# 游戏: A 小调 8 音符 (紧张, 战斗感)
GAME_MELODY = [
    ("A3", 0.5), ("C4", 0.5), ("D4", 0.5), ("E4", 0.5),
    ("F4", 0.5), ("E4", 0.5), ("D4", 0.5), ("C4", 0.5),
    ("A3", 0.5), ("C4", 0.5), ("E4", 0.5), ("A4", 1.0),
    ("G4", 0.5), ("E4", 0.5), ("D4", 0.5), ("REST", 0.5),
]

# 胜利: C 大调 4 音符欢快上行 (短)
VICTORY_MELODY = [
    ("C4", 0.5), ("E4", 0.5), ("G4", 0.5), ("C5", 2.0),
    ("E5", 1.0), ("REST", 0.5), ("G4", 0.5), ("C5", 2.0),
]


# ---- BGM 生成 (函数式, 也可独立调用测试) ----
def generate_menu_bgm(note_dur: float = 0.3, loop_count: int = 2) -> pygame.mixer.Sound:
    """菜单 BGM (循环). 默认 ~4.8s."""
    return _to_stereo_sound(_render_melody(MENU_MELODY, note_dur, loop_count))


def generate_game_bgm(note_dur: float = 0.18, loop_count: int = 3) -> pygame.mixer.Sound:
    """游戏 BGM (循环). 默认 ~5.8s."""
    return _to_stereo_sound(_render_melody(GAME_MELODY, note_dur, loop_count))


def generate_victory_bgm(note_dur: float = 0.25, loop_count: int = 1) -> pygame.mixer.Sound:
    """胜利 BGM (短, 不循环)."""
    return _to_stereo_sound(_render_melody(VICTORY_MELODY, note_dur, loop_count))


# ---- Manager ----
class MusicManager:
    """背景音乐管理器.

    用法:
        m = MusicManager()
        m.play_track("menu")       # 播菜单 BGM (循环)
        m.play_track("game")       # 切游戏 BGM
        m.pause()                  # 暂停 (按 P 暂停时调)
        m.resume()                 # 恢复
        m.stop()                   # 停
    """

    def __init__(self, volume: float = MUSIC_VOLUME):
        self._enabled = MUSIC_ENABLED
        self._volume = volume
        self._current_track: str | None = None
        self._was_playing_before_pause: bool = False
        # 预生成 3 段 BGM (一次性, 之后复用)
        self._tracks: dict[str, pygame.mixer.Sound] = {}
        if self._enabled:
            self._tracks["menu"] = generate_menu_bgm()
            self._tracks["game"] = generate_game_bgm()
            self._tracks["victory"] = generate_victory_bgm()
            for snd in self._tracks.values():
                snd.set_volume(volume)

    def set_enabled(self, enabled: bool):
        """总开关."""
        if enabled == self._enabled:
            return
        self._enabled = enabled
        if not enabled:
            self.stop()
        elif self._current_track is not None:
            # 重新播
            self.play_track(self._current_track)

    def is_enabled(self) -> bool:
        return self._enabled

    def set_volume(self, volume: float):
        """设置音量 (0.0 - 1.0)."""
        self._volume = max(0.0, min(1.0, float(volume)))
        for snd in self._tracks.values():
            snd.set_volume(self._volume)

    def get_volume(self) -> float:
        return self._volume

    def play_track(self, name: str, loops: int = -1):
        """播某段 BGM. loops=-1 表示无限循环 (菜单/游戏); 0=播1次 (胜利)."""
        if not self._enabled:
            return
        if name not in self._tracks:
            return  # 未知轨道, 静默忽略
        # 切轨时先 stop 旧的
        if self._current_track and self._current_track != name:
            self.stop()
        track = self._tracks[name]
        # 胜利不循环
        if name == "victory":
            loops = 0
        track.play(loops=loops)
        self._current_track = name

    def stop(self):
        """停 BGM. 保留 _current_track (便于 set_enabled(True) 恢复)."""
        if self._current_track and self._current_track in self._tracks:
            self._tracks[self._current_track].stop()
        self._was_playing_before_pause = False

    def pause(self):
        """暂停当前 BGM (按 P 暂停游戏时调)."""
        if not self._enabled or self._current_track is None:
            return
        if pygame.mixer.get_init() is None:
            return
        # 检查当前 track 是否在播
        if self._tracks[self._current_track].get_num_channels() > 0:
            self._was_playing_before_pause = True
            pygame.mixer.pause()

    def resume(self):
        """恢复暂停的 BGM."""
        if not self._enabled:
            return
        if self._was_playing_before_pause:
            pygame.mixer.unpause()
            self._was_playing_before_pause = False

    def current_track(self) -> str | None:
        return self._current_track

    def is_playing(self) -> bool:
        """当前 track 是否在播放 (不是暂停)."""
        if self._current_track is None or self._current_track not in self._tracks:
            return False
        # get_num_channels 在 pause 后仍 > 0 (SDL 行为)
        # 用 mixer.music.get_busy + paused state 综合判断
        if self._was_playing_before_pause:
            return False
        return self._tracks[self._current_track].get_num_channels() > 0


# ---- Game 集成辅助: state -> track name 映射 ----
def track_for_state(state: str) -> str | None:
    """根据 Game.state 返回要播的 BGM. None = 停."""
    if state == "menu":
        return "menu"
    if state == "playing":
        return "game"
    if state == "victory":
        return "victory"
    if state == "paused":
        return None  # 暂停时保留但 pause()
    return None  # game_over / level_complete 不播 (短促)
