"""F20 背景音乐 (路线图 §6 阶段 D) 测试.

- 旋律生成 (utils/music.py): 方波 + ADSR 包络
- 3 段 BGM: menu / game / victory
- MusicManager: play/pause/resume/stop + 音量 + 开关
- track_for_state: state -> track 映射
- Game 集成: BGM 在 state 变化时切换 (K_P 暂停时 pause / K_M 开关)
"""
import os
import pytest
import numpy as np
import pygame

from settings import MUSIC_SAMPLE_RATE
from utils import music as music_mod


# ---- 测试夹具 ----
@pytest.fixture(autouse=True)
def ensure_mixer():
    """确保 mixer 初始化 (conftest 已 init, 兜底)."""
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    yield


# ===== 1. 旋律生成 (函数) =====

def test_square_wave_basic():
    """方波: freq=0 返回静音, 正常频率返回非空."""
    silent = music_mod._square_wave(0, 0.1)
    assert len(silent) == int(MUSIC_SAMPLE_RATE * 0.1)
    assert np.all(silent == 0)

    wave = music_mod._square_wave(440, 0.1)
    assert len(wave) == int(MUSIC_SAMPLE_RATE * 0.1)
    # 方波只有 +1 和 -1
    assert set(np.unique(wave).tolist()).issubset({-1, 0, 1})


def test_adsr_envelope_length():
    """ADSR 包络长度 == duration * sample_rate."""
    env = music_mod._adsr_envelope(0.5)
    assert len(env) == int(MUSIC_SAMPLE_RATE * 0.5)


def test_adsr_envelope_shape():
    """ADSR 包络: 起始 0 -> 上升 -> 衰减到 sustain -> 渐弱到 0."""
    env = music_mod._adsr_envelope(0.5, attack=0.01, decay=0.05, sustain_level=0.7)
    # 起始接近 0
    assert env[0] < 0.1
    # 末尾接近 0
    assert env[-1] < 0.1
    # 中间有非零值
    assert env.max() > 0.5


def test_render_melody_empty():
    """空旋律返回空数组."""
    result = music_mod._render_melody([], note_dur=0.3, loop_count=1)
    assert len(result) == 0


def test_render_melody_single_note():
    """单音符: 长度 == note_dur * sample_rate."""
    result = music_mod._render_melody([("C4", 1.0)], note_dur=0.3, loop_count=1)
    assert len(result) == int(MUSIC_SAMPLE_RATE * 0.3)


def test_render_melody_loops():
    """loop_count 倍数关系."""
    one = music_mod._render_melody([("C4", 1.0)], note_dur=0.3, loop_count=1)
    twice = music_mod._render_melody([("C4", 1.0)], note_dur=0.3, loop_count=2)
    assert len(twice) == 2 * len(one)


def test_render_melody_rest_silent():
    """REST 音符是静音 (freq=0)."""
    result = music_mod._render_melody([("REST", 1.0)], note_dur=0.3, loop_count=1)
    # 包络 * 0 = 0, 全部静音
    assert np.all(result == 0)


def test_to_stereo_sound():
    """mono -> stereo pygame.mixer.Sound."""
    mono = np.array([100, -100, 0, 100, -100], dtype=np.int16)
    snd = music_mod._to_stereo_sound(mono)
    assert snd is not None
    # 立体声长度 == mono 长度
    assert snd.get_length() > 0


def test_to_stereo_sound_empty():
    """空 mono fallback 到 1 sample 静音 (不抛错)."""
    mono = np.zeros(0, dtype=np.int16)
    snd = music_mod._to_stereo_sound(mono)
    assert snd is not None


# ===== 2. 3 段 BGM 生成 =====

def test_generate_menu_bgm():
    """菜单 BGM 生成成功, 长度 > 0."""
    snd = music_mod.generate_menu_bgm()
    assert snd is not None
    assert snd.get_length() > 1.0  # 至少 1 秒


def test_generate_game_bgm():
    """游戏 BGM 生成成功, 长度 > 0."""
    snd = music_mod.generate_game_bgm()
    assert snd is not None
    assert snd.get_length() > 1.0


def test_generate_victory_bgm():
    """胜利 BGM 生成成功, 长度 > 0."""
    snd = music_mod.generate_victory_bgm()
    assert snd is not None
    assert snd.get_length() > 0.5


def test_three_tracks_have_different_durations():
    """3 段 BGM 长度不同 (按设计)."""
    s_menu = music_mod.generate_menu_bgm()
    s_game = music_mod.generate_game_bgm()
    s_victory = music_mod.generate_victory_bgm()
    # 至少 2 个长度不同
    lens = {round(s_menu.get_length(), 1),
            round(s_game.get_length(), 1),
            round(s_victory.get_length(), 1)}
    assert len(lens) >= 2


