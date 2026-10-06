"""Context: what the warehouse held about a call's customer as of the call, and which of its rows the call's words are about.

A conversation's id is the key of a call in the virtual graph (`process.context.conversation`), and that call points at the customer
(`process.context.subject`), so a conversation reaches its customer without anything about the call being said twice. From there:

  as of the call   the customer's context is fetched from the virtual graph as memory fetches one (qlsc/memory.py), but with the facts'
                   window ending on the call's day and starting `memory.window_quarters` before it, not today's: what the warehouse
                   held then. It is read, never remembered: a context as of a past day would be stale the moment it was kept.
  tables beyond    a table the virtual graph's model does not serve (`process.context.also`: the estate names it) is read from the
  the model        warehouse for the same customer: its customer column is the one the semantic layer says holds the same Variable as the
                   subject's key, its date the table's partition column, the same window, the most recent `memory.cap` rows.
  links, by lookup what the turns say is matched to those rows, never extracted: a name against the rows' names (a merchant), an amount
                   against the rows' amounts, written as a person writes or says it ("$7.65", "seven sixty-five", "eleven dollars and six
                   cents"). The candidates are the customer's own rows as of the call, so a match is a row the call can be about and
                   the context shown is the context the call is about.

Nothing here reads an answer key; the evaluation (eval/process_context.py) scores the links against it.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from qlsc import memory
from qlsc.config import Settings
from qlsc.graph import Graph
from qlsc.process.source import Turn
from qlsc.warehouse import Warehouse

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
LAYER_COLUMNS = """
MATCH (t:Table) WHERE t.id ENDS WITH $table
MATCH (t)-[:HAS_COLUMN]->(c:Column)-[:IS]->(v:Variable)<-[:IS]-(k:Column)<-[:HAS_COLUMN]-(st:Table)
WHERE st.id = $subject_table AND k.name = $subject_column
RETURN t.id AS table, c.name AS column, t.partition_column AS date
"""


class ContextError(RuntimeError):
    pass


# ------------------------------------------------------------------------------------------------------------------- words


def words(n: int) -> str:
    """0 to 999 in words, as a person says an amount of dollars: 74 is "seventy-four", 117 is "one hundred seventeen"."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + (f"-{ONES[n % 10]}" if n % 10 else "")
    rest = f" {words(n % 100)}" if n % 100 else ""
    return f"{ONES[n // 100]} hundred{rest}"


def normal(text: str) -> str:
    """Lower case, hyphens as spaces, one space between words: "Seventy-Four  twelve" and "seventy four twelve" are the same."""
    return re.sub(r"\s+", " ", text.lower().replace("-", " ")).strip()


def forms(amount: float) -> list[str]:
    """The ways an amount of dollars is written or said, normalised: "$7.65", "7.65", "seven dollars and sixty-five cents",
    "seven sixty-five"; a whole amount also "$42" and "forty-two dollars"."""
    cents = round(amount * 100)
    d, c = divmod(cents, 100)
    out = [f"${d}.{c:02d}", f"{d}.{c:02d}"]
    if d >= 1000:
        return out
    leads = [words(d)] + ([f"a hundred {words(d % 100)}".strip()] if 100 <= d < 200 else [])
    for lead in leads:
        if c == 0:
            out += [f"${d}", f"{lead} dollars", f"{lead} dollars and no cents"]
        else:
            tail = f"oh {words(c)}" if c < 10 else words(c)
            out += [
                f"{lead} dollars and {words(c)} cent{'s' * (c != 1)}",
                f"{lead} {tail}",
                f"{lead} dollars {tail}",
            ]
    return [normal(x) for x in out]


NUMBER_WORDS = {w for w in ONES + TENS if w != "_"} | {"hundred"}


def present(form: str, text: str) -> bool:
    """The form stands alone in the text: "$42" is not in "$42.50", "7.65" not in "17.65", and "five fifty" not in "twenty five
    fifty" (a spoken amount is not the tail of a longer number)."""
    for m in re.finditer(rf"(?<![\w.$]){re.escape(form)}(?![\w]|\.\d)", text):
        before = text[: m.start()].split()
        if form[0].isalpha() and before and before[-1] in NUMBER_WORDS:
            continue
        return True
    return False


# ------------------------------------------------------------------------------------------------------------------ linking


@dataclass
class Link:
    kind: str  # name | amount
    label: str  # the node's label, or the table's name
    key: object
    evidence: str  # what in the text matched
    turn: int  # the first turn (its seq) at which it did
    row: dict = field(default_factory=dict)


