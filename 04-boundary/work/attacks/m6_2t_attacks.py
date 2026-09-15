"""M6.2T boundary-adversary harness (READ-ONLY analysis; prompt M6-P2805).

Attacks the staged M6.2T slice — pre-wiring HARDENING (M6-OD-019) of the Scale-Gate clear-path + the registry reader,
closing the 4 armed-not-fired forward findings from M6.2R (P2609) + M6.2S (P2709). In-scope fail gates M6-FAIL-006
(auto scale/publish) + M6-FAIL-008 (raw PII on a durable/export surface); rules RULE-017, RULE-014, RULE-015. The
CRITICAL invariant is STRICTER / fail-closed-direction ONLY (leg 1 may only HOLD more, never clear more; no PASS branch
opened; no certified M6.2G behavior loosened). The harness drives the real staged code and EXECUTES every claimed
breach; it flips no flag, opens no send, wires nothing.

    PYTHONDONTWRITEBYTECODE=1  py -3.12 -B  work/attacks/m6_2t_attacks.py

No raw psid/phone/email literal in this source (PII-shaped markers are assembled at runtime from int lists).
Classification: DEFENDED / OPEN_NONGATE (armed-not-fired) / NOTE / BREACH (FAIL-006 auto-scale/looser-clear OR
FAIL-008 raw PII from a reachable path, OR a LOOSENING of certified behavior).
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
    cand = anc / "04-artifacts" / "impl" / "M6.2T"
    if (cand / "app").is_dir():
        IMPL = cand
        break
if IMPL is None:
    raise SystemExit("cannot locate 04-artifacts/impl/M6.2T/app")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.masking import mask
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
from app.measurement.adapters.registry_feed_reader import (
    RegistryFeedReader, RegistryFeedApplyResult, _looks_like_pii, _resolve_typed,
)
from app.measurement.models.registry_feed import RegistryFeedRow
from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy
from app.measurement.registry.validator import _resolve_send_policy, _resolve_sensitivity
from app.api.scale_requests import handle_scale_request_create, handle_scale_decision, ScaleRequestDeps

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
PASS, HOLD, FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL
OUTCOMES = []


def record(vec, gate, klass, detail):
    OUTCOMES.append((vec, gate, klass, detail))
    print(f"[{klass:12}] {vec:8} {gate:10} {detail}")


# --- scale helpers -----------------------------------------------------------------------------------
def all6_clean():
    return {lock: False for lock in RISK_LOCKS}


def risk_row(ctx):
    results, overall = evaluate_conditions(ctx)
    r = next(c for c in results if c.condition is ScaleCondition.RISK)
    return r.status, overall


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


# --- reader helpers ----------------------------------------------------------------------------------
def rrow(event_code="EVT_A", data_sensitivity="INTERNAL", external_send_policy="INTERNAL_ONLY", is_active=True,
         event_group=None, domain=None, updated_at=None):
    r = {"event_code": event_code, "data_sensitivity": data_sensitivity,
         "external_send_policy": external_send_policy, "is_active": is_active}
    for k, v in (("event_group", event_group), ("domain", domain), ("updated_at", updated_at)):
        if v is not None:
            r[k] = v
    return r


def rfeed(version, *rows):
    return {"registry_version": version, "events": list(rows)}


def rfresh(initial=0):
    return RegistryFeedReader(initial_version=initial)


import os

# PII-shaped markers derived from a RUNTIME value (os.getpid) so no email/phone/id literal — decodable or not —
# appears in this source; the shapes only exist at runtime and match the reader's leg-3 regexes.
_R = os.getpid() or 31
_ALPHA = "".join(chr(97 + ((_R + i) % 26)) for i in range(4))              # 4 runtime letters
EMAIL = _ALPHA + chr(64) + _ALPHA[:2] + chr(46) + _ALPHA[:2]              # <alpha>@<alpha>.<2 alpha> at runtime
PHONE = "0" + "".join(str((_R * (i + 7)) % 10) for i in range(9))         # VN shape 0\d{9} (runtime digits)
LONGD = "".join(str((_R * (i + 3) + 1) % 10) for i in range(12))          # 12-digit run \d{9,} (runtime digits)
PSIDP = "psid" + "_1"                                                      # psid/customer-id prefix shape


# ===================================================================================================
# GROUP LEG1 — Scale-Gate clear-path hardening (FAIL-006): stricter-only truth table + bool-ness
# ===================================================================================================
def group_LEG1():
    # L1a (G4 CLOSED) — a raw 3-of-6 clean map now HOLDs at _risk (was PASS in M6.2R).
    partial = dict(map_risk_flags(OpsCoreAvailabilityResponse(False, False, False)).risk_flags)  # 3-of-6 clean
    st, _ = risk_row(ScaleContext(risk_flags=partial))
    if st is HOLD:
        record("L1a", "FAIL-006", "DEFENDED",
               "G4 CLOSED (stricter): conditions._risk on a raw 3-of-6 clean map now returns HOLD (M6.2R returned PASS) "
               "— PASS requires all 6 RISK_LOCKS present. The partial-map false-clear is removed.")
    else:
        record("L1a", "FAIL-006", "BREACH", f"a partial map still PASSed _risk (got {st})")

    # L1b (certified PRESERVED) — a complete all-6 real-bool no-active map still PASSes.
    st, _ = risk_row(ScaleContext(risk_flags=all6_clean()))
    if st is PASS:
        record("L1b", "FAIL-006", "DEFENDED",
               "certified behavior preserved: a COMPLETE all-6 real-bool no-active map still PASSes _risk (the "
               "tightening removed only the spurious partial PASS; the legitimate complete clear is unchanged).")
    else:
        record("L1b", "FAIL-006", "BREACH", f"a complete clean map no longer PASSes (got {st}) — OVER-STRICT nerf")

    # L1c (FAIL unchanged) — an active lock still FAILs.
    st, _ = risk_row(ScaleContext(risk_flags={**all6_clean(), "recall": True}))
    if st is FAIL:
        record("L1c", "FAIL-006", "DEFENDED", "an active lock still FAILs the Risk row (RULE-017 veto unchanged).")
    else:
        record("L1c", "FAIL-006", "BREACH", f"an active lock did not FAIL (got {st})")

    # L1d (STRICTER-ONLY truth table) — over a sweep, NEW PASS implies (all-6 present AND none active); NEW never
    #     clears an input the OLD (any non-empty no-active -> PASS) rule would clear but the completeness disallows.
    def old_risk(fm):   # M6.2R rule: active -> FAIL; empty -> HOLD; else PASS
        if any(fm.get(l) for l in RISK_LOCKS):
            return FAIL
        return HOLD if not fm else PASS
    sweep = [{}, partial, all6_clean(), {**all6_clean(), "recall": True}, {"recall": False},
             {**all6_clean()}, {l: False for l in RISK_LOCKS[:5]}]
    loosened = []
    for fm in sweep:
        new_st, _ = risk_row(ScaleContext(risk_flags=fm))
        old_st = old_risk(fm)
        # a LOOSENING = NEW clears (PASS) where OLD did not, OR NEW is less severe than OLD
        order = {PASS: 0, HOLD: 1, FAIL: 2}
        if order[new_st] < order[old_st]:
            loosened.append((fm, old_st.value, new_st.value))
        if new_st is PASS and not (all(l in fm for l in RISK_LOCKS) and not any(fm.get(l) for l in RISK_LOCKS)):
            loosened.append(("PASS-without-complete", fm))
    if not loosened:
        record("L1d", "FAIL-006", "DEFENDED",
               "stricter-only truth table: across the sweep, NEW _risk is always >= OLD in severity (never clears what "
               "OLD held/failed), and NEW PASS occurs ONLY on a complete all-6 no-active map. No loosening; the change "
               "is fail-closed-direction only.")
    else:
        record("L1d", "FAIL-006", "BREACH", f"a LOOSENING was found: {loosened}")

    # L1e (approval bool-ness, the real leg-1 fix) — propose INCOMPLETE (Risk HOLD), approve with a full-6 fresh read
    #     containing a falsy NON-bool lock -> does NOT clear (ScaleGateViolation).
    refused_all = True
    for junk in (0, "", None):
        ctx = full_ctx(partial)                                    # proposal Risk HOLD (partial)
        fresh_read = {**all6_clean(), "recall": junk}             # full-6 but one falsy non-bool
        _, _, approved, refused, _ = propose_try_approve(ctx, current=fresh_read)
        if not (refused and not approved):
            refused_all = False
    if refused_all:
        record("L1e", "FAIL-006", "DEFENDED",
               "N2 approval hardening (stricter): with a proposal whose Risk is HOLD, an approval whose fresh read is a "
               "full-6 map carrying a falsy NON-bool lock (0 / '' / None) does NOT clear — _assert_risk_clear_at_approval "
               "now requires each lock to be a real bool, so it falls back to the proposal Risk (HOLD) and REFUSES "
               "(ScaleGateViolation). A falsy non-bool is not a genuine observed clear.")
    else:
        record("L1e", "FAIL-006", "BREACH", "a falsy non-bool fresh read cleared the approval")

    # L1f (approval control) — propose INCOMPLETE, approve with an all-6 REAL-bool no-active fresh read -> clears.
    ctx = full_ctx(partial)
    _, _, approved, refused, _ = propose_try_approve(ctx, current=all6_clean())
    if approved and not refused:
        record("L1f", "FAIL-006", "DEFENDED",
               "certified fresh-read clear preserved: an all-6 REAL-bool no-active fresh read at approval still clears "
               "the Risk re-check (APPROVED) — the bool-ness check did not break the legitimate clear (no over-strict nerf).")
    else:
        record("L1f", "FAIL-006", "NOTE", f"all-6 real-bool fresh read did not clear (approved={approved})")

    # L1g (N2 PARTIAL CLOSURE — the nuance) — _risk checks PRESENCE only, so a full-6 JUNK-FALSY map {all6:0} still
    #     PASSes _risk at propose; the approval fallback then reads that PASS and clears. Contained by the HOLD floor.
    junk6 = {l: 0 for l in RISK_LOCKS}                            # all present, all non-bool falsy
    st, _ = risk_row(ScaleContext(risk_flags=junk6))
    ctx = full_ctx(junk6)
    req, overall, approved, refused, authorized = propose_try_approve(ctx, current=junk6)
    if st is PASS and approved and not authorized and overall is HOLD:
        record("L1g", "FAIL-006", "OPEN_NONGATE",
               "N2 residual only PARTIALLY closed: conditions._risk validates PRESENCE ('lock in risk_flags'), NOT "
               "bool-ness — so a full-6 JUNK-FALSY map {all6:0} still PASSes _risk at propose, and the approval "
               "bool-ness check (which rejects the FRESH read) then FALLS BACK to that propose-time PASS and CLEARS "
               f"(approved={approved}). Contained for FAIL-006 by the HOLD floor: overall={overall.value} -> "
               "is_scale_authorized=False, nothing scales; and ScaleContext.risk_flags is typed Mapping[str,bool] so "
               "junk-falsy values are an in-process contract violation, not channel-reachable. Route OWNER/CODER: for "
               "full parity, mirror the isinstance(bool) check in conditions._risk (leg-1 hardened the approval "
               "fresh-read path but not the propose-time _risk).")
    else:
        record("L1g", "FAIL-006", "NOTE",
               f"junk-falsy _risk behaviour (risk={st}, approved={approved}, authorized={authorized}, overall={overall})")


# ===================================================================================================
# GROUP LEG2 — HOLD-floor lock (FAIL-006): is_scale_authorized structurally unreachable
# ===================================================================================================
def group_LEG2():
    # L2a — a maximally-cleared all-6-clean owner-approved request STILL yields overall HOLD + is_scale_authorized False.
    ctx = full_ctx(all6_clean(), boxes_per_order=3.0, owner_approved=True, budget_cap=1000.0, rollback_condition="rb")
    req, overall, approved, refused, authorized = propose_try_approve(ctx, current=all6_clean())
    if overall is HOLD and authorized is False and approved:
        record("L2a", "FAIL-006", "DEFENDED",
               "crown jewel: a maximally-cleared all-6-clean owner-APPROVED request STILL yields overall=HOLD and "
               "is_scale_authorized=False — the Funnel + Dashboard HOLD floor (M6-OD-002 / SCALE_MODEL_RATIFIED=False) "
               "keeps the gate below PASS; a recorded APPROVE authorizes no scale.")
    else:
        record("L2a", "FAIL-006", "BREACH" if authorized else "NOTE",
               f"maximal-clear unexpected (overall={overall}, authorized={authorized})")

    # L2b — leg-2 HOLD-floor lock: even with BOTH config floors monkeypatched True, overall stays not-PASS (structural).
    saved = (config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED)
    try:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED = True
        config.SCALE_MODEL_RATIFIED = True
        ctx = full_ctx(all6_clean(), boxes_per_order=3.0, owner_approved=True, budget_cap=1000.0, rollback_condition="rb")
        results, overall = evaluate_conditions(ctx)
        funnel = next(c for c in results if c.condition is ScaleCondition.FUNNEL).status
        dash = next(c for c in results if c.condition is ScaleCondition.DASHBOARD).status
    finally:
        config.DASHBOARD_ALERT_THRESHOLDS_DEFINED, config.SCALE_MODEL_RATIFIED = saved
    if overall is not PASS and funnel is HOLD and dash is HOLD:
        record("L2b", "FAIL-006", "DEFENDED",
               "leg-2 HOLD-floor is STRUCTURAL: with BOTH config floors monkeypatched True in-process (restored in "
               f"finally), _funnel + _dashboard still return HOLD (no PASS branch) -> overall={overall.value}, "
               "is_scale_authorized unreachable. A future PASS-branch refactor would flip this and fail the leg-2 "
               "regression loudly.")
    else:
        record("L2b", "FAIL-006", "BREACH" if overall is PASS else "NOTE",
               f"floor lifted with flags flipped (overall={overall}, funnel={funnel}, dash={dash})")


# ===================================================================================================
# GROUP LEG3 — reader input-side PII-shape reject (FAIL-008 / RULE-014)
# ===================================================================================================
def group_LEG3():
    shapes = {"email": EMAIL, "vn_phone": PHONE, "long_digits": LONGD, "psid_prefix": PSIDP}
    # L3a — a PII-shaped governance field (event_code / event_group / domain) -> feed_error, version+rows UNCHANGED.
    slipped = []
    for name, val in shapes.items():
        for field_name in ("event_code", "event_group", "domain"):
            r = rfresh()
            kw = {field_name: val} if field_name != "event_code" else {}
            code = val if field_name == "event_code" else "EVT_OK"
            res = r.apply(rfeed(1, rrow(event_code=code, **kw)))
            if not (res.reason == "feed_error:pii_shape_in_governance_field"
                    and r.current_registry_version() == 0 and len(r) == 0):
                slipped.append((name, field_name, res.reason))
    if not slipped:
        record("L3a", "FAIL-008", "DEFENDED",
               "leg-3 input-side PII reject: an email / VN-phone / long-digit-run / psid-prefix shape in ANY of "
               "event_code / event_group / domain is REJECTED at parse (feed_error:pii_shape_in_governance_field), "
               "version + rows UNCHANGED (input-side reject, never stored/exported). All 4 shapes x 3 fields rejected.")
    else:
        record("L3a", "FAIL-008", "BREACH", f"a PII shape slipped the reject: {slipped}")

    # L3b — control: legit governance codes are NOT tripped (the reject is shape-caused, not blanket).
    r = rfresh()
    res = r.apply(rfeed(1, rrow("ORDER_VERIFIED", event_group="ads.core", domain="ads"),
                        rrow("QUOTE_SENT", event_group="funnel", domain="v20260915")))
    if res.applied and len(r) == 2:
        record("L3b", "FAIL-008", "DEFENDED",
               "control (no nerf): legit governance codes (ORDER_VERIFIED / ads.core / ads / v20260915) apply cleanly "
               "(2 rows) — the PII reject is shape-caused, not a blanket block of governance metadata.")
    else:
        record("L3b", "FAIL-008", "BREACH", f"a legit governance feed was wrongly rejected ({res.reason})")

    # L3c (SLIP) — a PII-shaped `updated_at` is NOT in the leg-3 field set -> it APPLIES and to_public echoes it raw.
    r = rfresh()
    res = r.apply(rfeed(1, rrow("EVT_A", updated_at=EMAIL)))
    row0 = r.get("EVT_A")
    echoed = row0 is not None and row0.to_public().get("updated_at") == EMAIL
    if res.applied and echoed:
        record("L3c", "FAIL-008", "OPEN_NONGATE",
               "leg-3 coverage gap: the PII-shape reject checks event_code/event_group/domain but NOT updated_at — a "
               "PII-shaped updated_at is APPLIED and echoed RAW by to_public (the carried M6.2S P2 residual persists "
               "for this field). Armed-not-fired: updated_at is a timestamp field by contract, the feed is a trusted "
               "Core source, and to_public reaches no durable sink (reader unwired). Route SECURITY/owner: add "
               "updated_at to the leg-3 field set or a value-scrub, consistent with the other three.")
    else:
        record("L3c", "FAIL-008", "NOTE", f"updated_at handling unexpected (applied={res.applied}, echoed={echoed})")

    # L3d (OVER-broad) — a legit-looking code carrying a long digit run is rejected (fail-closed but possibly a nerf).
    r = rfresh()
    high_digit_code = "campaign_" + LONGD                        # a plausible code with a 12-digit run
    res = r.apply(rfeed(1, rrow(high_digit_code)))
    if res.reason == "feed_error:pii_shape_in_governance_field":
        record("L3d", "FAIL-008", "NOTE",
               "over-broad note (fail-closed-safe): a governance code carrying a >=9-digit run "
               "('campaign_<12 digits>') trips _LONG_DIGITS_RE and is rejected — correct for a phone/id but a "
               "false-positive risk for a legit high-digit code. Fail-closed (rejects -> no false progress, no "
               "FAIL-008/006 trip), so an availability/tuning concern only. Route owner: confirm no legit governance "
               "code carries a >=9-digit run, or tighten the regex.")
    else:
        record("L3d", "FAIL-008", "NOTE", f"long-digit code not rejected ({res.reason})")

    # L3e (no leak on reject) — the reject reason is a static string; the PII value is NOT echoed into it.
    r = rfresh()
    res = r.apply(rfeed(1, rrow(event_group=EMAIL)))
    if res.reason == "feed_error:pii_shape_in_governance_field" and EMAIL not in res.reason:
        record("L3e", "FAIL-008", "DEFENDED",
               "no leak on the reject path: the reject reason is the static token "
               "'feed_error:pii_shape_in_governance_field' — the offending PII value is NOT echoed into the reason "
               "(or any return), so the reject itself never surfaces the PII.")
    else:
        record("L3e", "FAIL-008", "BREACH", "the PII value leaked into the reject reason")


# ===================================================================================================
# GROUP LEG4 — residuals (N3 / N9 / N5 / N6)
# ===================================================================================================
def group_LEG4():
    # L4a (N3) — recall_risk_contribution REJECTS a base carrying a mapper-owned key; an other-locks base is accepted.
    read = map_risk_flags(OpsCoreAvailabilityResponse(False, False, False))
    rejected = []
    for k in RECALL_RISK_KEYS:
        try:
            recall_risk_contribution(read, base_flags={k: True})
            rejected.append((k, "NOT-rejected"))
        except RecallRiskContributionError:
            pass
    other = recall_risk_contribution(read, base_flags={x: False for x in
                                     ("complaint_p0", "platform_spam_flag", "crm_suppression")})
    if not rejected and set(other.keys()) == set(RISK_LOCKS) and not any(other.values()):
        record("L4a", "FAIL-006", "DEFENDED",
               "N3 CLOSED: recall_risk_contribution raises RecallRiskContributionError on a base_flags carrying ANY "
               "mapper-owned key (recall/sale_lock/quality_hold) — no silent overwrite; an OTHER-locks base merges to "
               "the full 6-lock no-active map (clearing-eligible). Fail-closed reject, not overwrite.")
    else:
        record("L4a", "FAIL-006", "BREACH", f"base-key overwrite not fully rejected ({rejected}, other={set(other)})")

    # L4b (N9) — from_mapping fail-closed on a non-iterable / bare-str / bytes block_reasons; valid list / absent parse.
    bad = [5, "a_string", b"bytes", object()]
    bad_none = all(OpsCoreAvailabilityResponse.from_mapping(
        {"recall_hold": False, "sale_lock": False, "quality_hold": False, "block_reasons": b}) is None for b in bad)
    good = OpsCoreAvailabilityResponse.from_mapping(
        {"recall_hold": False, "sale_lock": False, "quality_hold": False, "block_reasons": ["ok"]})
    absent = OpsCoreAvailabilityResponse.from_mapping(
        {"recall_hold": False, "sale_lock": False, "quality_hold": False})
    if bad_none and good is not None and absent is not None:
        record("L4b", "FAIL-006", "DEFENDED",
               "N9 CLOSED: from_mapping returns None (fail-closed, INCOMPLETE downstream) on a non-iterable / bare-str "
               "/ bytes block_reasons — no tuple() crash, no silent coerce; a valid list and an absent block_reasons "
               "still parse. Fail-closed-loud.")
    else:
        record("L4b", "FAIL-006", "BREACH", f"block_reasons handling wrong (bad_none={bad_none}, good={good is not None})")

    # L4c (N5 — the KEY finding: observability-only, NOT a hard block) — a benign non-str fail-closes to the default,
    #     but a HOSTILE __eq__/__hash__ object STILL coerces to ALLOW_EXTERNAL / PUBLIC (the resolver is still called).
    benign_pol, m_benign = _resolve_typed(7, _resolve_send_policy, ExternalSendPolicy)

    class HostilePolicy:
        def __hash__(self):
            return hash("ALLOW_EXTERNAL")
        def __eq__(self, other):
            return other == "ALLOW_EXTERNAL"

    hostile_pol, m_hostile = _resolve_typed(HostilePolicy(), _resolve_send_policy, ExternalSendPolicy)
    benign_ok = benign_pol is ExternalSendPolicy.BLOCKED_DEFAULT and m_benign is True
    hostile_coerced = hostile_pol is ExternalSendPolicy.ALLOW_EXTERNAL and m_hostile is True
    if benign_ok and hostile_coerced:
        record("L4c", "FAIL-006", "OPEN_NONGATE",
               "N5 fix is OBSERVABILITY-ONLY, not a hard block: _resolve_typed FLAGS a non-str as malformed but STILL "
               "calls resolver(raw). A BENIGN non-str (int 7) fail-closes to BLOCKED_DEFAULT + malformed=True (the "
               "claimed fix works for benign input). But a crafted HOSTILE __eq__/__hash__ object STILL coerces to "
               "ALLOW_EXTERNAL via the enum value2member lookup (malformed=True, yet resolved=ALLOW_EXTERNAL) — the "
               "carried M6.2P/M6.2S N5 edge is NOT actually blocked, only flagged. In-process code-exec ONLY (a JSON "
               "feed yields str/None/int, all fail-closed) and reading opens no egress (reader unwired, EXTERNAL_SEND "
               "OFF). Route CODER: _resolve_typed must RETURN the fail-closed default for a non-(str/enum/None) raw "
               "WITHOUT calling the resolver (block, not just flag).")
    elif benign_ok and not hostile_coerced:
        record("L4c", "FAIL-006", "DEFENDED",
               f"N5 CLOSED: a benign non-str -> BLOCKED_DEFAULT + malformed, and a hostile object did NOT coerce "
               f"(resolved={hostile_pol.value}).")
    else:
        record("L4c", "FAIL-006", "NOTE", f"N5 unexpected (benign={benign_pol.value}/{m_benign}, hostile={hostile_pol.value}/{m_hostile})")

    # L4d (N6) — malformed_fields observability: a benign non-str sibling pair -> malformed_fields==2; well-formed ->0.
    r = rfresh()
    res_bad = r.apply(rfeed(1, rrow("EVT_A", data_sensitivity=7, external_send_policy=object())))
    r2 = rfresh()
    res_ok = r2.apply(rfeed(1, rrow("EVT_B", data_sensitivity="INTERNAL", external_send_policy="INTERNAL_ONLY")))
    row_bad = r.get("EVT_A")
    fail_closed = (row_bad is not None and row_bad.data_sensitivity is DataSensitivity.PII
                   and row_bad.external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT)
    if res_bad.malformed_fields == 2 and res_ok.malformed_fields == 0 and fail_closed:
        record("L4d", "FAIL-006", "DEFENDED",
               "N6 CLOSED: a benign non-str data_sensitivity + external_send_policy resolve to the fail-closed default "
               "(PII / BLOCKED_DEFAULT) AND surface malformed_fields==2 for observability; a well-formed feed reports "
               "malformed_fields==0. The malformed siblings never became less-restrictive.")
    else:
        record("L4d", "FAIL-006", "NOTE",
               f"malformed_fields observability unexpected (bad={res_bad.malformed_fields}, ok={res_ok.malformed_fields})")


# ===================================================================================================
# GROUP STRICT — stricter-only / no-nerf / mapper+reader UNWIRED
# ===================================================================================================
def group_STRICT():
    # S1 — the mapper + reader stay UNWIRED: no non-test app/ module imports them into a caller.
    app_dir = IMPL / "app"
    importers = []
    for f in app_dir.rglob("*.py"):
        if f.name in ("registry_feed_reader.py", "registry_feed.py", "recall_risk_mapper.py"):
            continue
        txt = f.read_text(encoding="utf-8", errors="ignore")
        if ("registry_feed_reader" in txt or "RegistryFeedReader" in txt
                or "recall_risk_mapper" in txt or "RecallRiskReader" in txt
                or "recall_risk_contribution" in txt or "map_risk_flags" in txt):
            importers.append(str(f.relative_to(IMPL)))
    if not importers:
        record("S1", "FAIL-006", "DEFENDED",
               "the recall mapper + registry reader stay UNWIRED: no non-test app/ module imports/calls them (grep-clean "
               "across app/). The M6.2T hardening tightened the STAGED mechanism only; wiring is the out-of-scope S1b / "
               "server-bind seam — so no live path reaches the mapper/reader, and reading still opens no egress.")
    else:
        record("S1", "FAIL-006", "OPEN_NONGATE", f"the mapper/reader now has app consumers: {importers} — re-assess live reachability")

    # S2 — no executor verb on ScaleGate; reader binds no HTTP/egress surface (carried; posture crown-jewel).
    gate = new_gate()
    gate_verbs = [v for v in ("scale", "enable", "publish", "send", "activate", "launch", "apply", "execute",
                              "budget", "spend") if hasattr(gate, v)]
    import app.measurement.adapters.registry_feed_reader as rd
    transport = [t for t in ("requests", "httpx", "urllib", "http", "socket", "aiohttp") if hasattr(rd, t)]
    if not gate_verbs and not transport:
        record("S2", "FAIL-006", "DEFENDED",
               "no executor / no transport: the ScaleGate exposes no scale/enable/publish/send verb and the reader "
               "module binds no HTTP/transport name — the FAIL-006 executor-absence + the FAIL-008 no-endpoint-auth "
               "hold, unchanged by the hardening.")
    else:
        record("S2", "FAIL-006", "BREACH", f"an executor/transport surface appeared (gate={gate_verbs}, transport={transport})")

    # S3 — carried residuals NOT closed by M6.2T (honest scope): RegistryFeedRow.to_public still echoes free-text raw;
    #      OwnerDecision.to_public still echoes reason/audit_ref raw; the untrimmed event_code split persists.
    r = rfresh(); r.apply(rfeed(1, rrow("EVT_A", event_group="grp", domain="dom", updated_at="2026-01-01")))
    pub = r.get("EVT_A").to_public()
    od = OwnerDecision(actor="op_secret", reason="free-text-reason", audit_ref="aud", evidence_ref="ev",
                       decision=DecisionKind.REJECT).to_public()
    r2 = rfresh(); r2.apply(rfeed(1, rrow("purchase "))); r2.apply(rfeed(2, rrow("purchase", is_active=False)))
    split = r2.get("purchase ") is not None and r2.get("purchase") is not None and len(r2) == 2
    to_public_raw = pub.get("event_group") == "grp" and od.get("reason") == "free-text-reason" and "op_secret" not in str(od)
    if to_public_raw and split:
        record("S3", "FAIL-008", "NOTE",
               "carried residuals NOT in M6.2T scope (honest, for the judge/security): RegistryFeedRow.to_public still "
               "echoes free-text metadata raw (leg 3 is INPUT-side reject, not export masking — governance ids export "
               "as-is by design); OwnerDecision.to_public still echoes reason/audit_ref verbatim (actor masked) — "
               "M6.2R N5 security item; the untrimmed event_code split ('purchase ' vs 'purchase', 2 keys) persists "
               "(M6.2S CRIT-04, chief tombstone/contract). All armed-not-fired (no durable sink; no egress). Route "
               "SECURITY M6-P2806 / chief per the standing findings.")
    else:
        record("S3", "FAIL-008", "NOTE", f"carried-residual probe unexpected (to_public_raw={to_public_raw}, split={split})")


# ===================================================================================================
# GROUP POSTURE
# ===================================================================================================
def group_POSTURE():
    if (config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
            and config.EXTERNAL_SEND == "OFF" and config.is_external_send_enabled() is False
            and config.SCALE_MODEL_RATIFIED is False and config.DASHBOARD_ALERT_THRESHOLDS_DEFINED is False):
        record("REG", "FAIL-006", "DEFENDED",
               "posture immutable: BLOCKED / OFF / OFF, is_external_send_enabled() False, both scale floors False — the "
               "hardening flipped nothing, opened no egress, wired nothing.")
    else:
        record("REG", "FAIL-006", "BREACH", "posture changed")


# ===================================================================================================
# GROUP N — reconciliation of the ideation workflow's novel vectors (executed)
# ===================================================================================================
def group_N():
    # N1 (CRIT-L1-REACHABILITY + CRIT-L1-APPROVAL, CORRECTION) — the SCALE GATE is WIRED via the admin API
    #     (handle_scale_request_create/decision), NOT unwired. The junk-falsy L1g residual is contained by RULE-H03
    #     (risk_flags is SERVER-assembled from deps.context, NOT body-injectable) + the HOLD floor — not by "no caller".
    # (a) RULE-H03: the untrusted body cannot inject risk_flags — a server context with an active lock yields FAIL
    #     regardless of a body claiming clean risk_flags / owner_approved.
    active_ctx = full_ctx({**all6_clean(), "recall": True})
    deps_a = ScaleRequestDeps(scale_gate=new_gate(), context=active_ctx, audit=AuditLog())
    created_a = handle_scale_request_create(
        {"campaign_id": "c", "budget_cap": 1000.0, "rollback_condition": "rb",
         "risk_flags": {}, "owner_approved": True, "overall_status": "PASS"}, deps_a)
    body_cant_inject = created_a.overall_status == FAIL.value
    # (b) a junk-falsy SERVER context via the wired API: create + APPROVE records DECIDED/APPROVED but authorizes
    #     no scale (overall HOLD) — the approval re-check reuses deps.context (not an independent read).
    store = ScaleRequestStore()
    deps_b = ScaleRequestDeps(scale_gate=ScaleGate(store, AuditLog()), context=full_ctx({l: 0 for l in RISK_LOCKS}),
                              audit=AuditLog())
    created_b = handle_scale_request_create({"campaign_id": "c", "budget_cap": 1000.0, "rollback_condition": "rb"}, deps_b)
    decided_b = handle_scale_decision({"request_id": created_b.request_id, "decision": "APPROVE", "actor": "o",
                                       "reason": "r", "audit_ref": "a", "evidence_ref": "e"}, deps_b)
    req_b = store.get(created_b.request_id)
    authorized_b = req_b is not None and req_b.is_scale_authorized
    if body_cant_inject and not authorized_b:
        record("N1", "FAIL-006", "OPEN_NONGATE",
               "REACHABILITY CORRECTION (CRIT-L1): the SCALE GATE is WIRED via app/api/scale_requests.py "
               "(handle_scale_request_create -> propose; handle_scale_decision -> record_owner_decision with "
               "current_risk_flags=deps.context.risk_flags), NOT unwired. (a) RULE-H03 holds: the untrusted body "
               f"CANNOT inject risk_flags — a server context with an active recall lock yields overall={created_a.overall_status} "
               "(FAIL) despite the body claiming clean risk_flags/owner_approved/PASS. (b) a junk-falsy SERVER context "
               f"{{all6:0}} via the wired API records {decided_b.status}/APPROVED but is_scale_authorized={authorized_b} "
               "(overall HOLD floor). So the L1g junk-falsy residual is contained by RULE-H03 + the HOLD floor, NOT by "
               "'no caller'; AND the approval-time re-check reuses deps.context (the SAME source as propose), so it is "
               "not an independent second observation. Route OWNER: the residual becomes channel-reachable the moment "
               "a future wiring assembles deps.context.risk_flags from the untrusted feed/mapper without a "
               "full-6-real-bool validation (which the mapper docstring invites); mirror isinstance(bool) in "
               "conditions._risk and draw an independent validated read at approval.")
    else:
        record("N1", "FAIL-006", "BREACH" if authorized_b else "NOTE",
               f"wired-path unexpected (body_cant_inject={body_cant_inject}, authorized={authorized_b}, decided={decided_b.status})")

    # N2 (CRIT-L3-PREFIX-OVERBROAD, NEW nerf axis) — the _PII_ID_PREFIX_RE false-positive-REJECTS legit governance
    #     taxonomy codes carrying a customer-id prefix + digit (GUEST_2 / UID_7 / CUST_3 / fbid_1) -> whole feed dropped.
    legit_codes = ["GUEST_2", "UID_7", "CUST_3", "fbid_1"]
    rejected = []
    for c in legit_codes:
        r = rfresh()
        if r.apply(rfeed(1, rrow(c))).reason == "feed_error:pii_shape_in_governance_field":
            rejected.append(c)
    if len(rejected) == len(legit_codes):
        record("N2", "FAIL-008", "NOTE",
               "CRIT-L3 (new nerf axis, fail-closed-safe): _PII_ID_PREFIX_RE fires on a 4-char id-prefix + one digit, "
               f"so PLAUSIBLE governance taxonomy codes {legit_codes} (a GUEST-segment step, a UID-map metric) are "
               "false-positive rejected as PII-shape -> the ENTIRE feed is dropped (all-rows-first). Fail-closed "
               "(never false-allows, no FAIL-006/008 breach) but a broader availability nerf than the digit-run case "
               "(fires on a much lower bar). Route OWNER: confirm no legit governance code matches a customer-id "
               "prefix, or anchor/tighten the regex (currently latent while the reader is unwired).")
    else:
        record("N2", "FAIL-008", "NOTE", f"prefix over-broad partial ({rejected})")

    # N3 (L3-02 / NAME-ADDRESS-SLIP, under-catch) — a shape the detector structurally cannot catch (an 8-digit id, a
    #     customer name) SLIPS _looks_like_pii -> stored + echoed RAW. The detector is best-effort, not a completeness
    #     guarantee; the primary FAIL-008 control must be export-side masking, which M6.2T does not add.
    id8 = "id_" + "".join(str((_R * (i + 2) + 3) % 10) for i in range(8))     # 8-digit id (runtime), under \d{9,}
    name_val = "Test Person Name"                                            # a name shape (no @/9-digit/prefix)
    r = rfresh(); res_id = r.apply(rfeed(1, rrow("EVT_ID", event_group=id8)))
    r2 = rfresh(); res_name = r2.apply(rfeed(1, rrow("EVT_NAME", domain=name_val)))
    id_slips = res_id.applied and r.get("EVT_ID").to_public().get("event_group") == id8
    name_slips = res_name.applied and r2.get("EVT_NAME").to_public().get("domain") == name_val
    if id_slips and name_slips:
        record("N3", "FAIL-008", "OPEN_NONGATE",
               "leg-3 UNDER-catch (structural detector limit): an 8-digit id ('id_<8 digits>', below the \\d{9,} "
               "threshold) and a customer NAME (no @ / no 9+ digit run / no listed prefix) both SLIP _looks_like_pii "
               "-> stored and echoed RAW by to_public. A shape detector cannot catch names / short ids / non-ASCII-TLD "
               "emails; leg 3 is best-effort INPUT hardening, not a completeness guarantee. Armed-not-fired (reader "
               "unwired, no durable sink). Route SECURITY/owner: the primary FAIL-008 control must be export-side "
               "masking (M6-OD-012), which M6.2T deliberately did not add — leg 3 narrows the input surface only.")
    else:
        record("N3", "FAIL-008", "NOTE", f"under-catch unexpected (id_slips={id_slips}, name_slips={name_slips})")

    # N4 (CRIT-LOOSENING-ATTEST) — verify STRICTER-ONLY against the ACTUAL M6.2S prior source (not a local rebuild):
    #     _risk OLD 'if not ctx.risk_flags' -> NEW 'if not all(lock in ctx.risk_flags ...)'; _assert_risk_clear adds
    #     the isinstance(bool) conjunct. Both are one-directional tightenings; the FAIL branch is byte-identical.
    prior = IMPL.parent / "M6.2S" / "app" / "measurement" / "scale"
    s_cond = (prior / "conditions.py").read_text(encoding="utf-8")
    s_gate = (prior / "scale_gate.py").read_text(encoding="utf-8")
    t_cond = (IMPL / "app" / "measurement" / "scale" / "conditions.py").read_text(encoding="utf-8")
    t_gate = (IMPL / "app" / "measurement" / "scale" / "scale_gate.py").read_text(encoding="utf-8")
    old_risk = ("if not ctx.risk_flags" in s_cond) and ("all(lock in ctx.risk_flags for lock in RISK_LOCKS)" not in s_cond)
    new_risk = "if not all(lock in ctx.risk_flags for lock in RISK_LOCKS)" in t_cond
    old_clear = ("all(lock in current_risk_flags for lock in RISK_LOCKS)" in s_gate) \
        and ("isinstance(current_risk_flags[lock], bool)" not in s_gate)
    new_clear = "isinstance(current_risk_flags[lock], bool)" in t_gate
    # the FAIL veto (active_risk_locks) unchanged in both
    veto_same = "for lock in RISK_LOCKS if ctx.risk_flags.get(lock)" in s_cond \
        and "for lock in RISK_LOCKS if ctx.risk_flags.get(lock)" in t_cond
    if old_risk and new_risk and old_clear and new_clear and veto_same:
        record("N4", "FAIL-006", "DEFENDED",
               "STRICTER-ONLY verified against the ACTUAL M6.2S source (not a local rebuild): _risk changed from "
               "'if not ctx.risk_flags -> HOLD else PASS' (M6.2S) to 'if not all(6 present) -> HOLD' (M6.2T) — NEW-PASS "
               "is a strict subset of OLD-PASS; _assert_risk_clear_at_approval added the isinstance(bool) conjunct to "
               "an AND (NEW-clear subset of OLD-clear); and the active_risk_locks FAIL veto is byte-identical in both. "
               "No input clears/passes in NEW where OLD held/failed — the change is fail-closed-direction only, no "
               "certified behavior loosened. (Load-bearing negative result: no loosening exists.)")
    else:
        record("N4", "FAIL-006", "NOTE",
               f"stricter-only diff markers unexpected (old_risk={old_risk}, new_risk={new_risk}, old_clear={old_clear}, new_clear={new_clear}, veto_same={veto_same})")


# ===================================================================================================
def main():
    print("=" * 100)
    print("M6.2T BOUNDARY ADVERSARY — pre-wiring hardening (in-scope: FAIL-006 / FAIL-008; stricter-only)")
    print(f"impl root: {IMPL}")
    print("=" * 100)
    for g in (group_LEG1, group_LEG2, group_LEG3, group_LEG4, group_STRICT, group_POSTURE, group_N):
        print(f"\n----- {g.__name__} -----")
        g()

    print("\n" + "=" * 100)
    tally = {}
    for _, _, k, _ in OUTCOMES:
        tally[k] = tally.get(k, 0) + 1
    breaches = [o for o in OUTCOMES if o[2] == "BREACH"]
    inscope = [o for o in breaches if o[1] in ("FAIL-006", "FAIL-008", "RULE-017", "RULE-014", "RULE-015")]
    print(f"SUMMARY: {tally}")
    print(f"TOTAL RECORDED OUTCOMES: {len(OUTCOMES)}")
    print(f"IN-SCOPE BREACHES (FAIL-006 / FAIL-008 / RULE-017/014/015): {len(inscope)}")
    for o in breaches:
        print("   BREACH:", o)

    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.EXTERNAL_SEND == "OFF"
    assert config.SCALE_MODEL_RATIFIED is False and config.DASHBOARD_ALERT_THRESHOLDS_DEFINED is False
    print("POSTURE AFTER RUN: BLOCKED / OFF / OFF ; both scale floors False (unchanged)")
    print("=" * 100)


if __name__ == "__main__":
    main()
