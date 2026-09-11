"""RULE-007 append-only web_event_logs store + RULE-005 idempotency/dedup."""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.logs.web_event_log_store import AppendOnlyViolation, WebEventLogStore
from app.measurement.models.web_event_log import WebEventLog

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _row(key: str) -> WebEventLog:
    return WebEventLog(
        log_id=f"log_{key[:16]}", event_code="VIEW_LANDING", page_id="p1", session_id="s1",
        source="web", event_ts=TS, idempotency_key=key, ingested_at=TS,
    )


def test_insert_then_duplicate_is_deduped(store):
    key = build_idempotency_key("VIEW_LANDING", "p1", "s1", "rawhash", normalize_ts(TS))
    first = store.append(_row(key))
    assert first.created is True and len(store) == 1
    second = store.append(_row(key))
    assert second.created is False, "duplicate idempotency_key -> no second row (RULE-005)"
    assert len(store) == 1


def test_update_and_delete_are_rejected(store):
    key = build_idempotency_key("VIEW_LANDING", "p1", "s1", "rawhash", normalize_ts(TS))
    store.append(_row(key))
    with pytest.raises(AppendOnlyViolation):
        store.update(key)
    with pytest.raises(AppendOnlyViolation):
        store.delete(key)


def test_row_is_immutable(store):
    key = build_idempotency_key("VIEW_LANDING", "p1", "s1", "rawhash", normalize_ts(TS))
    row = store.append(_row(key)).row
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.source = "tampered"  # type: ignore[misc]


def test_idempotency_key_is_deterministic_and_locked_order():
    a = build_idempotency_key("VIEW_LANDING", "p1", "s1", "h", normalize_ts(TS))
    b = build_idempotency_key("VIEW_LANDING", "p1", "s1", "h", normalize_ts(TS))
    assert a == b
    # A change in any component changes the key (components are load-bearing).
    c = build_idempotency_key("VIEW_LANDING", "p1", "s2", "h", normalize_ts(TS))
    assert a != c
