"""The process corpus's world model: load `spec/corpus/*.yaml`, index it, and check it.

The YAML is the source of truth (it is the answer key for the process graph) and `World` only makes it convenient to walk.
`validate` keeps its own raw loading because it has to check the structure `World` assumes. A world this size has authoring
errors that are invisible by inspection (a cause no procedure can reach, an action with no efficacy row, a gate nothing can
satisfy), and each shows up not as a crash but as a quietly misshapen corpus, so run the check before anything else.

    uv run examples/fennmoor-bank/generate/corpus.py --validate-world [--strict]

Plan: plans/2026-10-05-process-corpus.md.
"""

from __future__ import annotations

import zlib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

WORLD = Path(__file__).resolve().parents[1] / "spec" / "corpus"
FILES = [
    "domains",
    "manifestations",
    "causes",
    "actions",
    "efficacy",
    "procedures",
    "policies",
    "outcomes",
    "reps",
    "customers",
    "mechanics",
]

# The vocabularies the files may use. Intents are the warehouse's own (`dw_contact_center.fct_calls.ivr_intent`).
INTENTS = {"BALANCE", "CARD", "PAYMENT", "OTHER", "FRAUD", "ADDRESS", "CLOSE_ACCOUNT"}
SITES = {"TUL", "SPK", "MNL"}
ACTION_TYPES = {
    "verify",
    "check",
    "elicit",
    "offer",
    "remediate",
    "explain",
    "answer",
    "process",
    "route",
    "transfer",
    "escalate",
}
EFFICACY = {"fixes", "partial", "no-effect", "makes-worse"}
FAVORABILITY = {"high", "medium", "low", "very-low"}
SEVERITY = {"standard", "serious"}
# What the warehouse must hold for a customer before a cause that names it can be drawn.
NEEDS = {"fee_unwaived_prior_days", "card_purchase_prior_days"}
# Conditions on the matched warehouse row a policy may apply under.
ROW_CONDITIONS = {"is_authenticated"}
OUTCOME_KEYS = {
    "abandoned",
    "abandon_reason",
    "procedure",
    "retained",
    "save_attempted",
    "policy_breach",
    "committed_action_type",
    "committed_incurs_cost",
    "efficacy",
    "rep_believes_resolved",
}
ABANDON_REASONS = {"queue", "frustration"}
REP_FIELDS = {
    "policy_compliance",
    "p_elicit_before_commit",
    "p_accept_misattribution",
    "p_premature_commit",
    "p_attempt_save",
    "p_early_transfer",
}
EPS = 0.02


def item_id(item) -> str:
    """A stage's action is a bare id or {id, requires_policy}."""
    return item["id"] if isinstance(item, dict) else item


