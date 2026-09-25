#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "sqlglot[c]>=30", "google-cloud-bigquery>=3.25"]
# ///
"""Simulate INFORMATION_SCHEMA.JOBS for the Fennmoor estate over the log window.

Inputs:  build/warehouse.json, build/templates.json, specs/simulation.yaml
Outputs: build/log/jobs.ndjson.gz        rows in the exact JOBS column shape
         build/log/jobs_truth.ndjson.gz  ground truth per job_id (never in the log)
         build/log/SIMULATION.md         distributions and planted-finding checks

Two passes. First every principal gets a timeline of events (schedules for
service accounts; sessions for people; dashboard views and explore sessions
for Looker). Then events execute in time order, because several behaviours
depend on history: BigQuery's 24h result cache (invalidated by writes to a
referenced table), Looker's own cache, dbt invocation ids shared by a run,
and typos that are followed by their fix.

Semantics taken from real JOBS rows in the project (see chat history):
views never appear in referenced_tables - their base tables do; wildcard
queries reference `events_*`; cache hits have empty referenced_tables and no
query hash; SELECT results go to an anonymous `_<40 hex>` dataset.

Usage: uv run specs/tools/simulate.py [--days N] [--scale X] [--validate N] [--load]
"""
from __future__ import annotations

import argparse
import bisect
import functools
import datetime as dt
import gzip
import hashlib
import json
import math
import random
import re
import sys
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import sqlglot
import yaml
from sqlglot import exp

sys.path.insert(0, str(Path(__file__).resolve().parent))
import templates as tpl  # noqa: E402

SPECS = Path(__file__).resolve().parent.parent
BUILD = SPECS / "build"
OUT = BUILD / "log"
UTC = dt.timezone.utc


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def parse_hhmm(s: str) -> dt.time:
    h, m = map(int, s.split(":"))
    return dt.time(h, m)


def every_minutes(s: str) -> int:
    n, unit = int(s[:-1]), s[-1]
    return n * (60 if unit == "h" else 1)


def cron_field(field: str, lo: int, hi: int) -> set[int]:
    out = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, step = part.split("/")
            step = int(step)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = map(int, part.split("-"))
        else:
            a = b = int(part)
        out |= set(range(a, b + 1, step))
    return out


def cron_times(expr: str, day: dt.date) -> list[dt.time]:
    mi, hr, dom, mon, dow = expr.split()
    if day.day not in cron_field(dom, 1, 31) or day.month not in cron_field(mon, 1, 12):
        return []
    if (day.isoweekday() % 7) not in cron_field(dow, 0, 6):
        return []
    return [dt.time(h, m) for h in sorted(cron_field(hr, 0, 23)) for m in sorted(cron_field(mi, 0, 59))]


TYPE_BYTES = {"INT64": 8, "FLOAT64": 8, "NUMERIC": 16, "BIGNUMERIC": 32, "BOOL": 1, "DATE": 8, "DATETIME": 8,
              "TIMESTAMP": 8, "TIME": 8, "GEOGRAPHY": 40, "JSON": 180, "BYTES": 60, "INTERVAL": 16}
LONG_TEXT = re.compile(r"(desc|description|subject|note|verbatim|narrative|body|url|user_agent|page_|properties|reason_codes)", re.I)


def col_bytes(c: dict) -> int:
    t, n = c["type"], c["name"]
    if t.startswith("ARRAY") or t.startswith("STRUCT"):
        return {"event_params": 450, "user_properties": 120, "device": 80, "geo": 60}.get(n, 60)
    if t == "STRING":
        if LONG_TEXT.search(n):
            return 90
        if re.search(r"(id|ID|Id|token|number|code|_cd|_CD|NO|NBR)$", n):
            return 14
        return 12 if not re.search(r"(name|email|phone|address)", n, re.I) else 18
    return TYPE_BYTES.get(t, 8)


NONDET = re.compile(r"\b(CURRENT_DATE|CURRENT_TIMESTAMP|CURRENT_DATETIME|RAND|SESSION_USER|GENERATE_UUID|TABLESAMPLE)\b", re.I)
LITERALS = re.compile(r"'(?:[^'\\]|\\.)*'|\b\d+(?:\.\d+)?\b")
KEYWORDS = set("select from where group order by having limit join left right inner outer on and or not null is in as case when then else end with distinct union all over partition qualify between like cast date timestamp interval day month week year true false exists merge into using update set insert values delete create replace table view options count sum avg min max countif coalesce safe_divide current_date extract format_date".split())


@functools.lru_cache(maxsize=None)
def normalized_hash(sql: str) -> str:
    """Mimic JOBS query_info.query_hashes.normalized_literals.

    Probed against real BigQuery: the hash ignores literals (typed ones too, and a
    whole array literal counts as one), comments, whitespace and keyword case, but an
    IN list of a different length hashes differently. So: parse, drop comments,
    replace each literal (or all-literal array) with a placeholder, re-render.
    """
    def lit(n):
        return isinstance(n, exp.Literal) or (isinstance(n, exp.Neg) and isinstance(n.this, exp.Literal))

    def norm(n):
        n.comments = None
        if isinstance(n, exp.Array) and n.expressions and all(lit(e) for e in n.expressions):
            return exp.Placeholder()
        return exp.Placeholder() if lit(n) else n

    try:
        parts = [t.transform(norm).sql(dialect="bigquery") for t in sqlglot.parse(sql, read="bigquery") if t]
    except Exception:
        parts = [re.sub(r"\s+", " ", LITERALS.sub("?", sql)).strip().lower()]
    return hashlib.sha256(";".join(parts).encode()).hexdigest()


def stable_hash(*parts) -> int:
    """Process-independent hash (the built-in hash() of a str is salted per process)."""
    return int.from_bytes(hashlib.blake2b(repr(parts).encode(), digest_size=8).digest(), "big")


# ----------------------------------------------------------------------------
# Simulator
# ----------------------------------------------------------------------------

