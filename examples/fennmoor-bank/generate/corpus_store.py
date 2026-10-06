"""Keeping the corpus in a bucket, and reading it from there: `corpus.py --push` and `--pull`.

`build/` is gitignored, and the corpus costs about $20 of Sonnet calls to write, so it is backed up in the project's bucket. Layout:

    <bucket>/full/        events.ndjson.gz  manifest.json  audit.txt  sample.txt         the demo corpus (2,000 realised, plus callbacks)
    <bucket>/scale/       events.ndjson.gz  manifest.json                                the scale set (placeholder text)
    <bucket>/<set>/answer-key/   truth.ndjson.gz  plans.ndjson.gz                       what a scorer reads and a builder never does
    <bucket>/inputs/      pool.ndjson.gz  realiser-cache.tar.gz                          what regenerates it: the warehouse extract, and
                                                                                         the model's answers (the cache keeps a rerun free
                                                                                         and byte-identical; without it, about $20 again)

The answer key sits under its own prefix so it can be restricted without touching the corpus. Writing and reading use `gcloud storage`
as the estate's named gcloud configuration, which is the service account it impersonates, like every other access to the project;
if that account lacks a permission the call fails, and nothing falls back to another identity. Reading a public bucket needs no
credentials: `open_text` takes a path, a `gs://` URI or an https URL, which is what the text knowledge-graph builder reads its
events by.

Plan: plans/2026-10-05-text-graph-construction.md.
"""

from __future__ import annotations

import gzip
import io
import json
import os
import shutil
import subprocess
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

import corpus_pool

BUCKET = "gs://fennmoor-corpus"
BASE = corpus_pool.POOL.parent  # build/corpus
CACHE_TAR = "realiser-cache.tar.gz"
# A realiser answer is {"turns": [...]}: the cache also holds every other prompt's answers, which are not this corpus's.
REALISER_KEY = "turns"
SETS = {
    "full": ("events.ndjson.gz", "manifest.json", "audit.txt", "sample.txt"),
    "scale": ("events.ndjson.gz", "manifest.json"),
}
KEY = ("truth.ndjson.gz", "plans.ndjson.gz")


def cache_dir() -> Path:
    return corpus_pool.settings().work / "llm_cache"


def plans_of(name: str) -> Path:
    """The plans each set was written from: the demo corpus's are beside the pool, the scale set's beside it."""
    return BASE / "plans.ndjson.gz" if name == "full" else BASE / name / "plans.ndjson.gz"


def layout() -> list[tuple[Path, str]]:
    """(local file, name in the bucket), for everything that is backed up, whether or not it exists here."""
    out: list[tuple[Path, str]] = []
    for name, files in SETS.items():
        out += [(BASE / name / f, f"{name}/{f}") for f in files]
        out.append((BASE / name / "truth.ndjson.gz", f"{name}/answer-key/truth.ndjson.gz"))
        out.append((plans_of(name), f"{name}/answer-key/plans.ndjson.gz"))
    out += [(corpus_pool.POOL, "inputs/pool.ndjson.gz"), (BASE / CACHE_TAR, f"inputs/{CACHE_TAR}")]
    return out


def pack_cache(path: Path) -> int:
    """The realiser's answers as a tarball, in sorted order with fixed times, so the same cache is the same file."""
    names = []
    for f in sorted(cache_dir().glob("*.json")):
        try:
            if REALISER_KEY in json.loads(f.read_text()):
                names.append(f)
        except (json.JSONDecodeError, TypeError):
            continue
    # The gzip header carries a time of its own: fixed, or the same cache would not be the same file.
    with (
        open(path, "wb") as raw,
        gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped,
        tarfile.open(fileobj=zipped, mode="w") as tar,
    ):
        for f in names:
            info = tar.gettarinfo(f, arcname=f.name)
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
            with open(f, "rb") as handle:
                tar.addfile(info, handle)
    return len(names)


def unpack_cache(data: bytes) -> int:
    CACHE = cache_dir()
    CACHE.mkdir(parents=True, exist_ok=True)
    n = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar:
            if member.isfile() and "/" not in member.name and member.name.endswith(".json"):
                (CACHE / member.name).write_bytes(tar.extractfile(member).read())
                n += 1
    return n


def https(location: str) -> str:
    """A gs:// URI as its public https URL; anything else as it is."""
    if location.startswith("gs://"):
        return "https://storage.googleapis.com/" + location.removeprefix("gs://")
    return location


def read_bytes(location: str) -> bytes:
    """A local path, a gs:// URI or an https URL. A bucket that is not public refuses the plain read, and a gs:// URI then falls
    back to `gcloud storage cat` as the configuration's service account, which fails if it may not read."""
    if not location.startswith(("gs://", "http://", "https://")):
        return Path(location).read_bytes()
    try:
        with urllib.request.urlopen(https(location), timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        if not location.startswith("gs://") or e.code not in (401, 403):
            raise
    return gcloud("cat", location, capture=True)


def open_text(location: str):
    """Lines of text from a path or URI, decompressed if it ends .gz: what a reader of the events file is given."""
    data = read_bytes(location)
    if location.endswith(".gz"):
        data = gzip.decompress(data)
    return io.StringIO(data.decode("utf-8"))


def gcloud(*args: str, capture: bool = False) -> bytes:
    config = corpus_pool.settings()["warehouse"]["gcloud_config"]
    env = {**os.environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": config}
    if not shutil.which("gcloud"):
        raise SystemExit("gcloud is not on the PATH")
    done = subprocess.run(["gcloud", "storage", *args], env=env, check=True, capture_output=capture)
    return done.stdout


def push(bucket: str, dry: bool = False) -> list[str]:
    """Copy everything in the layout, and the realiser's cache, to the bucket. Returns what was (or would be) written."""
    items = [(p, n) for p, n in layout() if p.is_file() and not n.endswith(CACHE_TAR)]
    done = []
    tar = BASE / CACHE_TAR
    n = pack_cache(tar)
    items.append((tar, f"inputs/{CACHE_TAR}"))
    for path, name in items:
        done.append(
            f"{name}  ({path.stat().st_size / 1e6:.1f} MB)" + (f"  [{n} answers]" if path == tar else "")
        )
        if not dry:
            gcloud("cp", "--quiet", str(path), f"{bucket}/{name}")
    return done


def pull(bucket: str, names: list[str] | None = None) -> list[str]:
    """Fetch the layout back into build/corpus (and the cache into the work folder) from a public bucket."""
    done = []
    for path, name in layout():
        if names and not any(name.startswith(n) for n in names):
            continue
        data = read_bytes(f"{bucket}/{name}")
        if name == f"inputs/{CACHE_TAR}":
            done.append(f"{name}: {unpack_cache(data)} answers into {cache_dir()}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        done.append(f"{name}  ({len(data) / 1e6:.1f} MB)")
    return done
