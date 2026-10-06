"""The corpus's bucket helpers (examples/fennmoor-bank/generate/corpus_store.py): what is backed up and where, the cache as a
reproducible tarball, and reading a path or a URI. No network and no gcloud."""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

GENERATE = Path(__file__).resolve().parents[1] / "examples" / "fennmoor-bank" / "generate"
sys.path.insert(0, str(GENERATE))

import corpus_store  # noqa: E402


def test_the_answer_key_is_under_its_own_prefix():
    names = [n for _, n in corpus_store.layout()]
    keys = [n for n in names if "truth" in n or "plans" in n]
    assert keys and all("/answer-key/" in n for n in keys)
    assert not any("/answer-key/" in n for n in names if "events" in n or "manifest" in n)


def test_a_gs_uri_is_read_as_its_public_url():
    assert (
        corpus_store.https("gs://b/full/events.ndjson.gz")
        == "https://storage.googleapis.com/b/full/events.ndjson.gz"
    )
    assert corpus_store.https("/tmp/x") == "/tmp/x"


def test_a_path_is_read_and_decompressed(tmp_path):
    path = tmp_path / "e.ndjson.gz"
    with gzip.open(path, "wt") as out:
        out.write('{"a": 1}\n{"a": 2}\n')
    assert [json.loads(line)["a"] for line in corpus_store.open_text(str(path))] == [1, 2]


def test_the_cache_packs_only_the_realisers_answers_and_the_same_cache_is_the_same_file(
    tmp_path, monkeypatch
):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "a.json").write_text(json.dumps({"turns": [{"slot": 1, "text": "hi"}]}))
    (cache / "b.json").write_text(json.dumps({"sql": "select 1"}))  # another prompt's answer
    monkeypatch.setattr(corpus_store, "cache_dir", lambda: cache)
    one, two = tmp_path / "1.tar.gz", tmp_path / "2.tar.gz"
    assert corpus_store.pack_cache(one) == 1
    corpus_store.pack_cache(two)
    assert one.read_bytes() == two.read_bytes()
    for f in cache.glob("*.json"):
        f.unlink()
    assert corpus_store.unpack_cache(one.read_bytes()) == 1
    assert [f.name for f in cache.glob("*.json")] == ["a.json"]
