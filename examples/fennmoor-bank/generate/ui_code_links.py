"""Re-pin the page's links to the code -> ui/src/examples/fennmoor/code-links.json.

Each section of the page lists the code that does its work (code-links.json: a label, a path and the symbol a line names), linked to a commit, since a branch's
lines move. When the code changes, this moves the links: it names the commit (the newest one on GitHub by default, so every link resolves), finds each symbol in that
commit's file, and writes the commit and the lines. A file or symbol that is gone is an error to fix by hand, not a link left pointing at the wrong line.

uv run examples/fennmoor-bank/generate/ui_code_links.py            # origin/main, after `git fetch`
uv run examples/fennmoor-bank/generate/ui_code_links.py <ref>      # another commit, branch or tag (a commit not pushed makes links GitHub cannot open)
uv run examples/fennmoor-bank/generate/ui_code_links.py --check    # nothing written: whether the links already hold at their commit

tests/test_code_links.py checks the same thing at the commit written. Add a link by adding an entry (label, path, and symbol with a `line` as a first guess) to the JSON.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILE = ROOT / "ui" / "src" / "examples" / "fennmoor" / "code-links.json"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def pattern(symbol: str) -> re.Pattern:
    """The symbol as a whole word where it ends in one (`def run` is not `def run_batch`)."""
    return re.compile(re.escape(symbol) + (r"\b" if symbol[-1].isalnum() or symbol[-1] == "_" else ""))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    data = json.loads(FILE.read_text())
    ref = args[0] if args else (data["commit"] if check else "origin/main")
    sha = git("rev-parse", "--verify", f"{ref}^{{commit}}")
    if sha.returncode:
        print(f"no commit {ref!r} here (git fetch?)")
        return 1
    commit = sha.stdout.strip()

    problems, moved = [], 0
    for section, refs in data["sections"].items():
        for r in refs:
            shown = git("show", f"{commit}:{r['path']}")
            if shown.returncode:
                problems.append(f"{section}: {r['path']} is not in {commit[:7]}")
                continue
            if "line" not in r:
                continue
            found = [
                i for i, text in enumerate(shown.stdout.splitlines(), 1) if pattern(r["symbol"]).search(text)
            ]
            if not found:
                problems.append(
                    f"{section}: {r['label']}: {r['symbol']!r} is not in {r['path']} at {commit[:7]}"
                )
                continue
            line = min(
                found, key=lambda i: abs(i - r["line"])
            )  # the nearest to where it was, if the symbol is named more than once
            if line != r["line"]:
                moved += 1
                print(f"  {section}: {r['label']}: line {r['line']} -> {line}")
                r["line"] = line
    if problems:
        print("\n".join(problems))
        return 1
    if check:
        print(
            f"every link holds at {commit[:7]}"
            if not moved
            else f"{moved} links are off their lines at {commit[:7]}"
        )
        return 1 if moved else 0
    data["commit"] = commit
    FILE.write_text(json.dumps(data, indent=1) + "\n")
    print(
        f"{FILE.relative_to(ROOT)}: pinned to {commit[:7]}, {sum(map(len, data['sections'].values()))} links, {moved} moved"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
