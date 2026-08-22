"""M6-CTR-017 POST /api/ads/conversions — framework-neutral request handler (M6.2C).

`handle_conversions_request(body, deps)` is a PURE function over an UNTRUSTED body (RULE-H03). It re-validates
server-side into CTR-017 error codes, creates an internal `conversion_events` row, and TRANSACTIONALLY enqueues
the measurement outbox (fan-out per platform) — it NEVER sends externally (RULE-004; it holds no Transport).
Revenue is recorded ONLY from ORDER_VERIFIED (RULE-003). Consent is referenced here (checkpoint 1) and
RE-VALIDATED by the dispatcher at send (checkpoint 2, RULE-002). Identity (`customer_or_guest_key`) is masked on
every export (O1). The HTTP routing / status-code mapping binds at the owner integration step (M6-OD-011).
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Tuple

from app.measurement.audit import AuditLog
from app.measurement.masking import mask
from app.measurement.models.conversion_event import CURRENCY_VND, ConversionEvent, DispatchState
from app.measurement.outbox.enqueue import enqueue_measurement
from app.measurement.registry.validator import EventValidator

_ORDER_VERIFIED = "ORDER_VERIFIED"


@dataclass
class ConversionDeps:
    validator: EventValidator
    conversion_store: Any          # ConversionEventStore
    measurement_outbox: Any        # OutboxStore[MeasurementOutboxItem]
    audit: AuditLog
    max_retries: int = 5


@dataclass(frozen=True)
class ConversionResult:
    """CTR-017 response (+ PII-safe error fields). status in {CREATED, DUPLICATE, REJECTED}."""

    status: str
    correlation_id: str
    conversion_id: Optional[str] = None
    idempotent_replay: bool = False
    dispatch_state: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    field: Optional[str] = None


def handle_conversions_request(body: Any, deps: ConversionDeps) -> ConversionResult:
    audit = deps.audit
    correlation_id = body.get("correlation_id") if isinstance(body, Mapping) else None
    if not isinstance(correlation_id, str) or not correlation_id:
        correlation_id = "corr_" + uuid.uuid4().hex

    if not isinstance(body, Mapping):
        return _reject(audit, correlation_id, "SCHEMA_INVALID", "request body must be an object")

    # required string fields (server re-validates; client never trusted alone, RULE-H03)
    for fname in ("event_code", "source_event_id", "customer_or_guest_key"):
        val = body.get(fname)
        if not isinstance(val, str) or not val:
            return _reject(audit, correlation_id, "SCHEMA_INVALID", f"{fname} is required", field=fname)
    if not isinstance(body.get("idempotency_key"), str) or not body.get("idempotency_key"):
        return _reject(audit, correlation_id, "SCHEMA_INVALID", "idempotency_key is required", field="idempotency_key")

    # consent reference required (CTR-017); the STATE is gated at send (dispatcher), not at creation
    consent_snapshot_id = body.get("consent_snapshot_id")
    if not isinstance(consent_snapshot_id, str) or not consent_snapshot_id:
        return _reject(
            audit, correlation_id, "CONSENT_MISSING_OR_INVALID", "consent_snapshot_id is required",
            field="consent_snapshot_id",
        )

    occurred_at, ts_ok = _parse_ts(body.get("occurred_at"))
    if not ts_ok:
        return _reject(
            audit, correlation_id, "SCHEMA_INVALID", "occurred_at must be an ISO-8601 tz-aware datetime",
            field="occurred_at",
        )

    event_code = body["event_code"]
    source_event_id = body["source_event_id"]
    customer_or_guest_key = body["customer_or_guest_key"]
    order_code = body.get("order_code") if isinstance(body.get("order_code"), str) else None

    # registry gate (RULE-001): unknown/deregistered event -> UNKNOWN_EVENT
    vr = deps.validator.validate(event_code)
    if not vr.accepted:
        audit.record("REJECT", "CONVERSION_UNKNOWN_EVENT", event_code=event_code, detail=_corr(correlation_id))
        return ConversionResult(
            status="REJECTED", correlation_id=correlation_id, error_code="UNKNOWN_EVENT",
            message="event is not an active registered event",
        )

    # revenue ONLY from ORDER_VERIFIED (RULE-003); PAYMENT_COMPLETED etc. non-revenue (M6-OD-008 default)
    revenue_value = body.get("revenue_value")
    currency: Optional[str] = None
    if revenue_value is not None:
        if isinstance(revenue_value, bool) or not isinstance(revenue_value, (int, float)):
            return _reject(audit, correlation_id, "SCHEMA_INVALID", "revenue_value must be a number", field="revenue_value")
        if event_code != _ORDER_VERIFIED:
            audit.record("REJECT", "CONVERSION_REVENUE_NOT_VERIFIED", event_code=event_code, detail=_corr(correlation_id))
            return ConversionResult(
                status="REJECTED", correlation_id=correlation_id, error_code="REVENUE_NOT_VERIFIED",
                message="revenue is recorded only for an ORDER_VERIFIED conversion",
            )
        currency = CURRENCY_VND
        revenue_value = float(revenue_value)

    # server-recompute the conversion replay key (never trust the client value; RULE-H03). Derived from the
    # conversion's OWN stable inputs (the conversion carries no page/session, so the track RULE-005 formula does
    # not apply here) -> a replayed conversion maps to the SAME key -> DUPLICATE (idempotent, replay-safe).
    idem = _conversion_key(event_code, source_event_id, customer_or_guest_key, occurred_at, order_code)
    conversion_id = "conv_" + idem[:24]

    conversion = ConversionEvent(
        conversion_id=conversion_id,
        event_code=event_code,
        source_event_id=source_event_id,
        correlation_id=correlation_id,
        customer_or_guest_key=customer_or_guest_key,
        consent_snapshot_id=consent_snapshot_id,
        occurred_at=occurred_at,
        idempotency_key=idem,
        attribution_context_ref=body.get("attribution_context_ref") if isinstance(body.get("attribution_context_ref"), str) else None,
        revenue_value=revenue_value,
        currency=currency,
        order_code=order_code,
        dispatch_state=DispatchState.CREATED,
        created_at=occurred_at,
    )
    created_result = deps.conversion_store.create(conversion)
    if not created_result.created:
        # replay: no new conversion, NO re-enqueue (no double count, RULE-005 / SMK-003)
        return ConversionResult(
            status="DUPLICATE", correlation_id=correlation_id, conversion_id=created_result.row.conversion_id,
            idempotent_replay=True, dispatch_state=DispatchState.QUEUED.value,
        )

    # transactionally ENQUEUE the measurement outbox (fan-out per platform); runtime sends nothing (RULE-004)
    enqueue_measurement(conversion, deps.measurement_outbox, max_retries=deps.max_retries)
    return ConversionResult(
        status="CREATED", correlation_id=correlation_id, conversion_id=conversion_id,
        idempotent_replay=False, dispatch_state=DispatchState.QUEUED.value,
    )


# --- helpers ---------------------------------------------------------------------------------------
def _corr(correlation_id: str) -> str:
    return f"corr={mask(correlation_id)}"   # O1: correlation_id masked on export


def _reject(audit: AuditLog, correlation_id: str, error_code: str, message: str, field: Optional[str] = None) -> ConversionResult:
    detail = _corr(correlation_id) + (f" field={field}" if field else "")
    audit.record("REJECT", f"CONVERSION_{error_code}", detail=detail)
    return ConversionResult(
        status="REJECTED", correlation_id=correlation_id, error_code=error_code, message=message, field=field,
    )


def _parse_ts(value: Any) -> Tuple[Optional[datetime], bool]:
    if isinstance(value, datetime):
        return value, value.tzinfo is not None
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None, False
        return dt, dt.tzinfo is not None
    return None, False


def _conversion_key(event_code: str, source_event_id: str, customer_or_guest_key: str, occurred_at: datetime, order_code: Optional[str]) -> str:
    occurred_utc = occurred_at.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    parts = [event_code, source_event_id, customer_or_guest_key, occurred_utc, order_code or ""]
    canonical = "|".join(p.replace("\\", "\\\\").replace("|", "\\|") for p in parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