class World:
    def __init__(self, raw: dict):
        self.domains = {d["id"]: d for d in raw["domains"]}
        self.manifestations = {m["id"]: m for m in raw["manifestations"]}
        self.causes = {c["id"]: c for c in raw["causes"]}
        self.actions = {a["id"]: a for a in raw["actions"]}
        self.efficacy = {e["action"]: (e.get("effects") or {}) for e in raw["efficacy"]}
        self.procedures = {p["id"]: p for p in raw["procedures"]}
        self.policies = {p["id"]: p for p in raw["policies"]}
        self.outcomes = raw["outcomes"]["outcomes"]
        self.acceptance = raw["outcomes"].get("acceptance", {})
        self.targets = raw["outcomes"].get("targets", {})
        self.reps = raw["reps"]
        self.rep_archetypes = {a["id"]: a for a in raw["reps"]["archetypes"]}
        self.customer_archetypes = {a["id"]: a for a in raw["customers"]["archetypes"]}
        self.authenticated_share = raw["customers"]["authenticated_share"]
        self.mechanics = raw["mechanics"]
        # An agent's archetype is a stable hash of the agent, so the same agent is the same rep in every conversation.
        self._rep_cumulative = []
        total = 0.0
        for a in raw["reps"]["archetypes"]:
            total += a["share"]
            self._rep_cumulative.append((total, a["id"]))
        self.site_share = raw["reps"]["site_share"]
        # cause -> {manifestation: probability it is present in the world}
        self.cause_manifestations = {
            cid: {m["id"]: m["probability"] for m in c["manifestations"]} for cid, c in self.causes.items()
        }
        # manifestation -> the action that retrieves it
        self.elicitor = {a["elicits"]: aid for aid, a in self.actions.items() if a.get("elicits")}
        self.intent_procedure = {
            intent: pid for pid, p in self.procedures.items() for intent in p["entry_when"]["intents"]
        }

    def rep_of(self, agent_user_id: str) -> str:
        """The rep archetype of an estate agent: a stable hash of the agent against the archetypes' shares."""
        x = (zlib.crc32(f"rep|{agent_user_id}".encode()) % 10000) / 10000
        for cumulative, aid in self._rep_cumulative:
            if x <= cumulative:
                return aid
        return self._rep_cumulative[-1][1]

    def effect(self, action_id: str, cause_id: str) -> str:
        """What `action_id` does to `cause_id`. The sparse default is load bearing: no row means no effect."""
        return self.efficacy.get(action_id, {}).get(cause_id, "no-effect")

    def procedure_actions(self, procedure_id: str, upto_stage: str | None = None) -> list[str]:
        """The action ids of a procedure, in stage order, stopping before `upto_stage` if given."""
        ids = []
        for stage in self.procedures[procedure_id]["stages"]:
            if stage["id"] == upto_stage:
                break
            ids.extend(item_id(i) for i in stage["actions"])
        return ids

    def causes_for(self, procedure_id: str, intent: str) -> list[str]:
        """The causes a procedure can draw for a row with this intent."""
        return [
            cid
            for cid in self.procedures[procedure_id]["hypotheses"]
            if intent
            in (self.causes[cid].get("intents") or self.procedures[procedure_id]["entry_when"]["intents"])
        ]


def load_world(path: Path = WORLD) -> World:
    return World(_raw(path))


def _raw(path: Path = WORLD) -> dict:
    raw = {}
    for name in FILES:
        with open(Path(path) / f"{name}.yaml") as handle:
            raw[name] = yaml.safe_load(handle)
    return raw


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def validate(path: Path = WORLD) -> tuple[Report, dict[str, int]]:
    r = Report()
    w = load_world(path)
    raw = _raw(path)

    _integrity(r, w)
    _procedures(r, w)
    _reachability(r, w)
    _policies(r, w)
    _outcomes(r, w)
    _distributions(r, w, raw)
    _shape(r, w)

    counts = {
        "domains": len(w.domains),
        "causes": len(w.causes),
        "manifestations": len(w.manifestations),
        "actions": len(w.actions),
        "efficacy rows": len(w.efficacy),
        "procedures": len(w.procedures),
        "policies": len(w.policies),
        "outcomes": len(w.outcomes),
        "rep archetypes": len(w.rep_archetypes),
        "customer archetypes": len(w.customer_archetypes),
    }
    return r, counts


