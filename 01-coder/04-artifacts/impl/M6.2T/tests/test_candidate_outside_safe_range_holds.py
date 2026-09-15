"""M6.2H leg 2 / M6-SMK-011 / M6-FAIL-006: a learning candidate outside (or, while M6-OD-006 is OPEN, UNKNOWN)
the safe range is HELD in review and never published. "Learning candidate ngoài safe range -> Hold review,
không publish."
"""
from __future__ import annotations

from app import config
from app.measurement.learning.candidate import ReviewState, SafeRangeStatus


def test_candidate_outside_safe_range_is_held(learning_engine, review_queue, make_candidate):
    cand = make_candidate("lc_out", target_dim="keyword", safe_range_status=SafeRangeStatus.OUTSIDE)
    queued = learning_engine.review(cand)
    assert queued.review_state is ReviewState.HOLD                 # SMK-011: hold review, no publish
    assert queued.safe_range_status is SafeRangeStatus.UNKNOWN     # fail-closed (M6-OD-006 OPEN)
    assert queued.is_publish_authorized is False                  # never publishable
    assert review_queue.get("lc_out").review_state is ReviewState.HOLD


def test_even_a_within_claim_is_forced_unknown_and_held(learning_engine, make_candidate):
    # a candidate that CLAIMS WITHIN is forced to UNKNOWN + HELD while the safe range is unratified (fail-closed)
    cand = make_candidate("lc_within_claim", safe_range_status=SafeRangeStatus.WITHIN)
    queued = learning_engine.review(cand)
    assert queued.safe_range_status is SafeRangeStatus.UNKNOWN
    assert queued.review_state is ReviewState.HOLD
    assert queued.is_publish_authorized is False


def test_guarded_publish_is_blocked(learning_engine):
    assert learning_engine.guarded_publish_blocked() is True
    assert config.LEARNING_SAFE_RANGE_RATIFIED is False
