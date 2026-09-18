"""M6.2C: POST /api/ads/conversions (M6-CTR-017) — validate + create conversion + transactionally enqueue the
measurement outbox (fan-out per platform). Revenue only from ORDER_VERIFIED (RULE-003). Replay-safe (RULE-005).
"""
from __future__ import annotations

from app.api.conversions import ConversionDeps, handle_conversions_request
from app.measurement.registry.validator import EventValidator
from app.measurement.store.conversion_event_store import ConversionEventStore
from app.measurement.outbox.outbox_store import OutboxStore


def _deps_with_events(event_codes, audit, consent_reader=None):
    """A ConversionDeps whose registry has the given event_codes ACTIVE (isolated from the shared fixture).
    M6.2E Round 2: F-D bind is MANDATORY, so a consent_reader must be wired (the default body's subject
    guest_mapped_ok matches cs_valid); callers pass the staged app_consent_reader."""
    from app.measurement.models.consumed import EventRegistryRow, RegistrationState

    class _Reg:
        def __init__(self, codes):
            self._rows = {
                c: EventRegistryRow(c, RegistrationState.ACTIVE, owner="core.tracking") for c in codes
            }

        def get(self, code):
            return self._rows.get(code)

    store = ConversionEventStore()
    outbox = OutboxStore()
    deps = ConversionDeps(
        EventValidator(_Reg(event_codes), audit), store, outbox, audit, max_retries=3,
        consent_reader=consent_reader,
    )
    return deps, store, outbox


def test_valid_conversion_creates_and_enqueues(conversion_deps, make_conversion_body, conversion_store, measurement_outbox):
    res = handle_conversions_request(make_conversion_body(), conversion_deps)
    assert res.status == "CREATED" and res.dispatch_state == "QUEUED"
    assert res.conversion_id and res.idempotent_replay is False
    assert len(conversion_store) == 1
    assert len(measurement_outbox) == 2      # PIXEL + CAPI (VIEW_LANDING, no OFFLINE)


def test_order_verified_with_revenue_fans_out_offline(audit, make_conversion_body, app_consent_reader):
    deps, _store, outbox = _deps_with_events(["ORDER_VERIFIED"], audit, consent_reader=app_consent_reader)
    res = handle_conversions_request(
        make_conversion_body(event_code="ORDER_VERIFIED", revenue_value=250000, source_event_id="evt_ov"), deps
    )
    assert res.status == "CREATED"
    assert len(outbox) == 3                  # PIXEL + CAPI + OFFLINE (OFFLINE only for ORDER_VERIFIED)


def test_revenue_on_non_verified_event_is_rejected(conversion_deps, make_conversion_body):
    res = handle_conversions_request(make_conversion_body(revenue_value=100000), conversion_deps)  # VIEW_LANDING
    assert res.error_code == "REVENUE_NOT_VERIFIED"


def test_unknown_event_rejected_nothing_enqueued(conversion_deps, make_conversion_body, conversion_store, measurement_outbox):
    res = handle_conversions_request(make_conversion_body(event_code="NOPE_NOT_REAL"), conversion_deps)
    assert res.error_code == "UNKNOWN_EVENT"
    assert len(conversion_store) == 0 and len(measurement_outbox) == 0


def test_missing_consent_reference_rejected(conversion_deps, make_conversion_body):
    body = make_conversion_body()
    del body["consent_snapshot_id"]
    assert handle_conversions_request(body, conversion_deps).error_code == "CONSENT_MISSING_OR_INVALID"


def test_missing_event_code_schema_invalid(conversion_deps, make_conversion_body):
    body = make_conversion_body()
    del body["event_code"]
    res = handle_conversions_request(body, conversion_deps)
    assert res.error_code == "SCHEMA_INVALID" and res.field == "event_code"


def test_replay_is_duplicate_no_reenqueue(conversion_deps, make_conversion_body, conversion_store, measurement_outbox):
    body = make_conversion_body()
    first = handle_conversions_request(body, conversion_deps)
    second = handle_conversions_request(dict(body), conversion_deps)
    assert first.status == "CREATED" and second.status == "DUPLICATE" and second.idempotent_replay is True
    assert second.conversion_id == first.conversion_id
    assert len(conversion_store) == 1 and len(measurement_outbox) == 2   # no second conversion, no re-enqueue
