"""The tool knows nothing about the example: the pipeline and its prompts never name the example's
estate, read its answer key, or assume its warehouse. Only the example may import the tool."""

from __future__ import annotations

import re

from conftest import PROMPTS, SRC

ESTATE_WORDS = re.compile(r"(?i)fennmoor|examples/|\bspec/|answer_key|jobs_truth|\bretail bank\b|jeffdavis")


def test_pipeline_never_names_the_example():
    hits = [
        f"{p.relative_to(SRC)}:{i}"
        for p in SRC.rglob("*.py")
        for i, line in enumerate(p.read_text().splitlines(), 1)
        if ESTATE_WORDS.search(line)
    ]
    assert not hits, f"the pipeline refers to the example: {hits}"


def test_prompts_never_name_the_estate():
    hits = [
        p.name for p in PROMPTS.glob("*.md") if p.name != "README.md" and ESTATE_WORDS.search(p.read_text())
    ]
    assert not hits, f"prompts name the estate; use {{business}} / {{kind}}: {hits}"


def test_only_the_bigquery_connector_imports_google():
    hits = [
        str(p.relative_to(SRC))
        for p in SRC.rglob("*.py")
        if "google" in p.read_text() and p.name != "bigquery.py"
    ]
    assert not hits, f"warehouse code outside src/qlsc/warehouse/bigquery.py: {hits}"
