"""M6.2J `GrowthReportBuilder` — the doc §9 growth-KPI assembler (read-only, measure-only).

Computes the five doc §9 growth groups' KPIs, each ONLY from its listed valid signals (fail-closed to None when a
signal is absent / a denominator is 0 — never fabricated). Sources:
  * Repeat/Reorder — CRM Revenue + Repeat rate from `CrmReorderMeasurement` (gated), AOV from the Data Mart.
  * Dormant/Reactivation — Reactivation rate + CPA from `ReactivationMeasurement`.
  * Diamond — Diamond lead rate + Diamond Revenue + commission-ready revenue from `DiamondReferralMeasurement`
    (commission MEASURED-not-computed, RULE-019).
  * Value Optimization — AOV + boxes/order from the Data Mart; CLV proxy + ads-ratio-reduction from consumed signals.
  * Learning Engine — approval rate from the M6.2H review queue (review_state), uplift from verified business
    signals (consumed cohort verified outcomes), drift violations from the Data Quality Gate (measurement rows whose
    data_quality_status is FAIL).

The Data Mart is READ as a support view (RULE-012); this builder exposes NO trigger / send / commission method.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from app.measurement.growth.crm import CrmReorderMeasurement
from app.measurement.growth.diamond import DiamondReferralMeasurement
from app.measurement.growth.models import GrowthKpi, GrowthReport
from app.measurement.growth.reactivation import ReactivationMeasurement
from app.measurement.growth.reads import _safe_div
from app.measurement.growth.signals import VALID_SIGNALS, GrowthGroup
from app.measurement.models.measurement_event import DataQualityStatus


@dataclass(frozen=True)
class GrowthConsumed:
    """Builder-level CONSUMED signals. All optional / fail-closed (absent ⇒ the dependent KPI is None)."""

    dormant_segment_id: Optional[str] = None
    uplift_treatment_revenue: Optional[float] = None   # verified business signal (treatment cohort)
    uplift_baseline_revenue: Optional[float] = None    # verified business signal (baseline cohort)
    clv_proxy: Optional[float] = None                  # consumed value-opt signal
    ads_ratio_current: Optional[float] = None          # ads/revenue ratio now (for ads-ratio-reduction)
    ads_ratio_baseline: Optional[float] = None         # ads/revenue ratio baseline


def _kpi(name, group, value, unit, *, num=None, den=None, note=None) -> GrowthKpi:
    return GrowthKpi(name=name, group=group, value=value, unit=unit,
                     source_signals=VALID_SIGNALS[group], numerator=num, denominator=den, note=note)


class GrowthReportBuilder:
    """Assemble the doc §9 growth report. Compose with the group measurements + the Data Mart support view."""

    def __init__(
        self,
        data_mart: Any,
        crm: CrmReorderMeasurement,
        diamond: DiamondReferralMeasurement,
        reactivation: ReactivationMeasurement,
        *,
        review_queue: Any = None,
        measurement_store: Any = None,
        consumed: Optional[GrowthConsumed] = None,
    ) -> None:
        self._mart = data_mart
        self._crm = crm
        self._diamond = diamond
        self._reactivation = reactivation
        self._queue = review_queue
        self._store = measurement_store
        self._c = consumed or GrowthConsumed()

    # --- shared Data Mart aggregates (reuse the support view) ---------------------------------------
    def _aov(self) -> Optional[float]:
        return _safe_div(self._mart.revenue_verified(), self._mart.verified_order_count())

    def _boxes_per_order(self) -> Optional[float]:
        return _safe_div(self._mart.verified_boxes(), self._mart.verified_order_count())

    # --- Learning-Engine KPIs ----------------------------------------------------------------------
    def _candidate_approval_rate(self) -> Optional[float]:
        """approved / total candidates in the M6.2H review queue (fail-closed; no queue / no candidates → None)."""
        if self._queue is None:
            return None
        cands = self._queue.all()
        if not cands:
            return None
        approved = sum(1 for c in cands if str(getattr(getattr(c, "review_state", None), "value", "")) == "APPROVED")
        return _safe_div(approved, len(cands))

    def _uplift(self) -> Optional[float]:
        """uplift = (treatment - baseline) / baseline over CONSUMED verified-business-signal cohorts (fail-closed:
        absent cohort or 0 baseline → None). Module 6 never fabricates a cohort."""
        t, b = self._c.uplift_treatment_revenue, self._c.uplift_baseline_revenue
        if t is None or b is None:
            return None
        return _safe_div(t - b, b)

    def _drift_violations(self) -> Optional[float]:
        """Data-Quality drift = count of measurement rows whose data_quality_status is FAIL (from the DQ gate).
        Fail-closed: no store wired → None (not 0)."""
        if self._store is None:
            return None
        return float(sum(1 for r in self._store.all()
                         if getattr(r, "data_quality_status", None) is DataQualityStatus.FAIL))

    def _ads_ratio_reduction(self) -> Optional[float]:
        cur, base = self._c.ads_ratio_current, self._c.ads_ratio_baseline
        if cur is None or base is None:
            return None
        return _safe_div(base - cur, base)     # reduction as a fraction of the baseline ratio

    # --- the full doc §9 report --------------------------------------------------------------------
    def build(self) -> GrowthReport:
        g = GrowthGroup
        seg = self._c.dormant_segment_id
        aov = self._aov()
        # Dormant/Reactivation KPIs need BOTH a named dormant segment AND a wired reactivation measurement.
        # Guard on the dependency too (mirrors the queue/store guards) — else a named-segment-but-unwired call
        # would crash instead of failing closed to None.
        have_react = bool(seg) and self._reactivation is not None
        react_rate = self._reactivation.reactivation_rate(seg) if have_react else None
        react_cpa = self._reactivation.cpa_reactivation(seg) if have_react else None
        react_note = None if have_react else "fail-closed: no dormant segment / reactivation not wired"
        # Value-opt / uplift: base the fail-closed note on the COMPUTED value (a missing numerator or a 0 baseline
        # also yields None via _safe_div), not on a single operand.
        uplift_v = self._uplift()
        ads_red_v = self._ads_ratio_reduction()
        kpis: List[GrowthKpi] = [
            # 1. Repeat / Reorder
            _kpi("Repeat rate", g.REPEAT_REORDER, self._crm.repeat_rate(), "ratio"),
            _kpi("CRM Revenue", g.REPEAT_REORDER, self._crm.crm_revenue(), "VND"),
            _kpi("AOV", g.REPEAT_REORDER, aov, "VND"),
            # 2. Dormant / Reactivation (None when no dormant segment / reactivation not wired — fail-closed)
            _kpi("Reactivation rate", g.DORMANT_REACTIVATION, react_rate, "ratio", note=react_note),
            _kpi("CPA reactivation", g.DORMANT_REACTIVATION, react_cpa, "VND", note=react_note),
            # 3. Diamond
            _kpi("Diamond lead rate", g.DIAMOND, self._diamond.diamond_lead_rate(), "ratio"),
            _kpi("Diamond Revenue", g.DIAMOND, self._diamond.diamond_revenue(), "VND"),
            _kpi("commission-ready revenue", g.DIAMOND, self._diamond.commission_ready_revenue(), "VND",
                 note="verified commission-ELIGIBLE revenue; NO commission computed (RULE-019, Finance owns)"),
            # 4. Value Optimization (AOV is doc-listed in BOTH group 1 and group 4; disambiguate by group)
            _kpi("AOV", g.VALUE_OPTIMIZATION, aov, "VND"),
            _kpi("CLV proxy", g.VALUE_OPTIMIZATION, self._c.clv_proxy, "VND",
                 note=None if self._c.clv_proxy is not None else "fail-closed: no consumed CLV signal"),
            _kpi("boxes/order", g.VALUE_OPTIMIZATION, self._boxes_per_order(), "ratio"),
            _kpi("ads ratio reduction", g.VALUE_OPTIMIZATION, ads_red_v, "ratio",
                 note=None if ads_red_v is not None else "fail-closed: no/zero consumed ads-ratio signal"),
            # 5. Learning Engine
            _kpi("Candidate approval rate", g.LEARNING_ENGINE, self._candidate_approval_rate(), "ratio"),
            _kpi("uplift", g.LEARNING_ENGINE, uplift_v, "ratio",
                 note=None if uplift_v is not None else "fail-closed: no/zero consumed cohort"),
            _kpi("drift violations", g.LEARNING_ENGINE, self._drift_violations(), "count"),
        ]
        return GrowthReport(kpis=tuple(kpis))
