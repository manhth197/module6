"""M6.2H leg 2 / M6-RULE-011 / M6-LEX-006 / M6-FAIL-006: NO auto-publish. Candidates land in the review queue
only; the learning layer / handlers / deps expose NO publish / auto-publish / execute method; publish is
owner-approval-only and the guarded safe-range publish is BLOCKED (M6-OD-006 OPEN). The machine never auto-publishes.
"""
from __future__ import annotations

from app import config
from app.api.learning_candidates import handle_learning_candidate_create

_FORBIDDEN = (
    "publish", "auto_publish", "auto_publish_candidate", "go_live", "launch", "execute", "apply", "act",
    "send", "dispatch", "transport",
)


def test_no_auto_publish_method_on_learning_layer(learning_engine, review_queue, library_store):
    for obj in (learning_engine, review_queue, library_store):
        for name in _FORBIDDEN:
            assert not hasattr(obj, name), f"{type(obj).__name__} exposes forbidden method {name!r}"


def test_learning_deps_are_inert(make_learning_deps):
    deps = make_learning_deps()
    assert set(vars(deps).keys()) == {"engine", "audit"}          # only the inert engine + audit
    for name in ("publisher", "publish", "transport", "send", "connector", "scale"):
        assert not hasattr(deps, name)


def test_candidate_created_lands_in_review_queue_held(make_learning_deps):
    deps = make_learning_deps()
    res = handle_learning_candidate_create(
        {"target_dim": "persona", "sku_ref": "SKU_HERO_1", "score": 0.9}, deps
    )
    assert res.status == "CREATED"
    assert res.review_state == "HOLD"                             # held, not published
    assert res.safe_range_status == "UNKNOWN"                    # fail-closed (M6-OD-006)


def test_autopublish_and_posture_flags():
    assert config.LEARNING_AUTOPUBLISH_ENABLED is False
    assert config.PRODUCTION_FLAG == "OFF" and config.GLOBAL_GATEWAY_STATE == "BLOCKED"
