"""M6.2F Data Mart — a READ-ONLY support view over the M6-owned measurement store + CONSUMED staged inputs.

RULE-012 / FAIL-005 / SMK-010: the Data Mart is a SUPPORT VIEW ONLY. It exposes ONLY read/aggregate methods —
there is deliberately NO write, and NO CRM / pricing / Diamond / budget-scale / trigger method to call. It can
never become a trigger owner.

Verified-only revenue (RULE-003 / FAIL-001, the single revenue choke): `verified_rows()` returns ONLY rows whose
set-once Zone-B `revenue_value` is populated — which M6.2E writes ONLY on the ORDER_VERIFIED path. Quote /
order-draft / payment-waiting events are counted in the funnel but contribute ZERO to any revenue aggregate.

CONSUMED inputs (Ads Spend, verified boxes, COD) are Ads-platform / Commerce owned — M6 READS them, never computes
or writes them; an absent input is fail-closed (the dependent metric is None, never fabricated).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Mapping, Optional, Tuple

_ORDER_VERIFIED = "ORDER_VERIFIED"


@dataclass(frozen=True)
class AdsSpendRecord:
    """One approved-spend line (CONSUMED, Ads platform). Must carry campaign/adset/ad mapping (doc §14 note);
    an unmapped record is excluded from the mapped total (fail-closed)."""

    amount: float
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    ad_id: Optional[str] = None
    # M6.2Q (A5): the calendar day this spend was reported — the key that cuts campaign-level spend to a
    # live_session window (dashboard/session_roas). ADDITIVE (default None): the positional constructor
    # AdsSpendRecord(amount, campaign, adset, ad) is unchanged and `mapped` is untouched.
    spend_date: Optional[datetime] = None

    @property
    def mapped(self) -> bool:
        return bool(self.campaign_id and self.adset_id and self.ad_id)


@dataclass(frozen=True)
class ConsumedFacts:
    """The Commerce/Ads-owned facts the dashboard READS but never computes. All optional — absent ⇒ fail-closed.
    `boxes_by_order` / cod counts come from Commerce; `ads_spend` from the approved spend import."""

    ads_spend: Tuple[AdsSpendRecord, ...] = ()
    boxes_by_order: Mapping[str, int] = field(default_factory=dict)   # order_code -> verified boxes
    cod_orders: Optional[int] = None
    cod_fail: Optional[int] = None

    def mapped_spend_total(self) -> Optional[float]:
        mapped = [r.amount for r in self.ads_spend if r.mapped]
        if not self.ads_spend or not mapped:
            return None                     # no spend / no mapped spend -> fail-closed (metric None)
        return float(sum(mapped))


class DataMart:
    """READ-ONLY support view. Construct with the measurement store (M6-owned) + consumed facts; expose only
    aggregates. There is NO method here that writes, sends, or triggers anything (RULE-012)."""

    def __init__(self, measurement_store: Any, consumed: Optional[ConsumedFacts] = None) -> None:
        self._store = measurement_store
        self._consumed = consumed or ConsumedFacts()

    # --- verified-revenue aggregates (RULE-003: revenue_value is set ONLY on the ORDER_VERIFIED path) -----
    def verified_rows(self) -> Tuple[Any, ...]:
        # B4 (M6.2L): self-enforcing event_code filter (belt-and-suspenders with the store's materialize choke) —
        # a row counts as verified revenue ONLY when it is an ORDER_VERIFIED row carrying a set-once revenue_value.
        # So even a quote/draft row that (through store/materializer misuse) held a revenue_value contributes 0 to
        # Revenue Verified / ROAS (SMK-023). Every genuine verified row is an ORDER_VERIFIED event.
        return tuple(
            r for r in self._store.all()
            if r.revenue_value is not None and getattr(r, "event_code", None) == _ORDER_VERIFIED
        )

    def revenue_verified(self) -> float:
        return float(sum(r.revenue_value for r in self.verified_rows()))

    def verified_order_count(self) -> int:
        # one verified order per verified row (distinct order_code where present)
        codes = {r.order_code for r in self.verified_rows() if r.order_code}
        anon = sum(1 for r in self.verified_rows() if not r.order_code)
        return len(codes) + anon

    def crm_revenue(self) -> float:
        return float(sum(
            r.revenue_value for r in self.verified_rows()
            if str(_attr(r, "entry_channel")) == "CRM"
        ))

    def diamond_revenue(self) -> float:
        return float(sum(
            r.revenue_value for r in self.verified_rows()
            if _attr(r, "referral_link_id") or _attr(r, "diamond_id")
        ))

    def verified_boxes(self) -> Optional[int]:
        codes = [r.order_code for r in self.verified_rows() if r.order_code]
        if not codes:
            return None
        boxes = self._consumed.boxes_by_order
        # Fail-closed (adversarial review): require FULL coverage. Partial coverage would fabricate 0 boxes for
        # an unreported verified order (a verified order cannot genuinely have 0 boxes) and understate the metric.
        if not all(c in boxes for c in codes):
            return None                     # boxes not fully provided by Commerce -> fail-closed (never fabricated)
        return int(sum(boxes[c] for c in codes))

    # --- event-code counts (funnel numerators/denominators) ----------------------------------------------
    def event_count(self, event_code: str) -> int:
        return sum(1 for r in self._store.all() if r.event_code == event_code)

    # --- consumed pass-throughs (M6 reads, never computes) -----------------------------------------------
    def ads_spend(self) -> Optional[float]:
        return self._consumed.mapped_spend_total()

    def cod_orders(self) -> Optional[int]:
        return self._consumed.cod_orders

    def cod_fail(self) -> Optional[int]:
        return self._consumed.cod_fail

    def sample_verified_correlation(self) -> Optional[str]:
        """A masked example correlation_id from a verified row, for a metric's sample_evidence_ref (evidence-
        first). Masking is applied by the caller (kpi_metrics) via app.measurement.masking.mask."""
        rows = self.verified_rows()
        return rows[0].correlation_id if rows else None


def _attr(row: Any, key: str) -> Any:
    """Read a field from a verified row's materialized attribution_context mapping (M6.2E `as_stored`)."""
    ctx = getattr(row, "attribution_context", None)
    if isinstance(ctx, Mapping):
        return ctx.get(key)
    return None
