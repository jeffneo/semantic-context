"""Meter: what answering a request costs, measured the same way whichever route answers it.

A request's measurement is the wall-clock seconds from the request to its final answer and the LLM tokens
it spent (every call's input, cache reads and writes included, and its output), with what they come
from: the LLM calls made and those answered from the call cache, their cost at list price, the
warehouse's queries and bytes billed, the texts embedded, the seconds spent waiting out rate limits, and
the turns of an exchange (a consumer's corrections).

The LLM, the embedder and the warehouse report to every meter open in their thread (a context variable),
so requests measured in parallel threads stay apart, and a meter open inside another reports to both.
`aside` sets another party's share of an exchange apart: while a consumer reads an answer and writes its
correction, that time and those tokens are its own, not the service's.

A measurement is checked against targets, a ceiling on any measured quantity (MEASURES): the service's are
`service.targets` in defaults.yaml, tokens and seconds for now. `summary` gives a set of measurements'
percentiles and the share of them within each target.
"""

from __future__ import annotations

import contextvars
import threading
import time
from collections import Counter
from contextlib import contextmanager

MEASURES = {
    "seconds": "wall clock from the request to its final answer",
    "tokens": "LLM tokens: input (cache reads and writes included) and output",
    "tokens_in": "input tokens not from a prompt cache",
    "cache_read": "input tokens read from a prompt cache",
    "cache_write": "input tokens written to a prompt cache",
    "tokens_out": "output tokens (thinking included)",
    "llm_calls": "LLM calls made",
    "llm_cached": "LLM calls answered from the call cache: no tokens, no time",
    "cost": "the LLM calls' cost at list price (llm.prices), $",
    "warehouse_queries": "dry runs and runs",
    "bytes_billed": "the warehouse's bytes billed",
    "embedded": "texts embedded (not from the cache)",
    "waits": "seconds spent waiting out rate limits",
    "turns": "the service's answers in the exchange",
}

_open: contextvars.ContextVar[tuple[Meter, ...]] = contextvars.ContextVar("meters", default=())


class Meter:
    def __init__(self) -> None:
        self.n: Counter = Counter()
        self._lock = threading.Lock()
        self._since: list[float] = []  # the starts of the blocks open now

    @contextmanager
    def on(self):
        """Measure a block: what it calls reports here, and its wall clock counts."""
        token = _open.set((*_open.get(), self))
        self._since.append(time.perf_counter())
        try:
            yield self
        finally:
            self.add("seconds", time.perf_counter() - self._since.pop())
            _open.reset(token)

    def add(self, name: str, n: float = 1) -> None:
        with self._lock:
            self.n[name] += n

    def measure(self) -> dict:
        """The measurement so far (a block still open counts to now)."""
        now = time.perf_counter()
        with self._lock:
            n = self.n.copy()
        n["seconds"] += sum(now - t for t in self._since)
        return {
            k: round(n.get(k, 0), 4 if k == "cost" else 2 if k in ("seconds", "waits") else 0)
            for k in MEASURES
        }


@contextmanager
def measure():
    """A new meter, open over the block."""
    m = Meter()
    with m.on():
        yield m


def current() -> Meter | None:
    """The innermost meter open in this thread."""
    return (_open.get() or (None,))[-1]


@contextmanager
def aside(other: Meter):
    """Another party's share: during the block, only `other` measures, and the block's wall clock is taken
    off the meters it interrupts."""
    held = _open.get()
    token = _open.set(())
    t0 = time.perf_counter()
    try:
        with other.on():
            yield other
    finally:
        _open.reset(token)
        for m in held:
            m.add("seconds", -(time.perf_counter() - t0))


def report(**counts: float) -> None:
    """Counts reported to every meter open in this thread."""
    for m in _open.get():
        for k, v in counts.items():
            m.add(k, v)


def llm(usage, price: tuple[float, float] | None, cache_prices: dict) -> None:
    """One LLM response's usage (the API's `usage`), priced at the model's list price ($ per million
    tokens in and out) and the prompt cache's multiples of the input price."""
    fresh, out = usage.input_tokens, usage.output_tokens
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cost = 0.0
    if price:
        cost = (fresh + read * cache_prices["read"] + write * cache_prices["write"]) * price[
            0
        ] / 1e6 + out * price[1] / 1e6
    report(tokens=fresh + read + write + out, tokens_in=fresh, cache_read=read, cache_write=write, tokens_out=out,
           llm_calls=1, cost=cost)  # fmt: skip


def check(measurement: dict, targets: dict) -> dict[str, bool]:
    """Each target met or not: the measured quantity at most its ceiling."""
    unknown = set(targets) - set(MEASURES)
    if unknown:
        raise ValueError(f"targets on nothing measured: {sorted(unknown)} (meter.MEASURES)")
    return {k: measurement.get(k, 0) <= ceiling for k, ceiling in targets.items()}


def within(measurement: dict, targets: dict) -> bool:
    return all(check(measurement, targets).values())


def percentile(xs: list[float], p: float) -> float:
    """The nearest-rank percentile (p in 0..100) of a non-empty list."""
    xs = sorted(xs)
    return xs[max(0, min(len(xs) - 1, round(p / 100 * len(xs) + 0.5) - 1))]


def summary(
    measurements: list[dict], targets: dict, quantities: tuple[str, ...] = ("tokens", "seconds")
) -> dict:
    """A set of measurements: each quantity's median, 90th percentile, maximum and mean, and the share
    within each target and within all of them."""
    out: dict = {"n": len(measurements)}
    if not measurements:
        return out
    for q in dict.fromkeys((*quantities, *targets)):
        xs = [m.get(q, 0) for m in measurements]
        out[q] = {"p50": percentile(xs, 50), "p90": percentile(xs, 90), "max": max(xs),
                  "mean": round(sum(xs) / len(xs), 2)}  # fmt: skip
    for q, ceiling in targets.items():
        out[q]["target"] = ceiling
        out[q]["within"] = sum(m.get(q, 0) <= ceiling for m in measurements)
    out["within"] = sum(within(m, targets) for m in measurements)
    return out


def line(measurement: dict, targets: dict) -> str:
    """A measurement in a line, against the targets."""
    met = check(measurement, targets)
    parts = [f"{measurement['seconds']:.1f} s", f"{measurement['tokens']:,.0f} tokens"]
    parts.append(f"{measurement['llm_calls']:.0f} LLM calls" + (f" ({measurement['llm_cached']:.0f} cached)"
                                                              if measurement["llm_cached"] else ""))  # fmt: skip
    parts.append(f"${measurement['cost']:.3f}")
    if measurement["warehouse_queries"]:
        parts.append(f"{measurement['warehouse_queries']:.0f} warehouse queries")
    verdict = ", ".join(f"{k} {'met' if ok else 'missed'} ({targets[k]:,})" for k, ok in met.items())
    return "; ".join(parts) + (f". Targets: {verdict}" if targets else "")
