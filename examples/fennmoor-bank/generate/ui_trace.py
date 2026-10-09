"""Write the demo UI's agent traces -> ui/src/examples/fennmoor/memory/traces.json.

An agent's work is kept in the memory database as a graph (qlsc/converse.py): the conversation's messages, the task each request started, the tool calls
(steps) of each task and the layer's tables and computations they read, what was learned (facts, and what each replaced), and the decisions, each based on
the facts and the tool calls it rests on. This reads the example's conversations back from it (`qlsc converse conversations/<name>.yaml` records one), each as
the transcript with its tool calls where they were made:
  messages  in order: who said it, the words, and under a user's message the tools its task called, what was learned, and what was decided
Only what the graph holds is written: the words, the tools, their arguments and results, what they read, how long they took. It holds no reasoning beyond a
decision's rationale, so none is shown. The principal is the one the conversation acts for (never a service account's address).
Usage: uv run examples/fennmoor-bank/generate/ui_trace.py   (the memory database must hold the conversations)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from ui_queries import query

from qlsc import config, memory

EXAMPLE = Path(__file__).resolve().parents[1]
PROJECT = config.load(EXAMPLE / "estate.yaml")["warehouse"][
    "project"
]  # the physical project: never in what is written
ROOT = EXAMPLE.parents[1]
OUT = ROOT / "ui" / "src" / "examples" / "fennmoor" / "memory" / "traces.json"

TITLES = (  # the example's conversations (conversations/*.yaml), in the order a banker's days run; support-1 waits for the process graph
    "Card offer for customer 8322097816940277129",
    "Travel card follow-up for customer 8322097816940277129",
    "Review of customer -9222608688654483010",
)

CONVERSATIONS = query("memory", "trace_conversations")
MESSAGES = query("memory", "trace_messages")
STEPS = query("memory", "trace_steps")
LEARNED = query("memory", "trace_learned")
DECISIONS = query("memory", "trace_decisions")


def tool(r: dict) -> dict:
    """One step: its words and numbers, from what the step recorded."""
    args, res = json.loads(r["arguments"] or "{}"), json.loads(r["result"] or "{}")
    out = {
        "tool": r["tool"],
        "status": r["status"],
        "ms": r["ms"],
        "reads": [x for x in r["reads"] if x["name"]],
    }
    if r["tool"] == "recall":
        out |= {
            "asked": f"{args['label']} {args['key']}",
            "origin": res.get("origin"),
            "nodes": res.get("nodes"),
            "edges": res.get("edges"),
        }
    elif r["tool"] == "ask":
        out |= {
            "asked": args["question"],
            "route": res.get("route"),
            "writer": res.get("writer"),
            "query": res.get("query"),
            "fromMemory": bool(res.get("from_memory")),
        }
    else:
        out |= {"asked": json.dumps(args)[:200]}
    return out


def conversation(M, c: dict, principals: dict[str, str]) -> dict:
    steps: dict[str, list[dict]] = {}
    for r in M.rows(STEPS, id=c["id"]):
        steps.setdefault(r["task"], []).append(tool(r))
    learned: dict[str, list[dict]] = {}
    for r in M.rows(LEARNED, id=c["id"]):
        learned.setdefault(r["message"], []).append(
            {
                k: v
                for k, v in {
                    "predicate": r["predicate"],
                    "value": r["value"],
                    "origin": r["origin"],
                    "entity": r["entity"],
                    "entityType": r["entity_type"],
                    "because": r["because"],
                    "replaced": r["replaced"],
                }.items()
                if v
            }
        )
    decided: dict[str, list[dict]] = {}
    for r in M.rows(DECISIONS, id=c["id"]):
        decided.setdefault(r["task"], []).append(
            {
                "choice": r["choice"],
                "rationale": r["rationale"],
                "alternatives": r["alternatives"] or [],
                "basedOn": [x for x in r["based_on"] if x["what"]],
                "outcome": r["outcome"],
            }
        )
    messages = []
    for r in M.rows(MESSAGES, id=c["id"]):
        m = {"role": r["role"], "text": r["text"]}
        if r["task"]:
            m |= {"tools": steps.get(r["task"], []), "decided": decided.get(r["task"], [])}
        if learned.get(r["id"]):
            m["learned"] = learned[r["id"]]
        messages.append(m)
    return {
        "title": c["title"],
        "as": principals.get(c["owner"], c["owner"]),
        "started": c["started_at"].isoformat(),
        "messages": messages,
    }


def main() -> None:
    s = config.load(EXAMPLE / "estate.yaml")
    principals = {
        v: k for k, v in s["entitlements"]["principals"].items()
    }  # a service account's address -> the principal it stands for
    with memory.memory_graph(s) as M:
        found = {c["title"]: c for c in M.rows(CONVERSATIONS, titles=list(TITLES))}
        missing = [t for t in TITLES if t not in found]
        assert not missing, f"not in memory (qlsc converse conversations/<name>.yaml records one): {missing}"
        out = {"conversations": [conversation(M, found[t], principals) for t in TITLES]}
    text = json.dumps(out, separators=(",", ":"), sort_keys=True)
    assert PROJECT not in text and "fnb_" not in text and "iam.gserviceaccount" not in text, (
        "the physical project or an address is named"
    )
    assert not re.search(r"@[a-z-]+\.", text), "an address is named"
    OUT.write_text(text + "\n")
    n = [
        (len(c["messages"]), sum(len(m.get("tools", [])) for m in c["messages"]))
        for c in out["conversations"]
    ]
    print(
        f"{OUT.relative_to(ROOT)}: {len(n)} conversations, (messages, tool calls) {n}, {OUT.stat().st_size / 1024:.0f} KB"
    )


if __name__ == "__main__":
    main()
