"""M6.2S / M6-OD-018 / SMK-031 / RULE-001 / RULE-014 / RULE-015 / FAIL-007 / FAIL-008: registry-feed reader.

The reader consumes a PROPOSED event-registry-feed.v1 (value object / dict — NO live HTTP), reusing the M6.2P
ExternalSendPolicy enum + the validator's fail-closed coercers: staleness-safe by monotonic registry_version (no
downgrade), fail-closed on every unknown (unknown external_send_policy -> BLOCKED_DEFAULT; unknown/SENSITIVE
data_sensitivity -> PII; missing/non-bool is_active -> False; feed error -> not applied), never inventing an omitted
field, opening NO egress. STAGED; posture BLOCKED/OFF/OFF unchanged. Includes the two plan-red-team regressions
(a non-Mapping row and a bool registry_version fail closed, no crash).
"""
from __future__ import annotations

import pytest

from app import config
from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy
from app.measurement.adapters.registry_feed_reader import RegistryFeedReader
import app.measurement.adapters.registry_feed_reader as reader_module


def _row(event_code="E1", **over):
    base = {
        "event_code": event_code, "event_group": "g1", "domain": "ads",
        "data_sensitivity": "INTERNAL", "external_send_policy": "INTERNAL_ONLY",
        "is_active": True, "updated_at": "2026-09-10T00:00:00Z",
    }
    base.update(over)
    return base


def _feed(version, rows):
    return {"registry_version": version, "events": rows}


# ---- (i) valid rows: parsed into typed rows reusing ExternalSendPolicy; current version exposed ----
def test_valid_feed_parses_typed_rows():
    r = RegistryFeedReader()
    assert r.current_registry_version() == 0
    res = r.apply(_feed(1, [_row("E1"), _row("E2", data_sensitivity="PUBLIC", external_send_policy="BLOCKED_PII")]))
    assert res.applied is True and res.registry_version == 1 and res.rows_applied == 2 and res.reason == "applied"
    assert r.current_registry_version() == 1
    e1 = r.get("E1")
    assert isinstance(e1.external_send_policy, ExternalSendPolicy) and e1.external_send_policy is ExternalSendPolicy.INTERNAL_ONLY
    assert e1.data_sensitivity is DataSensitivity.INTERNAL and e1.is_active is True
    assert e1.event_group == "g1" and e1.domain == "ads" and e1.updated_at == "2026-09-10T00:00:00Z"


def test_omitted_optional_metadata_is_none_not_invented():
    r = RegistryFeedReader()
    r.apply(_feed(1, [{"event_code": "E1", "data_sensitivity": "INTERNAL", "external_send_policy": "INTERNAL_ONLY",
                       "is_active": True}]))   # no event_group/domain/updated_at
    e1 = r.get("E1")
    assert e1.event_group is None and e1.domain is None and e1.updated_at is None


# ---- (ii) staleness-safe by monotonic registry_version (no downgrade); malformed higher does not bump ----
def test_stale_or_equal_version_not_applied_no_downgrade():
    r = RegistryFeedReader()
    r.apply(_feed(5, [_row("E1")]))
    assert r.current_registry_version() == 5
    for stale in (5, 4, 1):
        res = r.apply(_feed(stale, [_row("E_STALE")]))
        assert res.applied is False and res.reason == "stale"
        assert r.current_registry_version() == 5 and r.get("E_STALE") is None      # unchanged
    # a strictly-greater valid feed applies + advances the version (and UPSERTs, delta since_version)
    res2 = r.apply(_feed(6, [_row("E2")]))
    assert res2.applied is True and r.current_registry_version() == 6
    assert r.get("E1") is not None and r.get("E2") is not None                     # delta upsert, no drop


def test_malformed_higher_version_feed_does_not_bump_version():
    r = RegistryFeedReader()
    r.apply(_feed(2, [_row("E1")]))
    # a HIGHER version (3) but a malformed row -> rejected; version must NOT advance to 3 (no staleness poisoning)
    res = r.apply(_feed(3, [_row("E_OK"), {"data_sensitivity": "INTERNAL"}]))       # 2nd row missing event_code
    assert res.applied is False and r.current_registry_version() == 2
    assert r.get("E_OK") is None                                                    # not half-applied
    # a later genuine version-3 feed still applies (staleness not poisoned)
    assert r.apply(_feed(3, [_row("E3")])).applied is True and r.current_registry_version() == 3


