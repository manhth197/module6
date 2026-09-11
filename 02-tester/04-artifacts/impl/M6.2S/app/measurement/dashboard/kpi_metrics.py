"""M6-CTR-015 KPI metrics — the 14 doc §14 metrics, FORMULAS VERBATIM (registers/MONITORING_REGISTER).

`compute_metrics(mart)` returns the 14 `MetricResult`s over a read-only `DataMart`. Revenue-bearing metrics
(Revenue Verified, ROAS, CPA, AOV, Boxes/Order, CRM Revenue, Diamond Revenue) source ONLY the verified Zone-B
revenue (RULE-003 / FAIL-001) — a quote / order-draft is never revenue (SMK-004/005/015). Every division is
fail-closed: a zero (or missing) denominator yields value None, never a crash and never a fabricated number.
No numeric alert threshold is applied (M6-OD-002 OPEN). Each result carries a source_trace + a PII-safe
sample_evidence_ref (evidence-first, doc §15 Dashboard item).
"""
from __future__ import annotations

from typing import List, Optional

from app.measurement.dashboard.data_mart import DataMart
from app.measurement.dashboard.models import MetricResult
from app.measurement.masking import mask


def _safe_div(num: Optional[float], den: Optional[float]) -> Optional[float]:
    """Fail-closed division: None if either operand is None or the denominator is zero."""
    if num is None or den is None or den == 0:
        return None
    return float(num) / float(den)


def _revenue_evidence(mart: DataMart) -> Optional[str]:
    corr = mart.sample_verified_correlation()
    return f"ame:verified;corr={mask(corr)}" if corr else None


def _count_evidence(*pairs) -> str:
    return "ame:counts;" + ";".join(f"{name}={n}" for name, n in pairs)


