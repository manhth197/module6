"""M6-P1605 BOUNDARY_ADVERSARY executed attack harness for slice M6.2G (Scale Gate / owner-decision workflow).

READ-ONLY adversary: imports the FROZEN staged M6.2G app and drives the REAL code paths. Never modifies app code,
never writes 04-artifacts/state, never sends/scales anything (SCALE_EXECUTION_ENABLED / external_send stay OFF).

In-scope fail gate ATTACKED: M6-FAIL-006 (auto scale -- raise budget or publish optimization without approval).
In-scope rules: RULE-010 (scale is owner-only; M6 only computes conditions + creates an inert ads_scale_request;
never raises budget / enables campaign / bypasses approval), RULE-017 (suppression/risk hard veto), RULE-020
(entry-evidence gate).

Every claimed breach is EXECUTED here before it is recorded. Outcome classes:
  DEFENDED      - the invariant held; the attack was refused / fail-closed / structurally impossible.
  OPEN_NONGATE  - a real weakness that does NOT trip FAIL-006 (armed-not-fired / no-scale-authorized-regardless).
  NOTE          - an observation / robustness remark, no gate impact.
  BREACH        - FAIL-006 actually tripped (a scale authorized/executed without approval). Any BREACH => FAIL.

Launcher: py -3.12 -B (byte-clean). Owner/PII probes assembled at runtime, never echoed raw.
"""
from __future__ import annotations

import inspect
import itertools
import math
import sys
import tokenize
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
PACK_ROOT = HERE.parents[3]
IMPL = PACK_ROOT / "04-artifacts" / "impl" / "M6.2G"
if not IMPL.exists():
    IMPL = Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2G")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import (
    RISK_LOCKS,
    ScaleCondition,
    ScaleContext,
    active_risk_locks,
    evaluate_conditions,
)
from app.measurement.scale.models import (
    AdsScaleRequest,
    ApprovalState,
    DecisionKind,
    OwnerDecision,
)
from app.measurement.scale.scale_gate import ScaleGate, ScaleGateViolation
from app.measurement.scale.scale_request_store import ScaleRequestStore, ScaleRequestStoreViolation
from app.api.scale_requests import (
    ScaleRequestDeps,
    handle_scale_decision,
    handle_scale_request_create,
)

_PASS, _HOLD, _FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL
FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

RESULTS = []
BREACHES = []


def record(attack_id, gate, klass, detail):
    assert klass in ("DEFENDED", "OPEN_NONGATE", "NOTE", "BREACH"), klass
    RESULTS.append((attack_id, gate, klass, detail))
    if klass == "BREACH":
        BREACHES.append((attack_id, gate, detail))
    print(f"[{klass:12}] {attack_id:30} {gate:9} | {detail}")


# --- faithful factories (mirror tests/conftest.py) --------------------------------------------------
def best_context(**over):
    """BEST achievable staged ScaleContext (entry evidence present, boundaries attested, DQ PASS, all 6 risk
    locks observed clear, owner NOT approved). Still rolls up to HOLD (Funnel/Dashboard fail-closed)."""
    base = dict(
        entry_evidence_refs={"ENTRY-001": "e1", "ENTRY-002": "e2", "ENTRY-003": "e3", "ENTRY-004": "e4"},
        quote_order_ok=True, public_privacy_ok=True, boxes_per_order=2.0, dq_overall=_PASS,
        risk_flags={k: False for k in RISK_LOCKS}, owner_approved=False,
        budget_cap=None, rollback_condition=None,
    )
    base.update(over)
    return ScaleContext(**base)


def new_gate():
    store = ScaleRequestStore()
    return ScaleGate(store, AuditLog()), store


def owner(kind="APPROVE", **over):
    base = dict(actor="owner_ops", reason="pilot metrics reviewed", audit_ref="aud_1",
                evidence_ref="ev_1", decision=DecisionKind(kind))
    base.update(over)
    return OwnerDecision(**base)


# ================================================================================================
# GROUP A - FAIL-006 / RULE-010 : no executable scale path; no auto-scale; structurally can't authorize
# ================================================================================================
_ACTION_ATTRS = ("raise_budget", "set_budget", "enable_campaign", "open_audience", "scale", "execute",
                 "execute_scale", "send", "publish", "dispatch", "approve_all", "auto_approve",
                 "self_approve", "authorize", "trigger", "apply", "run")


