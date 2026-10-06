"""Process graph, phase 5 (plans/2026-10-05-text-graph-construction.md): can the context a call is about be fetched from the warehouse as of
the call, and are the rows its words name found in it?

For a sample of conversations (half whose answer key names a fee or a merchant, half control conversations that name neither), runs
`qlsc process context`'s logic and scores it against the answer key's `mentions`, which the tool never reads:
  retrieval   is the row the call is about in the context fetched as of the call (the virtual graph for merchants, the warehouse for fees)?
              And what would memory's ordinary window (from the quarter before today's, no end) have put in the context that did not exist
              yet when the call was made? (The contrast is the case for as-of.)
  linking     of the rows retrieved, are the right ones linked from the words, by lookup (a name, an amount said or written)? Precision and
              recall by type, over the turns alone (what the builder reads) and with the agent's after-call note.
  cost        seconds per context.

Writes results/process_context.md and .json. Spends BigQuery bytes (the virtual graph's reads, a fee read): cents. About ten seconds a context.
Usage: uv run examples/fennmoor-bank/eval/process_context.py [per_group=40]
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import sys
import time
from collections import defaultdict
from statistics import median

from common import BUILD, settings, write_result

from qlsc import memory
from qlsc.process import context, source
from qlsc.process.source import Turn

TYPE_OF = {"Merchant": "Merchant", "dw_core.fct_fees": "Fee"}


def sample(per_group: int) -> list[dict]:
    """The conversations scored, by id order: those the answer key says name a fee, a merchant, and neither."""
    groups = {"Fee": [], "Merchant": [], "neither": []}
    with gzip.open(BUILD / "corpus" / "full" / "truth.ndjson.gz", "rt") as f:
        for line in f:
            t = json.loads(line)
            if not t["events"] or t["follow_up_of"] is not None:
                continue
            mentions = {(m["type"], m["key"]) for e in t["events"] for m in e["mentions"]}
            kinds = {k for k, _ in mentions}
            for name in ("Fee", "Merchant"):
                if kinds == {name}:
                    groups[name].append(
                        {"conversation": t["conversation_id"], "truth": mentions, "group": name}
                    )
            if not mentions:
                groups["neither"].append(
                    {"conversation": t["conversation_id"], "truth": set(), "group": "neither"}
                )
    out = []
    for g in groups.values():
        out += sorted(g, key=lambda x: x["conversation"])[
            : per_group // 2 if g is groups["neither"] else per_group
        ]
    return out


def notes_of(conversations: set[str]) -> dict[str, str]:
    """The agent's after-call note per conversation (a turn the builder does not read, a text the linking may)."""
    out = {}
    with gzip.open(BUILD / "corpus" / "full" / "events.ndjson.gz", "rt") as f:
        for line in f:
            e = json.loads(line)
            if e["channel"] == "case_note" and e["conversation_id"] in conversations:
                out[e["conversation_id"]] = e["text"]
    return out


