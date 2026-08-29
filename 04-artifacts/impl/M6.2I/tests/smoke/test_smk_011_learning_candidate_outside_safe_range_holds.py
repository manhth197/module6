"""Official smoke — slice M6.2H — M6-SMK-011 (doc ADS-P0-011).

Authored by TESTER in M6-P1703 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1704
(TESTER_RUN -> 04-artifacts/test-reports/M6.2H/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF, LEARNING_AUTOPUBLISH_ENABLED=False,
LEARNING_SAFE_RANGE_RATIFIED=False, LEARNING_CONTENT_FILL_ENABLED=False — nothing below flips a flag and nothing
is ever published.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 411):

    Kịch bản (verbatim):          "Learning candidate ngoài safe range"
    Kết quả phải đạt (verbatim):  "Hold review, không publish"

A learning candidate outside (or, while M6-OD-006 is OPEN, UNKNOWN) the owner-ratified safe range is HELD in the
review queue and is never published (RULE-011, LEX-006, FAIL-006). The engine's `review()` forces the safe-range
status to fail-closed UNKNOWN (no ratified safe range), so the candidate goes to HOLD; `is_publish_authorized`
requires an owner APPROVE AND a WITHIN safe range, so it stays False — even after an explicit owner APPROVE. There
is deliberately no auto-publish method anywhere. Reuses the shared conftest learning fixtures (learning_engine,
review_queue, library_store, make_candidate, make_review_decision). All ids synthetic; no PII.
"""
from __future__ import annotations

import pytest

from app import config
from app.measurement.learning.candidate import (
    AdsLearningCandidate,
    LearningCandidateKind,
    ReviewState,
    SafeRangeStatus,
    TargetDim,
)


# --- primary smoke: scenario verbatim -------------------------------------------------------------
@pytest.mark.parametrize("claimed", [SafeRangeStatus.OUTSIDE, SafeRangeStatus.UNKNOWN])
def test_smk_011_candidate_outside_safe_range_is_held_not_published(
    learning_engine, review_queue, make_candidate, claimed
):
    """M6-SMK-011 "Learning candidate ngoài safe range" -> "Hold review, không publish".

    A candidate outside (or unknown) the safe range is HELD in the review queue and is never publishable.
    """
    cand = make_candidate("lc_out", target_dim="keyword", safe_range_status=claimed)
    queued = learning_engine.review(cand)

    assert queued.review_state is ReviewState.HOLD                 # hold review
    assert queued.safe_range_status is SafeRangeStatus.UNKNOWN     # fail-closed (M6-OD-006 OPEN)
    assert queued.is_publish_authorized is False                  # không publish
    assert review_queue.get("lc_out").review_state is ReviewState.HOLD


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_011_neg_within_claim_is_forced_unknown_and_held(learning_engine, make_candidate):
    """An untrusted 'WITHIN' claim cannot bypass the unratified safe range: `review()` forces it to UNKNOWN and
    HOLDs it (fail-closed) — a candidate can never talk its way into being publishable."""
    cand = make_candidate("lc_within_claim", safe_range_status=SafeRangeStatus.WITHIN)
    queued = learning_engine.review(cand)

    assert queued.safe_range_status is SafeRangeStatus.UNKNOWN
    assert queued.review_state is ReviewState.HOLD
    assert queued.is_publish_authorized is False


def test_smk_011_neg_no_auto_publish_method_and_guarded_publish_blocked(
    learning_engine, review_queue, library_store
):
    """"Không publish": the learning layer exposes NO publish/auto-publish/go-live/execute method, the guarded
    safe-range publish is BLOCKED, and the posture flags are immutable (RULE-011, LEX-006, FAIL-006)."""
    for obj in (learning_engine, review_queue, library_store):
        for name in ("publish", "auto_publish", "auto_publish_candidate", "go_live", "launch",
                     "execute", "apply", "act", "send", "dispatch", "transport"):
            assert not hasattr(obj, name), f"{type(obj).__name__} must not expose {name!r}"
    assert learning_engine.guarded_publish_blocked() is True
    assert config.LEARNING_AUTOPUBLISH_ENABLED is False
    assert config.LEARNING_SAFE_RANGE_RATIFIED is False
    assert config.PRODUCTION_FLAG == "OFF" and config.GLOBAL_GATEWAY_STATE == "BLOCKED"


def test_smk_011_neg_owner_approve_still_not_publishable_while_safe_range_unknown(
    learning_engine, review_queue, make_candidate, make_review_decision
):
    """Even a RECORDED owner APPROVE does not authorize a publish while the safe range is UNKNOWN (M6-OD-006
    OPEN): review_state becomes APPROVED but safe_range stays UNKNOWN, so is_publish_authorized stays False —
    "không publish". Nothing is published (RULE-011)."""
    learning_engine.review(make_candidate("lc_appr", safe_range_status=SafeRangeStatus.OUTSIDE))
    decided = learning_engine.record_review_decision("lc_appr", make_review_decision("APPROVED"))

    assert decided.review_state is ReviewState.APPROVED            # the review transition is recorded ...
    assert decided.safe_range_status is SafeRangeStatus.UNKNOWN    # ... but the safe range is still UNKNOWN ...
    assert decided.is_publish_authorized is False                 # ... so no publish is authorized
    assert review_queue.get("lc_appr").is_publish_authorized is False


# --- positive control: proves is_publish_authorized is discriminating, not always-False -----------
def test_smk_011_control_publish_authorized_is_discriminating_but_unreachable(learning_engine, make_candidate):
    """Control (non-vacuous): a candidate that is BOTH APPROVED and WITHIN the safe range WOULD be
    publish-authorized (the property can be True) — but the engine's `review()` forces UNKNOWN in the staged
    posture, so a reviewed candidate can never reach WITHIN. The HOLD is caused by the unratified safe range
    (M6-OD-006), not a guard that always denies."""
    would_publish = AdsLearningCandidate(
        candidate_id="lc_ctrl", kind=LearningCandidateKind.OPTIMIZATION, target_dim=TargetDim.PERSONA,
        score=0.9, sku_ref="SKU_HERO_1",
        review_state=ReviewState.APPROVED, safe_range_status=SafeRangeStatus.WITHIN,
    )
    assert would_publish.is_publish_authorized is True            # the property CAN be True (discriminating)

    # ... but no candidate put through review() reaches WITHIN while the safe range is unratified
    reviewed = learning_engine.review(make_candidate("lc_ctrl2", safe_range_status=SafeRangeStatus.WITHIN))
    assert reviewed.safe_range_status is SafeRangeStatus.UNKNOWN
    assert reviewed.is_publish_authorized is False
    assert config.LEARNING_SAFE_RANGE_RATIFIED is False