def group_a():
    gate, store = new_gate()
    req = gate.propose("scr_a", {"campaign_id": "c1"}, best_context(),
                       budget_cap=1_000_000.0, rollback_condition="revert to baseline")

    # A1 no executable-scale attribute anywhere on the gate / store / request / deps
    deps = ScaleRequestDeps(scale_gate=gate, context=best_context(), audit=AuditLog())
    surfaces = {"ScaleGate": gate, "ScaleRequestStore": store, "AdsScaleRequest": req, "ScaleRequestDeps": deps}
    present = {name: [a for a in _ACTION_ATTRS if hasattr(obj, a)] for name, obj in surfaces.items()}
    any_action = any(present.values())
    record("A1-no-executable-attr", "FAIL-006",
           "BREACH" if any_action else "DEFENDED",
           f"action-verb attrs on gate/store/request/deps: {present if any_action else 'NONE'}; "
           f"SCALE_EXECUTION_ENABLED={config.SCALE_EXECUTION_ENABLED}")

    # A2 propose -> inert PROPOSED, not authorized; no self-approval
    record("A2-propose-inert", "FAIL-006",
           "DEFENDED" if req.approval_state is ApprovalState.PROPOSED and not req.is_scale_authorized else "BREACH",
           f"propose -> state={req.approval_state.value}, is_scale_authorized={req.is_scale_authorized} "
           f"(overall={req.overall_status.value})")

    # A3 even a recorded owner APPROVE -> is_scale_authorized False (overall HOLD in staged posture)
    gate2, store2 = new_gate()
    r2 = gate2.propose("scr_a3", {"campaign_id": "c1"}, best_context(),
                       budget_cap=1_000_000.0, rollback_condition="revert")
    approved = gate2.record_owner_decision("scr_a3", owner("APPROVE"),
                                           current_risk_flags={k: False for k in RISK_LOCKS})
    record("A3-approve-not-authorized", "FAIL-006",
           "DEFENDED" if approved.approval_state is ApprovalState.APPROVED and not approved.is_scale_authorized else "BREACH",
           f"recorded APPROVE -> state={approved.approval_state.value}, is_scale_authorized="
           f"{approved.is_scale_authorized} (overall={approved.overall_status.value}=HOLD, not PASS)")

    # A4 (centerpiece) structurally impossible to reach overall PASS: maximally-favorable context still HOLD
    fav = best_context(owner_approved=True, budget_cap=1_000_000.0, rollback_condition="revert")
    results, overall = evaluate_conditions(fav)
    blockers = [r.condition.value for r in results if r.status is not _PASS]
    record("A4-structural-no-pass", "FAIL-006",
           "DEFENDED" if overall is not _PASS else "BREACH",
           f"maximally-favorable context -> overall={overall.value}; non-PASS conditions={blockers} "
           f"(Funnel M6-OD-002 + Dashboard M6-OD-005 hard-wired HOLD) -> is_scale_authorized unreachable")

    # A5 (config-mutation attack) even flipping BOTH staged flags in-process, overall stays HOLD (both fail-closed
    #    branches return HOLD regardless of the flag). Restore the flags afterwards.
    saved = (config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED)
    try:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED = True
        config.SCALE_MODEL_RATIFIED = True
        results2, overall2 = evaluate_conditions(fav)
        blockers2 = [(r.condition.value, r.status.value) for r in results2 if r.status is not _PASS]
    finally:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED = saved
    record("A5-config-flip-still-hold", "FAIL-006",
           "DEFENDED" if overall2 is not _PASS else "BREACH",
           f"in-process flip of BOTH flags -> overall={overall2.value}; still-HOLD conditions={blockers2} "
           f"(Funnel/Dashboard second branches also return HOLD) -> triple fail-closed; flags restored")

    # A6 budget_cap is a recorded FIELD, never applied: approving with a huge cap changes no external state
    gate3, store3 = new_gate()
    gate3.propose("scr_a6", {"campaign_id": "c1"}, best_context(),
                  budget_cap=9_999_999_999.0, rollback_condition="revert")
    a6 = gate3.record_owner_decision("scr_a6", owner("APPROVE"),
                                     current_risk_flags={k: False for k in RISK_LOCKS})
    record("A6-budget-cap-inert", "FAIL-006",
           "DEFENDED" if not a6.is_scale_authorized and a6.budget_cap == 9_999_999_999.0 else "BREACH",
           f"budget_cap={a6.budget_cap} is a recorded ceiling only; is_scale_authorized={a6.is_scale_authorized}; "
           f"nothing applied it (no budget API on the gate)")

    # A7 RULE-020 tie-in: missing entry evidence -> P3/P5/P6 HOLD -> overall HOLD (cannot PASS)
    _, overall_missing = evaluate_conditions(best_context(entry_evidence_refs={"ENTRY-001": "e1"}))
    p3 = next(r for r in evaluate_conditions(best_context(entry_evidence_refs={"ENTRY-001": "e1"}))[0]
              if r.condition is ScaleCondition.P3_P5_P6_EVIDENCE)
    record("A7-entry-evidence-gate", "FAIL-006",
           "DEFENDED" if p3.status is _HOLD and overall_missing is not _PASS else "BREACH",
           f"missing ENTRY-002/003/004 -> P3/P5/P6={p3.status.value}, overall={overall_missing.value} (RULE-020)")


