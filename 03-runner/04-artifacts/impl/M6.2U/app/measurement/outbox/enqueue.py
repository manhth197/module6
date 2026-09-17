"""Runtime-side ENQUEUE seam (M6.2C) — writes outbox rows ONLY; holds NO Transport (RULE-004).

`enqueue_measurement` fans one conversion out to one QUEUED outbox row per platform (OFFLINE only for
ORDER_VERIFIED, doc 12 L250), keyed by the LOCKED RULE-005 dedup_key (UNIQUE => no double send). `enqueue_audience_sync`
walks an APPROVED segment's members and enqueues ADD (consented) / REMOVE (opt-out) rows — never from an ad-hoc
query / data mart (RULE-012), never a trigger owner. Dedup keys are HASHED so no raw PII sits in the key; the
row's identity refs are masked on every export (O1, RULE-014/H02). Nothing here sends externally.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from app.measurement.masking import mask
from app.measurement.models.audience_outbox import (
    AudienceOperation,
    AudienceOutboxItem,
    AudiencePlatform,
)
from app.measurement.models.consumed import ConsentScope
from app.measurement.models.conversion_event import ConversionEvent
from app.measurement.models.measurement_outbox import MeasurementOutboxItem, MeasurementPlatform
from app.measurement.models.segments import ApprovalState
from app.measurement.outbox.transport import safe_subject_ref

_DELIM = "|"
_MEASUREMENT_PLATFORMS: Tuple[MeasurementPlatform, ...] = (
    MeasurementPlatform.PIXEL,
    MeasurementPlatform.CAPI,
    MeasurementPlatform.OFFLINE,
)
_ORDER_VERIFIED = "ORDER_VERIFIED"


def _hash_key(*parts: Any) -> str:
    """Injective, PII-safe serialization of dedup-key components: escape, join, sha256. Because a component
    (customer_or_guest_key / member_key) is identity-derived, HASHING keeps raw PII out of the stored key while
    preserving uniqueness. The component set/order is the LOCKED formula — only the serialization is hashed."""
    canonical = _DELIM.join(
        "\\0" if p is None else str(p).replace("\\", "\\\\").replace(_DELIM, "\\" + _DELIM) for p in parts
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def event_ts_bucket(occurred_at: datetime) -> str:
    """RULE-005 `event_ts_bucket` — the conversion time bucketed to the UTC hour (the dedup window; the
    granularity is operational config, not an owner value). Requires a tz-aware datetime (caller ensures)."""
    u = occurred_at.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return u.isoformat()


def measurement_dedup_key(
    platform: str, event_code: str, customer_or_guest_key: str, ts_bucket: str, source_event_id: str
) -> str:
    """LOCKED RULE-005: platform + event_code + customer_or_guest_key + event_ts_bucket + source_event_id."""
    return _hash_key(platform, event_code, customer_or_guest_key, ts_bucket, source_event_id)


def audience_dedup_key(segment_id: str, member_key: str, platform: str, operation: str) -> str:
    """AUDIENCE dedup (distinct from RULE-005): segment_id + member_key + platform + operation."""
    return _hash_key(segment_id, member_key, platform, operation)


def enqueue_measurement(
    conversion: ConversionEvent,
    store: Any,
    *,
    max_retries: int,
    platforms: Optional[Tuple[MeasurementPlatform, ...]] = None,
    now: Optional[datetime] = None,
) -> List[Tuple[MeasurementOutboxItem, bool]]:
    """Fan one conversion out to the measurement outbox — one QUEUED row per platform, UNIQUE dedup_key.
    OFFLINE is enqueued ONLY for an ORDER_VERIFIED conversion (doc 12 L250). Returns (row, created) per platform.
    Runtime-side: writes rows only, sends nothing (RULE-004)."""
    now = now or datetime.now(timezone.utc)
    platforms = platforms or _MEASUREMENT_PLATFORMS
    bucket = event_ts_bucket(conversion.occurred_at)
    out: List[Tuple[MeasurementOutboxItem, bool]] = []
    for platform in platforms:
        if platform is MeasurementPlatform.OFFLINE and conversion.event_code != _ORDER_VERIFIED:
            continue  # Offline only after ORDER_VERIFIED (fail-closed; never quote/draft as purchase)
        dk = measurement_dedup_key(
            platform.value, conversion.event_code, conversion.customer_or_guest_key, bucket,
            conversion.source_event_id,
        )
        item = MeasurementOutboxItem(
            outbox_id="mob_" + dk[:24],
            source_event_id=conversion.conversion_id,
            platform=platform,
            dedup_key=dk,
            idempotency_key=conversion.idempotency_key,
            payload_ref=f"conversion:{conversion.conversion_id}",   # PII-safe; hashed payload built at dispatch (M6.2D)
            consent_snapshot_id=conversion.consent_snapshot_id,
            max_retries=max_retries,
            created_at=now,
        )
        out.append(store.enqueue(item))
    return out


def enqueue_audience_sync(
    segment_id: str,
    *,
    reader: Any,
    consent_reader: Any,
    consent_gate: Any,
    store: Any,
    audit: Any,
    platform: AudiencePlatform,
    max_retries: int,
    now: Optional[datetime] = None,
) -> List[Tuple[AudienceOutboxItem, bool]]:
    """Enqueue audience-sync rows for an APPROVED segment. Fail-closed: a non-APPROVED segment enqueues nothing
    (audited). Per member: consent VALID (via the hardened gate) => ADD; opt-out/expired/absent => REMOVE. Reads
    membership for SYNC ONLY — triggers nothing (RULE-012). member_key is masked on every export (O1)."""
    now = now or datetime.now(timezone.utc)
    seg = reader.get_segment(segment_id)
    if seg is None or seg.approval_state is not ApprovalState.APPROVED:
        audit.record("HOLD", "AUDIENCE_SEGMENT_NOT_APPROVED", detail=f"segment={segment_id}")
        return []
    out: List[Tuple[AudienceOutboxItem, bool]] = []
    for member in reader.members(segment_id):
        snap = None
        try:
            snap = consent_reader.get(member.consent_snapshot_id)
        except Exception:
            snap = None
        # F-C (M6.2D): BIND consent to THIS member. A snapshot whose subject_ref is not this member's key is
        # BORROWED consent (member A synced under member B's valid consent) — only the member's OWN valid
        # consent yields ADD; a mismatch/absence/opt-out is fail-closed => REMOVE.
        # FF-2 (M6.2E Round 2): read subject via safe_subject_ref (plain str or None) so a hostile str-subclass
        # __eq__ / raising __class__ / raising property can never crash the enqueue (fail-closed, no crash).
        member_subject = safe_subject_ref(snap)
        eligible = (
            snap is not None
            and member_subject is not None
            and member_subject == member.member_key
            and consent_gate.evaluate(snap, ConsentScope.AUDIENCE_SYNC)
        )
        operation = AudienceOperation.ADD if eligible else AudienceOperation.REMOVE
        dk = audience_dedup_key(segment_id, member.member_key, platform.value, operation.value)
        item = AudienceOutboxItem(
            outbox_id="aob_" + dk[:24],
            segment_id=segment_id,
            member_key=member.member_key,          # identity ref; masked on export, hashed payload at dispatch
            platform=platform,
            operation=operation,
            dedup_key=dk,
            payload_ref=f"segment:{segment_id}",    # PII-safe reference
            consent_snapshot_id=member.consent_snapshot_id,
            max_retries=max_retries,
            created_at=now,
        )
        out.append(store.enqueue(item))
        audit.record(
            "IDENTITY_RESOLVE", "AUDIENCE_ENQUEUE",
            subject=member.member_key, detail=f"segment={segment_id};op={operation.value}",
        )
    return out
