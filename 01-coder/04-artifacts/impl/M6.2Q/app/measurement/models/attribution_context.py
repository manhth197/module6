"""M6-CTR-002 ads_attribution_context — the attribution snapshot (SPEC §10.2 / doc §11, 19 DRAFT_LOCKED fields).

Produced by the attribution_materializer (M6-CTR-023, M6.2E) from an `ads_measurement_event` (Zone A) + a
`conversion_event`, then written SET-ONCE into Zone B of `ads_measurement_events` (RULE-008). Missing / conflicting
sources degrade `source_confidence` -> LOW and set `conflict_status`; such a snapshot is NEVER scale evidence
(RULE-009). `psid_hash` is a ONE-WAY salted hash of the PSID (B1 / M5 PSID policy PSID_HASH_POLICY_M5_TMP): a raw
PSID is NEVER stored on any durable row (mask() is reversible, insufficient); the hash is safe on every surface.
`referral_link_id` / `diamond_id` are RECORDED for attribution only — Module 6 never computes a commission from them
(RULE-019; Finance owns).

The 19 fields are reproduced verbatim from SPEC §10.2 (name / type / optionality); `page_id`,
`attribution_window`, `entry_channel`, `source_confidence`, `conflict_status` are required, the other 14 optional
(a missing source is legitimate — it degrades confidence rather than raising, RULE-009).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class EntryChannel(str, Enum):
    """SPEC §10.2 entry_channel enum (verbatim)."""

    FACEBOOK_AD = "FACEBOOK_AD"
    LIVE_ORGANIC = "LIVE_ORGANIC"
    DIAMOND_LINK = "DIAMOND_LINK"
    CRM = "CRM"
    DIRECT = "DIRECT"


class SourceConfidence(str, Enum):
    """SPEC §10.2 source_confidence enum (verbatim). Only HIGH is unambiguous; LOW/MEDIUM never scale (RULE-009)."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConflictStatus(str, Enum):
    """SPEC §10.2 conflict_status enum (verbatim). Anything other than NONE degrades to not-scale-evidence."""

    NONE = "NONE"
    MULTI_TOUCH = "MULTI_TOUCH"
    MISSING_SOURCE = "MISSING_SOURCE"
    DUPLICATE_RISK = "DUPLICATE_RISK"


# Operational default attribution window. NOT an owner-ratified value — the attribution MODEL (window included) is
# M6-OD-005 (OPEN); no model is scale-authoritative until then (see config.SCALE_MODEL_RATIFIED). Recorded metadata
# only; the resolver lets a caller override it via signals.
DEFAULT_ATTRIBUTION_WINDOW = "7d_click_1d_view"


@dataclass(frozen=True)
class AdsAttributionContext:
    """One attribution snapshot (M6-CTR-002), frozen. Field order groups required-then-optional for readability;
    all 19 doc fields are present with their doc optionality."""

    # --- required (doc: non-optional) ---
    page_id: str
    entry_channel: EntryChannel
    attribution_window: str
    source_confidence: SourceConfidence
    conflict_status: ConflictStatus
    # --- optional ad hierarchy ---
    campaign_id: Optional[str] = None
    # M6.2Q (A5): primary_campaign_id first-class (mirrors live-session-ads-binding.v1). Deterministic from the
    # event's campaign_id (else a signal); ADDITIVE and NOT wired into .complete/_grade, so A4/SMK-020/006/007 are
    # unaffected. Governance ref (campaign id, NOT PII).
    primary_campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    adset_id: Optional[str] = None
    adset_name: Optional[str] = None
    ad_id: Optional[str] = None
    ad_name: Optional[str] = None
    # --- optional channel / identity refs ---
    live_session_id: Optional[str] = None
    comment_id: Optional[str] = None
    messenger_thread_id: Optional[str] = None
    psid_hash: Optional[str] = None             # B1 (M5 PSID policy): one-way salted hash (psid_hash:...), NEVER raw
    referral_link_id: Optional[str] = None      # Diamond referral — RECORDED only, never a commission (RULE-019)
    diamond_id: Optional[str] = None            # Diamond referral — RECORDED only, never a commission (RULE-019)
    # --- multi-model touch refs (M6-OD-005 OPEN -> BOTH recorded, neither marked scale-authoritative) ---
    first_touch_event_id: Optional[str] = None
    last_touch_event_id: Optional[str] = None
    # --- trace key (A3, M6.2L): the CTR-002 surrogate id already declared in migration 0006
    #     (attribution_id, PACK surrogate PK, one per measurement row via uq_aac_measurement_event), surfaced here
    #     as a first-class key so an ORDER_VERIFIED row traces attribution_id -> campaign. Deterministic (1:1 with
    #     the measurement event_id), governance ref only (NOT PII -> not masked); no commission field (RULE-019). ---
    attribution_id: Optional[str] = None

    def is_scale_evidence_eligible(self) -> bool:
        """Data-quality bar for scale evidence (RULE-009): a snapshot may be scale evidence ONLY when it is
        unambiguous — `source_confidence == HIGH` and `conflict_status == NONE`. LOW/MEDIUM, or ANY conflict
        (MULTI_TOUCH / MISSING_SOURCE / DUPLICATE_RISK), is NEVER scale evidence.

        This is necessary, NOT sufficient: whether any attribution MODEL is scale-authoritative is a separate
        forward owner gate (M6-OD-005 / config.SCALE_MODEL_RATIFIED). The materializer ANDs both — fail-closed."""
        return (
            self.source_confidence is SourceConfidence.HIGH
            and self.conflict_status is ConflictStatus.NONE
        )

    def to_public(self) -> Dict[str, Any]:
        """Export-safe mapping (audit / evidence / dashboard feed): `psid_hash` is a one-way salted hash (B1 — no raw
        PSID anywhere, so it needs no masking); enums rendered as their doc string tokens. No commission field to leak
        (RULE-019)."""
        return {
            "campaign_id": self.campaign_id,
            "primary_campaign_id": self.primary_campaign_id,   # M6.2Q (A5): first-class campaign ref (not PII)
            "campaign_name": self.campaign_name,
            "adset_id": self.adset_id,
            "adset_name": self.adset_name,
            "ad_id": self.ad_id,
            "ad_name": self.ad_name,
            "page_id": self.page_id,
            "live_session_id": self.live_session_id,
            "comment_id": self.comment_id,
            "messenger_thread_id": self.messenger_thread_id,
            "psid_hash": self.psid_hash,        # B1: one-way salted hash — safe as-is (no mask; raw never stored)
            "referral_link_id": self.referral_link_id,
            "diamond_id": self.diamond_id,
            "entry_channel": self.entry_channel.value,
            "attribution_window": self.attribution_window,
            "first_touch_event_id": self.first_touch_event_id,
            "last_touch_event_id": self.last_touch_event_id,
            "attribution_id": self.attribution_id,          # A3 trace key (governance ref; not PII)
            "source_confidence": self.source_confidence.value,
            "conflict_status": self.conflict_status.value,
        }

    def as_stored(self) -> Dict[str, Any]:
        """Durable Zone-B mapping written into `ads_measurement_events.attribution_context`. B1 (M5 PSID policy):
        the durable row NEVER keeps a raw PSID — `psid_hash` is a one-way salted hash, so the durable mapping is the
        SAME as the export mapping (nothing here is reversible). Trace joins use `psid_hash` (deterministic per
        pepper), not a raw id."""
        return dict(self.to_public())
