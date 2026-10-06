"""Two pieces of the 101 demo (demo-101.md) that have no `qlsc` command, run from the repo root:

uv run examples/fennmoor-bank/demo.py composite
    one Cypher query over the composite database: what the semantic layer knows about a relationship, beside live
    rows through the virtual graph. The query goes to the virtual graph signed (its pass-through refuses an
    unsigned one), which is why it isn't pasted into Browser.
uv run examples/fennmoor-bank/demo.py process
    the process shard beside the rows, through the composite: the busiest State of the State-Action graph (fennmoor.process), the
    calls it was found in, and those calls' live rows (fennmoor.rows); then one of them with its customer's context as of the call,
    and the rows its words are about (qlsc process context).
uv run examples/fennmoor-bank/demo.py exchange [0|1|2]
    an agent asks, asks again, and rejects an answer: what each costs and what is remembered. The first ask is live
    only if that question hasn't been asked in the last day (answers are kept while their data holds); pick another
    number if the first line says "from memory".
"""

import sys
import time
from pathlib import Path

from qlsc import config, converse, entitle, meter
from qlsc.memory import virtual_graph

s = config.load(Path(__file__).parent / "estate.yaml")

COMPOSITE = """
CALL () {                                   // the semantic layer: where this relationship comes from
  USE fennmoor.semantic
  MATCH (t:Table {graph_label: 'Call'})-[:HAS_COLUMN]->(c:Column {graph_relationship: 'PROCESSED_AT'}),
        (c)-[:IS]->(v:Variable)-[:IN_SEMANTIC]->(g:Semantic)
  RETURN g.name AS business_area, v.name AS variable, t.name + '.' + c.name AS column
}
CALL () {                                   // the warehouse: live rows, through Virtual Graph
  USE fennmoor.rows
  MATCH (call:Call)-[:PROCESSED_AT]->(s:ContactCenterSite)
  WHERE call.is_account_closure_call = true AND $qlsc_principal IS NOT NULL   // the gateway's signature
  RETURN s.site_name AS site, count(call) AS closure_calls
}
RETURN business_area, variable, column, site, closure_calls ORDER BY closure_calls DESC
"""


QUESTIONS = [
    "How many calls did each contact center site handle since April 2026?",
    "What is the total deposit balance by customer segment?",
    "How many card transactions were there per merchant category last quarter?",
]


def composite() -> None:
    """One Cypher query over the composite database: what the layer knows, beside live BigQuery rows."""
    print(COMPOSITE)
    t0 = time.time()
    with virtual_graph(s) as V:
        V.db = "fennmoor"
        rows = V.rows(COMPOSITE, qlsc_principal=entitle.token(s, ""))
    for r in rows:
        print(
            f"{r['business_area']} | {r['variable']} | {r['column']} | {r['site']:26} {r['closure_calls']:>6,}"
        )
    print(f"{len(rows)} rows in {time.time() - t0:.1f} s")


PROCESS_STATE = """
USE fennmoor.process
MATCH (s:State) WHERE s.level = 1 AND s.count >= 50 AND size(s.example_conversations) > 0
RETURN s.name AS state, s.description AS description, s.count AS turns, s.example_conversations AS calls
ORDER BY turns DESC LIMIT 1
"""
PROCESS_ROWS = """
USE fennmoor.rows
MATCH (c:Call)-[:PROCESSED_AT]->(site:ContactCenterSite)
WHERE c.conversation_id IN $ids AND $qlsc_principal IS NOT NULL   // the gateway's signature
RETURN c.conversation_id AS call, c.ivr_intent AS intent, site.site_name AS site, c.handle_sec AS handle_sec,
       c.was_transferred AS transferred, c.is_authenticated AS authenticated
ORDER BY call
"""


def process() -> None:
    """A State of the process graph, the calls it came from, those calls' live rows, and one call's context as of the call."""
    from qlsc.process import context, source

    t0 = time.time()
    with virtual_graph(s) as V:
        V.db = "fennmoor"
        state = V.rows(PROCESS_STATE)[0]
        print(f"State: {state['state']}  ({state['turns']} turns)\n  {state['description']}")
        print(
            f"  seen in calls {', '.join(c[:8] for c in state['calls'])} (fennmoor.process, {time.time() - t0:.1f} s)"
        )
        t1 = time.time()
        rows = V.rows(PROCESS_ROWS, ids=state["calls"], qlsc_principal=entitle.token(s, ""))
    for r in rows:
        print(
            f"  {r['call'][:8]}  {r['intent']:13} {r['site']:24} {r['handle_sec']:>5} s  transferred={r['transferred']}  authenticated={r['authenticated']}"
        )
    print(f"  the same calls' rows, live from BigQuery through fennmoor.rows ({time.time() - t1:.1f} s)")
    first = state["calls"][0]
    turns = source.read(s).conversations[first]
    c = context.at(s, first, turns)
    print(f"\nOne of them, {first[:8]}, with its customer's context as of the call:")
    print(context.show(c, turns, None))


def exchange() -> None:
    """An agent asks, asks again, rejects an answer and corrects it: what each costs, and what is remembered."""
    c = converse.Conversation(s, "demo: an agent's exchange")
    q = QUESTIONS[int(sys.argv[2]) if len(sys.argv) > 2 else 0]
    c.say("user", q)
    for label, fn in (("first ask", lambda: c.ask(q)), ("the same ask again", lambda: c.ask(q))):
        with meter.measure() as m:
            a = fn()
        x = m.measure()
        print(
            f"{label:20} {'from memory' if a.get('from_memory') else 'computed':12} {x['seconds']:5.1f} s "
            f"{x['tokens']:6,.0f} tokens {x['warehouse_queries']:.0f} warehouse queries"
        )
    with meter.measure() as m:
        a = c.correct(q, "only purchases count, not refunds")
    x = m.measure()
    print(
        f"{'after a rejection':20} {'from memory' if a.get('from_memory') else 'computed':12} {x['seconds']:5.1f} s "
        f"{x['tokens']:6,.0f} tokens (route: {a.get('route')}); the rejected answer isn't reused"
    )


if __name__ == "__main__":
    {"composite": composite, "process": process, "exchange": exchange}[sys.argv[1]]()
