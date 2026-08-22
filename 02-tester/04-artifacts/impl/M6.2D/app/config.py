"""Staged-posture constants for slice M6.2A.

These values are IMMUTABLE to the coder role (RULE-H01). No code path in this slice writes an enabling value
for them anywhere; the entrypoint and services only READ them.
"""
from __future__ import annotations

from typing import Final

# --- Immutable staged posture (RULE-H01) ---------------------------------------------------------
GLOBAL_GATEWAY_STATE: Final[str] = "BLOCKED"
PRODUCTION_FLAG: Final[str] = "OFF"
EXTERNAL_SEND: Final[str] = "OFF"          # egress is framework-only in M6.2A; nothing is ever sent

# --- PII masking format (RULE-014 / H02) ---------------------------------------------------------
# M6-OD-012 is OPEN; the pack-recommended default masked format is "abc***xy" (first 3 + *** + last 2).
MASK_INFIX: Final[str] = "***"
MASK_SHORT: Final[str] = "***"             # values too short to reveal any prefix/suffix are fully masked

# --- Outbox (M6.2C) ------------------------------------------------------------------------------
# The bounded-retry LIMIT is doc-mandated (doc 12 L252 "retry có giới hạn"); the numeric VALUE is operational
# config, NOT an owner-mandated value. No owner value invented; no enabling flag touched.
OUTBOX_MAX_RETRIES: Final[int] = 5

# --- Integration / hash policy (M6.2D) -----------------------------------------------------------
# RULE-014 / FAIL-008: no raw PII in any external payload/log. The hash MECHANISM is built here; the ratified
# permitted-send-fields policy is M6-OD-003 (OPEN, privacy/legal). Fail-closed: while NOT ratified, the payload
# builder emits EVERY identity field HASHED and NOTHING raw. This is NOT an enabling flag and NEVER makes a real
# send happen (external_send stays OFF); it only gates the raw-field allow-list.
MEASUREMENT_HASH_ALGO: Final[str] = "sha256"
HASH_POLICY_RATIFIED: Final[bool] = False   # M6-OD-003 OPEN -> no field may be sent raw (fail-closed)


def is_external_send_enabled() -> bool:
    """Always False in this slice — external send is OFF (staged). Kept as a single choke point."""
    return EXTERNAL_SEND == "ON"
