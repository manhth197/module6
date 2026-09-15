"""The 10 doc §22 evidence categories + each category's mandatory-content requirement keys.

Content is an English gloss of the doc §22 "Nội dung bắt buộc" column (extract L419–430); the category names and
requirement keys are faithful, and category 1 keeps the "Screenshot/API/DB record" proof-form to match the slice
exit-gate (M6.2K.md). A category is COMPLETE only when EVERY required key is present with a non-empty evidence ref;
a missing key ⇒ INCOMPLETE (fail-closed, FAIL-007).
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Tuple


class EvidenceCategory(str, Enum):
    """The 10 doc §22 evidence categories (verbatim order)."""

    EVENT_REGISTRY = "Event Registry"
    CONSENT = "Consent"
    OUTBOX = "Outbox"
    DEDUP = "Dedup"
    ATTRIBUTION = "Attribution"
    DASHBOARD = "Dashboard"
    SCALE_GATE = "Scale Gate"
    LEARNING = "Learning"
    SECURITY_PRIVACY = "Security/Privacy"
    SMOKE_REPORT = "Smoke Report"


# The mandatory content of each category as requirement KEYS (doc §22, glossed). All keys must be present with a
# non-empty evidence ref for the category to be COMPLETE.
CATEGORY_MANDATORY: Dict[EvidenceCategory, Tuple[str, ...]] = {
    # category 1 keeps the doc/exit-gate proof-form "Screenshot/API/DB record proving event codes, owner, policy"
    EvidenceCategory.EVENT_REGISTRY: ("screenshot_api_db_record", "event_codes", "owner", "policy"),
    EvidenceCategory.CONSENT: ("consent_pass", "consent_fail_closed", "opt_out_handling"),
    EvidenceCategory.OUTBOX: ("queued", "sent", "retry", "error", "dead_letter"),
    EvidenceCategory.DEDUP: ("pixel_capi_offline_duplicate_handled",),
    EvidenceCategory.ATTRIBUTION: ("order_verified_trace_campaign_adset_ad_page_live_comment_messenger",),
    EvidenceCategory.DASHBOARD: ("revenue_verified", "roas", "cpa", "aov", "correct_sources"),
    EvidenceCategory.SCALE_GATE: ("pass_hold_fail", "owner_approval_flow"),
    EvidenceCategory.LEARNING: ("candidate", "review", "approve_reject_hold", "rollback"),
    EvidenceCategory.SECURITY_PRIVACY: ("no_raw_pii", "consent", "hash_policy", "access_control"),
    EvidenceCategory.SMOKE_REPORT: ("smoke_results", "correlation_id", "evidence_id"),
}

# Human-readable mandatory-content description per category (doc §22 gloss) — for the owner-review package.
CATEGORY_DESCRIPTION: Dict[EvidenceCategory, str] = {
    EvidenceCategory.EVENT_REGISTRY: "Screenshot/API/DB record proving event codes, owner, policy",
    EvidenceCategory.CONSENT: "consent pass / fail-closed cases, opt-out handling",
    EvidenceCategory.OUTBOX: "conversion/audience outbox queued, sent, retry, error, dead-letter",
    EvidenceCategory.DEDUP: "Pixel/CAPI/Offline duplicate handled correctly",
    EvidenceCategory.ATTRIBUTION: "ORDER_VERIFIED traced back campaign/adset/ad/page/live/comment/Messenger",
    EvidenceCategory.DASHBOARD: "Revenue Verified / ROAS / CPA / AOV from correct sources",
    EvidenceCategory.SCALE_GATE: "PASS/HOLD/FAIL with owner approval flow",
    EvidenceCategory.LEARNING: "candidate -> review -> approve/reject/hold -> rollback",
    EvidenceCategory.SECURITY_PRIVACY: "no raw PII, consent, hash policy, access control",
    EvidenceCategory.SMOKE_REPORT: "P0 smoke result with correlation_id + evidence_id",
}
