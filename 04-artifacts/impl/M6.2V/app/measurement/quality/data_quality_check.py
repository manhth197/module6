"""M6-CTR-012 ads_data_quality_check — the 8 doc §15 Data Quality Gate items + a worst-status roll-up.

Gate items (verbatim, doc §15): Event Registry, Consent, Dedup, Identity, Attribution, Verified Revenue,
Suppression, Dashboard. Each item is PASS / HOLD / FAIL (nothing beyond the three states — the worker's
must-not-do, doc §9). The overall status is the WORST item (FAIL > HOLD > PASS, config.DQ_STATUS_ORDER). A HOLD/
FAIL overall is never scale evidence (RULE-009). PII-safe: `detail`/`evidence_ref` carry machine reasons /
masked refs only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from app import config
from app.measurement.models.measurement_event import DataQualityStatus

# The DQ gate uses the same PASS/HOLD/FAIL vocabulary as the measurement row's data_quality_status.
GateStatus = DataQualityStatus


class GateItem(str, Enum):
    """The 8 Data Quality Gate items (doc §15, verbatim order)."""

    EVENT_REGISTRY = "Event Registry"
    CONSENT = "Consent"
    DEDUP = "Dedup"
    IDENTITY = "Identity"
    ATTRIBUTION = "Attribution"
    VERIFIED_REVENUE = "Verified Revenue"
    SUPPRESSION = "Suppression"
    DASHBOARD = "Dashboard"


@dataclass(frozen=True)
class GateItemResult:
    item: GateItem
    status: GateStatus
    detail: str                                 # machine reason (no raw PII)
    evidence_ref: Optional[str] = None          # masked ref, if any


def worst_status(statuses) -> GateStatus:
    """Worst of a set of PASS/HOLD/FAIL per config.DQ_STATUS_ORDER (FAIL dominates HOLD dominates PASS).
    Empty ⇒ fail-closed HOLD (never PASS by default)."""
    order = config.DQ_STATUS_ORDER
    worst = GateStatus.PASS
    seen = False
    for s in statuses:
        seen = True
        if order.index(s.value) > order.index(worst.value):
            worst = s
    return worst if seen else GateStatus.HOLD


@dataclass(frozen=True)
class AdsDataQualityCheck:
    """M6-CTR-012 output for one subject (a measurement row / a dashboard view). `overall` is worst-of-items."""

    items: Tuple[GateItemResult, ...]
    overall: GateStatus
    subject_event_id: Optional[str] = None

    @classmethod
    def from_items(cls, items, *, subject_event_id: Optional[str] = None) -> "AdsDataQualityCheck":
        items = tuple(items)
        return cls(items=items, overall=worst_status([i.status for i in items]), subject_event_id=subject_event_id)

    def item(self, item: GateItem) -> Optional[GateItemResult]:
        for r in self.items:
            if r.item is item:
                return r
        return None

    def to_public(self) -> dict:
        return {
            "subject_event_id": self.subject_event_id,
            "overall": self.overall.value,
            "items": [
                {"item": r.item.value, "status": r.status.value, "detail": r.detail, "evidence_ref": r.evidence_ref}
                for r in self.items
            ],
        }
