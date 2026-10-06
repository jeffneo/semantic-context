"""The text source (src/qlsc/process/source.py): events read as ordered conversations of turns, by the config's field names and
role map, from a path, an https URL or a bucket. No network and no gcloud: the readers are faked."""

from __future__ import annotations

import gzip
import json

import pytest

from qlsc import config
from qlsc.process import source
from qlsc.warehouse import gcs

EVENTS = [
    # out of order within a conversation, and a note, a system line and a second conversation
    {
        "event_id": "e2",
        "conversation_id": "c1",
        "seq": 1,
        "ts": "t1",
        "channel": "voice_turn",
        "role": "customer",
        "text": "hi",
    },
    {
        "event_id": "e1",
        "conversation_id": "c1",
        "seq": 0,
        "ts": "t0",
        "channel": "voice_turn",
        "role": "agent",
        "text": "hello",
    },
    {
        "event_id": "e3",
        "conversation_id": "c1",
        "seq": 2,
        "ts": "t2",
        "channel": "case_note",
        "role": "agent",
        "text": "summary",
    },
    {
        "event_id": "e4",
        "conversation_id": "c0",
        "seq": 0,
        "ts": "t0",
        "channel": "system_log",
        "role": "system",
        "text": "hung up",
    },
    {
        "event_id": "e5",
        "conversation_id": "c0",
        "seq": 1,
        "ts": "t1",
        "channel": "chat_message",
        "role": "customer",
        "text": "yo",
    },
]


def settings(tmp_path, process: str = "") -> config.Settings:
    f = tmp_path / "estate.yaml"
    f.write_text(
        "business: {name: a bank, kind: bank}\nwarehouse: {gcloud_config: cfg}\nprocess:\n  events: events.ndjson\n"
        + process
    )
    return config.load(f)


def write(tmp_path, rows=EVENTS, name="events.ndjson", gz=False):
    body = "".join(json.dumps(r) + "\n" for r in rows)
    path = tmp_path / name
    if gz:
        path.write_bytes(gzip.compress(body.encode()))
    else:
        path.write_text(body)


def test_turns_are_ordered_and_a_note_or_a_system_line_is_not_a_turn(tmp_path):
    write(tmp_path)
    src = source.read(settings(tmp_path))
    assert list(src.conversations) == ["c0", "c1"]  # sorted: the same file is always the same graph
    assert [(t.event, t.kind) for t in src.conversations["c1"]] == [("e1", "action"), ("e2", "state")]
    assert src.skipped == {"channel case_note": 1, "channel system_log": 1}
    assert src.turns == 3


def test_a_gz_file_is_decompressed(tmp_path):
    write(tmp_path, name="events.ndjson.gz", gz=True)
    s = settings(tmp_path)
    s["process"]["events"] = "events.ndjson.gz"
    assert source.read(s).turns == 3


def test_the_field_names_and_the_roles_are_the_configs(tmp_path):
    rows = [{"id": "x", "call": "k", "n": 0, "at": "t", "chan": "voice", "who": "caller", "words": "hi"}]
    write(tmp_path, rows)
    cfg = (
        "  fields: {event: id, conversation: call, order: n, time: at, channel: chan, role: who, text: words}\n"
        "  kinds: [{role: caller, kind: state}]\n"
    )
    src = source.read(settings(tmp_path, cfg))
    assert [(t.event, t.kind, t.text) for t in src.conversations["k"]] == [("x", "state", "hi")]


def test_a_missing_field_a_repeated_event_and_a_bad_kind_are_errors(tmp_path):
    write(tmp_path, [{k: v for k, v in EVENTS[0].items() if k != "text"}])
    with pytest.raises(source.SourceError, match="no field"):
        source.read(settings(tmp_path))
    write(tmp_path, [EVENTS[0], EVENTS[0]])
    with pytest.raises(source.SourceError, match="twice"):
        source.read(settings(tmp_path))
    write(tmp_path)
    with pytest.raises(config.ConfigError, match="kinds"):
        source.read(settings(tmp_path, "  kinds: [{role: customer, kind: stat}]\n"))


def test_no_events_configured_is_a_clear_error(tmp_path):
    write(tmp_path)
    s = settings(tmp_path)
    s["process"]["events"] = None
    with pytest.raises(config.ConfigError, match="process.events"):
        source.read(s)


def test_a_bucket_is_read_as_the_configurations_identity_and_a_refusal_fails(tmp_path, monkeypatch):
    seen = {}

    def fake(uri, gcloud_config):
        seen.update(uri=uri, config=gcloud_config)
        return "".join(json.dumps(r) + "\n" for r in EVENTS).encode()

    monkeypatch.setattr(gcs, "read", fake)
    s = settings(tmp_path)
    s["process"]["events"] = "gs://bucket/full/events.ndjson"
    assert source.read(s).turns == 3
    assert seen == {"uri": "gs://bucket/full/events.ndjson", "config": "cfg"}

    def refuse(uri, gcloud_config):
        raise gcs.StorageError("403 Forbidden: the configuration's identity may not read it")

    monkeypatch.setattr(gcs, "read", refuse)
    with pytest.raises(source.SourceError, match="may not read"):
        source.read(s)


def test_a_bucket_location_is_split_and_a_bad_one_refused():
    assert gcs.split("gs://b/full/events.ndjson.gz") == ("b", "full/events.ndjson.gz")
    with pytest.raises(gcs.StorageError):
        gcs.split("gs://only-a-bucket")
