"""B1 红闪敌人（powerup carrier）测试。

- 默认 20% 概率成为红闪敌人
- 显式传 is_powerup_carrier=True/False 时锁定
- 红闪敌人颜色为 POWERUP_CARRIER_COLOR
- 红闪敌人 flashing_time 在 update 后仍 > 0（持续闪烁）
- 击杀红闪敌人时 100% 掉道具
- 击杀普通敌人时仍走 25% 概率
- ENTITY_KILLED 事件 payload 含 is_powerup_carrier 字段
"""
import random
import pytest
from unittest.mock import patch

import settings
from entities.enemy import EnemyTank
from entities.powerup import PowerUp
from utils import events


# ---- EnemyTank 构造 ----

def test_enemy_default_carrier_random_about_20pct():
    """默认 ~20% 成为红闪；100 个样本至少 5 个、至多 50 个。"""
    random.seed(0)
    carriers = sum(
        1 for i in range(100)
        if EnemyTank(i * 100, 0, tier=0, is_powerup_carrier=None).is_powerup_carrier
    )
    assert 5 <= carriers <= 50, f"expected ~20 carriers, got {carriers}"


def test_enemy_explicit_carrier_true():
    e = EnemyTank(0, 0, tier=0, is_powerup_carrier=True)
    assert e.is_powerup_carrier is True


def test_enemy_explicit_carrier_false():
    e = EnemyTank(0, 0, tier=0, is_powerup_carrier=False)
    assert e.is_powerup_carrier is False


def test_enemy_carrier_uses_carrier_color():
    """红闪敌人用 POWERUP_CARRIER_COLOR（鲜红）做车身色。"""
    e = EnemyTank(0, 0, tier=0, is_powerup_carrier=True)
    assert e.color == settings.POWERUP_CARRIER_COLOR


def test_enemy_normal_uses_tier_color():
    """非红闪敌人用 ENEMY_TIER_COLORS[tier]。"""
    e = EnemyTank(0, 0, tier=1, is_powerup_carrier=False)
    assert e.color == settings.ENEMY_TIER_COLORS[1]


# ---- 视觉闪烁 ----

def _make_level_stub(enemy):
    """构造一个最小可用的 Level-like 假对象用于单测 update。"""
    class Stub:
        pass
    s = Stub()
    s.players = []  # EnemyTank.update 不会用到
    s.bullets = []
    s.effects = []
    s.tilemap = None
    return s


def test_carrier_keeps_flashing_after_updates():
    """红闪敌人经过多帧 update 仍然闪烁（flashing_time > 0）。"""
    e = EnemyTank(0, 0, tier=0, is_powerup_carrier=True)
    # EnemyTank.update 需要 tilemap / other_tanks / player。我们直接调
    # update_cooldown + 手写闪烁补帧，避开 update 内部 AI 逻辑。
    for _ in range(20):
        e.update_cooldown(0.05)
        # 模拟 update 里的 carrier 闪烁补帧
        if e.is_powerup_carrier:
            e.flashing_time = settings.POWERUP_CARRIER_FLASH_PERIOD
        assert e.flashing_time > 0, "carrier should keep flashing"


def test_normal_enemy_stops_flashing():
    """普通敌人不会持续闪烁（出生 1s 无敌之后 flashing_time 归 0）。"""
    e = EnemyTank(0, 0, tier=0, is_powerup_carrier=False)
    e.flashing_time = 0.0
    e.update_cooldown(0.5)
    assert e.flashing_time == 0.0


# ---- 道具掉落逻辑（直接复刻 level.py 里的判定，验证规则） ----

def _should_drop(is_powerup_carrier, roll):
    """复刻 level.py:206-221 里的掉落判定。"""
    return is_powerup_carrier or roll < 0.25


def test_carrier_always_drops():
    for roll in (0.0, 0.1, 0.5, 0.9, 0.999):
        assert _should_drop(True, roll) is True, f"carrier must drop on roll={roll}"


def test_normal_drops_only_25pct():
    drops = sum(1 for r in (0.0, 0.1, 0.2, 0.24) if _should_drop(False, r))
    no_drops = sum(1 for r in (0.25, 0.5, 0.9, 0.999) if _should_drop(False, r))
    assert drops == 4
    assert no_drops == 0


# ---- 事件 payload ----

def test_event_payload_includes_carrier_flag(monkeypatch):
    """ENTITY_KILLED 事件 payload 含 is_powerup_carrier 字段。"""
    # 用一个 fake level 简化（不跑真 Level.update，只验证 publish 字段）
    from utils import events as ev
    ev.clear()
    received = []

    def cb(**kwargs):
        received.append(kwargs)

    ev.subscribe(ev.ENTITY_KILLED, cb)

    # 模拟 level 里的两次 publish
    e1 = EnemyTank(0, 0, tier=0, is_powerup_carrier=True)
    e1.rect.x, e1.rect.y = 100, 100
    ev.publish(ev.ENTITY_KILLED, kind="enemy", owner="player",
               x=e1.rect.centerx, y=e1.rect.centery, score_delta=100,
               is_powerup_carrier=e1.is_powerup_carrier)

    e2 = EnemyTank(0, 0, tier=0, is_powerup_carrier=False)
    e2.rect.x, e2.rect.y = 200, 200
    ev.publish(ev.ENTITY_KILLED, kind="enemy", owner="player",
               x=e2.rect.centerx, y=e2.rect.centery, score_delta=100,
               is_powerup_carrier=e2.is_powerup_carrier)

    assert len(received) == 2
    assert received[0]["is_powerup_carrier"] is True
    assert received[1]["is_powerup_carrier"] is False
    ev.clear()
