"""The config: defaults merge with an estate's file, and every parameter in defaults.yaml is read."""

from __future__ import annotations

import yaml
from conftest import SRC

from qlsc import config


def leaves(d: dict, prefix=()) -> list[tuple[str, ...]]:
    out = []
    for k, v in d.items():
        out += leaves(v, (*prefix, k)) if isinstance(v, dict) else [(*prefix, k)]
    return out


def test_every_parameter_is_read():
    """A setting nothing reads is a setting someone will tune for no effect."""
    code = "\n".join(p.read_text() for p in SRC.rglob("*.py"))
    defaults = yaml.safe_load(config.DEFAULTS.read_text())
    unread = [
        ".".join(path)
        for path in leaves(defaults)
        if f'"{path[-1]}"' not in code and f"'{path[-1]}'" not in code
    ]
    assert not unread, f"settings no code reads: {unread}"


def test_estate_overrides_defaults(tmp_path):
    f = tmp_path / "estate.yaml"
    f.write_text("cluster:\n  gamma: 2.5\nbusiness: {name: an insurer, kind: insurer}\n")
    s = config.load(f)
    assert s["cluster"]["gamma"] == 2.5
    assert s["cluster"]["seed"] == 42  # the rest of the section stays
    assert s.business == {"business": "an insurer", "kind": "insurer"}
    assert s.work == tmp_path / "work" and s.work.is_dir()


def test_missing_config_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.delenv("QLSC_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    try:
        config.load(None)
    except config.ConfigError as e:
        assert "QLSC_CONFIG" in str(e)
    else:
        raise AssertionError("expected a ConfigError")


def test_an_llm_call_is_priced_at_its_models_rate(tmp_path, monkeypatch):
    """The query model costs what it costs, not Haiku's rate."""
    from qlsc.llm import LLM

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    f = tmp_path / "estate.yaml"
    f.write_text("business: {name: a bank, kind: bank}\n")
    s = config.load(f)
    naming, query = LLM("", s), LLM("", s, s["llm"]["query_model"])
    for c in (naming, query):
        c.tokens.update({"in": 1_000_000, "out": 1_000_000})
    assert naming.cost() == 6.0 and query.cost() == 12.0
