"""The page's links to the code (ui/src/examples/fennmoor/code-links.json) name a commit; each link's file is in it, and its symbol is on the line named."""

from __future__ import annotations

import json
import subprocess

import pytest
from conftest import ROOT

LINKS = json.loads((ROOT / "ui" / "src" / "examples" / "fennmoor" / "code-links.json").read_text())
REFS = [(s, r) for s, refs in LINKS["sections"].items() for r in refs]


def show(path: str) -> str | None:
    p = subprocess.run(["git", "show", f"{LINKS['commit']}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


@pytest.fixture(scope="module", autouse=True)
def has_commit():
    if subprocess.run(["git", "cat-file", "-e", LINKS["commit"]], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("the linked commit is not in this checkout")


@pytest.mark.parametrize(("section", "ref"), REFS, ids=[f"{s}:{r['label']}" for s, r in REFS])
def test_link_points_at_its_symbol(section, ref):
    text = show(ref["path"])
    assert text is not None, f"{ref['path']} is not in {LINKS['commit'][:7]}"
    if "line" in ref:
        assert ref["symbol"] in text.splitlines()[ref["line"] - 1], (
            f"{ref['symbol']!r} is not on line {ref['line']} of {ref['path']}"
        )
