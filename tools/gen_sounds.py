"""程序生成 4 种坦克大战基础音效（不需要外部资源）。

使用 Python 标准库 wave + struct + math：
- fire.wav     - 300Hz->100Hz 短促扫频（0.08s）
- explosion.wav - 200Hz->40Hz 长扫频 + 噪声（0.3s）
- hit.wav      - 短促咔哒声（0.04s）
- start.wav    - 上行扫频（游戏开始提示，0.2s）

运行：python tools/gen_sounds.py
"""
import os
import math
import struct
import wave
import random

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
SAMPLE_RATE = 22050


def _save_wav(filename: str, samples: list[int]):
    """保存为单声道 16-bit WAV。"""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        # clip + 转换
        frames = b"".join(struct.pack("<h", max(-32767, min(32767, int(s)))) for s in samples)
        w.writeframes(frames)
    print(f"  saved {path} ({len(samples)} samples, {len(samples)/SAMPLE_RATE:.2f}s)")


def make_fire() -> list[int]:
    """300Hz -> 100Hz 短促扫频 + 衰减。"""
    duration = 0.08
    n = int(duration * SAMPLE_RATE)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # 频率随时间下降
        f = 300 - (200 * (i / n))
        # 音量衰减
        vol = 0.5 * (1 - i / n) ** 0.5
        sample = vol * math.sin(2 * math.pi * f * t)
        out.append(sample * 32767)
    return out


def make_explosion() -> list[int]:
    """200Hz -> 40Hz 扫频 + 噪声 + 衰减。"""
    duration = 0.3
    n = int(duration * SAMPLE_RATE)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # 频率快速下降
        f = 200 * ((n - i) / n) + 40
        vol = 0.6 * (1 - i / n) ** 1.5
        # 主频 + 噪声
        tone = math.sin(2 * math.pi * f * t)
        noise = (random.random() * 2 - 1) * 0.4
        sample = vol * (tone * 0.7 + noise * 0.3)
        out.append(sample * 32767)
    return out


def make_hit() -> list[int]:
    """短促咔哒（高频噪声 + 立即衰减）。"""
    duration = 0.04
    n = int(duration * SAMPLE_RATE)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # 高频 + 极快衰减
        f = 800
        vol = 0.4 * (1 - i / n) ** 3
        tone = math.sin(2 * math.pi * f * t)
        noise = (random.random() * 2 - 1) * 0.5
        sample = vol * (tone * 0.3 + noise * 0.7)
        out.append(sample * 32767)
    return out


def make_start() -> list[int]:
    """上行扫频（C2 -> C4）。"""
    duration = 0.2
    n = int(duration * SAMPLE_RATE)
    out = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # 频率上升
        f = 130 * (1 + 3 * (i / n))
        vol = 0.4 * math.sin(math.pi * i / n)  # 钟形包络
        sample = vol * math.sin(2 * math.pi * f * t)
        out.append(sample * 32767)
    return out


def main():
    print("Generating sound effects...")
    random.seed(42)  # 可重复
    _save_wav("fire.wav", make_fire())
    _save_wav("explosion.wav", make_explosion())
    _save_wav("hit.wav", make_hit())
    _save_wav("start.wav", make_start())
    print("Done.")


if __name__ == "__main__":
    main()