# ================================================================================================
# GROUP B - RULE-017 : Risk hard veto (never scale while a lock is active or unobserved)
# ================================================================================================
def group_b():
    # B1 each of the 6 RISK_LOCKS active (one at a time) -> Risk FAIL -> overall FAIL
    bad = []
    for lock in RISK_LOCKS:
        flags = {k: False for k in RISK_LOCKS}
        flags[lock] = True
        results, overall = evaluate_conditions(best_context(risk_flags=flags))
        risk = next(r for r in results if r.condition is ScaleCondition.RISK)
        if not (risk.status is _FAIL and overall is _FAIL):
            bad.append((lock, risk.status.value, overall.value))
    record("B1-risk-locks-veto", "RULE-017",
           "DEFENDED" if not bad else "BREACH",
           f"all 6 locks (recall/sale_lock/quality_hold/complaint_p0/platform_spam_flag/crm_suppression) -> "
           f"Risk FAIL + overall FAIL" if not bad else f"veto miss: {bad}")

    # B2 a risk-locked proposal cannot be approved (SMK-009)
    gate, store = new_gate()
    gate.propose("scr_b2", {"campaign_id": "c1"},
                 best_context(risk_flags={**{k: False for k in RISK_LOCKS}, "recall": True}),
                 budget_cap=1_000_000.0, rollback_condition="revert")
    try:
        gate.record_owner_decision("scr_b2", owner("APPROVE"),
                                   current_risk_flags={**{k: False for k in RISK_LOCKS}, "recall": True})
        record("B2-locked-cannot-approve", "RULE-017", "BREACH", "a recall-locked request was APPROVED")
    except ScaleGateViolation as e:
        record("B2-locked-cannot-approve", "RULE-017", "DEFENDED",
               f"recall-locked APPROVE refused: ScaleGateViolation ({str(e)[:60]})")

    # B3 fresh-read veto at approval: a clean proposal + a lock active at approval time -> refused
    gate, store = new_gate()
    gate.propose("scr_b3", {"campaign_id": "c1"}, best_context(),
                 budget_cap=1_000_000.0, rollback_condition="revert")
    try:
        gate.record_owner_decision("scr_b3", owner("APPROVE"),
                                   current_risk_flags={**{k: False for k in RISK_LOCKS}, "sale_lock": True})
        record("B3-fresh-read-veto", "RULE-017", "BREACH", "a late sale_lock was not caught at approval")
    except ScaleGateViolation as e:
        record("B3-fresh-read-veto", "RULE-017", "DEFENDED",
               f"late sale_lock caught at approval: refused ({str(e)[:50]})")

    # B4 (re-verify coder fix) empty fresh read + proposal Risk HOLD -> fail-closed refuse
    gate, store = new_gate()
    gate.propose("scr_b4", {"campaign_id": "c1"}, best_context(risk_flags={}),  # empty -> proposal Risk HOLD
                 budget_cap=1_000_000.0, rollback_condition="revert")
    try:
        gate.record_owner_decision("scr_b4", owner("APPROVE"), current_risk_flags={})  # empty fresh read
        record("B4-empty-read-failclosed", "RULE-017", "BREACH",
               "empty fresh read + HOLD proposal was approved (fail-open)")
    except ScaleGateViolation as e:
        record("B4-empty-read-failclosed", "RULE-017", "DEFENDED",
               f"empty fresh read + HOLD proposal refused (fail-closed): ({str(e)[:50]})")

    # B5 residual: a COMPLETE-clean proposal (Risk PASS) + an EMPTY fresh read at approval falls back to the STALE
    #    proposal PASS and approves, even if a lock became active meanwhile (the empty read hides it). No scale is
    #    authorized regardless (overall HOLD), but the fresh-read veto is only complete when the fresh read is.
    gate, store = new_gate()
    gate.propose("scr_b5", {"campaign_id": "c1"}, best_context(),  # complete-clean -> proposal Risk PASS
                 budget_cap=1_000_000.0, rollback_condition="revert")
    stale_ok = False
    try:
        res = gate.record_owner_decision("scr_b5", owner("APPROVE"), current_risk_flags={})  # empty hides a late lock
        stale_ok = res.approval_state is ApprovalState.APPROVED and not res.is_scale_authorized
    except ScaleGateViolation:
        stale_ok = None   # refused -> fully fail-closed
    if stale_ok is None:
        record("B5-stale-proposal-fallback", "RULE-017", "DEFENDED",
               "empty fresh read after a clean proposal is REFUSED (fully fail-closed)")
    else:
        record("B5-stale-proposal-fallback", "RULE-017", "OPEN_NONGATE",
               "empty fresh read falls back to the STALE proposal Risk PASS -> APPROVE recorded (a NEW lock hidden "
               "by the empty read is not re-caught); NO scale authorized (overall HOLD); fresh-read veto is only "
               "complete when the fresh read is -> route CODER/M6-P1606 (require a COMPLETE fresh read to approve)")

    # B6 frozen-record bypass of approval_state / overall_status requires object.__setattr__ (in-process code exec)
    gate, store = new_gate()
    req = gate.propose("scr_b6", {"campaign_id": "c1"}, best_context(),
                       budget_cap=1_000_000.0, rollback_condition="revert")
    try:
        req.overall_status = _PASS   # frozen
        record("B6-frozen-record", "FAIL-006", "BREACH", "mutated overall_status on a frozen request")
    except FrozenInstanceError:
        object.__setattr__(req, "overall_status", _PASS)
        object.__setattr__(req, "approval_state", ApprovalState.APPROVED)
        object.__setattr__(req, "decision", owner("APPROVE"))
        forged = req.is_scale_authorized
        record("B6-frozen-record", "FAIL-006", "NOTE",
               f"frozen blocks normal assignment; object.__setattr__ can forge is_scale_authorized={forged} but needs "
               f"arbitrary in-process code exec (all in-memory invariants moot) AND still executes nothing (no scale "
               f"path) -> defense-in-depth limit, not channel-reachable")


