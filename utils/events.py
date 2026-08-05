"""事件总线 - publish-subscribe, 同步触发, 异常隔离.

为成就(F10)、回放(F13)、CI 钩子(F12) 提供解耦的事件流.
游戏是单线程, 不需要锁; 但保留异步扩展点(后续可换 queue).

设计要点:
- 模块级单例, 全局可见
- 事件名用点分命名空间: 'entity.killed', 'powerup.picked' 等
- 订阅者接收 **kwargs, 命名见各事件常量下的注释
- 单个订阅者抛错被 try/except 吞掉, 打印 traceback, 不影响其他订阅者
- 测试用 clear() 重置
"""

# ---- 事件名常量 ----
ENTITY_KILLED = "entity.killed"          # kind: 'enemy'|'player', owner: 'player'|'enemy'|'powerup', x, y, score_delta
POWERUP_PICKED = "powerup.picked"        # type: str, x: int, y: int
BASE_HIT = "base.hit"                    # (no payload)
BASE_DESTROYED = "base.destroyed"        # (no payload)
LEVEL_COMPLETED = "level.completed"      # score: int, level_index: int
LEVEL_FAILED = "level.failed"            # reason: 'base_destroyed'|'lives_zero'
ACHIEVEMENT_UNLOCKED = "achievement.unlocked"  # id: str (成就 id)
# LEVEL_FAILED.reason 取值常量
REASON_BASE_DESTROYED = "base_destroyed"
REASON_LIVES_ZERO = "lives_zero"


# ---- 模块级状态 ----
_subscribers: dict = {}


def subscribe(event_name, callback):
    """订阅事件, 返回 unsubscribe() 函数."""
    _subscribers.setdefault(event_name, []).append(callback)

    def _unsub():
        cb_list = _subscribers.get(event_name, [])
        if callback in cb_list:
            cb_list.remove(callback)

    return _unsub


def publish(event_name, **kwargs):
    """发布事件, 同步触发所有订阅者. 异常隔离.

    遍历时复制一份列表, 避免回调内取消订阅导致遍历出错.
    """
    import traceback
    for cb in list(_subscribers.get(event_name, [])):
        try:
            cb(**kwargs)
        except Exception:
            traceback.print_exc()


def clear():
    """清空所有订阅 (测试用)."""
    _subscribers.clear()


def subscriber_count(event_name):
    """返回某事件的订阅者数量 (测试/调试用)."""
    return len(_subscribers.get(event_name, []))
