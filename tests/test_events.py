"""事件总线单元测试 (pytest 风格): subscribe/publish/unsubscribe/异常隔离/clear/多订阅者.

无 pygame 依赖, 不需要 dummy SDL, 跑得最快.
conftest.py 负责: dummy SDL env, pygame init, 每个测试前后清空事件总线.
"""
from utils import events


def test_basic_publish():
    """订阅 + publish 触发回调, kwargs 正确传递."""
    hits = []
    def cb1(x, y):
        hits.append((x, y))
    events.subscribe(events.POWERUP_PICKED, cb1)
    events.publish(events.POWERUP_PICKED, x=10, y=20)
    assert hits == [(10, 20)], f"hits={hits}"
    assert events.subscriber_count(events.POWERUP_PICKED) == 1


def test_unsubscribe():
    """unsub 后再 publish 不再触发."""
    hits = []
    unsub = events.subscribe(events.ENTITY_KILLED, lambda **kw: hits.append(("kill", kw)))
    events.publish(events.ENTITY_KILLED, kind="enemy")
    assert len(hits) == 1, f"after publish: {hits}"
    unsub()
    events.publish(events.ENTITY_KILLED, kind="enemy")
    assert len(hits) == 1, f"after unsub+publish: still 1 hit"
    assert events.subscriber_count(events.ENTITY_KILLED) == 0


def test_exception_isolation():
    """单订阅者抛错不影响其他订阅者."""
    call_log = []
    def good_cb(**kw):
        call_log.append("good")
    def bad_cb(**kw):
        call_log.append("bad")
        raise RuntimeError("test bad")
    events.subscribe(events.BASE_HIT, good_cb)
    events.subscribe(events.BASE_HIT, bad_cb)
    events.subscribe(events.BASE_HIT, good_cb)
    # publish 不应抛错, 两个 good_cb 都被调用
    events.publish(events.BASE_HIT)
    assert call_log == ["good", "bad", "good"], f"call_log={call_log}"


def test_in_callback_unsub():
    """回调内 unsubscribe 不影响本次 publish 的其他订阅者, 也不影响后续."""
    log = []
    def self_unsub(**kw):
        log.append("self_unsub")
        unsub_inner()
    def other(**kw):
        log.append("other")
    unsub_inner = events.subscribe(events.LEVEL_COMPLETED, self_unsub)
    events.subscribe(events.LEVEL_COMPLETED, other)
    events.publish(events.LEVEL_COMPLETED)
    assert "self_unsub" in log and "other" in log, f"log={log}"
    # 再次 publish: self_unsub 已退订, other 仍在
    log.clear()
    events.publish(events.LEVEL_COMPLETED)
    assert log == ["other"], f"after inner unsub: log={log}"


def test_clear():
    """clear 清空所有订阅."""
    events.subscribe("a", lambda **kw: None)
    events.subscribe("a", lambda **kw: None)
    events.subscribe("b", lambda **kw: None)
    assert events.subscriber_count("a") == 2
    assert events.subscriber_count("b") == 1
    events.clear()
    assert events.subscriber_count("a") == 0
    assert events.subscriber_count("b") == 0


def test_publish_to_no_subscribers():
    """publish 不存在的 event 是 no-op 不抛错."""
    events.publish("nobody.listening", x=1)
    # 通过: 不抛错即 OK


def test_event_name_constants():
    """事件名常量字符串值稳定 (订阅方硬编码的契约)."""
    assert events.ENTITY_KILLED == "entity.killed"
    assert events.POWERUP_PICKED == "powerup.picked"
    assert events.BASE_HIT == "base.hit"
    assert events.BASE_DESTROYED == "base.destroyed"
    assert events.LEVEL_COMPLETED == "level.completed"
    assert events.LEVEL_FAILED == "level.failed"


def test_level_failed_reasons():
    """LEVEL_FAILED.reason 常量."""
    assert events.REASON_BASE_DESTROYED == "base_destroyed"
    assert events.REASON_LIVES_ZERO == "lives_zero"


def test_subscriber_count_independent_events():
    """不同事件的订阅者独立计数."""
    events.subscribe("x", lambda **kw: None)
    events.subscribe("y", lambda **kw: None)
    events.subscribe("y", lambda **kw: None)
    assert events.subscriber_count("x") == 1
    assert events.subscriber_count("y") == 2
    # 隔离清空 (conftest 也会清, 但这里先验证 clear 只清指定订阅的逻辑)
    # 实际上 clear() 清全部, 我们靠 conftest 的 fixture 保证隔离
