"""Official smoke — slice M6.2B — M6-SMK-001 (doc ADS-P0-001), tracking-pipeline flavor.

Authored by TESTER in M6-P1103 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1104
(TESTER_RUN -> 04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 401):

    Kịch bản (verbatim):          "Event không có trong event_registry"
    Kết quả phải đạt (verbatim):  "Reject/HOLD, audit rõ"

M6.2B binds SMK-001 to the TRACKING PIPELINE and its exit-gate leg 1 requires the unknown event to fail at
BOTH independent layers (RULE-H03 — client validation is never trusted alone):
  - layer 1 = the frontend tracking hook (`app.measurement.tracking.hooks.TrackingHook`), a client allow-list
    of the 9 LOCKED base events;
  - layer 2 = the backend `POST /api/ads/events/track` handler (`app.api.track.handle_track_request`), which
    re-validates against the Core event_registry via the hardened ingest seam.
Prevents M6-FAIL-003 (event drift). RULE-001 / RULE-018. `event_code`/`session_id` are channel-origin,
untrusted DATA — these fixtures use synthetic codes only; no raw PII. Reuses the shared conftest fixtures
(`track_deps`, `make_track_body`, `store`, `measurement_store`, `audit`).
"""
from __future__ import annotations

from app.api.track import handle_track_request
from app.measurement.audit import AuditLog
from app.measurement.tracking.hooks import TrackingHook


# --- primary smoke: scenario verbatim, backend layer (leg-1 layer 2) ------------------------------
def test_smk_001_unknown_event_is_rejected_with_audit_through_track_endpoint(
    track_deps, make_track_body, audit, store, measurement_store
):
    """M6-SMK-001 "Event không có trong event_registry" -> "Reject/HOLD, audit rõ".

    An event code absent from event_registry, posted to the track endpoint, is REJECTED (error_code
    UNKNOWN_EVENT), the registry miss is clearly audited (audit rõ), and NOTHING is logged to
    web_event_logs or normalized into ads_measurement_events.
    """
    res = handle_track_request(
        make_track_body(event_code="SMK001_EVENT_NOT_IN_REGISTRY"), track_deps
    )
    assert res.status == "REJECTED"
    assert res.error_code == "UNKNOWN_EVENT"
    assert audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY"), "the backend registry miss must be audited (audit rõ)"
    assert len(store) == 0, "an unknown event never becomes a raw measurement row"
    assert len(measurement_store) == 0, "an unknown event never becomes a normalized row"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_001_neg_frontend_hook_refuses_unknown_event_audited():
    """Leg-1 layer 1: the client tracking hook refuses an unknown code and audits it — nothing is emitted."""
    audit = AuditLog()
    res = TrackingHook(audit).emit("SMK001_UNKNOWN_AT_HOOK")
    assert res.emitted is False
    assert res.reason == "HOOK_UNKNOWN_EVENT"
    assert audit.find("HOOK_UNKNOWN_EVENT"), "the client hook must audit the refused code"


def test_smk_001_neg_frontend_hook_refuses_non_str_code_failclosed():
    """Fail-closed at the hook: a hostile non-str code is refused (never coerced), audited, not emitted."""
    audit = AuditLog()
    res = TrackingHook(audit).emit(["not", "a", "code"])   # channel-origin hostile input, treated as DATA
    assert res.emitted is False
    assert audit.find("HOOK_UNKNOWN_EVENT")


def test_smk_001_neg_backend_layer_is_independent_of_the_hook(
    track_deps, make_track_body, store, measurement_store
):
    """The two unknown-event layers are INDEPENDENT (not redundant): CLICK_CTA IS a locked base event, so it
    passes the client hook (layer 1), but it is not seeded ACTIVE in the registry double, so the backend
    (layer 2) independently rejects it. Client validation is never trusted alone (RULE-H03)."""
    assert TrackingHook(AuditLog()).emit("CLICK_CTA").emitted is True            # passes layer 1
    res = handle_track_request(make_track_body(event_code="CLICK_CTA"), track_deps)  # caught by layer 2
    assert res.status == "REJECTED" and res.error_code == "UNKNOWN_EVENT"
    assert len(store) == 0 and len(measurement_store) == 0


def test_smk_001_neg_deregistered_event_is_held_failclosed(
    track_deps, make_track_body, audit, store, measurement_store
):
    """The "HOLD" arm of "Reject/HOLD": a DEREGISTERED registry entry is not usable -> rejected/held,
    audited (REGISTRATION_STATE_NOT_ACTIVE), never logged. Fail-closed, never false-ALLOW."""
    res = handle_track_request(make_track_body(event_code="DEREG_SAMPLE"), track_deps)
    assert res.status == "REJECTED"
    assert audit.find("REGISTRATION_STATE_NOT_ACTIVE"), "the HOLD arm must be audited"
    assert len(store) == 0 and len(measurement_store) == 0


# --- positive control: proves the smoke discriminates (does not reject everything) ----------------
def test_smk_001_control_known_active_event_is_accepted_end_to_end(
    track_deps, make_track_body, store, measurement_store
):
    """Control (non-vacuity): a known ACTIVE base event (VIEW_LANDING) posted to the endpoint IS accepted and
    creates exactly one row in each store — so the smoke is not vacuously rejecting everything."""
    res = handle_track_request(make_track_body(), track_deps)
    assert res.status == "ACCEPTED"
    assert len(store) == 1 and len(measurement_store) == 1
