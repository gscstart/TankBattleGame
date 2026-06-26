"""事件总线单元测试：subscribe / publish / unsubscribe / 异常隔离 / clear / 多订阅者.

无 pygame 依赖, 不需要 dummy SDL, 跑得最快.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import events

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)
        print("FAIL:", msg)
    else:
        print("OK  :", msg)


def main():
    events.clear()

    # 1. 基础 publish
    print("\n=== Test 1: basic publish ===")
    hits = []
    def cb1(x, y):
        hits.append((x, y))
    events.subscribe(events.POWERUP_PICKED, cb1)
    events.publish(events.POWERUP_PICKED, x=10, y=20)
    check(hits == [(10, 20)], f"hits={hits}")
    check(events.subscriber_count(events.POWERUP_PICKED) == 1, "subscriber count == 1")

    # 2. unsubscribe
    print("\n=== Test 2: unsubscribe ===")
    unsub = events.subscribe(events.ENTITY_KILLED, lambda **kw: hits.append(("kill", kw)))
    events.publish(events.ENTITY_KILLED, kind="enemy")
    check(len(hits) == 2, f"after publish: {hits}")
    unsub()
    events.publish(events.ENTITY_KILLED, kind="enemy")
    check(len(hits) == 2, f"after unsub+publish: still 2 hits")
    check(events.subscriber_count(events.ENTITY_KILLED) == 0, "subscriber count == 0 after unsub")

    # 3. 异常隔离
    print("\n=== Test 3: exception isolation ===")
    call_log = []
    def good_cb(**kw):
        call_log.append("good")
    def bad_cb(**kw):
        call_log.append("bad")
        raise RuntimeError("test bad")
    events.clear()
    events.subscribe(events.BASE_HIT, good_cb)
    events.subscribe(events.BASE_HIT, bad_cb)
    events.subscribe(events.BASE_HIT, good_cb)
    # publish 不应抛错, 两个 good_cb 都被调用
    events.publish(events.BASE_HIT)
    check(call_log == ["good", "bad", "good"], f"call_log={call_log}")

    # 4. 回调内 unsubscribe 不影响本次 publish 的其他订阅者
    print("\n=== Test 4: in-callback unsub ===")
    events.clear()
    log = []
    def self_unsub(**kw):
        log.append("self_unsub")
        unsub_inner()
    def other(**kw):
        log.append("other")
    unsub_inner = events.subscribe(events.LEVEL_COMPLETED, self_unsub)
    events.subscribe(events.LEVEL_COMPLETED, other)
    events.publish(events.LEVEL_COMPLETED)
    check("self_unsub" in log and "other" in log, f"log={log}")
    # 再次 publish: self_unsub 应已退订, other 仍在
    log.clear()
    events.publish(events.LEVEL_COMPLETED)
    check(log == ["other"], f"after inner unsub: log={log}")

    # 5. clear
    print("\n=== Test 5: clear ===")
    events.subscribe("a", lambda **kw: None)
    events.subscribe("a", lambda **kw: None)
    events.subscribe("b", lambda **kw: None)
    check(events.subscriber_count("a") == 2, "a has 2 subs")
    check(events.subscriber_count("b") == 1, "b has 1 sub")
    events.clear()
    check(events.subscriber_count("a") == 0, "a cleared")
    check(events.subscriber_count("b") == 0, "b cleared")

    # 6. publish 不存在的 event 不抛错
    print("\n=== Test 6: publish to no-subscribers ===")
    events.clear()
    events.publish("nobody.listening", x=1)  # 不应抛错
    check(True, "publish to nobody is a no-op")

    # 7. 事件名常量字符串
    print("\n=== Test 7: event name constants ===")
    check(events.ENTITY_KILLED == "entity.killed", "ENTITY_KILLED")
    check(events.POWERUP_PICKED == "powerup.picked", "POWERUP_PICKED")
    check(events.BASE_HIT == "base.hit", "BASE_HIT")
    check(events.BASE_DESTROYED == "base.destroyed", "BASE_DESTROYED")
    check(events.LEVEL_COMPLETED == "level.completed", "LEVEL_COMPLETED")
    check(events.LEVEL_FAILED == "level.failed", "LEVEL_FAILED")

    print("\n" + "=" * 50)
    if errors:
        print(f"FAILED: {len(errors)} test(s)")
        for e in errors:
            print("  -", e)
        return 1
    print("ALL EVENT TESTS PASSED ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
