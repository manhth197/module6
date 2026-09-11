"""M6-CTR-026 Scale-Gate approval flow — compute conditions, assemble evidence, PROPOSE; NEVER act (RULE-010).

`propose(...)` computes the 8 doc §16 conditions, assembles evidence refs, and creates an INERT PROPOSED
`ads_scale_request` (budget_cap + rollback_condition are request fields). `record_owner_decision(...)` records an
EXPLICIT `OwnerDecision` (APPROVE/REJECT): an APPROVE RE-CHECKS the Risk row at approval time (RULE-017) and
requires a budget cap + rollback condition + a non-FAIL request — otherwise it is REFUSED (the request cannot be
approved, SMK-009). The system NEVER approves its own request (RULE-015) and this class has DELIBERATELY NO method
that raises a budget, enables a campaign, opens audience scale, sends, or publishes (RULE-010, FAIL-006). Every
outcome is audited (subject masked).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Dict, Mapping, Optional

from app import config
from app.measurement.masking import mask
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
from app.measurement.scale.scale_request_store import ScaleRequestStore


class ScaleGateViolation(Exception):
    """Raised when an approval is REFUSED (active risk lock, missing budget cap/rollback, or a FAIL request) — a
    fail-closed hard stop; the request is NOT approved and nothing is scaled."""


class ScaleGate:
    def __init__(self, store: ScaleRequestStore, audit: Any = None) -> None:
        # RULE-010: no Transport, no budget API, no connector — this service holds only the inert request store.
        self._store = store
        self._audit = audit

    def propose(
        self,
        request_id: str,
        scale_target: Dict[str, Any],
        context: ScaleContext,
        *,
        budget_cap: Optional[float] = None,
        rollback_condition: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> AdsScaleRequest:
        """Compute conditions + assemble evidence + create a PROPOSED (inert) scale request. Never acts."""
        results, overall = evaluate_conditions(context)
        evidence_refs = self._assemble_evidence(context)
        request = AdsScaleRequest(
            request_id=request_id,
            scale_target=dict(scale_target),
            budget_cap=budget_cap,
            rollback_condition=rollback_condition,
            evidence_refs=evidence_refs,
            condition_results=results,
            overall_status=overall,
            approval_state=ApprovalState.PROPOSED,
            created_at=now,
        )
        self._store.create(request)
        if self._audit is not None:
            self._audit.record(
                "HOLD" if overall is not DataQualityStatus.PASS else "IDENTITY_RESOLVE",
                f"SCALE_REQUEST_PROPOSED_{overall.value}",
                detail=f"request={request_id};overall={overall.value};" + ";".join(
                    f"{r.condition.value}={r.status.value}" for r in results
                ),
            )
        return request

    def record_owner_decision(
        self,
        request_id: str,
        decision: OwnerDecision,
        *,
        current_risk_flags: Optional[Mapping[str, bool]] = None,
        now: Optional[datetime] = None,
    ) -> AdsScaleRequest:
        """Record an EXPLICIT owner decision. APPROVE re-checks the Risk row at approval (RULE-017) and requires a
        budget cap + rollback condition + a non-FAIL request; otherwise it is REFUSED (ScaleGateViolation). REJECT
        is always recordable. The system never synthesizes a decision (RULE-015)."""
        req = self._store.get(request_id)
        if req is None:
            raise ScaleGateViolation(f"unknown scale_request {request_id}")
        if req.approval_state in (ApprovalState.APPROVED, ApprovalState.REJECTED):
            raise ScaleGateViolation(f"scale_request {request_id} already {req.approval_state.value}")

        if decision.decision is DecisionKind.REJECT:
            new = replace(req, approval_state=ApprovalState.REJECTED, decision=decision, decided_at=now)
            self._store.update_state(new)
            self._audit_decision("SCALE_REQUEST_REJECTED", decision, request_id)
            return new

        # APPROVE — fail-closed gates before recording the approval (still nothing is executed, RULE-010):
        self._assert_risk_clear_at_approval(req, current_risk_flags)
        if req.budget_cap is None or not req.rollback_condition:
            raise ScaleGateViolation("cannot approve without a budget_cap and a rollback_condition (RULE-010)")
        if req.overall_status is DataQualityStatus.FAIL:
            raise ScaleGateViolation("cannot approve a FAIL scale request (fail-closed)")

        new = replace(req, approval_state=ApprovalState.APPROVED, decision=decision, decided_at=now)
        self._store.update_state(new)
        self._audit_decision("SCALE_REQUEST_APPROVED", decision, request_id)
        return new

    # --- helpers (all inert) -------------------------------------------------------------------------
    @staticmethod
    def _assert_risk_clear_at_approval(req: AdsScaleRequest, current_risk_flags: Optional[Mapping[str, bool]]) -> None:
        """RULE-017 hard veto RE-CHECKED at approval time, FAIL-CLOSED. A fresh risk read clears ONLY when it is
        COMPLETE — every one of the 6 RISK_LOCKS observed AND none active. An empty / partial / absent read means
        the risk state was NOT (fully) observed, so it does NOT clear: it falls back to the proposal's Risk
        condition, which only a PASS clears. (Adversarial-review fix: `{}` / partial maps forwarded by the API
        handler previously read as 'clear' via an `is not None` check — an unobserved lock could be active.)"""
        if current_risk_flags is not None:
            active = active_risk_locks(ScaleContext(risk_flags=dict(current_risk_flags)))
            if active:
                raise ScaleGateViolation(f"cannot approve: active risk lock(s) {','.join(active)} (RULE-017)")
            if all(lock in current_risk_flags for lock in RISK_LOCKS):
                return   # complete fresh read, none active -> cleared
            # empty / partial read: risk not fully observed -> fail-closed, fall through to the proposal fallback
        risk_res = next((c for c in req.condition_results if c.condition is ScaleCondition.RISK), None)
        if risk_res is None or risk_res.status is not DataQualityStatus.PASS:
            raise ScaleGateViolation("cannot approve: risk not fully re-checked / not PASS at approval (RULE-017, fail-closed)")

    def _assemble_evidence(self, context: ScaleContext) -> tuple:
        refs = []
        for key in ("ENTRY-001", "ENTRY-002", "ENTRY-003", "ENTRY-004"):
            ref = context.entry_evidence_refs.get(key)
            if ref:
                refs.append(f"{key}:{mask(ref)}")
        if context.dq_overall is not None:
            refs.append(f"dq_gate:{context.dq_overall.value}")
        return tuple(refs)

    def _audit_decision(self, code: str, decision: OwnerDecision, request_id: str) -> None:
        if self._audit is not None:
            # Audit detail is MACHINE-SAFE only (adversarial-review fix): the untrusted owner-supplied free-text
            # `reason` / `audit_ref` are NOT echoed into the audit log (they could carry PII, and the audit sink
            # does not identity-mask `detail`). `request_id` is a hash id and `decision` is an enum; the full
            # decision (reason/audit_ref/evidence) lives in the durable OwnerDecision record. `subject` (actor) is
            # masked by the audit sink.
            self._audit.record(
                "HOLD", code, subject=decision.actor,
                detail=f"request={request_id};decision={decision.decision.value}",
            )
