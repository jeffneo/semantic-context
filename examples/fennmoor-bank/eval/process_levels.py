"""Process abstraction, phase 1 (plans/2026-10-06-process-abstraction.md): do the levels above the first answer what the first level showed?

The first level is faithful and fine: about 800 Action elements for 64 planted actions (completeness 0.65), a quarter of State turns in a State
no other turn shares. Each level is scored as the first was (eval/process_graph.py: V-measure against the planted action and State key, stage
purity, fidelity, the share of turns in a singleton, turns with a recommendation), by level, on the tuning conversations (the first 600 by id)
and on the holdout (the rest).

  (default)  the levels in the process database, by level
  --grid     grouping only (no naming): similarity x resolution x transition weight, each a whole hierarchy, scored on the TUNING conversations.
             The rule for choosing, fixed before looking: at level 2 the States' stage purity is at least 0.85 and the Actions' homogeneity at
             least 0.90; of those, the one with the highest Action V + State V (against the planted State key); a tie goes to fewer elements.

Writes results/process_levels.md and .json (or process_levels_grid.md). Usage: uv run examples/fennmoor-bank/eval/process_levels.py [--grid]
"""

from __future__ import annotations

import json
import sys
from itertools import product

import process_graph as pg
from common import settings, write_result

from qlsc.graph import Graph
from qlsc.process import abstract

GATES = {"stage_purity": 0.85, "action_homogeneity": 0.90}


def load(s):
    rows = [
        json.loads(line) for line in (s.work / "process" / "observations.ndjson").read_text().splitlines()
    ]
    return rows, pg.Planted(rows)


def row_of(sc: dict) -> dict:
    a, d = sc["abstraction"], sc["diagnostic"]
    return {
        "states": a["elements"]["state"],
        "actions": a["elements"]["action"],
        "action_h": a["action"][0],
        "action_c": a["action"][1],
        "action_v": a["action"][2],
        "state_v": a["state_fine"][2],
        "state_coarse_v": a["state_coarse"][2],
        "stage_purity": a["stage_purity"],
        "singleton_states": a["singleton_turns"]["state"],
        "singleton_actions": a["singleton_turns"]["action"],
        "fidelity": sc["fidelity"]["pearson"],
        "coverage": d["coverage"],
        "diag": d["graph"],
    }


def table(levels: dict[int, dict]) -> list[str]:
    return [
        "| level | States | Actions | Action h / c / V | State V (key) | State V (coarse) | stage purity | singleton turns (S / A) | fidelity r | turns with a recommendation |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *[
            f"| {lv} | {r['states']} | {r['actions']} | {r['action_h']:.2f} / {r['action_c']:.2f} / **{r['action_v']:.2f}** | {r['state_v']:.2f} | "
            f"{r['state_coarse_v']:.2f} | {pg.pct(r['stage_purity'])} | {pg.pct(r['singleton_states'])} / {pg.pct(r['singleton_actions'])} | "
            f"{r['fidelity']:.2f} | {pg.pct(r['coverage'])} |"
            for lv, r in sorted(levels.items())
        ],
    ]


def ancestors(G: Graph, first: set[str], level: int) -> dict[str, str]:
    """Each first-level element's node at `level`: its highest ancestor of that level or below."""
    parent = {
        r["c"]: (r["p"], r["lv"])
        for r in G.rows("MATCH (c)-[:PART_OF]->(p) RETURN c.id AS c, p.id AS p, p.level AS lv")
    }
    out = {}
    for e in first:
        node = e
        while node in parent and parent[node][1] <= level:
            node = parent[node][0]
        out[e] = node
    return out


def main() -> None:
    s = settings()
    if "--grid" in sys.argv:
        return grid(s)
    rows, p = load(s)
    all_convs = sorted({r["conversation"] for r in rows})
    subsets = {"tuning": set(all_convs[: pg.TUNING]), "holdout": set(all_convs[pg.TUNING :])}
    with Graph(s, {"database": s["process"]["database"]}) as G:
        top = G.value("MATCH (n) WHERE n:State OR n:Action RETURN max(n.level)")
        first = {r["element"] for r in rows}
        scored: dict[str, dict[int, dict]] = {k: {} for k in subsets}
        for level in range(1, top + 1):
            of = ancestors(G, first, level)
            element_of = {r["event"]: of[r["element"]] for r in rows}
            for name, convs in subsets.items():
                scored[name][level] = row_of(pg.score(p, rows, element_of, convs=convs))
            print(f"  level {level} scored", flush=True)
    md = [
        "# Process abstraction, phase 1: the levels above the first",
        "",
        f"{len(all_convs)} conversations, one hierarchy built from all of them (`qlsc process abstract`), scored against the answer key by level. "
        f"Parameters: {json.dumps(s['process']['levels'])}. The tuning slice is the first {pg.TUNING} conversations by id, where the "
        "parameters were chosen; the holdout is the rest.",
        "",
        "## The holdout",
        "",
        *table(scored["holdout"]),
        "",
        "## The tuning conversations",
        "",
        *table(scored["tuning"]),
    ]
    print(write_result("process_levels", md, {"scored": scored, "parameters": s["process"]["levels"]}))
    print("\n".join(md))


