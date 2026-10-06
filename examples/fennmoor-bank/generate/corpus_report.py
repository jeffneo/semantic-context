"""The dry-run report: what a set of plans looks like, against the world's own targets, before any text is written.

Plan: plans/2026-10-05-process-corpus.md (validation step 2). Free: no warehouse, no LLM. It answers three questions: do the
distributions land where the world says they should; is every outcome reachable; and do the structures the process graph is
later asked to find actually show up in the plans, as the planted truths, with their size.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from corpus_world import World


def pct(n: float, d: float) -> str:
    return f"{100 * n / d:5.1f}%" if d else "    -"


def table(rows: list[list[str]], header: list[str]) -> str:
    cols = list(zip(header, *rows))
    widths = [max(len(str(c)) for c in col) for col in cols]
    fmt = "  ".join(f"{{:<{w}}}" if i == 0 else f"{{:>{w}}}" for i, w in enumerate(widths))
    return "\n".join(["  " + fmt.format(*header)] + ["  " + fmt.format(*map(str, r)) for r in rows])


def report(w: World, plans: list[dict]) -> str:
    n = len(plans)
    out = [f"{n:,} plans"]
    answered = [p for p in plans if p["steps"][0]["kind"] != "queue"]

    # --- the mix --------------------------------------------------------------------------------------------------------
    by_domain = Counter(p["domain"] for p in plans)
    out += ["", "domains (share of plans, against the world's)"]
    out.append(
        table(
            [[d, pct(by_domain[d], n), f"{100 * w.domains[d]['share']:5.1f}%"] for d in w.domains],
            ["", "got", "want"],
        )
    )

    # --- outcomes -------------------------------------------------------------------------------------------------------
    outcomes = Counter(p["outcome"] for p in plans)
    out += ["", "outcomes"]
    out.append(
        table(
            [[o["id"], outcomes[o["id"]], pct(outcomes[o["id"]], n), o["favorability"]] for o in w.outcomes],
            ["", "n", "share", "favorability"],
        )
    )
    unreached = [o["id"] for o in w.outcomes if not outcomes[o["id"]] and o["requires"]]
    out.append("  unreached: " + (", ".join(unreached) if unreached else "none"))
    fav = Counter(p["favorability"] for p in plans)
    want = w.targets.get("by_favorability", {})
    out += ["", "favorability (against the world's targets)"]
    out.append(
        table(
            [
                [f, pct(fav[f], n), f"{100 * want.get(f, 0):5.1f}%"]
                for f in ("high", "medium", "low", "very-low")
            ],
            ["", "got", "want"],
        )
    )

    # --- conduct --------------------------------------------------------------------------------------------------------
    gates: dict[str, list[bool]] = defaultdict(list)
    for p in plans:
        for g in p["gates"]:
            gates[g["policy"]].append(g["met"])
    out += ["", "policy compliance where the gate was reached (against the target)"]
    out.append(
        table(
            [
                [
                    pol,
                    len(met),
                    pct(sum(met), len(met)),
                    f"{100 * w.policies[pol]['target_compliance']:5.1f}%",
                ]
                for pol, met in sorted(gates.items())
            ],
            ["", "reached", "met", "target"],
        )
    )
    breach_success = sum(
        1 for p in plans if p["outcome"] in {"OUT-RETAINED-WITH-BREACH", "OUT-RESOLVED-POLICY-BREACH"}
    )
    out.append(
        f"  right outcome, wrong process (a serious gate skipped on a call that worked): {breach_success} ({pct(breach_success, n).strip()})"
    )

    # --- diagnosis ------------------------------------------------------------------------------------------------------
    out += ["", "misdiagnosis (the rep's final belief is not the cause), where an agent worked the call"]
    rows = []
    for key, label in (("rep", "by rep"), ("procedure", "by procedure"), ("customer", "by customer")):
        groups: dict[str, list[bool]] = defaultdict(list)
        for p in answered:
            if p["believed_cause"] is not None:
                groups[p[key]].append(p["misdiagnosed"])
        for g, v in sorted(groups.items()):
            rows.append([f"{label}: {g}", len(v), pct(sum(v), len(v))])
    out.append(table(rows, ["", "n", "wrong"]))
    mis = [p for p in answered if p["believed_cause"] is not None]
    asked = defaultdict(list)
    for p in mis:
        k = sum(1 for s in p["steps"] if s.get("action") and w.actions[s["action"]]["type"] == "elicit")
        asked[min(k, 3)].append(p["misdiagnosed"])
    out.append(
        table(
            [
                [f"questions asked: {k}{'+' if k == 3 else ''}", len(v), pct(sum(v), len(v))]
                for k, v in sorted(asked.items())
            ],
            ["", "n", "wrong"],
        )
    )

    # --- the planted truths ---------------------------------------------------------------------------------------------
    out += ["", "planted truths"]
    ret = [p for p in plans if p["procedure"] == "PROC-RETENTION" and p["steps"][0]["kind"] != "queue"]
    savable = [p for p in ret if w.effect("ACT-PROCESS-CLOSURE", p["cause"]) != "fixes"]

    def first_offer(p: dict) -> str | None:
        return next(
            (
                s["action"]
                for s in p["steps"]
                if s.get("action") and w.actions[s["action"]]["type"] == "offer"
            ),
            None,
        )

    def kind(p: dict) -> str:
        offer = first_offer(p)
        if offer in (None, "ACT-CONFIRM-DECISION-AND-OPTIONS"):
            return "no real offer"
        if offer == "ACT-OFFER-GENERIC-INCENTIVE":
            return "a generic incentive"
        return (
            "an offer that fits the cause"
            if w.effect(offer, p["cause"]) == "fixes"
            else "an offer for another cause"
        )

    out.append("  2. elicitation and the matching offer: savable closures, retained by what was offered")
    rows = []
    for label in (
        "an offer that fits the cause",
        "a generic incentive",
        "an offer for another cause",
        "no real offer",
    ):
        group = [p for p in savable if kind(p) == label]
        rows.append([label, len(group), pct(sum(p["retained"] for p in group), len(group))])
    out.append(table(rows, ["", "n", "retained"]))
    learned = [p for p in savable if any(s.get("reveals") for s in p["steps"])]
    not_learned = [p for p in savable if p not in learned]
    out.append(
        table(
            [
                [
                    "the rep learned the driver",
                    len(learned),
                    pct(sum(p["retained"] for p in learned), len(learned)),
                ],
                [
                    "the rep did not",
                    len(not_learned),
                    pct(sum(p["retained"] for p in not_learned), len(not_learned)),
                ],
            ],
            ["", "n", "retained"],
        )
    )
    out.append("  4. the site effect (the warehouse has none)")
    rows = []
    for site in sorted(w.site_share):
        s = [p for p in plans if p["site"] == site]
        a = [p for p in s if p["steps"][0]["kind"] != "queue"]
        rows.append(
            [
                site,
                len(s),
                pct(sum(1 for p in s if p["steps"][0]["kind"] == "queue"), len(s)),
                pct(sum(1 for p in a if p["facts"]["committed_action_type"] == "transfer"), len(a)),
                pct(sum(1 for p in a if any(b["severity"] == "serious" for b in p["breaches"])), len(a)),
                pct(sum(p["retained"] for p in a if p in ret), sum(1 for p in a if p in ret)),
            ]
        )
    out.append(table(rows, ["", "n", "hang up in queue", "transferred", "serious breach", "retained"]))
    rec = [p for p in plans if p["recurrence"]]
    out.append(
        f"  5. recurrence: {len(rec)} plans ({pct(len(rec), n).strip()}) bring a callback within the window"
    )
    ctrl = [p for p in plans if p["domain"] == "DOM-SERVICING" and p["steps"][0]["kind"] != "queue"]
    ctrl_out = Counter(p["outcome"] for p in ctrl)
    first = ctrl_out["OUT-RESOLVED-FIRST-CONTACT"]
    out.append(
        f"  7. the control (servicing): {pct(first, len(ctrl)).strip()} resolved on the first contact; the rest: "
        + ", ".join(
            f"{k.removeprefix('OUT-')} {v}"
            for k, v in ctrl_out.most_common()
            if k != "OUT-RESOLVED-FIRST-CONTACT"
        )
    )
    out.append(
        f"  6. text-only: the outcome is not in fct_calls for {sum(1 for p in answered if p['procedure'] == 'PROC-RETENTION')} retention conversations ({sum(p['retained'] for p in ret)} retained)"
    )

    out += [
        "",
        f"events per conversation: mean {sum(p['n_events'] for p in plans) / n:.1f}, max {max(p['n_events'] for p in plans)}",
    ]
    return "\n".join(out)


def verify(w: World, plans: list[dict], pool: list[dict]) -> list[str]:
    """Every plan agrees with the row it was matched to, and no row is used twice. Empty if all do."""
    rows = {r["conversation_id"]: r for r in pool}
    bad, seen = [], set()
    primary = {p["index"]: p for p in plans if "follow_up_of" not in p}
    for p in plans:
        cid = p["conversation_id"]
        r = rows.get(cid)
        if r is None:
            bad.append(f"{cid}: not in the pool")
            continue
        if cid in seen:
            bad.append(f"{cid}: used twice")
        seen.add(cid)
        queue = p["steps"][0]["kind"] == "queue"
        if r["ivr_intent"] != p["intent"]:
            bad.append(f"{cid}: intent {r['ivr_intent']} for a plan about {p['intent']}")
        if queue == bool(r["agent_user_id"]):
            bad.append(
                f"{cid}: the plan {'hangs up in the queue' if queue else 'was answered'}; the row says the opposite"
            )
        if not queue:
            if r["site_id"] != p["site"]:
                bad.append(f"{cid}: site {r['site_id']} for a plan at {p['site']}")
            if w.rep_of(r["agent_user_id"]) != p["rep"]:
                bad.append(f"{cid}: agent is {w.rep_of(r['agent_user_id'])}, the plan's rep {p['rep']}")
            if bool(r["is_authenticated"]) != p["authenticated"]:
                bad.append(f"{cid}: authentication differs")
            if bool(r["was_transferred"]) != (p["facts"]["committed_action_type"] == "transfer"):
                bad.append(f"{cid}: transfer differs")
            if (r["handle_sec"] or 0) < max(
                w.mechanics["handle_min_sec"], w.mechanics["handle_sec_per_event"] * p["n_events"]
            ):
                bad.append(f"{cid}: handle time too short for {p['n_events']} events")
            # A follow-up is about the same fee or purchase as the call it follows, which is the row that must hold it.
            anchor = rows[primary[p["follow_up_of"]]["conversation_id"]] if "follow_up_of" in p else r
            needs = w.causes[p["cause"]].get("needs", {})
            if "fee_unwaived_prior_days" in needs and not anchor["fees"]:
                bad.append(f"{cid}: no unwaived fee for {p['cause']}")
            if "card_purchase_prior_days" in needs and not anchor["purchases"]:
                bad.append(f"{cid}: no card purchase for {p['cause']}")
        else:
            if r["queue_site_id"] != p["site"]:
                bad.append(f"{cid}: queue site differs")
            needs = w.causes[p["cause"]].get("needs", {})
            if (
                p.get("recurrence")
                and not p["recurrence"].get("unrealised")
                and (
                    ("fee_unwaived_prior_days" in needs and not r["fees"])
                    or ("card_purchase_prior_days" in needs and not r["purchases"])
                )
            ):
                bad.append(
                    f"{cid}: a hang-up that is called back needs the fee or purchase the follow-up is about"
                )
        rec = p.get("recurrence")
        if rec and rec.get("follow_up") and rec["follow_up"] not in rows:
            bad.append(f"{cid}: follow-up {rec['follow_up']} is not a row")
    return bad


def against_the_warehouse(plans: list[dict], pool: list[dict]) -> str:
    """The corpus is a sample chosen to carry the planted truths, not a replica: where it differs from the warehouse, and why that
    is the point (the warehouse's flags carry no process)."""
    rows = {r["conversation_id"]: r for r in pool}
    matched = [rows[p["conversation_id"]] for p in plans]
    answered = [r for r in matched if r["agent_user_id"]]

    def share(rs, f):
        return pct(sum(1 for r in rs if f(r)), len(rs))

    def hours(rs):
        ordered = sorted((r["handle_sec"] or 0) for r in rs)
        return f"{ordered[len(ordered) // 2] / 60:5.0f} min"

    def line(label, f, base=pool, mine=matched):
        return [label, share(mine, f), share(base, f)]

    rows_out = [
        line("abandoned before an agent", lambda r: not r["agent_user_id"]),
        line(
            "transferred (of answered)",
            lambda r: r["was_transferred"],
            [r for r in pool if r["agent_user_id"]],
            answered,
        ),
        line("authenticated", lambda r: r["is_authenticated"]),
        line("voice", lambda r: r["media_type"] == "voice"),
        ["median handle time", hours(matched), hours(pool)],
    ]
    return "against the warehouse (the corpus is a sample, not a replica)\n" + table(
        rows_out, ["", "corpus", "warehouse"]
    )
