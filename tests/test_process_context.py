"""Context (src/qlsc/process/context.py): the ways an amount is written and said, linking what turns say to a customer's rows by
lookup, and the SQL for a table beyond the virtual graph's model. No warehouse, no Neo4j."""

from __future__ import annotations

import pytest

from qlsc.process import context
from qlsc.process.source import Turn


def turn(seq, text, role="customer"):
    return Turn(f"e{seq}", "c", seq, "t", "voice_turn", role, "state", text)


def test_a_number_is_said_the_way_a_person_says_it():
    assert [context.words(n) for n in (0, 12, 40, 74, 100, 117, 999)] == [
        "zero", "twelve", "forty", "seventy-four", "one hundred", "one hundred seventeen", "nine hundred ninety-nine"
    ]  # fmt: skip


def test_an_amount_has_the_forms_people_write_and_say():
    f = context.forms(7.65)
    assert {"$7.65", "7.65", "seven dollars and sixty five cents", "seven sixty five"} <= set(f)
    assert "forty two dollars" in context.forms(42.0) and "$42" in context.forms(42.0)
    assert "eleven dollars and six cents" in context.forms(11.06) and "eleven oh six" in context.forms(11.06)
    assert "a hundred seventeen fourteen" in context.forms(117.14)
    assert context.forms(1234.5) == ["$1234.50", "1234.50"]  # beyond words, only as digits


def test_a_form_stands_alone_in_the_text():
    assert context.present("$42", "it was $42 at the shop") and not context.present("$42", "it was $42.50")
    assert not context.present("7.65", "a fee of $17.65") and context.present("7.65", "a fee of 7.65 today")
    assert not context.present("five fifty", "twenty five fifty")


FEES = [
    {"fee_id": 2, "fee_amount": 7.65, "assessed_date": "2026-05-12"},
    {"fee_id": 1, "fee_amount": 7.65, "assessed_date": "2026-04-02"},  # the same amount, older
    {"fee_id": 3, "fee_amount": 19.34, "assessed_date": "2026-04-07"},
]
MERCHANTS = [
    {"merchant_id": "M1", "merchant_name": "Blue Plate Diner"},
    {"merchant_id": "M2", "merchant_name": "Corner Market"},
]
RULES = [
    {"label": "Merchant", "name": "merchant_name"},
    {"table": "dw_core.fct_fees", "key": "fee_id", "amount": "fee_amount"},
]
KEYS = {"Merchant": "merchant_id", "dw_core.fct_fees": "fee_id"}


def linked(turns):
    return context.link(RULES, {"Merchant": MERCHANTS, "dw_core.fct_fees": FEES}, KEYS, turns)


def test_a_name_and_an_amount_are_matched_to_the_customers_own_rows():
    got = linked(
        [
            turn(0, "I'm looking at a charge at blue plate diner."),
            turn(2, "Yeah, a fee of nineteen thirty-four."),
        ]
    )
    assert [(x.label, x.key, x.kind, x.turn) for x in got] == [
        ("Merchant", "M1", "name", 0),
        ("dw_core.fct_fees", 3, "amount", 2),
    ]


def test_of_rows_with_one_amount_the_most_recent_and_nothing_a_customer_did_not_have():
    got = linked([turn(0, "The $7.65 fee, and a charge at Harbor Inn.")])
    assert [(x.key) for x in got] == [
        2
    ]  # fee 2 is listed first (most recent); Harbor Inn is nobody's merchant here


def test_a_link_is_found_at_the_turn_it_is_first_said():
    got = linked([turn(0, "Hello."), turn(1, "The $7.65 one."), turn(3, "Yes, the $7.65 fee.")])
    assert got[0].turn == 1


def test_the_context_of_a_table_beyond_the_model_is_one_customers_window_by_the_layers_own_columns():
    assert context.literal(7) == "7" and context.literal("o'neil") == "'o\\'neil'"
    with pytest.raises(context.ContextError):
        context.literal(True)
    import datetime as dt

    assert context.date_of("2026-06-09T14:04:01+00:00") == dt.date(2026, 6, 9)
    assert context.date_of(dt.date(2026, 6, 9)) == dt.date(2026, 6, 9)


TWINS = [  # three merchants of one name: a name cannot say which
    {"merchant_id": "M7", "merchant_name": "Blue Plate Diner"},
    {"merchant_id": "M8", "merchant_name": "Blue Plate Diner"},
]
PURCHASES = [  # most recent first, each carrying the merchant it points at
    {
        "settlement_id": "S2",
        "amount": 46.37,
        "Merchant.merchant_id": "M8",
        "Merchant.merchant_name": "Blue Plate Diner",
    },
    {
        "settlement_id": "S1",
        "amount": 12.0,
        "Merchant.merchant_id": "M7",
        "Merchant.merchant_name": "Blue Plate Diner",
    },
]
PURCHASE_RULES = [
    {"label": "Merchant", "name": "merchant_name"},
    {"label": "CardTransaction", "amount": "amount", "name": "Merchant.merchant_name", "emit": "Merchant"},
]
PURCHASE_KEYS = {"Merchant": "merchant_id", "CardTransaction": "settlement_id"}


def purchases(text):
    return context.link(
        PURCHASE_RULES, {"Merchant": TWINS, "CardTransaction": PURCHASES}, PURCHASE_KEYS, [turn(0, text)]
    )


def test_a_name_several_merchants_share_links_nothing_by_itself():
    assert purchases("A charge at Blue Plate Diner.") == []


def test_a_purchases_amount_and_merchant_name_pick_out_the_one_merchant():
    got = purchases("A charge of $46.37 at Blue Plate Diner.")
    assert [(x.label, x.key) for x in got] == [
        ("CardTransaction", "S2"),
        ("Merchant", "M8"),
    ]  # not M7, which shares the name
    assert (
        purchases("A charge of $46.37.") == []
    )  # the amount alone says nothing of the merchant, and the rule wants both
    assert purchases("Twelve dollars at the Blue Plate Diner")[0].key == "S1"


def test_the_links_of_a_turn_never_use_the_future():
    later = [turn(0, "Hello."), turn(5, "The $46.37 at Blue Plate Diner.")]
    got = context.link(
        PURCHASE_RULES, {"Merchant": TWINS, "CardTransaction": PURCHASES}, PURCHASE_KEYS, later[:1]
    )
    assert got == []
    got = context.link(
        PURCHASE_RULES, {"Merchant": TWINS, "CardTransaction": PURCHASES}, PURCHASE_KEYS, later
    )
    assert {x.turn for x in got} == {5}


class Ctx:
    """The parts of a fetched context the lookup reads: its nodes, and the relationships between them."""

    def __init__(self, nodes, edges):
        self.nodes, self.edges = nodes, edges


def test_a_row_carries_the_properties_of_the_row_it_points_at():
    ctx = Ctx(
        {
            ("CardTransaction", "S1"): {"settlement_id": "S1", "amount": 5.0, "merchant_id": "M1"},
            ("Merchant", "M1"): {"merchant_id": "M1", "merchant_name": "Corner Market"},
            ("Merchant", "M2"): {
                "merchant_id": "M2",
                "merchant_name": "Elsewhere",
            },  # nobody here points at it
        },
        {("TRANSACTED_WITH", "CardTransaction", "S1", "Merchant", "M1")},
    )
    rows = context.neighbours(ctx)
    assert rows["CardTransaction"][0]["Merchant.merchant_name"] == "Corner Market"
    assert "Merchant.merchant_name" not in rows["Merchant"][0]  # a pointed-at row gains nothing
