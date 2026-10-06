"""The process corpus: unstructured event objects for the Fennmoor estate (plans/2026-10-05-process-corpus.md).

Phases 1 to 3 are built: the world (`spec/corpus/*.yaml`, the answer key) and its validator; the row pool, the sampler and the
matcher; the realiser, its checks and its gates. Phase 4 is the full run: 2,000 realised
(`build/corpus/full/`) and 20,000 stubbed (`build/corpus/scale/`, from `--plans`).

    uv run examples/fennmoor-bank/generate/corpus.py --validate-world [--strict]
    uv run examples/fennmoor-bank/generate/corpus.py --pool        # read the warehouse once (about a quarter of a GB scanned)
    uv run examples/fennmoor-bank/generate/corpus.py --dry-run     # plans against the world's targets: free, no warehouse
    uv run examples/fennmoor-bank/generate/corpus.py --plan        # plans matched to warehouse rows -> build/corpus/plans.ndjson
    uv run examples/fennmoor-bank/generate/corpus.py --realise --limit 25 [--model sonnet] [--stub]   # phase 3: the text
    uv run examples/fennmoor-bank/generate/corpus.py --realise --model sonnet --out build/corpus/full    # phase 4: the corpus
    uv run examples/fennmoor-bank/generate/corpus.py --audit [--out build/corpus/full]   # phase 5: the written corpus read back
    uv run examples/fennmoor-bank/generate/corpus.py --push [--dry-run] | --pull [--bucket gs://...]   # the bucket backup
    uv run examples/fennmoor-bank/generate/corpus.py --plan --n 20000 --plans build/corpus/scale/plans.ndjson.gz   # then --realise --stub --plans ...
"""

from __future__ import annotations

import argparse
import sys

from corpus_world import validate


def validate_world(strict: bool = False) -> int:
    report, counts = validate()
    print("world model")
    for key, value in counts.items():
        print(f"  {value:>4}  {key}")
    for note in report.notes:
        print(f"\nnote:    {note}")
    for warning in report.warnings:
        print(f"warning: {warning}")
    for error in report.errors:
        print(f"ERROR:   {error}")
    print(f"\n{len(report.errors)} errors, {len(report.warnings)} warnings, {len(report.notes)} notes")
    return 1 if report.errors or (strict and report.warnings) else 0


def pool() -> int:
    import corpus_pool

    info = corpus_pool.extract(corpus_pool.settings())
    print(f"wrote {corpus_pool.POOL} ({info['rows']:,} rows, {info['bytes_billed'] / 1e9:.2f} GB billed)")
    print(corpus_pool.describe(corpus_pool.load_pool()))
    return 0


def dry_run(n: int, seed: int) -> int:
    from corpus_plan import Sampler
    from corpus_report import report
    from corpus_world import load_world

    w = load_world()
    sampler = Sampler(w)
    print(report(w, [sampler.plan(seed, i) for i in range(n)]))
    return 0


def plan(n: int, seed: int, plans_file: str | None) -> int:
    import gzip
    import json
    from pathlib import Path

    import corpus_pool
    from corpus_plan import generate
    from corpus_report import against_the_warehouse, report, verify
    from corpus_world import load_world

    w = load_world()
    pool = corpus_pool.load_pool()
    plans, stats = generate(w, pool, seed, n)
    out = Path(plans_file) if plans_file else corpus_pool.POOL.parent / "plans.ndjson.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt") as handle:
        for p in plans:
            handle.write(json.dumps(p, sort_keys=True, default=str) + "\n")
    print(report(w, plans))
    print("\n" + against_the_warehouse(plans, pool))
    bad = verify(w, plans, pool)
    print(f"\nmatching: {stats}")
    print(f"consistency with the rows: {len(bad)} violations" + ("".join(f"\n  {b}" for b in bad[:20])))
    print(f"wrote {out}")
    return 0