def _integrity(r: Report, w: World) -> None:
    """Every reference resolves, every value is in its vocabulary."""
    for mid, m in w.manifestations.items():
        for key in ("salience", "volunteer"):
            if not 0.0 <= m[key] <= 1.0:
                r.errors.append(f"{mid}: {key} {m[key]} outside 0..1")
        if "topics" in m and (not m.get("presenting") or not m["topics"]):
            r.errors.append(f"{mid}: topics are for a presenting manifestation, and need at least one")
        if m.get("own") and not m.get("discriminating"):
            r.errors.append(f"{mid}: own is for the customer's reasons and acts, which are discriminating")
        if m.get("presenting") and m.get("discriminating"):
            r.errors.append(f"{mid}: presenting and discriminating (the opener says nothing about the cause)")

    for cid, c in w.causes.items():
        if c["domain"] not in w.domains:
            r.errors.append(f"{cid}: unknown domain {c['domain']}")
        if not c.get("manifestations"):
            r.errors.append(f"{cid}: no manifestations, so it can never present")
        for entry in c.get("manifestations", []):
            if entry["id"] not in w.manifestations:
                r.errors.append(f"{cid}: unknown manifestation {entry['id']}")
            if not 0.0 <= entry["probability"] <= 1.0:
                r.errors.append(f"{cid}: {entry['id']} probability {entry['probability']} outside 0..1")
        for key in c.get("needs", {}):
            if key not in NEEDS:
                r.errors.append(f"{cid}: unknown needs key {key}")
        for other in c.get("confusable_with", []):
            if other not in w.causes:
                r.errors.append(f"{cid}: confusable_with unknown cause {other}")
            elif w.causes[other]["domain"] != c["domain"]:
                r.errors.append(f"{cid}: confusable_with {other} from another domain")
        for intent in c.get("intents", []):
            if intent not in INTENTS:
                r.errors.append(f"{cid}: unknown intent {intent}")
        if not any(
            w.manifestations.get(e["id"], {}).get("presenting") and e["probability"] >= 0.9
            for e in c["manifestations"]
        ):
            r.errors.append(
                f"{cid}: no presenting manifestation that is near certain, so nothing opens the call"
            )

    for aid, a in w.actions.items():
        if a["type"] not in ACTION_TYPES:
            r.errors.append(f"{aid}: unknown type {a['type']}")
        if a.get("elicits") and a["elicits"] not in w.manifestations:
            r.errors.append(f"{aid}: elicits unknown manifestation {a['elicits']}")
        if "elicits_any" in a and not 0.0 < a["elicits_any"] <= 1.0:
            r.errors.append(f"{aid}: elicits_any {a['elicits_any']} outside (0, 1]")
        if a.get("resolving") and a["type"] != "offer":
            r.errors.append(f"{aid}: resolving is for offers")
        if a["type"] == "elicit" and not (a.get("elicits") or a.get("elicits_any")):
            r.errors.append(f"{aid}: an elicit action that elicits nothing")

    for aid, effects in w.efficacy.items():
        if aid not in w.actions:
            r.errors.append(f"efficacy: unknown action {aid}")
        for cid, value in effects.items():
            if cid not in w.causes:
                r.errors.append(f"efficacy[{aid}]: unknown cause {cid}")
            if value not in EFFICACY:
                r.errors.append(f"efficacy[{aid}][{cid}]: bad value {value!r}")


def _procedures(r: Report, w: World) -> None:
    claimed: dict[str, list[str]] = {}
    held: Counter = Counter()
    for pid, p in w.procedures.items():
        if p["domain"] not in w.domains:
            r.errors.append(f"{pid}: unknown domain {p['domain']}")
        for intent in p["entry_when"]["intents"]:
            if intent not in INTENTS:
                r.errors.append(f"{pid}: unknown intent {intent}")
            claimed.setdefault(intent, []).append(pid)
        for cid in p["hypotheses"]:
            if cid not in w.causes:
                r.errors.append(f"{pid}: hypothesis names unknown cause {cid}")
                continue
            held[cid] += 1
            if w.causes[cid]["domain"] != p["domain"]:
                r.errors.append(f"{pid}: holds {cid} from another domain")
            stray = set(w.causes[cid].get("intents", [])) - set(p["entry_when"]["intents"])
            if stray:
                r.errors.append(f"{pid}: {cid} names intents {sorted(stray)} the procedure is not entered by")

        committing = False
        for stage in p["stages"]:
            gate = stage.get("requires_policy")
            if gate and gate not in w.policies:
                r.errors.append(f"{pid}/{stage['id']}: unknown policy {gate}")
            for item in stage["actions"]:
                aid = item_id(item)
                if aid not in w.actions:
                    r.errors.append(f"{pid}/{stage['id']}: unknown action {aid}")
                    continue
                if isinstance(item, dict) and item.get("requires_policy") not in w.policies:
                    r.errors.append(
                        f"{pid}/{stage['id']}/{aid}: unknown policy {item.get('requires_policy')}"
                    )
                committing = committing or bool(w.actions[aid].get("commits"))
        if not committing:
            r.errors.append(f"{pid}: no committing action in any stage, so it cannot end")

    for intent in sorted(INTENTS):
        owners = claimed.get(intent, [])
        if len(owners) != 1:
            r.errors.append(f"intent {intent}: entered by {owners or 'no procedure'}, expected exactly one")
    for cid in w.causes:
        if held[cid] != 1:
            r.errors.append(
                f"{cid}: held by {held[cid]} procedures, expected one (a cause nobody holds is undiagnosable)"
            )
    for pid, p in w.procedures.items():
        for intent in p["entry_when"]["intents"]:
            if not w.causes_for(pid, intent):
                r.errors.append(f"{pid}: no cause can be drawn for intent {intent}")


