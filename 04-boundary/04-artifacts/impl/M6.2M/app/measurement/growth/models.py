"""Growth-report result models — frozen, read-only, data-only.

A `GrowthKpi` is one doc §9 growth KPI (value None when it cannot be computed from its valid signals — fail-closed,
never fabricated). A `GrowthReport` groups the KPIs by growth group. The values are aggregates (no PII); `to_public`
is a plain data mapping and carries NO write / trigger / send / commission field (RULE-012 / 019).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from app.measurement.growth.signals import GrowthGroup


@dataclass(frozen=True)
class GrowthKpi:
    """One doc §9 growth KPI. `value` is None when the valid signals are absent / a denominator is 0 (fail-closed)."""

    name: str
    group: GrowthGroup
    value: Optional[float]
    unit: str                                   # "VND" | "ratio" | "count" | ""
    source_signals: Tuple[str, ...]             # the doc §9 valid signals this KPI was computed from
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    note: Optional[str] = None                  # e.g. "fail-closed: no consumed cohort" (never raw PII)

    def to_public(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "group": self.group.value,
            "value": self.value,
            "unit": self.unit,
            "source_signals": list(self.source_signals),
            "numerator": self.numerator,
            "denominator": self.denominator,
            "note": self.note,
        }


@dataclass(frozen=True)
class GrowthReport:
    """The doc §9 growth report — the KPIs of all five groups. Read-only data; no trigger handle (RULE-012)."""

    kpis: Tuple[GrowthKpi, ...]

    def kpi(self, name: str) -> Optional[GrowthKpi]:
        for k in self.kpis:
            if k.name == name:
                return k
        return None

    def group(self, group: GrowthGroup) -> Tuple[GrowthKpi, ...]:
        return tuple(k for k in self.kpis if k.group is group)

    def to_public(self) -> Dict[str, Any]:
        return {"kpis": [k.to_public() for k in self.kpis]}
