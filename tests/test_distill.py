"""Distillation's pure parts, without a database (plans/2026-09-29-context-memory-model.md, memory phase 4)."""

from __future__ import annotations

import json

from qlsc import distill


def test_a_request_masked_holds_no_values():
    request = "Card spend for customer 8322097816940277129 ('Ana Campbell', ana@example.com) since 2026-04-01, last 90 days"
    masked = distill.mask(request)
    assert (
        "8322097816940277129" not in masked
        and "Ana Campbell" not in masked
        and "ana@example.com" not in masked
    )
    assert "2026-04-01" not in masked and "last 90 days" in masked  # a small number is the kind of request


def test_what_a_task_named_is_what_a_skill_must_not_say():
    task = {
        "request": "Prepare me for customer 8322097816940277129",
        "steps": [{"arguments": json.dumps({"label": "Customer", "key": "8322097816940277129"}),
                   "result": json.dumps({"query": "SELECT … WHERE customer_key = 8322097816940277129 AND x = 'KS'"})}],
    }  # fmt: skip
    assert {"8322097816940277129"} <= distill.literals(task)


def test_success_and_similarity():
    ok = {"status": "done", "steps": [{"status": "ok"}, {"status": "ok"}], "verdicts": ["helpful"]}
    assert distill.success(ok, ["wrong"])
    assert not distill.success(ok | {"verdicts": ["wrong"]}, ["wrong"])
    assert not distill.success(ok | {"steps": [{"status": "ok"}, {"status": "error"}]}, ["wrong"])
    assert distill.jaccard({"a", "b"}, {"b", "c"}) == 1 / 3 and distill.jaccard(set(), set()) == 0.0


def test_a_procedure_is_written_from_the_schema():
    shape = {
        "measures": [{"aggregate": "SUM", "column": "dw.fct_txn.amount"}],
        "dimensions": [{"column": "dw.dim_merchant.category"}],
        "filters": [{"column": "dw.fct_txn.customer_key", "op": "="}],
        "period": {"column": "dw.fct_txn.post_date", "from": "?", "to": "?"},
    }
    text = distill.readable_step("ask " + json.dumps(shape))
    assert text == (
        "ask SUM(fct_txn.amount) by dim_merchant.category where fct_txn.customer_key = ? over a period of fct_txn.post_date"
    )
    assert distill.readable_step("recall Customer ?") == "recall the Customer's context"
    by_name = distill.readable_step('ask {"measures": [{"computation": "c1"}]}', {"c1": "Card Spend"})
    assert by_name == "ask Card Spend"
