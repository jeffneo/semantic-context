"""The comparison: qlsc's answers against naive ones, on the business's own questions (README.md here).

Every method answers the same 186 questions: the gold questions that are scored, and every log question
kept (eval/log_questions.py: one per query the business ran, its result the reference answer), with
match.py's ruler and the log questions' leave-one-out (the query a question was written from is never
offered to answer it).
  naive-schema  the model with the warehouse's schema in its prompt, no semantic layer (naive.py)
  naive-agent   a generic tool-using agent over the warehouse's schema, no semantic layer (naive.py)
  layer         qlsc's compiled request, one shot, as the log evaluations score it (navigate.answer_sql)
  agent         qlsc as an AI agent uses it (consumer.py): the agent holds its process's state, writes its
                request, checks each answer and corrects it; qlsc answers by its router, precedent first
Each is Sonnet 5.5, measured the same way (qlsc/meter.py): tokens and seconds per request, from the request
to its final answer, the service's share only (an agent's reading and writing is measured apart), and
whether it is right within the service's targets (defaults.yaml service.targets): delivered.

Each method's LLM calls have their own cache (<work>/llm_cache_comparison/<method>[.TAG]): a first run is
live and measured; a run again replays it (the report says so), and --fresh=TAG measures anew.

Usage: uv run examples/fennmoor-bank/eval/comparison/run.py prep                 # references, the agent's states
       uv run examples/fennmoor-bank/eval/comparison/run.py <method> [--workers=N] [--only=Q01,L...] [--fresh=TAG]
       uv run examples/fennmoor-bank/eval/comparison/run.py report               # -> results/comparison.md, .json
"""

from __future__ import annotations

import json
import sys
import threading
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # the evaluations' shared modules

import yaml  # noqa: E402
from common import RESULTS, SPEC, commit, native, settings, write_result  # noqa: E402
from log_questions import QUESTIONS, answers_dir  # noqa: E402
from match import ROWS, references, verdict  # noqa: E402

from qlsc import llm, meter, navigate  # noqa: E402
from qlsc.graph import Graph  # noqa: E402
from qlsc.warehouse import connect  # noqa: E402

METHODS = ("naive-schema", "naive-agent", "layer", "agent")


def text(name: str, **values) -> str:
    return (HERE / "prompts" / f"{name}.md").read_text().format(**values)


def out_dir(s) -> Path:
    d = s.work / "comparison"
    d.mkdir(parents=True, exist_ok=True)
    return d


def arg(name: str) -> str | None:
    return next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{name}=")), None)


# ---- the questions


def prep_references() -> list[str]:
    """The gold questions that are scored (a reference that compares something), their references run once."""
    s, wh = settings(), None
    wh = connect(s)
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    refs_dir = out_dir(s) / "refs"
    refs_dir.mkdir(exist_ok=True)
    scored = []
    for qid in sorted(gold):
        refs = references(wh, qid)
        if not any(r["items"] for r in refs):
            continue
        for r in refs:
            r["result"] = {k: native(v) if k != "rows" else [{c: native(x) for c, x in row.items()} for row in v]
                           for k, v in r["result"].items()}  # fmt: skip
        (refs_dir / f"{qid}.json").write_text(json.dumps(refs, default=str))
        scored.append(qid)
    return scored


def questions(s) -> list[dict]:
    """[{qid, group (gold | log), question, shape, refs, sql (the reference's)}], in a fixed order."""
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    logq = yaml.safe_load(QUESTIONS.read_text())
    kept = sorted(
        q for q, r in json.loads((RESULTS / "log_answers.json").read_text()).items() if r["verdict"] == "kept"
    )
    out = []
    for path in sorted((out_dir(s) / "refs").glob("Q*.json")):
        qid = path.stem
        out.append({"qid": qid, "group": "gold", "question": gold[qid]["question"], "shape": None,
                    "refs": json.loads(path.read_text()), "sql": (HERE.parent / "reference" / f"{qid}.sql").read_text()})  # fmt: skip
    for qid in kept:
        q = logq[qid]
        refs = [{"name": qid, "items": [[c] for c in q["compare"]],
                 "result": json.loads((answers_dir(s) / f"{qid}.json").read_text())}]  # fmt: skip
        out.append({"qid": qid, "group": "log", "question": q["question"], "shape": q["shape"], "refs": refs,
                    "sql": q["sql"], "tables": q.get("tables")})  # fmt: skip
    return out


def trace_of(G, s, q: dict, question: str | None = None) -> dict:
    """Navigation for a question, the question's own query left out (the log questions' leave-one-out)."""
    exclude = frozenset({q["shape"]}) if q["shape"] else frozenset()
    return navigate.trace(G, s, question or q["question"], exclude=exclude)


