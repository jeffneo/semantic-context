"""The text source: an events file read as conversations of turns.

The estate's config says where the events are (`process.events`) and what its fields are called (`process.fields`); the default
names are the event object of plans/2026-10-05-process-corpus.md. A turn becomes a State (what the customer said, so where the
case stands) or an Action (what the agent did) by its role (`process.kinds`); channels that summarise a whole conversation are
named in `process.skip_channels` and never become turns, because they would put the end of a conversation into every State.
Nothing here reads an answer key, and nothing names an estate: the file is the only input.
"""

from __future__ import annotations

import gzip
import io
import json
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from qlsc.config import ConfigError, Settings
from qlsc.warehouse import gcs

KINDS = ("state", "action")


class SourceError(RuntimeError):
    """The events cannot be read, or are not what the config says they are."""


@dataclass(frozen=True)
class Turn:
    event: str
    conversation: str
    seq: int
    time: str
    channel: str
    role: str
    kind: str  # state | action
    text: str


@dataclass
class Source:
    location: str
    conversations: dict[str, list[Turn]]  # in conversation order, each by sequence
    skipped: Counter  # events that are not turns, by why: "channel case_note", "role system"

    @property
    def turns(self) -> int:
        return sum(len(t) for t in self.conversations.values())


def location(s: Settings) -> str:
    where = s["process"]["events"]
    if not where:
        raise ConfigError("process.events is not set: the events file, a path, gs:// URI or https URL")
    return where


def read_bytes(s: Settings, where: str) -> bytes:
    """A path (relative to the config), a gs:// URI (read as the project's identity) or an https URL."""
    try:
        if where.startswith("gs://"):
            return gcs.read(where, s["warehouse"]["gcloud_config"])
        if where.startswith(("http://", "https://")):
            with urllib.request.urlopen(where, timeout=gcs.TIMEOUT) as response:
                return response.read()
        path = Path(where)
        return (path if path.is_absolute() else s.resolve(where)).read_bytes()
    except (OSError, gcs.StorageError) as e:
        raise SourceError(f"cannot read {where}: {e}") from e


def lines(data: bytes, where: str):
    text = gzip.decompress(data) if where.endswith(".gz") else data
    return io.StringIO(text.decode("utf-8"))


def read(s: Settings) -> Source:
    """The events as ordered conversations. Fails if a field the config names is missing, or a role maps to neither kind."""
    where = location(s)
    cfg = s["process"]
    f, skip = cfg["fields"], set(cfg["skip_channels"])
    kinds = {k["role"]: k["kind"] for k in cfg["kinds"]}
    bad = {r: k for r, k in kinds.items() if k not in KINDS}
    if bad:
        raise ConfigError(f"process.kinds must map each role to one of {KINDS}: {bad}")
    by_conversation: dict[str, list[Turn]] = defaultdict(list)
    skipped: Counter = Counter()
    seen: set[str] = set()
    for n, line in enumerate(lines(read_bytes(s, where), where), 1):
        if not line.strip():
            continue
        e = json.loads(line)
        missing = [name for name in f.values() if name not in e]
        if missing:
            raise SourceError(f"{where} line {n}: no field {missing} (process.fields names them)")
        if e[f["event"]] in seen:
            raise SourceError(f"{where} line {n}: event {e[f['event']]} appears twice")
        seen.add(e[f["event"]])
        if e[f["channel"]] in skip:
            skipped[f"channel {e[f['channel']]}"] += 1
        elif e[f["role"]] not in kinds:
            skipped[f"role {e[f['role']]}"] += 1
        else:
            by_conversation[e[f["conversation"]]].append(
                Turn(
                    event=e[f["event"]],
                    conversation=e[f["conversation"]],
                    seq=int(e[f["order"]]),
                    time=e[f["time"]],
                    channel=e[f["channel"]],
                    role=e[f["role"]],
                    kind=kinds[e[f["role"]]],
                    text=e[f["text"]],
                )
            )
    ordered = {c: sorted(t, key=lambda x: x.seq) for c, t in sorted(by_conversation.items())}
    return Source(where, ordered, skipped)


def live(s: Settings, lines: list[dict]) -> list[Turn]:
    """A conversation in progress, as an agent holds it: [{role, text}] in order, as turns. A role the config does not map to a kind is an error:
    a turn the build would not have read is not one to locate a case by."""
    kinds = {k["role"]: k["kind"] for k in s["process"]["kinds"]}
    out = []
    for i, line in enumerate(lines):
        if line.get("role") not in kinds or not str(line.get("text", "")).strip():
            raise SourceError(f"line {i + 1}: a role from {sorted(kinds)} and some text, not {line!r}")
        role, text = line["role"], str(line["text"])
        out.append(Turn(f"live-{i}", "live", i, "", "live", role, kinds[role], text))
    return out


def notes(s: Settings) -> dict[str, str]:
    """The agent's after-call note per conversation (`process.outcomes.note_channels`): text that summarises the whole conversation, which
    the turns exclude and the outcome reads. Several notes of one conversation are joined in order."""
    where = location(s)
    cfg = s["process"]
    f, channels = cfg["fields"], set(cfg["outcomes"]["note_channels"])
    found: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for line in lines(read_bytes(s, where), where):
        if not line.strip():
            continue
        e = json.loads(line)
        if e[f["channel"]] in channels:
            found[e[f["conversation"]]].append((int(e[f["order"]]), e[f["text"]]))
    return {c: "\n".join(t for _, t in sorted(x)) for c, x in found.items()}


def summary(s: Settings) -> None:
    src = read(s)
    kinds = Counter(t.kind for turns in src.conversations.values() for t in turns)
    print(f"{src.location}")
    print(f"  {len(src.conversations):,} conversations, {src.turns:,} turns")
    print("  " + ", ".join(f"{n:,} {k}s" for k, n in sorted(kinds.items())))
    for why, n in sorted(src.skipped.items()):
        print(f"  not a turn: {n:,} ({why})")
