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


PRESETS = {
    "cypher": {
        "layer": ["MATCH (n) RETURN count(n)"],
        "memory": ["MATCH (c:Customer {cif_number: $customer}) RETURN count(c)"],
    },
    "sql": ["SELECT 1"],
    "ask": [
        {"question": "How many calls?", "route": "cypher"},
        {"question": "How many calls? Later.", "route": "auto"},
        {"question": "--help; rm -rf /", "route": "auto"},
    ],
    "recall": [{"entity": "Customer", "key": "cif_number=*"}],
    "exchange": ["0"],
}


def load(name: str, env: dict, tmp_path):
    """The server as a process with this environment would load it, and a presets file of its own."""
    import json

    presets = tmp_path / f"{name}-presets.json"
    presets.write_text(json.dumps(PRESETS))
    mp = pytest.MonkeyPatch()
    mp.setenv("QLSC_DEMO_PRESETS", str(presets))
    for k, v in env.items():
        mp.setenv(k, v)
    spec = importlib.util.spec_from_file_location(name, EXAMPLE / "server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    mp.undo()
    return module


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    return load("demo_server", {}, tmp_path_factory.mktemp("local"))


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


# ---- the page's own examples, and nothing else


@pytest.fixture
def pool(server, monkeypatch):
    """The customers a memory example may use: a short pool, so no warehouse is asked."""
    monkeypatch.setattr(server, "_customers", ["0001", "0002", "0003"])
    return server._customers


def test_only_the_presets_run(server, pool):
    for body in (
        {"target": "layer", "query": "MATCH (n) RETURN n LIMIT 5"},
        {"target": "memory", "query": "MATCH (n) RETURN count(n)"},  # a preset, but of another target
    ):
        with pytest.raises(server.Refused, match="page's own examples"):
            server.cypher(body)
    with pytest.raises(server.Refused, match="page's own examples"):
        server.sql({"query": "SELECT 2"})
    server.argv({"command": "ask", "question": "How many calls?", "route": "cypher"})
    server.argv(
        {"command": "ask", "question": "How many calls? Later."}
    )  # no route is auto, as the page sends it
    server.argv({"command": "recall", "label": "Customer", "key": "cif_number=0001"})
    server.argv({"command": "exchange", "n": "0"})
    for body in (
        {"command": "ask", "question": "How many calls? Or fewer?", "route": "auto"},
        {"command": "ask", "question": "How many calls?", "route": "sql"},
        {"command": "recall", "label": "Customer", "key": "cif_number=9999"},  # not a customer of the pool
        {"command": "recall", "label": "Customer", "key": "segment=retail"},
        {"command": "remember", "label": "Customer", "key": "cif_number=0001"},
        {"command": "exchange", "n": "1"},
        {"command": "composite"},
    ):
        with pytest.raises(server.Refused, match="page's own examples"):
            server.argv(body)


def test_a_customer_is_one_of_the_pool(server, pool):
    assert server.customer_of({}) is None
    assert server.customer_of({"customer": "0002"}) == "0002"
    with pytest.raises(server.Refused):
        server.customer_of({"customer": "0001 OR 1=1"})


def test_a_customer_is_chosen_who_is_not_remembered(server, pool, monkeypatch):
    class Fake:
        def __init__(self, rows):
            self.rows_ = rows

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def rows(self, query, **params):
            return self.rows_

    monkeypatch.setattr(server.memory, "memory_graph", lambda s: Fake([{"k": "0001"}, {"k": "0002"}]))
    assert {server.pick()["customer"] for _ in range(20)} == {"0003"}  # the only one memory does not hold
    monkeypatch.setattr(server.memory, "memory_graph", lambda s: Fake([{"k": c} for c in pool]))
    assert server.pick()["customer"] in pool  # all are remembered: one of them again, not none


def test_a_command_waits_for_a_free_place_and_then_is_refused(server, monkeypatch):
    """Visitors beyond the limit wait, and are told; they are refused only if no place frees in time."""
    import threading

    slot = threading.BoundedSemaphore(1)
    slot.acquire()
    monkeypatch.setattr(server, "_busy", slot)
    monkeypatch.setattr(server, "QUEUE_SECONDS", 0.2)
    events = []
    with pytest.raises(server.Refused, match="Too many"):
        server.stream({"command": "ask", "question": "How many calls?", "route": "cypher"}, events.append)
    assert events and "waiting" in events[0]["line"]


def test_commands_at_once_is_a_setting_not_a_rule(tmp_path):
    module = load("demo_server_slots", {"QLSC_DEMO_COMMANDS_AT_ONCE": "7"}, tmp_path)
    assert module.METHODS_AT_ONCE == 7


# ---- hosted: the page itself is served from here


@pytest.fixture(scope="module")
def hosted(tmp_path_factory):
    import json
    import threading
    import urllib.request
    from http.server import ThreadingHTTPServer

    site = tmp_path_factory.mktemp("dist")
    (site / "assets").mkdir()
    (site / "index.html").write_text("<html>the page</html>")
    (site / "assets" / "app-1.js").write_text("console.log(1)")
    (site / "presets.json").write_text(json.dumps(PRESETS))
    module = load(
        "demo_server_hosted",
        {
            "QLSC_DEMO_HOSTED": "1",
            "QLSC_DEMO_STATIC": str(site),
            "QLSC_DEMO_PRESETS": str(site / "presets.json"),
        },
        site,
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield module, f"http://127.0.0.1:{httpd.server_port}", urllib.request
    httpd.shutdown()


def asked(hosted, path, body=None, origin=None):
    import json
    import urllib.error

    _, base, request = hosted
    headers = {"Content-Type": "application/json"} | ({"Origin": origin} if origin else {})
    req = request.Request(
        base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers
    )
    try:
        with request.urlopen(req) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def test_hosted_serves_the_page_and_its_routes(hosted):
    status, headers, body = asked(hosted, "/")
    assert status == 200 and b"the page" in body
    assert b"the page" in asked(hosted, "/examples/fennmoor")[2]  # a route of the app is not a file
    status, headers, body = asked(hosted, "/assets/app-1.js")
    assert body == b"console.log(1)" and "immutable" in headers["Cache-Control"]
    assert asked(hosted, "/healthz")[0] == 200


def test_hosted_serves_nothing_outside_the_page(hosted):
    assert b"the page" in asked(hosted, "/../../../../etc/passwd")[2]
    assert b"the page" in asked(hosted, "/%2e%2e/%2e%2e/etc/passwd")[2]
    assert (
        b"cypher" not in asked(hosted, "/presets.json")[2]
    )  # the list of what may run is the server's, not a page's file
    assert asked(hosted, "/api/nothing")[0] == 404


def test_hosted_answers_only_its_own_page(hosted):
    _, base, _ = hosted
    host = base.removeprefix("http://")
    body = {"target": "layer", "query": "MATCH (n) RETURN n LIMIT 5"}
    assert asked(hosted, "/api/cypher", body, origin="https://elsewhere.example")[0] == 403
    status, _, text = asked(
        hosted, "/api/cypher", body, origin=f"http://{host}"
    )  # its own origin: past the door, refused as not a preset
    assert status == 400 and b"page's own examples" in text


def test_no_access_code_is_asked_for(hosted):
    """The page opens and runs: nothing but its presets stands between a visitor and an example."""
    body = {"target": "layer", "query": PRESETS["cypher"]["layer"][0] + "\n"}
    status, _, _ = asked(hosted, "/api/cypher", body)
    assert status != 401