def _reachability(r: Report, w: World) -> None:
    """Can each cause be fixed, can each discriminator be asked, can each cause be told from the others."""
    for pid, p in w.procedures.items():
        # An unknown action is reported by _procedures; the checks here go on without it.
        available = {a for a in w.procedure_actions(pid) if a in w.actions}
        askable = {w.actions[a]["elicits"] for a in available if w.actions[a].get("elicits")}
        for cid in p["hypotheses"]:
            if not any(w.effect(aid, cid) == "fixes" for aid in available):
                r.errors.append(
                    f"{pid}: no action in the procedure fixes {cid}, so the best outcome is unreachable"
                )
            for mid, prob in w.cause_manifestations[cid].items():
                m = w.manifestations[mid]
                if prob > 0 and m.get("discriminating") and mid not in askable:
                    r.errors.append(
                        f"{pid}: {cid} has discriminator {mid} that no action in the procedure elicits"
                    )

        # Separable by something: a question the procedure can ask, or the way the call opens.
        for cid in p["hypotheses"]:
            own = w.cause_manifestations[cid]
            rivals = [
                o
                for o in p["hypotheses"]
                if o != cid
                and set(w.causes[o].get("intents") or p["entry_when"]["intents"])
                & set(w.causes[cid].get("intents") or p["entry_when"]["intents"])
            ]
            if not rivals:
                continue
            for other in rivals:
                theirs = w.cause_manifestations[other]
                opens_differently = {
                    m for m, v in own.items() if v >= 0.9 and w.manifestations[m].get("presenting")
                } != {m for m, v in theirs.items() if v >= 0.9 and w.manifestations[m].get("presenting")}
                asks_differently = any(abs(own.get(m, 0.0) - theirs.get(m, 0.0)) > 0.25 for m in askable)
                if not (opens_differently or asks_differently):
                    r.warnings.append(
                        f"{pid}: {cid} cannot be told from {other} by anything the procedure can ask or hear"
                    )
                    break

        # A policy's gate must be satisfiable before the thing it gates.
        for stage in p["stages"]:
            gates = [(stage.get("requires_policy"), stage["id"], None)]
            gates += [
                (i.get("requires_policy"), stage["id"], i["id"])
                for i in stage["actions"]
                if isinstance(i, dict)
            ]
            for gate, sid, aid in gates:
                if not gate or gate not in w.policies:
                    continue
                # A stage's gate needs a satisfier in an earlier stage; an action's, in this stage or an earlier one.
                before = set(w.procedure_actions(pid, upto_stage=sid if aid is None else _next_stage(p, sid)))
                if not set(w.policies[gate]["satisfied_by"]) & before:
                    where = f"{sid}/{aid}" if aid else sid
                    r.errors.append(f"{pid}/{where}: gate {gate} cannot be satisfied by any earlier action")


def _next_stage(p: dict, sid: str) -> str | None:
    ids = [s["id"] for s in p["stages"]]
    i = ids.index(sid)
    return ids[i + 1] if i + 1 < len(ids) else None


