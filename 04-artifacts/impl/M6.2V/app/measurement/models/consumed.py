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


class ExternalSendPolicy(str, Enum):
    """M6-CTR-003 external_send_policy — the owner-signed 4-value enum (M6-OD-003 vocabulary half, QĐ-1 2026-09-07,
    chief-confirmed). Fail-closed: a None / blank / unknown registry token coerces to BLOCKED_DEFAULT (see
    `registry.validator._resolve_send_policy`), and `permits_external_send()` returns True ONLY for ALLOW_EXTERNAL.
    NO event is classified ALLOW_EXTERNAL by Module 6 — the permit-mapping (which events/fields are ALLOW_EXTERNAL)
    is the OPEN M6-OD-003 privacy/legal half (owner/Sếp); and even ALLOW_EXTERNAL opens no real egress while
    EXTERNAL_SEND stays Final OFF (defense-in-depth). M6 adopts this owner-signed vocabulary; it invents none
    (RULE-018)."""
    ALLOW_EXTERNAL = "ALLOW_EXTERNAL"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    BLOCKED_PII = "BLOCKED_PII"
    BLOCKED_DEFAULT = "BLOCKED_DEFAULT"


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
    defaults (MISSING external_send_policy => BLOCKED_DEFAULT; MISSING data_sensitivity => PII).
    `external_send_policy` is the owner-signed `ExternalSendPolicy` enum (M6-OD-003 vocabulary half, QĐ-1); the
    registry SOURCE may still hand a raw token, so `registry.validator._resolve_send_policy` coerces it fail-closed
    (mirroring `_resolve_sensitivity`) — an unratified/unknown token is NEVER treated as "allow".
    """
    event_code: str
    registration_state: RegistrationState
    owner: Optional[str] = None
    channel: Optional[str] = None
    data_sensitivity: Optional[DataSensitivity] = None
    external_send_policy: Optional[ExternalSendPolicy] = None   # owner-signed enum; coerced fail-closed -> BLOCKED_DEFAULT
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

    `consent_scope` is coerced to an immutable ``frozenset[ConsentScope]`` in ``__post_init__`` (see below).
    """
    consent_snapshot_id: str
    subject_ref: str                                # PII (guest_id/customer_id whose consent this is)
    consent_state: ConsentState
    captured_at: datetime
    consent_scope: FrozenSet[ConsentScope] = field(default_factory=frozenset)
    source_channel: Optional[str] = None

    def __post_init__(self) -> None:
        """Coerce `consent_scope` to an immutable frozenset of ConsentScope members (fail-closed).

        This closes two consent fail-open holes found by running the Round 1 code (M6-P1005/M6-P1006):

        * MAJOR-1 — a RAW STRING scope (e.g. "no_external_measurement_allowed") must be REJECTED, never
          accepted. ``ConsentScope`` subclasses ``str``, so a membership test `scope in <str>` degrades to
          a SUBSTRING match — a string that literally says "not allowed" would test as granted. A bare
          string (or a non-ConsentScope element) is therefore refused at construction.
        * MAJOR-3 — a caller-owned MUTABLE set is COPIED into a frozenset, so a later ``.add()`` on the
          caller's original set can no longer retroactively grant a scope on an already-built snapshot.

        `consent_state` is ALSO enforced here (Round 3). The earlier "already fail-closed, do not coerce"
        note was disproved by probe: a raw ``"VALID"`` string is indeed denied by the gate's ``is`` check,
        but a raw ``"MISSING"``/``"EXPIRED"`` or ``None`` sails through construction and then explodes the
        gate's DENY audit at ``consent_state.value.upper()`` (``AttributeError``). So a snapshot must carry a
        real ``ConsentState`` member — same discipline as ``consent_scope`` — refused at construction.
        """
        scope = self.consent_scope
        if isinstance(scope, (str, bytes)):
            raise TypeError(
                "consent_scope must be an iterable of ConsentScope members, not a raw string "
                "(a bare string fails open on membership checks)"
            )
        try:
            members = frozenset(scope)
        except TypeError as exc:  # not iterable
            raise TypeError("consent_scope must be an iterable of ConsentScope members") from exc
        for member in members:
            if not isinstance(member, ConsentScope):
                raise TypeError(
                    f"consent_scope element {member!r} is not a ConsentScope member"
                )
        # frozen dataclass: reassign the normalized, immutable value via object.__setattr__.
        object.__setattr__(self, "consent_scope", members)

        # consent_state must be a real ConsentState member (never a raw string / None) so no downstream
        # `.value.upper()` can raise. Fail-closed at construction, exactly like consent_scope.
        if not isinstance(self.consent_state, ConsentState):
            raise TypeError(
                f"consent_state {self.consent_state!r} must be a ConsentState member, not a raw value"
            )


# PII field names per model — consulted by masking/audit so no raw identity value reaches a log or evidence.
PII_FIELDS = {
    "EventRegistryRow": (),
    "GuestContact": ("guest_id", "contact_fingerprint", "mapped_customer_id"),
    "ConsentSnapshot": ("subject_ref",),
}
