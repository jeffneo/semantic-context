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


def test_memory_can_have_an_instance_of_its_own(tmp_path):
    """Memory is on the semantic layer's instance unless `memory.neo4j` names another: its uri changes, nothing else does."""
    from qlsc import memory

    f = tmp_path / "estate.yaml"
    f.write_text("neo4j: {uri: 'bolt://layer:7687', database: bigquery, user: neo4j}\n")
    s = config.load(f)
    assert memory.memory_instance(s) == {"database": "memory"}  # the layer's instance
    assert memory.memory_instance(s, "system") == {"database": "system"}
    f.write_text(
        "neo4j: {uri: 'bolt://layer:7687', database: bigquery, user: neo4j}\nmemory: {neo4j: {uri: 'bolt://memory:7687'}}\n"
    )
    s = config.load(f)
    assert memory.memory_instance(s) == {"uri": "bolt://memory:7687", "database": "memory"}
    assert s["neo4j"]["uri"] == "bolt://layer:7687"


def test_a_deployment_overrides_the_estate(tmp_path, monkeypatch):
    """QLSC_OVERRIDES is a second file merged over the estate's: a deployment says where its databases are and how it signs in, and nothing else changes."""
    monkeypatch.delenv(
        "QLSC_GCP_PROJECT", raising=False
    )  # the person's own project, from .env, is not what is being tested
    monkeypatch.setattr(config, "_dotenv", lambda start: {})
    f = tmp_path / "estate.yaml"
    f.write_text(
        "neo4j: {uri: 'bolt://localhost:7690', database: bigquery, user: neo4j}\nwarehouse: {project: p, gcloud_config: qlsc}\n"
    )
    o = tmp_path / "hosted.yaml"
    o.write_text("neo4j: {uri: 'neo4j+ssc://db-semantic:7687'}\nwarehouse: {identity: ambient}\n")
    assert config.load(f)["warehouse"]["identity"] == "gcloud"  # the default: a workstation
    monkeypatch.setenv("QLSC_OVERRIDES", str(o))
    s = config.load(f)
    assert s["neo4j"] == {"uri": "neo4j+ssc://db-semantic:7687", "database": "bigquery", "user": "neo4j"}
    assert s["warehouse"] == {"identity": "ambient", "project": "p", "gcloud_config": "qlsc"}


def test_overrides_can_be_given_inline(tmp_path, monkeypatch):
    """A value in curly braces is the settings themselves, not a path: what an environment variable carries."""
    f = tmp_path / "estate.yaml"
    f.write_text("neo4j: {uri: 'bolt://localhost:7690', database: bigquery, user: neo4j}\n")
    monkeypatch.setenv(
        "QLSC_OVERRIDES",
        '{"neo4j": {"uri": "bolt://10.10.0.4:7687"}, "memory": {"neo4j": {"uri": "bolt://10.10.0.3:7687"}}}',
    )
    s = config.load(f)
    assert s["neo4j"]["uri"] == "bolt://10.10.0.4:7687" and s["neo4j"]["database"] == "bigquery"
    assert s["memory"]["neo4j"] == {"uri": "bolt://10.10.0.3:7687"}


def test_the_project_comes_from_the_environment_and_the_principals_follow_it(tmp_path, monkeypatch):
    """No committed file names the project: the estate has a placeholder, QLSC_GCP_PROJECT the real one, and the test principals' addresses are written with {project}."""
    f = tmp_path / "estate.yaml"
    f.write_text(
        "warehouse: {project: your-project-id}\nentitlements:\n  principals:\n    risk: qlsc-risk@{project}.iam.gserviceaccount.com\n"
    )
    monkeypatch.delenv("QLSC_GCP_PROJECT", raising=False)
    monkeypatch.setattr(config, "_dotenv", lambda start: {})
    s = config.load(f)
    assert s["warehouse"]["project"] == "your-project-id"
    assert s["entitlements"]["principals"]["risk"] == "qlsc-risk@your-project-id.iam.gserviceaccount.com"
    monkeypatch.setenv("QLSC_GCP_PROJECT", "the-real-one")
    s = config.load(f)
    assert s["warehouse"]["project"] == "the-real-one"
    assert s["entitlements"]["principals"]["risk"] == "qlsc-risk@the-real-one.iam.gserviceaccount.com"