# ================================================================================================
# GROUP C - RULE-010 / RULE-015 : owner-approval discipline (never self-approve; terminal states)
# ================================================================================================
def group_c():
    # C1 REJECT is recorded, never a scale
    gate, store = new_gate()
    gate.propose("scr_c1", {"campaign_id": "c1"}, best_context(),
                 budget_cap=1_000_000.0, rollback_condition="revert")
    rej = gate.record_owner_decision("scr_c1", owner("REJECT"), current_risk_flags={k: False for k in RISK_LOCKS})
    record("C1-reject-recorded", "RULE-015",
           "DEFENDED" if rej.approval_state is ApprovalState.REJECTED and not rej.is_scale_authorized else "BREACH",
           f"owner REJECT -> state={rej.approval_state.value}, is_scale_authorized={rej.is_scale_authorized}")

    # C2 cannot re-decide a terminal request
    try:
        gate.record_owner_decision("scr_c1", owner("APPROVE"), current_risk_flags={k: False for k in RISK_LOCKS})
        record("C2-no-redecide", "RULE-015", "BREACH", "re-decided an already-REJECTED request")
    except ScaleGateViolation as e:
        record("C2-no-redecide", "RULE-015", "DEFENDED", f"re-decide refused: ({str(e)[:50]})")

    # C3 approve requires budget_cap AND rollback_condition
    gate, store = new_gate()
    gate.propose("scr_c3", {"campaign_id": "c1"}, best_context(), budget_cap=None, rollback_condition=None)
    try:
        gate.record_owner_decision("scr_c3", owner("APPROVE"), current_risk_flags={k: False for k in RISK_LOCKS})
        record("C3-approve-needs-cap-rollback", "RULE-010", "BREACH", "approved without budget_cap/rollback")
    except ScaleGateViolation as e:
        record("C3-approve-needs-cap-rollback", "RULE-010", "DEFENDED",
               f"approve without cap/rollback refused: ({str(e)[:50]})")

    # C4 cannot approve a FAIL (risk-locked) request even if a stale/None fresh read is passed
    gate, store = new_gate()
    gate.propose("scr_c4", {"campaign_id": "c1"},
                 best_context(risk_flags={**{k: False for k in RISK_LOCKS}, "quality_hold": True}),
                 budget_cap=1_000_000.0, rollback_condition="revert")
    try:
        gate.record_owner_decision("scr_c4", owner("APPROVE"), current_risk_flags=None)  # no fresh read
        record("C4-no-approve-fail-request", "RULE-010", "BREACH", "approved a FAIL (quality_hold) request")
    except ScaleGateViolation as e:
        record("C4-no-approve-fail-request", "RULE-010", "DEFENDED",
               f"FAIL request refused (proposal Risk FAIL, fail-closed): ({str(e)[:50]})")


