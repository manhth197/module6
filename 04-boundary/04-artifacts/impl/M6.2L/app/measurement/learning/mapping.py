"""M6.2H — the doc §17 strategy mapping chain (extract 336): the spine that keeps Ads from running on gut feel.

`SKU/Product line → Persona → Behavior → Keyword → Creative Hook → Landing → CTA → Event → Verified Revenue`.
Every mapping is ANCHORED to a sellable SKU (LEX-005: every optimization tied to a sellable SKU + program +
Golden-Hour/24-7 policy + product public claim + brand wording). This is read-only reference data assembled from
canonical sources — it never writes pricing / program / member-right / CRM / Diamond / Golden-Hour / 24-7
(RULE-013/018). PII masked on export.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


class StrategyMappingViolation(Exception):
    """Raised when a mapping is not anchored to a sellable SKU (LEX-005)."""


@dataclass(frozen=True)
class StrategyMapping:
    """One link of the doc §17 chain. `sku_ref` (a sellable SKU) is REQUIRED; the rest are optional references to
    library entries / the measurement event / the verified-revenue row (framework). No Core-owned value is written."""

    sku_ref: str                                    # sellable SKU / product line (REQUIRED, LEX-005)
    persona: Optional[str] = None                   # ref to a Persona Library entry
    behavior: Optional[str] = None                  # ref to a Behavior Library entry
    keyword: Optional[str] = None                   # ref to a Keyword Library entry
    creative_hook: Optional[str] = None             # ref to a Creative Hook Library entry
    landing: Optional[str] = None                   # ref to a Landing/CTA Library entry
    cta: Optional[str] = None
    event_ref: Optional[str] = None                 # ref to an ads_measurement_event
    verified_revenue_ref: Optional[str] = None      # ref to the ORDER_VERIFIED revenue row (M6.2E), never a value

    def __post_init__(self) -> None:
        if not self.sku_ref:
            raise StrategyMappingViolation("a strategy mapping must be anchored to a sellable SKU (LEX-005)")

    def to_public(self) -> Dict[str, Any]:
        return {
            "sku_ref": self.sku_ref,
            "persona": self.persona,
            "behavior": self.behavior,
            "keyword": self.keyword,
            "creative_hook": self.creative_hook,
            "landing": self.landing,
            "cta": self.cta,
            "event_ref": self.event_ref,
            "verified_revenue_ref": self.verified_revenue_ref,
        }
