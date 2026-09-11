"""M6.2B exit-gate leg 1 (SMK-001): an unknown event fails at BOTH the frontend-hook layer AND the backend
event_registry layer, each audited. The two layers are INDEPENDENT — a code can pass one and be caught by the
other — so client validation is never trusted alone (RULE-H03).
"""
from __future__ import annotations

from app.api.track import handle_track_request
from app.measurement.audit import AuditLog
from app.measurement.tracking.hooks import TrackingHook


# --- layer 1: the client-side tracking hook -------------------------------------------------------
def test_hook_layer_rejects_unknown_code_audited():
    audit = AuditLog()
    res = TrackingHook(audit).emit("TOTALLY_UNKNOWN_EVENT")
    assert res.emitted is False
    assert res.reason == "HOOK_UNKNOWN_EVENT"
    assert audit.find("HOOK_UNKNOWN_EVENT"), "the client hook must audit the refused code"


def test_hook_layer_rejects_non_str_code_failclosed():
    audit = AuditLog()
    res = TrackingHook(audit).emit(["not", "a", "code"])   # hostile non-str, never coerced
    assert res.emitted is False
    assert audit.find("HOOK_UNKNOWN_EVENT")


def test_hook_layer_allows_a_locked_base_event():
    audit = AuditLog()
    res = TrackingHook(audit).emit("VIEW_LANDING", page_id="p1")
    assert res.emitted is True and res.event_code == "VIEW_LANDING"


# --- layer 2: the backend event_registry gate (independent of the hook) ---------------------------
def test_backend_rejects_code_not_active_in_registry(track_deps, make_track_body, audit, store, measurement_store):
    """CLICK_CTA IS a locked base event (would pass the client hook) but is NOT seeded ACTIVE in the registry
    double — the backend independently rejects it. Proves layer 2 is not redundant with layer 1."""
    res = handle_track_request(make_track_body(event_code="CLICK_CTA"), track_deps)
    assert res.status == "REJECTED" and res.error_code == "UNKNOWN_EVENT"
    assert audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY"), "the seam audits the registry miss (SMK-001 audit rõ)"
    assert len(store) == 0 and len(measurement_store) == 0     # nothing logged / normalized


def test_backend_rejects_unknown_code(track_deps, make_track_body, store, measurement_store):
    res = handle_track_request(make_track_body(event_code="HACKME_NOT_REAL"), track_deps)
    assert res.status == "REJECTED" and res.error_code == "UNKNOWN_EVENT"
    assert len(store) == 0 and len(measurement_store) == 0


def test_backend_holds_a_deregistered_event(track_deps, make_track_body, audit, store, measurement_store):
    """A DEREGISTERED registry entry is not usable -> held/rejected, audited, never logged (fail-closed)."""
    res = handle_track_request(make_track_body(event_code="DEREG_SAMPLE"), track_deps)
    assert res.status == "REJECTED"
    assert audit.find("REGISTRATION_STATE_NOT_ACTIVE")
    assert len(store) == 0 and len(measurement_store) == 0
