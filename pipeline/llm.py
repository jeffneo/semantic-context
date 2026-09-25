"""Prompts and LLM calls shared by the pipeline stages.

Every prompt the pipeline sends lives in prompts/ at the repository root, one file per
prompt, with {placeholders} filled by prompt(name, **values). Code never holds prompt text.

LLM: Anthropic (estate.yaml `llm.model`), one forced tool per call so the answer is
structured, cached by the full request under work/llm_cache/ - a rebuild over unchanged
evidence is free.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from graphdb import config, env

HERE = Path(__file__).resolve().parent
PROMPTS = HERE.parent / "prompts"
CACHE = HERE / "work" / "llm_cache"
WORK = HERE / "work"


def prompt(name: str, **values) -> str:
    text = (PROMPTS / f"{name}.md").read_text()
    return text.format(**values) if values else text


class LLM:
    def __init__(self, system: str, cfg: dict | None = None, model: str | None = None):
        import anthropic
        self.anthropic = anthropic
        self.cfg = cfg or config()
        self.model = model or self.cfg["llm"]["model"]
        self.system = system
        self.client = anthropic.Anthropic(api_key=env()["ANTHROPIC_API_KEY"])
        CACHE.mkdir(parents=True, exist_ok=True)
        self.calls = self.cached = 0
        self.tokens = Counter()

    def call(self, user: str, schema: dict, tool: str, max_tokens: int = 8000) -> dict:
        key = hashlib.sha256(json.dumps([self.model, self.system, user, schema]).encode()).hexdigest()
        path = CACHE / f"{key}.json"
        if path.exists():
            self.cached += 1
            return json.loads(path.read_text())
        a = self.anthropic
        for attempt in range(5):
            try:
                resp = self.client.messages.create(
                    model=self.model, max_tokens=max_tokens, system=self.system,
                    tools=[{"name": tool, "description": "Record the results.", "input_schema": schema}],
                    tool_choice={"type": "tool", "name": tool},
                    messages=[{"role": "user", "content": user}])
                break
            except (a.RateLimitError, a.APIConnectionError, a.InternalServerError):
                time.sleep(2 ** attempt * 3)
        else:
            raise RuntimeError("LLM unavailable")
        self.calls += 1
        self.tokens["in"] += resp.usage.input_tokens
        self.tokens["out"] += resp.usage.output_tokens
        out = next(b.input for b in resp.content if b.type == "tool_use")
        for k, v in list(out.items()):          # a nested array sometimes arrives as a JSON string
            if isinstance(v, str) and v.lstrip().startswith(("[", "{")):
                try:
                    out[k] = json.JSONDecoder().raw_decode(v.strip())[0]
                except ValueError:
                    pass
        path.write_text(json.dumps(out))
        return out

    def cost(self) -> float:
        """Haiku 4.5 list price: $1 / $5 per million input / output tokens."""
        return self.tokens["in"] / 1e6 + self.tokens["out"] * 5 / 1e6


BOILERPLATE = __import__("re").compile(
    r"(?i)\b(okay|sure|certainly|as an ai|i understand|here (is|are)|let me)\b")
NAME_SCHEMA = {"type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {
    "type": "object", "required": ["id", "name", "description"], "properties": {
        "id": {"type": "string"}, "name": {"type": "string"}, "description": {"type": "string"}}}}}}


def check_name(item: dict | None, words=(1, 6), chars=(15, 500)) -> str | None:
    """A name of a few words and a sentence or two of description; nothing conversational."""
    if not item:
        return "missing from the answer"
    name, desc = (item.get("name") or "").strip(), (item.get("description") or "").strip()
    if not words[0] <= len(name.split()) <= words[1]:
        return f"name must be {words[0]} to {words[1]} words, got {name!r}"
    if not chars[0] <= len(desc) <= chars[1]:
        return f"description must be {chars[0]} to {chars[1]} characters"
    if BOILERPLATE.search(name + " " + desc):
        return "no conversational text; state the name and description only"
    return None


def name_all(llm: LLM, evidence: dict[str, str], kind: str, batch: int, workers: int,
             schema: dict = NAME_SCHEMA, check=check_name) -> dict[str, dict]:
    """Name objects in batches (prompts/<kind>_batch.md), validate, retry failures one by one
    (prompts/<kind>_retry.md); a second failure is recorded as failed, never dropped."""
    from concurrent.futures import ThreadPoolExecutor
    ids = sorted(evidence)
    batches = [ids[i:i + batch] for i in range(0, len(ids), batch)]
    tool = f"record_{kind}s"

    def run(b):
        out = llm.call(prompt(f"{kind}_batch", n=len(b), evidence="\n\n".join(evidence[x] for x in b)), schema, tool)
        return {i.get("id"): i for i in out.get("items", []) if isinstance(i, dict)}

    def redo(pair):
        x, err = pair
        out = llm.call(prompt(f"{kind}_retry", error=err, evidence=evidence[x]), schema, tool)
        item = next((i for i in out.get("items", []) if isinstance(i, dict)), None)
        e2 = check(item)
        return x, ({**item, "id": x, "status": "retried"} if not e2 else {"id": x, "status": "failed", "error": e2})
    got, final, retry = {}, {}, []
    with ThreadPoolExecutor(workers) as pool:
        for r in pool.map(run, batches):
            got.update(r)
        for x in ids:
            err = check(got.get(x))
            (retry.append((x, err)) if err else final.__setitem__(x, {**got[x], "status": "ok"}))
        for x, item in pool.map(redo, retry):
            final[x] = item
    return final


# ----------------------------------------------------------------- embeddings
# Azure OpenAI (estate.yaml `embeddings`), cached by text in work/emb_cache.json.
class Embedder:
    def __init__(self, cfg):
        e = env()
        self.url = (f"{e['AZURE_OPENAI_ENDPOINT'].rstrip('/')}/openai/deployments/{cfg['embeddings']['deployment']}"
                    f"/embeddings?api-version={e['AZURE_OPENAI_API_VERSION']}")
        self.key, self.dims = e["AZURE_OPENAI_API_KEY"], cfg["embeddings"]["dimensions"]
        self.cache_path = WORK / "emb_cache.json"
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}

    def embed(self, texts: list[str]) -> list[list[float]]:
        keys = [hashlib.sha256(f"{self.dims}|{t}".encode()).hexdigest() for t in texts]
        todo = [(k, t) for k, t in zip(keys, texts) if k not in self.cache]
        for i in range(0, len(todo), 64):
            chunk = todo[i:i + 64]
            body = json.dumps({"input": [t for _, t in chunk], "dimensions": self.dims}).encode()
            for attempt in range(5):
                try:
                    req = urllib.request.Request(self.url, data=body, headers={"api-key": self.key,
                                                                               "Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=120) as r:
                        data = json.loads(r.read())["data"]
                    break
                except urllib.error.HTTPError as e:
                    if e.code != 429 or attempt == 4:
                        raise
                    time.sleep(2 ** attempt * 2)
            for (k, _), d in zip(chunk, sorted(data, key=lambda d: d["index"])):
                self.cache[k] = d["embedding"]
        self.cache_path.write_text(json.dumps(self.cache))
        return [self.cache[k] for k in keys]
