"""Dashboard result models (M6.2F, CTR-015 / CTR-025 evidence discipline).

Each `MetricResult` carries its VALUE plus a `source_trace` (the inputs + the locked formula it came from) and a
`sample_evidence_ref` (a masked example correlation/event id). This makes the dashboard EVIDENCE-FIRST: a metric
with no trace/evidence is a Dashboard Data-Quality FAIL (doc §15 L308 "Dashboard chỉ là visual không có source
trace"). Values are numbers or None (fail-closed when a denominator is zero / a consumed input is absent — never
fabricated). No numeric alert threshold is attached (M6-OD-002 OPEN).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class MetricResult:
    """One KPI metric (CTR-015). `value` is None when it cannot be computed (zero denominator / missing consumed
    input) — fail-closed, never a fabricated number. `formula` is the locked doc §14 formula verbatim."""

    name: str
    formula: str
    value: Optional[float]
    unit: str                                   # "VND" | "ratio" | "count" | "" (dimensionless)
    source_trace: str                           # inputs + formula that produced value (no raw PII)
    sample_evidence_ref: Optional[str] = None   # masked example correlation_id/event_id (evidence-first)
    revenue_bearing: bool = False               # True for verified-only revenue metrics (RULE-003)

    @property
    def has_trace_and_evidence(self) -> bool:
        """Dashboard DQ item (doc §15): a metric is trace-backed only if it carries BOTH a source trace and a
        sample evidence ref. A visual-only metric (no trace) is a FAIL."""
        return bool(self.source_trace) and self.sample_evidence_ref is not None


@dataclass(frozen=True)
class DashboardView:
    """The read-only dashboard payload (CTR-018 response). Holds the 14 metrics + the overall data_quality_status
    (worst of the DQ gate items) + a generated_at stamp. Never carries a write/trigger handle (RULE-012)."""

    metrics: List[MetricResult]
    overall_data_quality: str                   # "PASS" | "HOLD" | "FAIL"
    generated_at: Optional[datetime] = None
    notes: Dict[str, Any] = field(default_factory=dict)

    def metric(self, name: str) -> Optional[MetricResult]:
        for m in self.metrics:
            if m.name == name:
                return m
        return None

    def to_public(self) -> Dict[str, Any]:
        """Export view (already PII-safe — traces/evidence are masked at construction)."""
        return {
            "overall_data_quality": self.overall_data_quality,
            "generated_at": self.generated_at.isoformat() if self.generated_at is not None else None,
            "metrics": [
                {
                    "name": m.name,
                    "formula": m.formula,
                    "value": m.value,
                    "unit": m.unit,
                    "source_trace": m.source_trace,
                    "sample_evidence_ref": m.sample_evidence_ref,
                    "revenue_bearing": m.revenue_bearing,
                }
                for m in self.metrics
            ],
            "notes": dict(self.notes),
        }
