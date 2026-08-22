"""RULE-006 guest -> customer identity resolution (read-only, audited).

The identity chain guest -> customer must be mapped WITH audit and is never overwritten without evidence.
Module 6 only READS guest_contacts; it has no write/overwrite path (so it structurally cannot overwrite a
mapping). A mapping presented without `mapping_audit_ref` is NOT trusted (HOLD). A missing/ambiguous mapping
yields LOW/HOLD confidence — never a guessed merge (RULE-009). Exit-gate leg L3.

All identity values are masked before entering the audit trail (RULE-014 / H02).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.measurement.audit import AuditLog
from app.measurement.masking import mask
from app.measurement.ports import CustomerRefReader, GuestContactReader


class Confidence(str, Enum):
    OK = "OK"        # guest mapped to an existing customer, with audit
    LOW = "LOW"      # guest known but not yet mapped (guest-only)
    HOLD = "HOLD"    # cannot be trusted (unknown guest / mapping without audit / mapped customer missing)


@dataclass(frozen=True)
class IdentityResolution:
    guest_id_masked: str
    confidence: Confidence
    mapped_customer_id_masked: Optional[str] = None
    reason: Optional[str] = None


class IdentityResolver:
    def __init__(
        self,
        contacts: GuestContactReader,
        customers: CustomerRefReader,
        audit: AuditLog,
    ) -> None:
        self._contacts = contacts
        self._customers = customers
        self._audit = audit

    def resolve(self, guest_id: str) -> IdentityResolution:
        gid_masked = mask(guest_id) or "***"
        gc = self._contacts.get(guest_id)

        # Unknown guest -> HOLD.
        if gc is None:
            self._audit.record("IDENTITY_RESOLVE", "GUEST_NOT_FOUND", subject=guest_id)
            return IdentityResolution(gid_masked, Confidence.HOLD, None, "GUEST_NOT_FOUND")

        # Known guest, not yet mapped -> LOW (guest-only; never guess a customer).
        if gc.mapped_customer_id is None:
            self._audit.record("IDENTITY_RESOLVE", "NO_CUSTOMER_MAPPING", subject=guest_id)
            return IdentityResolution(gid_masked, Confidence.LOW, None, "NO_CUSTOMER_MAPPING")

        # Mapping present but without audit -> NOT trusted (RULE-006) -> HOLD.
        if not gc.mapping_audit_ref:
            self._audit.record(
                "IDENTITY_RESOLVE", "MAPPING_WITHOUT_AUDIT", subject=guest_id
            )
            return IdentityResolution(
                gid_masked, Confidence.HOLD, mask(gc.mapped_customer_id), "MAPPING_WITHOUT_AUDIT"
            )

        # Mapped customer must actually exist -> else HOLD.
        if not self._customers.exists(gc.mapped_customer_id):
            self._audit.record(
                "IDENTITY_RESOLVE", "MAPPED_CUSTOMER_MISSING", subject=guest_id
            )
            return IdentityResolution(
                gid_masked, Confidence.HOLD, mask(gc.mapped_customer_id), "MAPPED_CUSTOMER_MISSING"
            )

        # Trusted mapping, with audit.
        self._audit.record(
            "IDENTITY_RESOLVE", "MAPPED_WITH_AUDIT", subject=guest_id,
            detail=f"audit_ref={mask(gc.mapping_audit_ref)}",
        )
        return IdentityResolution(
            gid_masked, Confidence.OK, mask(gc.mapped_customer_id), "MAPPED_WITH_AUDIT"
        )
