"""Test fixtures for slice M6.2A.

In-memory adapters are TEST DOUBLES for the CONSUMED tables (event_registry, guest_contacts,
guest_marketing_consent_snapshot, customers) that Core / Customer identity / the Consent system own. Seed values
are synthetic (never real customer PII); masking still applies wherever they would reach a log or evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional, Set

import pytest

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.identity.resolver import IdentityResolver
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.models.consumed import (
    ConsentScope,
    ConsentSnapshot,
    ConsentState,
    DataSensitivity,
    EventRegistryRow,
    GuestContact,
    RegistrationState,
)
from app.measurement.registry.validator import EventValidator

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- in-memory read-only adapters (test doubles) ---------------------------------------------------
class InMemoryEventRegistry:
    def __init__(self, rows: Dict[str, EventRegistryRow]) -> None:
        self._rows = rows

    def get(self, event_code: str) -> Optional[EventRegistryRow]:
        return self._rows.get(event_code)


class InMemoryGuestContacts:
    def __init__(self, rows: Dict[str, GuestContact]) -> None:
        self._rows = rows

    def get(self, guest_id: str) -> Optional[GuestContact]:
        return self._rows.get(guest_id)


class InMemoryConsent:
    def __init__(self, rows: Dict[str, ConsentSnapshot], current: Dict[str, ConsentState]) -> None:
        self._rows = rows
        self._current = current

    def get(self, consent_snapshot_id: str) -> Optional[ConsentSnapshot]:
        return self._rows.get(consent_snapshot_id)

    def current_state(self, subject_ref: str) -> ConsentState:
        return self._current.get(subject_ref, ConsentState.MISSING)  # unknown => fail-closed


class InMemoryCustomers:
    def __init__(self, ids: Set[str]) -> None:
        self._ids = ids

    def exists(self, customer_id: str) -> bool:
        return customer_id in self._ids


# --- seed data -------------------------------------------------------------------------------------
@pytest.fixture
def registry_rows() -> Dict[str, EventRegistryRow]:
    return {
        "VIEW_LANDING": EventRegistryRow(
            event_code="VIEW_LANDING",
            registration_state=RegistrationState.ACTIVE,
            owner="core.tracking",
            channel="web",
            data_sensitivity=DataSensitivity.INTERNAL,
            external_send_policy=None,          # M6-OD-003 OPEN
            schema_ref="evt.view_landing.v1",
        ),
        # ACTIVE with data_sensitivity MISSING -> validator must default to PII.
        "VIEW_LANDING_NO_SENS": EventRegistryRow(
            event_code="VIEW_LANDING_NO_SENS",
            registration_state=RegistrationState.ACTIVE,
            owner="core.tracking",
            channel="web",
            data_sensitivity=None,
        ),
        # De-registered -> HOLD (fail-closed, never false-ALLOW).
        "DEREG_SAMPLE": EventRegistryRow(
            event_code="DEREG_SAMPLE",
            registration_state=RegistrationState.DEREGISTERED,
            owner="core.tracking",
        ),
        # Registered ACTIVE but owner missing -> DQ item 1 FAIL -> HOLD.
        "NO_OWNER_SAMPLE": EventRegistryRow(
            event_code="NO_OWNER_SAMPLE",
            registration_state=RegistrationState.ACTIVE,
            owner=None,
        ),
    }


@pytest.fixture
def guest_rows() -> Dict[str, GuestContact]:
    return {
        "guest_mapped_ok": GuestContact(
            guest_id="guest_mapped_ok", contact_fingerprint="fp_aaaaaaaa",
            mapped_customer_id="cust_0001", mapping_audit_ref="audit_ref_123",
        ),
        "guest_no_audit": GuestContact(
            guest_id="guest_no_audit", contact_fingerprint="fp_bbbbbbbb",
            mapped_customer_id="cust_0001", mapping_audit_ref=None,   # mapping without audit -> HOLD
        ),
        "guest_unmapped": GuestContact(
            guest_id="guest_unmapped", contact_fingerprint="fp_cccccccc",
        ),
        "guest_bad_customer": GuestContact(
            guest_id="guest_bad_customer", contact_fingerprint="fp_dddddddd",
            mapped_customer_id="cust_ghost", mapping_audit_ref="audit_ref_999",
        ),
    }


@pytest.fixture
def consent_rows() -> Dict[str, ConsentSnapshot]:
    return {
        "cs_valid": ConsentSnapshot(
            "cs_valid", "guest_mapped_ok", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC}),
        ),
        "cs_valid_meas_only": ConsentSnapshot(
            "cs_valid_meas_only", "guest_mapped_ok", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
        # VALID consent issued for a DIFFERENT subject (guest_B) — used to prove the seam refuses to bind
        # one person's consent to another's event (subject mismatch, FAIL-002).
        "cs_valid_b": ConsentSnapshot(
            "cs_valid_b", "guest_B", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
        # VALID consent keyed by a CUSTOMER id (cust_0001) — subject binding must accept it for a guest that
        # is trustedly mapped to that customer (guest_mapped_ok -> cust_0001, with audit).
        "cs_valid_cust": ConsentSnapshot(
            "cs_valid_cust", "cust_0001", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
        "cs_missing": ConsentSnapshot(
            "cs_missing", "guest_x", ConsentState.MISSING, FIXED_TS, frozenset(),
        ),
        "cs_expired": ConsentSnapshot(
            "cs_expired", "guest_x", ConsentState.EXPIRED, FIXED_TS, frozenset(),
        ),
        "cs_optout": ConsentSnapshot(
            "cs_optout", "guest_x", ConsentState.OPT_OUT, FIXED_TS, frozenset(),
        ),
    }


@pytest.fixture
def audit() -> AuditLog:
    return AuditLog()


@pytest.fixture
def registry(registry_rows):
    return InMemoryEventRegistry(registry_rows)


@pytest.fixture
def guest_contacts(guest_rows):
    return InMemoryGuestContacts(guest_rows)


@pytest.fixture
def consent_reader(consent_rows):
    return InMemoryConsent(consent_rows, current={"guest_mapped_ok": ConsentState.VALID})


@pytest.fixture
def customers():
    return InMemoryCustomers({"cust_0001"})


@pytest.fixture
def validator(registry, audit):
    return EventValidator(registry, audit)


@pytest.fixture
def consent_gate(audit):
    return ConsentGate(audit)


@pytest.fixture
def resolver(guest_contacts, customers, audit):
    return IdentityResolver(guest_contacts, customers, audit)


@pytest.fixture
def store():
    return WebEventLogStore()
