"""M6-CTR-016 POST /api/ads/events/track — framework-neutral request handler (M6.2B).

`handle_track_request(body, deps)` is a PURE function over an UNTRUSTED request body (RULE-H03). It:
  1. re-validates the body server-side (client validation is NEVER trusted alone) into CTR-016 error codes;
  2. derives `raw_event_hash` SERVER-SIDE (a deterministic canonicalization of the raw body — never a client
     hash) so the LOCKED RULE-005 key is server-computed and replay-stable (SMK-003);
  3. drives the hardened ingest seam (event_registry gate = the SECOND unknown-event layer, RULE-001);
  4. on ACCEPT, normalizes into the M6-CTR-001 ads_measurement_event store (Zone-A insert, UNIQUE dedup);
  5. returns the CTR-016 response {status, log_id, event_id, idempotent_replay, data_quality_status,
     correlation_id} with a PII-safe error model {error_code, message, field?, correlation_id}.

It NEVER sends externally (RULE-004; there is no egress client in this path) and flips no flag. The HTTP
framework / routing / status-code mapping is the owner integration step (M6-OD-011); this handler is its core.

O1: `session_id` / `correlation_id` are masked (`mask()`) on every EXPORT surface (audit detail); the durable
web_event_logs / ads_measurement_events rows keep the raw value for dedup/trace joins. The response returns the
caller's own `correlation_id` (their trace id) unmasked — that is not an export surface.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterator, Mapping, Optional, Tuple

from app.measurement.audit import AuditLog
from app.measurement.ingest import IngestService
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.masking import mask
from app.measurement.models.consumed import ConsentScope
from app.measurement.normalize import normalize_to_measurement_event
from app.measurement.store.measurement_event_store import (
    MeasurementEventStore,
    MeasurementStoreViolation,
)

# Minimal raw-PII detectors for the public-safe payload guard (RULE-014, CTR-016 RAW_PII_IN_PAYLOAD). This is a
# fail-closed tripwire, not a full DLP: an email or a VN phone number in the payload is refused outright.
_EMAIL_RX = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_VN_PHONE_RX = re.compile(r"(?:\+?84|0)\d{9,10}")


@dataclass
class TrackDeps:
    """Wired collaborators (staged in-memory). `web_store` is the SAME instance inside `ingest_service`."""

    ingest_service: IngestService
    web_store: WebEventLogStore
    measurement_store: MeasurementEventStore
    audit: AuditLog


@dataclass(frozen=True)
class TrackResult:
    """CTR-016 response (+ PII-safe error fields). `status` in {ACCEPTED, DUPLICATE, REJECTED}."""

    status: str
    correlation_id: str
    log_id: Optional[str] = None
    event_id: Optional[str] = None
    idempotent_replay: bool = False
    data_quality_status: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    field: Optional[str] = None


def handle_track_request(body: Any, deps: TrackDeps) -> TrackResult:
    audit = deps.audit

    # correlation_id: prefer a client-supplied trace id (continuity); else generate one. Masked on export (O1).
    correlation_id = body.get("correlation_id") if isinstance(body, Mapping) else None
    if not isinstance(correlation_id, str) or not correlation_id:
        correlation_id = "corr_" + uuid.uuid4().hex

    # 1. The body itself is untrusted (RULE-H03) — must be an object.
    if not isinstance(body, Mapping):
        return _reject(audit, correlation_id, "SCHEMA_INVALID", "request body must be an object")

    # 2. Required string fields present + correctly typed (server re-validates; client never trusted alone).
    event_code = body.get("event_code")
    if not isinstance(event_code, str) or not event_code:
        return _reject(audit, correlation_id, "SCHEMA_INVALID", "event_code is required", field="event_code")
    for fname in ("page_id", "session_id", "source"):
        val = body.get(fname)
        if not isinstance(val, str) or not val:
            return _reject(audit, correlation_id, "SCHEMA_INVALID", f"{fname} is required", field=fname)

    # 3. idempotency_key MUST be present (CTR-016) — but the value is RECOMPUTED server-side and never trusted
    #    (RULE-005 locked formula + RULE-H03).
    if not isinstance(body.get("idempotency_key"), str) or not body.get("idempotency_key"):
        return _reject(
            audit, correlation_id, "IDEMPOTENCY_KEY_MISSING", "idempotency_key is required",
            field="idempotency_key",
        )

    # 4. consent_snapshot_id required (CTR-016 consent reference; RULE-002). Absent field => reject. An invalid
    #    consent STATE (missing/expired/opt-out) is fail-closed for EGRESS by the seam; the event still logs.
    consent_snapshot_id = body.get("consent_snapshot_id")
    if not isinstance(consent_snapshot_id, str) or not consent_snapshot_id:
        return _reject(
            audit, correlation_id, "CONSENT_MISSING_OR_INVALID", "consent_snapshot_id is required",
            field="consent_snapshot_id",
        )

    # 5. event_ts required + tz-aware (the seam re-checks; a naive/invalid ts is a client schema error here).
    event_ts, ts_ok = _parse_event_ts(body.get("event_ts"))
    if not ts_ok:
        return _reject(
            audit, correlation_id, "SCHEMA_INVALID", "event_ts must be an ISO-8601 tz-aware datetime",
            field="event_ts",
        )

    # 6. payload (optional) must be PUBLIC-SAFE: an object with NO raw PII (RULE-014).
    payload = body.get("payload")
    if payload is not None and not isinstance(payload, Mapping):
        return _reject(audit, correlation_id, "SCHEMA_INVALID", "payload must be an object", field="payload")
    if isinstance(payload, Mapping) and _contains_raw_pii(payload):
        return _reject(
            audit, correlation_id, "RAW_PII_IN_PAYLOAD", "payload must not contain raw PII", field="payload",
        )

    # 7. raw_event_hash DERIVED server-side (never a client hash; RULE-H03) — deterministic + replay-stable.
    raw_event_hash = _raw_event_hash(body)

    page_id = str(body["page_id"])
    session_id = str(body["session_id"])
    source = str(body["source"])
    guest_id = body.get("guest_id") if isinstance(body.get("guest_id"), str) else None

    # A4 (M6.2L): optional M6-owned ad-hierarchy ids decoded from the M6 ad-link / UTM (campaign/adset/ad/
    # live_session). These are platform identifiers (NOT PII, NOT channel free-text) — the same class as the
    # type-checked-only page_id/session_id above. Untrusted (RULE-H03): a PRESENT-but-non-string / empty value is a
    # fail-closed SCHEMA_INVALID reject; absent => None. Persisted to Zone-A so the resolver can reach HIGH source
    # confidence via the real API path (SMK-020). No revenue, no send, no flag flip here.
    ad_hierarchy: dict = {}
    for fname in ("campaign_id", "adset_id", "ad_id", "live_session_id"):
        if fname in body:
            val = body.get(fname)
            if not isinstance(val, str) or not val:
                return _reject(audit, correlation_id, "SCHEMA_INVALID", f"{fname} must be a non-empty string", field=fname)
            ad_hierarchy[fname] = val

    # 8. Drive the HARDENED seam. The event_registry gate is the SECOND independent unknown-event layer
    #    (RULE-001). The seam never raises (F1) and consent cannot fail-open (F2).
    result = deps.ingest_service.ingest_event(
        event_code=event_code,
        page_id=page_id,
        session_id=session_id,
        source=source,
        event_ts=event_ts,
        raw_event_hash=raw_event_hash,
        consent_snapshot_id=consent_snapshot_id,
        guest_id=guest_id,
        consent_scope=ConsentScope.EXTERNAL_MEASUREMENT,
        correlation_id=correlation_id,
    )

    # 9. Not logged => rejected/held (registry gate) or an internal ingest failure. Fail-closed, audited.
    if not result.logged:
        if result.validation.accepted:
            # accepted but not logged (e.g. a seam store-append failure, F1) — internal ingest failure.
            code, msg = "REJECTED", "event could not be ingested"
        else:
            # unknown or held (deregistered / missing-owner) — the SMK-001 backend layer (audit rõ in the seam).
            code, msg = "UNKNOWN_EVENT", "event is not an active registered event"
        audit.record("REJECT", "TRACK_REJECTED", event_code=event_code, detail=_corr(correlation_id))
        return TrackResult(status="REJECTED", correlation_id=correlation_id, error_code=code, message=msg)

    # 10. Accepted + logged => normalize into ads_measurement_event (Zone-A insert, UNIQUE dedup).
    key = result.idempotency_key
    web_row = deps.web_store.get(key) if key is not None else None
    log_id = web_row.log_id if web_row is not None else None
    mevent = normalize_to_measurement_event(
        event_code=event_code,
        idempotency_key=key,
        event_ts=event_ts,
        correlation_id=correlation_id,
        page_id=page_id,
        consent_snapshot_id=consent_snapshot_id,
        guest_id=guest_id,
        campaign_id=ad_hierarchy.get("campaign_id"),
        adset_id=ad_hierarchy.get("adset_id"),
        ad_id=ad_hierarchy.get("ad_id"),
        live_session_id=ad_hierarchy.get("live_session_id"),
    )
    try:
        inserted = deps.measurement_store.insert(mevent)
    except MeasurementStoreViolation:
        # Defense-in-depth: a store violation becomes a fail-closed REJECTED, never a raise out of the handler.
        audit.record("REJECT", "MEASUREMENT_STORE_VIOLATION", event_code=event_code, detail=_corr(correlation_id))
        return TrackResult(
            status="REJECTED", correlation_id=correlation_id, error_code="REJECTED",
            message="measurement store rejected the row",
        )

    replay = not inserted.created
    return TrackResult(
        status="DUPLICATE" if replay else "ACCEPTED",
        correlation_id=correlation_id,
        log_id=log_id,
        event_id=inserted.row.event_id,
        idempotent_replay=replay,
        data_quality_status=inserted.row.data_quality_status.value,
    )


# --- helpers ---------------------------------------------------------------------------------------
def _corr(correlation_id: str) -> str:
    """Build a PII-safe audit detail with the correlation_id MASKED on export (O1)."""
    return f"corr={mask(correlation_id)}"


def _reject(
    audit: AuditLog, correlation_id: str, error_code: str, message: str, field: Optional[str] = None
) -> TrackResult:
    """Emit a PII-safe rejection: static message, field NAME only, correlation_id masked in the audit (O1)."""
    detail = _corr(correlation_id) + (f" field={field}" if field else "")
    audit.record("REJECT", f"TRACK_{error_code}", detail=detail)
    return TrackResult(
        status="REJECTED", correlation_id=correlation_id, error_code=error_code, message=message, field=field,
    )


def _parse_event_ts(value: Any) -> Tuple[Optional[datetime], bool]:
    """Return (datetime, ok). ok is True only for a timezone-AWARE datetime (RULE-005 needs an unambiguous
    instant). A naive datetime, a bad string, or a non-datetime is (…, False)."""
    if isinstance(value, datetime):
        return value, value.tzinfo is not None
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None, False
        return dt, dt.tzinfo is not None
    return None, False


def _iter_strings(obj: Any) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, Mapping):
        for v in obj.values():
            yield from _iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _iter_strings(v)


def _contains_raw_pii(payload: Mapping[str, Any]) -> bool:
    """True if any string anywhere in the payload looks like raw PII (email / VN phone) — RULE-014 tripwire."""
    for s in _iter_strings(payload):
        if _EMAIL_RX.search(s) or _VN_PHONE_RX.search(s):
            return True
    return False


def _raw_event_hash(body: Mapping[str, Any]) -> str:
    """Deterministic server-side hash of the raw event body (RULE-H03: never a client-supplied hash).

    Excludes volatile / server fields (`idempotency_key`, `correlation_id`) so two identical replayed bodies
    hash the SAME -> identical RULE-005 key -> dedup (SMK-003). Key-sorted canonical JSON; datetimes via str.
    """
    volatile = {"idempotency_key", "correlation_id"}
    canon = {k: body[k] for k in sorted(body.keys()) if k not in volatile}
    blob = json.dumps(canon, sort_keys=True, default=str, ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