def _policies(r: Report, w: World) -> None:
    used = {
        gate
        for p in w.procedures.values()
        for s in p["stages"]
        for gate in [
            s.get("requires_policy"),
            *[i.get("requires_policy") for i in s["actions"] if isinstance(i, dict)],
        ]
        if gate
    }
    for pol_id, pol in w.policies.items():
        for aid in pol["satisfied_by"]:
            if aid not in w.actions:
                r.errors.append(f"{pol_id}: satisfied_by unknown action {aid}")
        for key in pol.get("applies_when", {}):
            if key not in ROW_CONDITIONS:
                r.errors.append(f"{pol_id}: applies_when key {key} is not a row condition")
        if pol["severity"] not in SEVERITY:
            r.errors.append(f"{pol_id}: bad severity {pol['severity']!r}")
        if not 0.0 < pol["target_compliance"] < 1.0:
            r.errors.append(
                f"{pol_id}: target_compliance {pol['target_compliance']} should be strictly between 0 and 1"
            )
        if pol_id not in used:
            r.warnings.append(f"{pol_id}: no stage or action is gated by it")


def _outcomes(r: Report, w: World) -> None:
    committing = [a for a in w.actions.values() if a.get("commits")]
    committing_types = {a["type"] for a in committing}
    cost_possible = any(a.get("incurs_cost") for a in committing)
    # An unlisted pair is no-effect, so it is always possible.
    efficacies = {v for effects in w.efficacy.values() for v in effects.values()} | {"no-effect"}
    if not w.outcomes:
        r.errors.append("outcomes.yaml: no outcomes defined")
        return
    if w.outcomes[-1].get("requires"):
        r.errors.append("outcomes.yaml: the last outcome must be an unconditional fallback")
    seen = set()
    for o in w.outcomes:
        oid = o["id"]
        if oid in seen:
            r.errors.append(f"{oid}: duplicate outcome id")
        seen.add(oid)
        if o["favorability"] not in FAVORABILITY:
            r.errors.append(f"{oid}: bad favorability {o['favorability']!r}")
        req = o.get("requires") or {}
        for key, value in req.items():
            if key not in OUTCOME_KEYS:
                r.errors.append(f"{oid}: unknown requires key {key}")
            elif key == "abandon_reason" and value not in ABANDON_REASONS:
                r.errors.append(f"{oid}: bad abandon_reason {value!r}")
            elif key == "procedure":
                for pid in value:
                    if pid not in w.procedures:
                        r.errors.append(f"{oid}: unknown procedure {pid}")
            elif key == "efficacy":
                for v in value:
                    if v not in EFFICACY:
                        r.errors.append(f"{oid}: bad efficacy {v!r}")
                    elif v not in efficacies:
                        r.warnings.append(f"{oid}: requires efficacy {v!r}, which no efficacy row ever gives")
            elif key == "committed_action_type" and value not in committing_types:
                r.errors.append(f"{oid}: no committing action has type {value!r}")
            elif key == "committed_incurs_cost" and value and not cost_possible:
                r.errors.append(f"{oid}: no committing action incurs a cost")
        if o.get("triggers_recurrence"):
            if not 0.0 < o.get("recurrence_probability", 0) <= 1.0:
                r.errors.append(f"{oid}: triggers_recurrence needs recurrence_probability in (0, 1]")
            d = o.get("recurrence_delay_days") or {}
            if not 0 <= d.get("min", -1) <= d.get("max", -2):
                r.errors.append(f"{oid}: recurrence_delay_days needs 0 <= min <= max")
    if not any(o.get("triggers_recurrence") for o in w.outcomes):
        r.warnings.append("no outcome triggers recurrence, so there will be no repeat callers")
    for key in ("partial_offer_accept", "makes_worse_escalates"):
        if not 0.0 <= w.acceptance.get(key, -1) <= 1.0:
            r.errors.append(f"outcomes.acceptance.{key} missing or outside 0..1")
    fav = w.targets.get("by_favorability", {})
    if fav and abs(sum(fav.values()) - 1.0) > EPS:
        r.errors.append(f"outcomes.targets.by_favorability sums to {sum(fav.values()):.3f}, expected 1.0")
    r.notes.append(
        "whether each outcome is reachable by a sampled walk is checked by the sampler's --dry-run"
    )


