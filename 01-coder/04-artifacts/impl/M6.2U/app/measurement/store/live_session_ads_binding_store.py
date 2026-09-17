"""In-memory store for live-session-ads-binding.v1 (M6.2Q, A5).

Keyed by live_session_id, with a reverse index primary_campaign_id -> live_session_id — the spend->session join
hook (session_for_campaign). Bindings are SET-ONCE: a re-bind of the same session with an identical binding is an
idempotent no-op; a different binding for a bound session, or a campaign already bound to a DIFFERENT session, is
refused loudly (LiveSessionAdsBindingStoreViolation) so session_for_campaign stays unambiguous. No update/delete.
The physical DB binding is the M6-OD-011 integration step (migration 0016, live_migrations=false).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.measurement.models.live_session_ads_binding import LiveSessionAdsBinding


class LiveSessionAdsBindingStoreViolation(Exception):
    """Raised on a forbidden op: re-binding a session to a different campaign, or binding a campaign already bound
    to a different session (would make session_for_campaign ambiguous)."""


class LiveSessionAdsBindingStore:
    def __init__(self) -> None:
        self._by_session: Dict[str, LiveSessionAdsBinding] = {}
        self._session_by_campaign: Dict[str, str] = {}
        self._order: List[str] = []

    def bind(self, binding: LiveSessionAdsBinding) -> LiveSessionAdsBinding:
        existing = self._by_session.get(binding.live_session_id)
        if existing is not None:
            if existing == binding:
                return existing                          # idempotent re-bind (set-once)
            raise LiveSessionAdsBindingStoreViolation(
                f"live_session {binding.live_session_id} already bound (set-once)"
            )
        owner = self._session_by_campaign.get(binding.primary_campaign_id)
        if owner is not None and owner != binding.live_session_id:
            raise LiveSessionAdsBindingStoreViolation(
                f"campaign {binding.primary_campaign_id} already bound to live_session {owner}"
            )
        self._by_session[binding.live_session_id] = binding
        self._session_by_campaign[binding.primary_campaign_id] = binding.live_session_id
        self._order.append(binding.live_session_id)
        return binding

    def get(self, live_session_id: str) -> Optional[LiveSessionAdsBinding]:
        return self._by_session.get(live_session_id)

    def session_for_campaign(self, campaign_id: str) -> Optional[str]:
        """The live_session a campaign's spend attributes to (M6-OD-011 binding direction). None when unbound."""
        if not campaign_id:
            return None
        return self._session_by_campaign.get(campaign_id)

    def all(self) -> Tuple[LiveSessionAdsBinding, ...]:
        return tuple(self._by_session[s] for s in self._order)

    def __len__(self) -> int:
        return len(self._order)
