"""Shared read helpers for the growth measurement — read-only over the M6-owned measurement store.

Reuses kpi_metrics' `_safe_div` (identical fail-closed division). No write path.
"""
from __future__ import annotations

from typing import Any, List, Mapping, Optional

from app.measurement.dashboard.kpi_metrics import _safe_div   # reuse the exact fail-closed division primitive

__all__ = ["_safe_div", "attribution_value", "verified_rows", "event_count", "is_crm_attributed",
           "has_referral_attribution"]


def attribution_value(row: Any, key: str) -> Any:
    """Read one field from a row's materialized attribution_context mapping (M6.2E `as_stored`)."""
    ctx = getattr(row, "attribution_context", None)
    if isinstance(ctx, Mapping):
        return ctx.get(key)
    return None


def verified_rows(store: Any) -> List[Any]:
    """The verified rows (set-once Zone-B revenue populated — the ORDER_VERIFIED path, RULE-003)."""
    return [r for r in store.all() if getattr(r, "revenue_value", None) is not None]


def event_count(store: Any, event_code: str) -> int:
    return sum(1 for r in store.all() if getattr(r, "event_code", None) == event_code)


def is_crm_attributed(row: Any) -> bool:
    """True iff the row's attribution entry_channel is CRM (doc §11 EntryChannel)."""
    return str(attribution_value(row, "entry_channel")) == "CRM"


def has_referral_attribution(row: Any) -> bool:
    """True iff the row carries Diamond referral attribution (referral_link_id or diamond_id)."""
    return bool(attribution_value(row, "referral_link_id") or attribution_value(row, "diamond_id"))