# ================================================================================================
# GROUP D - API / RULE-H03 : untrusted body cannot fake a condition or synthesize an approval
# ================================================================================================
def group_d():
    gate, store = new_gate()
    deps = ScaleRequestDeps(scale_gate=gate, context=best_context(), audit=AuditLog())

    # D1 create body claiming approval/PASS/clean-risk cannot fake a condition (conditions come from deps.context)
    evil_body = {"campaign_id": "c1", "owner_approved": True, "overall_status": "PASS",
                 "risk_flags": {}, "budget_cap": 5_000_000, "rollback_condition": "x",
                 "condition_results": "ALL_PASS", "is_scale_authorized": True}
    resp = handle_scale_request_create(evil_body, deps)
    req = store.get(resp.request_id)
    record("D1-body-cannot-fake-condition", "FAIL-006",
           "DEFENDED" if resp.overall_status == "HOLD" and not req.is_scale_authorized else "BREACH",
           f"malicious create body -> overall={resp.overall_status} (from server ctx), "
           f"is_scale_authorized={req.is_scale_authorized}; body claims ignored")

    # D2 decision requires all owner fields; a partial body is rejected, no decision recorded
    partial = handle_scale_decision({"request_id": resp.request_id, "decision": "APPROVE", "actor": "o"}, deps)
    bad_kind = handle_scale_decision({"request_id": resp.request_id, "decision": "SCALE_NOW", "actor": "o",
                                      "reason": "r", "audit_ref": "a", "evidence_ref": "e"}, deps)
    still = store.get(resp.request_id)
    record("D2-owner-fields-required", "RULE-015",
           "DEFENDED" if partial.error_code == "OWNER_DECISION_INCOMPLETE" and bad_kind.error_code == "SCHEMA_INVALID"
           and still.approval_state is ApprovalState.PROPOSED else "BREACH",
           f"partial owner body -> {partial.error_code}; bad decision kind -> {bad_kind.error_code}; "
           f"state still {still.approval_state.value}")

    # D3 API cannot approve a risk-locked request -> APPROVAL_REFUSED (refusal surfaced, not a silent scale)
    gate2, store2 = new_gate()
    locked_ctx = best_context(risk_flags={**{k: False for k in RISK_LOCKS}, "platform_spam_flag": True})
    deps2 = ScaleRequestDeps(scale_gate=gate2, context=locked_ctx, audit=AuditLog())
    c = handle_scale_request_create({"campaign_id": "c1", "budget_cap": 1_000_000, "rollback_condition": "revert"}, deps2)
    d = handle_scale_decision({"request_id": c.request_id, "decision": "APPROVE", "actor": "o", "reason": "r",
                               "audit_ref": "a", "evidence_ref": "e"}, deps2)
    record("D3-api-refuses-locked", "RULE-017",
           "DEFENDED" if d.error_code == "APPROVAL_REFUSED" and store2.get(c.request_id).approval_state is ApprovalState.PROPOSED else "BREACH",
           f"API APPROVE on a spam-flag-locked request -> {d.status}/{d.error_code}; "
           f"state stays {store2.get(c.request_id).approval_state.value}")

    # D4 budget_cap type guard: bool / non-number rejected at the API
    b_bool = handle_scale_request_create({"campaign_id": "c1", "budget_cap": True}, deps)
    b_str = handle_scale_request_create({"campaign_id": "c1", "budget_cap": "1e9"}, deps)
    record("D4-budget-cap-typeguard", "FAIL-006",
           "DEFENDED" if b_bool.error_code == "SCHEMA_INVALID" and b_str.error_code == "SCHEMA_INVALID" else "NOTE",
           f"budget_cap bool -> {b_bool.error_code}; str -> {b_str.error_code} (a number cap is a recorded field only)")

    # D5 (re-verify coder fix) untrusted owner reason/audit_ref does NOT reach the audit detail; actor masked
    gate3, store3 = new_gate()
    audit3 = AuditLog()
    gate3._audit = audit3
    ctx3 = best_context()
    gate3.propose("scr_d5", {"campaign_id": "c1"}, ctx3, budget_cap=1_000_000.0, rollback_condition="revert")
    # PII-shaped free text, digit run assembled at runtime so NO phone literal sits in this source
    pii_reason = "call" + "".join(str(d) for d in (9, 1, 2, 3, 4, 5, 6, 7, 8, 0)) + "now"
    gate3.record_owner_decision("scr_d5", owner("APPROVE", actor="owner_secretid", reason=pii_reason,
                                               audit_ref="aud_secret"),
                                current_risk_flags={k: False for k in RISK_LOCKS})
    details = " ".join((r.detail or "") for r in audit3.records)
    subjects = " ".join((r.subject_masked or "") for r in audit3.records)
    leaked = pii_reason in details or "aud_secret" in details or "owner_secretid" in subjects
    record("D5-audit-machine-safe", "RULE-014",
           "DEFENDED" if not leaked else "BREACH",
           f"owner free-text reason/audit_ref absent from audit detail; actor masked in subject; leaked={leaked}")


