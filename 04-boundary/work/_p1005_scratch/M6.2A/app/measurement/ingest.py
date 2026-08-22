"""Ingest seam — orchestrates validate -> append log -> consent-eligibility (measure-only).

Flow per ingress event:
  1. validate against event_registry (RULE-001). Unknown -> REJECT; de-registered / missing-owner -> HOLD.
     A rejected/held event is NOT written to web_event_logs (its event_code would not resolve) but the reject/
     hold IS audited (RULE-001) — never silently lost.
  2. for a valid event, append ONE append-only row to web_event_logs (RULE-007) with the locked idempotency key
     (RULE-005). A valid event whose consent is missing is still logged internally (durable), egress just blocked.
  3. evaluate consent eligibility (RULE-002) — this MARKS eligibility only; it never sends (external_send=OFF,
     no dispatcher in M6.2A).
  4. optionally resolve identity (RULE-006) for attribution confidence.

This is the seam the M6.2B HTTP endpoint (POST /api/ads/events/track) will later call. It performs no egress,
no scaling, no publishing, and flips no flag.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.identity.resolver import IdentityResolution, IdentityResolver
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot
from app.measurement.models.web_event_log import WebEventLog
from app.measurement.registry.validator import EventValidator, ValidationResult


@dataclass(frozen=True)
class IngestResult:
    event_code: str
    validation: ValidationResult
    logged: bool
    log_created: bool                       # False when deduped (RULE-005)
    idempotency_key: Optional[str]
    egress_eligible: bool                   # eligibility only — NEVER a send
    identity: Optional[IdentityResolution]
    notes: List[str] = field(default_factory=list)


class IngestService:
    def __init__(
        self,
        validator: EventValidator,
        store: WebEventLogStore,
        consent_gate: ConsentGate,
        resolver: Optional[IdentityResolver] = None,
    ) -> None:
        self._validator = validator
        self._store = store
        self._consent = consent_gate
        self._resolver = resolver

    def ingest_event(
        self,
        *,
        event_code: str,
        page_id: str,
        session_id: str,
        source: str,
        event_ts: datetime,
        raw_event_hash: str,
        consent_snapshot: Optional[ConsentSnapshot] = None,
        consent_scope: ConsentScope = ConsentScope.EXTERNAL_MEASUREMENT,
        guest_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        ingested_at: Optional[datetime] = None,
    ) -> IngestResult:
        notes: List[str] = []

        # 1. Event validity (RULE-001).
        vr = self._validator.validate(event_code)

        # 2. Log only valid events (event_code must resolve in the registry). Rejected/held events are audited
        #    inside the validator — recorded, never silently lost — but do not get a web_event_logs row.
        logged = False
        log_created = False
        key: Optional[str] = None
        if vr.accepted:
            key = build_idempotency_key(
                event_code, page_id, session_id, raw_event_hash, normalize_ts(event_ts)
            )
            row = WebEventLog(
                log_id=f"log_{key[:16]}",
                event_code=event_code,
                page_id=page_id,
                session_id=session_id,
                source=source,
                event_ts=event_ts,
                idempotency_key=key,
                ingested_at=ingested_at or datetime.now(timezone.utc),
                consent_snapshot_id=(
                    consent_snapshot.consent_snapshot_id if consent_snapshot else None
                ),
                correlation_id=correlation_id,
            )
            result = self._store.append(row)
            logged = True
            log_created = result.created
            if not result.created:
                notes.append("DEDUP_NO_DOUBLE_LOG")
        else:
            notes.append(f"NOT_LOGGED_{vr.decision.value}")

        # 3. Consent eligibility (RULE-002). Evaluate for EVERY accepted event so the fail-closed consent
        #    decision is always made and audited (not short-circuited by the policy flag); MARK ONLY, never
        #    sends. Egress additionally requires a ratified send policy, which stays framework-only while
        #    M6-OD-003 is OPEN (external_send=OFF).
        consent_ok = self._consent.evaluate(consent_snapshot, consent_scope) if vr.accepted else False
        egress_eligible = bool(vr.accepted and vr.external_send_permitted and consent_ok)
        if not vr.external_send_permitted:
            notes.append("EGRESS_FRAMEWORK_ONLY")   # external_send=OFF / policy not ratified (M6-OD-003 OPEN)
        elif not consent_ok:
            notes.append("EGRESS_BLOCKED_CONSENT")   # policy would allow, but consent is fail-closed

        # 4. Identity resolution (RULE-006), optional.
        identity: Optional[IdentityResolution] = None
        if self._resolver is not None and guest_id is not None:
            identity = self._resolver.resolve(guest_id)

        return IngestResult(
            event_code=event_code,
            validation=vr,
            logged=logged,
            log_created=log_created,
            idempotency_key=key,
            egress_eligible=egress_eligible,
            identity=identity,
            notes=notes,
        )
