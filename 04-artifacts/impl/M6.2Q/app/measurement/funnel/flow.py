"""The doc §8 conversion-flow chain (extract L151–157) — event codes reproduced from canon, NONE invented.

The six flows Ads → Live → Comment → Messenger → Quote → Order → Verified, and the mapping of each doc §8/§10
event code to its `FlowStage`. Module 6 references these codes as measurement-time constants (they are validated
upstream at ingest against the Core event_registry, RULE-001); it adds none to the Phase-1 client allow-list and
invents none (RULE-001 / RULE-018).

Only ORDER_TO_VERIFIED is revenue-valid (RULE-003 / FAIL-001): a quote / order-created is a funnel stage, never
revenue (SMK-004).
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, Tuple


class FlowStage(str, Enum):
    """The six doc §8 flows, in order."""

    ADS_TO_LIVE = "ADS_TO_LIVE"                 # identity boundary (campaign/adset/ad/live_session_id); no event code
    LIVE_TO_COMMENT = "LIVE_TO_COMMENT"         # LIVE_VIEW, LIVE_COMMENT
    COMMENT_TO_MESSENGER = "COMMENT_TO_MESSENGER"   # MESSENGER_STARTED
    MESSENGER_TO_QUOTE = "MESSENGER_TO_QUOTE"   # AI_PROPOSAL_SENT, QUOTE_CART_CREATED, QUOTE_SNAPSHOT_CREATED, QUOTE_SENT
    QUOTE_TO_ORDER = "QUOTE_TO_ORDER"           # ORDER_CONFIRMATION_SENT, CUSTOMER_CONFIRMED_ORDER, ORDER_CREATED
    ORDER_TO_VERIFIED = "ORDER_TO_VERIFIED"     # ORDER_VERIFIED, PAYMENT_COMPLETED (if any)


# The ordered chain (doc §8 L151–157).
CHAIN: Tuple[FlowStage, ...] = (
    FlowStage.ADS_TO_LIVE,
    FlowStage.LIVE_TO_COMMENT,
    FlowStage.COMMENT_TO_MESSENGER,
    FlowStage.MESSENGER_TO_QUOTE,
    FlowStage.QUOTE_TO_ORDER,
    FlowStage.ORDER_TO_VERIFIED,
)

# doc §8/§10 event code -> flow stage. ADS_TO_LIVE carries no event code (identity boundary); it is measured by
# ad/live identity presence, not an event count (see funnel.py). Every code below is doc-canon (§8 table + §10
# Event Taxonomy), referenced not invented.
EVENT_STAGE: Dict[str, FlowStage] = {
    # Live → Comment
    "LIVE_VIEW": FlowStage.LIVE_TO_COMMENT,
    "LIVE_COMMENT": FlowStage.LIVE_TO_COMMENT,
    # Comment → Messenger
    "MESSENGER_STARTED": FlowStage.COMMENT_TO_MESSENGER,
    # Messenger → Quote
    "AI_PROPOSAL_SENT": FlowStage.MESSENGER_TO_QUOTE,
    "QUOTE_CART_CREATED": FlowStage.MESSENGER_TO_QUOTE,
    "QUOTE_SNAPSHOT_CREATED": FlowStage.MESSENGER_TO_QUOTE,
    "QUOTE_SENT": FlowStage.MESSENGER_TO_QUOTE,
    # Quote → Order
    "ORDER_CONFIRMATION_SENT": FlowStage.QUOTE_TO_ORDER,
    "CUSTOMER_CONFIRMED_ORDER": FlowStage.QUOTE_TO_ORDER,
    "ORDER_CREATED": FlowStage.QUOTE_TO_ORDER,
    # Order → Verified
    "ORDER_VERIFIED": FlowStage.ORDER_TO_VERIFIED,
    "PAYMENT_COMPLETED": FlowStage.ORDER_TO_VERIFIED,
}

# Only this stage is revenue-valid (RULE-003). Verified revenue is ORDER_VERIFIED; PAYMENT_COMPLETED is recorded
# "nếu có" per Core policy but the revenue figure Module 6 consumes is the set-once ORDER_VERIFIED revenue_value.
REVENUE_VALID_STAGE: FlowStage = FlowStage.ORDER_TO_VERIFIED
REVENUE_VALID_EVENT: str = "ORDER_VERIFIED"

# The doc §14 funnel-rate definitions (name, formula VERBATIM, numerator event code, denominator event code) —
# the SAME formulas kpi_metrics computes globally, re-applied per-session / per-Golden-Hour-state here (the grain
# is the new contribution; the definitions are reused). Fail-closed division (0/None denominator → None).
FUNNEL_RATE_SPECS: Tuple[Tuple[str, str, str, str], ...] = (
    ("Comment Rate", "LIVE_COMMENT / LIVE_VIEW", "LIVE_COMMENT", "LIVE_VIEW"),
    ("Inbox Rate", "MESSENGER_STARTED / LIVE_COMMENT", "MESSENGER_STARTED", "LIVE_COMMENT"),
    ("Quote Rate", "QUOTE_SENT / MESSENGER_STARTED", "QUOTE_SENT", "MESSENGER_STARTED"),
    ("Order Rate", "ORDER_CREATED / QUOTE_SENT", "ORDER_CREATED", "QUOTE_SENT"),
    ("Verified Rate", "ORDER_VERIFIED / ORDER_CREATED", "ORDER_VERIFIED", "ORDER_CREATED"),
)


def stage_for(event_code: Optional[str]) -> Optional[FlowStage]:
    """The funnel stage for a doc-canon event code, or None for an unrecognized code (fail-closed — an unknown
    code is never silently bucketed). Type-safe: a non-str is None."""
    if not isinstance(event_code, str):
        return None
    return EVENT_STAGE.get(event_code)