# ================================================================================================
# GROUP E - belt sweeps: no action identifiers / no posture-flag writes; PII masking on export
# ================================================================================================
def group_e():
    action_verbs = ("raise_budget", "set_budget", "enable_campaign", "open_audience", "execute_scale",
                    "scale_now", "publish_optim", "order_state", "write_order", "crm_send", "set_price",
                    "commission")
    posture_flags = ("GLOBAL_GATEWAY_STATE", "PRODUCTION_FLAG", "EXTERNAL_SEND", "SCALE_EXECUTION_ENABLED",
                     "SCALE_MODEL_RATIFIED", "DASHBOARD_ALERT_THRESHOLDS_DEFINED")
    targets = [
        IMPL / "app" / "measurement" / "scale" / "conditions.py",
        IMPL / "app" / "measurement" / "scale" / "scale_gate.py",
        IMPL / "app" / "measurement" / "scale" / "models.py",
        IMPL / "app" / "measurement" / "scale" / "scale_request_store.py",
        IMPL / "app" / "api" / "scale_requests.py",
    ]
    action_hits, flag_writes = [], []
    for p in targets:
        with tokenize.open(str(p)) as fh:
            toks = list(tokenize.generate_tokens(fh.readline))
        for i, tok in enumerate(toks):
            if tok.type == tokenize.NAME and tok.string.lower() in action_verbs:
                action_hits.append(f"{p.name}:{tok.start[0]}:{tok.string}")
            # a posture flag on the LHS of an assignment (config.X = ... or X = ...) would be a write
            if tok.type == tokenize.NAME and tok.string in posture_flags:
                nxt = toks[i + 1] if i + 1 < len(toks) else None
                if nxt is not None and nxt.type == tokenize.OP and nxt.string == "=":
                    flag_writes.append(f"{p.name}:{tok.start[0]}:{tok.string}=")
    record("E1-no-action-no-flagwrite", "RULE-010",
           "DEFENDED" if not action_hits and not flag_writes else "NOTE",
           f"token sweep of 5 scale modules: action defs={action_hits or 'NONE'}; posture-flag writes="
           f"{flag_writes or 'NONE'}")

    # E2 owner actor masked on export; scale_target ids are campaign refs (not PII); no raw actor in to_public
    gate, store = new_gate()
    gate.propose("scr_e2", {"campaign_id": "c1", "adset_id": "a1"}, best_context(),
                 budget_cap=1_000_000.0, rollback_condition="revert")
    gate.record_owner_decision("scr_e2", owner("APPROVE", actor="owner_distinctid"),
                               current_risk_flags={k: False for k in RISK_LOCKS})
    pub = repr(store.get("scr_e2").to_public())
    masked = "own***id" in pub  # first3+last2 of owner_distinctid
    record("E2-export-masking", "RULE-014",
           "DEFENDED" if "owner_distinctid" not in pub and masked else "NOTE",
           f"AdsScaleRequest.to_public: raw actor absent={'owner_distinctid' not in pub}, masked-present={masked} "
           f"(scale_target campaign refs are not PII); belt -> M6-P1606")


