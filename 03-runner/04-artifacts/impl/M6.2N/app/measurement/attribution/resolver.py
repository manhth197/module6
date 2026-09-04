"""M6-CTR-002 Attribution Resolver (+ Ads Context Resolver, Live Session Resolver) — M6.2E.

`AttributionResolver.resolve(event, conversion, signals=...)` builds an `AdsAttributionContext` from an
`ads_measurement_event` (Zone A) and its `conversion_event`. Fields the normalized event does not carry
(campaign/adset/ad NAMES, comment_id, messenger_thread_id, psid, referral_link_id, diamond_id) are supplied by
`signals` — the mapping the real Ads-Context / Live-Session sub-resolvers WOULD fetch from the ads-metadata and
live-session sources at the owner integration step. Everything is a pure, deterministic function of its inputs
(no clock, no randomness) so a re-materialize is idempotent (replay-stable).

Grading (RULE-009, fail-closed):
  * NO attributable entry-channel source            -> conflict = MISSING_SOURCE, confidence = LOW
  * an explicit duplicate-risk signal (dedup flag)   -> conflict = DUPLICATE_RISK, confidence = LOW
  * MORE THAN ONE entry channel present              -> conflict = MULTI_TOUCH,    confidence = LOW
  * exactly ONE clear entry channel                  -> conflict = NONE; confidence HIGH iff that channel's
                                                        identifying fields are complete, else MEDIUM
A LOW / non-NONE snapshot is never scale evidence (`AdsAttributionContext.is_scale_evidence_eligible`). No
attribution model is marked scale-authoritative (M6-OD-005 OPEN); first_touch AND last_touch are BOTH recorded
(multi-model display). The resolver reads consumed sources only — it never overrides Core / order state (FAIL-004).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional

from app.measurement.identity.psid_hash import hash_psid
from app.measurement.models.attribution_context import (
    DEFAULT_ATTRIBUTION_WINDOW,
    AdsAttributionContext,
    ConflictStatus,
    EntryChannel,
    SourceConfidence,
)


def derive_attribution_id(event_id: Optional[str]) -> Optional[str]:
    """A3 (M6.2L): the CTR-002 surrogate `attribution_id` (migration 0006), derived DETERMINISTICALLY and 1:1 from
    the attributed measurement `event_id` (mirrors 0006's `uq_aac_measurement_event` one-snapshot-per-row). Pure —
    no clock, no randomness (the `normalize.event_id_for` pattern) — so a re-materialize is a byte-identical no-op
    (store idempotency preserved). Returns None only when there is no event_id to key on (fail-closed)."""
    if not event_id:
        return None
    return "attr_" + hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class AdsContext:
    """Ads Context Resolver output — the ad hierarchy (ids from the event's Zone A; names from ads-metadata
    signals, absent when the ads-metadata source has not been joined)."""

    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    adset_id: Optional[str] = None
    adset_name: Optional[str] = None
    ad_id: Optional[str] = None
    ad_name: Optional[str] = None

    @property
    def present(self) -> bool:
        return bool(self.campaign_id or self.adset_id or self.ad_id)

    @property
    def complete(self) -> bool:
        """A fully-specified ad path (campaign + adset + ad) — the precondition for HIGH confidence."""
        return bool(self.campaign_id and self.adset_id and self.ad_id)


@dataclass(frozen=True)
class LiveContext:
    """Live Session Resolver output — the live/comment/messenger trace (SMK-013)."""

    live_session_id: Optional[str] = None
    comment_id: Optional[str] = None
    messenger_thread_id: Optional[str] = None
    psid_hash: Optional[str] = None      # B1: one-way salted hash of the PSID (raw psid never leaves resolve())

    @property
    def present(self) -> bool:
        return bool(self.live_session_id or self.comment_id or self.messenger_thread_id)


def resolve_ads_context(event: Any, signals: Mapping[str, Any]) -> AdsContext:
    """Ads Context Resolver: ad ids come from the measurement event's Zone A; ad NAMES are metadata the resolver
    would join from the ads platform (supplied via signals in the staged slice)."""
    return AdsContext(
        campaign_id=getattr(event, "campaign_id", None),
        campaign_name=signals.get("campaign_name"),
        adset_id=getattr(event, "adset_id", None),
        adset_name=signals.get("adset_name"),
        ad_id=getattr(event, "ad_id", None),
        ad_name=signals.get("ad_name"),
    )


def resolve_live_session(event: Any, signals: Mapping[str, Any]) -> LiveContext:
    """Live Session Resolver: `live_session_id` from the event's Zone A; comment/messenger from the live source
    (supplied via signals). Traces the live/comment/messenger chain (SMK-013). B1 (M5 PSID policy): the raw PSID
    (a `signals["psid"]`) is HASHED here — one-way + salted — so the raw value never enters the LiveContext or any
    durable row; only `psid_hash` travels onward."""
    return LiveContext(
        live_session_id=getattr(event, "live_session_id", None) or signals.get("live_session_id"),
        comment_id=signals.get("comment_id"),
        messenger_thread_id=signals.get("messenger_thread_id"),
        psid_hash=hash_psid(signals.get("psid")),
    )


class AttributionResolver:
    """Resolve one conversion's full source chain into an `AdsAttributionContext` (CTR-002)."""

    def resolve(
        self,
        event: Any,
        conversion: Any,
        *,
        signals: Optional[Mapping[str, Any]] = None,
    ) -> AdsAttributionContext:
        signals = dict(signals or {})
        ads = resolve_ads_context(event, signals)
        live = resolve_live_session(event, signals)
        referral_link_id = signals.get("referral_link_id")
        diamond_id = signals.get("diamond_id")
        crm = bool(signals.get("crm")) or signals.get("entry_channel") == EntryChannel.CRM.value

        channels = self._entry_channels(ads, live, referral_link_id, diamond_id, crm)
        confidence, conflict = self._grade(ads, live, referral_link_id, diamond_id, channels, signals)
        entry_channel = self._reported_channel(channels)

        page_id = getattr(event, "page_id", None) or signals.get("page_id") or ""
        window = signals.get("attribution_window") or DEFAULT_ATTRIBUTION_WINDOW
        first_touch = signals.get("first_touch_event_id") or getattr(event, "event_id", None)
        last_touch = signals.get("last_touch_event_id") or getattr(conversion, "source_event_id", None)
        # A3: deterministic trace key, 1:1 with the measurement row (migration 0006 surrogate id) -> id -> campaign.
        attribution_id = derive_attribution_id(getattr(event, "event_id", None) or last_touch)

        return AdsAttributionContext(
            page_id=page_id,
            entry_channel=entry_channel,
            attribution_window=window,
            source_confidence=confidence,
            conflict_status=conflict,
            campaign_id=ads.campaign_id,
            campaign_name=ads.campaign_name,
            adset_id=ads.adset_id,
            adset_name=ads.adset_name,
            ad_id=ads.ad_id,
            ad_name=ads.ad_name,
            live_session_id=live.live_session_id,
            comment_id=live.comment_id,
            messenger_thread_id=live.messenger_thread_id,
            psid_hash=live.psid_hash,
            referral_link_id=referral_link_id,
            diamond_id=diamond_id,
            first_touch_event_id=first_touch,
            last_touch_event_id=last_touch,
            attribution_id=attribution_id,
        )

    # --- helpers -----------------------------------------------------------------------------------
    @staticmethod
    def _entry_channels(
        ads: AdsContext, live: LiveContext, referral_link_id: Optional[str], diamond_id: Optional[str], crm: bool
    ) -> List[EntryChannel]:
        channels: List[EntryChannel] = []
        if ads.present:
            channels.append(EntryChannel.FACEBOOK_AD)
        if referral_link_id or diamond_id:
            channels.append(EntryChannel.DIAMOND_LINK)
        # A4 (M6.2L): a live_session/comment/messenger co-present with a COMPLETE FACEBOOK_AD path (campaign AND
        # adset AND ad) is that ad funnel's downstream live trace, NOT a competing organic entry -> it does not add
        # a LIVE_ORGANIC channel, so a fully-identified ad carrying a live_session grades single-channel
        # FACEBOOK_AD/HIGH (SMK-020). An INCOMPLETE ad path + live stays a genuine MULTI_TOUCH ambiguity (SMK-007).
        if live.present and not ads.complete:
            channels.append(EntryChannel.LIVE_ORGANIC)
        if crm:
            channels.append(EntryChannel.CRM)
        return channels

    @staticmethod
    def _reported_channel(channels: List[EntryChannel]) -> EntryChannel:
        """The single reported entry_channel. With no source -> DIRECT (unattributed). With exactly one -> that
        one. With several (a MULTI_TOUCH conflict) -> the highest-priority present one; the conflict_status flags
        the ambiguity so the row is not treated as clean single-source evidence."""
        if not channels:
            return EntryChannel.DIRECT
        priority = [
            EntryChannel.FACEBOOK_AD,
            EntryChannel.DIAMOND_LINK,
            EntryChannel.LIVE_ORGANIC,
            EntryChannel.CRM,
        ]
        for ch in priority:
            if ch in channels:
                return ch
        return EntryChannel.DIRECT

    @staticmethod
    def _grade(
        ads: AdsContext,
        live: LiveContext,
        referral_link_id: Optional[str],
        diamond_id: Optional[str],
        channels: List[EntryChannel],
        signals: Mapping[str, Any],
    ):
        # An explicit dedup/duplicate-risk signal fails closed (a possible double count is never HIGH evidence).
        if signals.get("duplicate_risk"):
            return SourceConfidence.LOW, ConflictStatus.DUPLICATE_RISK
        if not channels:
            return SourceConfidence.LOW, ConflictStatus.MISSING_SOURCE
        if len(channels) > 1:
            return SourceConfidence.LOW, ConflictStatus.MULTI_TOUCH
        # exactly one clear entry channel -> no conflict; HIGH only if that channel is fully identified.
        only = channels[0]
        if only is EntryChannel.FACEBOOK_AD:
            conf = SourceConfidence.HIGH if ads.complete else SourceConfidence.MEDIUM
        elif only is EntryChannel.LIVE_ORGANIC:
            conf = SourceConfidence.HIGH if live.live_session_id else SourceConfidence.MEDIUM
        elif only is EntryChannel.DIAMOND_LINK:
            conf = SourceConfidence.HIGH if diamond_id else SourceConfidence.MEDIUM
        else:  # CRM
            conf = SourceConfidence.MEDIUM
        return conf, ConflictStatus.NONE
