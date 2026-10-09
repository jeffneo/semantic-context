"""A key is read when a call is made that is not cached, not before: a process with no keys (a hosted demo whose questions are all cached) answers from the cache and
is never the one that spends. A miss says which key is missing."""

from __future__ import annotations

import hashlib
import json

import pytest

from qlsc import config, llm


@pytest.fixture
def keyless(tmp_path, monkeypatch):
    for name in (
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)  # no .env above here to fall back on
    monkeypatch.setattr(config, "_dotenv", lambda start: {})
    f = tmp_path / "estate.yaml"
    f.write_text("business: {name: a bank, kind: bank}\n")
    return config.load(f)


def test_a_cached_embedding_needs_no_key(keyless):
    emb = llm.Embedder(keyless)
    key = hashlib.sha256(f"{emb.dims}|hello".encode()).hexdigest()
    emb.cache[key] = [0.5, 0.25]
    assert emb.embed(["hello"]) == [[0.5, 0.25]]
    with pytest.raises(config.ConfigError, match="AZURE_OPENAI_ENDPOINT"):
        emb.embed(["not cached"])


def test_a_cached_model_call_needs_no_key(keyless):
    model = llm.LLM("system", keyless)
    schema = {"type": "object"}
    key = hashlib.sha256(json.dumps([model.model, "system", "question", schema]).encode()).hexdigest()
    (model.cache / f"{key}.json").write_text(json.dumps({"answer": 1}))
    assert model.call("question", schema) == {"answer": 1}
    with pytest.raises(config.ConfigError, match="ANTHROPIC_API_KEY"):
        model.call("another question", schema)


@pytest.fixture
def azure(keyless, monkeypatch):
    """A request to Azure is caught: what URL would have been called."""
    import urllib.request

    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    asked = []

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps({"data": [{"index": 0, "embedding": [0.5]}]}).encode()

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda req, timeout=0: asked.append(req.full_url) or Reply()
    )
    return keyless, asked


@pytest.mark.parametrize("endpoint", ["https://r.openai.azure.com", "https://r.openai.azure.com/"])
def test_the_azure_endpoint_is_the_resources_address(azure, monkeypatch, endpoint):
    s, asked = azure
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", endpoint)
    emb = llm.Embedder(s)
    emb.embed(["a new text"])
    assert asked == [
        f"https://r.openai.azure.com/openai/deployments/{emb.deployment}/embeddings?api-version=2025-01-01-preview"
    ]


def test_the_portals_v1_url_is_refused_by_name_not_as_a_404(azure, monkeypatch):
    s, asked = azure
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://r.openai.azure.com/openai/v1")
    with pytest.raises(config.ConfigError, match="resource's address"):
        llm.Embedder(s).embed(["a new text"])
    assert asked == []  # nothing was sent