# ================================================================================================
# GROUP W - workflow-harvested vectors (6-agent adversarial ideation + completeness critic; 49 vectors).
#           Every claimed breach EXECUTED here before recording; reachability checked against the real wiring.
# ================================================================================================
def group_w():
    import app.measurement.scale.conditions as C

    # W1 (CC-01) EXHAUSTIVE proof: overall is NEVER PASS across the full 1296-cell ScaleContext cross-product
    #    (the Funnel+Dashboard config rows pin it to HOLD-at-best regardless of the other 6 rows).
    entry_full = {"ENTRY-001": "e1", "ENTRY-002": "e2", "ENTRY-003": "e3", "ENTRY-004": "e4"}
    bools = [True, False, None]
    dqs = [_PASS, _HOLD, _FAIL, None]
    found_pass = []
    n = 0
    for qo, pp, dq, ee, rf, oa, box in itertools.product(
        bools, bools, dqs, [entry_full, {}],
        [{k: False for k in RISK_LOCKS}, {"recall": True}, {}], [True, False], [2.0, 1.0, None]
    ):
        n += 1
        _, overall = evaluate_conditions(ScaleContext(
            entry_evidence_refs=ee, quote_order_ok=qo, public_privacy_ok=pp, boxes_per_order=box,
            dq_overall=dq, risk_flags=rf, owner_approved=oa, budget_cap=1.0, rollback_condition="x"))
        if overall is _PASS:
            found_pass.append((qo, pp, dq, ee, rf, oa, box))
    record("W1-exhaustive-no-pass", "FAIL-006",
           "DEFENDED" if not found_pass else "BREACH",
           f"exhaustive {n}-cell ScaleContext cross-product -> overall==PASS count={len(found_pass)} "
           f"(structurally unreachable; is_scale_authorized can never be True in the staged posture)")

    # W2 (CC-05) approval LAUNDERING / bait-and-switch: a GENUINE owner APPROVE then dataclasses.replace swaps the
    #    scale_target + budget_cap and store.update_state persists it -- the store pins neither to what the owner
    #    reviewed. In-process only (update_state is not wire-exposed; the API only calls record_owner_decision which
    #    changes solely approval_state/decision/decided_at). No scale authorized (overall HOLD). Binding gap for M6-OD-011.
    gate, store = new_gate()
    gate.propose("scr_bait", {"campaign_id": "cmp_SMALL"}, best_context(),
                 budget_cap=100.0, rollback_condition="halt if CPA>x")
    appr = gate.record_owner_decision("scr_bait", owner("APPROVE", reason="reviewed small pilot"),
                                      current_risk_flags={k: False for k in RISK_LOCKS})
    swapped = replace(appr, scale_target={"campaign_id": "cmp_HUGE"}, budget_cap=10_000_000.0)
    store.update_state(swapped)
    got = store.get("scr_bait")
    laundered = (got.scale_target == {"campaign_id": "cmp_HUGE"} and got.budget_cap == 10_000_000.0
                 and got.decision.decision is DecisionKind.APPROVE)
    record("W2-approval-laundering", "FAIL-006",
           "OPEN_NONGATE" if laundered and not got.is_scale_authorized else ("BREACH" if got.is_scale_authorized else "NOTE"),
           f"replace()+update_state swaps a REAL APPROVE onto target={got.scale_target} cap={got.budget_cap} "
           f"(owner reviewed cmp_SMALL/100.0); store pins neither; is_scale_authorized={got.is_scale_authorized} "
           f"(overall HOLD, no executor); in-process only (update_state not wire-exposed) -> route CODER "
           f"(update_state must reject target/cap/condition mutation) + M6-OD-011")

    # W3 (CC-02/CC-03) module-global kill-switches: emptying RISK_LOCKS disables the RULE-017 veto; emptying
    #    REQUIRED_ENTRY_EVIDENCE disables the RULE-020 gate. Requires in-process code exec; module tuples are mutable
    #    (Final is a hint). No scale authorized regardless (Funnel/Dashboard still HOLD). Save/restore.
    saved_locks, saved_entry = C.RISK_LOCKS, C.REQUIRED_ENTRY_EVIDENCE
    try:
        C.RISK_LOCKS = ()
        res_r, _ = evaluate_conditions(ScaleContext(risk_flags={"recall": True, "sale_lock": True}))
        risk_bypassed = next(r for r in res_r if r.condition is ScaleCondition.RISK).status is _PASS
        C.REQUIRED_ENTRY_EVIDENCE = ()
        res_e, _ = evaluate_conditions(ScaleContext(entry_evidence_refs={}))
        entry_bypassed = next(r for r in res_e if r.condition is ScaleCondition.P3_P5_P6_EVIDENCE).status is _PASS
    finally:
        C.RISK_LOCKS, C.REQUIRED_ENTRY_EVIDENCE = saved_locks, saved_entry
    record("W3-module-global-killswitch", "FAIL-006", "NOTE",
           f"in-process C.RISK_LOCKS=() -> active recall+sale_lock read as Risk PASS (bypassed={risk_bypassed}); "
           f"C.REQUIRED_ENTRY_EVIDENCE=() -> P3/P5/P6 PASS with zero entry evidence (bypassed={entry_bypassed}); "
           f"module tuples mutable (Final unenforced), needs arbitrary in-process code exec, no scale authorized "
           f"(Funnel/Dashboard HOLD) -> defense-in-depth; harden: source from a frozen/validated registry; restored")

    # W4 (CC-06) budget_cap has no positivity/finiteness validation: -1 / 0 / inf / NaN all pass as a 'present' cap
    #    (handler checks only numeric-not-bool; is_scale_authorized checks only 'is not None'). Inert today.
    gate, store = new_gate()
    deps = ScaleRequestDeps(scale_gate=gate, context=best_context(), audit=AuditLog())
    caps = {}
    for cap in (-1.0, 0.0, float("inf"), float("nan")):
        resp = handle_scale_request_create({"campaign_id": "c1", "budget_cap": cap, "rollback_condition": "r"}, deps)
        r = store.get(resp.request_id)
        present = r.budget_cap is not None  # is_scale_authorized's cap precondition
        caps[repr(cap)] = (resp.status, present)
    all_accepted = all(s == "CREATED" and present for s, present in caps.values())
    record("W4-budget-cap-unvalidated", "FAIL-006",
           "OPEN_NONGATE" if all_accepted else "NOTE",
           f"budget_cap -1/0/inf/NaN all CREATED and satisfy the 'present cap' precondition {caps}; no isfinite/>0 "
           f"check anywhere; the number destined to become a real ceiling at M6-OD-011 is unvalidated; inert today "
           f"(overall HOLD, no executor) -> route CODER/M6-P1606 (require isfinite AND >0)")

    # W5 (CC-08) rollback_condition is validated for truthiness only: a whitespace ' ' clears the RULE-010 safety
    #    pairing (a meaningless 'rollback plan'). Inert today; accountability/safety validation gap.
    gate, store = new_gate()
    deps = ScaleRequestDeps(scale_gate=gate, context=best_context(), audit=AuditLog())
    created = handle_scale_request_create({"campaign_id": "c1", "budget_cap": 100.0, "rollback_condition": " "}, deps)
    dec = handle_scale_decision({"request_id": created.request_id, "decision": "APPROVE", "actor": "o",
                                 "reason": "r", "audit_ref": "a", "evidence_ref": "e"}, deps)
    ws_cleared = store.get(created.request_id).rollback_condition == " " and dec.approval_state == "APPROVED"
    record("W5-whitespace-rollback", "FAIL-006",
           "OPEN_NONGATE" if ws_cleared else "NOTE",
           f"whitespace rollback_condition=' ' is accepted and clears the RULE-010 cap+rollback pairing "
           f"(APPROVE recorded={dec.approval_state}); is_scale_authorized still False (overall HOLD); a meaningless "
           f"halt plan satisfies the safety requirement -> route CODER/M6-P1606 (content-validate rollback)")

    # W6 (CC-04/CC-07) the decisive FAIL-006 negative: the scale surface has NO wire deserializer (so every forge/
    #    laundering vector is in-process only) AND reads NO posture flag to branch into an action (no executor to arm).
    import app.measurement.scale.scale_gate as G
    import app.measurement.scale.models as M
    import app.measurement.scale.scale_request_store as St
    import app.api.scale_requests as Api
    surface_src = "".join(inspect.getsource(m) for m in (G, M, St, Api))
    deser = [t for t in ("from_public", "from_dict", "from_json", "json.loads", "pickle",
                         "__setstate__", "model_validate", "parse_obj", "eval(") if t in surface_src]
    posture = [t for t in ("PRODUCTION_FLAG", "GLOBAL_GATEWAY_STATE", "EXTERNAL_SEND",
                          "is_external_send_enabled", "SCALE_EXECUTION_ENABLED") if t in surface_src]
    cond_src = inspect.getsource(C)
    dead_import = "from app import config" in inspect.getsource(G) and "config." not in inspect.getsource(G)
    record("W6-no-deser-no-posture-reader", "FAIL-006",
           "DEFENDED" if not deser and not posture else "BREACH",
           f"scale surface: wire-deserializers={deser or 'NONE'} (forge family is in-process-only, not wire-reachable); "
           f"posture-flag reads={posture or 'NONE'} (no executor to arm); conditions.py reads config only for the 2 "
           f"OPEN-decision rows (count={cond_src.count('config.')}); scale_gate dead `import config`={dead_import} "
           f"(cosmetic) -> FAIL-006 has NO reachable executor")