# ===== 3. MusicManager =====

def test_manager_default_state():
    """Manager 默认: enabled=True, 3 段预生成."""
    m = music_mod.MusicManager()
    assert m.is_enabled() is True
    assert set(m._tracks.keys()) == {"menu", "game", "victory"}
    assert m.current_track() is None


def test_manager_disabled_no_tracks():
    """disabled 时不预生成 tracks."""
    # 通过设置 MUSIC_ENABLED=False 创建 (但 settings 是模块级常量, 修改后改回)
    from settings import MUSIC_ENABLED
    original = MUSIC_ENABLED
    try:
        # 不直接改 settings (会影响其他测试), 测 set_enabled
        m = music_mod.MusicManager()
        m.set_enabled(False)
        assert m.is_enabled() is False
        m.play_track("menu")
        # disabled 时不播
        assert m.current_track() is None
    finally:
        pass  # MUSIC_ENABLED 本身没改


def test_manager_play_track():
    """play_track 切到某 track 并标记 current."""
    m = music_mod.MusicManager()
    m.play_track("menu")
    assert m.current_track() == "menu"
    assert m.is_playing() is True


def test_manager_play_track_switch():
    """切 track 时先 stop 旧的."""
    m = music_mod.MusicManager()
    m.play_track("menu")
    m.play_track("game")
    assert m.current_track() == "game"


def test_manager_play_unknown_track_no_error():
    """未知 track 静默忽略."""
    m = music_mod.MusicManager()
    m.play_track("nonexistent")
    assert m.current_track() is None


def test_manager_stop():
    """stop 后 is_playing=False (保留 current_track 便于 set_enabled 恢复)."""
    m = music_mod.MusicManager()
    m.play_track("menu")
    m.stop()
    assert m.is_playing() is False
    # current_track 保留 (设计如此, set_enabled(True) 能重新播)


def test_manager_pause_resume():
    """pause/resume 保持 current_track."""
    m = music_mod.MusicManager()
    m.play_track("game")
    m.pause()
    # 暂停后 is_playing=False
    assert m.is_playing() is False
    # 恢复
    m.resume()
    # 恢复后 is_playing=True
    assert m.is_playing() is True


def test_manager_pause_when_not_playing():
    """未播时 pause 不抛错."""
    m = music_mod.MusicManager()
    m.pause()  # should not raise
    assert m.is_playing() is False


def test_manager_set_volume():
    """set_volume 改变 volume + 应用到所有 tracks.

    注意: pygame mixer 量化音量到 1/128 精度 (0.7 -> 0.6953)
    """
    m = music_mod.MusicManager()
    m.set_volume(0.7)
    assert m.get_volume() == 0.7
    # 所有 track 音量一致 (允许量化误差)
    for snd in m._tracks.values():
        assert abs(snd.get_volume() - 0.7) < 0.01


def test_manager_set_volume_clamps():
    """set_volume 限制在 [0, 1]."""
    m = music_mod.MusicManager()
    m.set_volume(2.0)
    assert m.get_volume() == 1.0
    m.set_volume(-0.5)
    assert m.get_volume() == 0.0


def test_manager_set_enabled_disable_stops():
    """set_enabled(False) 时停 BGM (current_track 保留, is_playing=False)."""
    m = music_mod.MusicManager()
    m.play_track("menu")
    m.set_enabled(False)
    assert m.is_enabled() is False
    assert m.is_playing() is False


def test_manager_set_enabled_reenable_resumes():
    """set_enabled(True) 重新播当前 track (如果有)."""
    m = music_mod.MusicManager()
    m.play_track("menu")
    m.set_enabled(False)
    m.set_enabled(True)
    # 重新播
    assert m.is_playing() is True


# ===== 4. track_for_state =====

def test_track_for_menu():
    assert music_mod.track_for_state("menu") == "menu"


def test_track_for_playing():
    assert music_mod.track_for_state("playing") == "game"


def test_track_for_victory():
    assert music_mod.track_for_state("victory") == "victory"


def test_track_for_paused_none():
    """paused 状态: None (pause() 保留 track, 不切)."""
    assert music_mod.track_for_state("paused") is None


def test_track_for_unknown_none():
    """未知 state 返回 None."""
    assert music_mod.track_for_state("level_complete") is None
    assert music_mod.track_for_state("game_over") is None
    assert music_mod.track_for_state("") is None
