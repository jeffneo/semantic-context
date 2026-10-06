"""Phase A of the process corpus: decide everything causal, free and seeded, then select a real warehouse row to fit it.

Plan: plans/2026-10-05-process-corpus.md. The world is `spec/corpus/*.yaml`; this module walks it.

A **plan** is one conversation, decided before any text exists: why the customer called (a cause), what they notice and say,
what the rep asks, concludes and does, whether it worked, and how it ended. The walk is the causal chain the demo this follows
is built on:

    cause -> present manifestations -> perceived (salience x attentiveness) -> volunteered (unprompted), or elicited
          -> the rep's belief (exact Bayes over the cause-to-manifestation probabilities) -> an action -> its efficacy
          against the REAL cause -> an outcome derived from the walk, never sampled on its own

Misdiagnosis is therefore a consequence of what was not asked or not noticed, never injected, and a rep who elicits
everything converges on the truth. Reps shift probabilities and never dictate outcomes.

`match` then selects a warehouse row that fits the plan (same intent, site, authentication, rep archetype through the agent,
transfer, a customer who has the fee or the purchase the story names), because the warehouse's own flags carry no process
(measured 2026-10-05) and cannot constrain the story. Nothing in the warehouse changes.

Everything is seeded per conversation: plan i is the same whatever else is generated. Row selection can depend on rows already
taken, which is the one place order shows, and it is reported.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict

from corpus_world import World, item_id

FLOOR = 1e-6  # a likelihood is never exactly zero: a rep is never certain
LIGHT_SAVE = "ACT-CONFIRM-DECISION-AND-OPTIONS"
GENERIC_SAVE = "ACT-OFFER-GENERIC-INCENTIVE"


def pick(rng: random.Random, weights: dict[str, float]) -> str:
    total = sum(weights.values())
    x = rng.random() * total
    for key, weight in weights.items():
        x -= weight
        if x <= 0:
            return key
    return key


def entropy(p: dict[str, float]) -> float:
    return -sum(v * math.log(v) for v in p.values() if v > 0)


class Belief:
    """What the rep thinks is going on: a distribution over the causes the procedure can consider, from the evidence heard.

    The evidence is kept, not just folded in, so a claim the customer made unprompted can be retracted when a direct question
    shows it was not so."""

    def __init__(self, w: World, causes: list[str]):
        self.w = w
        self.attentive = w.mechanics["assumed_attentiveness"]
        self.causes = causes
        self.evidence: list[tuple[str, str]] = []
        self.p: dict[str, float] = {}
        self._rebuild()

    def _reported(self, cause: str, m: str, kind: str) -> float:
        """How likely it is the customer would say this (or say no to it), if this were the cause."""
        in_world = self.w.cause_manifestations[cause].get(m, 0.0)
        if kind == "opener":
            return in_world
        mm = self.w.manifestations[m]
        noticed = mm["salience"] if mm.get("own") else min(1.0, mm["salience"] * self.attentive)
        return in_world * noticed * (mm["volunteer"] if kind == "volunteered" else 1.0)

    def _apply(self, p: dict[str, float], m: str, kind: str) -> dict[str, float]:
        if kind == "denied":
            post = {c: p[c] * max(FLOOR, 1.0 - self._reported(c, m, "heard")) for c in p}
        else:
            post = {c: p[c] * max(FLOOR, self._reported(c, m, kind)) for c in p}
        total = sum(post.values())
        return {c: v / total for c, v in post.items()}

    def _rebuild(self) -> None:
        total = sum(self.w.causes[c]["base_rate"] for c in self.causes)
        p = {c: self.w.causes[c]["base_rate"] / total for c in self.causes}
        for m, kind in self.evidence:
            p = self._apply(p, m, kind)
        self.p = p

    def hear(self, m: str, kind: str) -> None:
        """kind: opener (why they called), volunteered (said unprompted), heard (the answer to a question), denied."""
        self.evidence.append((m, kind))
        self.p = self._apply(self.p, m, kind)

    def retract(self, m: str) -> None:
        """The customer's unprompted claim about m did not survive a direct question."""
        self.evidence = [(x, k) for x, k in self.evidence if not (x == m and k == "volunteered")]
        self._rebuild()

    def leader(self) -> str:
        return max(self.p, key=lambda c: (self.p[c], self.w.causes[c]["base_rate"]))

    def confidence(self) -> float:
        return self.p[self.leader()]

    def gain(self, m: str) -> float:
        """Expected drop in uncertainty from asking about m: the question worth asking has the largest."""
        yes = {c: self.p[c] * self._reported(c, m, "heard") for c in self.p}
        no = {c: self.p[c] * (1.0 - self._reported(c, m, "heard")) for c in self.p}
        p_yes = sum(yes.values())
        if p_yes <= 0 or p_yes >= 1:
            return 0.0
        return (
            entropy(self.p)
            - p_yes * entropy({c: v / p_yes for c, v in yes.items()})
            - (1 - p_yes) * entropy({c: v / (1 - p_yes) for c, v in no.items()})
        )

    def snapshot(self) -> dict:
        return {"leader": self.leader(), "p": round(self.confidence(), 3)}


