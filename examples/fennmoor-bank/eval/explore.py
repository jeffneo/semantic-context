"""Exploring accuracy: candidate factors tested one at a time on one probe set, quick and directional
(plans/2026-09-30-accuracy-orthogonal.md, "The tests"). Not a result the docs quote: everything is
written to <work>/qdd/explore/.

The probe set (eval/explore_probe.yaml, frozen by `probe`): the gold questions that are scored, every
question the log's SQL route got wrong in the last full run (48), and every fourth it got right (32),
to catch a change that breaks what works. Each miss carries its cause as the plan reads it, so a
factor's gain is reported by the kind of miss it addresses; the "ruler" misses can't be fixed by a
method, only matched by accident.

Every experiment answers the same questions with the same ruler (match.py) and the log questions'
leave-one-out (their own shape is never an example); only the factor under test changes. Questions run
in parallel.

Every answer is measured (qlsc/meter.py): its tokens and wall clock from the request to the final answer,
the service's share only (a consumer's reading and corrections are measured apart), against the
service's targets (defaults.yaml `service.targets`). An answer counts as delivered when it is right
within the targets. `--fresh=TAG` gives the run's LLM calls their own cache (<name>.TAG), so every call is
live and measured; without it, calls answered from the cache cost nothing and take no time.

Usage: uv run examples/fennmoor-bank/eval/explore.py probe                  # freeze the probe set, cache references
       uv run examples/fennmoor-bank/eval/explore.py run <experiment> [--workers=N] [--only=Q01,L...] [--fresh=TAG]
       uv run examples/fennmoor-bank/eval/explore.py report                 # every experiment side by side
`--set=full` answers every scored gold question and every kept log question (186) instead of the probe.
Experiments: baseline, baseline-b (a second sample, for the noise), sonnet-reasoning, opus, fable; the
agent, confirm and precedent experiments are in explore_agent.py, explore_confirm.py, explore_precedent.py.
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

import yaml
from common import RESULTS, SPEC, commit, native, settings, write_result
from log_questions import QUESTIONS, answers_dir
from match import ROWS, references, verdict

from qlsc import llm, meter, navigate
from qlsc.graph import Graph
from qlsc.warehouse import connect

HERE = Path(__file__).resolve().parent
PROBE = HERE / "explore_probe.yaml"
PROMPTS = HERE / "prompts"

# The last full run's SQL misses, by main cause (the plan's table).
CAUSE = {
    **dict.fromkeys("L4540fe70 L469ef255 L4b4d230a L62fdbc12 L788679b6 Lefe10343 L12addf1d L66b70456 "
                    "L8ee70d9a L97629e25 Lfba52c1e Led874c20 L78f9c15c L73371e91 L359c74a0 L986ea342 "
                    "L7e87d30b".split(), "ruler"),
    **dict.fromkeys("Lba494fec La5545641 L7ac9ed17 L9bedbbe0 Lf24da50d L6b9d5aa5 Ld63381a3 L6d29ff82".split(),
                    "source"),
    **dict.fromkeys("L30b11cd6 L42795751 L5e63b8a9 L6505b2e4 L0b88eeab L5bac0ee7 Ld5366f8d Lb680ccfe".split(),
                    "dimension"),
    **dict.fromkeys("Lb79256f9 Le166be49 Le8c70805 La0ef9034 Le6d5789b L8f767484 L754091da".split(), "request"),
    **dict.fromkeys("L04bfef55 L78ae7fd3 L8bc8a936 L42c41a99 L9d80def1 Lccd8d6b4".split(), "column"),
    **dict.fromkeys("La6c932d6 Ldfe49bfa".split(), "join"),
}  # fmt: skip
GROUPS = ("gold", "right", "ruler", "source", "dimension", "request", "column", "join")


def text(name: str, **values) -> str:
    return (PROMPTS / f"{name}.md").read_text().format(**values)


def out_dir(s) -> Path:
    d = s.work / "qdd" / "explore"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---- the probe set


def make_probe() -> int:
    """Freeze the probe set from the last full run, and cache the gold references' results."""
    s, wh = settings(), None
    last = json.loads((RESULTS / "log_accuracy.json").read_text())
    misses = sorted(q for q, r in last.items() if r["sql"]["verdict"] != "correct")
    right = sorted(q for q, r in last.items() if r["sql"]["verdict"] == "correct")[::4]
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    wh = connect(s)
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
    probe = {"gold": scored, "misses": {q: CAUSE[q] for q in misses}, "right": right}
    PROBE.write_text(yaml.safe_dump(probe, sort_keys=False))
    print(f"probe: {len(scored)} gold, {len(misses)} misses, {len(right)} right -> {PROBE}")
    return 0


