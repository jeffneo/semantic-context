"""Write the slice of work/ a hosted demo needs -> build/hosted-work/, and say which of the page's questions it can answer.

A hosted demo (plans/2026-10-08-cloud-deploy.md) runs only the page's own presets (ui/dist/presets.json). work/ is 800 MB, most of it the pipeline's; the
questions need the files they read: the catalog, the virtual model, the allowlists, the cached model calls and the cached embeddings they hit. This runs each
`ask` preset in-process, as every principal, with the model and embedding keys set to nothing valid: a cache hit answers, a miss fails and costs nothing. What
the run opened is what the slice holds (the embedding cache cut to the keys it was asked for), and `report.json` says, per question, route and principal, whether
it was answered. It also runs the page's `exchange` presets (demo.py: an agent asks, asks again and corrects), which are conversations and so are *recorded in memory*,
as the panel does whenever anyone runs it; `recall` reads the same files and is not run (it would remember a customer).
The Virtual Graph's signing key (virtual/passthrough.key) is never copied: a deployment gets it from its secret store.
Usage: uv run examples/fennmoor-bank/generate/hosted_work.py [--warm]   (Neo4j, Virtual Graph and the BigQuery login up; `npm run build` in ui/ first)
  --warm   keeps the real keys, so a miss is answered by the model and cached (the questions are cached per principal: this is the only way a public page answers
           them all). It spends: each question about 3 cents, once; run it again and nothing is spent.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
from pathlib import Path

from qlsc import cli, config, llm

EXAMPLE = Path(__file__).resolve().parents[1]
ROOT = EXAMPLE.parents[1]
OUT = EXAMPLE / "build" / "hosted-work"
NEVER = {
    "passthrough.key",
    "credentials.json",
    "neo4j.keystore",
    "secret.json",
}  # secrets: a deployment is given its own

WARM = "--warm" in sys.argv
if not WARM:
    for name in ("ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY"):
        os.environ[name] = "not-a-key"  # a miss must fail, not spend

os.environ["QLSC_CONFIG"] = str(EXAMPLE / "estate.yaml")
s = config.load(EXAMPLE / "estate.yaml")
work = s.work.resolve()
presets = json.loads((ROOT / "ui" / "dist" / "presets.json").read_text())
principals = ["admin", *s["entitlements"]["principals"]]

opened: set[Path] = set()
asked_keys: set[str] = set()


def watch(event: str, args: tuple) -> None:
    if event == "open" and isinstance(args[0], str):
        p = Path(args[0])
        if p.is_absolute() and work in p.parents:
            opened.add(p)  # a file a miss is about to write is not there yet: it is checked when copied


sys.addaudithook(watch)

_embed = llm.Embedder.embed


def embed(self, texts):
    asked_keys.update(hashlib.sha256(f"{self.dims}|{t}".encode()).hexdigest() for t in texts)
    return _embed(self, texts)


llm.Embedder.embed = embed

ROUTES = {"auto": [], "sql": ["--sql"], "cypher": ["--cypher"], "memory": ["--memory"]}
report = []
for who in principals:
    for p in presets["ask"]:
        argv = [
            "ask",
            *ROUTES[p["route"]],
            "--run",
            *([] if who == "admin" else ["--as", who]),
            p["question"],
        ]
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cli.main(argv)
            ok, why = code in (0, None), ""
        except BaseException as e:  # a miss raises where the model or embedding is called: SystemExit too
            ok, why = False, f"{type(e).__name__}: {str(e)[:120]}"
        report.append(
            {"question": p["question"], "route": p["route"], "principal": who, "answered": ok, "why": why}
        )
        print(f"{'ok  ' if ok else 'MISS'} {who:15} {p['route']:7} {p['question'][:70]}  {why}", flush=True)

# the exchanges: demo.py's, as the panel runs them (a model call to correct, and the questions' embeddings)
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("demo", EXAMPLE / "demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
for n in presets["exchange"]:
    sys.argv = ["demo.py", "exchange", n]
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            demo.exchange()
        ok, why = True, ""
    except BaseException as e:
        ok, why = False, f"{type(e).__name__}: {str(e)[:120]}"
    report.append(
        {"question": f"exchange {n}", "route": "exchange", "principal": "admin", "answered": ok, "why": why}
    )
    print(f"{'ok  ' if ok else 'MISS'} {'admin':15} exchange {n}  {why}", flush=True)

shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir(parents=True)
kept = 0
for path in sorted(opened):
    rel = path.relative_to(work)
    if not path.is_file() or path.name in NEVER or rel.name == "emb_cache.json":
        continue
    (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, OUT / rel)
    kept += 1
emb = json.loads((work / "emb_cache.json").read_text())
(OUT / "emb_cache.json").write_text(json.dumps({k: v for k, v in emb.items() if k in asked_keys}))
(OUT / "report.json").write_text(json.dumps(report, indent=1))

size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
answered = sum(r["answered"] for r in report)
print(
    f"\n{answered} of {len(report)} (question, route, principal) answered from cache; {kept} files and {len(asked_keys)} embeddings -> {OUT} ({size / 1e6:.1f} MB)"
)
