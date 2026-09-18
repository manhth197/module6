"""M6.2S event-registry-feed.v1 read-models — the PROPOSED registry-feed shape M6 READS (chief RELAY_V221 §2.4).

TODO(contract): the feed name/shape is PROPOSED — the FINAL name/shape is chief-issued (RELAY_V221 finalization),
not M6-invented (RULE-001/018). The PROPOSED endpoint is `GET /api/v1/internal/event-registry?since_version={n}`
returning `{registry_version, events:[{event_code, event_group, domain, data_sensitivity, external_send_policy,
is_active, updated_at}]}`. M6 READS this Core-owned governance metadata for its own fail-closed validation; it
never writes/invents an event, reconciles the Core enum, or decides the permit-mapping. The feed carries NO
customer PII (RULE-014) — only event governance fields. Reuses the M6.2P `DataSensitivity` + `ExternalSendPolicy`
enums (no new vocabulary, RULE-018).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy

# TODO(contract): PROPOSED name/shape — the FINAL name/shape is chief-issued (RELAY_V221 finalization).
PROPOSED_FEED_CONTRACT = "event-registry-feed.v1"                                    # TODO(contract)
PROPOSED_FEED_ENDPOINT = "GET /api/v1/internal/event-registry?since_version={n}"     # TODO(contract)


@dataclass(frozen=True)
class RegistryFeedRow:
    """One parsed feed row (typed, RESOLVED). `data_sensitivity` / `external_send_policy` carry the fail-closed
    COERCED enum members (unknown -> PII / BLOCKED_DEFAULT); `is_active` is a strict bool (fail-closed False). The
    optional metadata (`event_group`/`domain`/`updated_at`) is `None` when the feed omits it — never invented."""

    event_code: str
    data_sensitivity: DataSensitivity
    external_send_policy: ExternalSendPolicy
    is_active: bool
    event_group: Optional[str] = None
    domain: Optional[str] = None
    updated_at: Optional[str] = None

    def to_public(self) -> Dict[str, Any]:
        """Export-safe mapping (governance metadata — not customer PII, RULE-014); enums as their string tokens."""
        return {
            "event_code": self.event_code,
            "data_sensitivity": self.data_sensitivity.value,
            "external_send_policy": self.external_send_policy.value,
            "is_active": self.is_active,
            "event_group": self.event_group,
            "domain": self.domain,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class RegistryFeed:
    """One feed snapshot as read: the monotonic `registry_version` + its parsed rows."""

    registry_version: int
    rows: Tuple[RegistryFeedRow, ...] = ()

    def to_public(self) -> Dict[str, Any]:
        return {
            "registry_version": self.registry_version,
            "events": [r.to_public() for r in self.rows],
        }