def compute_metrics(mart: DataMart) -> List[MetricResult]:
    revenue_verified = mart.revenue_verified()
    verified_orders = mart.verified_order_count()
    n_order_verified = mart.event_count("ORDER_VERIFIED")
    ads_spend = mart.ads_spend()
    verified_boxes = mart.verified_boxes()
    rev_ev = _revenue_evidence(mart)

    # funnel counts
    live_view = mart.event_count("LIVE_VIEW")
    live_comment = mart.event_count("LIVE_COMMENT")
    messenger = mart.event_count("MESSENGER_STARTED")
    quote_sent = mart.event_count("QUOTE_SENT")
    order_created = mart.event_count("ORDER_CREATED")
    cod_orders = mart.cod_orders()
    cod_fail = mart.cod_fail()

    metrics: List[MetricResult] = [
        MetricResult(
            name="Ads Spend", formula="Từ Ads platform / approved spend import", value=ads_spend, unit="VND",
            source_trace="consumed: approved spend import (mapped campaign/adset/ad only)",
            sample_evidence_ref="consumed:ads_spend;mapped_only=true",
        ),
        MetricResult(
            name="Revenue Verified", formula="SUM(verified_revenue)", value=revenue_verified, unit="VND",
            source_trace="SUM(revenue_value) over ORDER_VERIFIED rows (Zone-B set-once, RULE-003)",
            sample_evidence_ref=rev_ev, revenue_bearing=True,
        ),
        MetricResult(
            name="ROAS", formula="Revenue Verified / Ads Spend", value=_safe_div(revenue_verified, ads_spend),
            unit="ratio",
            source_trace=f"Revenue Verified={revenue_verified} / Ads Spend={ads_spend} (verified-only, RULE-003)",
            sample_evidence_ref=rev_ev, revenue_bearing=True,
        ),
        MetricResult(
            name="CPA", formula="Ads Spend / number_of_ORDER_VERIFIED",
            value=_safe_div(ads_spend, n_order_verified), unit="VND",
            source_trace=f"Ads Spend={ads_spend} / number_of_ORDER_VERIFIED={n_order_verified}",
            sample_evidence_ref=_count_evidence(("ORDER_VERIFIED", n_order_verified)), revenue_bearing=True,
        ),
        MetricResult(
            name="AOV", formula="Revenue Verified / verified_orders",
            value=_safe_div(revenue_verified, verified_orders), unit="VND",
            source_trace=f"Revenue Verified={revenue_verified} / verified_orders={verified_orders}",
            sample_evidence_ref=rev_ev, revenue_bearing=True,
        ),
        MetricResult(
            name="Boxes per Order", formula="Verified boxes / verified_orders",
            value=_safe_div(verified_boxes, verified_orders), unit="ratio",
            source_trace=f"Verified boxes={verified_boxes} (consumed) / verified_orders={verified_orders}",
            sample_evidence_ref=_count_evidence(("verified_orders", verified_orders)), revenue_bearing=True,
        ),
        MetricResult(
            name="Comment Rate", formula="LIVE_COMMENT / LIVE_VIEW",
            value=_safe_div(live_comment, live_view), unit="ratio",
            source_trace=f"LIVE_COMMENT={live_comment} / LIVE_VIEW={live_view}",
            sample_evidence_ref=_count_evidence(("LIVE_COMMENT", live_comment), ("LIVE_VIEW", live_view)),
        ),
        MetricResult(
            name="Inbox Rate", formula="MESSENGER_STARTED / LIVE_COMMENT",
            value=_safe_div(messenger, live_comment), unit="ratio",
            source_trace=f"MESSENGER_STARTED={messenger} / LIVE_COMMENT={live_comment}",
            sample_evidence_ref=_count_evidence(("MESSENGER_STARTED", messenger), ("LIVE_COMMENT", live_comment)),
        ),
        MetricResult(
            name="Quote Rate", formula="QUOTE_SENT / MESSENGER_STARTED",
            value=_safe_div(quote_sent, messenger), unit="ratio",
            source_trace=f"QUOTE_SENT={quote_sent} / MESSENGER_STARTED={messenger}",
            sample_evidence_ref=_count_evidence(("QUOTE_SENT", quote_sent), ("MESSENGER_STARTED", messenger)),
        ),
        MetricResult(
            name="Order Rate", formula="ORDER_CREATED / QUOTE_SENT",
            value=_safe_div(order_created, quote_sent), unit="ratio",
            source_trace=f"ORDER_CREATED={order_created} / QUOTE_SENT={quote_sent}",
            sample_evidence_ref=_count_evidence(("ORDER_CREATED", order_created), ("QUOTE_SENT", quote_sent)),
        ),
        MetricResult(
            name="Verified Rate", formula="ORDER_VERIFIED / ORDER_CREATED",
            value=_safe_div(n_order_verified, order_created), unit="ratio",
            source_trace=f"ORDER_VERIFIED={n_order_verified} / ORDER_CREATED={order_created}",
            sample_evidence_ref=_count_evidence(("ORDER_VERIFIED", n_order_verified), ("ORDER_CREATED", order_created)),
        ),
        MetricResult(
            name="COD Fail Rate", formula="COD fail / COD orders", value=_safe_div(cod_fail, cod_orders),
            unit="ratio", source_trace=f"COD fail={cod_fail} (consumed) / COD orders={cod_orders} (consumed)",
            sample_evidence_ref="consumed:cod",
        ),
        MetricResult(
            name="CRM Revenue", formula="Verified revenue từ CRM attribution", value=mart.crm_revenue(),
            unit="VND",
            source_trace="SUM(revenue_value) over verified rows where attribution entry_channel=CRM (RULE-003)",
            sample_evidence_ref=rev_ev, revenue_bearing=True,
        ),
        MetricResult(
            name="Diamond Revenue", formula="Verified revenue từ referral/Diamond attribution",
            value=mart.diamond_revenue(), unit="VND",
            source_trace="SUM(revenue_value) over verified rows with referral_link_id/diamond_id (RULE-003; "
                         "NO commission computed — Finance owns, RULE-019)",
            sample_evidence_ref=rev_ev, revenue_bearing=True,
        ),
    ]
    return metrics
