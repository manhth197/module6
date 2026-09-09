"""RULE-001 event-registry validation path (fail-closed).

Every event must exist in event_registry (ACTIVE, with an owner) before it may be logged for measurement or
considered for egress. Unknown events are REJECTed; registered-but-unusable events (de-registered / missing
owner) are HELD; both are audited. Module 6 never inserts or invents an event code (RULE-001 / RULE-018).

Prevents M6-FAIL-003 (event drift). Backs smoke M6-SMK-001. Exit-gate leg L1.

Entry-gap-driven fail-closed defaults (ENTRY-003 risk-acceptance, see PLAN.md §9):
  * MISSING/unknown external_send_policy  -> egress BLOCKED (M6-OD-003 OPEN: no token is "allow")
  * MISSING data_sensitivity              -> treat as PII (mask)
  * registration_state not ACTIVE / stale -> HOLD (never false-ALLOW)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.measurement.audit import AuditLog
from app.measurement.models.consumed import (
    DataSensitivity,
    EventRegistryRow,
    ExternalSendPolicy,
    RegistrationState,
)
from app.measurement.ports import EventRegistryReader


class EventDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"      # unknown event — not in registry
    HOLD = "HOLD"          # registered but not usable (de-registered / missing owner)


@dataclass(frozen=True)
class ValidationResult:
    decision: EventDecision
    event_code: str
    data_sensitivity: DataSensitivity          # resolved (MISSING -> PII)
    external_send_permitted: bool              # resolved fail-closed (MISSING/unknown -> False)
    reason: Optional[str] = None

    @property
    def accepted(self) -> bool:
        return self.decision is EventDecision.ACCEPT


def _resolve_sensitivity(raw: object) -> DataSensitivity:
    """Fail-closed normalization of `data_sensitivity`.

    ENTRY-003 default is "MISSING => PII", but a raw string coming from the registry (someone else's data)
    is truthy and would slip through a bare ``row.data_sensitivity or PII`` unchecked — defeating the
    default. Coerce explicitly: a real enum/value maps to its member; MISSING (None) or an unknown/raw
    token maps to the MOST-RESTRICTIVE PII. Never trusts an unrecognized token as less sensitive.
    """
    if isinstance(raw, DataSensitivity):
        return raw
    if raw is None:
        return DataSensitivity.PII
    try:
        return DataSensitivity(raw)
    except (ValueError, TypeError):
        return DataSensitivity.PII


def _resolve_send_policy(raw: object) -> ExternalSendPolicy:
    """Fail-closed normalization of `external_send_policy` (M6.2P; mirrors `_resolve_sensitivity`).

    The owner-signed enum (M6-OD-003 vocabulary half, QĐ-1) is now real, but the registry SOURCE (someone else's
    data, M3) may hand a None / blank / unknown / raw token — which must NEVER be trusted as "allow". Coerce
    explicitly: a real `ExternalSendPolicy` maps to its member; a valid token string maps to its member; None /
    blank / an unrecognized token / any non-coercible value maps to the MOST-RESTRICTIVE `BLOCKED_DEFAULT` (never
    crashes, never auto-allows). Whitespace is treated as blank.
    """
    if isinstance(raw, ExternalSendPolicy):
        return raw
    if raw is None:
        return ExternalSendPolicy.BLOCKED_DEFAULT
    if isinstance(raw, str) and not raw.strip():
        return ExternalSendPolicy.BLOCKED_DEFAULT
    try:
        return ExternalSendPolicy(raw)
    except (ValueError, TypeError):
        return ExternalSendPolicy.BLOCKED_DEFAULT


def permits_external_send(policy: ExternalSendPolicy) -> bool:
    """Typed, fail-closed egress-policy gate (M6.2P). Returns True ONLY for `ExternalSendPolicy.ALLOW_EXTERNAL`;
    False for INTERNAL_ONLY / BLOCKED_PII / BLOCKED_DEFAULT and for every fail-closed coerced default.

    NO event is classified ALLOW_EXTERNAL by Module 6 (the permit-mapping is the OPEN M6-OD-003 privacy/legal half,
    owner/Sếp), so every real ACCEPTED event resolves to False; and even an ALLOW_EXTERNAL row opens no real egress
    because `config.EXTERNAL_SEND` is Final "OFF" (independent defense-in-depth). Callers pass the COERCED policy
    (see `_resolve_send_policy`), never a raw token.
    """
    return policy is ExternalSendPolicy.ALLOW_EXTERNAL


class EventValidator:
    def __init__(self, registry: EventRegistryReader, audit: AuditLog) -> None:
        self._registry = registry
        self._audit = audit

    def validate(self, event_code: str) -> ValidationResult:
        row: Optional[EventRegistryRow] = self._registry.get(event_code)

        # Unknown event -> REJECT + audit (RULE-001, SMK-001, prevents FAIL-003).
        if row is None:
            self._audit.record(
                "REJECT", "UNKNOWN_EVENT_NOT_IN_REGISTRY", event_code=event_code
            )
            return ValidationResult(
                EventDecision.REJECT, event_code, DataSensitivity.PII, False,
                reason="UNKNOWN_EVENT_NOT_IN_REGISTRY",
            )

        # Registered but de-registered / stale -> HOLD (fail-closed; never false-ALLOW).
        if row.registration_state is not RegistrationState.ACTIVE:
            self._audit.record(
                "HOLD", "REGISTRATION_STATE_NOT_ACTIVE", event_code=event_code,
                detail=str(row.registration_state),
            )
            return ValidationResult(
                EventDecision.HOLD, event_code, DataSensitivity.PII, False,
                reason="REGISTRATION_STATE_NOT_ACTIVE",
            )

        # Missing owner -> DQ item 1 FAIL -> HOLD (fail-closed). A whitespace-only owner is NOT an owner:
        # `.strip()` so "   " is treated as missing, not silently ACCEPTed.
        if not row.owner or not str(row.owner).strip():
            self._audit.record("HOLD", "MISSING_OWNER", event_code=event_code)
            return ValidationResult(
                EventDecision.HOLD, event_code, DataSensitivity.PII, False,
                reason="MISSING_OWNER",
            )

        # Accepted. Resolve fail-closed defaults for the downstream (masking + egress gate).
        sensitivity = _resolve_sensitivity(row.data_sensitivity)
        send_permitted = permits_external_send(_resolve_send_policy(row.external_send_policy))
        return ValidationResult(
            EventDecision.ACCEPT, event_code, sensitivity, send_permitted, reason=None
        )