def _distributions(r: Report, w: World, raw: dict) -> None:
    total = sum(d["share"] for d in w.domains.values())
    if abs(total - 1.0) > EPS:
        r.errors.append(f"domains: shares sum to {total:.3f}, expected 1.0")
    for did in w.domains:
        rates = [c["base_rate"] for c in w.causes.values() if c["domain"] == did]
        if not rates:
            r.errors.append(f"{did}: no causes")
        elif abs(sum(rates) - 1.0) > EPS:
            r.errors.append(f"{did}: cause base_rates sum to {sum(rates):.3f}, expected 1.0")
    for name, group in (("customers", raw["customers"]["archetypes"]), ("reps", raw["reps"]["archetypes"])):
        total = sum(a["share"] for a in group)
        if abs(total - 1.0) > EPS:
            r.errors.append(f"{name}.archetypes shares sum to {total:.3f}, expected 1.0")
    for aid, a in w.customer_archetypes.items():
        for key in ("attentiveness", "forthcoming", "patience", "p_misattribute", "escalation_propensity"):
            if not 0.0 <= a[key] <= 1.0:
                r.errors.append(f"{aid}: {key} {a[key]} outside 0..1")
    for aid, a in w.rep_archetypes.items():
        for key in REP_FIELDS:
            # An archetype shifts probabilities and never dictates: none is 0 or 1.
            if not 0.0 < a[key] < 1.0:
                r.errors.append(f"{aid}: {key} {a[key]} must be strictly between 0 and 1")
    for site, mods in w.reps["sites"].items():
        if site not in SITES:
            r.errors.append(f"reps.sites: unknown site {site}")
        for key in mods:
            if key not in REP_FIELDS and key != "queue_abandon":
                r.errors.append(f"reps.sites[{site}]: unknown modifier {key}")
    for key, value in w.mechanics.items():
        if key in {"max_asks", "handle_min_sec", "handle_sec_per_event", "match_attempts", "callback_days"}:
            if not isinstance(value, int) or value < 1:
                r.errors.append(f"mechanics.{key} must be a positive integer")
        elif not 0.0 <= value <= 1.0:
            r.errors.append(f"mechanics.{key} {value} outside 0..1")
    if set(w.site_share) != SITES or abs(sum(w.site_share.values()) - 1.0) > EPS:
        r.errors.append("reps.site_share must name every site and sum to 1.0")
    if not 0.0 < w.authenticated_share < 1.0:
        r.errors.append("customers.authenticated_share must be strictly between 0 and 1")
    if not 0.0 <= w.reps.get("queue_abandon_default", -1) <= 1.0:
        r.errors.append("reps.queue_abandon_default missing or outside 0..1")


def _shape(r: Report, w: World) -> None:
    """What is being built: the structure a process graph should be able to recover, and the control that has none."""
    disc = [m for m in w.manifestations.values() if m.get("discriminating")]
    hidden = [m for m in disc if m["volunteer"] <= 0.30]
    r.notes.append(
        f"{len(disc)} discriminating manifestations, {len(hidden)} of them volunteered at 0.30 or less "
        "(perceived, usually unsaid: the ones a question has to retrieve)"
    )
    savable = [
        cid
        for cid in w.procedures["PROC-RETENTION"]["hypotheses"]
        if w.effect("ACT-PROCESS-CLOSURE", cid) != "fixes"
    ]
    r.notes.append(
        f"retention: {len(savable)} of {len(w.procedures['PROC-RETENTION']['hypotheses'])} causes are savable, "
        f"{sum(w.causes[c]['base_rate'] for c in savable):.0%} of closure calls"
    )
    # The control family must have nothing to find.
    for cid, c in w.causes.items():
        if c["domain"] != "DOM-SERVICING":
            continue
        if c.get("confusable_with"):
            r.errors.append(f"{cid}: the control family must not be confusable")
        if any(w.manifestations[m["id"]].get("discriminating") for m in c["manifestations"]):
            r.errors.append(f"{cid}: the control family must have nothing discriminating")
    needing = [cid for cid, c in w.causes.items() if c.get("needs")]
    r.notes.append(
        f"{len(needing)} causes need a real fee or card purchase in the warehouse before they can be drawn"
    )
