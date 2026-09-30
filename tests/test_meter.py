"""The meter: every request measured the same way, apart from the requests beside it, against targets."""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

from qlsc import meter

CACHE = {"read": 0.1, "write": 1.25}


def usage(i=1000, o=100, read=0, write=0):
    return SimpleNamespace(input_tokens=i, output_tokens=o, cache_read_input_tokens=read,
                           cache_creation_input_tokens=write)  # fmt: skip


def test_an_llm_call_counts_its_tokens_and_cost():
    with meter.measure() as m:
        meter.llm(usage(1000, 100, read=2000, write=400), (2, 10), CACHE)
    got = m.measure()
    assert got["tokens"] == 3500 and got["llm_calls"] == 1
    assert got["cost"] == pytest.approx((1000 + 2000 * 0.1 + 400 * 1.25) * 2 / 1e6 + 100 * 10 / 1e6, abs=1e-4)


def test_nothing_is_measured_without_a_meter():
    meter.report(tokens=5)  # no meter open: no error, nothing kept
    assert meter.current() is None


def test_a_meter_inside_another_reports_to_both():
    with meter.measure() as outer:
        with meter.measure() as inner:
            meter.report(tokens=10)
        meter.report(tokens=1)
    assert inner.measure()["tokens"] == 10 and outer.measure()["tokens"] == 11


def test_the_consumers_share_is_set_aside():
    """A consumer's tokens and time are its own: the service's meter doesn't count them."""
    consumer = meter.Meter()
    with meter.measure() as service:
        meter.report(tokens=100)
        with meter.aside(consumer):
            meter.report(tokens=40)
            time.sleep(0.05)
    assert service.measure()["tokens"] == 100 and consumer.measure()["tokens"] == 40
    assert consumer.measure()["seconds"] >= 0.05 > service.measure()["seconds"]


def test_parallel_requests_stay_apart():
    got = {}

    def one(n):
        with meter.measure() as m:
            for _ in range(n):
                meter.report(tokens=1)
                time.sleep(0.001)
        got[n] = m.measure()["tokens"]

    threads = [threading.Thread(target=one, args=(n,)) for n in (3, 7, 11)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert got == {3: 3, 7: 7, 11: 11}


def test_targets():
    m = {"tokens": 30000, "seconds": 70.0}
    assert meter.check(m, {"tokens": 40000, "seconds": 60}) == {"tokens": True, "seconds": False}
    assert not meter.within(m, {"tokens": 40000, "seconds": 60})
    with pytest.raises(ValueError):
        meter.check(m, {"happiness": 1})


def test_summary():
    ms = [{"tokens": t, "seconds": t / 1000} for t in (1000, 2000, 3000, 4000, 50000)]
    got = meter.summary(ms, {"tokens": 40000})
    assert got["tokens"]["p50"] == 3000 and got["tokens"]["max"] == 50000
    assert got["tokens"]["within"] == 4 and got["within"] == 4 and got["n"] == 5
