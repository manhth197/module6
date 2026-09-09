"""M6.2I Phase-2 Golden Hour funnel — a DERIVED, READ-ONLY measurement projection.

This package MEASURES the doc §8 conversion machine (Ads → Live → Comment → Messenger → Quote → Order → Verified)
over the existing `ads_measurement_events` (CTR-001) + `ads_attribution_context` (CTR-002) stores. It owns NO new
table (doc §13 defines none — inventing one breaches RULE-018), operates NO live session (Gateway/Live's; RULE-013),
sends NOTHING, and counts revenue ONLY from ORDER_VERIFIED (RULE-003 / FAIL-001). Everything here is fail-closed.
"""
