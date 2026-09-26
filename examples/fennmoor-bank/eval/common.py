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


def write_result(name: str, markdown: list[str], data: dict) -> Path:
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(data, indent=1, default=list))
    (RESULTS / f"{name}.md").write_text("\n".join(markdown) + "\n")
    return RESULTS / f"{name}.md"


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
