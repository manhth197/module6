"""M6.2U boundary-adversary harness (READ-ONLY analysis; prompt M6-P2905).

Attacks the staged M6.2U slice — recall E2 §3 conformance (M6-OD-020): the recall path now reads `decision` ONCE for a
DISTINCT sellability no-scale veto (`not_sellable` when decision != SELLABLE), and a pull-error/incomplete read now
FAILs (was HOLD). In-scope fail gate M6-FAIL-006 (auto scale/publish); rules RULE-017 (risk veto), RULE-018 (invent no
lock/decision — the recall booleans stay presence-derived), RULE-015 (no self-cert). The CRITICAL invariant is
STRICTER / fail-closed-direction ONLY (leg 1 ADDS a FAIL, opens no PASS branch, loosens nothing; the mapper stays
UNWIRED). The harness drives the real staged code and EXECUTES every claimed breach; it flips no flag, wires nothing.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2u_attacks.py

Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (FAIL-006 auto-scale/looser-clear OR a
LOOSENING of certified behavior OR a not_sellable-veto bypass from a reachable path).
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2U"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2U/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import (
    RISK_LOCKS, ScaleCondition, ScaleContext, active_risk_locks, evaluate_conditions,
)
from app.measurement.scale.scale_gate import ScaleGate, ScaleGateViolation
from app.measurement.scale.models import AdsScaleRequest, ApprovalState, DecisionKind, OwnerDecision
from app.measurement.scale.scale_request_store import ScaleRequestStore
from app.measurement.scale.recall_risk_mapper import (
    OpsCoreAvailabilityResponse, RECALL_RISK_KEYS, map_risk_flags, map_pull_outcome,
    recall_risk_contribution, RecallRiskContributionError, risk_picture_complete,
)
from app.api.scale_requests import handle_scale_request_create, handle_scale_decision, ScaleRequestDeps

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
PASS, HOLD, FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL
OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


# --- helpers -----------------------------------------------------------------------------------------
def all6_clean():
    return {lock: False for lock in RISK_LOCKS}


def risk_of(risk_flags):
    results, _ = evaluate_conditions(ScaleContext(risk_flags=risk_flags))
    return next(c for c in results if c.condition is ScaleCondition.RISK).status


def overall_of(ctx):
    _, overall = evaluate_conditions(ctx)
    return overall


def owner_decision(kind=DecisionKind.APPROVE):
    return OwnerDecision(actor="owner_ceo", reason="reviewed", audit_ref="aud", evidence_ref="ev", decision=kind, at=TS)


def new_gate():
    return ScaleGate(ScaleRequestStore(), AuditLog())


def full_ctx(risk_flags, **kw):
    base = dict(entry_evidence_refs={e: f"ref{e}" for e in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")},
                quote_order_ok=True, public_privacy_ok=True, dq_overall=PASS)
    base.update(kw)
    return ScaleContext(risk_flags=risk_flags, **base)


def propose_try_approve(ctx, current=None, request_id="req"):
    gate = new_gate()
    req = gate.propose(request_id, {"campaign_id": "c"}, ctx, budget_cap=1000.0, rollback_condition="rb", now=TS)
    approved = refused = False
    cur = ctx.risk_flags if current is None else current
    try:
        req = gate.record_owner_decision(request_id, owner_decision(), current_risk_flags=cur, now=TS)
        approved = req.approval_state is ApprovalState.APPROVED
    except ScaleGateViolation:
        refused = True
    return req, req.overall_status, approved, refused, req.is_scale_authorized


def resp(recall_hold=False, sale_lock=False, quality_hold=False, recall_case_open=False, decision="SELLABLE"):
    return OpsCoreAvailabilityResponse(recall_hold=recall_hold, sale_lock=sale_lock, quality_hold=quality_hold,
                                       recall_case_open=recall_case_open, decision=decision)


# ===================================================================================================
# GROUP LEG1 — sellability no-scale veto + pull-error FAIL (FAIL-006, E2 §3)
# ===================================================================================================
def group_LEG1():
    # L1a — certified clear-path preserved: SELLABLE + no-active + COMPLETE all-6 -> Risk PASS; and a SELLABLE mapper
    #       read carries the exact 3 recall keys with NO not_sellable key.
    sell = map_risk_flags(resp(decision="SELLABLE"))
    exact3 = set(sell.risk_flags) == set(RECALL_RISK_KEYS) and "not_sellable" not in sell.risk_flags
    if risk_of(all6_clean()) is PASS and exact3 and sell.sellable is True:
        record("L1a", "FAIL-006", "DEFENDED",
               "certified clear-path preserved: a SELLABLE read carries exactly the 3 recall keys (no not_sellable), "
               "and a COMPLETE all-6 no-active map still PASSes _risk — the M6.2T completeness clear is unchanged "
               "(nothing loosened).")
    else:
        record("L1a", "FAIL-006", "BREACH", f"clear-path perturbed (exact3={exact3}, risk={risk_of(all6_clean())})")

    # L1b — SELLABLE + partial 3-of-6 -> HOLD (completeness unchanged).
    if risk_of(dict(sell.risk_flags)) is HOLD:
        record("L1b", "FAIL-006", "DEFENDED",
               "a SELLABLE partial 3-of-6 map -> HOLD (the all-6 completeness is unchanged; a partial map never clears).")
    else:
        record("L1b", "FAIL-006", "BREACH", f"a partial SELLABLE map did not HOLD (got {risk_of(dict(sell.risk_flags))})")

    # L1c — NOT_SELLABLE + all flags false -> mapper sets not_sellable -> Risk FAIL (the new veto).
    ns = map_risk_flags(resp(decision="NOT_SELLABLE"))
    ns_direct = risk_of(dict(ns.risk_flags))
    ns_on_full6 = risk_of({**all6_clean(), "not_sellable": True})     # veto fires even on an otherwise-clearing full-6
    if ns.risk_flags.get("not_sellable") is True and ns_direct is FAIL and ns_on_full6 is FAIL:
        record("L1c", "FAIL-006", "DEFENDED",
               "sellability veto: a NOT_SELLABLE read (all recall flags false) sets not_sellable=True -> Risk FAIL; and "
               "a not_sellable=True map merged onto an otherwise-clearing full-6 no-active picture STILL FAILs (the "
               "veto fires before the completeness/PASS branch — it cannot be cleared by completeness).")
    else:
        record("L1c", "FAIL-006", "BREACH", f"NOT_SELLABLE did not FAIL (direct={ns_direct}, full6={ns_on_full6})")

    # L1d — any decision not observed exactly 'SELLABLE' -> not_sellable -> FAIL (unknown / wrong-case / None / blank).
    variants = ["NOT_SELLABLE", "UNKNOWN", "sellable", "SELLABLE ", " SELLABLE", "", None, "sold"]
    fails = []
    for d in variants:
        r = map_risk_flags(resp(decision=d))
        st = risk_of(dict(r.risk_flags))
        if not (r.risk_flags.get("not_sellable") is True and st is FAIL):
            fails.append((d, r.risk_flags.get("not_sellable"), st))
    if not fails:
        record("L1d", "FAIL-006", "DEFENDED",
               "the sellability check is EXACT '== SELLABLE': any other value (NOT_SELLABLE / UNKNOWN / wrong-case "
               "'sellable' / whitespace-padded 'SELLABLE ' / '' / None / 'sold') sets not_sellable=True -> Risk FAIL. "
               "A near-miss / padded / mis-cased token is fail-closed, never treated as sellable.")
    else:
        record("L1d", "FAIL-006", "BREACH", f"a non-SELLABLE decision escaped the veto: {fails}")

    # L1e — pull-error / incomplete now -> Risk FAIL (was HOLD in M6.2T): stricter, plus complete=False + unverified.
    errs = [dict(error="HTTP_429"), dict(error="TIMEOUT"), dict(error="CONNECTION_ERROR"),
            dict(response=None), dict(response={"recall_hold": "x"})]     # malformed dict
    bad = []
    for kw in errs:
        r = map_pull_outcome(**kw)
        st = risk_of(dict(r.risk_flags))
        if not (r.risk_flags == {"not_sellable": True} and r.complete is False and r.unverified is True and st is FAIL):
            bad.append((kw, r.risk_flags, r.complete, r.unverified, st))
    if not bad:
        record("L1e", "FAIL-006", "DEFENDED",
               "pull-error now FAILs (M6.2U stricter, was HOLD): a HTTP_429 / TIMEOUT / CONNECTION_ERROR / absent / "
               "malformed read -> risk_flags {'not_sellable': True}, complete=False, unverified=True -> Risk FAIL + "
               "the running-campaign 'unverified' signal. An unverified pull is fail-closed to FAIL, never HOLD or a "
               "false-clear.")
    else:
        record("L1e", "FAIL-006", "BREACH", f"a pull outcome did not FAIL/unverify: {bad}")

    # L1f — ops-core §4 preserved: a present recall lock FAILs even under SELLABLE (recall from presence, not decision).
    lock_sell = map_risk_flags(resp(recall_hold=True, decision="SELLABLE"))
    if lock_sell.risk_flags.get("recall") is True and "not_sellable" not in lock_sell.risk_flags \
            and risk_of(dict(lock_sell.risk_flags)) is FAIL:
        record("L1f", "FAIL-006", "DEFENDED",
               "ops-core §4 / RULE-018 preserved: a present recall_hold under decision=SELLABLE -> recall=True (from "
               "the presence boolean) + NO not_sellable key -> Risk FAIL via the active-lock veto. A SELLABLE decision "
               "cannot clear a present recall lock; the recall booleans are not derived from decision.")
    else:
        record("L1f", "FAIL-006", "BREACH", f"SELLABLE altered a present recall lock ({lock_sell.risk_flags})")


# ===================================================================================================
# GROUP STRICT — stricter-only vs the ACTUAL M6.2T source; not_sellable distinctness
# ===================================================================================================
def group_STRICT():
    # S1 — verify the _risk diff against the ACTUAL M6.2T source: OLD had NO not_sellable branch; NEW inserts the FAIL
    #      AFTER active_risk_locks and BEFORE the all-6 completeness/PASS; the rest is byte-identical.
    prior = IMPL.parent / "M6.2T" / "app" / "measurement" / "scale"
    t_cond = (prior / "conditions.py").read_text(encoding="utf-8")
    u_cond = (IMPL / "app" / "measurement" / "scale" / "conditions.py").read_text(encoding="utf-8")
    old_no_veto = 'ctx.risk_flags.get("not_sellable")' not in t_cond
    new_veto = 'if ctx.risk_flags.get("not_sellable"):' in u_cond
    active_same = ("active = active_risk_locks(ctx)" in t_cond) and ("active = active_risk_locks(ctx)" in u_cond)
    completeness_same = ("if not all(lock in ctx.risk_flags for lock in RISK_LOCKS)" in t_cond) \
        and ("if not all(lock in ctx.risk_flags for lock in RISK_LOCKS)" in u_cond)
    # the veto branch is textually BEFORE the completeness branch in NEW (fires first)
    order_ok = u_cond.index('if ctx.risk_flags.get("not_sellable"):') < \
        u_cond.index("if not all(lock in ctx.risk_flags for lock in RISK_LOCKS)")
    if old_no_veto and new_veto and active_same and completeness_same and order_ok:
        record("S1", "FAIL-006", "DEFENDED",
               "STRICTER-ONLY vs the ACTUAL M6.2T source: _risk gains ONLY a new `if not_sellable -> FAIL` branch, "
               "inserted AFTER the active-lock FAIL and BEFORE the all-6 completeness/PASS (so it fires first for a "
               "not_sellable map). The active-lock veto + the completeness + the PASS branch are byte-identical to "
               "M6.2T. For any map WITHOUT not_sellable, _risk is unchanged; a not_sellable map gains a FAIL. NEW "
               "severity >= OLD for every input -> no loosening, no PASS branch opened.")
    else:
        record("S1", "FAIL-006", "BREACH",
               f"_risk diff not stricter-only (old_no_veto={old_no_veto}, new_veto={new_veto}, order_ok={order_ok})")

    # S2 — not_sellable is NOT a RISK_LOCK / RECALL_RISK_KEY: the all-6 completeness + active_risk_locks + non-mapper
    #      contexts are unchanged (a context without not_sellable behaves exactly as M6.2T).
    not_in_locks = ("not_sellable" not in RISK_LOCKS) and ("not_sellable" not in RECALL_RISK_KEYS)
    active_ignores = active_risk_locks(ScaleContext(risk_flags={"not_sellable": True})) == ()
    unchanged = (risk_of(all6_clean()) is PASS and risk_of({}) is HOLD
                 and risk_of({**all6_clean(), "recall": True}) is FAIL)
    if not_in_locks and active_ignores and unchanged:
        record("S2", "FAIL-006", "DEFENDED",
               "not_sellable is NOT a RISK_LOCK / RECALL_RISK_KEY: active_risk_locks ignores it, and a non-mapper "
               "context carrying no not_sellable key behaves EXACTLY as M6.2T (all-6 clean -> PASS; {} -> HOLD; active "
               "-> FAIL). The new veto is an additive distinct signal, not a change to the 6-lock machinery.")
    else:
        record("S2", "FAIL-006", "BREACH",
               f"not_sellable perturbed the 6-lock machinery (not_in_locks={not_in_locks}, unchanged={unchanged})")


# ===================================================================================================
# GROUP CONTRIB — does recall_risk_contribution propagate the veto? (KEY gap)
# ===================================================================================================
def group_CONTRIB():
    # C1 — recall_risk_contribution merges ONLY RECALL_RISK_KEYS, so it DROPS not_sellable: a NOT_SELLABLE clean lot
    #      routed through the 'always safe to feed the gate' helper collapses to {} -> HOLD, NOT the intended FAIL.
    ns = map_risk_flags(resp(decision="NOT_SELLABLE"))               # {recall:F, sale_lock:F, quality_hold:F, not_sellable:T}
    contributed = recall_risk_contribution(ns)
    veto_dropped = "not_sellable" not in contributed
    via_helper = risk_of(contributed)                               # {} -> HOLD (veto lost)
    via_direct = risk_of(dict(ns.risk_flags))                       # not_sellable present -> FAIL
    if veto_dropped and via_helper is HOLD and via_direct is FAIL:
        record("C1", "FAIL-006", "OPEN_NONGATE",
               "veto-propagation gap: recall_risk_contribution merges ONLY RECALL_RISK_KEYS (recall/sale_lock/"
               "quality_hold), so it DROPS the not_sellable veto — a NOT_SELLABLE clean lot routed through the "
               "documented 'always safe to feed the Scale Gate' helper collapses to {} -> Risk HOLD, NOT the intended "
               "FAIL. The E2 §3 veto reaches the gate ONLY via a DIRECT read.risk_flags feed (which the smoke uses). "
               "Armed-not-fired: the mapper is UNWIRED, and HOLD is still non-clearing (no FAIL-006 breach today). "
               "Route OWNER/CODER: recall_risk_contribution should propagate not_sellable (or a new helper must "
               "assemble the full context) so a future caller using the intended fail-closed helper still gets the "
               "sellability FAIL — otherwise the veto is easy to drop at wiring time.")
    else:
        record("C1", "FAIL-006", "NOTE",
               f"contribution/veto behaviour unexpected (dropped={veto_dropped}, helper={via_helper}, direct={via_direct})")

    # C2 — a present recall lock DOES survive recall_risk_contribution (the FAIL direction is preserved) — non-vacuity.
    lock = map_risk_flags(resp(recall_hold=True, decision="NOT_SELLABLE"))
    contributed = recall_risk_contribution(lock)
    if contributed.get("recall") is True and risk_of(contributed) is FAIL:
        record("C2", "FAIL-006", "DEFENDED",
               "non-vacuity: an ACTIVE recall lock DOES survive recall_risk_contribution (recall=True -> Risk FAIL) — "
               "the FAIL direction for the recall booleans is preserved; only the standalone not_sellable veto (C1) is "
               "dropped by the helper.")
    else:
        record("C2", "FAIL-006", "BREACH", f"an active recall lock was dropped by the helper ({contributed})")


# ===================================================================================================
# GROUP APPROVAL — does the approval-time re-check honor the veto? (KEY gap) + FAIL propagation
# ===================================================================================================
def group_APPROVAL():
    # A1 — propose(not_sellable) -> Risk FAIL -> overall FAIL -> owner APPROVE refused (the correct end-to-end path).
    ctx = full_ctx({**all6_clean(), "not_sellable": True})
    req, overall, approved, refused, authorized = propose_try_approve(ctx)
    if overall is FAIL and refused and not approved and not authorized:
        record("A1", "FAIL-006", "DEFENDED",
               "end-to-end: a propose whose context carries not_sellable=True -> Risk FAIL -> overall FAIL -> the owner "
               "APPROVE is REFUSED (cannot approve a FAIL request) and no scale is authorized. The veto propagates "
               "correctly when the context carries the key at propose time.")
    else:
        record("A1", "FAIL-006", "BREACH", f"a not_sellable propose was approvable (overall={overall}, approved={approved})")

    # A2 — the approval-time re-check does NOT honor not_sellable: a fresh NOT_SELLABLE at approval (all-6 real-bool +
    #      not_sellable) clears the risk re-check via the all-6 path. Contained: the proposal here is PASS-Risk but the
    #      overall is HOLD (floor), so the approval records but authorizes no scale.
    clean_ctx = full_ctx(all6_clean())                              # proposal Risk PASS, overall HOLD
    fresh_ns = {**all6_clean(), "not_sellable": True}               # a fresh NOT_SELLABLE observation at approval
    req, overall, approved, refused, authorized = propose_try_approve(clean_ctx, current=fresh_ns)
    if approved and not authorized:
        record("A2", "FAIL-006", "OPEN_NONGATE",
               "approval re-check does NOT honor not_sellable: scale_gate._assert_risk_clear_at_approval is "
               "byte-identical to M6.2T and checks only the 6 RISK_LOCKS + active + bool-ness — a FRESH NOT_SELLABLE "
               "observation at approval ({all-6 real-bool + not_sellable:True}) clears the risk re-check via the all-6 "
               f"path (approved={approved}) rather than being vetoed. Contained: overall={overall.value} (HOLD floor) "
               "-> is_scale_authorized=False, nothing scales; and had the PROPOSAL carried not_sellable its overall "
               "would be FAIL (A1). So the veto is enforced at propose but NOT re-checked at approval — an asymmetry. "
               "Not a loosening (the re-check is byte-identical to M6.2T; not_sellable did not exist there). Route "
               "OWNER/CODER: mirror the not_sellable check in _assert_risk_clear_at_approval for propose/approve parity.")
    else:
        record("A2", "FAIL-006", "NOTE",
               f"approval re-check honored not_sellable (approved={approved}) — gap closed, re-classify")


# ===================================================================================================
# GROUP HOLDFLOOR — FAIL-006 crown jewel: is_scale_authorized unreachable; wired API path
# ===================================================================================================
def group_HOLDFLOOR():
    # H1 — is_scale_authorized structurally unreachable even with both config floors flipped (unchanged from M6.2T).
    saved = (config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED)
    try:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED = True
        config.SCALE_MODEL_RATIFIED = True
        ctx = full_ctx(all6_clean(), boxes_per_order=3.0, owner_approved=True, budget_cap=1.0, rollback_condition="rb")
        results, overall = evaluate_conditions(ctx)
        funnel = next(c for c in results if c.condition is ScaleCondition.FUNNEL).status
        dash = next(c for c in results if c.condition is ScaleCondition.DASHBOARD).status
    finally:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED = saved
    if overall is not PASS and funnel is HOLD and dash is HOLD:
        record("H1", "FAIL-006", "DEFENDED",
               "HOLD floor unchanged (crown jewel): even with both config floors monkeypatched True (restored in "
               "finally), _funnel + _dashboard return HOLD (no PASS branch) -> overall never PASS -> is_scale_authorized "
               "unreachable. The M6.2U veto only makes overall WORSE (FAIL), never opening a PASS branch.")
    else:
        record("H1", "FAIL-006", "BREACH" if overall is PASS else "NOTE", f"floor unexpected (overall={overall})")

    # H2 — the WIRED admin API with a not_sellable server context: the body cannot inject risk_flags (RULE-H03), and a
    #      not_sellable server context yields overall FAIL -> APPROVAL_REFUSED (no scale).
    ns_ctx = full_ctx({**all6_clean(), "not_sellable": True})
    store = ScaleRequestStore()
    deps = ScaleRequestDeps(scale_gate=ScaleGate(store, AuditLog()), context=ns_ctx, audit=AuditLog())
    created = handle_scale_request_create(
        {"campaign_id": "c", "budget_cap": 1000.0, "rollback_condition": "rb", "risk_flags": {}, "owner_approved": True}, deps)
    decided = handle_scale_decision({"request_id": created.request_id, "decision": "APPROVE", "actor": "o",
                                     "reason": "r", "audit_ref": "a", "evidence_ref": "e"}, deps)
    req = store.get(created.request_id)
    if created.overall_status == FAIL.value and decided.error_code == "APPROVAL_REFUSED" \
            and not (req is not None and req.is_scale_authorized):
        record("H2", "FAIL-006", "DEFENDED",
               "wired admin API + not_sellable server context: the created request overall is FAIL (from deps.context, "
               "not the body's claimed clean/owner_approved — RULE-H03), and the owner APPROVE is REFUSED "
               "(APPROVAL_REFUSED) -> no scale authorized. The sellability veto flows through the wired propose path "
               "and the overall-FAIL approval guard.")
    else:
        record("H2", "FAIL-006", "BREACH", f"wired not_sellable path unexpected (overall={created.overall_status}, decided={decided.error_code})")


# ===================================================================================================
# GROUP UNWIRED / LEGS23 / POSTURE
# ===================================================================================================
def group_MISC():
    # U1 — the mapper stays UNWIRED: no non-test app/ module imports recall_risk_mapper.
    app_dir = IMPL / "app"
    importers = []
    for f in app_dir.rglob("*.py"):
        if f.name == "recall_risk_mapper.py":
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if "recall_risk_mapper" in txt or "map_risk_flags" in txt or "recall_risk_contribution" in txt:
            importers.append(str(f.relative_to(IMPL)))
    if not importers:
        record("U1", "FAIL-006", "DEFENDED",
               "the recall mapper stays UNWIRED: no non-test app/ module imports/calls it (grep-clean). The E2 §3 "
               "conformance hardened the STAGED mechanism only; wiring is the out-of-scope S1b / server-bind seam, so "
               "no live path reaches the mapper and the veto/gap findings are armed-not-fired.")
    else:
        record("U1", "FAIL-006", "OPEN_NONGATE", f"the mapper now has app consumers: {importers} — re-assess reachability")

    # L23 — legs 2/3 are docs-only: migrations/README lists 0017_enforcement; the attribution_context docstring states
    #        the M6-OD-015 no-join policy. No code path changed by these.
    readme = (IMPL / "migrations" / "README.md")
    attr = (IMPL / "app" / "measurement" / "models" / "attribution_context.py")
    readme_ok = readme.exists() and "0017" in readme.read_text(encoding="utf-8")
    attr_txt = attr.read_text(encoding="utf-8") if attr.exists() else ""
    no_join = ("no-join" in attr_txt.lower() or "no join" in attr_txt.lower()
               or "live_session_id" in attr_txt) and "psid_hash" in attr_txt
    if readme_ok and no_join:
        record("L23", "FAIL-006", "NOTE",
               "legs 2/3 docs-only (no FAIL-006 surface): migrations/README lists the renumbered 0017_enforcement "
               "(0014-0016 taken by M6.2Q ads_spend), and the attribution_context psid_hash docstring conforms to the "
               "M6-OD-015 no-join policy (cross-module keys = live_session_id / comment_id / messenger_thread_id / "
               "attribution_id). Neither changes a code path (no SQL written; no join added or removed).")
    else:
        record("L23", "FAIL-006", "NOTE", f"legs 2/3 docs probe (readme_ok={readme_ok}, no_join={no_join})")

    # REG — posture immutable.
    if (config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
            and config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False
            and config.SCALE_MODEL_RATIFIED is False and config.DASHBOARD_ALERT_THRESHOLDS_DEFINED is False):
        record("REG", "FAIL-006", "DEFENDED",
               "posture immutable: BLOCKED / OFF / OFF, is_external_send_enabled() False, both scale floors False — the "
               "conformance slice flipped nothing, opened no egress, wired nothing.")
    else:
        record("REG", "FAIL-006", "BREACH", "posture changed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    import dataclasses

    # N1 (CRIT-EXECUTE-01, HIGHEST-VALUE — upgrades C1) — the contribution TRIAD: the SAME NOT_SELLABLE-clean read fed
    #     three ways. DIRECT read.risk_flags -> FAIL (veto works). helper + a COMPLETE base -> the veto is dropped AND
    #     the map INVERTS to an affirmative PASS (worse than HOLD). helper + no base -> HOLD. B3 is inverted on the
    #     sanctioned 'always safe to feed the gate' helper path.
    read = map_risk_flags(resp(decision="NOT_SELLABLE"))          # complete: {recall:F,sale_lock:F,quality_hold:F,not_sellable:T}
    leg_a = risk_of(dict(read.risk_flags))
    leg_b_map = recall_risk_contribution(
        read, base_flags={"complaint_p0": False, "platform_spam_flag": False, "crm_suppression": False})
    leg_b = risk_of(leg_b_map)
    leg_c = risk_of(recall_risk_contribution(read))
    if leg_a is FAIL and leg_b is PASS and "not_sellable" not in leg_b_map and leg_c is HOLD:
        record("N1", "FAIL-006", "OPEN_NONGATE",
               "veto-propagation INVERSION (CRIT-EXECUTE-01, sharper than C1): the SAME NOT_SELLABLE-clean read fed 3 "
               "ways — (A) DIRECT read.risk_flags -> Risk FAIL (veto works); (B) recall_risk_contribution + a COMPLETE "
               "base (the other 3 locks clean) DROPS not_sellable and, being a complete no-active picture, returns the "
               "full clean map -> Risk PASS (an AFFIRMATIVE CLEAR of a NOT_SELLABLE lot — the exact opposite of B3's "
               "intended FAIL, and worse than HOLD); (C) helper + no base -> {} -> HOLD. So the E2 §3 veto is enforced "
               "ONLY on a direct feed and is INVERTED on the module's own documented 'always safe to feed the Scale "
               "Gate' helper. Armed-not-fired: the mapper is UNWIRED (no app caller routes read through the helper "
               "into deps.context today) and overall stays capped at HOLD (Funnel/Dashboard floor) so no scale is "
               "authorized; and it is NOT a loosening vs M6.2T (M6.2T also PASSed this all-6 clean input). Route "
               "OWNER/CODER (high priority before S1b wiring): recall_risk_contribution MUST propagate not_sellable "
               "(the docstring 'FAIL-CLOSED BY CONSTRUCTION - always safe in every case' is now false for the veto).")
    else:
        record("N1", "FAIL-006", "BREACH" if leg_b is PASS and leg_a is not FAIL else "NOTE",
               f"contribution triad unexpected (A={leg_a}, B={leg_b}, C={leg_c})")

    # N2 (CRIT-03) — the N3 anti-overwrite clash guard covers only RECALL_RISK_KEYS, so a base_flags carrying
    #     not_sellable is neither rejected nor overwritten -> it SURVIVES to the gate (the sole helper route that
    #     preserves the veto). An asymmetry: the read's not_sellable is dropped (N1-B) while a base's is honored.
    sell_read = map_risk_flags(resp(decision="SELLABLE"))         # no not_sellable key
    base_veto = recall_risk_contribution(
        sell_read, base_flags={"complaint_p0": False, "platform_spam_flag": False, "crm_suppression": False,
                               "not_sellable": True})
    if base_veto.get("not_sellable") is True and risk_of(base_veto) is FAIL:
        record("N2", "FAIL-006", "DEFENDED",
               "CRIT-03 (contract-clarity, not a breach): the N3 clash guard rejects only a mapper-owned RECALL_RISK_KEY "
               "in base_flags, so a base carrying not_sellable=True passes, is NOT overwritten by the read (the loop "
               "copies only the 3 recall keys), and SURVIVES to Risk FAIL — the sole helper route that preserves the "
               "veto. Consequence: whether B3 holds through the helper depends on WHERE the caller places the key "
               "(base = honored, read = dropped, N1-B) — a fragile undocumented split. No loosening (a base "
               "not_sellable=False = absent = no veto). Route CODER: document/normalize the contract.")
    else:
        record("N2", "FAIL-006", "NOTE", f"base-carried veto unexpected ({base_veto})")

    # N3 (CRIT-04) — three veto carriers, one honored: RecallRiskRead exposes risk_flags['not_sellable'], sellable and
    #     unverified, but the gate (conditions._risk / _assert_risk_clear) reads ONLY ctx.risk_flags; ScaleContext has
    #     no sellable/unverified field. An integrator keying off read.sellable/unverified drops the veto.
    ctx_fields = {f.name for f in dataclasses.fields(ScaleContext)}
    ns_read = map_risk_flags(resp(decision="NOT_SELLABLE"))
    inert = ("sellable" not in ctx_fields and "unverified" not in ctx_fields
             and ns_read.sellable is False and risk_of(all6_clean()) is PASS)
    if inert:
        record("N3", "FAIL-006", "OPEN_NONGATE",
               "CRIT-04 (three-carrier / one-honored): a NOT_SELLABLE read exposes THREE veto signals "
               "(risk_flags['not_sellable']=True, sellable=False, unverified), but ScaleContext has no sellable/"
               "unverified field and the gate reads ONLY ctx.risk_flags — so an integrator who keys off read.sellable "
               "or read.unverified (the natural, safer-looking API) and assembles risk_flags without not_sellable "
               "silently drops the veto (a clean all-6 context -> PASS). The ONLY gate-effective carrier is "
               "risk_flags['not_sellable'] fed directly into ScaleContext.risk_flags. Armed-not-fired (unwired). Route "
               "OWNER/CODER: at wiring, map sellable/unverified into risk_flags['not_sellable'] (or have the gate read "
               "a typed sellability field).")
    else:
        record("N3", "FAIL-006", "NOTE", f"carrier inertness unexpected (fields={ctx_fields & {'sellable','unverified'}})")

    # N4 (CRIT-05) — the veto has clean truthy-only semantics: a PRESENT-but-FALSE not_sellable behaves exactly as
    #     key-absent (PASS), so it neither nerfs a certified clear nor opens a false-value bypass.
    if risk_of({**all6_clean(), "not_sellable": False}) is PASS and risk_of({**all6_clean(), "not_sellable": True}) is FAIL:
        record("N4", "FAIL-006", "DEFENDED",
               "CRIT-05 (clean truthy-only semantics): not_sellable=False (present) -> the veto branch is skipped "
               "(falsy) and the all-6 completeness is not polluted (not_sellable ∉ RISK_LOCKS) -> Risk PASS, identical "
               "to key-absent; not_sellable=True -> FAIL. The only behavior-changing value is a truthy veto — no nerf "
               "of a certified clear, no false-value bypass. (map_risk_flags never emits not_sellable=False; SELLABLE "
               "omits the key entirely.)")
    else:
        record("N4", "FAIL-006", "BREACH", "not_sellable value semantics are not truthy-only")

    # N5 (V2 str-subclass) — a hostile str-subclass whose __eq__ returns True for 'SELLABLE' drops the veto for a
    #     NOT_SELLABLE lot (the '== SELLABLE' compare trusts the left operand). In-process code-exec only.
    class EvilSellable(str):
        def __eq__(self, other):
            return True
        def __hash__(self):
            return hash("x")
    evil = map_risk_flags(OpsCoreAvailabilityResponse(False, False, False, decision=EvilSellable("NOT_SELLABLE")))
    if "not_sellable" not in evil.risk_flags and evil.sellable is True:
        record("N5", "FAIL-006", "OPEN_NONGATE",
               "V2 (str-subclass eq): the sellability check is `response.decision == 'SELLABLE'`, which dispatches to "
               "the LEFT operand's __eq__ — a hostile str-subclass whose __eq__ returns True makes a NOT_SELLABLE "
               "value read as sellable -> the veto is DROPPED (no not_sellable key). In-process code-exec ONLY: a JSON "
               "/ S1b wire yields a plain str (from_mapping keeps a str-subclass, but the wire cannot carry one), and "
               "the mapper is unwired -> not channel-reachable. Route CODER: use `type(decision) is str and decision "
               "== 'SELLABLE'` (or normalize) so a subclass cannot spoof sellability.")
    else:
        record("N5", "FAIL-006", "DEFENDED", f"str-subclass did not spoof sellability ({evil.risk_flags})")

    # N6 (CRIT-02 / CRIT-06 honesty framing) — the veto branch is DEAD on every channel-reachable input today, and the
    #     approval refusal of a not_sellable lot rests on a SINGLE point (the overall-FAIL coupling), which the N1-B +
    #     A2 gaps could compound.
    record("N6", "FAIL-006", "NOTE",
           "honest scope (CRIT-02/CRIT-06, for the judge/owner): (a) the ONLY producer of not_sellable is the UNWIRED "
           "mapper (no app importer), so on every channel-reachable input conditions._risk's not_sellable branch is "
           "DEAD CODE today -> the leg-1 change has ZERO behavioral effect on any current channel; 'B3 closed' is true "
           "only for a FUTURE direct-feed wiring (NOT via recall_risk_contribution, per N1). (b) the approval refusal "
           "of a not_sellable lot rests ENTIRELY on the overall-FAIL check (record_owner_decision), NOT on the risk "
           "re-check (which ignores not_sellable, A2). If a future wiring built the propose context via the helper "
           "(N1-B: Risk PASS, overall HOLD) then approved with a fresh not_sellable read, the overall-FAIL guard would "
           "not fire and the re-check would clear it -> APPROVED (still contained by is_scale_authorized needing "
           "overall==PASS, structurally unreachable). A single-point defense; route OWNER/CODER to make the veto "
           "two-deep (propagate through the helper + re-check at approval) before S1b wiring.")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2U BOUNDARY ADVERSARY — recall E2 §3 conformance (in-scope: FAIL-006; stricter-only)")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for g in (group_LEG1, group_STRICT, group_CONTRIB, group_APPROVAL, group_HOLDFLOOR, group_MISC, group_N):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope = [o for o in breaches if o[1] in ("FAIL-006", "RULE-017", "RULE-018", "RULE-015")]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE BREACHES (FAIL-006 / RULE-017/018/015): {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    assert config.SCALE_MODEL_RATIFIED is False and config.DASHBOARD_ALERT_THRESHOLDS_DEFINED is False
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF ; both scale floors False (unchanged)")
    print("=" * 100)


if __name__ == "__main__":
    main()
