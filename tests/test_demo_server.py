"""The demo server's guards (examples/fennmoor-bank/server.py), and that every query the page opens with runs.

The guards need no service: what is refused before it is sent, what a command's argument list can and cannot be, and what never reaches the page. The queries run
against the example's graph (skipped when Neo4j is not up), in a read session, as the server runs them.
"""

from __future__ import annotations

import importlib.util
import math

import neo4j
import pytest
from conftest import EXAMPLE, ROOT

QUERIES = ROOT / "ui" / "src" / "examples" / "fennmoor" / "queries"


@pytest.fixture(scope="module")
def server():
    spec = importlib.util.spec_from_file_location("demo_server", EXAMPLE / "server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- what is refused before it is sent


@pytest.mark.parametrize(
    "query",
    [
        'CALL apoc.load.json("http://example.com") YIELD value RETURN value',
        "CALL apoc.cypher.runWrite('CREATE (n)', {}) YIELD value RETURN value",
        "CALL dbms.listConfig() YIELD name RETURN name",
        "CALL gds.graph.project('g', '*', '*')",
        "LOAD CSV FROM 'file:///x.csv' AS row RETURN row",
        "USE system SHOW USERS",
        "UNWIND range(1, 5) AS i CALL { CREATE (:X) } IN TRANSACTIONS RETURN i",
        "",
    ],
)
def test_refused_before_it_is_sent(server, query):
    with pytest.raises(server.Refused):
        server.check_cypher(query)


@pytest.mark.parametrize(
    "query",
    [
        "MATCH (n) RETURN n LIMIT 1",
        "// apoc.load.json is only a word here\nRETURN 1",
        "RETURN 'dbms.listConfig' AS text",
        "USE fennmoor.rows CALL db.schema.visualization()",
        "CALL db.index.vector.queryNodes('semantic_embedding', 3, [0.1]) YIELD node RETURN node",
        "RETURN apoc.create.vRelationship IS NULL AS ok",
    ],
)
def test_reads_are_not_refused(server, query):
    server.check_cypher(query)


def test_a_write_is_left_to_the_database(server):
    """No keyword list decides what is a write: the session is opened read-only, so the database refuses it whatever the text says."""
    source = (EXAMPLE / "server.py").read_text()
    assert "default_access_mode=neo4j.READ_ACCESS" in source
    server.check_cypher("CREATE (n:Probe) RETURN n")  # not caught here, and cannot run there


# ---- commands: a fixed list, as argument lists


def test_ask_is_an_argument_list(server):
    args = server.argv(
        {"command": "ask", "question": "How many calls?", "route": "cypher", "principal": "risk"}
    )
    assert args[-4:] == ["--run", "--as", "risk", "How many calls?"]
    assert "--cypher" in args and not any(
        a.startswith("-") and a not in ("--cypher", "--run", "--as", "-c") for a in args[3:]
    )


@pytest.mark.parametrize(
    "body",
    [
        {"command": "rm -rf /"},
        {"command": "ask", "question": ""},
        {"command": "ask", "question": "x", "route": "--help"},
        {"command": "ask", "question": "x", "principal": "root"},
        {"command": "recall", "label": "Customer", "key": "--full"},
        {"command": "recall", "label": "Customer; ls", "key": "1"},
        {"command": "exchange", "n": "9"},
    ],
)
def test_a_command_is_refused(server, body):
    with pytest.raises(server.Refused):
        server.argv(body)


def test_a_question_that_looks_like_a_flag_is_one_argument(server):
    args = server.argv({"command": "ask", "question": "--help; rm -rf /"})
    assert args[-1] == "--help; rm -rf /"
    assert args.count("--help; rm -rf /") == 1


# ---- what the page is shown


def test_the_project_and_service_accounts_never_reach_the_page(server):
    project = server.s["warehouse"]["project"]
    prefix = server.s["warehouse"]["dataset_prefix"]
    risk = server.s["entitlements"]["principals"]["risk"]
    text = server.logical(f"denied: {project}:{prefix}dw_core.dim_customer, as {risk}, in {project}")
    assert project not in text and prefix not in text and "gserviceaccount" not in text
    assert "dw_core.dim_customer" in text and "risk" in text


def test_values_are_plain(server):
    assert server.plain(math.nan) is None
    assert server.plain(list(range(100))) == "[100 values]"
    assert server.plain({"a": [1, 2]}) == {"a": [1, 2]}


# ---- every query the page opens with runs


LAYER = [
    p
    for d in ("discovery", "virtual")
    for p in sorted((QUERIES / d).glob("*.cypher"))
    if p.stem not in ("rows_schema", "customers_sample", "accounts_graph", "nodes", "pointers")
] + [QUERIES / "memory" / "holds_summary.cypher", QUERIES / "memory" / "holds.cypher"]


@pytest.mark.parametrize("path", LAYER, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_a_layer_query_runs_read_only(graph, server, path):
    server.check_cypher(path.read_text())
    params = {"key": "0"} if "$key" in path.read_text() else {}
    with graph.driver.session(database=graph.db, default_access_mode=neo4j.READ_ACCESS) as session:
        assert list(session.run(path.read_text(), params)), f"{path.name} returned nothing"


# ---- the agent traces' queries run on memory, which holds the example's conversations once `qlsc converse` has recorded them

TRACE = [
    QUERIES / "memory" / f"{n}.cypher"
    for n in ("trace_of_a_conversation", "trace_decision_evidence", "trace_who_read", "trace_summary")
]


@pytest.mark.parametrize("path", TRACE, ids=lambda p: p.name)
def test_a_trace_query_runs_read_only(server, path):
    from qlsc import memory

    server.check_cypher(path.read_text())
    with (
        memory.memory_graph(server.s) as M,
        M.driver.session(database=M.db, default_access_mode=neo4j.READ_ACCESS) as session,
    ):
        rows = list(session.run(path.read_text()))
    if not rows:
        pytest.skip(
            "memory holds no conversations: qlsc converse examples/fennmoor-bank/conversations/marketing-1.yaml records one"
        )


def test_a_refusal_by_the_warehouse_confirms_nothing(server):
    said = server.told(
        "BigQueryException during runQuery: Access Denied: Table dw_core.dim_customer: User does not have permission to query table dw_core.dim_customer, or perhaps it does not exist."
    )
    assert "dim_customer" not in said and "dw_core" not in said and "contact-center" not in said
    assert "does not exist or is not available" in said
    assert "no such property" in server.told("no such property: x")
