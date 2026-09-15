"""M6-CTR-018 GET /api/admin/ads/dashboard — framework-neutral, READ-ONLY request handler (M6.2F).

`handle_dashboard_request(query, deps)` reads the `DataMart` (a support view) and returns a `DashboardView` with
the 14 CTR-015 metrics + an overall data_quality_status. It NEVER writes, NEVER triggers CRM / pricing / Diamond /
scale (RULE-012, FAIL-005, SMK-010): `DashboardDeps` holds only the read-only mart — no store-writer, no
Transport, no trigger. Revenue figures are verified-only by construction (RULE-003 / FAIL-001, SMK-015). The
`query` is untrusted admin input (RULE-H03) — treated as DATA (optional filters), never executed. Traces/evidence
are PII-safe. No numeric threshold is applied (M6-OD-002 OPEN). The HTTP status mapping binds at the owner
integration step (M6-OD-011).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Mapping, Optional

from app.measurement.dashboard.data_mart import DataMart
from app.measurement.dashboard.kpi_metrics import compute_metrics
from app.measurement.dashboard.models import DashboardView, MetricResult


@dataclass
class DashboardDeps:
    """Read-only dependency container for the dashboard endpoint. Deliberately holds ONLY the support-view mart —
    no store writer, no Transport, no CRM/scale/trigger handle (RULE-004/012). The absence of those is asserted by
    a test (SMK-010)."""

    mart: DataMart


def _dashboard_data_quality(metrics: List[MetricResult]) -> str:
    """View-level Data Quality (doc §15 Dashboard + Verified-Revenue items): a metric that reports a VALUE must
    carry a source trace + sample evidence — a visual-only figure is a FAIL (doc §15 L308). Revenue figures are
    verified-only by construction (RULE-003), so no unverified revenue can be displayed. Fail-closed."""
    for m in metrics:
        if m.value is not None and not m.has_trace_and_evidence:
            return "FAIL"          # visual-only figure with no source trace
    return "PASS"


def handle_dashboard_request(
    query: Any, deps: DashboardDeps, *, now: Optional[datetime] = None
) -> DashboardView:
    # query is untrusted admin filter DATA (RULE-H03) — read-only; unknown keys ignored (forgiving seam).
    _ = query if isinstance(query, Mapping) else {}
    metrics = compute_metrics(deps.mart)      # verified-only revenue by construction (RULE-003)
    overall = _dashboard_data_quality(metrics)
    return DashboardView(metrics=metrics, overall_data_quality=overall, generated_at=now)
