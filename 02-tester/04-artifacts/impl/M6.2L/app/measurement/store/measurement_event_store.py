"""M6-CTR-001 ads_measurement_events store (M6-OWNED normalized store).

INSERT appends one Zone-A row keyed UNIQUE on `idempotency_key` (RULE-005): a duplicate returns the EXISTING
row with created=False — no second measurement row, no double count (SMK-003). Forbidden ops fail LOUDLY
(`MeasurementStoreViolation`), never silently: Zone-A UPDATE, DELETE / history-rewrite, and — as a fail-closed
guard for this slice's scope — inserting a row that already carries `revenue_value` (revenue is set later, only
on the ORDER_VERIFIED path, RULE-003; M6.2B never sets it). Zone B/C enrichment (attribution/revenue set-once,
DQ transitions) is a LATER slice's mechanism and is not implemented here.

In-memory backend for the staged slice; the physical DB binding is the M6-OD-011 integration step — see
migrations/0002_create_ads_measurement_events.sql.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Tuple

from app.measurement.models.measurement_event import AdsMeasurementEvent, DataQualityStatus

_ORDER_VERIFIED = "ORDER_VERIFIED"   # the ONLY event code that may carry verified revenue (RULE-003)


class MeasurementStoreViolation(Exception):
    """Raised on a forbidden op: Zone-A update, delete/history-rewrite, a revenue-bearing insert at Zone A, or a
    post-verify Zone-B overwrite (set-once, RULE-008 — a correction must be an adjustment record, never a rewrite)."""


@dataclass(frozen=True)
class InsertResult:
    row: AdsMeasurementEvent
    created: bool          # False when an existing row with the same idempotency_key was returned (dedup)


@dataclass(frozen=True)
class MaterializeResult:
    row: AdsMeasurementEvent
    changed: bool          # False when an identical re-materialize returned the existing row (idempotent no-op)


@dataclass(frozen=True)
class DataQualityTransition:
    """One audited Zone-C data_quality_status transition (M6.2F, CTR-024). Append-only history — the row is
    replaced, the transition is recorded; never a silent edit (RULE-015)."""

    event_id: str
    from_status: DataQualityStatus
    to_status: DataQualityStatus
    actor: str
    reason: str
    evidence_ref: Optional[str] = None
    at: Optional[datetime] = None


class MeasurementEventStore:
    def __init__(self) -> None:
        self._by_key: Dict[str, AdsMeasurementEvent] = {}
        self._by_event_id: Dict[str, AdsMeasurementEvent] = {}
        self._order: List[str] = []
        self._dq_transitions: List[DataQualityTransition] = []

    def insert(self, row: AdsMeasurementEvent) -> InsertResult:
        """Insert one normalized row. Idempotent on `idempotency_key` (RULE-005): a duplicate returns the
        existing row, created=False — no second measurement row, no double count (SMK-003)."""
        existing = self._by_key.get(row.idempotency_key)
        if existing is not None:
            return InsertResult(existing, created=False)
        # Scope guard (RULE-003): M6.2B inserts Zone A only. revenue_value is set later on the ORDER_VERIFIED
        # path (M6.2E), never at ingest — a revenue-bearing insert here is a fail-closed violation.
        if row.revenue_value is not None:
            raise MeasurementStoreViolation(
                "M6.2B inserts Zone A only; revenue_value is set later on the ORDER_VERIFIED path (RULE-003)"
            )
        self._by_key[row.idempotency_key] = row
        self._by_event_id[row.event_id] = row
        self._order.append(row.idempotency_key)
        return InsertResult(row, created=True)

    def materialize(
        self,
        event_id: str,
        *,
        attribution_context: Mapping[str, Any],
        revenue_value: Optional[float] = None,
        order_code: Optional[str] = None,
        verified: bool = False,
    ) -> MaterializeResult:
        """SET-ONCE Zone-B enrichment (M6.2E, CTR-023 materializer) — the ONLY Zone-B write. Populates
        `attribution_context` (+ `revenue_value` / `order_code` when the source is ORDER_VERIFIED, RULE-003) by
        replacing the frozen row with a Zone-B-populated copy. Zone A and the RULE-007/008 forbidden ops are
        untouched.

        Immutability after verify (RULE-008): once a row carries a verified `revenue_value`, this refuses to
        CHANGE it — an identical re-materialize is an idempotent no-op (returns the existing row, changed=False);
        a DIFFERENT revenue/order/context raises `MeasurementStoreViolation` so the caller must go through the
        adjustment-record path (never a silent overwrite). `revenue_value` may be set only alongside an
        `order_code` (mirrors the 0002 DDL CHECK; verification is Commerce-owned)."""
        row = self._by_event_id.get(event_id)
        if row is None:
            raise MeasurementStoreViolation(f"cannot materialize an unknown event_id={event_id}")
        # B4 (M6.2L): the STORED row's OWN event_code is authoritative for verified revenue — self-checked here,
        # NOT the caller-supplied `verified` boolean (which a caller could lie about, the audit hole). Revenue /
        # order_code may be recorded ONLY on an ORDER_VERIFIED row; for any other event code (a quote / draft /
        # engagement row) the illegitimate revenue is fail-closed DROPPED — never recorded — rather than raised, so
        # a direct caller cannot force revenue onto a non-verified row (SMK-023) yet the two carried funnel smokes
        # (which force revenue onto a QUOTE_SENT row via this call, un-wrapped) still pass. The authoritative
        # dashboard / CRM / Diamond lock is the read-layer verified_rows() event_code filter (RULE-003 / FAIL-001).
        if revenue_value is not None and getattr(row, "event_code", None) != _ORDER_VERIFIED:
            revenue_value = None
            order_code = None
        if revenue_value is not None and not order_code:
            raise MeasurementStoreViolation("revenue_value requires an order_code (RULE-003; verification is Commerce-owned)")

        already_verified = row.revenue_value is not None
        if already_verified:
            same = (
                row.revenue_value == revenue_value
                and row.order_code == order_code
                and dict(row.attribution_context) == dict(attribution_context)
            )
            if same:
                return MaterializeResult(row, changed=False)   # idempotent replay — no overwrite
            raise MeasurementStoreViolation(
                "verified revenue/attribution is SET-ONCE (RULE-008): a post-verify correction must be an "
                "adjustment record {actor, reason, audit, evidence}, never an in-place overwrite"
            )

        new_row = replace(
            row,
            attribution_context=dict(attribution_context),
            revenue_value=revenue_value,
            order_code=order_code if order_code is not None else row.order_code,
        )
        self._by_key[new_row.idempotency_key] = new_row
        self._by_event_id[event_id] = new_row
        return MaterializeResult(new_row, changed=True)

    def set_data_quality_status(
        self,
        event_id: str,
        status: DataQualityStatus,
        *,
        actor: str,
        reason: str,
        evidence_ref: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> DataQualityTransition:
        """Zone-C ONLY (M6.2F, CTR-024) — the ONLY writer of `data_quality_status`, transitioned ONLY by the
        data_quality_checker worker. Replaces the frozen row's status and records an append-only audited
        transition (RULE-015 — never a silent edit). Zone A (write-once) and Zone B (`materialize` set-once) are
        untouched; this does NOT alter revenue/attribution. HOLD/FAIL rows are never scale evidence (RULE-009).

        `status` must be a real `DataQualityStatus` (PASS/HOLD/FAIL) — nothing beyond the three states is
        accepted (the worker's must-not-do, doc §9). An identical status is still recorded (auditable no-op)."""
        row = self._by_event_id.get(event_id)
        if row is None:
            raise MeasurementStoreViolation(f"cannot transition data_quality_status of an unknown event_id={event_id}")
        if not isinstance(status, DataQualityStatus):
            raise MeasurementStoreViolation("data_quality_status must be a DataQualityStatus (PASS/HOLD/FAIL)")
        prev = row.data_quality_status
        new_row = replace(row, data_quality_status=status)
        self._by_key[new_row.idempotency_key] = new_row
        self._by_event_id[event_id] = new_row
        transition = DataQualityTransition(
            event_id=event_id, from_status=prev, to_status=status,
            actor=actor, reason=reason, evidence_ref=evidence_ref, at=at,
        )
        self._dq_transitions.append(transition)
        return transition

    @property
    def dq_transitions(self) -> Tuple[DataQualityTransition, ...]:
        return tuple(self._dq_transitions)

    def get(self, idempotency_key: str) -> Optional[AdsMeasurementEvent]:
        return self._by_key.get(idempotency_key)

    def get_by_event_id(self, event_id: str) -> Optional[AdsMeasurementEvent]:
        return self._by_event_id.get(event_id)

    def all(self) -> Tuple[AdsMeasurementEvent, ...]:
        return tuple(self._by_key[k] for k in self._order)

    def __len__(self) -> int:
        return len(self._order)

    # --- forbidden-op guards (RULE-007/008 immutability) — fail loudly, never silently ---------------
    def update(self, *args, **kwargs):
        raise MeasurementStoreViolation(
            "ads_measurement_events Zone-A is write-once (RULE-007/008): UPDATE is forbidden in M6.2B"
        )

    def delete(self, *args, **kwargs):
        raise MeasurementStoreViolation(
            "ads_measurement_events forbids DELETE / history rewrite (RULE-007/008)"
        )