# ---- running questions in parallel: what the tool shares between calls, made safe to share


def safe_unique_checks() -> None:
    """navigate.unique_check writes its cache file on a miss; parallel questions mustn't race on it. Read it
    once, and keep new answers in the process."""
    lock, known = threading.Lock(), {}

    def unique_check(s):
        path = s.work / "unique_cache.json"
        if not known:
            known.update(json.loads(path.read_text()) if path.exists() else {})
        wh = connect(s)

        def unique(table: str, column: str) -> bool:
            key = f"{table}|{column}"
            with lock:
                if key in known:
                    return known[key]
            got = wh.is_unique(table, [column])
            with lock:
                known[key] = got
            return got

        return unique

    navigate.unique_check = unique_check


def safe_embeddings(name: str) -> None:
    """The shared embedding cache read once and never written (a file half written breaks other readers);
    a text not in it is embedded into this method's own cache, one at a time (and measured)."""
    import hashlib

    real_init, real_embed = llm.Embedder.__init__, llm.Embedder.embed
    lock, state = threading.Lock(), {}

    def init(self, settings_):
        with lock:
            if not state:
                real_init(self, settings_)
                own = out_dir(settings_) / f"embeddings-{name}.json"
                state.update(shared=self.cache, url=self.url, key=self.key, dims=self.dims, path=own,
                             own=json.loads(own.read_text()) if own.exists() else {})  # fmt: skip
            self.url, self.key, self.dims = state["url"], state["key"], state["dims"]
            self.cache, self.cache_path = state["own"], state["path"]

    def embed(self, texts):
        keys = [hashlib.sha256(f"{self.dims}|{t}".encode()).hexdigest() for t in texts]
        missing = [t for k, t in zip(keys, texts) if k not in state["shared"]]
        with lock:
            if missing:
                real_embed(self, missing)
            return [state["shared"].get(k) or state["own"][k] for k in keys]

    llm.Embedder.__init__, llm.Embedder.embed = init, embed


def own_cache(name: str) -> None:
    """The query model's calls in this method's own cache: a first run is live, and so measured."""
    init = llm.LLM.__init__

    def patched(self, system, settings_, model_=None):
        init(self, system, settings_, model_)
        if self.model == settings_["llm"]["query_model"]:
            self.cache = settings_.work / "llm_cache_comparison" / name
            self.cache.mkdir(parents=True, exist_ok=True)

    llm.LLM.__init__ = patched


# ---- a run


def run(name: str, answer, workers: int, only: set | None = None) -> dict:
    """Answer every question with `answer(G, s, q) -> answer dict`, score and measure it, write the results.
    An answer that is an exchange scores itself (`scored`: (verdict, why); `delivered`)."""
    s = settings()
    tag = arg("fresh")
    cache = name + (f".{tag}" if tag else "")
    safe_unique_checks()
    safe_embeddings(cache)
    own_cache(cache)
    targets = s["service"]["targets"]
    if (probe := connect(s).dry_run("SELECT 1"))["ok"] is not True:
        raise SystemExit(f"the warehouse isn't reachable: {probe.get('error')}")
    todo = [q for q in questions(s) if not only or q["qid"] in only]
    res: dict = {}
    t0 = time.time()
    with Graph(s) as G:

        def one(q: dict) -> tuple[str, dict]:
            with meter.measure() as m:
                try:
                    a = answer(G, s, q)
                    v, why = a.get("scored") or verdict(a, q["refs"])
                except Exception as e:  # one question's failure is a verdict, not the run's end
                    a, v, why = (
                        {"error": repr(e)[:300], "trace": traceback.format_exc()[-600:]},
                        "failed",
                        repr(e)[:160],
                    )
            measured = m.measure()
            measured["turns"] = measured["turns"] or 1
            delivered = a.get("delivered", v == "correct" and meter.within(measured, targets))
            r = {"group": q["group"], "verdict": v, "why": why, "delivered": delivered, "measure": measured,
                 "sql": a.get("sql"), "route": a.get("route") or a.get("writer"), **a.get("exchange", {})}  # fmt: skip
            print(f"{name} {q['qid']:10} {q['group']:4} {v:10} {measured['tokens']:>8,.0f} tok "
                  f"{measured['seconds']:>5.1f} s  {why[:70]}", flush=True)  # fmt: skip
            return q["qid"], r

        with ThreadPoolExecutor(workers) as pool:
            for qid, r in pool.map(one, todo):
                res[qid] = r
    info = {"commit": commit(), "seconds": round(time.time() - t0), "targets": targets, "cache": cache,
            "replayed": sum(r["measure"]["llm_cached"] for r in res.values())}  # fmt: skip
    (out_dir(s) / f"{name}.json").write_text(json.dumps(res | {"_run": info}, indent=1, default=str))
    right = Counter((r["group"], r["verdict"] == "correct") for r in res.values())
    print(f"{name}: " + ", ".join(f"{g} {right[(g, True)]}/{right[(g, True)] + right[(g, False)]}" for g in ("gold", "log"))
          + f" in {info['seconds']} s")  # fmt: skip
    return res


