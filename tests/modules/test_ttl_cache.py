import time

from fpms.modules.pages.utils import ttl_cache


def test_ttl_cache_shared_across_instances_and_keyed_by_args():
    calls = []

    class Thing:
        @ttl_cache(60)
        def value(self, key):
            calls.append(key)
            return len(calls)

    a = Thing()
    b = Thing()
    assert a.value("x") == 1
    assert a.value("x") == 1  # cached, and shared across instances
    assert b.value("x") == 1
    assert a.value("y") == 2  # different argument is cached separately
    assert calls == ["x", "y"]


def test_ttl_cache_expires():
    calls = []

    class Thing:
        @ttl_cache(0)
        def value(self):
            calls.append(1)
            return len(calls)

    thing = Thing()
    assert thing.value() == 1
    time.sleep(0.01)
    assert thing.value() == 2