def realise(
    limit: int | None, model: str | None, stub: bool, out: str | None, seed: int, plans_file: str | None
) -> int:
    import gzip
    import json
    from pathlib import Path

    import corpus_check
    import corpus_pool
    import corpus_text
    from corpus_world import load_world

    w = load_world()
    source = Path(plans_file) if plans_file else corpus_pool.POOL.parent / "plans.ndjson.gz"
    if not source.is_file():
        raise SystemExit(f"{source} does not exist: run corpus.py --plan first")
    with gzip.open(source, "rt") as handle:
        plans = [json.loads(line) for line in handle]
    plans = plans[:limit] if limit else plans
    settings = corpus_pool.settings()
    if model in ("haiku", None):
        model = None
    elif model == "sonnet":
        model = settings["llm"]["query_model"]
    out_dir = Path(out) if out else corpus_pool.POOL.parent / ("sample" if limit else "")
    summary = corpus_text.realise(w, settings, plans, seed, model, stub, out_dir)
    results = summary.pop("results")
    (out_dir / "sample.txt").write_text(corpus_text.render(w, results))
    print(corpus_check.gates(results))
    print(
        f"\n{summary['llm'] or 'stub: no model'}; {summary['calls']} calls, {summary['cached']} cached, {summary['events']} events"
    )
    print(f"wrote {out_dir}/ (events.ndjson.gz, truth.ndjson.gz, manifest.json, sample.txt)")
    return 0 if summary["written"] else 1


def audit(directory: str | None, plans_file: str | None) -> int:
    from pathlib import Path

    import corpus_audit
    import corpus_pool
    from corpus_world import load_world

    base = corpus_pool.POOL.parent
    folder = Path(directory) if directory else base / "full"
    plans = Path(plans_file) if plans_file else base / "plans.ndjson.gz"
    text, failed = corpus_audit.audit(load_world(), folder, plans, corpus_pool.load_pool())
    (folder / "audit.txt").write_text(text + "\n")
    print(text)
    print(f"\n{failed} failed; wrote {folder}/audit.txt")
    return 1 if failed else 0


def store(bucket: str, pull: bool, dry: bool) -> int:
    import corpus_store

    done = corpus_store.pull(bucket) if pull else corpus_store.push(bucket, dry)
    verb = "fetched" if pull else ("would copy" if dry else "copied")
    print(f"{verb} {len(done)} files {'from' if pull else 'to'} {bucket}")
    print("\n".join(f"  {d}" for d in done))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--validate-world", action="store_true", help="check spec/corpus/*.yaml and exit")
    parser.add_argument(
        "--strict", action="store_true", help="with --validate-world, warnings are errors too"
    )
    parser.add_argument(
        "--pool", action="store_true", help="read the warehouse once and keep the row pool locally"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="sample plans and report them against the world's targets"
    )
    parser.add_argument(
        "--plan", action="store_true", help="sample plans and match each to a warehouse row (needs the pool)"
    )
    parser.add_argument(
        "--realise", action="store_true", help="phase 3: write the text for the planned conversations"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="with --realise, only the first N plans (a trial)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="with --realise: haiku (llm.model, default), sonnet (llm.query_model) or a model id",
    )
    parser.add_argument(
        "--stub", action="store_true", help="with --realise, free placeholder text instead of a model"
    )
    parser.add_argument("--out", default=None, help="with --realise, the folder to write")
    parser.add_argument(
        "--push", action="store_true", help="back the corpus up to the bucket (with --dry-run: list it)"
    )
    parser.add_argument("--pull", action="store_true", help="fetch the corpus back from the bucket")
    parser.add_argument("--bucket", default="gs://fennmoor-corpus", help="with --push or --pull")
    parser.add_argument(
        "--audit", action="store_true", help="read a written corpus (--out) back and check it: no spend"
    )
    parser.add_argument(
        "--plans",
        default=None,
        help="the plans file: written by --plan, read by --realise (default build/corpus/plans.ndjson.gz)",
    )
    parser.add_argument("--n", type=int, default=2000, help="conversations to plan (default 2,000)")
    parser.add_argument("--seed", type=int, default=7, help="the seed: the same seed gives the same plans")
    args = parser.parse_args()
    if args.push or args.pull:
        return store(args.bucket, args.pull, args.dry_run)
    if args.audit:
        return audit(args.out, args.plans)
    if args.realise:
        return realise(args.limit, args.model, args.stub, args.out, args.seed, args.plans)
    if args.dry_run:
        return dry_run(args.n, args.seed)
    if args.plan:
        return plan(args.n, args.seed, args.plans)
    if args.validate_world:
        return validate_world(strict=args.strict)
    if args.pool:
        return pool()
    parser.error("choose --validate-world, --pool, --dry-run, --plan, --realise, --audit, --push or --pull")
    return 2


if __name__ == "__main__":
    sys.exit(main())
