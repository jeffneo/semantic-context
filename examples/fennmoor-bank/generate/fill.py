#!/usr/bin/env python3
"""Fill the deployed Fennmoor estate with rows: generate the base tables, compute the rest in BigQuery.

Plan: plans/2026-09-26-fill-the-estate.md. Configuration: spec/data.yaml.

  generate  the slice's base tables -> build/data/<dataset>.<table>.ndjson.gz (seeded: the same spec
            gives the same rows)
  load      each file into its deployed table, replacing what is there (load jobs are free)
  compute   the slice's derived tables in dependency order: TRUNCATE, then INSERT the model's own SQL,
            with CURRENT_DATE() pinned to dates.as_of. Tables with `sql` in data.yaml join here, after
            the tables they read.
  check     row counts, unique keys, filled required columns, identifiers found at their home table
            -> build/data/FILL.md

Every value comes from the table specs (type, concept, flags, the value comments) and data.yaml;
nothing is read from qlsc's output.

Usage: uv run examples/fennmoor-bank/generate/fill.py --slice 1 [--steps generate,load,compute,check]
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import random
import re
import time
import uuid
import zlib
from collections import defaultdict
from pathlib import Path

import yaml
from deploy import levels, physical

from qlsc.warehouse.bigquery import client

EXAMPLE = Path(__file__).resolve().parents[1]
SPEC, BUILD = EXAMPLE / "spec", EXAMPLE / "build"
DATA = BUILD / "data"

FIRST = "James Mary Robert Patricia John Jennifer Michael Linda David Elizabeth William Barbara Richard Susan Joseph Jessica Thomas Sarah Carlos Maria Wei Mei Anh Minh Aisha Omar Priya Arjun Grace Ethan Olivia Noah Emma Liam Sofia Mateo Hannah Lucas Chloe".split()
LAST = "Smith Johnson Williams Brown Jones Garcia Miller Davis Rodriguez Martinez Hernandez Lopez Wilson Anderson Thomas Taylor Moore Jackson Martin Lee Nguyen Tran Patel Kim Clark Lewis Walker Hall Allen Young King Wright Scott Green Baker Adams Nelson Hill Ramirez Campbell".split()
STREETS = (
    "Elm Oak Maple Cedar Pine Birch Walnut Main Park Lake Hill River Sunset Prairie Redbud Willow".split()
)
CITIES = "Tulsa Oklahoma_City Norman Spokane Boise Wichita Topeka Omaha Lincoln Kansas_City Springfield Bartlesville Stillwater Lawton".split()
WINDOW_TYPES = {"DATE", "TIMESTAMP"}


def stable(*parts) -> int:
    return zlib.crc32("|".join(map(str, parts)).encode())


def hexof(*parts, n=24) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:n]


# ------------------------------------------------------------------- the spec


def comment_domains() -> dict[tuple[str, str, str], list[str]]:
    """Code values from the column comments in spec/warehouse/*.yaml: `A active, I inactive`,
    `PURCH REFUND CASH_ADV`, `'Y'/'N'`, `I=individual B=business`."""
    out = {}
    for f in sorted((SPEC / "warehouse").glob("*.yaml")):
        ds = tab = None
        for line in f.read_text().splitlines():
            if m := re.match(r"^dataset:\s*(\S+)", line):
                ds = m.group(1)
            elif m := re.match(r"^\s*- name:\s*(\S+)", line):
                tab = m.group(1)
            elif (m := re.match(r'^\s*- "([A-Za-z_0-9]+)\s*\|.*"\s*#\s*(.+)$', line)) and ds and tab:
                values = parse_comment(m.group(2))
                if values:
                    out[(ds, tab, m.group(1))] = values
    return out


def parse_comment(text: str) -> list[str] | None:
    quoted = re.findall(r"'([^']*)'", text)
    if quoted:
        return quoted
    token = re.compile(r"^[A-Za-z0-9_+\-]+$")
    if "=" in text and "," not in text:
        values = [part.split("=")[0] for part in text.split()]
    elif "," in text:
        values = [
            item.strip().split()[0] for item in text.split(",") if item.strip() and item.strip() != "..."
        ]
    else:
        values = text.split()
    values = [v for v in values if token.match(v) and v != "..."]
    return values if len(values) >= 2 and all(len(v) <= 24 for v in values) else None


def pick(rng: random.Random, domain):
    """A value from a list (uniform) or a {value: weight} map."""
    if isinstance(domain, dict):
        values, weights = list(domain), list(domain.values())
        return rng.choices(values, weights)[0]
    return rng.choice(domain)


def key_of(t: dict) -> str:
    return f"{t['dataset']}.{t['name']}"


# --------------------------------------------------------------- generation


class Estate:
    """The slice's base tables as rows, generated in two phases: first every table's row count,
    parents and keys (so identifiers exist before anything refers to them), then every other column."""

    def __init__(self, wh: dict, concepts: dict, cfg: dict, slice_tables: set[str]):
        self.cfg, self.concepts = cfg, concepts
        self.spec = {key_of(t): t for t in wh["tables"]}
        self.fqn = {key_of(t): t["fqn"] for t in wh["tables"]}
        # sharded tables (one table per day or month) wait for the slice that fills shards
        self.tables = sorted(
            k
            for k in slice_tables
            if self.spec[k]["kind"] == "base"
            and "sql" not in cfg["tables"].get(k, {})
            and not self.spec[k].get("shard")
        )
        self.comments = comment_domains()
        d = cfg["dates"]
        self.window = [dt.date.fromisoformat(str(x)) for x in d["window"]]
        self.history = dt.date.fromisoformat(str(d["history_start"]))
        self.as_of = dt.date.fromisoformat(str(d["as_of"]))
        self.rows: dict[str, list[dict]] = {}
        self.parent: dict[str, dict[str, list[int]]] = {}
        self.position: dict[str, list[int]] = {}  # a row's place among its main parent's rows
        self.population: dict[str, list] = {}
        self.pk_concept: dict[str, dict[str, str]] = {}

    # ---- phase 1: rows, parents, keys

    def tcfg(self, k: str) -> dict:
        return self.cfg["tables"].get(k, {})

    def order(self) -> list[str]:
        out, seen = [], set()

        def visit(k):
            if k in seen:
                return
            seen.add(k)
            for p in [*self.tcfg(k).get("parents", {}), *self.tcfg(k).get("needs", [])]:
                if p in self.tables:
                    visit(p)
            out.append(k)

        for k in self.tables:
            visit(k)
        return out

    def scaled(self, k: str) -> int:
        s, spec_rows = self.cfg["scale"], self.spec[k].get("rows") or 1000
        if spec_rows < s["reference_below"]:
            return spec_rows
        share = s["events"] if spec_rows >= s["event_threshold"] else s["entities"]
        return max(1, min(s["cap"], round(spec_rows * share)))

    def plan(self, k: str) -> None:
        rng = random.Random(stable(self.cfg["seed"], k, "plan"))
        c = self.tcfg(k)
        if c.get("fixed"):
            self.rows[k] = [dict(r) for r in c["fixed"]]
            self.parent[k], self.position[k] = {}, [0] * len(c["fixed"])
            return
        parents = [p for p in c.get("parents", {}) if p in self.rows]
        links, position = defaultdict(list), []
        main = parents[0] if parents else None
        mcfg = c.get("parents", {}).get(main, {}) if main else {}
        if main and c.get("daily"):
            days = (self.window[1] - self.window[0]).days + 1
            for i in range(len(self.rows[main])):
                for day in range(days):
                    links[main].append(i)
                    position.append(day)
        elif main and ("per" in mcfg or "share" in mcfg):
            for i in range(len(self.rows[main])):
                if "per" in mcfg:
                    count = rng.randint(*mcfg["per"])
                else:
                    count = 1 if rng.random() < mcfg["share"] else 0
                for j in range(count):
                    links[main].append(i)
                    position.append(j)
        else:
            n = c.get("rows") or self.domain_size(k) or self.scaled(k)
            position = [0] * n
            if main:
                links[main] = self.sample_parents(rng, main, n, mcfg.get("unique"))
        n = len(position)
        for p in parents[1:] if links else parents:
            if p not in links:
                links[p] = self.sample_parents(rng, p, n, c["parents"][p].get("unique"))
                if main in links:  # rows of one main parent get different rows of the others
                    seen = set()
                    for r in range(n):
                        for _ in range(20):
                            if (links[main][r], links[p][r]) not in seen:
                                break
                            links[p][r] = self.sample_parents(rng, p, 1)[0]
                        seen.add((links[main][r], links[p][r]))
        self.rows[k] = [{} for _ in range(n)]
        self.parent[k], self.position[k] = dict(links), position
        self.keys(k)

    def domain_size(self, k: str) -> int | None:
        for rule in self.tcfg(k).get("columns", {}).values():
            if rule.get("unique") and "from_domain" in rule:
                return len(self.cfg["domains"][rule["from_domain"]])
        return None

    def sample_parents(self, rng, p: str, n: int, unique: bool = False) -> list[int]:
        size = len(self.rows[p])
        if unique and size >= n:
            return rng.sample(range(size), n)
        return [min(size - 1, int(size * rng.random() ** 1.7)) for _ in range(n)]

    def keys(self, k: str) -> None:
        """The key and grain columns, and the populations of the id spaces this table is home to."""
        t = self.spec[k]
        grain = {g.strip() for g in (t.get("grain") or "").split(",")}
        self.pk_concept[k] = {}
        for col in t["columns"]:
            name, concept = col["name"], col.get("concept")
            is_pk = (col.get("flags") or {}).get("pk")
            if not (is_pk or name in grain):
                continue
            fn = self.column_fn(k, col)
            for i, row in enumerate(self.rows[k]):
                row[name] = fn(i, row)
            if is_pk and concept:
                self.pk_concept[k][concept] = name
                home = (self.concepts.get(concept) or {}).get("home", "")
                if home.rsplit(".", 1)[0] == k or concept not in self.population:
                    self.population[concept] = [r[name] for r in self.rows[k]]

    # ---- phase 2: every other column

    def fill(self, k: str) -> None:
        t = self.spec[k]
        done = set(self.rows[k][0]) if self.rows[k] else set()
        fns = {col["name"]: self.column_fn(k, col) for col in t["columns"] if col["name"] not in done}
        for i, row in enumerate(self.rows[k]):
            for name, fn in fns.items():
                if name not in row:
                    row[name] = fn(i, row)

    def column_fn(self, k: str, col: dict):
        """A function (row index, row) -> value for one column, from its rule in data.yaml, its
        concept, its flags and its type, compiled once per table."""
        name, flags = col["name"], col.get("flags") or {}
        rule = dict(self.tcfg(k).get("columns", {}).get(name, {}))
        rng = random.Random(stable(self.cfg["seed"], k, name))
        base = self.base_fn(k, col, rule, rng)
        required = flags.get("required") or flags.get("pk")
        share, unless = rule.get("share"), rule.get("null_unless")
        null_after = flags.get("null_after")
        get = self.getter(k)

        def fn(i, row):
            if null_after and self.as_of > dt.date.fromisoformat(str(null_after)):
                return None  # retired upstream: every current row is null (00_estate.yaml events)
            if unless and not all(get(i, row, c) in vals for c, vals in unless.items()):
                return None
            if share is not None and not required and rng.random() > share:
                return None
            return base(i, row)

        return fn

    def getter(self, k: str):
        """Read another column of the same row, computing it first if needed."""
        cols = {c["name"]: c for c in self.spec[k]["columns"]}
        cache: dict[str, object] = {}

        def get(i, row, name):
            if name not in row:
                if name not in cache:
                    cache[name] = self.column_fn(k, cols[name])
                row[name] = cache[name](i, row)
            return row[name]

        return get

    def parent_row(self, k: str, parent: str, i: int) -> dict | None:
        idx = self.parent[k].get(parent)
        return self.rows[parent][idx[i]] if idx else None

    def base_fn(self, k: str, col: dict, rule: dict, rng: random.Random):  # noqa: C901 - one rule per branch
        name, typ, concept = col["name"], col["type"], col.get("concept")
        flags = col.get("flags") or {}
        t, get = self.spec[k], self.getter(k)
        parents = (
            list(self.parent.get(k, {}))
            if k in self.parent
            else [p for p in self.tcfg(k).get("parents", {}) if p in self.rows]
        )
        pos = lambda i: self.position[k][i] if k in self.position and i < len(self.position[k]) else 0

        if self.tcfg(k).get("daily") and typ == "DATE" and name in (t.get("grain") or ""):
            return lambda i, row: str(self.window[0] + dt.timedelta(days=pos(i)))

        # explicit rules
        if "const" in rule:
            return lambda i, row: rule["const"]
        if "const_json" in rule:
            return lambda i, row: dict(rule["const_json"])
        if "same_as" in rule:
            return lambda i, row: get(i, row, rule["same_as"])
        if "from_parent" in rule:
            return lambda i, row: (self.parent_row(k, rule["from_parent"], i) or {}).get(rule["column"])
        if "first" in rule:
            first, then = rule["first"], rule["then"]
            return lambda i, row: (
                first if pos(i) == 0 else (pick(rng, then) if isinstance(then, (dict, list)) else then)
            )
        if "sequence" in rule:
            seq = rule["sequence"]
            return lambda i, row: seq[min(pos(i), len(seq) - 1)]
        if rule.get("seq_per_parent"):
            return lambda i, row: pos(i) + 1
        if "first_values" in rule:
            fv = rule["first_values"]
            return lambda i, row: fv[i] if i < len(fv) else rule["then_pattern"].format(n=i)
        if "from_domain" in rule:
            domain = self.cfg["domains"][rule["from_domain"]]
            if rule.get("unique"):
                values = list(domain)
                return lambda i, row: values[i]
            if "where_prefix" in rule:
                keep = [v for v in domain if v.split("-")[0] in rule["where_prefix"]]
                domain = {v: domain[v] for v in keep} if isinstance(domain, dict) else keep
            return lambda i, row: pick(rng, domain)
        if "choice" in rule or "words" in rule:
            domain = rule.get("choice", rule.get("words"))
            return lambda i, row: pick(rng, domain)
        if "bool" in rule:
            return lambda i, row: rng.random() < rule["bool"]
        if rule.get("self"):
            own = self.spec[k]["columns"][0]["name"]
            return lambda i, row: self.rows[k][int(len(self.rows[k]) * rng.random())][own]
        if "derive" in rule:
            return self.derive(k, name, rule, rng, get)
        if "after" in rule or "before" in rule:
            ref = rule.get("after") or rule.get("before")
            lo, hi = rule.get("days", [1, 3000] if "after" in rule else [0, 3])
            sign = 1 if "after" in rule else -1

            recent = rule.get("in_window", 0)

            def shifted(i, row):
                base = get(i, row, ref)
                if base is None:
                    return None
                if recent and rng.random() < recent:
                    a = max(self.window[0], self.as_date(base) + dt.timedelta(days=1))
                    return self.typed(
                        a + dt.timedelta(days=rng.randint(0, max(0, (self.window[1] - a).days))), typ, rng
                    )
                v = self.as_date(base) + dt.timedelta(days=sign * rng.randint(lo, hi))
                return self.typed(min(v, self.as_of), typ, rng)

            return shifted
        if "after_seconds" in rule:
            ref, (lo, hi) = rule["after_seconds"], rule["seconds"]
            of_parent = rule.get("of_parent")

            def later(i, row):
                src = self.parent_row(k, parents[0], i) if of_parent else row
                base = src.get(ref) if of_parent else get(i, row, ref)
                if base is None:
                    return None
                return self.ts(
                    dt.datetime.fromisoformat(base[:19]) + dt.timedelta(seconds=rng.randint(lo, hi))
                )

            return later
        if "pattern" in rule and set(re.findall(r"\{(\w+)", rule["pattern"])) <= {"n"}:
            start = rule.get("start", 1)
            return lambda i, row: rule["pattern"].format(n=start + i)
        if "pattern" in rule:
            return lambda i, row: rule["pattern"].format(
                n=i,
                **{
                    f: str(get(i, row, f) or "").replace("_", " ")
                    for f in re.findall(r"\{([A-Za-z_]+)\}", rule["pattern"])
                },
            )
        if "range" in rule:
            lo, hi = rule["range"]
            if isinstance(lo, (dt.date, str)):
                a, b = self.as_date(lo), self.as_date(hi)
                return lambda i, row: self.typed(
                    a + dt.timedelta(days=rng.randint(0, (b - a).days)), typ, rng
                )
            if isinstance(lo, int) and isinstance(hi, int) and typ == "INT64":
                return lambda i, row: rng.randint(lo, hi)
            return lambda i, row: self.number(rng.uniform(lo, hi), typ)
        if "in_window" in rule:
            share = rule["in_window"]
            business = rule.get("business_hours")
            return lambda i, row: self.when(rng, typ, rng.random() < share, business)

        # dates and times first: a `date.day` concept is a calendar, not an id space
        if concept == "date.day" or (typ in WINDOW_TYPES and self.partitioned_by(t, name)):
            return lambda i, row: self.when(rng, typ, True)
        if typ in WINDOW_TYPES:
            return self.type_fn(k, name, typ, flags, rng, get)

        # the column's identity: copied from a parent, sampled from its id space, or new
        if concept and parents:
            for p in parents:
                for pc in self.spec[p]["columns"]:
                    if pc.get("concept") == concept and (
                        concept.split(".")[0] in ("geo",) or self.is_identifier(concept)
                    ):
                        pname = pc["name"]
                        return lambda i, row, p=p, pname=pname: (self.parent_row(k, p, i) or {}).get(pname)
        if concept and self.is_identifier(concept):
            home = (self.concepts.get(concept) or {}).get("home", "")
            is_home = home == f"{k}.{name}" or (flags.get("pk") and concept not in self.population)
            fmt = self.cfg["formats"].get(concept)
            if not is_home and concept in self.population and self.population[concept]:
                pop = self.population[concept]
                return lambda i, row: pop[min(len(pop) - 1, int(len(pop) * rng.random() ** 1.7))]
            if fmt:
                return self.format_fn(k, name, fmt, rng, new=is_home)
            return lambda i, row: str(uuid.UUID(hexof(k, name, i, n=32)))
        if flags.get("pk") and typ == "STRING":
            return lambda i, row: str(uuid.UUID(hexof(k, name, i, n=32)))
        if flags.get("pk") and typ == "INT64":
            return lambda i, row: i + 1
        if concept == "geo.state":
            return lambda i, row: pick(rng, self.cfg["domains"]["states"])
        if concept == "geo.zip" and "geo.zip" in self.population:
            pop = self.population["geo.zip"]
            return lambda i, row: rng.choice(pop)
        if flags.get("pii") or (concept or "").startswith("pii."):
            return self.pii_fn(k, name, flags.get("pii") or concept.split(".")[1], rng, get)
        if concept and concept.startswith("money.") or flags.get("unit") in ("usd", "cents"):
            return self.money_fn(concept or "", flags.get("unit"), typ, rng)

        # the value comments, then data.yaml domains, then the type
        domain = self.cfg["domains"].get(f"{k}.{name}") or self.comments.get((t["dataset"], t["name"], name))
        if domain:
            return lambda i, row: pick(rng, domain)
        return self.type_fn(k, name, typ, flags, rng, get)

    # ---- value helpers

    def is_identifier(self, concept: str) -> bool:
        return (self.concepts.get(concept) or {}).get("kind") == "identifier" or concept in self.cfg[
            "formats"
        ]

    def partitioned_by(self, t: dict, name: str) -> bool:
        return bool(t.get("partition")) and re.sub(r"^DATE\((.*)\)$", r"\1", t["partition"]) == name

    def format_fn(self, k: str, name: str, fmt: dict, rng: random.Random, new: bool):
        if "choice" in fmt:
            return lambda i, row: rng.choice(fmt["choice"])
        if "from_domain" in fmt:
            return lambda i, row: pick(rng, self.cfg["domains"][fmt["from_domain"]])
        if fmt.get("uuid"):
            return (
                (lambda i, row: str(uuid.UUID(hexof(k, name, i, n=32))))
                if new
                else (lambda i, row: str(uuid.UUID(hexof(k, name, "orphan", rng.random(), n=32))))
            )
        start, step = fmt.get("start", 1), fmt.get("step", 1)
        if fmt.get("int"):
            return (
                (lambda i, row: start + i * step)
                if new
                else (lambda i, row: start + rng.randint(0, 10**6) * step)
            )
        pattern = fmt["pattern"]

        def value(i, row):
            n = start + (i * step if new else rng.randint(0, 10**6))
            h = hexof(k, name, i if new else rng.random(), n=32)
            return re.sub(r"\{h:(\d+)\}", lambda m: h[: int(m.group(1))], pattern).format(n=n)

        return value

    def derive(self, k: str, name: str, rule: dict, rng: random.Random, get):
        kind, of = rule["derive"], rule.get("of")
        if kind == "sha256_hex":
            return lambda i, row: hashlib.sha256(get(i, row, of).encode()).hexdigest()
        if kind == "prefix_before_dash":
            mapping = rule.get("map", {})
            return lambda i, row: mapping.get(get(i, row, of).split("-")[0], get(i, row, of).split("-")[0])
        if kind == "title":
            return lambda i, row: get(i, row, of).replace("-", " ").replace("_", " ").title()
        if kind == "queue_name":
            sites = {"TUL_": 38, "SPK_": 28, "MNL_": 34}
            functions = [
                "Retail_Service",
                "Card_Services",
                "Collections",
                "Fraud_Callbacks",
                "Overflow",
                "Account_Maintenance",
                "Digital_Support",
                "Spanish_Line",
                "Business_Banking",
            ]
            return lambda i, row: (
                f"{pick(rng, sites)}{functions[i % len(functions)]}"
                + (f"_{i // len(functions) + 1}" if i >= len(functions) else "")
            )
        if kind == "participant_attributes":
            cifs = self.population.get("customer.cif", [])
            intents = {"BALANCE": 30, "CARD": 20, "PAYMENT": 15, "FRAUD": 8, "ADDRESS": 7, "OTHER": 14}

            def attributes(i, row):
                if get(i, row, "purpose") != "customer":
                    return {}
                closure = self.is_closure(get(i, row, "conversation_id"))
                out = {
                    "ivr_auth": pick(rng, {"AUTH_OK": 80, "AUTH_FAIL": 8, "NONE": 12}),
                    "intent": "CLOSE_ACCOUNT" if closure else pick(rng, intents),
                }
                if cifs and rng.random() < 0.88:
                    out["cif"] = cifs[min(len(cifs) - 1, int(len(cifs) * rng.random() ** 1.7))]
                return out

            return attributes
        if kind == "wrapup_code":
            codes = {r["name"]: r["id"] for r in self.rows.get("genesys_cloud.wrapup_code", [])}
            others = [v for n_, v in codes.items() if n_ not in ("ACCT_CLOSE", "ACCT_MAINT")]
            switch = dt.date.fromisoformat(str(rule["switch_date"]))

            def wrapup(i, row):
                if get(i, row, "segment_type") != "wrapup":
                    return None
                if self.is_closure(get(i, row, "conversation_id")):
                    start = dt.datetime.fromisoformat(get(i, row, "segment_start")[:19]).date()
                    return codes["ACCT_CLOSE"] if start >= switch else codes["ACCT_MAINT"]
                return codes["ACCT_MAINT"] if rng.random() < 0.05 else rng.choice(others)

            return wrapup
        if kind == "household":
            fmt = self.cfg["formats"]["customer.sf_household_id"]["pattern"]
            return lambda i, row: re.sub(
                r"\{h:(\d+)\}", lambda m: hexof("household", i - (i % 3 == 2), n=int(m.group(1))), fmt
            )
        raise ValueError(f"{k}.{name}: unknown derive {kind!r}")

    def is_closure(self, conversation_id: str) -> bool:
        """Closure calls: the same 6% of conversations in the IVR intent and in the wrap-up code."""
        return stable("closure", conversation_id) % 1000 < 60

    def pii_fn(self, k: str, name: str, kind: str, rng: random.Random, get):
        low = name.lower()
        if kind == "name":
            if "frst" in low or "first" in low:
                return lambda i, row: rng.choice(FIRST)
            if "lst" in low or "last" in low:
                return lambda i, row: rng.choice(LAST)
            if "midl" in low or "middle" in low:
                return lambda i, row: rng.choice("ABCDEFGHJKLMNPRSTW")
            return lambda i, row: f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if kind in ("email",):
            return lambda i, row: f"{rng.choice(FIRST).lower()}.{rng.choice(LAST).lower()}{i}@example.com"
        if kind in ("phone",):
            return lambda i, row: f"555-01{rng.randint(0, 99):02d}"
        if kind == "phone_hash":
            return lambda i, row: hashlib.sha256(f"555-01{rng.randint(0, 99):02d}-{i}".encode()).hexdigest()
        if kind == "ssn":
            return lambda i, row: f"9{rng.randint(0, 99):02d}-{rng.randint(10, 99)}-{rng.randint(1000, 9999)}"
        if kind == "dob":
            return lambda i, row: str(dt.date(1940, 1, 1) + dt.timedelta(days=rng.randint(0, 24000)))
        if kind == "address":
            return lambda i, row: (
                f"{rng.randint(10, 9999)} {rng.choice(STREETS)} {rng.choice(['St', 'Ave', 'Dr', 'Ln'])}"
            )
        if kind == "account_number":
            return lambda i, row: f"{610000000000 + i:012d}"
        if kind == "email_or_phone":
            return lambda i, row: (
                f"{rng.choice(FIRST).lower()}.{rng.choice(LAST).lower()}{i}@example.com"
                if get(i, row, "CNTCT_TYP_CD") == "EML"
                else f"555-01{rng.randint(0, 99):02d}"
            )
        if kind == "free_text":
            return lambda i, row: "note " + hexof(k, name, i, n=6)
        return lambda i, row: f"{kind}-{i}"

    def money_fn(self, concept: str, unit: str | None, typ: str, rng: random.Random):
        shape = {
            "money.txn_amount": (3.6, 1.1),
            "money.balance": (8.0, 1.3),
            "money.credit_limit": (8.6, 0.7),
            "money.fee": (2.3, 0.6),
            "money.interest": (1.5, 1.0),
            "money.loan_principal": (10.4, 0.8),
            "money.revenue": (0.5, 0.8),
        }.get(concept, (4.0, 1.0))

        def amount(i, row):
            dollars = math.exp(rng.gauss(*shape))
            if unit == "cents" or typ == "INT64":
                return int(round(dollars * 100)) if unit == "cents" else int(round(dollars))
            return self.number(dollars, typ)

        return amount

    def type_fn(self, k: str, name: str, typ: str, flags: dict, rng: random.Random, get):
        low = name.lower()
        if low in ("_fivetran_deleted", "is_deleted"):
            return lambda i, row: False
        if low in ("_fivetran_synced", "_load_ts", "_uploaded_at", "system_modstamp"):
            return lambda i, row: self.ts(
                dt.datetime.combine(self.as_of, dt.time(3)) - dt.timedelta(minutes=rng.randint(0, 600))
            )
        if low == "_source_file":
            return lambda i, row: f"{k.split('.')[1]}_{self.as_of:%Y%m%d}.csv"
        if low == "_source_file_date":
            return lambda i, row: str(self.as_of)
        if low == "_uploaded_by":
            return lambda i, row: "reference-loader"
        if low == "datastream_metadata":
            return lambda i, row: {
                "uuid": str(uuid.UUID(hexof(k, "ds", i, n=32))),
                "source_timestamp": int(dt.datetime.combine(self.as_of, dt.time(2)).timestamp() * 1000),
            }
        if typ == "BOOL":
            return lambda i, row: rng.random() < 0.15
        if typ == "STRING" and "city" in low:
            return lambda i, row: rng.choice(CITIES).replace("_", " ")
        if typ == "STRING" and (low.endswith("_flg") or low.endswith("_flag")):
            return lambda i, row: "Y" if rng.random() < 0.2 else "N"
        if typ == "STRING":
            return lambda i, row: f"{low}_{rng.randint(1, 12)}"
        if typ == "INT64":
            hi = 600000 if low.endswith("_ms") else 3600 if low.endswith("_sec") else 100
            return lambda i, row: rng.randint(0, hi)
        if typ in ("NUMERIC", "FLOAT64", "BIGNUMERIC"):
            hi = 10 if flags.get("unit") == "pct" else 1000
            return lambda i, row: self.number(rng.uniform(0, hi), typ)
        if typ in WINDOW_TYPES:
            recent = any(s in low for s in ("upd", "modified", "updated", "last_"))
            return lambda i, row: self.when(rng, typ, recent and rng.random() < 0.5)
        if typ == "JSON":
            return lambda i, row: {}
        if typ.startswith("ARRAY"):
            return lambda i, row: []
        return lambda i, row: None

    def as_date(self, v) -> dt.date:
        if isinstance(v, dt.date):
            return v
        return dt.date.fromisoformat(str(v)[:10])

    def ts(self, v: dt.datetime) -> str:
        return v.strftime("%Y-%m-%d %H:%M:%S+00:00")

    def typed(self, d: dt.date, typ: str, rng: random.Random):
        if typ == "TIMESTAMP":
            return self.ts(
                dt.datetime.combine(d, dt.time(rng.randint(6, 21), rng.randint(0, 59), rng.randint(0, 59)))
            )
        return str(d)

    def when(self, rng: random.Random, typ: str, in_window: bool, business: bool = False):
        a, b = self.window if in_window else (self.history, self.window[0] - dt.timedelta(days=1))
        day = a + dt.timedelta(days=rng.randint(0, (b - a).days))
        if in_window and day.weekday() >= 5 and rng.random() < 0.6:  # quieter weekends
            day -= dt.timedelta(days=day.weekday() - 4)
        if typ == "TIMESTAMP":
            hour = rng.randint(13, 23) if business else rng.randint(0, 23)  # 8:00-18:00 Chicago, in UTC
            return self.ts(dt.datetime.combine(day, dt.time(hour, rng.randint(0, 59), rng.randint(0, 59))))
        return str(day)

    def number(self, v: float, typ: str):
        return round(v, 6) if typ == "FLOAT64" else f"{v:.2f}"

    # ---- run

    def generate(self) -> dict[str, int]:
        t0 = time.time()
        order = self.order()
        for k in order:
            self.plan(k)
        for k in order:
            self.fill(k)
            print(f"  {k:52} {len(self.rows[k]):>10,} rows  ({time.time() - t0:.0f}s)", flush=True)
        return {k: len(v) for k, v in self.rows.items()}

    def write(self) -> None:
        DATA.mkdir(parents=True, exist_ok=True)
        for k, rows in self.rows.items():
            cols = [c["name"] for c in self.spec[k]["columns"]]
            with gzip.GzipFile(DATA / f"{k}.ndjson.gz", "wb", mtime=0) as f:
                for r in rows:
                    f.write(
                        (
                            json.dumps({c: r.get(c) for c in cols}, separators=(",", ":"), default=str) + "\n"
                        ).encode()
                    )


# ------------------------------------------------------------------ BigQuery


def closure(spec: dict, targets: list[str]) -> set[str]:
    """Every table a set of target tables reads, directly or not (by column lineage and sources)."""
    by_fqn = {t["fqn"]: key_of(t) for t in spec.values()}
    by_name = {t["name"]: key_of(t) for t in spec.values()}
    seen, stack = set(), [by_name[n] for n in targets]
    while stack:
        k = stack.pop()
        if k in seen:
            continue
        seen.add(k)
        t = spec[k]
        ups = {lin.rsplit(".", 1)[0] for c in t["columns"] for lin in c.get("lineage") or []} | set(
            t.get("sources") or []
        )
        stack += [by_fqn[u] for u in ups if u in by_fqn and by_fqn[u] != k]
    return seen


def deployed(t: dict, project: str, prefix: str) -> str:
    return f"{project}.{prefix}{t['dataset']}.{t['name']}"


def load(bq, spec: dict, keys: list[str], project: str, prefix: str) -> None:
    from google.cloud import bigquery

    for k in keys:
        table = deployed(spec[k], project, prefix)
        schema = bq.get_table(table).schema
        config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition="WRITE_TRUNCATE",
            schema=schema,
        )
        with open(DATA / f"{k}.ndjson.gz", "rb") as f:
            job = bq.load_table_from_file(f, table, job_config=config)
        job.result()
        print(f"  loaded {k:52} {job.output_rows:>10,} rows")


def compute(bq, spec: dict, cfg: dict, keys: set[str], project: str, prefix: str) -> None:
    as_of = str(cfg["dates"]["as_of"])
    derived = []
    for k in keys:
        t, extra = spec[k], cfg["tables"].get(k, {})
        if "sql" in extra:
            derived.append({**t, "sql": extra["sql"], "sources": extra.get("depends_on", [])})
        elif t.get("sql") and t.get("materialized") != "view":
            derived.append(t)
    for level in levels(derived):
        for t in level:
            cols = ", ".join(f"`{c['name']}`" for c in t["columns"])
            sql = physical(t["sql"], project, prefix)
            sql = sql.replace("CURRENT_DATE()", f"DATE '{as_of}'").replace(
                "CURRENT_TIMESTAMP()", f"TIMESTAMP '{as_of} 23:00:00+00'"
            )
            target = deployed(t, project, prefix)
            job = bq.query(
                f"TRUNCATE TABLE `{target}`;\nINSERT INTO `{target}` ({cols})\nSELECT {cols} FROM (\n{sql}\n)"
            )
            job.result()
            n = next(iter(bq.query(f"SELECT COUNT(*) FROM `{target}`").result()))[0]
            print(
                f"  computed {key_of(t):50} {n:>10,} rows  ({(job.total_bytes_billed or 0) / 2**20:,.0f} MiB billed)"
            )


def check(
    bq, spec: dict, concepts: dict, keys: set[str], expected: dict, project: str, prefix: str
) -> list[str]:
    L = [
        "# Fill check",
        "",
        "| table | rows | expected | key unique | required filled |",
        "|---|---|---|---|---|",
    ]
    problems = []
    for k in sorted(keys):
        t = spec[k]
        if t.get("materialized") == "view" or t.get("shard"):
            continue
        target = deployed(t, project, prefix)
        grain = [g.strip() for g in (t.get("grain") or "").split(",") if g.strip()]
        required = [c["name"] for c in t["columns"] if (c.get("flags") or {}).get("required")]
        key = f"TO_JSON_STRING(STRUCT({', '.join(f'`{g}`' for g in grain)}))" if grain else "1"
        nulls = " + ".join(f"COUNTIF(`{c}` IS NULL)" for c in required) or "0"
        n, distinct, missing = next(
            iter(bq.query(f"SELECT COUNT(*), COUNT(DISTINCT {key}), {nulls} FROM `{target}`").result())
        )
        exp = expected.get(k, "")
        unique = distinct == n if grain else True
        L.append(
            f"| {k} | {n:,} | {exp if exp == '' else f'{exp:,}'} | {'yes' if unique else f'no ({n - distinct:,} dup)'} | "
            f"{'yes' if not missing else f'no ({missing:,} null)'} |"
        )
        if n == 0 or not unique or missing:
            problems.append(
                f"{k}: {n} rows, {n - distinct} duplicate keys, {missing} nulls in required columns"
            )
    # identifiers found at their home table
    L += ["", "## Identifiers found at their home table", "", "| column | home | found |", "|---|---|---|"]
    for k in sorted(keys):
        t = spec[k]
        if t.get("materialized") == "view":
            continue
        for c in [] if t.get("shard") else t["columns"]:
            home = (concepts.get(c.get("concept") or "") or {}).get("home", "")
            if not home or home.rsplit(".", 1)[0] == k:
                continue
            hk, hc = home.rsplit(".", 1)
            if (
                hk not in keys
                or spec[hk].get("materialized") == "view"
                or t.get("shard")
                or spec[hk].get("shard")
                or c["type"].startswith(("ARRAY", "STRUCT"))
            ):
                continue
            share = next(
                iter(
                    bq.query(f"""
                SELECT SAFE_DIVIDE(COUNTIF(h.v IS NOT NULL), COUNT(*)) FROM `{deployed(t, project, prefix)}` x
                LEFT JOIN (SELECT DISTINCT `{hc}` AS v FROM `{deployed(spec[hk], project, prefix)}`) h ON h.v = x.`{c["name"]}`
                WHERE x.`{c["name"]}` IS NOT NULL""").result()
                )
            )[0]
            if share is not None:
                L.append(f"| {k}.{c['name']} | {home} | {share:.0%} |")
    (DATA / "FILL.md").write_text("\n".join(L) + "\n")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slice", type=int, default=1)
    ap.add_argument("--steps", default="generate,load,compute,check")
    a = ap.parse_args()
    steps = set(a.steps.split(","))
    cfg = yaml.safe_load((SPEC / "data.yaml").read_text())
    concepts = yaml.safe_load((SPEC / "concepts.yaml").read_text())["concepts"]
    wh = json.loads((BUILD / "warehouse.json").read_text())
    spec = {key_of(t): t for t in wh["tables"]}
    keys = closure(spec, cfg["slices"][a.slice]["targets"])
    est = Estate(wh, concepts, cfg, keys)
    print(
        f"slice {a.slice} ({cfg['slices'][a.slice]['title']}): {len(keys)} tables, "
        f"{len(est.tables)} generated here, the rest computed in BigQuery"
    )
    expected = {}
    if "generate" in steps:
        expected = est.generate()
        est.write()
        (DATA / "expected_rows.json").write_text(json.dumps(expected, indent=1))
    elif (DATA / "expected_rows.json").exists():
        expected = json.loads((DATA / "expected_rows.json").read_text())
    if steps & {"load", "compute", "check"}:
        w = yaml.safe_load((EXAMPLE / "estate.yaml").read_text())["warehouse"]
        bq = client(w["project"], w["gcloud_config"], w["location"])
        project, prefix = w["project"], w["dataset_prefix"]
        if "load" in steps:
            load(bq, spec, est.tables, project, prefix)
        if "compute" in steps:
            compute(bq, spec, cfg, keys, project, prefix)
        if "check" in steps:
            problems = check(bq, spec, concepts, keys, expected, project, prefix)
            print(
                f"-> {DATA / 'FILL.md'}" + ("" if not problems else "\nproblems:\n  " + "\n  ".join(problems))
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