# ---- (iii) fail-closed tokens: unknown -> BLOCKED_DEFAULT / PII; no ALLOW_EXTERNAL fabricated ----
def test_unknown_tokens_resolve_failclosed():
    r = RegistryFeedReader()
    r.apply(_feed(1, [
        _row("E_UNK", external_send_policy="WEIRD_TOKEN", data_sensitivity="MYSTERY"),
        _row("E_SENS", data_sensitivity="SENSITIVE"),               # M3 SENSITIVE is unknown to M6 -> PII
        {"event_code": "E_MISS"},                                    # missing policy/sensitivity/is_active
    ]))
    unk = r.get("E_UNK")
    assert unk.external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT     # unknown -> BLOCKED_DEFAULT
    assert unk.data_sensitivity is DataSensitivity.PII                        # unknown -> PII
    assert r.get("E_SENS").data_sensitivity is DataSensitivity.PII           # SENSITIVE -> PII
    miss = r.get("E_MISS")
    assert miss.external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT    # missing -> BLOCKED_DEFAULT
    assert miss.data_sensitivity is DataSensitivity.PII                       # missing -> PII
    assert miss.is_active is False                                            # missing is_active -> fail-closed False
    # NO row's policy is ALLOW_EXTERNAL via the fail-closed path (unknown never fabricates ALLOW_EXTERNAL)
    assert all(row.external_send_policy is not ExternalSendPolicy.ALLOW_EXTERNAL for row in r.rows())


@pytest.mark.parametrize("is_active_raw", [None, "true", 1, 0, "false", "True"])
def test_non_bool_is_active_is_failclosed_false(is_active_raw):
    r = RegistryFeedReader()
    r.apply(_feed(1, [{"event_code": "E", "is_active": is_active_raw}]))
    assert r.get("E").is_active is False           # only a real True is active


# ---- (iv) feed error -> no update (fail-closed), state unchanged ----
@pytest.mark.parametrize("bad_feed", [
    None, [1, 2, 3], "registry", 42,                                  # not a Mapping
    {"events": [_row("X")]},                                          # missing registry_version
    {"registry_version": 1},                                         # missing events
    {"registry_version": "1", "events": []},                        # non-int version
    {"registry_version": 6.0, "events": []},                        # float version
    {"registry_version": 1, "events": {"not": "a list"}},          # events not a list
    {"registry_version": 4, "events": [{"data_sensitivity": "PII"}]},  # row missing event_code (v4 > seed 3)
    {"registry_version": 4, "events": [{"event_code": "  "}]},      # blank event_code (v4 > seed 3)
])
def test_feed_error_not_applied_state_unchanged(bad_feed):
    r = RegistryFeedReader()
    r.apply(_feed(3, [_row("SEED")]))              # a prior valid apply (version 3)
    res = r.apply(bad_feed)
    assert res.applied is False and res.reason.startswith("feed_error:")
    assert r.current_registry_version() == 3 and len(r) == 1 and r.get("SEED") is not None   # unchanged


# ---- red-team regressions: a non-Mapping row + a bool version fail closed (no crash) ----
@pytest.mark.parametrize("events", [[_row("OK"), 42], ["EVENTCODE"], [None], [_row("OK"), None]])
def test_non_mapping_row_is_failclosed_no_crash(events):
    r = RegistryFeedReader()
    r.apply(_feed(1, [_row("SEED")]))
    res = r.apply(_feed(2, events))                 # a garbage events[] element -> graceful reject, no AttributeError
    assert res.applied is False and res.reason == "feed_error:row_not_mapping"
    assert r.current_registry_version() == 1 and r.get("OK") is None            # not half-applied


@pytest.mark.parametrize("boolver", [True, False])
def test_bool_registry_version_is_failclosed(boolver):
    r = RegistryFeedReader()
    res = r.apply({"registry_version": boolver, "events": [_row("X")]})         # bool is NOT a valid int version
    assert res.applied is False and res.reason == "feed_error:bad_version"
    assert r.current_registry_version() == 0 and r.get("X") is None
    # a later genuine version-1 feed is NOT shut out by a bool having 'applied' as version 1
    assert r.apply(_feed(1, [_row("X")])).applied is True


# ---- boundary: no live endpoint, external_send OFF, no raw PII ----
def test_reader_has_no_live_endpoint_and_no_egress():
    src = open(reader_module.__file__, encoding="utf-8").read()
    for forbidden in ("import requests", "import httpx", "import urllib", "http.client", "import socket", "aiohttp"):
        assert forbidden not in src, f"reader must not import a live HTTP client: {forbidden}"
    assert config.EXTERNAL_SEND == "OFF"           # reading the registry opens no egress; external_send stays OFF


def test_to_public_is_governance_metadata_no_pii():
    r = RegistryFeedReader()
    r.apply(_feed(1, [_row("E1")]))
    pub = r.get("E1").to_public()
    assert set(pub.keys()) == {"event_code", "data_sensitivity", "external_send_policy", "is_active",
                               "event_group", "domain", "updated_at"}
    # no identity/PII field name leaks into the export (governance metadata only, RULE-014)
    for pii in ("customer_id", "guest_id", "psid", "phone", "email", "subject_ref"):
        assert pii not in pub
