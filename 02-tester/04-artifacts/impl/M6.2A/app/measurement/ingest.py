"""Ingest seam — orchestrates validate -> append log -> consent-eligibility (measure-only).

Design contract (Round 3): **STRICT CALLEE, FORGIVING SEAM.**
  The sub-functions stay strict — `normalize_ts()` rejects a naive datetime, `ConsentSnapshot` rejects a
  malformed scope/state, the store refuses UPDATE/DELETE. But at a MEASUREMENT seam a raised exception is
  NOT fail-closed, it is DATA LOSS: an exception escaping `ingest_event()` means no `IngestResult`, no log
  line, and — worst — NO audit record, silently breaking this seam's promise that every rejected/held event
  is audited, never lost. So `ingest_event()` WRAPS every call that touches external / untrusted data and
  turns each failure into an AUDITED DENY: it records a reject/hold with a specific reason and returns an
  `IngestResult` with `logged=False, egress_eligible=False`. `ingest_event()` itself never raises on
  hostile input (see `tests/test_round3_regressions.py` and `tests/test_round4_regressions.py`, the seam
  property tests). Round 4 extends this from hostile VALUES to hostile TYPES: a TYPE BOUNDARY at the head
  of the seam type-checks every channel-origin scalar and the consent value the reader/caller hands back,
  turning a wrong-typed input into an AUDITED DENY too (never a `str()`-coerced garbage row, never a raise).

Flow per ingress event:
  T. TYPE BOUNDARY (Round 4): type-check every channel-origin scalar before any callee runs. A required
     field (event_code/page_id/session_id/source/raw_event_hash) of a non-`str` type -> fail-closed REJECT
     (audited, early return); an optional field (guest_id/consent_snapshot_id/correlation_id) of the wrong
     type -> dropped to absent (audited). Never `str()`-coerced: coercing a list to "['x']" ingests garbage,
     the opposite of fail-closed. Closes the whole wrong-TYPE input class at the single seam entry.
  0. resolve identity (RULE-006) so the event's SUBJECT is known before consent is bound/judged.
  1. resolve the consent snapshot from the system of record (ConsentReader) and BIND it to the subject:
     only a reader-issued snapshot WHOSE `subject_ref` matches THIS event's subject is trusted. A reader
     failure, an unresolved handle, or a subject mismatch is fail-closed (audited, not egress-eligible) and
     its id is NEVER written to the append-only log (fixes MAJOR-2 + the subject-confusion FAIL-002).
  2. validate against event_registry (RULE-001). Unknown -> REJECT; de-registered / missing-owner -> HOLD.
     A rejected/held event is audited (RULE-001) — recorded, never silently lost — and gets no log row.
  3. for a valid event, append ONE append-only row to web_event_logs (RULE-007) with the locked idempotency
     key (RULE-005). A valid event whose `event_ts` cannot be normalized is audited (`TS_NOT_TZ_AWARE`) and
     NOT logged — a durable key cannot be formed, but the rejection is still recorded.
  4. evaluate consent eligibility (RULE-002) — this MARKS eligibility only; it never sends (external_send=
     OFF, no dispatcher in M6.2A). A malformed consent_state handed back by the reader cannot crash the seam.

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
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, DataSensitivity
from app.measurement.models.web_event_log import WebEventLog
from app.measurement.ports import ConsentReader
from app.measurement.registry.validator import EventDecision, EventValidator, ValidationResult


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
        consent_reader: ConsentReader,
        audit: AuditLog,
        resolver: Optional[IdentityResolver] = None,
    ) -> None:
        self._validator = validator
        self._store = store
        self._consent = consent_gate
        # Consent system of record: resolves a snapshot handle to the authoritative issued snapshot.
        # REQUIRED (Round 3): a consent reference can never be trusted without it. R2.3 made this Optional
        # "fail-closed anyway"; a probe showed that instead hollowed out the fail-closed guarantee and the
        # SMK-002 end-to-end leg (a wired-with-no-reader seam turned every consent into UNRESOLVED). Reversed.
        self._consent_reader = consent_reader
        # REQUIRED audit sink: the seam's OWN fail-closed decisions (bad ts, reader failure, subject
        # mismatch, unresolved / malformed consent) must be recorded. "Never silently lost" is the seam's
        # core promise and cannot depend on an optional argument.
        self._audit = audit
        # Identity resolver stays optional (attribution confidence only); when absent, consent can only be
        # subject-bound by a direct guest_id match (still fail-closed — never a customer-id upgrade).
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
        consent_snapshot_id: Optional[str] = None,
        consent_snapshot: Optional[ConsentSnapshot] = None,
        consent_scope: ConsentScope = ConsentScope.EXTERNAL_MEASUREMENT,
        guest_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        ingested_at: Optional[datetime] = None,
    ) -> IngestResult:
        notes: List[str] = []

        # T. TYPE BOUNDARY (Round 4). Channel-origin scalars are UNTRUSTED DATA of UNKNOWN TYPE: a JSON body
        #    can hand this seam a list / dict / number / None where a str is required. Enforce the seam's
        #    contract ("never raises on hostile input") HERE, once, before any callee runs — otherwise a
        #    non-str reaches `validator.validate` / `resolver.resolve` and raises straight out of the seam
        #    (0 audit = data loss), or is silently baked into the idempotency key as `str(list)` garbage.
        #    We never str()-coerce (that ingests garbage). Logic is centralized in `_require_str`.
        for _name, _value in (
            ("event_code", event_code),
            ("page_id", page_id),
            ("session_id", session_id),
            ("source", source),
            ("raw_event_hash", raw_event_hash),
        ):
            ok, _ = self._require_str(_name, _value, notes, optional=False)
            if not ok:
                # A required channel scalar of the wrong type is a hard fail-closed REJECT: audited (inside
                # _require_str), never logged, never egress-eligible, and the seam returns early — no raise.
                return self._field_type_reject(event_code, notes)
        # Optional str fields: wrong type -> dropped to ABSENT (audited), the bad value is never used.
        _, guest_id = self._require_str("guest_id", guest_id, notes, optional=True)
        _, consent_snapshot_id = self._require_str(
            "consent_snapshot_id", consent_snapshot_id, notes, optional=True
        )
        _, correlation_id = self._require_str("correlation_id", correlation_id, notes, optional=True)

        # 0. Identity first (RULE-006) so the event's subject is known before consent is bound/judged.
        identity: Optional[IdentityResolution] = None
        if self._resolver is not None and guest_id is not None:
            identity = self._resolver.resolve(guest_id)

        # 1. Consent provenance + subject binding (fail-closed; forgiving seam).
        #    The consent_snapshot_id written to the append-only log MUST be one the consent system of record
        #    ISSUED *and* whose subject matches THIS event's subject. A caller-supplied id/snapshot is an
        #    untrusted assertion. Every failure mode — reader error, unresolved id, or a snapshot about a
        #    different subject — denies egress, is audited, and never writes the id to the immutable log.
        handle_id: Optional[str] = consent_snapshot_id
        if handle_id is None and consent_snapshot is not None:
            # FIX 2b (Round 4): `consent_snapshot` is a caller-supplied OBJECT. Only a real ConsentSnapshot
            # (which passed __post_init__ hardening) exposes a trustworthy `.consent_snapshot_id`; a stray
            # object without that attribute would otherwise raise AttributeError straight out of the seam.
            # Wrong type -> treat as absent + audit, never raise.
            if isinstance(consent_snapshot, ConsentSnapshot):
                handle_id = consent_snapshot.consent_snapshot_id
            else:
                notes.append("CONSENT_SNAPSHOT_UNTRUSTED_TYPE")
                self._record("HOLD", "CONSENT_SNAPSHOT_UNTRUSTED_TYPE", event_code=event_code)
        resolved_snapshot: Optional[ConsentSnapshot] = None
        if handle_id is not None:
            try:
                resolved_snapshot = self._consent_reader.get(handle_id)
            except Exception:
                # The consent store is someone else's system; ANY way it can fail (DB unreachable, odd token
                # scope, ...) becomes a Module-6 DENY, never a Module-6 crash. Fixes the raise-escapes-seam
                # data-loss class at its most external edge.
                resolved_snapshot = None
                notes.append("CONSENT_READER_FAILED")
                self._record("HOLD", "CONSENT_READER_FAILED", event_code=event_code)
            else:
                if resolved_snapshot is None:
                    notes.append("CONSENT_SNAPSHOT_UNRESOLVED")
                    self._record("HOLD", "CONSENT_SNAPSHOT_UNRESOLVED", event_code=event_code)
                elif not isinstance(resolved_snapshot, ConsentSnapshot):
                    # FIX 2 (Round 4) — MAJOR-7, fail-OPEN. The consent reader is ANOTHER team's system; it
                    # may hand back a duck-typed object that never went through ConsentSnapshot.__post_init__,
                    # so its `consent_scope` could be a RAW STRING that fails OPEN on the gate's membership
                    # test ("external_measurement" IS a substring of "no_external_measurement_allowed"). Only
                    # a real, hardened ConsentSnapshot is trusted; anything else is fail-closed and its id is
                    # NEVER written to the append-only log. Checked BEFORE subject binding, so a duck-type can
                    # never reach the gate at all.
                    notes.append("CONSENT_SNAPSHOT_UNTRUSTED_TYPE")
                    self._record("HOLD", "CONSENT_SNAPSHOT_UNTRUSTED_TYPE", event_code=event_code)
                    resolved_snapshot = None
                elif not self._subject_bound(resolved_snapshot, guest_id):
                    # The snapshot exists but is about a DIFFERENT subject (or there is no subject to verify
                    # against): one person's consent must never authorize another's event. Drop it.
                    notes.append("CONSENT_SUBJECT_MISMATCH")
                    self._record(
                        "HOLD", "CONSENT_SUBJECT_MISMATCH",
                        subject=resolved_snapshot.subject_ref, event_code=event_code,
                    )
                    resolved_snapshot = None  # id is never written; consent is treated as absent

        # 2. Event validity (RULE-001).
        vr = self._validator.validate(event_code)

        # 3. Log only valid events. A valid event whose ts cannot be normalized is audited and NOT logged
        #    (the locked RULE-005 key needs a canonical ts) — audited, never silently lost.
        logged = False
        log_created = False
        key: Optional[str] = None
        if vr.accepted:
            normalized_ts: Optional[str] = None
            try:
                normalized_ts = normalize_ts(event_ts)
            except (ValueError, AttributeError, TypeError):
                # event_ts is channel-origin (a beacon may send "2026-07-29T12:00:00" with no offset, or a
                # str / None / number from a JSON body). Reject with a specific audited reason; do not raise.
                notes.append("TS_NOT_TZ_AWARE")
                self._record("REJECT", "TS_NOT_TZ_AWARE", event_code=event_code)
            if normalized_ts is not None:
                key = build_idempotency_key(
                    event_code, page_id, session_id, raw_event_hash, normalized_ts
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
                        resolved_snapshot.consent_snapshot_id if resolved_snapshot else None
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

        # 4. Consent eligibility (RULE-002). Evaluate for EVERY accepted event so the fail-closed consent
        #    decision is always made and audited (not short-circuited by the policy flag); MARK ONLY, never
        #    sends. A snapshot the reader handed back with a malformed consent_state cannot crash the seam.
        consent_ok = False
        if vr.accepted:
            try:
                consent_ok = self._consent.evaluate(resolved_snapshot, consent_scope)
            except (AttributeError, TypeError):
                consent_ok = False
                notes.append("CONSENT_STATE_MALFORMED")
                self._record("HOLD", "CONSENT_STATE_MALFORMED", event_code=event_code)
        egress_eligible = bool(vr.accepted and vr.external_send_permitted and consent_ok)
        if vr.accepted:
            if not vr.external_send_permitted:
                notes.append("EGRESS_FRAMEWORK_ONLY")   # external_send=OFF / policy not ratified (OD-003 OPEN)
            elif not consent_ok:
                notes.append("EGRESS_BLOCKED_CONSENT")    # policy would allow, but consent is fail-closed

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

    # --- helpers -----------------------------------------------------------------------------------
    def _subject_bound(self, snapshot: ConsentSnapshot, guest_id: Optional[str]) -> bool:
        """True only if `snapshot` is about THIS event's subject.

        The subject is `guest_id` (and, when trustedly mapped, its customer id via the resolver). With no
        `guest_id` there is nothing to verify against -> fail-closed (False). Raw ids are compared in memory
        only; they never enter a log or evidence.
        """
        if guest_id is None or snapshot.subject_ref is None:
            return False
        if snapshot.subject_ref == guest_id:
            return True
        if self._resolver is not None:
            return self._resolver.subject_matches(guest_id, snapshot.subject_ref)
        return False

    def _require_str(
        self, name: str, value: object, notes: List[str], *, optional: bool
    ) -> tuple[bool, Optional[str]]:
        """Type-check ONE channel-origin scalar at the seam boundary. Returns ``(ok, sanitized_value)``.

        * required (``optional=False``): a ``str`` -> ``(True, value)``; any other type (incl. ``None``) ->
          ``(False, None)`` plus an audited REJECT (``FIELD_TYPE_INVALID`` + the field name). The caller
          fail-closes and returns early.
        * optional (``optional=True``): ``None`` or a ``str`` -> ``(True, value)``; any other type ->
          ``(True, None)`` — i.e. treated as ABSENT — plus an audited HOLD. The caller proceeds without it.

        Never ``str()``-coerces: a list coerced to ``"['x']"`` is ingested GARBAGE, not fail-closed. The
        offending VALUE is never handed to the audit sink (it could be attacker-shaped or unhashable) — only
        the field NAME (our own controlled token) is recorded.
        """
        if isinstance(value, str) or (optional and value is None):
            return True, value
        action = "HOLD" if optional else "REJECT"
        notes.append("FIELD_TYPE_INVALID")
        self._record(action, "FIELD_TYPE_INVALID", detail=f"field={name}")
        # optional -> caller continues with an absent value (ok=True); required -> caller must fail-close.
        return optional, None

    def _field_type_reject(self, event_code: object, notes: List[str]) -> IngestResult:
        """Build the fail-closed ``IngestResult`` for a required channel scalar of the wrong type.

        The audit REJECT was already recorded by ``_require_str``. ``event_code`` may itself be the offending
        non-``str`` value, so it is surfaced only when it is genuinely a ``str`` (else ``""``) — a bad
        ``event_code`` never reaches the typed result fields or the audit sink.
        """
        safe_code = event_code if isinstance(event_code, str) else ""
        return IngestResult(
            event_code=safe_code,
            validation=ValidationResult(
                EventDecision.REJECT, safe_code, DataSensitivity.PII, False,
                reason="FIELD_TYPE_INVALID",
            ),
            logged=False,
            log_created=False,
            idempotency_key=None,
            egress_eligible=False,
            identity=None,
            notes=notes,
        )

    def _record(self, action: str, reason: str, **kw) -> None:
        """Record one of the seam's OWN fail-closed decisions. Guarded so a mis-wired seam (audit=None)
        degrades to over-denial without raising — the audit sink is REQUIRED, this is belt-and-suspenders."""
        if self._audit is not None:
            self._audit.record(action, reason, **kw)