def main():
    print("=" * 100)
    print("M6-P1605 BOUNDARY_ADVERSARY - executed attacks vs FROZEN staged M6.2G (Scale Gate)")
    print(f"impl root: {IMPL}")
    print(f"posture: gateway={config.GLOBAL_GATEWAY_STATE} prod={config.PRODUCTION_FLAG} "
          f"external_send={config.EXTERNAL_SEND} SCALE_EXECUTION_ENABLED={config.SCALE_EXECUTION_ENABLED} "
          f"SCALE_MODEL_RATIFIED={config.SCALE_MODEL_RATIFIED} "
          f"DASHBOARD_ALERT_THRESHOLDS_DEFINED={config.DASHBOARD_ALERT_THRESHOLDS_DEFINED}")
    print("=" * 100)
    for grp in (group_a, group_b, group_c, group_d, group_e, group_w):
        print(f"\n----- {grp.__name__} -----")
        grp()

    from collections import Counter
    tally = Counter(k for _, _, k, _ in RESULTS)
    print("\n" + "=" * 100)
    print(f"SUMMARY: {dict(tally)}")
    print(f"TOTAL RECORDED OUTCOMES: {len(RESULTS)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-006): {len(BREACHES)}")
    for b in BREACHES:
        print(f"   !!! BREACH {b}")
    print("=" * 100)
    # posture must be unchanged by anything we did (A5 saves/restores)
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF" and config.SCALE_EXECUTION_ENABLED is False
    assert config.SCALE_MODEL_RATIFIED is False and config.DASHBOARD_ALERT_THRESHOLDS_DEFINED is False


if __name__ == "__main__":
    main()
