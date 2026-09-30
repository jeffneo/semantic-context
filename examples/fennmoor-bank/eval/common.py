"""What the Fennmoor evaluations share: paths, the answer key's names in the graph's spelling, and
partition agreement (NMI, ARI).

The evaluations are the only code that reads both the spec (the answer key) and what qlsc built.
"""

from __future__ import annotations

import json
from collections import Counter
from math import log
from pathlib import Path

from qlsc import config
from qlsc.names import canonical_table
from qlsc_parse.catalog import Catalog

EXAMPLE = Path(__file__).resolve().parents[1]
SPEC, BUILD, RESULTS = EXAMPLE / "spec", EXAMPLE / "build", EXAMPLE / "results"


def settings() -> config.Settings:
    return config.load(EXAMPLE / "estate.yaml")


def build(name: str):
    """A file the spec's build wrote (generate/build.py)."""
    return json.loads((BUILD / name).read_text())


def write_result(name: str, markdown: list[str], data: dict, where: Path = RESULTS) -> Path:
    """An evaluation's report (.md) and its data (.json): in results/, which the docs quote, unless
    `where` says otherwise (an experiment's, in work/)."""
    where.mkdir(parents=True, exist_ok=True)
    as_list = lambda x: sorted(x, key=str) if isinstance(x, set | frozenset) else list(x)  # a set, in order
    (where / f"{name}.json").write_text(json.dumps(data, indent=1, default=as_list))
    (where / f"{name}.md").write_text("\n".join(markdown) + "\n")
    return where / f"{name}.md"


def commit() -> str:
    """The commit the code under test is at, with a mark when the tree has changes."""
    import subprocess

    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=EXAMPLE
    )
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", "src", "prompts"],
        capture_output=True,
        text=True,
        cwd=EXAMPLE.parents[1],
    )
    return head.stdout.strip() + ("+changes" if dirty.stdout.strip() else "")


def quantiles(xs: list[float]) -> dict:
    """The median and 95th percentile."""
    import statistics

    xs = sorted(xs)
    if not xs:
        return {}
    return {
        "median": round(statistics.median(xs), 3),
        "p95": round(xs[min(len(xs) - 1, round(0.95 * (len(xs) - 1)))], 3),
    }


def native(v):
    """A value from Neo4j or BigQuery, comparable across the two."""
    import datetime as dt
    from decimal import Decimal

    v = v.to_native() if hasattr(v, "to_native") else v
    if isinstance(v, Decimal):
        v = float(v)
    if isinstance(v, float):
        return float(f"{v:.9g}")
    if isinstance(v, dt.datetime):  # Virtual Graph returns a TIMESTAMP without its zone: it is UTC
        return (v if v.tzinfo else v.replace(tzinfo=dt.UTC)).astimezone(dt.UTC).isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    return v


class Names:
    """The spec's table and column names, spelled as the graph spells them (the parser's rules,
    from the catalog snapshot qlsc extracted)."""

    def __init__(self, s: config.Settings, wh: dict):
        self.catalog = Catalog(json.loads((s.work / "catalog.json").read_text()))
        self.cols = {
            self.table(t["fqn"]): {c["name"].lower(): c["name"] for c in t["columns"]} for t in wh["tables"]
        }

    def table(self, fqn: str) -> str:
        return canonical_table(self.catalog, fqn)

    def column(self, fqn_col: str) -> str | None:
        t, _, c = fqn_col.rpartition(".")
        t = self.table(t)
        spelled = self.cols.get(t, {}).get(c.lower())
        return f"{t}.{spelled}" if spelled else None


def nmi(pred: dict, true: dict) -> float:
    """Normalized mutual information of two partitions over their shared items."""
    items = [x for x in pred if x in true]
    n = len(items)
    if not n:
        return 0.0
    pa, pb = Counter(pred[x] for x in items), Counter(true[x] for x in items)
    joint = Counter((pred[x], true[x]) for x in items)
    mi = sum(c / n * log((c / n) / ((pa[a] / n) * (pb[b] / n))) for (a, b), c in joint.items())
    ha = -sum(c / n * log(c / n) for c in pa.values())
    hb = -sum(c / n * log(c / n) for c in pb.values())
    return 2 * mi / (ha + hb) if ha + hb else 1.0


def ari(a: dict, b: dict) -> float:
    """Adjusted Rand index of two partitions over their shared items (1 = identical)."""
    keys = a.keys() & b.keys()
    pairs = lambda n: n * (n - 1) / 2
    joint = Counter((a[k], b[k]) for k in keys)
    ra, rb = Counter(a[k] for k in keys), Counter(b[k] for k in keys)
    index = sum(pairs(n) for n in joint.values())
    ea, eb, n = sum(pairs(x) for x in ra.values()), sum(pairs(x) for x in rb.values()), pairs(len(keys))
    expected = ea * eb / n if n else 0
    top = (ea + eb) / 2
    return (index - expected) / (top - expected) if top != expected else 1.0


def overrides(s, argv: list[str]) -> tuple[list[str], str]:
    """`param=value` arguments set settings: a navigation parameter (tables=10), or any section's
    (memory.cap=100). The rest are returned, with a suffix naming the result file after the values
    that differ from the configured ones, so a run with overrides never writes over the baseline, and one
    that sets the defaults is the baseline."""
    import re

    import yaml

    sets = [a for a in argv if "=" in a and not a.startswith("--")]
    changed = []
    for a in sets:
        k, v = a.split("=", 1)
        section, _, key = k.rpartition(".")
        where, value = s[section or "navigate"], yaml.safe_load(v)
        if where.get(key) != value:
            changed.append(a)
        where[key] = value
    return [a for a in argv if a not in sets], "".join(f"_{re.sub(r'\W+', '_', a)}" for a in changed)