class Sampler:
    def __init__(self, w: World):
        self.w = w
        self.m = w.mechanics
        self.domain_procedure = {p["domain"]: pid for pid, p in w.procedures.items()}
        self.domain_share = {d: v["share"] for d, v in w.domains.items()}
        self.customer_share = {a: v["share"] for a, v in w.customer_archetypes.items()}
        self.rep_share = {a: v["share"] for a, v in w.rep_archetypes.items()}
        self.gates = self._gates()

    def _gates(self) -> dict[str, set[str]]:
        """procedure -> the policies that gate any of its stages or actions."""
        out: dict[str, set[str]] = {}
        for pid, p in self.w.procedures.items():
            found = set()
            for s in p["stages"]:
                if s.get("requires_policy"):
                    found.add(s["requires_policy"])
                found |= {i["requires_policy"] for i in s["actions"] if isinstance(i, dict)}
            out[pid] = found
        return out

    # ------------------------------------------------------------------ context

    def context(self, rng: random.Random) -> dict:
        """Who calls about what, answered where, by which kind of rep. The warehouse's own marginals where it has them."""
        w = self.w
        pid = self.domain_procedure[pick(rng, self.domain_share)]
        proc = w.procedures[pid]
        cause = pick(rng, {c: w.causes[c]["base_rate"] for c in proc["hypotheses"]})
        intents = w.causes[cause].get("intents") or proc["entry_when"]["intents"]
        return {
            "procedure": pid,
            "domain": proc["domain"],
            "cause": cause,
            "intent": rng.choice(intents),
            "customer": pick(rng, self.customer_share),
            "rep": pick(rng, self.rep_share),
            "site": pick(rng, w.site_share),
            "authenticated": rng.random() < w.authenticated_share,
        }

    def rep_params(self, rep: str, site: str) -> dict:
        base = dict(self.w.rep_archetypes[rep])
        for key, delta in self.w.reps["sites"].get(site, {}).items():
            if key in base:
                base[key] = min(0.98, max(0.02, base[key] + delta))
        return base

    def queue_abandon(self, site: str, patience: float) -> float:
        base = self.w.reps["sites"].get(site, {}).get("queue_abandon", self.w.reps["queue_abandon_default"])
        return min(self.m["queue_abandon_cap"], base * (2.0 - patience))

    def applies(self, policy_id: str, ctx: dict) -> bool:
        cond = self.w.policies[policy_id].get("applies_when", {})
        # A row condition is named as the warehouse column (is_authenticated); the context holds it without the prefix.
        return all(ctx[k.removeprefix("is_")] in v for k, v in cond.items())

    # ------------------------------------------------------------------ the walk

    def walk(self, rng: random.Random, ctx: dict, force_queue: bool | None = None) -> dict:
        w, m = self.w, self.m
        proc = w.procedures[ctx["procedure"]]
        cust = w.customer_archetypes[ctx["customer"]]
        rep = self.rep_params(ctx["rep"], ctx["site"])
        cause = ctx["cause"]
        held = w.causes_for(ctx["procedure"], ctx["intent"])
        plan = {**ctx, "steps": [], "breaches": [], "gates": [], "recurrence": None}

        # --- what the customer is aware of and says -------------------------------------------------------------------
        average_forthcoming = sum(a["forthcoming"] * a["share"] for a in w.customer_archetypes.values())
        present, perceived, volunteered = {}, {}, {}
        for mid, prob in w.cause_manifestations[cause].items():
            mm = w.manifestations[mid]
            present[mid] = rng.random() < prob
            noticed = mm["salience"] if mm.get("own") else min(1.0, mm["salience"] * cust["attentiveness"])
            perceived[mid] = present[mid] and (mm.get("presenting") or rng.random() < noticed)
            volunteered[mid] = perceived[mid] and (
                mm.get("presenting")
                or rng.random() < min(1.0, mm["volunteer"] * cust["forthcoming"] / average_forthcoming)
            )
        # The customer called for a reason: the cause's presenting manifestation is always there, noticed and said.
        opener = max(
            (mid for mid in present if w.manifestations[mid].get("presenting")),
            key=lambda mid: w.cause_manifestations[cause][mid],
        )
        present[opener] = perceived[opener] = volunteered[opener] = True
        topics = w.manifestations[opener].get("topics")
        topic = rng.choice(topics) if topics else None
        said = [mid for mid in volunteered if volunteered[mid] and mid != opener]

        # A customer sure of the wrong cause volunteers a manifestation of the one they have in mind.
        false_claim = None
        confusable = [c for c in w.causes[cause].get("confusable_with", []) if c in held]
        if confusable and rng.random() < cust["p_misattribute"]:
            other = rng.choice(confusable)
            options = [
                mid
                for mid, prob in w.cause_manifestations[other].items()
                if w.manifestations[mid].get("discriminating")
                and prob >= 0.5
                and w.cause_manifestations[cause].get(mid, 0.0) < 0.3
            ]
            if options:
                false_claim = rng.choice(options)

        plan["world"] = {
            "present": [x for x in present if present[x]],
            "perceived": [x for x in perceived if perceived[x]],
            "volunteered": said,
            "opener": opener,
            "topic": topic,
            "false_claim": false_claim,
        }

        # --- the queue -------------------------------------------------------------------------------------------------
        hung_up = force_queue
        if hung_up is None:
            hung_up = rng.random() < self.queue_abandon(ctx["site"], cust["patience"])
        if hung_up:
            plan["steps"].append(
                {"kind": "queue", "actor": "customer", "note": "hangs up before an agent answers"}
            )
            return self._finish(rng, plan, abandoned="queue")

        # --- the opening: what the rep hears -----------------------------------------------------------------------------
        belief = Belief(w, held)
        belief.hear(opener, "opener")
        plan["steps"].append(
            {
                "kind": "open",
                "actor": "customer",
                "manifestation": opener,
                "volunteers": said,
                "false_claim": false_claim,
            }
        )
        for mid in said:
            belief.hear(mid, "volunteered")
        accepted_claim = false_claim is not None and rng.random() < rep["p_accept_misattribution"]
        if accepted_claim:
            belief.hear(false_claim, "volunteered")
        plan["steps"][-1]["claim_accepted"] = accepted_claim
        plan["steps"][-1]["belief"] = belief.snapshot()

        taken: list[str] = []

        def step(stage: str, action: str, **extra) -> None:
            taken.append(action)
            plan["steps"].append({"kind": "rep", "actor": "rep", "stage": stage, "action": action, **extra})

        def satisfied(policy_id: str) -> bool:
            return bool(set(w.policies[policy_id]["satisfied_by"]) & set(taken))

        def gate(policy_id: str, where: str, met: bool) -> None:
            """Record a gate the rep reached, and a breach if it was not met."""
            plan["gates"].append({"policy": policy_id, "at": where, "met": met})
            if not met:
                plan["breaches"].append(
                    {"policy": policy_id, "severity": w.policies[policy_id]["severity"], "at": where}
                )

        stages = proc["stages"]

        # --- open and verify ---------------------------------------------------------------------------------------------
        opening = [item_id(i) for i in stages[0]["actions"]]
        for pol in sorted(self.gates[ctx["procedure"]]):
            if not self.applies(pol, ctx) or satisfied(pol):
                continue
            first = next((a for a in opening if a in w.policies[pol]["satisfied_by"]), None)
            if first and rng.random() < rep["policy_compliance"]:
                step(stages[0]["id"], first)
        courtesy = ctx["authenticated"] and rng.random() < m["courtesy_verify"]
        if courtesy and "ACT-VERIFY-IDENTITY" in opening and "ACT-VERIFY-IDENTITY" not in taken:
            step(stages[0]["id"], "ACT-VERIFY-IDENTITY")
        # Some policies gate the discovery stage; entering it unsatisfied is the breach.
        asks = [s for s in stages[1:] if any(w.actions[item_id(i)]["type"] == "elicit" for i in s["actions"])]
        discover = asks[0] if asks else None
        if discover and discover.get("requires_policy"):
            pol = discover["requires_policy"]
            if self.applies(pol, ctx):
                gate(pol, discover["id"], satisfied(pol))

        # --- a rep who hands the call on before working it ---------------------------------------------------------------
        resolve = next(
            s for s in reversed(stages) if any(w.actions[item_id(i)].get("commits") for i in s["actions"])
        )
        by_type = {w.actions[item_id(i)]["type"]: item_id(i) for i in resolve["actions"]}
        if "transfer" in by_type and rng.random() < rep["p_early_transfer"]:
            step(resolve["id"], by_type["transfer"], belief=belief.snapshot())
            return self._finish(rng, plan, commit=by_type["transfer"], believed_cause=belief.leader())

        # --- discovery -----------------------------------------------------------------------------------------------------
        asked = 0
        if discover:
            options = [item_id(i) for i in discover["actions"]]
            open_q = next((a for a in options if w.actions[a].get("elicits_any")), None)
            works_it = rng.random() < rep["p_elicit_before_commit"]
            if open_q and rng.random() < (
                m["open_question_first"] if works_it else m["open_question_hurried"]
            ):
                recovered = []
                for mid in present:
                    hidden = (
                        perceived[mid]
                        and not volunteered[mid]
                        and w.manifestations[mid].get("discriminating")
                    )
                    if hidden and rng.random() < w.actions[open_q]["elicits_any"]:
                        recovered.append(mid)
                        belief.hear(mid, "heard")
                step(discover["id"], open_q, reveals=recovered, belief=belief.snapshot())
                asked += 1
            while (
                works_it
                and asked < m["max_asks"] + (1 if open_q else 0)
                and belief.confidence() < m["stop_confidence"]
            ):
                known = {mid for mid in present if perceived[mid] and volunteered[mid]}
                candidates = [
                    a
                    for a in options
                    if w.actions[a].get("elicits")
                    and a not in taken
                    and w.actions[a]["elicits"] not in known
                    and w.actions[a]["elicits"]
                    not in {r for s in plan["steps"] for r in s.get("reveals", [])}
                ]
                if not candidates:
                    break
                best = max(candidates, key=lambda a: belief.gain(w.actions[a]["elicits"]))
                mid = w.actions[best]["elicits"]
                if belief.gain(mid) < 0.01:
                    break
                yes = perceived.get(mid, False)
                if yes:
                    belief.hear(mid, "heard")
                else:
                    if accepted_claim and mid == false_claim:
                        belief.retract(mid)
                    belief.hear(mid, "denied")
                step(
                    discover["id"],
                    best,
                    reveals=[mid] if yes else [],
                    answer="yes" if yes else "no",
                    belief=belief.snapshot(),
                )
                asked += 1
                # A hurried rep stops early, in proportion to how unsure they still are.
                if rng.random() < rep["p_premature_commit"] * (1.0 - belief.confidence()):
                    break

            # The customer's patience.
            if asked and rng.random() < m["frustration"] * (1.0 - cust["patience"]) * (1 + asked):
                plan["steps"].append(
                    {"kind": "hangup", "actor": "customer", "note": "hangs up in frustration"}
                )
                return self._finish(rng, plan, abandoned="frustration", believed_cause=belief.leader())

        # --- trying to keep the customer ---------------------------------------------------------------------------------
        retained = False
        offers_stage = next(
            (s for s in stages if any(w.actions[item_id(i)]["type"] == "offer" for i in s["actions"])), None
        )
        accepted_offer = None
        escalated = False
        if offers_stage:
            offers = [item_id(i) for i in offers_stage["actions"]]
            if rng.random() < rep["p_attempt_save"]:
                tries = 0
                while tries < 2:
                    fits = [
                        a
                        for a in offers
                        if a != LIGHT_SAVE and a not in taken and w.effect(a, belief.leader()) == "fixes"
                    ]
                    if fits:
                        choice = rng.choice(fits)
                    elif GENERIC_SAVE not in taken and rng.random() < m["generic_when_no_match"]:
                        choice = GENERIC_SAVE
                    else:
                        choice = LIGHT_SAVE
                    step(offers_stage["id"], choice, belief=belief.snapshot())
                    if choice == LIGHT_SAVE:
                        break
                    effect = w.effect(choice, cause)
                    plan["steps"][-1]["effect"] = effect
                    if effect == "fixes" or (
                        effect == "partial" and rng.random() < w.acceptance["partial_offer_accept"]
                    ):
                        retained, accepted_offer = True, choice
                        break
                    if effect == "makes-worse" and rng.random() < w.acceptance["makes_worse_escalates"]:
                        escalated = True
                        break
                    tries += 1
                    if tries == 1 and rng.random() >= m["second_offer"]:
                        break
            elif rng.random() < rep["policy_compliance"]:
                step(offers_stage["id"], LIGHT_SAVE, belief=belief.snapshot())
            plan["save_attempted"] = any(a in taken for a in offers)
            if retained:
                return self._finish(
                    rng, plan, retained=True, accepted_offer=accepted_offer, believed_cause=belief.leader()
                )

        # --- deciding ---------------------------------------------------------------------------------------------------
        commits = [item_id(i) for i in resolve["actions"] if w.actions[item_id(i)].get("commits")]
        escalate = by_type.get("escalate")
        demands = rng.random() < m["supervisor_base"] + m["supervisor_scale"] * cust["escalation_propensity"]
        if escalated or (escalate and demands):
            step(
                resolve["id"], escalate, belief=belief.snapshot(), reason="the customer asks for a supervisor"
            )
            return self._finish(rng, plan, commit=escalate, believed_cause=belief.leader())

        plain = [a for a in commits if w.actions[a]["type"] not in {"transfer", "escalate"}]
        fixers = [a for a in plain if w.effect(a, belief.leader()) == "fixes"]
        if fixers:
            commit = rng.choice(fixers)
        else:
            commit = (
                next((a for a in plain if w.actions[a]["type"] == "process"), None)
                or by_type.get("transfer")
                or plain[0]
            )
        # A gate on the stage itself (nothing before it could satisfy it) is a breach if open; one on the action can be met by a
        # step in between, which a compliant rep takes.
        if resolve.get("requires_policy") and not discover:
            pol = resolve["requires_policy"]
            if self.applies(pol, ctx):
                gate(pol, commit, satisfied(pol))
        gated = next((i for i in resolve["actions"] if isinstance(i, dict) and i["id"] == commit), None)
        pol = (gated or {}).get("requires_policy")
        if pol and self.applies(pol, ctx):
            if not satisfied(pol):
                # Only a stage the rep has not been through can still satisfy it (the discovery and save stages have been).
                passed = {discover["id"] if discover else None, offers_stage["id"] if offers_stage else None}
                late = next(
                    (
                        (s["id"], a)
                        for s in stages
                        if s["id"] not in passed
                        for a in map(item_id, s["actions"])
                        if a in w.policies[pol]["satisfied_by"]
                    ),
                    None,
                )
                if late and rng.random() < rep["policy_compliance"]:
                    step(*late)
            gate(pol, commit, satisfied(pol))
        if offers_stage:
            plan["save_attempted"] = any(a in taken for a in map(item_id, offers_stage["actions"]))
        step(resolve["id"], commit, belief=belief.snapshot())
        if (
            w.effect(commit, cause) == "makes-worse"
            and escalate
            and rng.random() < w.acceptance["makes_worse_escalates"]
        ):
            step(resolve["id"], escalate, reason="the customer pushes back on what was done")
            return self._finish(
                rng, plan, commit=escalate, believed_cause=belief.leader(), first_commit=commit
            )
        return self._finish(rng, plan, commit=commit, believed_cause=belief.leader())

    # ------------------------------------------------------------------ outcome

    def _finish(
        self,
        rng: random.Random,
        plan: dict,
        *,
        abandoned: str | None = None,
        retained: bool = False,
        accepted_offer: str | None = None,
        commit: str | None = None,
        first_commit: str | None = None,
        believed_cause: str | None = None,
    ) -> dict:
        w = self.w
        cause = plan["cause"]
        final = accepted_offer or commit
        effect_of = w.effect(final, cause) if final else None
        # The rep believes it is settled when the action they took is what they would expect to fix what they believed.
        believes = bool(final) and w.effect(final, believed_cause) == "fixes" if believed_cause else False
        facts = {
            "abandoned": abandoned is not None,
            "abandon_reason": abandoned,
            "procedure": plan["procedure"],
            "retained": retained,
            "save_attempted": plan.get("save_attempted", False),
            "policy_breach": any(b["severity"] == "serious" for b in plan["breaches"]),
            "committed_action_type": w.actions[final]["type"] if final else None,
            "committed_incurs_cost": bool(final and w.actions[final].get("incurs_cost")),
            "efficacy": effect_of,
            "rep_believes_resolved": believes,
        }
        outcome = next(o for o in w.outcomes if self._matches(o.get("requires") or {}, facts))
        plan.update(
            {
                "outcome": outcome["id"],
                "favorability": outcome["favorability"],
                "final_action": final,
                "first_commit": first_commit,
                "efficacy": effect_of,
                "retained": retained,
                "believed_cause": believed_cause,
                "misdiagnosed": believed_cause is not None and believed_cause != cause,
                "abandoned": abandoned,
                "facts": facts,
            }
        )
        plan.setdefault("save_attempted", False)
        # A callback: only inside the window the pool can support, and only if the outcome makes one likely.
        window = self.m["callback_days"]
        delay = outcome.get("recurrence_delay_days") or {}
        callable_back = outcome.get("triggers_recurrence") and delay.get("min", window + 1) <= window
        if callable_back and rng.random() < outcome["recurrence_probability"]:
            plan["recurrence"] = {"delay_days": rng.randint(delay["min"], min(delay["max"], window))}
        plan["n_events"] = self._events(plan)
        return plan

    @staticmethod
    def _matches(requires: dict, facts: dict) -> bool:
        for key, want in requires.items():
            have = facts[key]
            if key in {"procedure", "efficacy"}:
                if have not in want:
                    return False
            elif have != want:
                return False
        return True

    @staticmethod
    def _events(plan: dict) -> int:
        """About how many utterances the conversation needs: an opener and a greeting, two for every step the rep takes, a close."""
        if plan["steps"][0]["kind"] == "queue":
            return 1
        reps = sum(1 for s in plan["steps"] if s["kind"] == "rep")
        return 2 + 2 * reps + 2 + (1 if not plan.get("abandoned") else 0)

    # ------------------------------------------------------------------ one plan

    def plan(self, seed: int, i: int, attempt: int = 0) -> dict:
        rng = random.Random(f"corpus:{seed}:{i}:{attempt}")
        ctx = self.context(rng)
        plan = self.walk(rng, ctx)
        plan.update({"index": i, "attempt": attempt})
        return plan

    def follow_up(
        self, seed: int, i: int, first: dict, row: dict, w_rep: str, tries: int = 200
    ) -> dict | None:
        """The same customer calls again about the same cause, on a row that is already fixed: the walk is resampled until
        it agrees with what the row says happened (an answered call or not; transferred or not)."""
        answered = bool(row["agent_user_id"])
        for k in range(tries):
            rng = random.Random(f"corpus:{seed}:{i}:follow:{k}")
            ctx = {
                **{key: first[key] for key in ("procedure", "domain", "cause", "customer")},
                "intent": row["ivr_intent"],
                "rep": w_rep,
                "site": row["site_id"] if answered else row["queue_site_id"],
                "authenticated": bool(row["is_authenticated"]),
            }
            plan = self.walk(rng, ctx, force_queue=not answered)
            transferred = plan["facts"]["committed_action_type"] == "transfer"
            floor = max(self.m["handle_min_sec"], self.m["handle_sec_per_event"] * plan["n_events"])
            if not answered or (
                transferred == bool(row["was_transferred"]) and (row["handle_sec"] or 0) >= floor
            ):
                plan.update({"index": i, "attempt": k, "follow_up_of": first["index"]})
                return plan
        return None


