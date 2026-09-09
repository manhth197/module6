"""The doc §9 growth groups + their valid signals (VERBATIM, MONITORING_REGISTER Phase-3 / extract L173–177).

Each growth group may be computed ONLY from its listed valid signals. Event codes (CRM_REORDER_SENT,
CRM_REORDER_ORDER_CREATED, DIAMOND_LEAD_CREATED, DIAMOND_REFERRAL_ORDER_VERIFIED, ORDER_VERIFIED) are doc §10 canon —
referenced as measurement-time constants (registry-validated upstream, RULE-001); Module 6 invents none (RULE-018)
and adds none to the Phase-1 client allow-list.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Tuple

# doc §10 CRM / Diamond / verified event codes (referenced, not invented)
CRM_REORDER_SENT = "CRM_REORDER_SENT"
CRM_REORDER_ORDER_CREATED = "CRM_REORDER_ORDER_CREATED"
DIAMOND_LEAD_CREATED = "DIAMOND_LEAD_CREATED"
DIAMOND_REFERRAL_ORDER_VERIFIED = "DIAMOND_REFERRAL_ORDER_VERIFIED"
ORDER_VERIFIED = "ORDER_VERIFIED"


class GrowthGroup(str, Enum):
    """The five doc §9 growth groups."""

    REPEAT_REORDER = "Repeat / Reorder"
    DORMANT_REACTIVATION = "Dormant / Reactivation"
    DIAMOND = "Diamond"
    VALUE_OPTIMIZATION = "Value Optimization"
    LEARNING_ENGINE = "Learning Engine"


# The VERBATIM doc §9 valid-signal set per group — the ONLY inputs each group's KPIs may use.
VALID_SIGNALS: Dict[GrowthGroup, Tuple[str, ...]] = {
    GrowthGroup.REPEAT_REORDER: ("CRM_REORDER_SENT", "CRM_REORDER_ORDER_CREATED", "ORDER_VERIFIED"),
    GrowthGroup.DORMANT_REACTIVATION: ("Dormant segment", "consent pass", "CRM eligibility pass", "order verified"),
    GrowthGroup.DIAMOND: ("DIAMOND_LEAD_CREATED", "referral_link_id", "DIAMOND_REFERRAL_ORDER_VERIFIED"),
    GrowthGroup.VALUE_OPTIMIZATION: ("High-value order", "boxes/order", "tier upgrade", "product affinity"),
    GrowthGroup.LEARNING_ENGINE: ("Verified business signals", "data quality pass"),
}

# The doc §9 KPI names per group (for reference / report labelling).
GROUP_KPIS: Dict[GrowthGroup, Tuple[str, ...]] = {
    GrowthGroup.REPEAT_REORDER: ("Repeat rate", "CRM Revenue", "AOV"),
    GrowthGroup.DORMANT_REACTIVATION: ("Reactivation rate", "CPA reactivation"),
    GrowthGroup.DIAMOND: ("Diamond lead rate", "Diamond Revenue", "commission-ready revenue"),
    GrowthGroup.VALUE_OPTIMIZATION: ("AOV", "CLV proxy", "boxes/order", "ads ratio reduction"),
    GrowthGroup.LEARNING_ENGINE: ("Candidate approval rate", "uplift", "drift violations"),
}
