"""Integration layer (M6.2D): the STAGED platform send discipline — hash policy (no raw PII), PII-safe payload
with a shared platform event_id for cross-platform dedup, platform result logs, and a staged transport that
builds+logs but NEVER sends (external_send=OFF). No real platform call, no connector (M6-OD-004), no invented
hash fields (M6-OD-003)."""
