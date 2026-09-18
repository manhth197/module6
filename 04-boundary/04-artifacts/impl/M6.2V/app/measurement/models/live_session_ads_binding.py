"""M6.2Q live-session-ads-binding.v1 (A5, M6-OD-011 binding direction) — bind a live_session to its primary campaign.

A frozen binding {live_session_id, primary_campaign_id, adset_id?, ad_id?, bound_at, bound_by}. `primary_campaign_id`
is first-class (mirrors the attribution snapshot's new field); the binding is the hook the CPA/ROAS reader uses to
attribute campaign-level spend to a live_session (session_for_campaign). `bound_by` is an actor/governance ref
(masked on export, RULE-014), never PII. No commission field (RULE-019); measure/record only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from app.measurement.masking import mask


@dataclass(frozen=True)
class LiveSessionAdsBinding:
    """One live_session <-> primary campaign binding (v1). Frozen; set-once per live_session (store-enforced)."""

    live_session_id: str
    primary_campaign_id: str
    adset_id: Optional[str] = None
    ad_id: Optional[str] = None
    bound_at: Optional[datetime] = None
    bound_by: Optional[str] = None          # actor/governance ref — masked on export (RULE-014), never PII

    def to_public(self) -> Dict[str, Any]:
        return {
            "live_session_id": self.live_session_id,
            "primary_campaign_id": self.primary_campaign_id,   # campaign ref, not PII
            "adset_id": self.adset_id,
            "ad_id": self.ad_id,
            "bound_at": self.bound_at.isoformat() if self.bound_at is not None else None,
            "bound_by": mask(self.bound_by),
        }

    def as_stored(self) -> Dict[str, Any]:
        return dict(self.to_public())
