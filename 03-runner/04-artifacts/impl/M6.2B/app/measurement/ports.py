"""Read-only ports to the CONSUMED sources.

These Protocols expose ONLY read methods — there is deliberately no insert/update/delete — so Module 6 cannot
mutate a table owned by Core Event Governance, Customer identity, or the Consent system (RULE-018, boundary).
Concrete adapters are supplied by the caller; in the staged slice the test doubles live in tests/conftest.py.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from app.measurement.models.consumed import (
    ConsentSnapshot,
    ConsentState,
    EventRegistryRow,
    GuestContact,
)


@runtime_checkable
class EventRegistryReader(Protocol):
    """Read-only view of Core's event_registry (M6-CTR-003)."""

    def get(self, event_code: str) -> Optional[EventRegistryRow]:
        ...


@runtime_checkable
class GuestContactReader(Protocol):
    """Read-only view of guest_contacts (M6-CTR-005)."""

    def get(self, guest_id: str) -> Optional[GuestContact]:
        ...


@runtime_checkable
class ConsentReader(Protocol):
    """Read-only view of guest_marketing_consent_snapshot (M6-CTR-006)."""

    def get(self, consent_snapshot_id: str) -> Optional[ConsentSnapshot]:
        ...

    def current_state(self, subject_ref: str) -> ConsentState:
        """Send-time checkpoint the FUTURE dispatcher will use (out of scope in M6.2A)."""
        ...


@runtime_checkable
class CustomerRefReader(Protocol):
    """Minimal read-only existence check for a mapped customer id (customers/... consumed)."""

    def exists(self, customer_id: str) -> bool:
        ...