def load_set(s) -> list[dict]:
    """The questions a run answers: the probe set, or with --set=full every scored gold question and every
    log question kept (log_answers), a miss of the last full run grouped by its cause, the rest 'right'."""
    if "--set=full" not in sys.argv:
        return load_probe(s)
    kept = sorted(
        q for q, r in json.loads((RESULTS / "log_answers.json").read_text()).items() if r["verdict"] == "kept"
    )
    probe = yaml.safe_load(PROBE.read_text())
    full = {"gold": probe["gold"], "misses": {q: CAUSE[q] for q in kept if q in CAUSE},
            "right": [q for q in kept if q not in CAUSE]}  # fmt: skip
    return load_probe(s, full)


def load_probe(s, probe: dict | None = None) -> list[dict]:
    """[{qid, group, question, shape, refs, sql (the reference's)}] in a fixed order."""
    probe = probe or yaml.safe_load(PROBE.read_text())
    gold = yaml.safe_load((SPEC / "questions.yaml").read_text())["questions"]
    logq = yaml.safe_load(QUESTIONS.read_text())
    out = []
    for qid in probe["gold"]:
        refs = json.loads((out_dir(s) / "refs" / f"{qid}.json").read_text())
        sql = (HERE / "reference" / f"{qid}.sql").read_text()
        out.append({"qid": qid, "group": "gold", "question": gold[qid]["question"], "shape": None,
                    "refs": refs, "sql": sql, "who": None})  # fmt: skip
    for qid, group in [*probe["misses"].items(), *((q, "right") for q in probe["right"])]:
        q = logq[qid]
        refs = [{"name": qid, "items": [[c] for c in q["compare"]],
                 "result": json.loads((answers_dir(s) / f"{qid}.json").read_text())}]  # fmt: skip
        out.append({"qid": qid, "group": group, "question": q["question"], "shape": q["shape"], "refs": refs,
                    "sql": q["sql"], "who": q.get("who"), "tables": q.get("tables")})  # fmt: skip
    return out


# ---- what every experiment shares


def safe_unique_checks() -> None:
    """navigate.unique_check writes its cache file on a miss; runs in parallel mustn't race on it. Read it
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
    """The shared embedding cache read once per process and never written (other runs read it: a file half
    written breaks them); a text not in it is embedded into this experiment's own cache, one at a time."""
    real_init, real_embed = llm.Embedder.__init__, llm.Embedder.embed
    lock, state = threading.Lock(), {}

    def init(self, settings_):
        with lock:
            if not state:
                real_init(self, settings_)
                own = settings_.work / "qdd" / "explore" / f"embeddings-{name}.json"
                state.update(shared=self.cache, url=self.url, key=self.key, dims=self.dims, path=own,
                             own=json.loads(own.read_text()) if own.exists() else {})  # fmt: skip
            self.url, self.key, self.dims = state["url"], state["key"], state["dims"]
            self.cache, self.cache_path = state["own"], state["path"]

    def embed(self, texts):
        import hashlib

        keys = [hashlib.sha256(f"{self.dims}|{t}".encode()).hexdigest() for t in texts]
        missing = [t for k, t in zip(keys, texts) if k not in state["shared"]]
        with lock:
            if missing:
                real_embed(self, missing)  # into the own cache, written to the own file (and measured)
            return [state["shared"].get(k) or state["own"][k] for k in keys]

    llm.Embedder.__init__, llm.Embedder.embed = init, embed


SPEND: Counter = Counter()  # model -> tokens in, out, calls: over the run
_spend_lock = threading.Lock()


def query_model(
    s,
    model: str | None = None,
    thinking: str | None = None,
    effort: str | None = None,
    cache: str | None = None,
    min_tokens: int | None = None,
    fresh: str | None = None,
    name: str = "",
) -> None:
    """Set the query model and its reasoning for this process. `effort` goes into the request's
    output_config beside the structured output's format; `cache` gives the query model's calls their own
    cache (a second sample of the same model, or a setting the cache key doesn't hold), and `fresh` a new
    one, for a run whose every call is live and measured. Counts tokens."""
    if fresh:  # the run's own: another run's calls, answered from its cache, would cost nothing here
        cache = f"{cache or name}.{fresh}"
    if model:
        s["llm"]["query_model"] = model
    if thinking:
        s["llm"]["query_thinking"] = thinking
    init = llm.LLM.__init__

    def patched(self, system, settings_, model_=None):
        init(self, system, settings_, model_)
        if self.model != settings_["llm"]["query_model"]:
            return
        if cache:
            self.cache = settings_.work / "llm_cache_explore" / cache
            self.cache.mkdir(parents=True, exist_ok=True)
        create = self.client.messages.create

        def counted(**kw):
            if effort:
                kw.setdefault("extra_body", {}).setdefault("output_config", {})["effort"] = effort
            if min_tokens:  # thinking shares max_tokens with the answer
                kw["max_tokens"] = max(kw.get("max_tokens", 0), min_tokens)
            resp = create(**kw)
            with _spend_lock:
                SPEND[(self.model, "in")] += resp.usage.input_tokens
                SPEND[(self.model, "out")] += resp.usage.output_tokens
                SPEND[(self.model, "calls")] += 1
                if resp.stop_reason == "refusal":
                    SPEND[(self.model, "refusals")] += 1
            return resp

        self.client.messages.create = counted

    llm.LLM.__init__ = patched