class Sim:
    def __init__(self, cfg: dict, wh: dict, records: list[dict], estate: dict, days: int | None, scale: float):
        self.cfg, self.wh, self.estate = cfg, wh, estate
        self.tz = ZoneInfo(cfg["timezone"])
        self.start = dt.date.fromisoformat(str(wh["log_window"]["start"]))
        self.days = days or wh["log_window"]["days"]
        self.end = self.start + dt.timedelta(days=self.days - 1)
        self.scale = scale
        self.holidays = {dt.date.fromisoformat(str(d)) for d in cfg.get("holidays", [])}
        self.T = {t["fqn"]: t for t in wh["tables"]}
        self.est = tpl.Estate(wh)
        self.rng = random.Random(cfg["seed"])
        self.by_id: dict[str, list[dict]] = defaultdict(list)
        for r in records:
            self.by_id[r["id"]].append(r)
        self.member_team = self.est.member_team
        self.sa = estate["service_accounts"]
        self.rows = self.estimate_rows()
        self.view_names = self.view_partition_names()
        self.shape_info: dict[tuple, dict] = {}
        self.writers_until = self.table_writer_windows(records)

    # ---- estate facts ------------------------------------------------------
    def is_view(self, fqn: str) -> bool:
        t = self.T[fqn]
        return t.get("materialized") == "view" or t["kind"] == "staging"

    def base_tables(self, fqn: str, seen=None) -> set[str]:
        if not self.is_view(fqn):
            return {fqn}
        seen = seen or set()
        out = set()
        for s in self.T[fqn].get("sources", []):
            if s in self.T and s not in seen:
                seen.add(s)
                out |= self.base_tables(s, seen)
        return out

    def estimate_rows(self) -> dict[str, int]:
        rows, pending = {}, list(self.T)
        for _ in range(20):
            nxt = []
            for f in pending:
                t = self.T[f]
                srcs = [s for s in t.get("sources", []) if s in self.T]
                if t.get("rows"):
                    rows[f] = int(t["rows"])
                    continue
                if any(s not in rows for s in srcs):
                    nxt.append(f)
                    continue
                m = max((rows[s] for s in srcs), default=1000)
                sql = t.get("sql", "")
                if t["kind"] == "copy":
                    rows[f] = int(m * (0.3 if "WHERE" in sql else 1))
                elif "GROUP BY" in sql and t["kind"] != "staging":
                    rows[f] = max(50, m // 300)
                else:
                    rows[f] = m
            pending = nxt
            if not pending:
                break
        for f in pending:
            rows[f] = 1000
        return rows

    def view_partition_names(self) -> dict[str, dict[str, list[str]]]:
        """view -> base table -> view columns that pass the base partition column through unchanged."""
        out = {}
        for f, t in self.T.items():
            if not self.is_view(f):
                continue
            m = defaultdict(list)
            for c in t["columns"]:
                expr_ = c.get("expr", "")
                if not re.fullmatch(r"\w+\.\w+", expr_ or "") or len(c.get("lineage", [])) != 1:
                    continue
                leaf = c["lineage"][0]
                bfqn, _, bcol = leaf.rpartition(".")
                bt = self.T.get(bfqn)
                if bt and bt.get("partition"):
                    pcol = re.sub(r"DATE\((\w+)\)", r"\1", bt["partition"])
                    if pcol.lower() == bcol.lower():
                        m[bfqn].append(c["name"])
            out[f] = dict(m)
        return out

    def table_writer_windows(self, records) -> dict[str, str | None]:
        """table -> last date any writer is active (None = whole window)."""
        out = {}
        for r in records:
            for w in r.get("tables_written", []):
                prev = out.get(w, "unset")
                u = r.get("active_until")
                out[w] = None if (u is None or prev is None) else max(u, prev) if prev != "unset" else u
        return out

    # ---- shape analysis ----------------------------------------------------
    def analyze(self, rec: dict) -> dict:
        key = (rec["id"], rec["variant"])
        if key in self.shape_info:
            return self.shape_info[key]
        info = {"scan": {}, "names": {}, "joins": 0, "window": False, "group": False, "nondet": False,
                "reads_bases": set(), "writes": set(rec.get("tables_written", []))}
        if rec["job_type"] != "QUERY":
            self.shape_info[key] = info
            return info
        sample = tpl.render(rec["sql"], rec["params"], random.Random(0), self.start + dt.timedelta(days=45))
        up = sample.upper()
        info["joins"] = up.count(" JOIN ")
        info["window"] = " OVER (" in up or " OVER(" in up
        info["group"] = "GROUP BY" in up
        info["nondet"] = bool(NONDET.search(sample))
        reads = [r for r in rec["tables_read"] if r in self.T]
        used: dict[str, set | None] = {f: set() for f in reads}
        try:
            stmts = [s for s in sqlglot.parse(sample, read="bigquery") if s]
        except Exception:
            stmts = []
        alias = {}
        for s in stmts:
            for tbl in s.find_all(exp.Table):
                f = self.est.logical(tbl.catalog, tbl.db, tbl.name, rec["job_project"]) if tbl.db else None
                if f in used:
                    alias[tbl.alias_or_name] = f
            for star in s.find_all(exp.Star):
                if not isinstance(star.parent, exp.Count):
                    q = star.parent.table if isinstance(star.parent, exp.Column) else None
                    for f in ([alias[q]] if q in alias else reads):
                        used[f] = None
            for c in s.find_all(exp.Column):
                parts = [x for x in (c.catalog, c.db, c.table) if x] + [c.name]
                if len(parts) >= 2 and parts[0] in alias:
                    f, root = alias[parts[0]], parts[1]
                    if used[f] is not None:
                        used[f].add(root.lower())
                else:
                    root = parts[0].lower()
                    for f in reads:
                        if used[f] is not None and any(cc["name"].lower() == root for cc in self.T[f]["columns"]):
                            used[f].add(root)
        if not stmts:
            used = {f: None for f in reads}
        # expand views to base tables, mapping used view columns to base columns
        scan: dict[str, set | None] = {}
        for f, cols in used.items():
            for b in self.base_tables(f):
                info["reads_bases"].add(b)
                if f == b:
                    base_cols = cols
                else:
                    base_cols = None if cols is None else {
                        leaf.rpartition(".")[2].lower()
                        for c in self.T[f]["columns"] if c["name"].lower() in cols
                        for leaf in c.get("lineage", []) if leaf.rpartition(".")[0] == b}
                prev = scan.get(b, set())
                scan[b] = None if (prev is None or base_cols is None) else prev | base_cols
                names = info["names"].setdefault(b, set())
                bt = self.T[b]
                if bt.get("partition"):
                    if f == b:
                        names.add(re.sub(r"DATE\((\w+)\)", r"\1", bt["partition"]))
                    else:
                        names |= set(self.view_names.get(f, {}).get(b, []))
        info["scan"] = scan
        self.shape_info[key] = info
        return info

    def shards_available(self, t: dict, run: dt.date) -> list[str]:
        sfx = tpl.shard_suffixes if hasattr(tpl, "shard_suffixes") else None
        sh = t["shard"]
        start, to = str(sh["from"]), (run - dt.timedelta(days=1)).isoformat() if sh["to"] == "log_end" else str(sh["to"])
        if sh["suffix"] == "YYYYMMDD":
            d0, d1 = dt.date.fromisoformat(start), dt.date.fromisoformat(to)
            return [(d0 + dt.timedelta(days=i)).strftime("%Y%m%d") for i in range(max(0, (d1 - d0).days + 1))]
        y, m = map(int, start.split("-"))
        ey, em = map(int, to.split("-")[:2])
        out = []
        while (y, m) <= (ey, em):
            out.append(f"{y}{m:02d}")
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return out

    def scan_bytes(self, info: dict, sql: str, run: dt.date) -> tuple[int, int, bool]:
        """(bytes, partitions_touched, pruned_everywhere)."""
        total, parts, pruned_all = 0, 0, True
        hist = self.cfg["cost"]["history_days_default"]
        for b, cols in info["scan"].items():
            t = self.T[b]
            width = sum(col_bytes(c) for c in t["columns"] if cols is None or c["name"].lower() in cols)
            if width == 0:
                continue
            rows = self.rows.get(b, 1000)
            if t.get("shard"):
                avail = self.shards_available(t, run)
                m = re.search(r"_TABLE_SUFFIX\s*(=|BETWEEN|>=)\s*'(\d{6,8})'(?:\s*AND\s*'(\d{6,8})')?", sql, re.I)
                if re.search(r"_TABLE_SUFFIX\s*=\s*FORMAT_DATE", sql, re.I):
                    n = 1
                elif m and m.group(1) == "=":
                    n = 1
                elif m and m.group(1).upper() == "BETWEEN" and m.group(3):
                    n = sum(1 for s in avail if m.group(2) <= s <= m.group(3))
                elif m:
                    n = sum(1 for s in avail if s >= m.group(2))
                else:
                    n, pruned_all = len(avail), False
                total += rows * max(n, 0) * width
                parts += n
                continue
            frac = 1.0
            if t.get("partition"):
                frac = None
                for name in info["names"].get(b, ()):
                    m = re.search(rf"\b{re.escape(name)}\b\)?\s*(>=|<=|=|>|<|BETWEEN)\s*(.{{0,120}})", sql, re.I | re.S)
                    if not m:
                        continue
                    op, rest = m.group(1).upper(), m.group(2)
                    dates = [dt.date.fromisoformat(d) for d in re.findall(r"\d{4}-\d{2}-\d{2}", rest)]
                    iv = re.search(r"INTERVAL\s+(\d+)\s+DAY", rest, re.I)
                    if op == "=":
                        days = 1
                    elif op == "BETWEEN" and len(dates) >= 2:
                        days = abs((dates[1] - dates[0]).days) + 1
                    elif op in (">=", ">") and dates:
                        days = max(1, (run - dates[0]).days + 1)
                    elif op in (">=", ">") and iv:
                        days = int(iv.group(1)) + 1
                    else:
                        continue
                    frac = min(1.0, days / hist)
                    parts += days
                    break
                if frac is None:
                    frac, pruned_all = 1.0, False
                    parts += hist
            total += int(rows * frac * width)
        return int(total), parts, pruned_all

    # ---- event generation --------------------------------------------------
    def local_dt(self, day: dt.date, t: dt.time, jitter_s: float = 0) -> dt.datetime:
        base = dt.datetime.combine(day, t, tzinfo=self.tz) + dt.timedelta(seconds=jitter_s)
        return base.astimezone(UTC)

    def workday(self, d: dt.date) -> bool:
        return d.weekday() < 5 and d not in self.holidays

    def active(self, rec: dict, d: dt.date) -> bool:
        if rec.get("active_from") and d < dt.date.fromisoformat(rec["active_from"]):
            return False
        if rec.get("active_until") and d > dt.date.fromisoformat(rec["active_until"]):
            return False
        return True

    def dates(self):
        return [self.start + dt.timedelta(days=i) for i in range(self.days)]

    def principal_for(self, rec: dict, member: str | None = None) -> dict:
        if rec["principal_kind"] == "service_account":
            sa = self.sa[rec["principal"]]
            return {"email": sa["email"], "kind": "serviceAccount", "member": None, "team": None,
                    "tool": rec["principal"]}
        m = member or (rec["members"][0] if rec["members"] else self.rng.choice(self.wh["teams"][rec["principal"]]["members"]))
        team = self.member_team[m]
        return {"email": f"{m}@{self.cfg['human_email_domain']}", "kind": "user", "member": m, "team": team,
                "tool": None}

    def gen_scheduled(self, events: list):
        ov = self.cfg.get("schedule_overrides", {})
        dbt_cfg = self.cfg["dbt"]
        # dbt DAG levels for the nightly run
        dbt_models = {r["tables_written"][0]: r for rs in self.by_id.values() for r in rs
                      if r["family"] == "dbt_build" and r["tables_written"]}
        level = {}

        def lvl(f):
            if f in level:
                return level[f]
            level[f] = 0
            srcs = [s for s in self.T[f].get("sources", []) if s in dbt_models]
            level[f] = 1 + max((lvl(s) for s in srcs), default=-1)
            return level[f]
        for f in dbt_models:
            lvl(f)
        for tid, recs in self.by_id.items():
            rec = recs[0]
            fam = rec["family"]
            if fam in ("human", "looker_query") or (fam == "tableau" and rec["schedule"].get("cadence") == "dashboard"):
                continue
            sched = dict(rec["schedule"])
            if fam in ov:
                sched = dict(ov[fam])
            for d in self.dates():
                if not self.active(rec, d):
                    continue
                times: list[dt.datetime] = []
                if "once" in sched:
                    if d.isoformat() == str(sched["once"]):
                        times.append(self.local_dt(d, dt.time(10, 30), self.rng.uniform(0, 5400)))
                elif "cadence" in sched:
                    times += self.cadence_times(tid, sched["cadence"], d)
                elif fam == "dbt_build" and sched.get("cron", "").endswith("2 * * *") and sched["cron"].startswith("0 "):
                    f = rec["tables_written"][0]
                    idx = sorted(f2 for f2 in dbt_models if level[f2] == level[f]).index(f)
                    off = level[f] * dbt_cfg["seconds_per_level"] + (idx // dbt_cfg["threads"]) * 25
                    times.append(self.local_dt(d, parse_hhmm(dbt_cfg["nightly_start"]), off + self.rng.uniform(0, 20)))
                elif "cron" in sched:
                    for t in cron_times(sched["cron"], d):
                        j = self.rng.uniform(0, 90) + (40 if ".insert." in tid else 0)
                        times.append(self.local_dt(d, t, j))
                elif "every" in sched:
                    step = every_minutes(sched["every"])
                    w0, w1 = (parse_hhmm(x) for x in sched.get("window", ["00:00", "23:59"]))
                    phase = stable_hash(tid) % step
                    for k in range(0, 24 * 60, step):
                        minute = (k + phase) % (24 * 60)
                        t = dt.time(minute // 60, minute % 60)
                        if sched.get("window") and not (w0 <= t <= w1):
                            continue
                        if "window" in sched:
                            t = dt.time(w0.hour, w0.minute)
                            span = (w1.hour * 60 + w1.minute) - (w0.hour * 60 + w0.minute)
                            times.append(self.local_dt(d, t, self.rng.uniform(0, span * 60)))
                            break
                        times.append(self.local_dt(d, t, self.rng.uniform(0, 30)))
                if fam == "ingest_merge":
                    rows = self.rows.get(rec["tables_written"][0], 0)
                    cp = self.cfg["fivetran"]["change_probability"]
                    p = cp["small"] if rows < 1e5 else cp["medium"] if rows < 1e7 else cp["large"]
                    times = [t for t in times if self.rng.random() < p]
                if fam == "looker_pdt":
                    srcs = self.T[rec["tables_written"][0]].get("sources", [])
                    stop = [self.writers_until.get(b) for s in srcs for b in self.base_tables(s)]
                    if any(u and d > dt.date.fromisoformat(u) + dt.timedelta(days=1) for u in stop):
                        times = []   # datagroup trigger never changes - no rebuild
                for t in times:
                    v = self.rng.choice(recs)
                    member = None
                    if rec["principal_kind"] == "human":
                        member = self.rng.choice(rec["members"]) if rec["members"] else None
                    events.append({"t": t, "rec": v, "who": self.principal_for(v, member), "why": "schedule"})

    def cadence_times(self, tid: str, cadence: str, d: dt.date) -> list[dt.datetime]:
        h = int(hashlib.md5(tid.encode()).hexdigest(), 16)
        if cadence == "daily":           # scheduled query under the owner's credentials
            return [self.local_dt(d, dt.time(6, 30), self.rng.uniform(0, 300))] if d.weekday() < 5 else []
        if not self.workday(d):
            return []
        if cadence == "weekly" and d.weekday() == h % 5:
            return [self.local_dt(d, dt.time(9 + h % 3, 0), self.rng.uniform(0, 3600))]
        if cadence == "monthly":
            bdays = [x for x in (d.replace(day=i) for i in range(1, 11)) if self.workday(x)]
            if len(bdays) >= 3 and d == bdays[2]:
                return [self.local_dt(d, dt.time(9, 30), self.rng.uniform(0, 5400))]
        return []

    def gen_humans(self, events: list):
        hc = self.cfg["humans"]
        people = {m: team for team, t in self.wh["teams"].items() for m in t["members"]}
        pool = defaultdict(list)          # team -> adhoc template ids
        scheduled = []
        for tid, recs in self.by_id.items():
            r = recs[0]
            if r["family"] != "human":
                continue
            if r["schedule"].get("cadence", "adhoc") != "adhoc":
                scheduled.append(tid)
            else:
                pool[r["principal"]].append(tid)
        for tid in scheduled:             # recurring human queries: owner, fixed cadence
            recs = self.by_id[tid]
            r = recs[0]
            owners = r["members"] or self.wh["teams"][r["principal"]]["members"][:1]
            for d in self.dates():
                if self.active(r, d):
                    for t in self.cadence_times(tid, r["schedule"]["cadence"], d):
                        events.append({"t": t, "rec": self.rng.choice(recs), "why": "recurring",
                                       "who": self.principal_for(r, self.rng.choice(owners))})
        for m, team in people.items():
            prng = random.Random(f"{self.cfg['seed']}:{m}")
            mean = hc["queries_per_day"][team] * math.exp(prng.gauss(0, hc["person_sigma"])) * self.scale
            aff = {}
            for tid in pool[team]:
                r = self.by_id[tid][0]
                if r["members"] and m not in r["members"]:
                    continue
                w = r["schedule"].get("weight", 1) * math.exp(prng.gauss(0, hc["affinity_sigma"]))
                if m in r["members"]:
                    w *= hc["own_template_boost"]
                aff[tid] = w
            if not aff:
                continue
            shift = prng.uniform(-45, 45)
            w0, w1 = (parse_hhmm(x) for x in hc["workday"])
            day_minutes = (w1.hour * 60 + w1.minute) - (w0.hour * 60 + w0.minute)
            tool_list = self.wh["teams"][team]["tools"]
            for d in self.dates():
                if not self.workday(d) or prng.random() < hc["pto_rate"]:
                    continue
                live = {t: w for t, w in aff.items() if self.active(self.by_id[t][0], d)}
                if not live:
                    continue
                budget = self.poisson(prng, mean)
                while budget > 0:
                    start_min = prng.uniform(0, day_minutes)
                    if 240 <= start_min <= 300 and prng.random() < 0.6:     # lunch
                        continue
                    t = self.local_dt(d, w0, shift * 60 + start_min * 60)
                    tool = tool_list[0] if prng.random() < 0.7 else prng.choice(tool_list)
                    budget -= self.session(events, prng, m, team, t, live, tool, budget)

    @staticmethod
    def poisson(rng, lam):
        if lam > 30:
            return max(0, int(rng.gauss(lam, math.sqrt(lam))))
        L, k, p = math.exp(-lam), 0, 1.0
        while True:
            p *= rng.random()
            if p <= L:
                return k
            k += 1

    def session(self, events, prng, m, team, t, live, tool, budget) -> int:
        hc = self.cfg["humans"]
        step = hc["session"]["next_step"]
        sid = f"s-{uuid.UUID(int=prng.getrandbits(128)).hex[:12]}"
        ids, weights = list(live), list(live.values())
        tid = prng.choices(ids, weights)[0]
        variant = prng.choice(self.by_id[tid])
        n = min(budget, 1 + int(prng.expovariate(1 / max(hc["session"]["queries_mean"] - 1, 0.5))), 15)
        seed = prng.getrandbits(32)
        who = {"email": f"{m}@{self.cfg['human_email_domain']}", "kind": "user", "member": m, "team": team, "tool": tool}
        for i in range(n):
            events.append({"t": t, "rec": variant, "who": who, "why": "adhoc", "session": sid, "seed": seed})
            t += dt.timedelta(seconds=prng.lognormvariate(math.log(hc["session"]["gap_median_sec"]), 0.8))
            x = prng.random()
            if x < step["rerun_same_text"]:
                continue
            x -= step["rerun_same_text"]
            if x < step["retweak_params"]:
                seed = prng.getrandbits(32)
                continue
            x -= step["retweak_params"]
            if x < step["switch_shape"]:
                variant, seed = prng.choice(self.by_id[tid]), prng.getrandbits(32)
                continue
            x -= step["switch_shape"]
            tables = set(variant["tables_read"])
            related = [i2 for i2 in ids if i2 != tid and tables & set(self.by_id[i2][0]["tables_read"])]
            cand = related if (related and x < step["related_template"]) else ids
            tid = prng.choices(cand, [live[c] for c in cand])[0]
            variant, seed = prng.choice(self.by_id[tid]), prng.getrandbits(32)
        return n

    def gen_looker(self, events: list):
        lc = self.cfg["looker"]
        tiles, explores = defaultdict(list), defaultdict(list)
        for tid, recs in self.by_id.items():
            r = recs[0]
            if r["family"] != "looker_query":
                continue
            name = tid.split(".")[2]
            (tiles if ".tile." in tid else explores)[name].append(recs[0])
        analyst_ids = {}
        for m in self.member_team:
            analyst_ids[m] = 40 + int(hashlib.md5(m.encode()).hexdigest(), 16) % 80

        def looker_user(prng, users):
            if users and prng.random() < lc["analyst_share"]:
                m = prng.choice(users)
                return analyst_ids[m], m
            return 121 + prng.randrange(lc["business_users"]), None
        prng = random.Random(f"{self.cfg['seed']}:looker")
        for d in self.dates():
            f = 1.0 if d.weekday() < 5 else lc["weekend_factor"]
            if d in self.holidays:
                f = lc["weekend_factor"]
            for name, recs in tiles.items():
                for _ in range(self.poisson(prng, lc["dashboard_views_per_day"].get(name, 5) * f * self.scale)):
                    t = self.local_dt(d, dt.time(7, 30), prng.uniform(0, 11 * 3600))
                    uid, m = looker_user(prng, recs[0]["members"])
                    for k, r in enumerate(recs):
                        events.append({"t": t + dt.timedelta(milliseconds=150 * k), "rec": r, "why": "dashboard",
                                       "who": self.principal_for(r), "looker_user": uid, "looker_member": m})
            for name, recs in explores.items():
                for _ in range(self.poisson(prng, lc["explore_queries_per_day"].get(name, 2) * f * self.scale)):
                    t = self.local_dt(d, dt.time(8, 0), prng.uniform(0, 10 * 3600))
                    uid, m = looker_user(prng, recs[0]["members"])
                    for _k in range(1 + int(prng.expovariate(0.7))):
                        r = prng.choice(recs)
                        events.append({"t": t, "rec": r, "why": "explore", "who": self.principal_for(r),
                                       "looker_user": uid, "looker_member": m})
                        t += dt.timedelta(seconds=prng.uniform(15, 180))
        # Tableau live connections
        live = [recs[0] for recs in self.by_id.values()
                if recs[0]["family"] == "tableau" and recs[0]["schedule"].get("cadence") == "dashboard"]
        for d in self.dates():
            if not self.workday(d):
                continue
            for _ in range(self.poisson(prng, self.cfg["tableau"]["live_queries_per_day"] * self.scale)):
                r = prng.choices(live, [x["schedule"].get("weight", 1) for x in live])[0]
                events.append({"t": self.local_dt(d, dt.time(8, 0), prng.uniform(0, 9 * 3600)), "rec": r,
                               "why": "dashboard", "who": self.principal_for(r)})

    # ---- execution ---------------------------------------------------------
    def run(self):
        events: list[dict] = []
        self.gen_scheduled(events)
        self.gen_humans(events)
        self.gen_looker(events)
        events.sort(key=lambda e: e["t"])
        return self.execute(events)

    def execute(self, events):
        hc = self.cfg["humans"]
        cost = self.cfg["cost"]
        pn = self.cfg["project_numbers"]
        last_write: dict[str, dt.datetime] = {}
        bq_cache: dict[tuple, tuple] = {}
        looker_cache: dict[str, dt.datetime] = {}
        dbt_invocation: dict[str, str] = {}
        rows, truth = [], []
        erng = random.Random(f"{self.cfg['seed']}:exec")
        restricted_targets = [f for f, t in self.T.items() if self.wh["datasets"][t["dataset"]].get("restricted")
                              and t["kind"] == "base" and t.get("status", "active") == "active"]
        for e in events:
            rec, who = e["rec"], e["who"]
            local = e["t"].astimezone(self.tz)
            run_date = local.date()
            prng = random.Random(e.get("seed", erng.getrandbits(32)))
            params = dict(rec.get("params", {}))
            sql = ""
            if rec["job_type"] == "QUERY":
                try:
                    sql = tpl.render(rec["sql"], params, prng, run_date)
                except Exception:
                    continue
                if e.get("looker_user") is not None:
                    ctx = {"user_id": e["looker_user"], "history_slug": uuid.UUID(int=erng.getrandbits(128)).hex[:13],
                           "instance_slug": "7e3f0c2b9a4d4f1e8c6b5a0d3e2f1a9b"}
                    sql = re.sub(r"-- Looker Query Context '[^\n]*'",
                                 "-- Looker Query Context '" + json.dumps(ctx, separators=(",", ":")) + "'", sql, count=1)
                    key = re.sub(r"-- Looker Query Context '[^\n]*'\n", "", sql)
                    if key in looker_cache and (e["t"] - looker_cache[key]).total_seconds() < self.cfg["looker"]["cache_minutes"] * 60:
                        continue     # served from Looker's cache: no BigQuery job
                    looker_cache[key] = e["t"]
                if who["kind"] == "user" and e["why"] == "adhoc" and erng.random() < hc["comment_noise"]:
                    note = erng.choice(["-- check", "-- for deck", "-- TODO clean up", "-- v2", "-- ask marcus", "-- temp"])
                    sql = f"{note}\n{sql}"
            if rec["family"] == "dbt_build" or rec["family"] == "dbt_test":
                inv_key = f"{run_date}:{'hourly' if rec['schedule'].get('every') else 'nightly'}:{local.hour if rec['schedule'].get('every') else ''}"
                inv = dbt_invocation.setdefault(inv_key, str(uuid.UUID(int=erng.getrandbits(128))))
                sql = sql.replace("{{invocation}}", inv)
            # --- injected human errors: emitted before the real job --------
            if who["kind"] == "user" and e["why"] == "adhoc" and rec["job_type"] == "QUERY":
                if erng.random() < hc["errors"]["access_denied"]:
                    team = who["team"]
                    denied = [f for f in restricted_targets if not tpl.team_can_read(self.est, team, self.T[f]["dataset"])]
                    if denied:
                        f = erng.choice(denied)
                        p, ds, tb = f.split(".")
                        bad = f"SELECT * FROM `{f}` LIMIT 100"
                        msg = (f"Access Denied: Table {p}:{ds}.{tb}: User does not have permission to query table "
                               f"{p}:{ds}.{tb}, or perhaps it does not exist.")
                        rows.append(self.job_row(e, who, rec, bad, pn, error=("accessDenied", msg), attempted=f))
                        truth.append(self.truth_row(rows[-1], e, rec, injected="access_denied", attempted=f))
                if erng.random() < hc["errors"]["typo"]:
                    bad, msg = self.typo(sql, erng)
                    if bad:
                        t_fix = e["t"]
                        e = {**e, "t": e["t"] - dt.timedelta(seconds=erng.uniform(20, 120))}
                        rows.append(self.job_row(e, who, rec, bad, pn, error=("invalidQuery", msg)))
                        truth.append(self.truth_row(rows[-1], e, rec, injected="typo"))
                        e = {**e, "t": t_fix}
            info = self.analyze(rec)
            nbytes, parts, pruned = self.scan_bytes(info, sql, run_date) if rec["job_type"] == "QUERY" else (0, 0, True)
            if rec.get("statement_type") == "CREATE_VIEW":
                nbytes = 0
            # --- cache ------------------------------------------------------
            cache_hit = False
            ckey = (who["email"], sql)
            if (rec.get("statement_type") == "SELECT" and not info["nondet"] and ckey in bq_cache):
                prev_end, bases = bq_cache[ckey]
                if (e["t"] - prev_end).total_seconds() < 86400 and all(last_write.get(b, dt.datetime.min.replace(tzinfo=UTC)) < prev_end for b in bases):
                    cache_hit = True
            error = None
            if (not cache_hit and who["kind"] == "user" and not pruned and nbytes > 5e11
                    and erng.random() < hc["errors"]["resources_exceeded_full_scan"]):
                error = ("resourcesExceeded", "Resources exceeded during query execution: Your project or organization "
                         "exceeded the maximum disk and memory limit available for shuffle operations. Consider "
                         "provisioning more slots, reducing query concurrency, or using more efficient logic in this job.")
            if rec["family"] == "dbt_build" and erng.random() < self.cfg["dbt"]["failure_rate"]:
                error = ("resourcesExceeded", "Resources exceeded during query execution: The query could not be "
                         "executed in the allotted memory.")
            row = self.job_row(e, who, rec, sql, pn, nbytes=nbytes, parts=parts, info=info, cache_hit=cache_hit,
                               error=error)
            rows.append(row)
            truth.append(self.truth_row(row, e, rec))
            end = dt.datetime.fromisoformat(row["end_time"])
            if not error:
                if rec.get("statement_type") == "SELECT" and not cache_hit:
                    bq_cache[ckey] = (end, info["reads_bases"])
                for w in rec.get("tables_written", []):
                    if rec.get("statement_type") != "CREATE_VIEW":
                        last_write[w] = end
        return rows, truth

    def typo(self, sql: str, rng) -> tuple[str | None, str | None]:
        cands = [m for m in re.finditer(r"\b([a-z][a-z0-9_]{5,})\b", sql)
                 if m.group(1) not in KEYWORDS and "." not in sql[max(0, m.start() - 1):m.start()]
                 and not sql[max(0, m.start() - 1):m.start()] in ("`", "'")]
        if not cands:
            return None, None
        m = rng.choice(cands)
        w = m.group(1)
        i = rng.randrange(1, len(w) - 1)
        bad = w[:i] + w[i + 1:]
        line = sql[:m.start()].count("\n") + 1
        col = m.start() - (sql.rfind("\n", 0, m.start()) + 1) + 1
        return (sql[:m.start()] + bad + sql[m.end():],
                f"Unrecognized name: {bad}; Did you mean {w}? at [{line}:{col}]")

    def job_row(self, e, who, rec, sql, pn, nbytes=0, parts=0, info=None, cache_hit=False, error=None,
                attempted=None) -> dict:
        rng = random.Random(stable_hash(e["t"].timestamp(), who["email"], sql[:50]))
        created = e["t"]
        is_query = rec["job_type"] == "QUERY" and sql
        project = rec["job_project"]
        # job id by client
        if who["kind"] == "user" and who.get("tool") == "bigquery_console":
            job_id = f"bquxjob_{rng.getrandbits(32):08x}_{rng.getrandbits(44):011x}"
        elif rec["family"] == "legacy_dag":
            job_id = (f"airflow_edw_nightly_balances_{rec['id'].split('.')[1]}_{created.strftime('%Y%m%dT%H%M%S')}"
                      f"_{rng.getrandbits(32):08x}")
        else:
            job_id = str(uuid.UUID(int=rng.getrandbits(128), version=4))
        stmt = None if rec["job_type"] == "LOAD" else ("SELECT" if attempted else rec.get("statement_type"))
        # timing
        contention = 4.0 if 2 <= created.astimezone(self.tz).hour < 4 else 1.0
        queue_ms = rng.uniform(15, 300) * contention
        if error and error[0] in ("invalidQuery", "accessDenied"):
            slot, exec_ms, nbytes = None, rng.uniform(40, 250), None
        elif cache_hit:
            slot, exec_ms, nbytes = None, rng.uniform(40, 140), 0
        elif rec["job_type"] == "LOAD":
            slot, exec_ms, nbytes = int(rng.uniform(2e3, 6e5)), rng.uniform(4e3, 9e4), None
        else:
            cx = 1 + 0.35 * info["joins"] + 0.3 * info["window"] + 0.2 * info["group"]
            slot = int(max(12 + 5 * info["joins"], nbytes / self.cfg["cost"]["bytes_per_slot_ms"] * cx
                           * rng.lognormvariate(0, 0.35)))
            par = min(1500, max(1, nbytes / 4e8))
            exec_ms = slot / par + rng.uniform(120, 420)
            if error:
                exec_ms *= rng.uniform(2, 6)
        start = created + dt.timedelta(milliseconds=queue_ms)
        end = start + dt.timedelta(milliseconds=exec_ms)
        billed = 0 if not nbytes or error else max(self.cfg["cost"]["min_billed_bytes"], math.ceil(nbytes / 2**20) * 2**20)
        # tables
        refs, dest = [], None
        if attempted:
            p, ds, tb = attempted.split(".")
        if is_query and not cache_hit and not error:
            if stmt == "CREATE_VIEW":
                bases = set(rec.get("tables_read", []))
            else:
                bases = info["reads_bases"]
            for b in sorted(bases):
                p, ds, tb = b.split(".")
                refs.append({"project_id": p, "dataset_id": ds, "table_id": tb})
        if rec.get("tables_written") and stmt != "SELECT":
            p, ds, tb = rec["tables_written"][0].split(".")
            if rec["job_type"] == "LOAD" and rec.get("destination"):
                tb = re.sub(r"\{\{\w+\}\}", (created.astimezone(self.tz).date() - dt.timedelta(days=1)).strftime("%Y%m%d"),
                            rec["destination"].split(".")[2])
            dest = {"project_id": p, "dataset_id": ds, "table_id": tb}
        elif is_query and not (error and error[0] in ("invalidQuery", "accessDenied")):
            ads = "_" + hashlib.sha1(f"{who['email']}|{project}".encode()).hexdigest()
            tbl = ("anon" + hashlib.sha256(sql.encode()).hexdigest()
                   if info and not info["nondet"] else "anon" + str(uuid.UUID(int=rng.getrandbits(128))).replace("-", "_"))
            dest = {"project_id": project, "dataset_id": ads, "table_id": tbl}
        labels = []
        for k, v in (rec.get("labels") or {}).items():
            if "{{" in str(v):
                m = re.search(r"invocation_id\": \"([0-9a-f-]{36})", sql) or re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", sql)
                v = m.group(1) if m else str(uuid.UUID(int=rng.getrandbits(128)))
            labels.append({"key": k, "value": str(v)})
        dml = None
        if stmt in ("MERGE", "INSERT", "DELETE") and not error:
            n = int((self.rows.get(rec["tables_written"][0], 1000) / 1095) * rng.uniform(0.2, 1.5))
            dml = {"inserted_row_count": n if stmt != "DELETE" else 0,
                   "deleted_row_count": n if stmt == "DELETE" else 0,
                   "updated_row_count": int(n * rng.uniform(0, 0.3)) if stmt == "MERGE" else 0}
        return {
            "creation_time": created.isoformat(), "project_id": project, "project_number": pn[project],
            "user_email": who["email"], "principal_subject": f"{who['kind']}:{who['email']}",
            "job_id": job_id, "job_type": rec["job_type"], "statement_type": stmt,
            "priority": "INTERACTIVE" if rec["job_type"] == "QUERY" else "BATCH",
            "start_time": start.isoformat(), "end_time": end.isoformat(),
            "query": sql if is_query else None, "state": "DONE", "reservation_id": None,
            "total_bytes_processed": nbytes, "total_slot_ms": slot,
            "final_execution_duration_ms": None if cache_hit or not is_query else int(exec_ms),
            "error_result": ({"reason": error[0], "location": "query", "debug_info": None, "message": error[1]}
                             if error else None),
            "cache_hit": cache_hit if rec["job_type"] == "QUERY" else None,
            "destination_table": dest, "referenced_tables": refs, "labels": labels,
            "total_bytes_billed": billed if rec["job_type"] == "QUERY" else None,
            "dml_statistics": dml,
            "total_modified_partitions": (parts if stmt in ("MERGE", "INSERT", "DELETE", "CREATE_TABLE_AS_SELECT")
                                          and not error else None),
            "query_info": ({"query_hashes": {"normalized_literals": normalized_hash(sql)}}
                           if is_query and not cache_hit and not (error and error[0] in ("invalidQuery", "accessDenied"))
                           else None),
            "query_dialect": "GOOGLE_SQL" if is_query else None,
        }

    def truth_row(self, row, e, rec, injected=None, attempted=None) -> dict:
        who = e["who"]
        return {"job_id": row["job_id"], "template_id": rec["id"], "variant": rec["variant"], "family": rec["family"],
                "principal": rec["principal"], "member": who.get("member") or e.get("looker_member"),
                "team": who.get("team") or (self.member_team.get(e.get("looker_member")) if e.get("looker_member") else None),
                "tool": who.get("tool"), "why": e["why"], "session": e.get("session"),
                "looker_user_id": e.get("looker_user"), "findings": rec.get("findings", []),
                "tables_read": [attempted] if attempted else rec.get("tables_read", []),
                "tables_written": [] if (injected or attempted) else rec.get("tables_written", []),
                "injected_error": injected}


# ----------------------------------------------------------------------------
# Report, validation, load
# ----------------------------------------------------------------------------

def report(rows, truth, sim: Sim, validated: tuple[int, int] | None) -> str:
    L = ["# Simulated query log", "", f"Window {sim.start} to {sim.end} ({sim.days} days), seed {sim.cfg['seed']}, "
         f"scale {sim.scale}. {len(rows):,} jobs.", ""]
    kinds = Counter(r["principal_subject"].split(":")[0] for r in rows)
    L += [f"- Service-account jobs: {kinds['serviceAccount'] / len(rows):.1%}; human jobs: {kinds['user'] / len(rows):.1%}"]
    fam = Counter(t["family"] for t in truth)
    L += ["", "## Jobs by family", "", "| Family | Jobs | Share |", "|---|---|---|"]
    L += [f"| {k} | {v:,} | {v / len(rows):.1%} |" for k, v in fam.most_common()]
    per_user = Counter(r["user_email"] for r in rows if r["principal_subject"].startswith("user:"))
    vals = sorted(per_user.values(), reverse=True)
    L += ["", "## People", "", f"{len(per_user)} people ran queries. Jobs per person: max {vals[0]:,}, "
          f"median {vals[len(vals) // 2]:,}, min {vals[-1]:,}.", "",
          "| Person | Jobs |", "|---|---|"] + [f"| {u} | {n:,} |" for u, n in per_user.most_common(8)]
    looker_users = Counter(t["looker_user_id"] for t in truth if t["looker_user_id"] is not None)
    L += ["", f"Looker queries carry {len(looker_users)} distinct Looker user ids in their Query Context comment."]
    q = [r for r in rows if r["job_type"] == "QUERY"]
    L += ["", "## Execution", "",
          f"- Cache hits: {sum(1 for r in q if r['cache_hit']) / len(q):.1%} of query jobs",
          f"- Errors: {sum(1 for r in rows if r['error_result']):,} "
          f"({Counter(r['error_result']['reason'] for r in rows if r['error_result']).most_common()})",
          f"- Bytes processed: {sum(r['total_bytes_processed'] or 0 for r in q) / 2**50:.2f} PiB; "
          f"billed: {sum(r['total_bytes_billed'] or 0 for r in q) / 2**50:.2f} PiB "
          f"(~${sum(r['total_bytes_billed'] or 0 for r in q) / 2**40 * 6.25:,.0f} on-demand)"]
    by_bytes = defaultdict(lambda: [0, 0, ""])
    tmap = {t["job_id"]: t for t in truth}
    for r in q:
        t = tmap[r["job_id"]]
        k = t["template_id"]
        by_bytes[k][0] += r["total_bytes_billed"] or 0
        by_bytes[k][1] += 1
        by_bytes[k][2] = ",".join(t["findings"])
    L += ["", "## Top 12 templates by bytes billed", "", "| Template | Jobs | TiB billed | Findings |", "|---|---|---|---|"]
    for k, (b, n, f) in sorted(by_bytes.items(), key=lambda kv: -kv[1][0])[:12]:
        L.append(f"| {k} | {n:,} | {b / 2**40:,.1f} | {f} |")
    L += ["", "## Planted findings - checks against the log", ""]
    for name, ok, detail in finding_checks(rows, truth, sim):
        L.append(f"- {'PASS' if ok else 'FAIL'} **{name}**: {detail}")
    if validated:
        L += ["", f"## Validation", "", f"{validated[1]} distinct successful query texts sampled and dry-run in "
              f"BigQuery: {validated[0]} passed."]
    return "\n".join(L) + "\n"


def finding_checks(rows, truth, sim: Sim):
    tmap = {t["job_id"]: t for t in truth}
    day = lambda r: dt.datetime.fromisoformat(r["creation_time"]).astimezone(sim.tz).date()
    def reads(fqn, fam_exclude=("dq_monitor",)):
        return [r for r in rows if fqn in tmap[r["job_id"]]["tables_read"] and tmap[r["job_id"]]["family"] not in fam_exclude
                and not r["error_result"]]
    def writes(fqn):
        return [r for r in rows if fqn in tmap[r["job_id"]]["tables_written"] and not r["error_result"]]
    out = []
    dead = [f for f, t in sim.T.items() if t.get("status") == "dead"]
    n = sum(len(reads(f)) for f in dead)
    out.append(("F06 dead tables", n == 0, f"{len(dead)} dead tables, {n} non-monitor reads"))
    wo = [f for f, t in sim.T.items() if t.get("status") == "write_only"]
    w = {f: len(writes(f)) for f in wo}
    rd = sum(len(reads(f)) for f in wo)
    out.append(("F07 write-only", rd == 0 and all(w.values()), f"writes {w}, non-monitor reads {rd}"))
    v2 = "fennmoor-dw.ml_scores.churn_score_v2"
    v2w = [day(r) for r in writes(v2)]
    v2r = [r for r in reads(v2) if day(r) > dt.date(2026, 5, 14)]
    covers = sim.end > dt.date(2026, 5, 20)
    out.append(("F11 churn v2 stragglers" + ("" if covers else " (window ends before the cutover - not applicable)"),
                (not covers) or (bool(v2w) and max(v2w) <= dt.date(2026, 5, 14) and len(v2r) > 0),
                f"last v2 write {max(v2w) if v2w else None}; {len(v2r):,} reads after the cutover by "
                f"{sorted({tmap[r['job_id']]['principal'] for r in v2r})}"))
    eom = "fennmoor-analytics.legacy_edw.ACCT_DLY_BAL"
    out.append(("F05 deprecated but load-bearing", len(writes(eom)) > 0 and len(reads("fennmoor-analytics.sbx_finance.eom_bal_by_product_tableau")) > 0,
                f"{len(writes(eom))} writes to ACCT_DLY_BAL; "
                f"{len(reads('fennmoor-analytics.sbx_finance.eom_bal_by_product_tableau'))} reads of the Tableau source"))
    wtb = "fennmoor-analytics.sbx_marketing.web_to_branch_journeys"
    out.append(("F13 weekly CTAS of an always-empty join", len(writes(wtb)) >= sim.days // 7 - 1,
                f"{len(writes(wtb))} rebuilds by {sorted({r['user_email'] for r in writes(wtb)})}"))
    first_close = min((day(r) for r in rows if r["query"] and "wrapup_code_name = 'ACCT_CLOSE'" in r["query"]
                       and r["principal_subject"].startswith("user:")), default=None)
    out.append(("F17 new closure code appears in human filters on/after 2026-06-02",
                first_close is None and sim.end < dt.date(2026, 6, 2) or (first_close and first_close >= dt.date(2026, 6, 2)),
                f"first human use: {first_close}"))
    dq = sum(1 for t in truth if t["family"] == "dq_monitor")
    out.append(("F19 monitor share", dq > 0, f"{dq:,} monitor jobs ({dq / len(rows):.1%})"))
    cdr = [r for r in rows if r["query"] and "cdr_*" in r["query"] and "_TABLE_SUFFIX" not in r["query"] and not r["error_result"]]
    out.append(("F09 unfiltered shard scans", len(cdr) > 0,
                f"{len(cdr)} cdr_* jobs with no suffix filter, {sum(r['total_bytes_processed'] or 0 for r in cdr) / 2**40:.1f} TiB"))
    def bytes_of(pred):
        sel = [r for r in rows if pred(r, tmap[r["job_id"]]) and not r["error_result"]]
        return len(sel), sum(r["total_bytes_billed"] or 0 for r in sel) / 2**40
    n, tib = bytes_of(lambda r, t: bool(r["query"]) and re.search(r"SELECT \*[^;]*\bLIMIT \d+\s*$", r["query"], re.I | re.S)
                      and (r["total_bytes_billed"] or 0) > 2**30)
    out.append(("F20 SELECT * ... LIMIT still full-scans", n > 0, f"{n:,} jobs over 1 GiB, {tib:,.1f} TiB billed"))
    n, tib = bytes_of(lambda r, t: t["family"] in ("dbt_freshness", "looker_trigger"))
    out.append(("F21 freshness and trigger checks that scan data", tib > 1, f"{n:,} jobs, {tib:,.1f} TiB billed"))
    n, tib = bytes_of(lambda r, t: t["template_id"] in ("dbt.build.fct_app_sessions", "dbt.build.int_digital_sessions"))
    out.append(("F22 incremental models that rescan their source", tib > 1, f"{n:,} runs, {tib:,.1f} TiB billed"))
    return out


def validate_sample(rows, sim: Sim, n: int, project: str) -> tuple[int, int]:
    physical = tpl.make_physical(sim.est, project, "fnb_")
    dry = tpl.DryRunner(project, "qlsc", True)
    seen, sample = set(), []
    rng = random.Random(7)
    pool = [r for r in rows if r["query"] and not r["error_result"]]
    rng.shuffle(pool)
    for r in pool:
        k = normalized_hash(r["query"])
        if k in seen:
            continue
        seen.add(k)
        q = r["query"]
        q = re.sub(r"`fennmoor-raw\.fivetran_staging\.[^`]+`", lambda m: "(SELECT 1 AS x WHERE FALSE)", q)
        if "MERGE" in q[:400] and "fivetran" in (r["user_email"] or ""):
            continue   # the Fivetran staging table only exists mid-sync
        sample.append(physical(q)[0])
        if len(sample) >= n:
            break
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(16) as pool_:
        res = list(pool_.map(dry.check, sample))
    dry.save()
    bad = [(s, r) for s, r in zip(sample, res) if not r.get("ok")]
    for s, r in bad[:10]:
        print("VALIDATION FAIL:", r.get("error"), "\n   ", s[:300].replace("\n", " "))
    return len(sample) - len(bad), len(sample)


def load_to_bigquery(project: str, config: str, prefix: str = "fnb_"):
    """Load the log into <prefix>query_log.jobs, whose schema is copied from the real JOBS view."""
    from deploy import GcloudCredentials
    from google.cloud import bigquery
    c = bigquery.Client(project=project, credentials=GcloudCredentials(config), location="US")
    ds = bigquery.Dataset(f"{project}.{prefix}query_log")
    ds.location = "US"
    ds.description = "Simulated INFORMATION_SCHEMA.JOBS for the Fennmoor estate. No ground truth here."
    c.create_dataset(ds, exists_ok=True)
    table = f"{project}.{prefix}query_log.jobs"
    c.query(f"""CREATE OR REPLACE TABLE `{table}`
PARTITION BY DATE(creation_time) CLUSTER BY project_id, user_email AS
SELECT * FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_USER WHERE FALSE""").result()
    schema = c.get_table(table).schema
    cfg = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON, schema=schema,
                                 write_disposition="WRITE_TRUNCATE")
    with open(OUT / "jobs.ndjson.gz", "rb") as f:
        job = c.load_table_from_file(f, table, job_config=cfg)
    job.result()
    t = c.get_table(table)
    print(f"loaded {t.num_rows:,} rows into {table} ({t.num_bytes / 2**20:,.0f} MiB)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--validate", type=int, default=0, help="dry-run N distinct generated queries")
    ap.add_argument("--project", default="jeffdavis-bq-testproj")
    ap.add_argument("--load", action="store_true", help="load the log into BigQuery (fnb_query_log.jobs)")
    ap.add_argument("--load-only", action="store_true", help="load the existing build/log output, no re-simulation")
    args = ap.parse_args()
    if args.load_only:
        load_to_bigquery(args.project, "qlsc")
        return 0
    cfg = yaml.safe_load((SPECS / "simulation.yaml").read_text())
    wh = json.loads((BUILD / "warehouse.json").read_text())
    records = json.loads((BUILD / "templates.json").read_text())
    estate = yaml.safe_load((SPECS / "warehouse" / "00_estate.yaml").read_text())
    sim = Sim(cfg, wh, records, estate, args.days, args.scale)
    rows, truth = sim.run()
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / "jobs.ndjson.gz", "wt") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    with gzip.open(OUT / "jobs_truth.ndjson.gz", "wt") as f:
        for t in truth:
            f.write(json.dumps(t) + "\n")
    validated = validate_sample(rows, sim, args.validate, args.project) if args.validate else None
    (OUT / "SIMULATION.md").write_text(report(rows, truth, sim, validated))
    print(f"{len(rows):,} jobs -> {OUT / 'jobs.ndjson.gz'}")
    if args.load:
        load_to_bigquery(args.project, "qlsc")
    return 0


if __name__ == "__main__":
    sys.exit(main())