# ---------------------------------------------------------------------- matching a plan to a row


class Matcher:
    """Selects warehouse rows for plans. Rows are bucketed once by what every plan fixes (intent, answered, site, rep
    archetype, authenticated), and a plan filters its bucket by the rest, taking the first unused row of a seeded shuffle."""

    def __init__(self, w: World, pool: list[dict]):
        self.w = w
        self.m = w.mechanics
        self.rows = {r["conversation_id"]: r for r in pool}
        self.used: set[str] = set()
        self.buckets: dict[tuple, list[dict]] = defaultdict(list)
        for r in pool:
            if r["agent_user_id"]:
                key = (
                    r["ivr_intent"],
                    True,
                    r["site_id"],
                    w.rep_of(r["agent_user_id"]),
                    bool(r["is_authenticated"]),
                )
            else:
                key = (r["ivr_intent"], False, r["queue_site_id"], None, None)
            self.buckets[key].append(r)

    def wanted(self, plan: dict) -> dict:
        """What the plan needs of its row, in the row's own terms."""
        w = self.w
        queue = plan["steps"][0]["kind"] == "queue"
        floor = max(self.m["handle_min_sec"], self.m["handle_sec_per_event"] * plan["n_events"])
        return {
            "queue": queue,
            "transferred": plan["facts"]["committed_action_type"] == "transfer",
            "closure": plan["procedure"] == "PROC-RETENTION" and not queue,
            "needs": w.causes[plan["cause"]].get("needs", {}),
            "handle_floor": floor,
        }

    def fits(self, r: dict, want: dict, plan: dict) -> bool:
        if r["conversation_id"] in self.used:
            return False
        # A fee or a purchase is what a later call is about too, so a plan that will be called back needs it even if it hung up.
        needs = want["needs"] if not want["queue"] or plan["recurrence"] is not None else {}
        if "fee_unwaived_prior_days" in needs and not r["fees"]:
            return False
        if "card_purchase_prior_days" in needs and not r["purchases"]:
            return False
        if want["queue"]:
            return True
        if bool(r["was_transferred"]) != want["transferred"]:
            return False
        if (r["handle_sec"] or 0) < want["handle_floor"]:
            return False
        return not (want["closure"] and not r["is_account_closure_call"])

    def callback_ok(self, r: dict, plan: dict) -> bool:
        """The anchor's next call about the same thing, near the planned delay, is a row the follow-up can use: answered by an
        agent and not transferred (the follow-up is a conversation of its own, not a hang-up or a hand-off the plan forced), long
        enough for its events, a closure call if the story is a closure, and not already taken."""
        nxt = self.rows.get(r["next_id"]) if r["next_id"] else None
        if (
            nxt is None
            or nxt["conversation_id"] in self.used
            or not nxt["agent_user_id"]
            or nxt["was_transferred"]
        ):
            return False
        if abs(r["next_gap_days"] - plan["recurrence"]["delay_days"]) > 3:
            return False
        if plan["procedure"] == "PROC-RETENTION" and not nxt["is_account_closure_call"]:
            return False
        return (nxt["handle_sec"] or 0) >= self.m["handle_min_sec"] + self.m["handle_sec_per_event"] * 12

    def select(self, plan: dict, rng: random.Random) -> dict | None:
        key = (
            (plan["intent"], False, plan["site"], None, None)
            if plan["steps"][0]["kind"] == "queue"
            else (plan["intent"], True, plan["site"], plan["rep"], plan["authenticated"])
        )
        want = self.wanted(plan)
        bucket = self.buckets.get(key, [])
        order = list(range(len(bucket)))
        rng.shuffle(order)
        wants_callback = plan["recurrence"] is not None
        for j in order:
            r = bucket[j]
            if not self.fits(r, want, plan):
                continue
            if wants_callback and not self.callback_ok(r, plan):
                continue
            self.used.add(r["conversation_id"])
            return r
        return None


