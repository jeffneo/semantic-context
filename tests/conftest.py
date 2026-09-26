"""Shared fixtures: the repository's paths, and the example's settings and graph when they are available."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "qlsc"
PROMPTS = ROOT / "prompts"
EXAMPLE = ROOT / "examples" / "fennmoor-bank"


@pytest.fixture(scope="session")
def example_settings():
    from qlsc import config

    return config.load(EXAMPLE / "estate.yaml")


@pytest.fixture(scope="session")
def graph(example_settings):
    """The example's graph; the test is skipped when Neo4j is not up or the password is not set."""
    from qlsc.config import ConfigError
    from qlsc.graph import Graph

    try:
        G = Graph(example_settings)
        G.value("RETURN 1")
    except (ConfigError, Exception) as e:  # no .env, no server
        pytest.skip(f"Neo4j not available: {e}")
    yield G
    G.close()
