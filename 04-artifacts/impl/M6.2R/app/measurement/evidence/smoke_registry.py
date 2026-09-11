"""The canonical P0 smoke registry — the 18 smoke ids (doc §21 + proposed hardening), scenario/expected verbatim.

SMK-001..015 are owner smokes (doc §21 P0 matrix); SMK-016/017/018 are `proposed` (HARDENING — owner review) and
require EITHER an executed result OR a recorded owner waiver at the exit gate. Each smoke binds to its test file(s)
by the `test_smk_<nnn>_*` prefix under `tests/smoke/`. Module 6 re-runs these; it invents no smoke and re-authors
none (the TESTER executes, RULE-015).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple


class SmokeStatus(str, Enum):
    OWNER = "owner"          # doc §21 P0 matrix (mandatory)
    PROPOSED = "proposed"    # HARDENING — executed OR owner-waived


@dataclass(frozen=True)
class SmokeSpec:
    """One P0 smoke's canonical spec. Scenario/expected are quoted from SMOKE_REGISTER (doc §21, verbatim)."""

    smoke_id: str
    alias: str               # the owner document's original id (ADS-P0-xxx)
    scenario: str            # Kịch bản (verbatim)
    expected: str            # Kết quả phải đạt (verbatim)
    status: SmokeStatus
    test_glob: str           # bound test files: tests/smoke/<test_glob>


def _spec(n: int, alias: str, scenario: str, expected: str, status: SmokeStatus) -> SmokeSpec:
    sid = f"M6-SMK-{n:03d}"
    return SmokeSpec(sid, alias, scenario, expected, status, f"test_smk_{n:03d}_*.py")


# The 18 P0 smokes (SMOKE_REGISTER; scenario/expected verbatim from doc §21 + the proposed additions).
SMOKE_REGISTRY: Tuple[SmokeSpec, ...] = (
    _spec(1, "ADS-P0-001", "Event không có trong event_registry", "Reject/HOLD, audit rõ", SmokeStatus.OWNER),
    _spec(2, "ADS-P0-002", "Event hợp lệ nhưng thiếu consent", "Không external measurement, không audience sync", SmokeStatus.OWNER),
    _spec(3, "ADS-P0-003", "Duplicate Pixel/CAPI/Offline", "Dedup, không double count", SmokeStatus.OWNER),
    _spec(4, "ADS-P0-004", "Quote được tạo nhưng chưa order", "Không revenue, không ROAS", SmokeStatus.OWNER),
    _spec(5, "ADS-P0-005", "Order Draft / Order Created chưa verified", "Không tính Revenue Verified", SmokeStatus.OWNER),
    _spec(6, "ADS-P0-006", "ORDER_VERIFIED có campaign/adset/ad đầy đủ", "ROAS/CPA/AOV dashboard cập nhật", SmokeStatus.OWNER),
    _spec(7, "ADS-P0-007", "ORDER_VERIFIED thiếu source", "Revenue vẫn lưu, attribution confidence LOW/HOLD", SmokeStatus.OWNER),
    _spec(8, "ADS-P0-008", "CRM opt-out", "Không sync CRM audience/CRM event outbound", SmokeStatus.OWNER),
    _spec(9, "ADS-P0-009", "Recall/Sale Lock active", "Scale Gate FAIL/HOLD", SmokeStatus.OWNER),
    _spec(10, "ADS-P0-010", "Data Mart tạo trigger CRM/scale", "Fail - Data Mart chỉ support view", SmokeStatus.OWNER),
    _spec(11, "ADS-P0-011", "Learning candidate ngoài safe range", "Hold review, không publish", SmokeStatus.OWNER),
    _spec(12, "ADS-P0-012", "Scale request không owner approval", "Không scale", SmokeStatus.OWNER),
    _spec(13, "ADS-P0-013", "Live/Comment/Messenger chain", "Trace được live_session_id, comment_id, messenger_thread_id", SmokeStatus.OWNER),
    _spec(14, "ADS-P0-014", "Diamond referral order verified", "Gắn referral attribution, không tự tính commission", SmokeStatus.OWNER),
    _spec(15, "ADS-P0-015", "Dashboard hiển thị quote/order draft như revenue", "Fail", SmokeStatus.OWNER),
    _spec(16, "proposed", "Outbox item fails to send N times", "Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry, no silent loss", SmokeStatus.PROPOSED),
    _spec(17, "proposed", "External payload (CAPI/Offline) built from an event containing raw PII", "Hash policy applied per M6-OD-003; no raw phone/email/user-id in the outbound payload or platform result log", SmokeStatus.PROPOSED),
    _spec(18, "proposed", "Attribution correction attempted after ORDER_VERIFIED", "Direct mutation rejected; adjustment record created with actor, reason, audit, evidence", SmokeStatus.PROPOSED),
)

SMOKE_IDS: Tuple[str, ...] = tuple(s.smoke_id for s in SMOKE_REGISTRY)
_BY_ID: Dict[str, SmokeSpec] = {s.smoke_id: s for s in SMOKE_REGISTRY}


def get_spec(smoke_id: str) -> SmokeSpec:
    return _BY_ID[smoke_id]


def proposed_ids() -> Tuple[str, ...]:
    return tuple(s.smoke_id for s in SMOKE_REGISTRY if s.status is SmokeStatus.PROPOSED)
