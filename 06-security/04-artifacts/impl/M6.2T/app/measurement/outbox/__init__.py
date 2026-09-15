"""Outbox layer (M6.2C): transactional outbox stores, the enqueue seam, the send transport, and the two
dispatcher workers. External measurement/audience goes ONLY through an outbox row drained by a worker; the
runtime never sends (RULE-004). Staged: no real platform send ever (external_send=OFF)."""
