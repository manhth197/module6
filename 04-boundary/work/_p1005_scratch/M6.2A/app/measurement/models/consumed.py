"""CONSUMED read-models — the row shapes Module 6 READS but never writes.

- M6-CTR-003 event_registry            (owner: Core Event Governance)
- M6-CTR-005 guest_contacts            (owner: Customer identity)
- M6-CTR-006 guest_marketing_consent_snapshot (owner: Consent system)

Module 6 defines only the minimum shape it reads (contracts in 00-spec/contracts/). It never inserts, updates,
or invents any of these rows (RULE-018 Core owner wins). Identity fields are PII-class: mask / secret_ref before
they enter any log or evidence (RULE-014 / H02) — see app.measurement.masking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import FrozenSet, Optional


# --- enums -----------------------------------------------------------------------------------------
class RegistrationState(str, Enum):
    """M6-CTR-003 addition (fail-closed de-registration). On any doubt, treat as NOT active."""
    ACTIVE = "ACTIVE"
    DEREGISTERED = "DEREGISTERED"


class DataSensitivity(str, Enum):
    """M6-CTR-003 data_sensitivity. Values are Core policy's; PACK candidates only. MISSING => treat as PII."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PII = "PII"


class ConsentState(str, Enum):
    """M6-CTR-006 consent_state — doc-sourced vocabulary (§15 L302). Only VALID permits egress."""
    VALID = "VALID"
    MISSING = "MISSING"
    EXPIRED = "EXPIRED"
    OPT_OUT = "OPT_OUT"


class ConsentScope(str, Enum):
    """The three egress kinds consent gates (§7 L118)."""
    EXTERNAL_MEASUREMENT = "external_measurement"
    AUDIENCE_SYNC = "audience_sync"
    CRM = "crm"


# --- M6-CTR-003 event_registry (CONSUMED) ----------------------------------------------------------
@dataclass(frozen=True)
class EventRegistryRow:
    """One valid event's governance metadata (read-only lookup row).

    `owner`, `channel`, `data_sensitivity`, `external_send_policy` are the doc-named fields (§13 L263).
    Any of them may be absent per the ENTRY-003 owner risk-acceptance — the validator applies fail-closed
    defaults (MISSING external_send_policy => BLOCKED; MISSING data_sensitivity => PII). `external_send_policy`
    is kept as a raw token because its values are M6-OD-003 (OPEN); the validator never treats an unratified
    token as "allow".
    """
    event_code: str
    registration_state: RegistrationState
    owner: Optional[str] = None
    channel: Optional[str] = None
    data_sensitivity: Optional[DataSensitivity] = None
    external_send_policy: Optional[str] = None      # M6-OD-003 OPEN — raw token; never auto-"allow"
    schema_ref: Optional[str] = None


# --- M6-CTR-005 guest_contacts (CONSUMED) ----------------------------------------------------------
@dataclass(frozen=True)
class GuestContact:
    """Guest identity + the guest->customer mapping M6 reads for attribution (RULE-006).

    A trusted mapping requires BOTH `mapped_customer_id` and `mapping_audit_ref` (mapping must carry audit and is
    never overwritten without evidence). `guest_id`, `contact_fingerprint`, `mapped_customer_id` are PII-class.
    """
    guest_id: str                                   # PII
    contact_fingerprint: str                        # PII (still identity-class though hashed)
    mapped_customer_id: Optional[str] = None        # PII; present only when mapped
    mapping_audit_ref: Optional[str] = None         # required whenever mapped_customer_id is present (RULE-006)
    first_seen_at: Optional[datetime] = None


# --- M6-CTR-006 guest_marketing_consent_snapshot (CONSUMED) ----------------------------------------
@dataclass(frozen=True)
class ConsentSnapshot:
    """Point-in-time consent recorded AT EVENT TIME. Send-time re-validation is the dispatcher's job (out of
    scope in M6.2A). `subject_ref` is PII-class.
    """
    consent_snapshot_id: str
    subject_ref: str                                # PII (guest_id/customer_id whose consent this is)
    consent_state: ConsentState
    captured_at: datetime
    consent_scope: FrozenSet[ConsentScope] = field(default_factory=frozenset)
    source_channel: Optional[str] = None


# PII field names per model — consulted by masking/audit so no raw identity value reaches a log or evidence.
PII_FIELDS = {
    "EventRegistryRow": (),
    "GuestContact": ("guest_id", "contact_fingerprint", "mapped_customer_id"),
    "ConsentSnapshot": ("subject_ref",),
}
