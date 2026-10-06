"""Process graph, phase 4: how the stages that need no LLM grow with the size of the corpus.

The scale set (generate/corpus.py, build/corpus/scale/) is the demo corpus's plans with placeholder text, about ten times its size. Nobody
would annotate it ($150 and ten hours), so each of its turns stands in for an annotation: the placeholder text is the description, and
the stages after annotation run on it unchanged (embed, nearest neighbours, Leiden, lift, write) in a database of its own
(`processscale`), its elements numbered and not named. The text is repetitive by construction, so this says nothing about quality: only
about time, and whether anything stops scaling. Sizes are conversations taken in id order. Writes results/process_scale.md and .json.

Usage: uv run examples/fennmoor-bank/eval/process_scale.py [conversations ...]   (default 2000 10000 21161)
"""

from __future__ import annotations

import gzip
import json
import sys
import time
from collections import defaultdict

from common import BUILD, settings, write_result

from qlsc.graph import Graph
from qlsc.process import build

KINDS = {"customer": "state", "agent": "action"}
DATABASE = "processscale"


def stand_ins(limit: int) -> list[dict]:
    """Annotation records for the first `limit` conversations of the scale set: the turns, their text as the description."""
    by: dict[str, list[dict]] = defaultdict(list)
    with gzip.open(BUILD / "corpus" / "scale" / "events.ndjson.gz", "rt") as f:
        for line in f:
            e = json.loads(line)
            if e["channel"] in ("case_note", "system_log") or e["role"] not in KINDS:
                continue
            by[e["conversation_id"]].append(e)
    rows = []
    for c in sorted(by)[:limit]:
        for e in by[c]:
            rows.append(
                {
                    "event": e["event_id"],
                    "conversation": c,
                    "seq": e["seq"],
                    "kind": KINDS[e["role"]],
                    "description": e["text"],
                    "answer": {"latest_turn": e["text"], "established": e["text"]},
                    "problems": [],
                }
            )
    return rows


def main() -> None:
    s = settings()
    sizes = [int(x) for x in sys.argv[1:]] or [2000, 10000, 21161]
    out = []
    for n in sizes:
        rows = stand_ins(n)
        t0 = time.perf_counter()
        m = build.run(s, rows=rows, database=DATABASE, naming=False)
        wall = time.perf_counter() - t0
        out.append(
            {
                "conversations": n,
                "turns": len(rows),
                "wall_seconds": round(wall, 1),
                **{k: m[k] for k in ("seconds", "elements", "transitions")},
            }
        )
        print(out[-1], flush=True)
    stages = ["embed", "neighbours", "group", "lift", "write"]
    md = [
        "# Process graph, phase 4: the stages with no LLM, against the size of the corpus",
        "",
        "The scale set's placeholder text stands in for annotations (see the script); it is repetitive, so only the time means anything. "
        f"Database `{DATABASE}`, elements numbered, no naming.",
        "",
        "| conversations | turns | "
        + " | ".join(f"{x} s" for x in stages)
        + " | total s | seconds per 1,000 turns |",
        "|---|---|" + "---|" * (len(stages) + 2),
        *[
            f"| {r['conversations']:,} | {r['turns']:,} | "
            + " | ".join(f"{r['seconds'].get(x, 0):.1f}" for x in stages)
            + f" | {r['wall_seconds']} | {1000 * r['wall_seconds'] / r['turns']:.1f} |"
            for r in out
        ],
    ]
    print(write_result("process_scale", md, {"runs": out}))
    print("\n".join(md))
    with Graph(s, {"database": "system"}) as system:
        print("databases:", [r["name"] for r in system.rows("SHOW DATABASES YIELD name RETURN name")])


if __name__ == "__main__":
    main()