def trace_of(G, s, q: dict) -> dict:
    exclude = frozenset({q["shape"]}) if q["shape"] else frozenset()
    return navigate.trace(G, s, q["question"], exclude=exclude)


def baseline_answer(G, s, q: dict, tr: dict) -> dict:
    return navigate.answer_sql(G, s, tr, execute=True, rows=ROWS)


def fresh_tag() -> str | None:
    return next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--fresh=")), None)


def run(name: str, answer, workers: int = 8, only: set | None = None, model: dict | None = None,
        notes: str = "") -> dict:  # fmt: skip
    """Answer the probe set with `answer(G, s, q, tr) -> answer dict`, score and measure it, write the
    results. `model`: query_model's settings. An answer may score itself (`scored`: (verdict, why), and
    `delivered`: right within the targets) when it is an exchange, not one answer."""
    s = settings()
    fresh = fresh_tag()
    if "--set=full" in sys.argv:
        name += ".full"
    if fresh:
        name = f"{name}.{fresh}"
    safe_unique_checks()
    safe_embeddings(name)
    query_model(s, **(model or {}), fresh=fresh, name=name)
    targets = s["service"]["targets"]
    wh = connect(s)
    if (probe := wh.dry_run("SELECT 1"))["ok"] is not True:
        raise SystemExit(f"the warehouse isn't reachable: {probe.get('error')}")
    todo = [q for q in load_set(s) if not only or q["qid"] in only]
    res: dict = {}
    t0 = time.time()
    with Graph(s) as G:

        def one(q: dict) -> tuple[str, dict]:
            with meter.measure() as m:
                try:
                    # an answer that navigates for itself (a consumer's own request) gets no trace
                    tr = None if getattr(answer, "own_trace", False) else trace_of(G, s, q)
                    a = answer(G, s, q, tr)
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
                 "sql": a.get("sql"), "writer": a.get("writer"), **a.get("explore", {})}  # fmt: skip
            print(
                f"{name} {q['qid']:10} {q['group']:9} {v:10} {(a.get('writer') or '')[:8]:8} "
                f"{measured['tokens']:>7,.0f} tok {measured['seconds']:>5.1f} s  {why[:60]}",
                flush=True,
            )
            return q["qid"], r

        with ThreadPoolExecutor(workers) as pool:
            for qid, r in pool.map(one, todo):
                res[qid] = r
    run_info = {"commit": commit(), "seconds": round(time.time() - t0), "notes": notes, "targets": targets,
                "fresh": bool(fresh), "spend": {f"{m} {k}": n for (m, k), n in SPEND.items()},
                "measure": meter.summary([r["measure"] for r in res.values()], targets)}  # fmt: skip
    write_result(name, summary(name, res, run_info), res | {"_run": run_info}, out_dir(s))
    print(f"{name}: {tally(res)} in {run_info['seconds']} s; {run_info['spend']}")
    return res


def tally(res: dict) -> dict:
    by = Counter()
    for qid, r in res.items():
        if qid.startswith("_"):
            continue
        by[(r["group"], r["verdict"] == "correct")] += 1
    return {
        g: f"{by[(g, True)]}/{by[(g, True)] + by[(g, False)]}"
        for g in GROUPS
        if by[(g, True)] + by[(g, False)]
    }


def summary(name: str, res: dict, info: dict) -> list[str]:
    t, ms = tally(res), info["measure"]
    delivered = sum(r.get("delivered", False) for r in res.values())
    L = [f"# Explore: {name}", "", f"At {info['commit']}. {info['notes']}", "",
         "| " + " | ".join(t) + " |", "|" + "---|" * len(t), "| " + " | ".join(t.values()) + " |", "",
         f"Right within the targets ({targets_text(info['targets'])}): {delivered} of {ms['n']}. "
         f"Tokens: median {ms['tokens']['p50']:,.0f}, p90 {ms['tokens']['p90']:,.0f}; seconds: median "
         f"{ms['seconds']['p50']:.1f}, p90 {ms['seconds']['p90']:.1f}"
         + ("" if info.get("fresh") else " (cached calls cost nothing: not a measurement run)") + ".", "",
         f"Spend: {info['spend']}", "", "| question | group | verdict | tokens | s |", "|---|---|---|---|---|"]  # fmt: skip
    L += [f"| {q} | {r['group']} | {r['verdict']}: {r['why'][:120]} | {r['measure']['tokens']:,.0f} | "
          f"{r['measure']['seconds']:.1f} |".replace("\n", " ") for q, r in res.items() if not q.startswith("_")]  # fmt: skip
    return L


