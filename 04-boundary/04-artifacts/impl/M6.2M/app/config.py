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

# --- Attribution / scale evidence (M6.2E) --------------------------------------------------------
# M6-OD-005 (attribution model final choice) is OPEN. Multi-model attribution is DISPLAYED (first_touch AND
# last_touch recorded), but NO model is scale-authoritative until the owner ratifies one. Fail-closed: while this
# is False the materializer marks NO row as scale evidence, whatever its confidence. This is NOT an enabling flag
# and never triggers a scale action (global_gateway_state stays BLOCKED; the M6.2G Scale-Gate re-gate governs scale).
SCALE_MODEL_RATIFIED: Final[bool] = False
# RULE-009 data-quality bar: only a snapshot at or above this confidence (with no conflict) may EVER be scale
# evidence. HIGH here — LOW/MEDIUM or any conflict is never scale evidence.
SCALE_EVIDENCE_MIN_CONFIDENCE: Final[str] = "HIGH"

# --- Dashboard / Data Quality Gate (M6.2F) -------------------------------------------------------
# Worst-status roll-up order for the Data Quality Gate (doc §15): FAIL dominates HOLD dominates PASS. The overall
# ads_data_quality_check status is the worst item status. Index 0 = best, last = worst.
DQ_STATUS_ORDER: Final[tuple] = ("PASS", "HOLD", "FAIL")
# Alert / scale thresholds (CPA/ROAS/AOV/verified-rate, duplicate rate, ...) are owner decision M6-OD-002 (OPEN).
# The pack invents NONE. The KPI dashboard reports VALUES only; the Data Quality Gate is STRUCTURAL (the 8 doc §15
# items), needing no numeric threshold. Fail-closed: no threshold defined here, so no alert/scale is triggered.
DASHBOARD_ALERT_THRESHOLDS_DEFINED: Final[bool] = False   # M6-OD-002 OPEN -> no thresholds (out of scope, M6.2G)

# --- Scale Gate (M6.2G) --------------------------------------------------------------------------
# RULE-010 / FAIL-006: Module 6 NEVER executes a scale. It computes conditions and creates an inert
# ads_scale_request (budget_cap + rollback_condition are request FIELDS, not actions) for OWNER review; raising a
# budget, enabling a campaign, opening audience scale, or publishing an optimization is OWNER-only, performed
# OUTSIDE Module 6 and gated by production_flag=OFF. This is a single explicit choke asserting no executable path
# exists in this module; it is IMMUTABLE here and never flipped. There is deliberately no code that reads it to
# act — it exists so a test can assert the module ships no scale-execution path.
SCALE_EXECUTION_ENABLED: Final[bool] = False

# --- Learning engine / ADS Strategy Libraries (M6.2H) --------------------------------------------
# RULE-011 / LEX-006 / FAIL-006: the learning engine NEVER auto-publishes. Candidates land in a review queue for
# owner/marketing approval; a guarded auto-publish would require an owner-ratified safe range (M6-OD-006, OPEN).
# This is a single explicit choke asserting no auto-publish path exists in this module; there is deliberately no
# code that reads it to act. IMMUTABLE here, never flipped.
LEARNING_AUTOPUBLISH_ENABLED: Final[bool] = False
# M6-OD-007 (persona/keyword/hook content fill) is OPEN -> the strategy libraries stay FRAMEWORK-ONLY: the machine
# never fabricates origin strategy (LEX-006). A library entry seeds from a canonical source but carries NO
# machine-generated content while this is False. Fail-closed.
LEARNING_CONTENT_FILL_ENABLED: Final[bool] = False
# M6-OD-006 (guarded auto-publish safe range) is OPEN -> no safe range is defined, so the guarded-publish path is
# BLOCKED and a candidate's safe-range status is fail-closed UNKNOWN (never WITHIN by default). The pack invents no
# safe-range values. SMK-011 boundary values depend on this decision.
LEARNING_SAFE_RANGE_RATIFIED: Final[bool] = False


def is_external_send_enabled() -> bool:
    """Always False in this slice — external send is OFF (staged). Kept as a single choke point."""
    return EXTERNAL_SEND == "ON"