def link(
    rules: list[dict], rows: dict[str, list[dict]], keys: dict[str, str], turns: list[Turn]
) -> list[Link]:
    """Match what the turns say to the rows. `rows`: per label or table, the customer's rows as of the call, most recent first, each
    carrying the properties of the rows it points at as `Label.property`; `keys`: each one's key column. A rule is
    {label | table, name: <column>} (the row's name is said), {..., amount: <column>} (its amount is said) or both (both are: a purchase's
    amount and its merchant's name pick one merchant out of several that share a name); `emit: Label` also links the row it points at.
    A name carried by more than one row is no link by itself: it cannot say which. The first turn a row matches at is kept; of rows
    with one amount, the most recent, which `rows` lists first."""
    out: dict[tuple[str, object], Link] = {}
    claimed: set[tuple[str, str]] = (
        set()
    )  # an amount said once is one row's: the first listed, which is the most recent
    texts = [(t, normal(t.text)) for t in turns]

    def hits(rule: dict, row: dict) -> tuple[Turn, str] | None:
        """The turn by which every condition of the rule has been met, and what matched."""
        evidence, last = [], None
        if "name" in rule:
            name = normal(str(row.get(rule["name"]) or ""))
            seen = next(
                (t for t, x in texts if name and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", x)), None
            )
            if seen is None:
                return None
            evidence.append(name)
            last = seen
        if "amount" in rule:
            amount = row.get(rule["amount"])
            if amount is None:
                return None
            forms_ = forms(float(amount))
            seen = next(((t, f) for t, x in texts for f in forms_ if present(f, x)), None)
            if seen is None:
                return None
            evidence.append(seen[1])
            last = seen[0] if last is None or seen[0].seq > last.seq else last
        return last, " + ".join(evidence)

    for rule in rules:
        what = rule.get("label") or rule["table"]
        candidates = rows.get(what, [])
        count: dict[str, int] = {}
        if "name" in rule and "amount" not in rule:
            for row in candidates:
                n = normal(str(row.get(rule["name"]) or ""))
                count[n] = count.get(n, 0) + 1
        for row in candidates:
            key = row[keys[what]]
            if count and count.get(normal(str(row.get(rule["name"]) or "")), 0) > 1:
                continue
            found = hits(rule, row)
            if found is None:
                continue
            turn, evidence = found
            kind = "amount" if "amount" in rule else "name"
            if "amount" in rule:
                token = (what, evidence)
                if token in claimed and (what, key) not in out:
                    continue
                claimed.add(token)
            first = out.get((what, key))
            if first is None or turn.seq < first.turn:
                out[(what, key)] = Link(kind, what, key, evidence, turn.seq, row)
            end = rule.get("emit")
            if end and row.get(f"{end}.{keys[end]}") is not None:
                prefix = f"{end}."
                end_row = {k[len(prefix) :]: v for k, v in row.items() if k.startswith(prefix)}
                ek = end_row[keys[end]]
                if (end, ek) not in out or turn.seq < out[(end, ek)].turn:
                    out[(end, ek)] = Link(kind, end, ek, evidence, turn.seq, end_row)
    return sorted(out.values(), key=lambda x: (x.turn, x.label, str(x.key)))


def neighbours(ctx) -> dict[str, list[dict]]:
    """The context's rows by label, each with the properties of the row it points at (a purchase's merchant) as `Label.property`."""
    pointed: dict[tuple[str, object], dict] = {}
    for _, start, skey, end, ekey in ctx.edges:
        end_row = ctx.nodes.get((end, ekey))
        if end_row and ekey is not None:
            pointed.setdefault((start, skey), {}).update({f"{end}.{k}": v for k, v in end_row.items()})
    out: dict[str, list[dict]] = {}
    for (label, key), row in ctx.nodes.items():
        out.setdefault(label, []).append({**row, **pointed.get((label, key), {})})
    return out


# ------------------------------------------------------------------------------------------------------------------ context


def literal(value) -> str:
    if isinstance(value, bool):
        raise ContextError("a boolean is no key")
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def date_of(value) -> dt.date:
    return (
        value
        if isinstance(value, dt.date) and not isinstance(value, dt.datetime)
        else dt.date.fromisoformat(str(value)[:10])
    )


def also(
    s: Settings, G: Graph, m: memory.Model, wh: Warehouse, table: str, subject_key, as_of: dt.date
) -> list[dict]:
    """A table beyond the virtual graph's model, for the subject: the rows of its own column that holds the subject's key (the semantic
    layer's Variable says which), dated in the window ending on `as_of`, most recent first, at most memory.cap."""
    subject = s["process"]["context"]["subject"]
    column = m.nodes[subject]["columns"][m.key(subject)]
    found = G.rows(LAYER_COLUMNS, table=table, subject_table=m.tables[subject]["id"], subject_column=column)
    if not found:
        raise ContextError(f"no column of {table} holds the same Variable as {subject}'s key {column}")
    t = found[0]
    if not t["date"]:
        raise ContextError(f"{t['table']} has no partition column to date its rows by")
    ident = memory.ident
    p = s["memory"]
    sql = (
        f"SELECT * FROM `{t['table']}` WHERE `{ident(t['column'])}` = {literal(subject_key)} "
        f"AND `{ident(t['date'])}` BETWEEN DATE '{memory.window_start(s, as_of)}' AND DATE '{as_of}' "
        f"ORDER BY `{ident(t['date'])}` DESC LIMIT {p['cap']}"
    )
    out = wh.run(sql, s["navigate"]["maximum_bytes_billed"], p["cap"])
    if not out.get("ok"):
        raise ContextError(f"{table}: {out.get('error')}")
    return out["rows"]


def at(
    s: Settings,
    conversation: str,
    turns: list[Turn],
    upto: int | None = None,
    as_of: dt.date | None = None,
    model: memory.Model | None = None,
) -> dict:
    """The context of a conversation as of its day (or `as_of`), and the links from its turns up to sequence `upto` (all by default)
    into it: {call, subject, as_of, nodes: {label: [row]}, also: {table: [row]}, links, seconds}."""
    import time

    from qlsc.warehouse import connect

    t0 = time.time()
    cfg = s["process"]["context"]
    m = model or memory.reader_model(s, None)
    call, subject = cfg["conversation"], cfg["subject"]
    rel = next((r for r in m.rels if r["start"] == call and r["end"] == subject), None)
    if rel is None:
        raise ContextError(f"no relationship from {call} to {subject} in the virtual graph")
    now = dt.datetime.now(dt.UTC)
    with memory.virtual_graph(s) as V, Graph(s) as G:
        first = memory.run_batch(s, m, [memory.Read(0, call)], [conversation], V, False, now)[conversation]
        row = first.nodes.get((call, conversation))
        if row is None:
            raise ContextError(f"the virtual graph has no {call} {conversation}")
        key = row[rel["fk"]]
        day = as_of or date_of(row[m.nodes[call]["partition"]])
        if (
            key is None
        ):  # a call nobody was identified on (an IVR hang-up, an unauthenticated caller): no customer, no context
            return {
                "conversation": conversation,
                "call": row,
                "subject": {"label": subject, "key": None},
                "as_of": day,
                "nodes": {},
                "also": {},
                "links": [],
                "reads": {},
                "seconds": round(time.time() - t0, 1),
            }
        ctx = memory.run_batch(
            s, m, memory.template(m, subject, s["memory"]["hops"]), [key], V, False, now, as_of=day
        )[key]
        wh = connect(s)
        extra = {t: also(s, G, m, wh, t, key, day) for t in cfg["also"]}
    nodes = neighbours(ctx)
    for label, rows in nodes.items():
        part = m.nodes[label]["partition"]
        if part:
            rows.sort(key=lambda r, part=part: str(r.get(part)), reverse=True)
    pool = {**nodes, **extra}
    keys = {label: m.key(label) for label in nodes} | {
        r["table"]: r["key"] for r in cfg["match"] if "table" in r
    }
    said = [t for t in turns if upto is None or t.seq <= upto]
    return {
        "conversation": conversation,
        "call": row,
        "subject": {"label": subject, "key": key},
        "as_of": day,
        "nodes": nodes,
        "also": extra,
        "links": link(cfg["match"], pool, keys, said),
        "reads": {x["read"]: x["rows"] for x in ctx.reads},
        "seconds": round(time.time() - t0, 1),
    }


# --------------------------------------------------------------------------------------------------------------------- show


def show(c: dict, turns: list[Turn], upto: int | None) -> str:
    if c["subject"]["key"] is None:
        return f"conversation {c['conversation']}: the call has no {c['subject']['label']}, so there is no context to fetch"
    n = len(c["nodes"].get(c["subject"]["label"], []))
    lines = [
        f"conversation {c['conversation']}: {c['subject']['label']} {c['subject']['key']}, as of {c['as_of']} "
        f"({c['seconds']} s; turns up to {upto if upto is not None else 'the last'})",
        "  the context, by what the warehouse held then: "
        + ", ".join(
            f"{len(v)} {k}" for k, v in sorted(c["nodes"].items()) if k != c["subject"]["label"] or n > 1
        )
        + (", " if c["also"] else "")
        + ", ".join(f"{len(v)} rows of {k}" for k, v in c["also"].items()),
    ]
    if not c["links"]:
        lines.append("  nothing the turns say matched a row")
    for x in c["links"]:
        shown = ", ".join(f"{k}={v}" for k, v in x.row.items() if v is not None and not isinstance(v, bool))
        lines.append(f"  turn {x.turn}: {x.label} {x.key} (by {x.kind}: '{x.evidence}')  {shown[:150]}")
    return "\n".join(lines)


def report(s: Settings, conversation: str, turn: int | None, as_of: str | None) -> None:
    """`qlsc process context CONVERSATION [--turn N] [--as-of DATE]`."""
    from qlsc.process import source

    src = source.read(s)
    turns = src.conversations.get(conversation)
    if turns is None:
        raise ContextError(f"{conversation} is not in {src.location}")
    c = at(s, conversation, turns, turn, dt.date.fromisoformat(as_of) if as_of else None)
    print(show(c, turns, turn))
