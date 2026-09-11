"""M6-CTR-013 scale-condition evaluation — the 8 doc §16 Scale-Gate conditions (verbatim rows, extract 317–324).

`evaluate_conditions(ctx)` returns 8 `ConditionResult`s (each PASS/HOLD/FAIL) + a worst-status overall. The
**Risk** row is a HARD VETO (RULE-017): any active recall / sale-lock / quality-hold / complaint-P0 /
platform-spam-flag / CRM-suppression ⇒ Risk = FAIL ⇒ the whole gate is FAIL. Fail-closed everywhere: a missing
boundary signal is HOLD (never PASS); the **Funnel** condition is fail-closed HOLD while CPA/verified-rate
thresholds are M6-OD-002 (OPEN); the **Dashboard**-as-scale-evidence condition is fail-closed HOLD while
`SCALE_MODEL_RATIFIED=False` (M6-OD-005). The **Approval** condition is HOLD until an explicit owner approval
exists (SMK-012). So in the staged posture the overall gate can reach HOLD at best — never a clean scale-ready
PASS — which is the honest truth while M6-OD-002/005 are OPEN. This module COMPUTES only; it never acts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional, Tuple

from app import config
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.quality.data_quality_check import worst_status

# Reuse the locked PASS/HOLD/FAIL vocabulary (same as the DQ gate / data_quality_status).
ConditionStatus = DataQualityStatus
_PASS, _HOLD, _FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL

# The 6 Risk-row locks (doc §16 L323 + §15 L307 CRM suppression). ANY active ⇒ hard veto (RULE-017).
RISK_LOCKS: Tuple[str, ...] = (
    "recall", "sale_lock", "quality_hold", "complaint_p0", "platform_spam_flag", "crm_suppression",
)

# The four entry-evidence rows the P3/P5/P6 condition requires to be present (doc §16 row 1).
REQUIRED_ENTRY_EVIDENCE: Tuple[str, ...] = ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004")


class ScaleCondition(str, Enum):
    """The 8 doc §16 Scale-Gate conditions (verbatim order, extract 317–324)."""

    P3_P5_P6_EVIDENCE = "P3/P5/P6 evidence"
    QUOTE_ORDER = "Quote/Order"
    PUBLIC_PRIVACY = "Public/Privacy"
    FUNNEL = "Funnel"
    DASHBOARD = "Dashboard"
    QUALITY = "Quality"
    RISK = "Risk"
    APPROVAL = "Approval"


@dataclass(frozen=True)
class ConditionResult:
    condition: ScaleCondition
    status: ConditionStatus
    detail: str                                 # machine reason (no raw PII)
    evidence_ref: Optional[str] = None          # masked ref, if any


@dataclass
class ScaleContext:
    """The inputs the scale conditions read. All CONSUMED / read-only — M6 records whether a boundary passed, it
    never validates or owns it (RULE-018/021). Fail-closed: None = unknown ⇒ HOLD (never PASS)."""

    entry_evidence_refs: Mapping[str, str] = field(default_factory=dict)   # ENTRY-00x -> masked ref
    quote_order_ok: Optional[bool] = None          # M3/M8 boundary attestation (consumed)
    public_privacy_ok: Optional[bool] = None       # M4/M5 boundary attestation (consumed)
    boxes_per_order: Optional[float] = None        # from the M6.2F Boxes/Order metric (AOV>=2 structural sub-check)
    dq_overall: Optional[DataQualityStatus] = None # the M6.2F Data Quality Gate overall
    risk_flags: Mapping[str, bool] = field(default_factory=dict)   # recall/sale_lock/... -> active?
    owner_approved: bool = False                   # set only by an explicit OwnerDecision (never self-set)
    budget_cap: Optional[float] = None             # request field (a requirement), never an action
    rollback_condition: Optional[str] = None       # request field (a requirement), never an action


def active_risk_locks(ctx: ScaleContext) -> Tuple[str, ...]:
    """The subset of RISK_LOCKS currently active (truthy) in the context."""
    return tuple(lock for lock in RISK_LOCKS if ctx.risk_flags.get(lock))


def _p3_p5_p6(ctx: ScaleContext) -> ConditionResult:
    missing = [e for e in REQUIRED_ENTRY_EVIDENCE if not ctx.entry_evidence_refs.get(e)]
    if missing:
        return ConditionResult(ScaleCondition.P3_P5_P6_EVIDENCE, _HOLD, f"entry evidence missing: {','.join(missing)}")
    return ConditionResult(ScaleCondition.P3_P5_P6_EVIDENCE, _PASS, "P3/P5/P6 entry evidence present")


def _flag_condition(cond: ScaleCondition, value: Optional[bool], ok_detail: str, bad_detail: str) -> ConditionResult:
    if value is True:
        return ConditionResult(cond, _PASS, ok_detail)
    if value is False:
        return ConditionResult(cond, _FAIL, bad_detail)
    return ConditionResult(cond, _HOLD, "boundary attestation missing (fail-closed)")


def _funnel(ctx: ScaleContext) -> ConditionResult:
    # Fail-closed HOLD: CPA / verified-rate thresholds are M6-OD-002 (OPEN) -> the pack invents none, so the Funnel
    # condition can never be PASS today. The AOV>=2-boxes sub-check is structural but insufficient alone.
    if not config.DASHBOARD_ALERT_THRESHOLDS_DEFINED:
        aov_note = ""
        if ctx.boxes_per_order is not None:
            aov_note = f"; AOV boxes/order={ctx.boxes_per_order} (>=2 required)"
        return ConditionResult(ScaleCondition.FUNNEL, _HOLD, "CPA/verified-rate thresholds unratified (M6-OD-002)" + aov_note)
    # (unreachable in the staged posture; kept for the ratified-threshold future path)
    if ctx.boxes_per_order is not None and ctx.boxes_per_order < 2:
        return ConditionResult(ScaleCondition.FUNNEL, _FAIL, "AOV below 2 boxes/order")
    return ConditionResult(ScaleCondition.FUNNEL, _HOLD, "thresholds ratified but funnel not fully evaluated (fail-closed)")


def _dashboard(ctx: ScaleContext) -> ConditionResult:
    # ROAS is verified-only by construction (M6.2F, RULE-003). But as SCALE EVIDENCE it is fail-closed HOLD until
    # the owner ratifies an attribution model (M6-OD-005 / SCALE_MODEL_RATIFIED=False, RULE-009).
    if not config.SCALE_MODEL_RATIFIED:
        return ConditionResult(ScaleCondition.DASHBOARD, _HOLD, "no scale-authoritative attribution model (M6-OD-005)")
    return ConditionResult(ScaleCondition.DASHBOARD, _HOLD, "scale model ratified but not yet scale-evidence graded (fail-closed)")


def _quality(ctx: ScaleContext) -> ConditionResult:
    if ctx.dq_overall is None:
        return ConditionResult(ScaleCondition.QUALITY, _HOLD, "data quality gate not run (fail-closed)")
    if ctx.dq_overall is DataQualityStatus.PASS:
        return ConditionResult(ScaleCondition.QUALITY, _PASS, "Data Quality Gate PASS")
    return ConditionResult(ScaleCondition.QUALITY, ctx.dq_overall, f"Data Quality Gate {ctx.dq_overall.value}")


def _risk(ctx: ScaleContext) -> ConditionResult:
    # HARD VETO (RULE-017): any active lock ⇒ FAIL. If the risk state was never observed ⇒ HOLD (fail-closed).
    active = active_risk_locks(ctx)
    if active:
        return ConditionResult(ScaleCondition.RISK, _FAIL, f"active risk lock(s): {','.join(active)} (RULE-017 hard veto)")
    if not ctx.risk_flags:
        return ConditionResult(ScaleCondition.RISK, _HOLD, "risk/suppression state not checked (fail-closed)")
    return ConditionResult(ScaleCondition.RISK, _PASS, "no recall/sale-lock/quality-hold/complaint-P0/spam/CRM-suppression")


def _approval(ctx: ScaleContext) -> ConditionResult:
    if ctx.owner_approved and ctx.budget_cap is not None and ctx.rollback_condition:
        return ConditionResult(ScaleCondition.APPROVAL, _PASS, "owner approved with budget cap + rollback condition")
    if not ctx.owner_approved:
        return ConditionResult(ScaleCondition.APPROVAL, _HOLD, "no owner approval yet (proposal only)")
    return ConditionResult(ScaleCondition.APPROVAL, _HOLD, "approval requires budget_cap + rollback_condition")


def evaluate_conditions(ctx: ScaleContext) -> Tuple[Tuple[ConditionResult, ...], ConditionStatus]:
    """Compute the 8 conditions + the worst-status overall. Pure computation — never acts (RULE-010)."""
    results = (
        _p3_p5_p6(ctx),
        _flag_condition(ScaleCondition.QUOTE_ORDER, ctx.quote_order_ok,
                        "Quote/Order boundary attested", "Quote/Order boundary failed (consumed)"),
        _flag_condition(ScaleCondition.PUBLIC_PRIVACY, ctx.public_privacy_ok,
                        "Public/Privacy boundary attested", "Public/Privacy boundary failed (consumed)"),
        _funnel(ctx),
        _dashboard(ctx),
        _quality(ctx),
        _risk(ctx),
        _approval(ctx),
    )
    overall = worst_status([r.status for r in results])
    return results, overall
