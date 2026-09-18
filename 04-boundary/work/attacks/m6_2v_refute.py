"""M6.2V REFUTATION harness (READ-ONLY; operator ad-hoc adversarial verification).

Tries to REFUTE three claims about the M6.2V fix (which closes the M6.2U N1/A2 findings):
  (i)  stricter-only vs M6.2U         -> stricter_only_holds
  (ii) veto now two-deep (propagate through recall_risk_contribution + refuse at approval) -> veto_two_deep
  (iii) no nerfed test                -> no_nerfed_test (static diff analysis, reported separately)

Method: EXECUTE the real M6.2V staged code AND re-implement the M6.2U (OLD) recall_risk_contribution + approval
clear-check inline, then diff OLD vs NEW over a truth table. A single input where NEW clears/passes MORE than OLD is a
LOOSENING -> BLOCKER. Also enumerate every path to the gate and confirm not_sellable is never silently dropped.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2v_refute.py
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
    cand = anc / "04-artifacts" / "impl" / "M6.2V"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2V/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.scale.conditions import (
    RISK_LOCKS, ScaleCondition, ScaleContext, evaluate_conditions,
)
from app.measurement.scale.scale_gate import ScaleGate, ScaleGateViolation
from app.measurement.scale.models import ApprovalState, DecisionKind, OwnerDecision
from app.measurement.scale.scale_request_store import ScaleRequestStore
from app.measurement.scale.recall_risk_mapper import (
    OpsCoreAvailabilityResponse, RECALL_RISK_KEYS, RecallRiskContributionError,
    map_risk_flags, map_pull_outcome, recall_risk_contribution, risk_picture_complete,
)

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
PASS, HOLD, FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL
SEV = {PASS: 0, HOLD: 1, FAIL: 2}
OTHER3 = ("complaint_p0", "platform_spam_flag", "crm_suppression")
OUTCOMES = []
LOOSENING = []


def record(vec, klass, detail):
    OUTCOMES.append((vec, klass, detail))
    print(f"[{klass:12}] {vec:16} {detail}")


def risk_of(risk_flags):
    results, _ = evaluate_conditions(ScaleContext(risk_flags=risk_flags))
    return next(c for c in results if c.condition is ScaleCondition.RISK).status


# --- OLD (M6.2U) re-implementations (faithful to the M6.2U source I read) ---------------------------
def old_contribution(read, base_flags=None):
    """M6.2U recall_risk_contribution — NO veto propagation, NO short-circuit (the buggy version)."""
    if base_flags is not None:
        clash = [k for k in RECALL_RISK_KEYS if k in base_flags]
        if clash:
            raise RecallRiskContributionError(clash)
    merged = dict(base_flags or {})
    if read.complete:
        for k in RECALL_RISK_KEYS:
            merged[k] = bool(read.risk_flags.get(k))
    if any(merged.get(lock) for lock in RISK_LOCKS):
        return merged
    if risk_picture_complete(merged):
        return merged
    return {}


def old_approval_clears(current):
    """M6.2U/M6.2T _assert_risk_clear_at_approval fresh-read branch — NO not_sellable refuse."""
    if current is not None:
        if any(current.get(l) for l in RISK_LOCKS):
            return False
        if all(l in current and isinstance(current[l], bool) for l in RISK_LOCKS):
            return True
    return None   # None = falls back to the proposal Risk (not modelled here; the diff is the fresh-read branch)


# --- gate helpers ------------------------------------------------------------------------------------
def owner_decision():
    return OwnerDecision(actor="o", reason="r", audit_ref="a", evidence_ref="e", decision=DecisionKind.APPROVE, at=TS)


def full_ctx(risk_flags):
    return ScaleContext(
        risk_flags=risk_flags,
        entry_evidence_refs={e: f"r{e}" for e in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")},
        quote_order_ok=True, public_privacy_ok=True, dq_overall=PASS,
        budget_cap=1.0, rollback_condition="rb")


def gate_refuses_approve(propose_flags, current):
    store = ScaleRequestStore()
    gate = ScaleGate(store, AuditLog())
    gate.propose("rq", {"campaign_id": "c"}, full_ctx(propose_flags), budget_cap=1.0, rollback_condition="rb", now=TS)
    try:
        gate.record_owner_decision("rq", owner_decision(), current_risk_flags=current, now=TS)
        return store.get("rq").approval_state is not ApprovalState.APPROVED
    except ScaleGateViolation:
        return True


def resp(recall_hold=False, sale_lock=False, quality_hold=False, decision="SELLABLE"):
    return OpsCoreAvailabilityResponse(recall_hold=recall_hold, sale_lock=sale_lock, quality_hold=quality_hold,
                                       decision=decision)


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2V REFUTATION — try to break (i) stricter-only, (ii) veto two-deep, (iii) no nerfed test")
    print(f"impl root: {IMPL}")
    print("=" * 100)

    # ---- CLAIM (ii): the N1 chí-mạng case — NOT_SELLABLE + full-6-clean base via recall_risk_contribution -> FAIL ---
    ns = map_risk_flags(resp(decision="NOT_SELLABLE"))
    n1_map = recall_risk_contribution(ns, base_flags={l: False for l in OTHER3})
    n1_complete = all(l in n1_map for l in RISK_LOCKS) and not any(n1_map.get(l) for l in RISK_LOCKS)
    n1_risk = risk_of(n1_map)
    if n1_map.get("not_sellable") is True and n1_complete and n1_risk is FAIL:
        record("N1-critical", "DEFENDED",
               "REFUTE FAILED (fix holds): a NOT_SELLABLE read + a COMPLETE other-3-clean base via "
               "recall_risk_contribution -> the merged map is a complete 6-lock no-active picture that CARRIES "
               "not_sellable=True and returns BEFORE the completeness branch -> Risk FAIL (NOT the M6.2U inversion to "
               "PASS). The veto is no longer swallowed by completeness.")
    else:
        record("N1-critical", "BLOCKER",
               f"the N1 inversion is NOT fixed: NOT_SELLABLE+complete-base -> risk={n1_risk} (expected FAIL), "
               f"not_sellable={n1_map.get('not_sellable')}")

    # ---- CLAIM (ii) approval leg — not_sellable must REFUSE at approval (two-deep) --------------------------------
    #   (a) a not_sellable propose -> overall FAIL -> refused; (b) a FRESH not_sellable at approval (complete-6) -> refused
    refuse_propose = gate_refuses_approve({**{l: False for l in RISK_LOCKS}, "not_sellable": True},
                                          {**{l: False for l in RISK_LOCKS}, "not_sellable": True})
    refuse_fresh = gate_refuses_approve({l: False for l in RISK_LOCKS},                    # SELLABLE-clean propose
                                        {**{l: False for l in RISK_LOCKS}, "not_sellable": True})   # fresh veto
    if refuse_propose and refuse_fresh:
        record("approval-two-deep", "DEFENDED",
               "REFUTE FAILED (A2 holds): the approval REFUSES a not_sellable lot both (a) when the propose context "
               "carries it (overall FAIL) AND (b) when it appears ONLY as a FRESH read at approval over an otherwise "
               "complete-6 no-active map (_assert_risk_clear_at_approval now raises on not_sellable before the all-6 "
               "clear). The veto is enforced at BOTH propose-time _risk and approval-time re-check = two-deep.")
    else:
        record("approval-two-deep", "BLOCKER",
               f"approval does not refuse not_sellable (propose={refuse_propose}, fresh={refuse_fresh})")

    # ---- DROP-PATH enumeration — every path from a NOT_SELLABLE / unverified read to the gate carries the veto -----
    paths = {}
    paths["direct read.risk_flags"] = risk_of(dict(map_risk_flags(resp(decision="NOT_SELLABLE")).risk_flags))
    paths["contribution no base"] = risk_of(recall_risk_contribution(map_risk_flags(resp(decision="NOT_SELLABLE"))))
    paths["contribution +other3 base"] = risk_of(recall_risk_contribution(
        map_risk_flags(resp(decision="NOT_SELLABLE")), base_flags={l: False for l in OTHER3}))
    paths["pull-error no base"] = risk_of(recall_risk_contribution(map_pull_outcome(error="HTTP_429")))
    paths["pull-error +other3 base"] = risk_of(recall_risk_contribution(
        map_pull_outcome(error="TIMEOUT"), base_flags={l: False for l in OTHER3}))
    # a base that already carries not_sellable + a SELLABLE read -> preserved
    paths["base-carried veto + SELLABLE read"] = risk_of(recall_risk_contribution(
        map_risk_flags(resp(decision="SELLABLE")), base_flags={**{l: False for l in OTHER3}, "not_sellable": True}))
    dropped = [p for p, st in paths.items() if st is not FAIL]
    if not dropped:
        record("drop-path-scan", "DEFENDED",
               "REFUTE FAILED (no drop path): EVERY gate-reaching path for a NOT_SELLABLE / unverified / base-carried "
               f"veto ends in Risk FAIL — {', '.join(f'{p}={st.value}' for p, st in paths.items())}. The veto is not "
               "silently dropped on any of: direct feed, contribution (complete/incomplete, with/without base), or a "
               "base-carried veto. (The one exception is a hand-built str-subclass decision that prevents the veto "
               "from being CREATED at the mapper — N5-residual below, in-process only.)")
    else:
        record("drop-path-scan", "BLOCKER", f"a path drops the veto (not FAIL): {dropped}")

    # ---- CLAIM (i) STRICTER-ONLY truth table: OLD(M6.2U) vs NEW(M6.2V) over a read x base grid --------------------
    reads = {
        "SELLABLE-clean": map_risk_flags(resp(decision="SELLABLE")),
        "NOT_SELLABLE-clean": map_risk_flags(resp(decision="NOT_SELLABLE")),
        "SELLABLE-recall-active": map_risk_flags(resp(recall_hold=True, decision="SELLABLE")),
        "NOT_SELLABLE-recall-active": map_risk_flags(resp(recall_hold=True, decision="NOT_SELLABLE")),
        "pull-error": map_pull_outcome(error="HTTP_429"),
    }
    bases = {"no-base": None, "other3-clean": {l: False for l in OTHER3}}
    print("\n  truth table (read x base): OLD(M6.2U) -> NEW(M6.2V) gate Risk status")
    for rname, read in reads.items():
        for bname, base in bases.items():
            try:
                old_risk = risk_of(old_contribution(read, base))
                new_risk = risk_of(recall_risk_contribution(read, base))
            except RecallRiskContributionError:
                continue
            flag = ""
            if SEV[new_risk] < SEV[old_risk]:
                LOOSENING.append(f"{rname} x {bname}: OLD={old_risk.value} NEW={new_risk.value}")
                flag = "  <<< LOOSENING"
            print(f"    {rname:28} x {bname:14}  OLD={old_risk.value:5} -> NEW={new_risk.value:5}{flag}")
    # approval clear-set (fresh-read branch): NEW must clear a subset of OLD
    approval_cases = {
        "all6-clean": {l: False for l in RISK_LOCKS},
        "all6-clean+not_sellable": {**{l: False for l in RISK_LOCKS}, "not_sellable": True},
        "active-recall": {**{l: False for l in RISK_LOCKS}, "recall": True},
    }
    approval_loosen = []
    for cname, cur in approval_cases.items():
        old_c = old_approval_clears(cur) is True
        # NEW: refuses on not_sellable; else same as OLD
        new_refuses = gate_refuses_approve({l: False for l in RISK_LOCKS}, cur)   # SELLABLE-clean proposal (Risk PASS)
        new_c = not new_refuses
        if new_c and not old_c:
            approval_loosen.append(f"approval {cname}: OLD-clears={old_c} NEW-clears={new_c}")
        print(f"    approval {cname:24}  OLD-clears={old_c} -> NEW-clears={new_c}")
    LOOSENING.extend(approval_loosen)
    if not LOOSENING:
        record("stricter-only", "DEFENDED",
               "REFUTE FAILED (stricter-only holds): across the read x base grid + the approval clear-set, NEW(M6.2V) "
               "severity >= OLD(M6.2U) for EVERY input, and NEW clears a SUBSET of OLD (the not_sellable refuse only "
               "ADDs). No input clears/passes/HOLDs in NEW where OLD FAILed. loosening_inputs = [].")
    else:
        record("stricter-only", "BLOCKER", f"LOOSENING inputs found: {LOOSENING}")

    # ---- NON-VACUITY: a SELLABLE + no-active + complete-6 picture still PASSes (gate can still clear) --------------
    sell_map = recall_risk_contribution(map_risk_flags(resp(decision="SELLABLE")), base_flags={l: False for l in OTHER3})
    sell_pass = "not_sellable" not in sell_map and set(sell_map) == set(RISK_LOCKS) and risk_of(sell_map) is PASS
    sell_approve_clears = not gate_refuses_approve({l: False for l in RISK_LOCKS}, {l: False for l in RISK_LOCKS})
    if sell_pass and sell_approve_clears:
        record("non-vacuity", "DEFENDED",
               "the gate can STILL clear: a SELLABLE + no-active + complete-6 picture via recall_risk_contribution has "
               "no not_sellable key and PASSes _risk; a complete-6 no-active fresh read still clears at approval "
               "(APPROVED). The fix did not turn the gate into a dead refuse-all.")
    else:
        record("non-vacuity", "BLOCKER", f"the SELLABLE clear-path broke (pass={sell_pass}, approve={sell_approve_clears})")

    # ---- N5 residual (in-process only) — the isinstance(str) guard does NOT catch a str-SUBCLASS __eq__ ------------
    class EvilSellable(str):
        def __eq__(self, other):
            return True
        def __hash__(self):
            return 0
    subclass = map_risk_flags(OpsCoreAvailabilityResponse(False, False, False, decision=EvilSellable("NOT_SELLABLE")))
    nonstr = map_risk_flags(OpsCoreAvailabilityResponse(False, False, False, decision=object()))
    subclass_drops = subclass.sellable is True and "not_sellable" not in subclass.risk_flags
    nonstr_kept = nonstr.sellable is False and nonstr.risk_flags.get("not_sellable") is True
    if subclass_drops and nonstr_kept:
        record("N5-residual", "OPEN_NONGATE",
               "the M6.2V N5 fix uses isinstance(decision, str) — it CLOSES a non-str hostile object (object()/Mock -> "
               "sellable=False, veto kept) but a str-SUBCLASS with a hostile __eq__ still passes isinstance(str) and "
               "then == 'SELLABLE' dispatches its __eq__ -> sellable=True -> veto DROPPED at the mapper. NOT a "
               "loosening vs M6.2U (M6.2U dropped it too; M6.2V is strictly better for non-str). In-process code-exec "
               "ONLY (the wire yields a plain str; mapper UNWIRED) -> armed-not-fired, NOT a claim refutation. Route "
               "CODER: use `type(decision) is str` for a complete close of the str-subclass edge.")
    else:
        record("N5-residual", "DEFENDED",
               f"str-subclass handled (subclass_drops={subclass_drops}, nonstr_kept={nonstr_kept})")

    # ================================================================================================
    stricter_only_holds = not LOOSENING
    veto_two_deep = (n1_risk is FAIL and refuse_propose and refuse_fresh and not dropped)
    print("\n" + "=" * 100)
    tally = {}
    for _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    print(f"SUMMARY: {tally}")
    print(f"stricter_only_holds = {stricter_only_holds}")
    print(f"veto_two_deep       = {veto_two_deep}")
    print(f"loosening_inputs    = {LOOSENING}")
    print(f"BLOCKERS            = {[o for o in OUTCOMES if o[1] == 'BLOCKER']}")
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF" and config.EXTERNAL_SEND == "OFF"
    print("POSTURE: BLOCKED / OFF / OFF (unchanged)")
    print("=" * 100)


if __name__ == "__main__":
    main()
