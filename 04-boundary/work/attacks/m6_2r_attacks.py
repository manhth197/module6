"""M6.2R boundary-adversary harness (READ-ONLY analysis; prompt M6-P2605).

Attacks the staged M6.2R slice — the recall-risk mapper (ops-core availability response -> Scale-Gate risk_flags)
feeding the EXISTING Scale Gate. In-scope fail gate M6-FAIL-006 (auto scale / publish without approval); rules
RULE-017 (risk hard veto), RULE-018 (invent no lock/decision), RULE-015 (no self-cert). The harness drives the real
staged code and EXECUTES every claimed breach; it flips no flag, opens no send, builds no HTTP client.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2r_attacks.py

No raw psid/phone/email literal appears in this source (markers synthetic + runtime-assembled).
Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (FAIL-006 trips: a scale is authorized or
executed, or a present/unobserved risk lock false-clears the gate, from a reachable path).
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve()
IMPL = None
for anc in HERE.parents:
    cand = anc / "04-artifacts" / "impl" / "M6.2R"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2R/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.recall_risk_mapper import (
    OpsCoreAvailabilityResponse, RecallRiskRead, RECALL_RISK_KEYS,
    map_risk_flags, map_pull_outcome, risk_picture_complete, recall_risk_contribution,
)
from app.measurement.scale.conditions import (
    RISK_LOCKS, ScaleCondition, ScaleContext, active_risk_locks, evaluate_conditions,
)
from app.measurement.scale.scale_gate import ScaleGate, ScaleGateViolation
from app.measurement.scale.models import AdsScaleRequest, ApprovalState, DecisionKind, OwnerDecision
from app.measurement.scale.scale_request_store import ScaleRequestStore
from app.api.scale_requests import (
    handle_scale_request_create, handle_scale_decision, ScaleRequestDeps, ScaleResponse,
)

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
PASS, HOLD, FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL
OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


# --- factories ---------------------------------------------------------------------------------------
def resp(recall_hold=False, sale_lock=False, quality_hold=False, recall_case_open=False,
         decision=None, block_reasons=(), sku_ref=None):
    return OpsCoreAvailabilityResponse(
        recall_hold=recall_hold, sale_lock=sale_lock, quality_hold=quality_hold,
        recall_case_open=recall_case_open, decision=decision, block_reasons=tuple(block_reasons), sku_ref=sku_ref)


def all6_clean():
    """A COMPLETE 6-lock clean picture (all RISK_LOCKS observed, none active) — the only legitimately clearing map."""
    return {lock: False for lock in RISK_LOCKS}


def risk_row(ctx):
    results, overall = evaluate_conditions(ctx)
    r = next(c for c in results if c.condition is ScaleCondition.RISK)
    return r.status, overall


def owner_decision(actor="owner_ceo", kind=DecisionKind.APPROVE):
    return OwnerDecision(actor=actor, reason="reviewed", audit_ref="aud", evidence_ref="ev", decision=kind, at=TS)


def new_gate():
    return ScaleGate(ScaleRequestStore(), AuditLog())


def propose_and_try_approve(ctx, *, budget_cap=1000.0, rollback="rollback if CPA>x", request_id="req"):
    """Propose with the given context, then attempt an owner APPROVE re-checking current_risk_flags=ctx.risk_flags.
    Returns (request, overall, approved_bool, refused_bool, authorized_bool)."""
    gate = new_gate()
    req = gate.propose(request_id, {"campaign_id": "camp_1"}, ctx,
                       budget_cap=budget_cap, rollback_condition=rollback, now=TS)
    approved = refused = False
    try:
        req = gate.record_owner_decision(request_id, owner_decision(),
                                         current_risk_flags=ctx.risk_flags, now=TS)
        approved = req.approval_state is ApprovalState.APPROVED
    except ScaleGateViolation:
        refused = True
    return req, req.overall_status, approved, refused, req.is_scale_authorized


# ===================================================================================================
# GROUP MAP — the mapper's fail-closed correctness (RULE-017 / RULE-018)
# ===================================================================================================
def group_MAP():
    # M1 — recall = recall_hold OR recall_case_open (both directions); clean -> False.
    r_hold = map_risk_flags(resp(recall_hold=True))
    r_case = map_risk_flags(resp(recall_case_open=True))
    r_clean = map_risk_flags(resp())
    if (r_hold.risk_flags["recall"] is True and r_case.risk_flags["recall"] is True
            and r_clean.risk_flags["recall"] is False and r_hold.complete and r_case.complete):
        record("M1", "RULE-017", "DEFENDED",
               "recall = recall_hold OR recall_case_open: recall_hold=True -> recall True; recall_case_open=True "
               "(hold False) -> recall True (additive OR); all-clean -> recall False. Both map complete.")
    else:
        record("M1", "RULE-017", "BREACH", f"recall OR mis-mapped (hold={r_hold.risk_flags}, case={r_case.risk_flags})")

    # M2 — additive default: recall_case_open absent (dict path) -> treated False -> recall follows recall_hold only.
    r_absent = map_pull_outcome({"recall_hold": False, "sale_lock": False, "quality_hold": False})
    if r_absent.complete and r_absent.risk_flags["recall"] is False:
        record("M2", "RULE-018", "DEFENDED",
               "recall_case_open absent (dict path) defaults to False (additive) -> recall follows recall_hold only "
               "(=False here); the absent additive flag never fabricates a recall.")
    else:
        record("M2", "RULE-018", "BREACH", f"additive default wrong ({r_absent.risk_flags}, complete={r_absent.complete})")

    # M3 — decision / block_reasons are NEVER read: a SELLABLE decision + clean block_reasons cannot clear a present
    #      recall_hold; a scary decision string + scary block_reasons cannot fabricate a lock on clean booleans.
    r_sell = map_risk_flags(resp(recall_hold=True, decision="SELLABLE", block_reasons=("clean_lot",)))
    scary = "RECALL_" + "".join(["H", "O", "L", "D"]) + "_ACTIVE"
    r_scary = map_risk_flags(resp(decision=scary, block_reasons=(scary, "danger")))
    if (r_sell.risk_flags["recall"] is True
            and r_scary.risk_flags == {"recall": False, "sale_lock": False, "quality_hold": False}):
        record("M3", "RULE-018", "DEFENDED",
               "the mapper reads presence booleans ONLY: decision='SELLABLE' + clean block_reasons cannot clear a "
               "present recall_hold (recall stays True); a scary decision string + scary block_reasons cannot "
               "fabricate a lock on clean booleans (all False). decision/block_reasons never reach risk_flags.")
    else:
        record("M3", "RULE-018", "BREACH", f"decision/block_reasons leaked into risk_flags (sell={r_sell.risk_flags})")

    # M4 — strict-bool choke: a non-bool presence flag (value-object AND dict path) -> INCOMPLETE, never coerced.
    non_bools = [None, 0, 1, 1.0, "false", "true", "", (), [], {}]
    vo_leaks = []
    dict_leaks = []
    for nb in non_bools:
        # value-object path (direct construction, non-bool recall_hold)
        vo = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=nb, sale_lock=False, quality_hold=False))
        if vo.complete or vo.risk_flags:
            vo_leaks.append(repr(nb))
        # dict path
        dp = map_pull_outcome({"recall_hold": nb, "sale_lock": False, "quality_hold": False})
        if dp.complete or dp.risk_flags:
            dict_leaks.append(repr(nb))
    if not vo_leaks and not dict_leaks:
        record("M4", "FAIL-006", "DEFENDED",
               "strict-bool choke (isinstance bool, so 0/1/int/float/str/'false'/'true'/empty-containers rejected): a "
               "non-bool presence flag on EITHER the value-object or the dict path is an INCOMPLETE empty read "
               "(complete=False, risk_flags {}), never bool()-coerced to a clear or a lock. 0/1 (int, bool-subclass "
               "check) and 'false'/'true' both fail closed.")
    else:
        record("M4", "FAIL-006", "BREACH", f"non-bool coerced (vo={vo_leaks}, dict={dict_leaks})")

    # M5 — missing presence key (dict path) -> None -> INCOMPLETE.
    r_missing = map_pull_outcome({"sale_lock": False})           # recall_hold + quality_hold absent
    if not r_missing.complete and r_missing.risk_flags == {}:
        record("M5", "FAIL-006", "DEFENDED",
               "a missing presence key (dict path) becomes None -> INCOMPLETE empty read (locks unobserved); a "
               "partial dict never yields a partial clearing map.")
    else:
        record("M5", "FAIL-006", "BREACH", f"missing key cleared ({r_missing.risk_flags})")

    # M6 — None / absent response -> INCOMPLETE (both map_risk_flags and map_pull_outcome).
    if (not map_risk_flags(None).complete and not map_pull_outcome(None).complete
            and not map_pull_outcome().complete):
        record("M6", "FAIL-006", "DEFENDED",
               "a None / absent response is INCOMPLETE (map_risk_flags(None) + map_pull_outcome(None)/() all empty) — "
               "a pulled-nothing is never a false-clear.")
    else:
        record("M6", "FAIL-006", "BREACH", "None/absent response was not fail-closed")

    # M7 — map_pull_outcome error + unrecognized-type paths -> INCOMPLETE (models the S1b seam without HTTP).
    errs = ["TIMEOUT", "HTTP_429", "CONNECTION_ERROR"]
    err_ok = all(not map_pull_outcome(error=e).complete and map_pull_outcome(error=e).risk_flags == {} for e in errs)
    unrec = [7, "a string", ["list"], object()]
    unrec_ok = all(not map_pull_outcome(u).complete and map_pull_outcome(u).risk_flags == {} for u in unrec)
    if err_ok and unrec_ok:
        record("M7", "FAIL-006", "DEFENDED",
               "map_pull_outcome fail-closes every transport outcome: error=TIMEOUT/HTTP_429/CONNECTION_ERROR -> "
               "INCOMPLETE; an unrecognized response type (int/str/list/object) -> INCOMPLETE. No pull outcome is a "
               "False false-clear; the S1b seam is modelled without any HTTP.")
    else:
        record("M7", "FAIL-006", "BREACH", f"a pull outcome cleared (err_ok={err_ok}, unrec_ok={unrec_ok})")

    # M8 — the mapper output is a strict 3-of-6 SUBSET and fabricates none of the other 3 locks.
    complete = map_risk_flags(resp())
    keys = set(complete.risk_flags)
    others = {"complaint_p0", "platform_spam_flag", "crm_suppression"}
    if keys == set(RECALL_RISK_KEYS) and keys < set(RISK_LOCKS) and not (keys & others):
        record("M8", "RULE-018", "DEFENDED",
               f"the mapper owns exactly its 3 ops-core keys {sorted(keys)} — a strict SUBSET of the 6 RISK_LOCKS; it "
               "fabricates none of complaint_p0/platform_spam_flag/crm_suppression (those come from their own sources).")
    else:
        record("M8", "RULE-018", "BREACH", f"mapper fabricated/omitted keys ({keys})")

    # M9 — the mapper module imports NO HTTP/transport surface (the S1b live client is not built) — FAIL-006-adjacent.
    import app.measurement.scale.recall_risk_mapper as m
    transport = ("requests", "httpx", "urllib", "http", "socket", "aiohttp", "urllib3")
    present = [t for t in transport if hasattr(m, t)]
    if not present:
        record("M9", "FAIL-006", "DEFENDED",
               "the mapper module binds NO HTTP/transport name (requests/httpx/urllib/http/socket/aiohttp) — the S1b "
               "live client to ops-core /v1/availability/check is NOT built; the mapper consumes an in-memory value "
               "object / dict only, so this slice pulls nothing live.")
    else:
        record("M9", "FAIL-006", "BREACH", f"a transport surface is imported: {present}")


# ===================================================================================================
# GROUP CONTRIB — recall_risk_contribution fail-closed-by-construction (the partial-map defense)
# ===================================================================================================
def group_CONTRIB():
    # C1 — an active lock (from the read) reaches the gate WITH the lock (FAIL direction).
    read_lock = map_risk_flags(resp(recall_hold=True))
    merged = recall_risk_contribution(read_lock)
    if merged.get("recall") is True and any(merged.get(l) for l in RISK_LOCKS):
        record("C1", "RULE-017", "DEFENDED",
               "recall_risk_contribution keeps an ACTIVE lock: a complete read with recall True -> merged carries "
               "recall=True (an active lock), so the gate FAILs (the FAIL direction is never suppressed).")
    else:
        record("C1", "RULE-017", "BREACH", f"an active lock was dropped by the merge ({merged})")

    # C2 — a bare 3-of-6 CLEAN read (no base) collapses to {} (HOLD) — the core partial-map defense.
    read_clean = map_risk_flags(resp())
    bare = recall_risk_contribution(read_clean)
    st, overall = risk_row(ScaleContext(risk_flags=bare))
    if bare == {} and st is HOLD:
        record("C2", "FAIL-006", "DEFENDED",
               "a bare 3-of-6 CLEAN read (no base sources) collapses to {} via recall_risk_contribution -> the Scale "
               "Gate Risk row is HOLD (fail-closed), NOT a partial map the gate's _risk would wrongly PASS. The "
               "mapper's clean output is structurally never a standalone clearing map.")
    else:
        record("C2", "FAIL-006", "BREACH", f"a bare clean 3-of-6 did not collapse (bare={bare}, risk={st})")

    # C3 — a COMPLETE 6-lock clean picture (caller merged all sources) -> full map returned -> Risk PASS (non-vacuous).
    read_clean = map_risk_flags(resp())
    full = recall_risk_contribution(read_clean, base_flags={k: False for k in
                                                            ("complaint_p0", "platform_spam_flag", "crm_suppression")})
    st, _ = risk_row(ScaleContext(risk_flags=full))
    if risk_picture_complete(full) and st is PASS:
        record("C3", "FAIL-006", "DEFENDED",
               "non-vacuity: a COMPLETE 6-lock clean picture (this read's 3 + the other 3 sources, none active) is "
               "returned in full and the Risk row PASSes — so C2's collapse is a genuine fail-closed, not a dead "
               "refuse-all. Only an all-6 no-active picture clears.")
    else:
        record("C3", "FAIL-006", "NOTE", f"complete-clean picture did not PASS as expected (risk={st})")

    # C4 — an incomplete (pull-error) read + no base -> {} -> HOLD.
    inc = recall_risk_contribution(map_pull_outcome(error="TIMEOUT"))
    st, _ = risk_row(ScaleContext(risk_flags=inc))
    if inc == {} and st is HOLD:
        record("C4", "FAIL-006", "DEFENDED",
               "a pull-error INCOMPLETE read + no base collapses to {} -> Risk HOLD; an unobserved risk read never "
               "clears the gate.")
    else:
        record("C4", "FAIL-006", "BREACH", f"incomplete read cleared ({inc}, risk={st})")

    # C5 — risk_picture_complete predicate: 3-of-6 -> False; 6-of-6 -> True.
    if not risk_picture_complete({k: False for k in RECALL_RISK_KEYS}) and risk_picture_complete(all6_clean()):
        record("C5", "FAIL-006", "DEFENDED",
               "risk_picture_complete is the honest all-6 predicate: a 3-of-6 map is NOT complete; only a 6-of-6 map "
               "is. A clearing decision must assemble all 6 sources before treating a map as clearing-eligible.")
    else:
        record("C5", "FAIL-006", "BREACH", "risk_picture_complete mis-judged completeness")

    # C5b — incomplete read but the base carries an active lock -> the active lock STILL reaches the gate (FAIL).
    inc_base = recall_risk_contribution(map_pull_outcome(error="TIMEOUT"), base_flags={"complaint_p0": True})
    st, _ = risk_row(ScaleContext(risk_flags=inc_base))
    if inc_base.get("complaint_p0") is True and st is FAIL:
        record("C5b", "RULE-017", "DEFENDED",
               "an INCOMPLETE recall read does not erase a base active lock: base complaint_p0=True + a pull-error "
               "read -> the merge keeps complaint_p0 -> Risk FAIL (the FAIL direction survives an incomplete recall).")
    else:
        record("C5b", "RULE-017", "BREACH", f"an incomplete read erased a base active lock ({inc_base}, risk={st})")


# ===================================================================================================
# GROUP GATE — feeding mapped flags to the EXISTING Scale Gate (RULE-017 veto; FAIL despite SELLABLE)
# ===================================================================================================
def group_GATE():
    # G1 — FAIL despite SELLABLE (recall_hold): a present recall_hold + decision=SELLABLE -> Risk FAIL -> overall FAIL;
    #      owner APPROVE refused (ScaleGateViolation). The clean-lot recall still locks.
    read = map_risk_flags(resp(recall_hold=True, decision="SELLABLE", block_reasons=("clean_lot",)))
    ctx = ScaleContext(risk_flags=recall_risk_contribution(read))
    _, overall, approved, refused, authorized = propose_and_try_approve(ctx)
    st, _ = risk_row(ctx)
    if st is FAIL and overall is FAIL and refused and not approved and not authorized:
        record("G1", "FAIL-006", "DEFENDED",
               "FAIL despite SELLABLE (recall_hold): a present recall_hold with decision=SELLABLE maps to recall=True "
               "-> Risk row FAIL -> overall FAIL; the owner APPROVE is REFUSED (ScaleGateViolation) and no scale is "
               "authorized. A clean-lot decision cannot lift a recall lock.")
    else:
        record("G1", "FAIL-006", "BREACH", f"SELLABLE cleared a recall (risk={st}, overall={overall}, appr={approved})")

    # G2 — FAIL despite SELLABLE (recall_case_open additive): recall_case_open True, recall_hold False -> recall True.
    read = map_risk_flags(resp(recall_case_open=True, decision="SELLABLE"))
    ctx = ScaleContext(risk_flags=recall_risk_contribution(read))
    _, overall, approved, refused, authorized = propose_and_try_approve(ctx)
    st, _ = risk_row(ctx)
    if st is FAIL and refused and not authorized:
        record("G2", "FAIL-006", "DEFENDED",
               "FAIL despite SELLABLE (recall_case_open additive): recall_case_open=True with recall_hold=False -> "
               "recall True -> Risk FAIL -> owner APPROVE refused, no scale authorized. The additive open-case locks.")
    else:
        record("G2", "FAIL-006", "BREACH", f"recall_case_open did not lock (risk={st}, appr={approved})")

    # G3 — fail-closed on incomplete read: contribution {} -> Risk HOLD -> owner APPROVE refused (not PASS at approval).
    ctx = ScaleContext(risk_flags=recall_risk_contribution(map_pull_outcome(error="HTTP_429")))
    _, overall, approved, refused, authorized = propose_and_try_approve(ctx)
    st, _ = risk_row(ctx)
    if st is HOLD and refused and not approved and not authorized:
        record("G3", "FAIL-006", "DEFENDED",
               "fail-closed on pull error: an INCOMPLETE read -> contribution {} -> Risk HOLD -> the owner APPROVE is "
               "REFUSED (the approval-time re-check falls back to the proposal Risk HOLD, not PASS) -> the gate does "
               "NOT clear and no scale is authorized.")
    else:
        record("G3", "FAIL-006", "BREACH", f"an incomplete read cleared the gate (risk={st}, appr={approved})")

    # G4 (HIGHEST-VALUE) — the carried partial-map gate limitation: a RAW 3-of-6 clean map fed DIRECTLY as
    #      ScaleContext.risk_flags (bypassing recall_risk_contribution) makes conditions._risk PASS. Execute it and
    #      prove the DOWNSTREAM chokes contain it (no auto-scale): overall still HOLD, is_scale_authorized False.
    raw_partial = dict(map_risk_flags(resp()).risk_flags)         # {recall:False, sale_lock:False, quality_hold:False}
    ctx = ScaleContext(risk_flags=raw_partial, entry_evidence_refs={e: f"ref{e}" for e in
                       ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")},
                       quote_order_ok=True, public_privacy_ok=True, dq_overall=PASS)
    st, overall = risk_row(ctx)
    _, overall2, approved, refused, authorized = propose_and_try_approve(ctx)
    # the intended wiring would have collapsed this to {} (HOLD):
    collapsed = recall_risk_contribution(map_risk_flags(resp()))
    if st is PASS and overall is HOLD and not authorized and collapsed == {}:
        record("G4", "FAIL-006", "OPEN_NONGATE",
               "carried gate-hardening limitation (tester forward finding): a RAW 3-of-6 clean map fed DIRECTLY as "
               "ScaleContext.risk_flags (bypassing recall_risk_contribution) makes conditions._risk PASS (non-empty, "
               "no active) though 3 of the 6 RISK_LOCKS (complaint_p0/platform_spam_flag/crm_suppression) are "
               "UNOBSERVED. Contained for FAIL-006 by THREE downstream chokes: (1) overall stays HOLD (Funnel + "
               "Dashboard HOLD via M6-OD-002 / SCALE_MODEL_RATIFIED=False) so is_scale_authorized is False and NO "
               "scale is authorized; (2) the intended wiring recall_risk_contribution collapses this exact clean map "
               "to {} (HOLD), so a correctly-wired caller never produces the partial map; (3) approval-time "
               f"_assert_risk_clear_at_approval requires all-6. Result here: Risk={st.value}, overall={overall.value}, "
               f"approve_recorded={approved}, is_scale_authorized={authorized}. Pre-existing gate limitation, NOT "
               "introduced by M6.2R (no-gate-change scope, M6-OD-017). Route OWNER: require all-6 RISK_LOCKS present "
               "for _risk PASS (mirror _assert_risk_clear_at_approval).")
    else:
        record("G4", "FAIL-006", "BREACH" if authorized else "NOTE",
               f"partial-map path unexpected (risk={st}, overall={overall}, authorized={authorized}, collapse={collapsed})")

    # G5 — a sale_lock and a quality_hold each independently FAIL the Risk row (all three ops-core locks veto).
    for lock_kw, name in (({"sale_lock": True}, "sale_lock"), ({"quality_hold": True}, "quality_hold")):
        ctx = ScaleContext(risk_flags=recall_risk_contribution(map_risk_flags(resp(**lock_kw))))
        st, _ = risk_row(ctx)
        if st is not FAIL:
            record("G5", "FAIL-006", "BREACH", f"{name} did not FAIL the Risk row (risk={st})")
            break
    else:
        record("G5", "FAIL-006", "DEFENDED",
               "each ops-core lock independently vetoes: sale_lock=True -> Risk FAIL; quality_hold=True -> Risk FAIL "
               "(RULE-017 hard veto covers all three mapped locks, not just recall).")


# ===================================================================================================
# GROUP EXEC — FAIL-006 crown jewel: no executor; overall HOLD floor; is_scale_authorized unreachable
# ===================================================================================================
def group_EXEC():
    # E1 — no executor verb on ScaleGate.
    gate = new_gate()
    verbs = ("scale", "enable", "publish", "send", "raise_budget", "activate", "launch", "apply", "execute",
             "campaign", "audience", "spend", "deliver", "http", "post", "connect", "budget")
    hits = [v for v in verbs if hasattr(gate, v)]
    if not hits:
        record("E1", "FAIL-006", "DEFENDED",
               "the ScaleGate exposes NO executor verb (scale/enable/publish/send/raise_budget/activate/launch/apply/"
               "execute/campaign/audience/spend). It computes conditions + records an inert PROPOSED request and NEVER "
               "acts (RULE-010).")
    else:
        record("E1", "FAIL-006", "BREACH", f"an executor verb is exposed: {hits}")

    # E2 — ScaleRequestDeps holds no transport / budget handle (only gate/context/audit).
    deps = ScaleRequestDeps(scale_gate=new_gate(), context=ScaleContext(), audit=AuditLog())
    fields = set(vars(deps))
    if fields <= {"scale_gate", "context", "audit"}:
        record("E2", "FAIL-006", "DEFENDED",
               f"ScaleRequestDeps holds only {sorted(fields)} — no Transport / budget / campaign / audience handle; "
               "the admin API path cannot reach an executor (RULE-010/012, FAIL-006).")
    else:
        record("E2", "FAIL-006", "BREACH", f"deps carries an extra handle: {fields}")

    # E3 — AdsScaleRequest carries no execute method; APPROVED is a recorded state, is_scale_authorized only reports.
    req_methods = [m for m in ("execute", "scale", "apply", "publish", "send", "activate", "launch")
                   if callable(getattr(AdsScaleRequest, m, None))]
    if not req_methods:
        record("E3", "FAIL-006", "DEFENDED",
               "AdsScaleRequest carries NO execute/scale/apply/publish method — 'APPROVED' is a recorded decision, not "
               "a trigger; is_scale_authorized only REPORTS (owner performs any scale outside Module 6).")
    else:
        record("E3", "FAIL-006", "BREACH", f"AdsScaleRequest exposes an action method: {req_methods}")

    # E4 (CROWN JEWEL) — the maximal-clear attempt: a fully-cleared, fully-approved, no-lock, all-6-clean request
    #      STILL yields overall HOLD and is_scale_authorized False (Funnel + Dashboard HOLD floor). Nothing scales.
    ctx = ScaleContext(
        entry_evidence_refs={e: f"ref{e}" for e in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")},
        quote_order_ok=True, public_privacy_ok=True, boxes_per_order=3.0, dq_overall=PASS,
        risk_flags=all6_clean(), owner_approved=True, budget_cap=1000.0, rollback_condition="rollback",
    )
    req, overall, approved, refused, authorized = propose_and_try_approve(ctx)
    results, _ = evaluate_conditions(ctx)
    funnel = next(c for c in results if c.condition is ScaleCondition.FUNNEL).status
    dash = next(c for c in results if c.condition is ScaleCondition.DASHBOARD).status
    if overall is HOLD and not authorized and funnel is HOLD and dash is HOLD and approved:
        record("E4", "FAIL-006", "DEFENDED",
               "CROWN JEWEL: a maximally-cleared request (all 4 entry evidences, quote/order + public/privacy attested, "
               "DQ PASS, all-6 RISK_LOCKS clean, owner APPROVE recorded, budget cap + rollback present) STILL yields "
               f"overall=HOLD and is_scale_authorized=FALSE — Funnel HOLD (M6-OD-002) + Dashboard HOLD "
               "(SCALE_MODEL_RATIFIED=False) floor the gate below PASS. Even a recorded owner APPROVE authorizes no "
               "scale while M6-OD-002/005 are OPEN — the deepest FAIL-006 defense (is_scale_authorized structurally "
               "unreachable), independent of any mapper/risk quirk.")
    else:
        record("E4", "FAIL-006", "BREACH" if authorized else "NOTE",
               f"maximal-clear unexpected (overall={overall}, authorized={authorized}, funnel={funnel}, dash={dash})")

    # E5 — the HOLD floor is a config invariant (immutable to this role): both gate flags are False.
    if config.SCALE_MODEL_RATIFIED is False and config.DASHBOARD_ALERT_THRESHOLDS_DEFINED is False:
        record("E5", "FAIL-006", "DEFENDED",
               "the HOLD floor is a config invariant immutable to this role: SCALE_MODEL_RATIFIED=False (M6-OD-005) + "
               "DASHBOARD_ALERT_THRESHOLDS_DEFINED=False (M6-OD-002). The boundary role writes no enabling value; "
               "Funnel + Dashboard can never PASS today, so overall is HOLD-floored.")
    else:
        record("E5", "FAIL-006", "BREACH", "a scale-enabling config flag is True")


# ===================================================================================================
# GROUP API — the channel-reachable admin path (untrusted body; RULE-H03 / RULE-015)
# ===================================================================================================
def group_API():
    # A1 — the untrusted body cannot inject conditions / risk_flags / overall: conditions come from deps.context.
    #      Server context carries an active recall lock; a body claiming "all clear" cannot fake a PASS.
    active_ctx = ScaleContext(risk_flags=recall_risk_contribution(map_risk_flags(resp(recall_hold=True))))
    deps = ScaleRequestDeps(scale_gate=new_gate(), context=active_ctx, audit=AuditLog())
    body = {"campaign_id": "camp_1", "budget_cap": 1000.0, "rollback_condition": "rb",
            "risk_flags": {}, "overall_status": "PASS", "owner_approved": True,
            "conditions": [{"condition": "Risk", "status": "PASS"}]}
    created = handle_scale_request_create(body, deps)
    if created.status == "CREATED" and created.overall_status == FAIL.value:
        record("A1", "FAIL-006", "DEFENDED",
               "RULE-H03: the untrusted admin body cannot inject conditions/risk_flags/overall — the created request's "
               "overall is FAIL (computed from deps.context's active recall lock), NOT the body's claimed PASS/"
               "owner_approved. A request body can never fake a condition PASS.")
    else:
        record("A1", "FAIL-006", "BREACH", f"body injected a condition (status={created.status}, overall={created.overall_status})")

    # A2 — APPROVE via the API on an active-lock context -> APPROVAL_REFUSED (Risk veto re-check).
    deps = ScaleRequestDeps(scale_gate=new_gate(), context=active_ctx, audit=AuditLog())
    created = handle_scale_request_create({"campaign_id": "camp_1", "budget_cap": 1000.0, "rollback_condition": "rb"}, deps)
    dec = {"request_id": created.request_id, "decision": "APPROVE", "actor": "owner_ceo",
           "reason": "go", "audit_ref": "a", "evidence_ref": "e"}
    decided = handle_scale_decision(dec, deps, now=TS)
    if decided.status == "REJECTED_INPUT" and decided.error_code == "APPROVAL_REFUSED":
        record("A2", "FAIL-006", "DEFENDED",
               "the admin APPROVE on an active-recall context is REFUSED (error_code=APPROVAL_REFUSED): the gate "
               "re-checks current_risk_flags=deps.context.risk_flags at approval (RULE-017) and refuses — no scale "
               "happens, the refusal is reported honestly (not hidden).")
    else:
        record("A2", "FAIL-006", "BREACH", f"an active-lock approve was not refused ({decided})")

    # A3 — the API cannot synthesize an owner approval: a decision missing actor/reason/audit/evidence -> refused.
    deps = ScaleRequestDeps(scale_gate=new_gate(), context=ScaleContext(risk_flags=all6_clean()), audit=AuditLog())
    created = handle_scale_request_create({"campaign_id": "camp_1", "budget_cap": 1000.0, "rollback_condition": "rb"}, deps)
    incomplete = handle_scale_decision({"request_id": created.request_id, "decision": "APPROVE", "actor": "owner_ceo"},
                                       deps, now=TS)
    if incomplete.status == "REJECTED_INPUT" and incomplete.error_code == "OWNER_DECISION_INCOMPLETE":
        record("A3", "RULE-015", "DEFENDED",
               "the API never synthesizes an approval: an owner decision missing reason/audit_ref/evidence_ref is "
               "REJECTED (OWNER_DECISION_INCOMPLETE) — all four owner fields must be present (RULE-015).")
    else:
        record("A3", "RULE-015", "BREACH", f"an incomplete owner decision was accepted ({incomplete})")

    # A4 — schema validation: a non-numeric budget_cap and a bad decision enum are rejected before any state change.
    deps = ScaleRequestDeps(scale_gate=new_gate(), context=ScaleContext(risk_flags=all6_clean()), audit=AuditLog())
    bad_budget = handle_scale_request_create({"campaign_id": "camp_1", "budget_cap": "lots"}, deps)
    bad_decision = handle_scale_decision({"request_id": "x", "decision": "SCALE_NOW", "actor": "a",
                                          "reason": "r", "audit_ref": "au", "evidence_ref": "e"}, deps, now=TS)
    no_target = handle_scale_request_create({"budget_cap": 1000.0}, deps)
    if (bad_budget.error_code == "SCHEMA_INVALID" and bad_decision.error_code == "SCHEMA_INVALID"
            and no_target.error_code == "SCHEMA_INVALID"):
        record("A4", "RULE-015", "DEFENDED",
               "schema validation: a non-numeric budget_cap, a bogus decision enum ('SCALE_NOW'), and a missing "
               "scale_target are all REJECTED (SCHEMA_INVALID) before any state change — the body cannot smuggle a "
               "non-APPROVE/REJECT action.")
    else:
        record("A4", "RULE-015", "BREACH",
               f"schema validation gap (budget={bad_budget.error_code}, dec={bad_decision.error_code})")

    # A5 — even a fully-clean all-6 context + a complete owner APPROVE via the API authorizes NO scale (overall HOLD).
    clean_ctx = ScaleContext(
        entry_evidence_refs={e: f"ref{e}" for e in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")},
        quote_order_ok=True, public_privacy_ok=True, dq_overall=PASS,
        risk_flags=all6_clean(), owner_approved=True, budget_cap=1000.0, rollback_condition="rb")
    store = ScaleRequestStore()
    gate = ScaleGate(store, AuditLog())
    deps = ScaleRequestDeps(scale_gate=gate, context=clean_ctx, audit=AuditLog())
    created = handle_scale_request_create({"campaign_id": "camp_1", "budget_cap": 1000.0, "rollback_condition": "rb"}, deps)
    decided = handle_scale_decision({"request_id": created.request_id, "decision": "APPROVE", "actor": "owner_ceo",
                                     "reason": "go", "audit_ref": "a", "evidence_ref": "e"}, deps, now=TS)
    req = store.get(created.request_id)
    if decided.status == "DECIDED" and decided.overall_status == HOLD.value and req.is_scale_authorized is False:
        record("A5", "FAIL-006", "DEFENDED",
               "channel end-to-end: a fully-clean all-6 context + a complete owner APPROVE records DECIDED/APPROVED, "
               "yet overall=HOLD and is_scale_authorized=False — the admin API can record an approval but authorizes "
               "NO scale while the HOLD floor holds. The recorded approval is inert (nothing executes).")
    else:
        record("A5", "FAIL-006", "BREACH" if (req and req.is_scale_authorized) else "NOTE",
               f"API clean-approve unexpected (status={decided.status}, overall={decided.overall_status})")


# ===================================================================================================
# GROUP CARRIED — posture + evidence pack + PII (RULE-014)
# ===================================================================================================
def group_CARRIED():
    # PII — OwnerDecision.to_public masks the actor; AdsScaleRequest export carries campaign refs (not PII).
    import re as _re
    d = OwnerDecision(actor="owner_secret", reason="ok", audit_ref="a", evidence_ref="e", decision=DecisionKind.APPROVE)
    pub = d.to_public()
    req = AdsScaleRequest(request_id="r", scale_target={"campaign_id": "camp_1"}, budget_cap=1.0,
                          rollback_condition="rb", evidence_refs=(), condition_results=(), overall_status=HOLD,
                          decision=d)
    blob = str(pub) + str(req.to_public())
    actor_leaked = "owner_secret" in blob
    pii_shaped = ("@" in blob) or bool(_re.findall(r"\d{7,}", blob))
    if not actor_leaked and not pii_shaped and pub["decision"] == "APPROVE":
        record("PII", "RULE-014", "DEFENDED",
               "RULE-014: OwnerDecision.to_public masks the actor (raw 'owner_secret' absent) while keeping the "
               "decision enum; AdsScaleRequest.to_public carries campaign refs (not PII) and no '@'/phone-shaped "
               "token. (reason/audit_ref are owner-supplied free text — flagged to security below.)")
    else:
        record("PII", "RULE-014", "BREACH", f"a raw actor / PII leaked on export (actor_leaked={actor_leaked})")

    # AUDIT — the owner-supplied free-text reason/audit_ref is NOT echoed into the audit detail (machine-safe).
    audit = AuditLog()
    gate = ScaleGate(ScaleRequestStore(), audit)
    ctx = ScaleContext(risk_flags=all6_clean(), owner_approved=True, budget_cap=1.0, rollback_condition="rb",
                       dq_overall=PASS, quote_order_ok=True, public_privacy_ok=True,
                       entry_evidence_refs={e: f"r{e}" for e in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")})
    gate.propose("rq", {"campaign_id": "c"}, ctx, budget_cap=1.0, rollback_condition="rb", now=TS)
    pii_reason = "leak-" + chr(64) + "-marker"
    gate.record_owner_decision("rq", OwnerDecision(actor="owner_ceo", reason=pii_reason, audit_ref=pii_reason,
                               evidence_ref="e", decision=DecisionKind.APPROVE), current_risk_flags=ctx.risk_flags, now=TS)
    ablob = str([(getattr(e, "action", None), getattr(e, "reason", None), getattr(e, "detail", None),
                  getattr(e, "subject", None)) for e in getattr(audit, "entries", [])])
    if pii_reason not in ablob:
        record("AUDIT", "FAIL-008", "DEFENDED",
               "the owner-supplied free-text reason/audit_ref is NOT echoed into the audit detail (machine-safe: only "
               "request id + decision enum; actor masked by the sink) — no raw PII in the scale audit trail.")
    else:
        record("AUDIT", "FAIL-008", "NOTE", "owner free-text reached the audit blob (inspect masking scope)")

    # REG — posture immutable (BLOCKED / OFF / OFF), no egress opened.
    if (config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
            and config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False):
        record("REG", "FAIL-006", "DEFENDED",
               "posture immutable: BLOCKED / OFF / OFF, is_external_send_enabled() False — the recall-mapper slice "
               "flipped nothing, built no live client, opened no egress.")
    else:
        record("REG", "FAIL-006", "BREACH", "posture changed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    # N1 (CRIT-01, HIGHEST-VALUE) — the overall=HOLD floor is STRUCTURAL, not config-valued: even with BOTH config
    #     floors monkeypatched True in-process, _funnel/_dashboard have NO PASS branch, so overall never reaches PASS
    #     and is_scale_authorized stays False. (In-process probe only; the real config values are restored in finally
    #     and re-asserted — no enabling value is written to disk.)
    saved = (config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED)
    try:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED = True
        config.SCALE_MODEL_RATIFIED = True
        ctx = ScaleContext(
            entry_evidence_refs={e: f"ref{e}" for e in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")},
            quote_order_ok=True, public_privacy_ok=True, boxes_per_order=3.0, dq_overall=PASS,
            risk_flags=all6_clean(), owner_approved=True, budget_cap=1000.0, rollback_condition="rb")
        results, overall = evaluate_conditions(ctx)
        funnel = next(c for c in results if c.condition is ScaleCondition.FUNNEL).status
        dash = next(c for c in results if c.condition is ScaleCondition.DASHBOARD).status
        req = AdsScaleRequest(request_id="r", scale_target={}, budget_cap=1.0, rollback_condition="rb",
                              evidence_refs=(), condition_results=results, overall_status=overall,
                              approval_state=ApprovalState.APPROVED, decision=owner_decision())
        authorized_even_flipped = req.is_scale_authorized
    finally:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED = saved
    if overall is not PASS and funnel is HOLD and dash is HOLD and not authorized_even_flipped:
        record("N1", "FAIL-006", "DEFENDED",
               "CRIT-01 (load-bearing regression): the overall=HOLD floor is STRUCTURAL, not merely config-valued — "
               "with BOTH config floors monkeypatched True in-process (DASHBOARD_ALERT_THRESHOLDS_DEFINED + "
               "SCALE_MODEL_RATIFIED), _funnel still returns HOLD ('funnel not fully evaluated') and _dashboard still "
               f"returns HOLD ('not yet scale-evidence graded') — neither has a PASS branch — so overall={overall.value} "
               "and is_scale_authorized stays False even with a maximally-cleared owner-approved request. The FAIL-006 "
               "containment holds in the function bodies, not just the config values. Config restored + re-asserted. "
               "NOTE: if a future slice adds a PASS branch to _funnel/_dashboard, every OPEN_NONGATE below becomes a "
               "live breach at once — this is the invariant to lock.")
    else:
        record("N1", "FAIL-006", "BREACH" if authorized_even_flipped else "NOTE",
               f"floor lifted with flags flipped (overall={overall}, funnel={funnel}, dash={dash}, auth={authorized_even_flipped})")

    # N2 (CRIT-02, NOVEL) — a FULL-6 map of non-bool FALSY values ({all 6: 0}) clears conditions._risk AND passes the
    #     approval-time all-6 completeness guard (which tests key PRESENCE, not bool-ness) — a distinct gate-hardening
    #     gap beyond the carried 3-of-6 partial. Contained: overall HOLD -> is_scale_authorized False.
    junk = {lock: 0 for lock in RISK_LOCKS}                       # 6 keys present, all non-bool falsy
    ctx = ScaleContext(risk_flags=junk,
                       entry_evidence_refs={e: f"ref{e}" for e in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")},
                       quote_order_ok=True, public_privacy_ok=True, dq_overall=PASS)
    st, overall = risk_row(ctx)
    _, overall2, approved, refused, authorized = propose_and_try_approve(ctx)
    if st is PASS and approved and not authorized and overall is HOLD:
        record("N2", "FAIL-006", "OPEN_NONGATE",
               "CRIT-02 (novel, beyond the carried 3-of-6): a FULL-6 map of non-bool FALSY values ({lock:0 for all 6 "
               "RISK_LOCKS}) clears conditions._risk to PASS (active_risk_locks reads 0 as not-active; the map is "
               "non-empty) AND clears the approval-time re-check — _assert_risk_clear_at_approval's all-6 test checks "
               "key PRESENCE only ('all(lock in current_risk_flags)'), which junk-falsy values satisfy — so the "
               f"owner APPROVE is RECORDED (approved={approved}). Contained for FAIL-006: overall={overall.value} "
               "(Funnel/Dashboard floor) -> is_scale_authorized=False, nothing executes. Distinct from G4 (which used "
               "the mapper's real bool 3-of-6): here the all-6 completeness guard is defeated by non-bool falsies. "
               "Route OWNER/CODER: the approval all-6 guard should validate bool-ness (or route through "
               "active_risk_locks + an explicit clean-bool completeness check), not mere key presence.")
    else:
        record("N2", "FAIL-006", "BREACH" if authorized else "NOTE",
               f"full-6 junk-falsy unexpected (risk={st}, overall={overall}, approved={approved}, auth={authorized})")

    # N3 (CRIT-03 / BV-R6) — recall_risk_contribution UNCONDITIONALLY overwrites the mapper's own 3 keys from the read:
    #     a base_flags that (violating the documented contract) already asserts recall=True is ERASED by a clean read.
    read_clean = map_risk_flags(resp())                          # complete clean: recall/sale_lock/quality_hold False
    base_conflict = {"recall": True, "sale_lock": False, "quality_hold": False,
                     "complaint_p0": False, "platform_spam_flag": False, "crm_suppression": False}
    merged = recall_risk_contribution(read_clean, base_flags=base_conflict)
    st, _ = risk_row(ScaleContext(risk_flags=merged))
    if merged.get("recall") is False and st is PASS:
        record("N3", "RULE-017", "OPEN_NONGATE",
               "CRIT-03/BV-R6: recall_risk_contribution overwrites its own 3 keys UNCONDITIONALLY "
               "(merged[k]=bool(read.risk_flags.get(k))) — a base_flags that asserts recall=True is ERASED to False by "
               "a clean ops-core read, and the resulting complete-clean 6-map clears the Risk row to PASS. Safe ONLY "
               "by the docstring CONTRACT (base carries only the OTHER 3 keys, since the mapper is the authoritative "
               "ops-core source for recall/sale_lock/quality_hold) + the N1 floor — there is NO runtime guard that "
               "base didn't already assert one of the mapper's keys. Armed-not-fired (in-process, caller-assembled "
               "base; not channel-reachable; overall stays HOLD). Route CODER: fail-closed if base_flags contains any "
               "RECALL_RISK_KEYS rather than silently overwriting.")
    else:
        record("N3", "RULE-017", "NOTE", f"base overwrite unexpected (merged={merged}, risk={st})")

    # N4 (CRIT-04) — overall_status is FROZEN at propose-time and NEVER recomputed at approval: a fresh complete-clean
    #     risk read at approval clears the Risk re-check but cannot lift the stored HOLD -> is_scale_authorized False.
    gate = new_gate()
    hold_ctx = ScaleContext(risk_flags=all6_clean())             # Risk PASS but Funnel/Dashboard HOLD -> overall HOLD
    req = gate.propose("frozen", {"campaign_id": "c"}, hold_ctx, budget_cap=1.0, rollback_condition="rb", now=TS)
    propose_overall = req.overall_status
    req2 = gate.record_owner_decision("frozen", owner_decision(), current_risk_flags=all6_clean(), now=TS)
    if propose_overall is HOLD and req2.overall_status is HOLD and req2.is_scale_authorized is False \
            and req2.approval_state is ApprovalState.APPROVED:
        record("N4", "FAIL-006", "DEFENDED",
               "CRIT-04 (defensive invariant): overall_status is frozen at propose-time (record_owner_decision reads "
               "the STORED req.overall_status and never re-runs evaluate_conditions) — an APPROVE with a fresh "
               "complete-clean current_risk_flags clears the Risk re-check yet the authorization predicate keys off "
               "the immutable propose-time HOLD, so is_scale_authorized stays False. No approval-time input can "
               "escalate HOLD->PASS; a future 'recompute overall at approval' refactor must not silently open FAIL-006.")
    else:
        record("N4", "FAIL-006", "NOTE",
               f"frozen-overall unexpected (propose={propose_overall}, after={req2.overall_status}, auth={req2.is_scale_authorized})")

    # N5 (BND-08) — OwnerDecision.to_public echoes reason/audit_ref/evidence_ref RAW (only actor masked): a PII-shaped
    #     reason from the untrusted admin body exports unmasked. Channel-reachable; PII-hygiene, not a scale path.
    marker = "op" + chr(64) + "x" + chr(46) + "t"                # email-shaped, runtime-assembled (no literal in source)
    d = OwnerDecision(actor="owner_secret", reason=marker, audit_ref=marker, evidence_ref="E1",
                      decision=DecisionKind.REJECT)
    pub = d.to_public()
    if pub["reason"] == marker and pub["audit_ref"] == marker and "owner_secret" not in str(pub):
        record("N5", "FAIL-008", "OPEN_NONGATE",
               "BND-08: OwnerDecision.to_public() masks the actor but echoes reason/audit_ref/evidence_ref VERBATIM — "
               "a PII-shaped reason supplied through the untrusted admin API body (handle_scale_decision copies "
               "body.reason/audit_ref straight into OwnerDecision) exports UNMASKED via to_public/AdsScaleRequest."
               "to_public. Channel-reachable, but PII-hygiene (armed-not-fired for FAIL-006: no scale-authorization "
               "path). Route SECURITY (M6-P2606): owns the durable-export masking-scope call (mirror the scale-gate "
               "audit hardening that already drops reason/audit_ref).")
    else:
        record("N5", "FAIL-008", "NOTE", f"to_public masking unexpected (pub={pub})")

    # N6 (CRIT-06 / BV-R3) — a malformed sibling downgrades an ACTIVE recall FAIL->HOLD and renders it as 'not checked'
    #     (indistinguishable from never-observed). Fail-closed for FAIL-006 (HOLD blocks scale); observability gap.
    read = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=True, sale_lock="n/a", quality_hold=False))
    st, _ = risk_row(ScaleContext(risk_flags=read.risk_flags))
    if not read.complete and read.risk_flags == {} and st is HOLD:
        record("N6", "FAIL-006", "DEFENDED",
               "CRIT-06/BV-R3: an all-or-nothing read — a genuine recall_hold=True paired with ONE non-bool sibling "
               "(sale_lock='n/a') collapses the WHOLE read to INCOMPLETE {} -> Risk HOLD 'not checked'. Fail-closed "
               "for FAIL-006 (HOLD never authorizes a scale, and the active lock is never false-cleared). "
               "Observability NOTE: the ACTIVE recall is downgraded FAIL->HOLD and rendered identical to "
               "never-queried, so monitoring keyed on 'active lock observed' loses the malformed-with-active-lock vs "
               "unobserved distinction. Route: evidence/observability hardening (not a gate change).")
    else:
        record("N6", "FAIL-006", "NOTE", f"malformed-sibling downgrade unexpected (complete={read.complete}, risk={st})")

    # N7 (CRIT-07) — extend the no-executor / no-transport assertion across the WHOLE scale package source closure
    #     (not just the deps dataclass): no HTTP/transport/publish import anywhere in the shipped scale surface.
    import re as _re2
    scale_dir = IMPL / "app" / "measurement" / "scale"
    files = list(scale_dir.glob("*.py")) + [IMPL / "app" / "api" / "scale_requests.py"]
    transport_re = _re2.compile(r"^\s*(?:import|from)\s+(requests|httpx|urllib|http\.client|http\b|socket|aiohttp|boto|kafka)")
    offenders = []
    for f in files:
        for ln in f.read_text(encoding="utf-8").splitlines():
            if transport_re.match(ln):
                offenders.append(f"{f.name}:{ln.strip()}")
    if not offenders:
        record("N7", "FAIL-006", "DEFENDED",
               f"CRIT-07: the whole shipped scale package closure ({len(files)} files: recall_risk_mapper/conditions/"
               "scale_gate/models/scale_request_store/__init__ + api/scale_requests) binds NO HTTP/transport/queue "
               "import (requests/httpx/urllib/http.client/socket/aiohttp/boto/kafka) — the no-executor claim extends "
               "beyond the deps dataclass to the full source closure; the S1b live client exists nowhere.")
    else:
        record("N7", "FAIL-006", "BREACH", f"a transport import exists in the scale closure: {offenders}")

    # N8 (CRIT-05, SCOPE HONESTY) — the mapper has ZERO app callers (only tests import it): recall_risk_contribution's
    #     collapse-to-{} defense is DORMANT in the shipped path; live FAIL-006 containment is the floor + no-executor.
    app_dir = IMPL / "app"
    importers = []
    for f in app_dir.rglob("*.py"):
        txt = f.read_text(encoding="utf-8")
        if "recall_risk_mapper" in txt and f.name != "recall_risk_mapper.py":
            importers.append(str(f.relative_to(IMPL)))
    if not importers:
        record("N8", "FAIL-006", "NOTE",
               "CRIT-05 (scope honesty): NO app module imports recall_risk_mapper (only tests do) — the mapper is a "
               "fail-closed LIBRARY awaiting a caller. Its recall_risk_contribution collapse-to-{} and "
               "risk_picture_complete defenses are real but DORMANT in the shipped path; whatever reaches "
               "ScaleContext.risk_flags is assembled out-of-slice. So the LIVE FAIL-006 containment is (1) the N1 "
               "overall-HOLD floor and (2) the absence of any executor (N7/E1-E3) — the sign-off must not "
               "over-attribute safety to the unwired mapper. Forward: a future caller MUST be forced to route through "
               "recall_risk_contribution + risk_picture_complete (owner/coder).")
    else:
        record("N8", "FAIL-006", "NOTE", f"mapper now has app callers: {importers}")

    # N9 (BV-R4) — from_mapping's block_reasons parse is unguarded: a non-iterable truthy raises TypeError. Fail-closed
    #     LOUD (a crash yields no false-clear), but an uncaught parse on provenance-only data — robustness nit.
    raised = False
    try:
        map_pull_outcome({"recall_hold": False, "sale_lock": False, "quality_hold": False, "block_reasons": 5})
    except TypeError:
        raised = True
    if raised:
        record("N9", "FAIL-006", "NOTE",
               "BV-R4: from_mapping does tuple(mapping.get('block_reasons') or ()) — a non-iterable truthy "
               "(block_reasons=5) makes tuple(5) raise TypeError, propagating uncaught through map_pull_outcome. "
               "Fail-closed LOUD (a crash never yields a false-clear or a fabricated lock) and block_reasons is "
               "provenance-only trusted-seam data, so no FAIL-006 consequence — but an unguarded parse. Route CODER "
               "(coerce/guard block_reasons at from_mapping) for robustness parity with the strict-bool presence choke.")
    else:
        record("N9", "FAIL-006", "NOTE", "block_reasons non-iterable did not raise (inspect coercion)")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2R BOUNDARY ADVERSARY — recall-risk mapper -> Scale Gate (in-scope: FAIL-006)")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for g in (group_MAP, group_CONTRIB, group_GATE, group_EXEC, group_API, group_CARRIED, group_N):
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
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF ; SCALE_MODEL_RATIFIED False ; THRESHOLDS_DEFINED False (unchanged)")
    print("=" * 100)


if __name__ == "__main__":
    main()
