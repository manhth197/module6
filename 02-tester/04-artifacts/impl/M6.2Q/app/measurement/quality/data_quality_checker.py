"""M6-CTR-024 data_quality_checker — the worker that evaluates the 8 doc §15 gate items for a measurement row.

`check(event, context)` returns an `AdsDataQualityCheck` whose per-item and overall status are ONLY PASS/HOLD/
FAIL (nothing beyond the three states — the worker's must-not-do, doc §9). `check_and_record(...)` additionally
transitions the row's Zone-C `data_quality_status` via the store's audited setter (RULE-015 — never a silent
edit) and audits the decision (subject masked, RULE-014).

Fail-closed everywhere: a missing signal is HOLD (never PASS). FAIL is reserved for a real violation — an
unregistered / owner-less event, missing/expired/opt-out consent, a double count, a broken identity/order map,
a NON-verified figure counted as revenue (RULE-003 / FAIL-001), active suppression not reflected (RULE-017), or a
visual-only dashboard metric with no trace (doc §15 L308). HOLD/FAIL rows are never scale evidence (RULE-009).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.quality.data_quality_check import (
    AdsDataQualityCheck,
    GateItem,
    GateItemResult,
    GateStatus,
)

_ORDER_VERIFIED = "ORDER_VERIFIED"
_PASS, _HOLD, _FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL


@dataclass
class DQContext:
    """Non-event signals the checker cannot derive from the row itself (each fail-closed): the registry/consent/
    dedup/identity findings, suppression state, and whether the dashboard metric carries a trace. Attribution and
    Verified-Revenue are derived from the event. `None` = unknown ⇒ HOLD (never PASS)."""

    event_registered: Optional[bool] = None
    event_owner_known: Optional[bool] = None
    consent_valid: Optional[bool] = None
    no_duplicate: Optional[bool] = None
    identity_mapped: Optional[bool] = None
    # Fail-closed like every sibling signal (adversarial review): None = suppression state UNKNOWN (not checked)
    # -> HOLD, never PASS. False = confirmed no active suppression -> PASS. True = active (then check reflected).
    suppression_active: Optional[bool] = None
    suppression_reflected: Optional[bool] = None
    dashboard_has_trace: Optional[bool] = None


def _flag(value: Optional[bool]) -> GateStatus:
    """True→PASS, False→FAIL, None→HOLD (fail-closed)."""
    if value is True:
        return _PASS
    if value is False:
        return _FAIL
    return _HOLD


class DataQualityChecker:
    def __init__(self, store: Any = None, audit: Any = None) -> None:
        self._store = store
        self._audit = audit

    def check(self, event: Any, context: Optional[DQContext] = None) -> AdsDataQualityCheck:
        ctx = context or DQContext()
        items = [
            self._event_registry(ctx),
            self._consent(ctx),
            self._dedup(ctx),
            self._identity(ctx),
            self._attribution(event),
            self._verified_revenue(event),
            self._suppression(ctx),
            self._dashboard(ctx),
        ]
        return AdsDataQualityCheck.from_items(items, subject_event_id=getattr(event, "event_id", None))

    def check_and_record(
        self, event: Any, context: Optional[DQContext] = None, *, at: Optional[datetime] = None
    ) -> AdsDataQualityCheck:
        """Evaluate + transition the row's Zone-C status (audited). The store is the ONLY writer of
        data_quality_status; this worker is its ONLY caller (CTR-024)."""
        result = self.check(event, context)
        event_id = getattr(event, "event_id", None)
        if self._store is not None and event_id is not None:
            self._store.set_data_quality_status(
                event_id, result.overall, actor="data_quality_checker",
                reason=f"dq_gate_overall={result.overall.value}", evidence_ref=None, at=at,
            )
        if self._audit is not None:
            self._audit.record(
                "HOLD" if result.overall is not _PASS else "IDENTITY_RESOLVE",
                f"DATA_QUALITY_{result.overall.value}",
                subject=getattr(event, "guest_id", None) or getattr(event, "customer_id", None),
                detail=f"event={event_id};" + ";".join(f"{i.item.value}={i.status.value}" for i in result.items),
            )
        return result

    # --- the 8 gate items (doc §15) ------------------------------------------------------------------
    @staticmethod
    def _event_registry(ctx: DQContext) -> GateItemResult:
        # PASS only when the event is registered AND has an owner; unregistered/owner-less ⇒ FAIL; unknown ⇒ HOLD.
        if ctx.event_registered is False or ctx.event_owner_known is False:
            return GateItemResult(GateItem.EVENT_REGISTRY, _FAIL, "unknown event or owner-less (RULE-001)")
        if ctx.event_registered is None or ctx.event_owner_known is None:
            return GateItemResult(GateItem.EVENT_REGISTRY, _HOLD, "registry signal missing (fail-closed)")
        return GateItemResult(GateItem.EVENT_REGISTRY, _PASS, "event registered, owner known")

    @staticmethod
    def _consent(ctx: DQContext) -> GateItemResult:
        return GateItemResult(
            GateItem.CONSENT, _flag(ctx.consent_valid),
            "consent valid at event time" if ctx.consent_valid else "missing/expired/opt-out or unknown (RULE-002)",
        )

    @staticmethod
    def _dedup(ctx: DQContext) -> GateItemResult:
        return GateItemResult(
            GateItem.DEDUP, _flag(ctx.no_duplicate),
            "no duplicate / merged" if ctx.no_duplicate else "possible Pixel/CAPI/Offline double count (RULE-005)",
        )

    @staticmethod
    def _identity(ctx: DQContext) -> GateItemResult:
        return GateItemResult(
            GateItem.IDENTITY, _flag(ctx.identity_mapped),
            "guest/customer/order mapping clear" if ctx.identity_mapped else "identity/order map unclear (RULE-006)",
        )

    @staticmethod
    def _attribution(event: Any) -> GateItemResult:
        ctx_map = getattr(event, "attribution_context", None) or {}
        conflict = ctx_map.get("conflict_status") if isinstance(ctx_map, dict) else None
        confidence = ctx_map.get("source_confidence") if isinstance(ctx_map, dict) else None
        if not ctx_map:
            return GateItemResult(GateItem.ATTRIBUTION, _HOLD, "attribution not materialized yet (fail-closed)")
        if conflict == "NONE" and confidence == "HIGH":
            return GateItemResult(GateItem.ATTRIBUTION, _PASS, "chain complete, no conflict")
        # ambiguous source / unhandled conflict ⇒ HOLD (never scale evidence, RULE-009)
        return GateItemResult(
            GateItem.ATTRIBUTION, _HOLD, f"ambiguous source (confidence={confidence};conflict={conflict})"
        )

    @staticmethod
    def _verified_revenue(event: Any) -> GateItemResult:
        revenue = getattr(event, "revenue_value", None)
        code = getattr(event, "event_code", None)
        if revenue is None:
            return GateItemResult(GateItem.VERIFIED_REVENUE, _PASS, "no revenue figure (nothing miscounted)")
        if code != _ORDER_VERIFIED or not getattr(event, "order_code", None):
            # a non-verified figure presented as revenue ⇒ revenue misuse (RULE-003, FAIL-001)
            return GateItemResult(
                GateItem.VERIFIED_REVENUE, _FAIL,
                "revenue on a non-ORDER_VERIFIED event (quote/draft/unpaid counted as revenue, FAIL-001)",
            )
        return GateItemResult(GateItem.VERIFIED_REVENUE, _PASS, "revenue from Commerce Verified Revenue (ORDER_VERIFIED)")

    @staticmethod
    def _suppression(ctx: DQContext) -> GateItemResult:
        # Fail-closed: if whether suppression applies was never observed -> HOLD (never PASS by default).
        if ctx.suppression_active is None:
            return GateItemResult(GateItem.SUPPRESSION, _HOLD, "suppression state not checked (fail-closed)")
        if ctx.suppression_active is False:
            return GateItemResult(GateItem.SUPPRESSION, _PASS, "confirmed no active suppression")
        # suppression is active -> it must be reflected (RULE-017); unknown reflection is fail-closed HOLD.
        if ctx.suppression_reflected is True:
            return GateItemResult(GateItem.SUPPRESSION, _PASS, "recall/sale-lock/CRM suppression reflected (RULE-017)")
        if ctx.suppression_reflected is None:
            return GateItemResult(GateItem.SUPPRESSION, _HOLD, "suppression active, reflection unknown (fail-closed)")
        return GateItemResult(GateItem.SUPPRESSION, _FAIL, "active suppression NOT reflected (RULE-017)")

    @staticmethod
    def _dashboard(ctx: DQContext) -> GateItemResult:
        return GateItemResult(
            GateItem.DASHBOARD, _flag(ctx.dashboard_has_trace),
            "metric has sample evidence + trace" if ctx.dashboard_has_trace
            else "visual-only, no source trace (doc §15) or unknown",
        )