def main() -> None:
    s = settings()
    per_group = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    picked = sample(per_group)
    src = source.read(s)
    notes = notes_of({p["conversation"] for p in picked})
    m = memory.reader_model(s, None)
    results, retries, t0 = [], [], time.time()
    for i, p in enumerate(picked, 1):
        cid = p["conversation"]
        turns = src.conversations[cid]
        note = Turn("note", cid, 10**6, "", "case_note", "agent", "action", notes.get(cid, ""))
        for attempt in range(
            3
        ):  # the virtual graph refused a read once under load ("Unsupported parameter type List"), then answered the same
            try:
                c = context.at(s, cid, turns, model=m)
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 2:
                    raise
                retries.append((cid, str(e)[:80]))
                time.sleep(10)
        with_note = context.link(
            s["process"]["context"]["match"], {**c["nodes"], **c["also"]}, _keys(s, m, c), [*turns, note]
        )
        key = c["subject"]["key"]
        if key is None:  # no customer on the call: nothing was fetched, and nothing can be linked
            results.append(
                {
                    **p,
                    "truth": sorted(map(list, p["truth"])),
                    "retrieved": [],
                    "postdating": {},
                    "todays_context": 0,
                    "turns_only": [],
                    "with_note": [],
                    "seconds": c["seconds"],
                    "as_of": str(c["as_of"]),
                    "no_customer": True,
                }
            )
            print(f"  {i}/{len(picked)} {cid[:8]} {p['group']}: no customer on the call", flush=True)
            continue
        with memory.virtual_graph(
            s
        ) as V:  # memory's ordinary window: facts up to today, whenever the call was
            today = memory.run_batch(
                s,
                m,
                memory.template(m, c["subject"]["label"], s["memory"]["hops"]),
                [key],
                V,
                False,
                dt.datetime.now(dt.UTC),
            )[key]
        day = context.date_of(c["as_of"])
        later = {
            label: sum(
                1 for (lb, _), row in today.nodes.items() if lb == label and context.date_of(row[part]) > day
            )
            for label in m.nodes
            if (part := m.nodes[label]["partition"])
        }
        have = {("Merchant", r["merchant_id"]) for r in c["nodes"].get("Merchant", [])} | {
            ("Fee", r["fee_id"]) for r in c["also"].get("dw_core.fct_fees", [])
        }
        results.append(
            {
                **p,
                "truth": sorted(map(list, p["truth"])),
                "retrieved": [list(t) for t in p["truth"] if t in have],
                "postdating": later,
                "todays_context": len(today.nodes),
                "turns_only": sorted([TYPE_OF[x.label], x.key] for x in c["links"] if x.label in TYPE_OF),
                "with_note": sorted([TYPE_OF[x.label], x.key] for x in with_note if x.label in TYPE_OF),
                "seconds": c["seconds"],
                "as_of": str(c["as_of"]),
            }
        )
        print(f"  {i}/{len(picked)} {cid[:8]} {p['group']}: {c['seconds']} s", flush=True)
    wall = time.time() - t0

    def rates(variant: str, kind: str) -> tuple[int, int, int]:
        tp = fp = fn = 0
        for r in results:
            truth = {tuple(x) for x in r["truth"] if x[0] == kind}
            got = {tuple(x) for x in r[variant] if x[0] == kind}
            tp, fp, fn = tp + len(truth & got), fp + len(got - truth), fn + len(truth - got)
        return tp, fp, fn

    def pr(tp: int, fp: int, fn: int) -> str:
        return (
            f"{tp / (tp + fp):.0%} / {tp / (tp + fn):.0%} ({tp} found, {fp} wrong, {fn} missed)"
            if tp + fp and tp + fn
            else "-"
        )

    named = [(r, tuple(x)) for r in results for x in r["truth"]]
    total_truth = len(named)
    retrieved = sum(1 for r in results for x in r["retrieved"])
    leaked = {
        label: sum(r["postdating"].get(label, 0) for r in results)
        for label in ("CardTransaction", "DepositTransaction", "Call")
    }
    in_ordinary = sum(r["todays_context"] for r in results)
    by = defaultdict(list)
    for r in results:
        by[r["group"]].append(r["seconds"])
    md = [
        "# Process graph, phase 5: the context a call is about, as of the call",
        "",
        f"{len(results)} conversations ({', '.join(f'{len(v)} {k}' for k, v in by.items())}); a group is what the answer key says the conversation names. "
        f"Each context is fetched as of the call's day: {median(r['seconds'] for r in results):.1f} s median, {wall / 60:.0f} minutes for all.",
        "",
        "## Retrieval: is the row the call is about in the context?",
        "",
        f"- {len(retries)} reads were retried after the virtual graph refused them once.",
        f"- {sum(1 for r in results if r.get('no_customer'))} of the {len(results)} calls had no customer on them (nobody was identified): no context to fetch.",
        f"- As of the call: **{retrieved} of {total_truth}** named rows were in the context (merchants from the virtual graph, fees from the warehouse).",
        f"- Memory's ordinary window would have put **{sum(leaked.values()):,} facts into the contexts that postdate their calls** "
        f"({', '.join(f'{n:,} {k}' for k, n in leaked.items())}), of {in_ordinary:,} nodes: what the warehouse did not yet hold when the call was made.",
        "",
        "## Linking: of the rows retrieved, are the right ones found from the words? (precision / recall)",
        "",
        "| | Merchant (by amount and name) | Fee (by amount) |",
        "|---|---|---|",
        f"| the turns alone | {pr(*rates('turns_only', 'Merchant'))} | {pr(*rates('turns_only', 'Fee'))} |",
        f"| the turns and the after-call note | {pr(*rates('with_note', 'Merchant'))} | {pr(*rates('with_note', 'Fee'))} |",
        "",
        "The control conversations (the answer key names neither) are in the precision: a link there is a wrong one.",
    ]
    print(write_result("process_context", md, {"results": results, "seconds_wall": wall}))
    print("\n".join(md))


def _keys(s, m, c) -> dict[str, str]:
    cfg = s["process"]["context"]
    return {label: m.key(label) for label in c["nodes"]} | {
        r["table"]: r["key"] for r in cfg["match"] if "table" in r
    }


if __name__ == "__main__":
    main()
