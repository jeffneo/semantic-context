"""Prompts, LLM calls and embeddings, shared by the stages.

Every prompt lives in prompts/ at the repository root, one file each, with {placeholders} filled by
prompt(name, **values). Code never holds prompt text.

LLM: Anthropic (config `llm.model`), one forced tool per call so the answer is structured, cached by
the full request in <work>/llm_cache/. Embeddings: Azure OpenAI (config `embeddings`), cached by text
in <work>/emb_cache.json. A rebuild over unchanged evidence calls neither.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import anthropic

from qlsc.config import PROMPTS, Settings, secret
from qlsc.graph import Graph


def prompt(name: str, **values) -> str:
    return (PROMPTS / f"{name}.md").read_text().format(**values)


class LLM:
    def __init__(self, system: str, settings: Settings):
        self.model = settings["llm"]["model"]
        self.workers = settings["llm"]["concurrency"]
        self.system = system
        self.client = anthropic.Anthropic(api_key=secret("ANTHROPIC_API_KEY"))
        self.cache = settings.work / "llm_cache"
        self.cache.mkdir(exist_ok=True)
        self.calls = self.cached = 0
        self.tokens = Counter()

    def call(self, user: str, schema: dict, tool: str, max_tokens: int = 8000) -> dict:
        key = hashlib.sha256(json.dumps([self.model, self.system, user, schema]).encode()).hexdigest()
        path = self.cache / f"{key}.json"
        if path.exists():
            self.cached += 1
            return json.loads(path.read_text())
        for attempt in range(5):
            try:
                resp = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=self.system,
                    tools=[{"name": tool, "description": "Record the results.", "input_schema": schema}],
                    tool_choice={"type": "tool", "name": tool},
                    messages=[{"role": "user", "content": user}],
                )
                break
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError):
                time.sleep(2**attempt * 3)
        else:
            raise RuntimeError("LLM unavailable")
        self.calls += 1
        self.tokens["in"] += resp.usage.input_tokens
        self.tokens["out"] += resp.usage.output_tokens
        out = next(b.input for b in resp.content if b.type == "tool_use")
        for k, v in list(out.items()):  # a nested array sometimes arrives as a JSON string
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

    def summary(self) -> str:
        return f"LLM {self.model}: {self.calls} calls, {self.cached} cached, ${self.cost():.2f}"


# ------------------------------------------------------------------ naming

BOILERPLATE = re.compile(r"(?i)\b(okay|sure|certainly|as an ai|i understand|here (is|are)|let me)\b")
NAME_SCHEMA = {
    "type": "object",
    "required": ["items"],
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "description"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        }
    },
}


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


def name_all(
    llm: LLM,
    evidence: dict[str, str],
    thing: tuple[str, str],
    batch: int,
    schema: dict = NAME_SCHEMA,
    check=check_name,
) -> dict[str, dict]:
    """Name objects in batches (prompts/name_batch.md), validate, retry failures one by one
    (prompts/name_retry.md); a second failure is recorded as failed, never dropped.
    `thing` is the object's name, singular and plural: ("variable", "variables")."""
    one, many = thing
    ids = sorted(evidence)
    tool = f"record_{one.split()[-1]}s"

    def first(b):
        text = prompt("name_batch", n=len(b), things=many, evidence="\n\n".join(evidence[x] for x in b))
        out = llm.call(text, schema, tool)
        return {i.get("id"): i for i in out.get("items", []) if isinstance(i, dict)}

    def again(pair):
        x, error = pair
        out = llm.call(prompt("name_retry", thing=one, error=error, evidence=evidence[x]), schema, tool)
        item = next((i for i in out.get("items", []) if isinstance(i, dict)), None)
        error = check(item)
        return x, (
            {**item, "id": x, "status": "retried"}
            if not error
            else {"id": x, "status": "failed", "error": error}
        )

    got, final, retry = {}, {}, []
    with ThreadPoolExecutor(llm.workers) as pool:
        for r in pool.map(first, [ids[i : i + batch] for i in range(0, len(ids), batch)]):
            got.update(r)
        for x in ids:
            error = check(got.get(x))
            if error:
                retry.append((x, error))
            else:
                final[x] = {**got[x], "status": "ok"}
        for x, item in pool.map(again, retry):
            final[x] = item
    return final


def write_names(
    G: Graph, label: str, named: dict[str, dict], model: str, extra: tuple[str, ...] = ()
) -> None:
    """Store names on (:label {id}): name, description, name_status, name_error, named_by, plus `extra` fields."""
    fields = ("name", "description", *extra)
    sets = ", ".join(f"n.{f} = r.{f}" for f in fields)
    G.batch(
        f"{label}.name",
        f"""UNWIND $rows AS r MATCH (n:{label} {{id: r.id}})
            SET {sets}, n.name_status = r.status, n.name_error = r.error, n.named_by = r.model""",
        [
            {
                "id": x,
                **{f: (None if d.get(f) == "" else d.get(f)) for f in fields},
                "status": d["status"],
                "error": d.get("error"),
                "model": model,
            }
            for x, d in named.items()
        ],
    )


# -------------------------------------------------------------- embeddings


class Embedder:
    def __init__(self, settings: Settings):
        endpoint, version = secret("AZURE_OPENAI_ENDPOINT").rstrip("/"), secret("AZURE_OPENAI_API_VERSION")
        e = settings["embeddings"]
        self.url = f"{endpoint}/openai/deployments/{e['deployment']}/embeddings?api-version={version}"
        self.key, self.dims = secret("AZURE_OPENAI_API_KEY"), e["dimensions"]
        self.cache_path = settings.work / "emb_cache.json"
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}

    def embed(self, texts: list[str]) -> list[list[float]]:
        keys = [hashlib.sha256(f"{self.dims}|{t}".encode()).hexdigest() for t in texts]
        todo = [(k, t) for k, t in zip(keys, texts) if k not in self.cache]
        for i in range(0, len(todo), 64):
            chunk = todo[i : i + 64]
            body = json.dumps({"input": [t for _, t in chunk], "dimensions": self.dims}).encode()
            for attempt in range(5):
                try:
                    req = urllib.request.Request(
                        self.url, data=body, headers={"api-key": self.key, "Content-Type": "application/json"}
                    )
                    with urllib.request.urlopen(req, timeout=120) as r:
                        data = json.loads(r.read())["data"]
                    break
                except urllib.error.HTTPError as e:
                    if e.code != 429 or attempt == 4:
                        raise
                    time.sleep(2**attempt * 2)
            for (k, _), d in zip(chunk, sorted(data, key=lambda d: d["index"])):
                self.cache[k] = d["embedding"]
        if todo:
            self.cache_path.write_text(json.dumps(self.cache))
        return [self.cache[k] for k in keys]


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine of two embeddings (they are unit length, so the dot product)."""
    return sum(x * y for x, y in zip(a, b))
