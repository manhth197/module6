"""Attribution layer (M6.2E): resolver (M6-CTR-002) + materializer (M6-CTR-023) + adjustment-record path.

Resolve the source chain of a verified conversion into an `ads_attribution_context`; materialize it SET-ONCE
into Zone B of `ads_measurement_events` (revenue only from ORDER_VERIFIED, RULE-003; immutable after verify,
RULE-008); missing / conflicting sources degrade to LOW / a conflict status and are NEVER scale evidence
(RULE-009). No commission is ever computed here (RULE-019). Nothing sends; nothing scales.
"""
