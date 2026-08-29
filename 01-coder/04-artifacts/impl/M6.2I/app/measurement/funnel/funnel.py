"""M6.2I `GoldenHourFunnel` — the derived, read-only conversion-funnel assembler.

Projects the doc §8 chain (Ads → Live → Comment → Messenger → Quote → Order → Verified) over the M6-owned
`ads_measurement_events` store, per live-session, bucketable by observed Golden Hour state. It:

  * counts per-stage events (ADS_TO_LIVE is an identity-presence indicator, not an event code);
  * computes the doc §14 funnel rates — reusing kpi_metrics' `_safe_div` (identical fail-closed division) and the
    §14 formula definitions (`flow.FUNNEL_RATE_SPECS`), re-applied at the per-session / per-state grain;
  * sums verified revenue from ORDER_VERIFIED rows ONLY (RULE-003 / FAIL-001) — a quote / order-created is a
    funnel stage, never revenue (SMK-004);
  * records the RULE-021 order-capture flag from a CONSUMED Commerce signal (absent ⇒ False, fail-closed) —
    Module 6 records whether Commerce's gate passed; it never performs / owns / bypasses that validation;
  * threads the live/comment/messenger trace from `ads_attribution_context` (SMK-013); psid masked on export.

Golden-hour state and the capture flag are CONSUMED signals (Gateway/Live, Commerce) injected at construction —
Module 6 reads them, never computes them. This class is READ-ONLY: it has no write / send / scale / publish method.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from app.measurement.dashboard.kpi_metrics import _safe_div   # reuse the exact fail-closed division primitive
from app.measurement.funnel.flow import (
    CHAIN,
    FUNNEL_RATE_SPECS,
    REVENUE_VALID_EVENT,
    FlowStage,
    stage_for,
)
from app.measurement.funnel.golden_hour import GoldenHourState, observe_state
from app.measurement.funnel.models import FunnelRate, FunnelTrace, GoldenHourFunnelView

_AD_IDENTITY_FIELDS = ("campaign_id", "adset_id", "ad_id", "live_session_id")


def _session_key(event: Any) -> Optional[str]:
    """The live-session grouping key: the event's Zone-A live_session_id, else its attribution_context's."""
    key = getattr(event, "live_session_id", None)
    if key:
        return key
    ctx = getattr(event, "attribution_context", None)
    if isinstance(ctx, Mapping):
        return ctx.get("live_session_id")
    return None


def _has_ads_or_live_identity(event: Any) -> bool:
    """True iff the Ads → Live identity boundary is present (any ad-hierarchy id or a live_session_id)."""
    if any(getattr(event, f, None) for f in _AD_IDENTITY_FIELDS):
        return True
    ctx = getattr(event, "attribution_context", None)
    if isinstance(ctx, Mapping):
        return bool(ctx.get("campaign_id") or ctx.get("adset_id") or ctx.get("ad_id") or ctx.get("live_session_id"))
    return False


def _count_code(events: List[Any], code: str) -> int:
    return sum(1 for e in events if getattr(e, "event_code", None) == code)


def _stage_counts(events: List[Any]) -> Dict[FlowStage, int]:
    """Per-stage counts over `events`. ADS_TO_LIVE is a 0/1 identity-presence indicator (no event code); the other
    five stages are event-code counts (doc §8 map)."""
    counts: Dict[FlowStage, int] = {stage: 0 for stage in CHAIN}
    counts[FlowStage.ADS_TO_LIVE] = 1 if any(_has_ads_or_live_identity(e) for e in events) else 0
    for e in events:
        stage = stage_for(getattr(e, "event_code", None))
        if stage is not None:
            counts[stage] += 1
    return counts


def _rates(events: List[Any]) -> Tuple[FunnelRate, ...]:
    """The doc §14 funnel rates over `events` — same formula definitions as kpi_metrics, per-session grain,
    fail-closed via the reused `_safe_div`."""
    out: List[FunnelRate] = []
    for name, formula, num_code, den_code in FUNNEL_RATE_SPECS:
        num = _count_code(events, num_code)
        den = _count_code(events, den_code)
        out.append(FunnelRate(name=name, formula=formula, value=_safe_div(num, den), numerator=num, denominator=den))
    return tuple(out)


class GoldenHourFunnel:
    """Read-only Golden Hour funnel projection over the measurement store + CONSUMED golden-hour / capture signals."""

    def __init__(
        self,
        measurement_store: Any,
        *,
        golden_hour_state_by_event: Optional[Mapping[str, Any]] = None,
        capture_gate_passed_by_order: Optional[Mapping[str, bool]] = None,
    ) -> None:
        self._store = measurement_store
        # CONSUMED: Gateway/Live reports the golden-hour state an event occurred in (event_id -> state signal).
        self._gh: Dict[str, Any] = dict(golden_hour_state_by_event or {})
        # CONSUMED: Commerce reports whether its stock/fulfillment/trust/policy + confirmation gate passed BEFORE
        # send-to-Core (order_code -> bool). RULE-021: Module 6 records this; it never computes it.
        self._cap: Dict[str, bool] = dict(capture_gate_passed_by_order or {})

    # --- measurement (read-only) -------------------------------------------------------------------
    def assemble(self) -> List[GoldenHourFunnelView]:
        """Group the store's events by live-session and build one `GoldenHourFunnelView` per session. Nothing is
        written; nothing is sent. Sessions are ordered by first-seen key for determinism."""
        by_session: Dict[Optional[str], List[Any]] = {}
        order: List[Optional[str]] = []
        for event in self._store.all():
            key = _session_key(event)
            if key not in by_session:
                by_session[key] = []
                order.append(key)
            by_session[key].append(event)
        return [self._view(key, by_session[key]) for key in order]

    def view_for(self, live_session_id: str) -> Optional[GoldenHourFunnelView]:
        for v in self.assemble():
            if v.live_session_id == live_session_id:
                return v
        return None

    # --- helpers -----------------------------------------------------------------------------------
    def _view(self, key: Optional[str], events: List[Any]) -> GoldenHourFunnelView:
        # observed golden-hour states, dedup preserving first-seen order (fail-closed to UNKNOWN per event)
        states: List[GoldenHourState] = []
        state_of: Dict[int, GoldenHourState] = {}
        for e in events:
            st = observe_state(self._gh.get(getattr(e, "event_id", None)))
            state_of[id(e)] = st
            if st not in states:
                states.append(st)

        state_breakdown: Dict[GoldenHourState, Dict[FlowStage, int]] = {}
        for st in states:
            st_events = [e for e in events if state_of[id(e)] is st]
            state_breakdown[st] = _stage_counts(st_events)

        return GoldenHourFunnelView(
            live_session_id=key,
            golden_hour_states=tuple(states),
            stage_counts=_stage_counts(events),
            state_breakdown=state_breakdown,
            rates=_rates(events),
            verified_revenue=self._verified_revenue(events),
            capture_gate_passed=self._capture_gate_passed(events),
            trace=self._trace(key, events),
        )

    @staticmethod
    def _verified_revenue(events: List[Any]) -> float:
        """RULE-003 / FAIL-001: sum revenue ONLY from ORDER_VERIFIED rows whose set-once Zone-B revenue_value is
        populated. The choke is SELF-ENFORCING (defense-in-depth): it ANDs the ORDER_VERIFIED event code with
        revenue presence, so even a row that (through store/materializer misuse or a mismatched event↔conversion
        pairing) carried a revenue_value on a non-verified event code contributes 0 — a quote / order-created is
        never revenue (SMK-004). PAYMENT_COMPLETED and every non-verified stage are meant to contribute 0."""
        return float(sum(
            e.revenue_value for e in events
            if getattr(e, "event_code", None) == REVENUE_VALID_EVENT and getattr(e, "revenue_value", None) is not None
        ))

    def _capture_gate_passed(self, events: List[Any]) -> bool:
        """RULE-021, fail-closed: True only when EVERY order in the session carries the consumed Commerce-gate
        flag True. No order, or any order missing/False, ⇒ False. Module 6 records this; it never validates."""
        order_codes = {e.order_code for e in events if getattr(e, "order_code", None)}
        if not order_codes:
            return False
        return all(self._cap.get(oc, False) is True for oc in order_codes)

    @staticmethod
    def _trace(key: Optional[str], events: List[Any]) -> FunnelTrace:
        """Thread live_session_id + comment_id + messenger_thread_id from the session's materialized
        attribution_context (SMK-013). psid is carried durably here (raw) but masked on export (FunnelTrace)."""
        comment_id = messenger_thread_id = psid = None
        for e in events:
            ctx = getattr(e, "attribution_context", None)
            if isinstance(ctx, Mapping) and ctx:
                comment_id = comment_id or ctx.get("comment_id")
                messenger_thread_id = messenger_thread_id or ctx.get("messenger_thread_id")
                psid = psid or ctx.get("psid")
        return FunnelTrace(
            live_session_id=key, comment_id=comment_id, messenger_thread_id=messenger_thread_id, psid=psid
        )
