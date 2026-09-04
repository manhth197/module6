"""M6.2H leg 3 / M6-RULE-011: the Learn stage runs ONLY after a canonical seed exists AND consumes ONLY verified
business signals that passed the Data Quality Gate ("chỉ được học sau khi có seed chuẩn và dữ liệu verified
business signal đủ sạch", doc §17). It scores the 5 doc dims. Fail-closed.
"""
from __future__ import annotations

import pytest

from app.measurement.learning.candidate import TargetDim
from app.measurement.learning.learning_engine import LearningPreconditionError


def test_learn_refuses_without_a_canonical_seed(learning_engine, make_signal):
    with pytest.raises(LearningPreconditionError):
        learning_engine.learn([make_signal("persona")])          # no seed yet -> fail-closed refuse


def test_learn_consumes_only_dq_passed_verified_signals(learning_engine, seed_all_libraries, make_signal):
    seed_all_libraries()
    signals = [
        make_signal("persona", value=1.0, dq_status="PASS", verified=True),    # usable
        make_signal("persona", value=9.0, dq_status="HOLD", verified=True),    # excluded (DQ not PASS)
        make_signal("keyword", value=5.0, dq_status="FAIL", verified=True),    # excluded (DQ FAIL)
        make_signal("keyword", value=7.0, dq_status="PASS", verified=False),   # excluded (unverified)
        make_signal("hook",    value=2.0, dq_status="PASS", verified=True),    # usable
    ]
    scores = learning_engine.learn(signals)
    assert scores == {TargetDim.PERSONA: 1.0, TargetDim.HOOK: 2.0}   # only usable signals scored
    assert TargetDim.KEYWORD not in scores                          # both keyword signals were non-usable


def test_learn_scores_are_from_verified_signals_only(learning_engine, seed_all_libraries, make_signal):
    seed_all_libraries()
    # two usable persona signals -> mean
    scores = learning_engine.learn([
        make_signal("persona", value=2.0, dq_status="PASS", verified=True),
        make_signal("persona", value=4.0, dq_status="PASS", verified=True),
    ])
    assert scores[TargetDim.PERSONA] == 3.0