# ---- the report


def percentile(xs: list[float], p: float) -> float:
    return meter.percentile(xs, p) if xs else 0


def report() -> int:
    s = settings()
    runs = {m: json.loads(p.read_text()) for m in METHODS if (p := out_dir(s) / f"{m}.json").exists()}
    data, L = {}, []
    for part in ("log", "gold"):
        L += [f"**{'Log questions' if part == 'log' else 'Gold questions'}**", "",
              "| method | right | delivered | tokens p50 / p90 | seconds p50 / p90 | $ per request | $ per right answer |",
              "|---|---|---|---|---|---|---|"]  # fmt: skip
        for m, res in runs.items():
            qs = [q for q, r in res.items() if not q.startswith("_") and r["group"] == part]
            ms = [res[q]["measure"] for q in qs]
            right = sum(res[q]["verdict"] == "correct" for q in qs)
            deliv = sum(bool(res[q]["delivered"]) for q in qs)
            cost = sum(x["cost"] for x in ms)
            tok = [x["tokens"] for x in ms]
            sec = [x["seconds"] for x in ms]
            row = {"n": len(qs), "right": right, "delivered": deliv, "tokens_p50": percentile(tok, 50),
                   "tokens_p90": percentile(tok, 90), "seconds_p50": percentile(sec, 50),
                   "seconds_p90": percentile(sec, 90), "cost": round(cost, 3),
                   "replayed": res["_run"]["replayed"], "commit": res["_run"]["commit"]}  # fmt: skip
            data.setdefault(m, {})[part] = row
            L.append(f"| {m} | {right} of {len(qs)} ({right / len(qs):.0%}) | {deliv} ({deliv / len(qs):.0%}) | "
                     f"{row['tokens_p50']:,.0f} / {row['tokens_p90']:,.0f} | {row['seconds_p50']:.1f} / "
                     f"{row['seconds_p90']:.1f} | {cost / len(qs):.3f} | {cost / max(right, 1):.3f} |")  # fmt: skip
        L.append("")
    if "agent" in runs:
        res = {q: r for q, r in runs["agent"].items() if not q.startswith("_")}
        outcomes = Counter(r["outcome"] for r in res.values())
        first = Counter(r["turns"][0]["route"] for r in res.values())
        first_right = Counter(
            r["turns"][0]["route"] for r in res.values() if r["turns"][0]["verdict"] == "correct"
        )
        data["agent"]["outcomes"], data["agent"]["first_route"] = dict(outcomes), dict(first)
        L += ["**The agent's exchanges** (186): " + "; ".join(f"{k} {v}" for k, v in outcomes.most_common()) + ".",
              "", "First answers by route: " + "; ".join(f"{k} {v} ({first_right[k]} right)" for k, v in first.most_common())
              + ". Consumer's own spend: $" + f"{sum(r['consumer']['cost'] for r in res.values()):.2f}.", ""]  # fmt: skip
    replayed = {m: r["_run"]["replayed"] for m, r in runs.items() if r["_run"]["replayed"]}
    L += [f"Targets: {s['service']['targets']}. " + (f"Replayed from the cache, so not measured: {replayed}."
          if replayed else "Every LLM call live: measured.")]  # fmt: skip
    path = write_result("comparison", ["# The comparison: qlsc against naive approaches", ""] + L, data)
    print("\n".join(L))
    print(f"-> {path}")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = set(arg("only").split(",")) if arg("only") else None
    workers = int(arg("workers") or 6)
    if args[0] == "prep":
        import consumer

        scored = prep_references()
        print(f"{len(scored)} gold questions scored")
        return consumer.prep()
    if args[0] == "report":
        return report()
    name = args[0]
    if name.startswith("naive-"):
        import naive

        run(name, naive.answer_schema if name == "naive-schema" else naive.answer_agent, workers, only)
    elif name == "layer":
        run(
            name,
            lambda G, s, q: navigate.answer_sql(G, s, trace_of(G, s, q), execute=True, rows=ROWS),
            workers,
            only,
        )
    elif name == "agent":
        import consumer

        run(name, consumer.answerer(), workers, only)
    else:
        raise SystemExit(f"a method: {', '.join(METHODS)}, or prep, report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
