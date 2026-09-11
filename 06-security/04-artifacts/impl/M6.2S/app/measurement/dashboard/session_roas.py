"""M6.2Q CPA/ROAS-by-live_session (A5) — the đường-tới-tiền reader (M6-CTR-015 formulas; RULE-003 lock).

A STANDALONE read-only reader (mirrors funnel.assemble) — deliberately NOT a DataMart method and NOT a 15th
kpi_metrics metric, so the pinned DataMart support-view allow-set (RULE-012 / SMK-010) and the 14-metric verbatim
formula test both stay exactly green. Per live_session it computes, from APPROVED imported spend only:

    CPA  = session_spend / count(ORDER_VERIFIED in session)          (spend / verified-order count)
    ROAS = session_verified_revenue / session_spend                  (verified revenue / spend)

Verified revenue + the ORDER_VERIFIED count keep the Zone-B verified lock (RULE-003 / FAIL-001): a quote / draft in
the window contributes 0. Spend is attributed to a session ONLY when the record's campaign_id is BOUND to that
session (live_session_ads_binding: session_for_campaign) AND its spend_date falls inside the session's derived
[min,max event_ts] window. The spend source is CAMPAIGN-LEVEL (M6-OD-016), so inclusion gates on the
campaign-binding — NOT the 3-id AdsSpendRecord.mapped predicate (a campaign-only record has adset_id/ad_id None and
would be wrongly dropped by .mapped). Spend outside every session window, or on an unbound campaign, is NOT
session-attributed — it falls to daily_total(). Every division is fail-closed via the shared _safe_div: a session
with spend + ZERO verified orders -> CPA None (no divide-by-zero) and ROAS 0.0 (wasted spend); a session with NO
bound spend -> CPA None and ROAS None (a genuine 0/0, never a fabricated 0). Reading writes nothing (SMK-010 purity).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from app.measurement.dashboard.data_mart import AdsSpendRecord
from app.measurement.dashboard.kpi_metrics import _safe_div      # reuse the exact fail-closed division primitive
from app.measurement.funnel.funnel import _session_key            # reuse the exact live-session grouping key

_ORDER_VERIFIED = "ORDER_VERIFIED"


@dataclass(frozen=True)
class SessionCpaRoas:
    """One live_session's spend-derived CPA/ROAS (read-only; fail-closed). `session_spend` is None when no APPROVED
    spend is bound-and-in-window; `cpa`/`roas` are None on a fail-closed (zero/None) denominator."""

    live_session_id: str
    session_spend: Optional[float]
    verified_orders: int
    verified_revenue: float
    cpa: Optional[float]
    roas: Optional[float]

    def to_public(self) -> Dict[str, Any]:
        return {
            "live_session_id": self.live_session_id,
            "session_spend": self.session_spend,
            "verified_orders": self.verified_orders,
            "verified_revenue": self.verified_revenue,
            "cpa": self.cpa,
            "roas": self.roas,
        }


class SessionRoasReader:
    """Read-only CPA/ROAS-by-live_session over the measurement store + APPROVED spend records + the
    campaign->session binding. Holds no write/send/scale handle (RULE-012)."""

    def __init__(self, measurement_store: Any, spend_records, binding_store: Any) -> None:
        self._store = measurement_store
        # only APPROVED-materialized spend reaches here (the record store holds nothing else) — campaign-level.
        self._spend: Tuple[AdsSpendRecord, ...] = tuple(spend_records)
        self._binding = binding_store

    # --- grouping -----------------------------------------------------------------------------------
    def _sessions(self) -> List[Tuple[str, List[Any]]]:
        by_session: Dict[Optional[str], List[Any]] = {}
        order: List[Optional[str]] = []
        for event in self._store.all():
            key = _session_key(event)
            if key not in by_session:
                by_session[key] = []
                order.append(key)
            by_session[key].append(event)
        # CPA/ROAS is per live_session — the None-key bucket (events with no live_session) is not a session.
        return [(k, by_session[k]) for k in order if k is not None]

    @staticmethod
    def _window(events: List[Any]):
        ts = [e.event_ts for e in events if getattr(e, "event_ts", None) is not None]
        if not ts:
            return None, None
        return min(ts), max(ts)

    def _session_spend(self, live_session_id: str, window_start, window_end) -> Optional[float]:
        """Sum APPROVED spend BOUND to this session (campaign-binding, NOT .mapped) whose spend_date is in the
        derived window. None when nothing qualifies (fail-closed — never a fabricated 0)."""
        if window_start is None or window_end is None:
            return None
        amounts = [
            r.amount for r in self._spend
            if r.campaign_id
            and self._binding.session_for_campaign(r.campaign_id) == live_session_id
            and r.spend_date is not None
            and window_start <= r.spend_date <= window_end
        ]
        if not amounts:
            return None
        return float(sum(amounts))

    @staticmethod
    def _verified(events: List[Any]) -> Tuple[int, float]:
        """(count of ORDER_VERIFIED rows, sum of their set-once revenue) — RULE-003 verified lock; a quote/draft
        contributes 0. Mirrors data_mart.verified_rows / funnel._verified_revenue."""
        count = sum(1 for e in events if getattr(e, "event_code", None) == _ORDER_VERIFIED)
        revenue = float(sum(
            e.revenue_value for e in events
            if getattr(e, "event_code", None) == _ORDER_VERIFIED and getattr(e, "revenue_value", None) is not None
        ))
        return count, revenue

    # --- public read --------------------------------------------------------------------------------
    def by_session(self) -> List[SessionCpaRoas]:
        out: List[SessionCpaRoas] = []
        for live_session_id, events in self._sessions():
            window_start, window_end = self._window(events)
            spend = self._session_spend(live_session_id, window_start, window_end)
            verified_orders, verified_revenue = self._verified(events)
            out.append(SessionCpaRoas(
                live_session_id=live_session_id,
                session_spend=spend,
                verified_orders=verified_orders,
                verified_revenue=verified_revenue,
                cpa=_safe_div(spend, verified_orders),           # spend / verified count; None on 0/None den
                roas=_safe_div(verified_revenue, spend),         # verified revenue / spend; None on 0/None spend
            ))
        return out

    def for_session(self, live_session_id: str) -> Optional[SessionCpaRoas]:
        for s in self.by_session():
            if s.live_session_id == live_session_id:
                return s
        return None

    def daily_total(self) -> Optional[float]:
        """Spend NOT attributed to any live_session — a record whose campaign is unbound, or whose spend_date is
        outside its bound session's window. None when there is no spend at all; a float sum otherwise (0.0 when every
        spend record was session-attributed)."""
        if not self._spend:
            return None
        window_by_session = {sid: self._window(evs) for sid, evs in self._sessions()}
        attributed = set()
        for idx, r in enumerate(self._spend):
            if not r.campaign_id or r.spend_date is None:
                continue
            sid = self._binding.session_for_campaign(r.campaign_id)
            if sid is None or sid not in window_by_session:
                continue
            ws, we = window_by_session[sid]
            if ws is not None and we is not None and ws <= r.spend_date <= we:
                attributed.add(idx)
        unattributed = [r.amount for idx, r in enumerate(self._spend) if idx not in attributed]
        return float(sum(unattributed))