def targets_text(targets: dict) -> str:
    return ", ".join(f"{k} {v:,}" for k, v in targets.items())


def report() -> int:
    """Every experiment's tally beside the baseline's, and the questions each gained and lost."""
    s = settings()
    runs = {
        p.stem: json.loads(p.read_text()) for p in sorted(out_dir(s).glob("*.json")) if p.stem != "report"
    }
    runs = {k: v for k, v in runs.items() if isinstance(v, dict) and "_run" in v}  # not the prep files
    base = runs.get(next((k for k in runs if k.startswith("baseline.")), "baseline"))
    L = ["# Explore: every experiment", "", "Measured (tokens, seconds: median / p90; delivered: right within the "
         "targets) only for a run with its own cache (`--fresh`); otherwise cached calls cost nothing.", "",
         "| experiment | " + " | ".join(GROUPS) + " | all | gained | lost | delivered | tokens | seconds |",
         "|" + "---|" * (len(GROUPS) + 7)]  # fmt: skip
    for name, res in runs.items():
        qs = [q for q in res if not q.startswith("_")]
        by = Counter((res[q]["group"], res[q]["verdict"] == "correct") for q in qs)
        cells = [
            f"{by[(g, True)]}/{by[(g, True)] + by[(g, False)]}" if by[(g, True)] + by[(g, False)] else ""
            for g in GROUPS
        ]
        ok = sum(res[q]["verdict"] == "correct" for q in qs)
        right = lambda r, q: r[q]["verdict"] == "correct"
        gained = [q for q in qs if base and q in base and right(res, q) and not right(base, q)]
        lost = [q for q in qs if base and q in base and right(base, q) and not right(res, q)]
        ms = res["_run"].get("measure") if res["_run"].get("fresh") else None
        cost = (f" | {sum(res[q]['delivered'] for q in qs)} | {ms['tokens']['p50']:,.0f} / {ms['tokens']['p90']:,.0f} | "
                f"{ms['seconds']['p50']:.0f} / {ms['seconds']['p90']:.0f} |" if ms else " | | | |")  # fmt: skip
        L.append(
            f"| {name} | " + " | ".join(cells) + f" | {ok}/{len(qs)} | {len(gained)} | {len(lost)}" + cost
        )
    L += [""]
    for name, res in runs.items():
        if name == "baseline" or not base:
            continue
        qs = [q for q in res if not q.startswith("_") and q in base]
        g = [q for q in qs if res[q]["verdict"] == "correct" and base[q]["verdict"] != "correct"]
        lo = [q for q in qs if base[q]["verdict"] == "correct" and res[q]["verdict"] != "correct"]
        named = lambda xs, res=res: ", ".join(f"{q} ({res[q]['group']})" for q in xs) or "none"
        L += [f"- **{name}:** gained {named(g)}; lost {named(lo)}"]
    path = write_result("report", L, {k: {"_run": v.get("_run")} for k, v in runs.items()}, out_dir(s))
    print("\n".join(L))
    print(f"-> {path}")
    return 0


# ---- the model experiments

MODELS = {
    "baseline": dict(notes="The configuration as it is: Sonnet 5.5, thinking between tools (off before the answer)."),
    "baseline-b": dict(cache="baseline-b", notes="The baseline again, a second sample (its own cache): the noise."),
    "sonnet-reasoning": dict(thinking="adaptive", effort="high", cache="sonnet-reasoning", min_tokens=16000,
                             notes="Sonnet 5.5 with adaptive thinking at high effort: reasoning without a model change."),
    "opus": dict(model="claude-opus-5-5", thinking="adaptive", effort="high", cache="opus", min_tokens=16000,
                 notes="Opus 5.5, adaptive thinking at high effort (its default is medium)."),
    "fable": dict(model="claude-fable-5-1", thinking="adaptive", effort="high", cache="fable", min_tokens=16000,
                  notes="Fable 5.1, thinking always on, high effort. No refusal fallback: a refusal is a failure."),
}  # fmt: skip


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    if not args or args[0] == "report":
        return report()
    if args[0] == "probe":
        return make_probe()
    name = args[1]
    only = set(opt["only"].split(",")) if "only" in opt else None
    cfg = dict(MODELS[name])
    notes = cfg.pop("notes")
    run(
        name,
        baseline_answer,
        int(opt.get("workers", 8)),
        only,
        model=cfg,
        notes=notes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