# ---------------------------------------------------------------------- the whole set


def generate(w: World, pool: list[dict], seed: int, n: int) -> tuple[list[dict], dict]:
    """n conversations matched to rows, plus their follow-up calls. Returns the plans and what it took."""
    sampler, matcher = Sampler(w), Matcher(w, pool)
    plans: list[dict] = []
    stats: Counter = Counter()
    for i in range(n):
        for attempt in range(w.mechanics["match_attempts"]):
            plan = sampler.plan(seed, i, attempt)
            rng = random.Random(f"match:{seed}:{i}:{attempt}")
            # A callback needs an anchor row with a successor; if there is none, the plan keeps its outcome and loses the callback.
            row = matcher.select(plan, rng)
            if row is None and plan["recurrence"] is not None:
                stats["callback_unmatched"] += 1
                saved, plan["recurrence"] = plan["recurrence"], None
                row = matcher.select(plan, rng)
                plan["recurrence"] = {**saved, "unrealised": True}
            if row is not None:
                break
            stats["resampled"] += 1
        else:
            stats["given_up"] += 1
            continue
        plan["conversation_id"] = row["conversation_id"]
        plan["row"] = {
            k: row[k]
            for k in (
                "conversation_start",
                "media_type",
                "site_id",
                "queue_site_id",
                "agent_user_id",
                "cif_number",
                "is_authenticated",
                "was_transferred",
                "is_abandoned",
                "handle_sec",
                "wrapup_code_name",
                "ivr_intent",
            )
        }
        plan["mentions"] = {"fees": row["fees"] or [], "purchases": row["purchases"] or []}
        plans.append(plan)
        rec = plan["recurrence"]
        if rec and not rec.get("unrealised"):
            nxt = matcher.rows[row["next_id"]]
            matcher.used.add(nxt["conversation_id"])
            follow = sampler.follow_up(
                seed, i, plan, nxt, w.rep_of(nxt["agent_user_id"]) if nxt["agent_user_id"] else plan["rep"]
            )
            if follow is None:
                stats["follow_up_unmatched"] += 1
                rec["unrealised"] = True
                matcher.used.discard(nxt["conversation_id"])
            else:
                follow["conversation_id"] = nxt["conversation_id"]
                follow["row"] = {k: nxt[k] for k in plan["row"]}
                # The same fee or purchase is what the customer is still calling about, so it is the anchor's.
                follow["mentions"] = plan["mentions"]
                follow["recurrence"] = None
                rec["follow_up"] = nxt["conversation_id"]
                plans.append(follow)
                stats["follow_ups"] += 1
    stats["plans"] = len(plans)
    return plans, dict(stats)
