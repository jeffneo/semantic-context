"""Join confidence (qlsc/joins.py), the method's central rule: a join is suspect when it equates two id
spaces that production keeps as separate columns of one table; production outranks people; two people
who made the same join independently corroborate it."""

from __future__ import annotations

from qlsc.joins import confidence, joins_identity, suspects

# dim_account holds both of the bank's account ids, core and card, and production translates between
# them there. A card transaction carries the card id; a core transaction, the core id.
COLS = {
    "dim_account.core_id": {"name": "core_id", "table": "dim_account", "type": "INT64"},
    "dim_account.card_id": {"name": "card_id", "table": "dim_account", "type": "INT64"},
    "fct_core.core_id": {"name": "core_id", "table": "fct_core", "type": "INT64"},
    "fct_card.card_id": {"name": "card_id", "table": "fct_card", "type": "INT64"},
    "rpt.card_id": {"name": "card_id", "table": "rpt", "type": "INT64"},
}
TABLE_COLS = {}
for c, m in COLS.items():
    TABLE_COLS.setdefault(m["table"], set()).add(c)


def key(i, left, right, identity=True, **kw):
    return {"id": i, "l": left, "r": right, "identity": identity, "production": False, "people": [], **kw}


PRODUCTION = [
    key("p1", "fct_core.core_id", "dim_account.core_id", production=True, services=["dbt@x"]),
    key("p2", "fct_card.card_id", "dim_account.card_id", production=True, services=["dbt@x"]),
]


def test_a_join_across_two_id_spaces_production_keeps_apart_is_suspect():
    wrong = key("h1", "fct_core.core_id", "fct_card.card_id", people=["ann@x"])
    right = key("h2", "fct_card.card_id", "rpt.card_id", people=["bob@x"])
    found = suspects(PRODUCTION, [wrong, right], [], COLS, TABLE_COLS)
    assert set(found) == {"h1"} and found["h1"] == ["dim_account"]  # the table that keeps them apart


def test_wrong_joins_cannot_vouch_for_each_other():
    """Two people making the same wrong join are still judged against production first."""
    a = key("h1", "fct_core.core_id", "fct_card.card_id", people=["ann@x"])
    b = key("h2", "fct_core.core_id", "fct_card.card_id", people=["bob@x"])
    assert set(suspects(PRODUCTION, [a, b], [], COLS, TABLE_COLS)) == {"h1", "h2"}


def test_separation_needs_positive_evidence():
    """Two id spaces that never met in production are not thereby separate: no suspicion without a table
    that holds both."""
    lone = key("h1", "fct_core.core_id", "fct_card.card_id", people=["ann@x"])
    assert suspects([], [lone], [], COLS, TABLE_COLS) == {}


def test_confidence_ranks_production_then_evidence_from_people():
    assert confidence(PRODUCTION[0], {})[0] == "production"
    suspect = key("h1", "fct_core.core_id", "fct_card.card_id", people=["ann@x", "bob@x"])
    assert confidence(suspect, {"h1": ["dim_account"]})[0] == "suspect"
    assert confidence(key("h2", "a", "b", people=["ann@x", "bob@x"]), {})[0] == "corroborated"
    assert confidence(key("h3", "a", "b", people=["ann@x"]), {})[0] == "single"
    assert confidence(key("h4", "a", "a", people=["ann@x"]), {})[0] == "self"


def test_a_join_through_a_format_function_still_says_identity():
    assert joins_identity([{"wraps": ["TRIM", "CAST<STRING>"], "vias": ["direct", "direct"]}])
    assert not joins_identity([{"wraps": ["DATE_TRUNC"], "vias": ["direct", "direct"]}])
