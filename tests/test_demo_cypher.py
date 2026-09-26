"""Every query in the example's demo.cypher runs against the example's graph and returns something."""

from __future__ import annotations

import re

import pytest
from conftest import EXAMPLE


def statements() -> list[tuple[str, str]]:
    text = (EXAMPLE / "demo.cypher").read_text()
    out = []
    for chunk in text.split(";"):
        lines = [line for line in chunk.splitlines() if line.strip()]
        titles = [line for line in lines if re.match(r"//\s*\d+\.\d+", line)]
        cypher = "\n".join(line for line in lines if not line.lstrip().startswith("//"))
        if cypher.strip():
            out.append((titles[-1].strip("/ ").split("  ")[0] if titles else cypher[:40], cypher))
    return out


@pytest.mark.parametrize(("title", "cypher"), statements(), ids=[t for t, _ in statements()])
def test_demo_query(graph, title, cypher):
    assert graph.rows(cypher), f"{title} returned nothing"
