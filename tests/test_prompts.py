"""Every prompt file is used, and every call fills exactly the placeholders its file has."""

from __future__ import annotations

import ast
import re

from conftest import PROMPTS, SRC

BUSINESS = {"business", "kind"}  # what **settings.business supplies


def calls() -> list[tuple[str, set[str], str]]:
    """(prompt name, keyword names supplied, where) for every prompt("literal", ...) call in the pipeline."""
    out = []
    for path in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "prompt":
                name = node.args[0]
                assert isinstance(name, ast.Constant), (
                    f"{path.name}:{node.lineno}: prompt names must be literals"
                )
                keys = {k.arg for k in node.keywords if k.arg}
                if any(k.arg is None for k in node.keywords):  # **s.business
                    keys |= BUSINESS
                out.append((name.value, keys, f"{path.name}:{node.lineno}"))
    return out


def placeholders(name: str) -> set[str]:
    return set(re.findall(r"\{(\w+)\}", (PROMPTS / f"{name}.md").read_text()))


def test_every_call_fills_its_prompt():
    for name, keys, where in calls():
        assert (PROMPTS / f"{name}.md").exists(), f"{where}: no prompts/{name}.md"
        missing = placeholders(name) - keys
        assert not missing, f"{where}: prompts/{name}.md needs {missing}"


def test_every_prompt_is_used_and_listed():
    used = {name for name, _, _ in calls()}
    files = {p.stem for p in PROMPTS.glob("*.md") if p.name != "README.md"}
    assert files == used, f"unused: {files - used}"
    readme = (PROMPTS / "README.md").read_text()
    assert all(f"`{f}.md`" in readme for f in files), "prompts/README.md does not list every prompt"