def grid(s) -> None:
    """Each setting is a whole hierarchy built by the real stage (`abstract.run`, unnamed) and read back from the database; the database is left
    as the last setting made it, so the default build is run again at the end."""
    rows, p = load(s)
    all_convs = sorted({r["conversation"] for r in rows})
    tuning = set(all_convs[: pg.TUNING])
    first = {r["element"] for r in rows}
    results = []
    base = pg.score(p, rows, {r["event"]: r["element"] for r in rows}, convs=tuning)
    results.append({"setting": "level 1 (as built)", "levels": {1: row_of(base)}})
    sims = [float(x) for x in pg.option("--sims", "0.75,0.80,0.85,0.90").split(",")]
    gammas = [float(x) for x in pg.option("--gammas", "1.0,2.0,4.0").split(",")]
    weights = [float(x) for x in pg.option("--weights", "0.0,0.3").split(",")]
    for sim, gamma, weight in product(sims, gammas, weights):
        params = {
            **s["process"]["levels"],
            "kinds": ["state", "action"],  # the grid asks of both, whatever the default builds
            "similarity": sim,
            "gamma": gamma,
            "transition_weight": weight,
        }
        info = abstract.run(s, params, naming=False)
        scored = {}
        with Graph(s, {"database": s["process"]["database"]}) as G:
            for lv in range(2, 2 + len(info["levels"])):
                of = ancestors(G, first, lv)
                scored[lv] = row_of(
                    pg.score(p, rows, {r["event"]: of[r["element"]] for r in rows}, convs=tuning)
                )
        results.append(
            {"setting": f"sim {sim}, gamma {gamma}, transitions {weight}", "params": params, "levels": scored}
        )
        print(
            results[-1]["setting"],
            {
                k: (
                    v["states"],
                    v["actions"],
                    round(v["action_v"], 2),
                    round(v["state_v"], 2),
                    round(v["stage_purity"], 2),
                )
                for k, v in scored.items()
            },
            flush=True,
        )
    abstract.run(s)  # the default levels again

    def passes(r: dict) -> bool:
        l2 = r["levels"].get(2)
        return (
            bool(l2)
            and l2["stage_purity"] >= GATES["stage_purity"]
            and l2["action_h"] >= GATES["action_homogeneity"]
        )

    ranked = sorted(
        (r for r in results if passes(r)),
        key=lambda r: (
            -(r["levels"][2]["action_v"] + r["levels"][2]["state_v"]),
            r["levels"][2]["states"] + r["levels"][2]["actions"],
        ),
    )
    md = [
        "# Process abstraction, phase 1: the grouping parameters, by the score",
        "",
        f"Whole hierarchies, grouping only, scored on the tuning conversations (the first {pg.TUNING} by id). The rule, set beforehand: at level 2 "
        f"stage purity at least {GATES['stage_purity']} and Action homogeneity at least {GATES['action_homogeneity']}; of those, the highest Action V + State V.",
        "",
        "| setting | level | States | Actions | Action h / c / V | State V | stage purity | singleton (S / A) | fidelity | recommended |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        mark = "**passes**" if passes(r) else ""
        for lv, x in sorted(r["levels"].items()):
            md.append(
                f"| {r['setting'] if lv == min(r['levels']) else ''} {mark if lv == min(r['levels']) else ''} | {lv} | {x['states']} | {x['actions']} | "
                f"{x['action_h']:.2f} / {x['action_c']:.2f} / {x['action_v']:.2f} | {x['state_v']:.2f} | {pg.pct(x['stage_purity'])} | "
                f"{pg.pct(x['singleton_states'])} / {pg.pct(x['singleton_actions'])} | {x['fidelity']:.2f} | {pg.pct(x['coverage'])} |"
            )
    md += ["", "Chosen: " + (ranked[0]["setting"] if ranked else "none passes the gates")]
    print(
        write_result(
            "process_levels_grid",
            md,
            {"results": results, "chosen": ranked[0]["setting"] if ranked else None},
        )
    )


if __name__ == "__main__":
    main()
