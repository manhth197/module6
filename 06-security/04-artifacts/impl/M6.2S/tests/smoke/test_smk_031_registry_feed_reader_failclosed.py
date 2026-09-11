"""Official smoke — slice M6.2S — M6-SMK-031 (chief RELAY_V221 §2.4; registry-feed reader; M6-OD-018).

Authored by TESTER in M6-P2703 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P2704
(TESTER_RUN -> 04-artifacts/test-reports/M6.2S/SMOKE_RESULTS.md). Governance is immutable here and nothing below
flips a flag, opens egress, or calls a real network: global_gateway_state=BLOCKED, production_flag=OFF,
external_send=OFF. The event-registry-feed.v1 response is a value object / dict built in the test (STAGED, PROPOSED
shape, TODO(contract)); the live M3 endpoint (GET /api/v1/internal/event-registry?since_version={n}) is out of
scope (M3 ENTRY-003 V221 pending) and is not built or called.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (row M6-SMK-031):

    Scenario (verbatim):
        A mock event-registry-feed.v1 response (proposed shape): (i) valid rows; (ii) a feed with registry_version
        <= last applied (stale); (iii) a row with an unknown external_send_policy token + unknown data_sensitivity
        value; (iv) a feed error

    Expected (verbatim):
        reader parses valid rows into typed rows reusing ExternalSendPolicy; a stale/older registry_version is NOT
        applied (no downgrade); unknown external_send_policy → BLOCKED_DEFAULT and unknown/SENSITIVE data_sensitivity
        → PII (fail-closed); a feed error → no update (fail-closed); the reader NEVER calls a live endpoint; no event
        becomes ALLOW_EXTERNAL, external_send OFF, no raw PII

The reader (app.measurement.adapters.registry_feed_reader.RegistryFeedReader) consumes the feed fail-closed: it
parses valid rows into typed RegistryFeedRow reusing the M6.2P ExternalSendPolicy + DataSensitivity enums; it is
staleness-safe by a monotonic registry_version (a version <= the last applied is not applied — no downgrade); every
unknown is fail-closed (unknown external_send_policy -> BLOCKED_DEFAULT, unknown/SENSITIVE data_sensitivity -> PII,
non-bool is_active -> False); a feed error leaves the reader unchanged; it holds no HTTP client and opens no egress.
Reuses the CODER's inline feed-builder pattern (_row / _feed) from tests/test_m6_2s_registry_feed_reader.py. The
feed carries governance metadata (event_code/group/domain/sensitivity/policy/is_active/updated_at), not customer PII.
"""
from __future__ import annotations

import inspect

import pytest

from app import config
from app.measurement.adapters.registry_feed_reader import RegistryFeedReader
import app.measurement.adapters.registry_feed_reader as reader_module
from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy


def _row(event_code="E1", **over):
    """A valid proposed-shape feed row; override per case (mirrors the coder regression's builder)."""
    base = {
        "event_code": event_code, "event_group": "g1", "domain": "ads",
        "data_sensitivity": "INTERNAL", "external_send_policy": "INTERNAL_ONLY",
        "is_active": True, "updated_at": "2026-09-10T00:00:00Z",
    }
    base.update(over)
    return base


def _feed(version, rows):
    return {"registry_version": version, "events": rows}


# ---- (i) valid rows -> typed rows reusing ExternalSendPolicy; current version exposed -------------------------
def test_smk_031_fixture_i_valid_rows_parse_typed_reusing_externalsendpolicy():
    """SMK-031(i). A valid feed parses into typed RegistryFeedRow reusing the M6.2P ExternalSendPolicy +
    DataSensitivity enums; the reader exposes + advances its current registry_version; omitted optional metadata is
    None (never invented)."""
    r = RegistryFeedReader()
    assert r.current_registry_version() == 0
    res = r.apply(_feed(1, [
        _row("E1"),
        _row("E2", data_sensitivity="PUBLIC", external_send_policy="BLOCKED_PII"),
    ]))
    assert res.applied is True and res.registry_version == 1 and res.rows_applied == 2 and res.reason == "applied"
    assert r.current_registry_version() == 1

    e1 = r.get("E1")
    assert isinstance(e1.external_send_policy, ExternalSendPolicy)               # reuses the enum, not a raw token
    assert e1.external_send_policy is ExternalSendPolicy.INTERNAL_ONLY
    assert e1.data_sensitivity is DataSensitivity.INTERNAL and e1.is_active is True
    assert e1.event_group == "g1" and e1.domain == "ads" and e1.updated_at == "2026-09-10T00:00:00Z"
    # a distinct known token maps through too (classification is real, not everything-collapses-to-one)
    assert r.get("E2").external_send_policy is ExternalSendPolicy.BLOCKED_PII

    # omitted optional metadata -> None (not invented)
    r2 = RegistryFeedReader()
    r2.apply(_feed(1, [{"event_code": "E1", "data_sensitivity": "INTERNAL",
                        "external_send_policy": "INTERNAL_ONLY", "is_active": True}]))
    only = r2.get("E1")
    assert only.event_group is None and only.domain is None and only.updated_at is None


# ---- (ii) staleness-safe: registry_version <= last applied is NOT applied (no downgrade) ----------------------
def test_smk_031_fixture_ii_stale_version_not_applied_no_downgrade():
    """SMK-031(ii). A feed whose registry_version is <= the last applied (equal or older) is not applied — no
    downgrade, state unchanged. A strictly-greater feed applies and advances the version (delta upsert: the prior
    row survives, no drop)."""
    r = RegistryFeedReader()
    r.apply(_feed(5, [_row("E1")]))
    assert r.current_registry_version() == 5
    for stale in (5, 4, 1):                                               # equal + older
        res = r.apply(_feed(stale, [_row("E_STALE")]))
        assert res.applied is False and res.reason == "stale"
        assert r.current_registry_version() == 5 and r.get("E_STALE") is None      # unchanged, no downgrade

    res2 = r.apply(_feed(6, [_row("E2")]))                                # strictly greater -> applies
    assert res2.applied is True and r.current_registry_version() == 6
    assert r.get("E1") is not None and r.get("E2") is not None            # delta upsert, prior row kept


def test_smk_031_neg_malformed_higher_version_does_not_poison_staleness():
    """Fail-closed staleness edge: a HIGHER registry_version carrying a malformed row is rejected and the version
    does NOT advance (parse-all-first, never half-applied), so a later genuine feed at that version still applies —
    a malformed higher-version feed cannot poison staleness."""
    r = RegistryFeedReader()
    r.apply(_feed(2, [_row("E1")]))
    res = r.apply(_feed(3, [_row("E_OK"), {"data_sensitivity": "INTERNAL"}]))     # 2nd row missing event_code
    assert res.applied is False and r.current_registry_version() == 2
    assert r.get("E_OK") is None                                                  # not half-applied
    assert r.apply(_feed(3, [_row("E3")])).applied is True and r.current_registry_version() == 3


# ---- (iii) unknown external_send_policy -> BLOCKED_DEFAULT, unknown/SENSITIVE data_sensitivity -> PII ----------
def test_smk_031_fixture_iii_unknown_tokens_failclosed_blocked_default_and_pii():
    """SMK-031(iii). An unknown external_send_policy token coerces to BLOCKED_DEFAULT; an unknown data_sensitivity
    value, and the M3 'SENSITIVE' token unknown to M6, coerce to PII; a row missing both coerces to
    BLOCKED_DEFAULT / PII / is_active False. No row is fabricated ALLOW_EXTERNAL by the fail-closed path (even
    though ALLOW_EXTERNAL is a real enum member — the guard is non-vacuous)."""
    assert ExternalSendPolicy.ALLOW_EXTERNAL in set(ExternalSendPolicy)          # the member is real...
    r = RegistryFeedReader()
    r.apply(_feed(1, [
        _row("E_UNK", external_send_policy="WEIRD_TOKEN", data_sensitivity="MYSTERY"),
        _row("E_SENS", data_sensitivity="SENSITIVE"),                            # M3 SENSITIVE unknown to M6 -> PII
        {"event_code": "E_MISS"},                                                # missing policy/sensitivity/is_active
    ]))
    unk = r.get("E_UNK")
    assert unk.external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT        # unknown -> BLOCKED_DEFAULT
    assert unk.data_sensitivity is DataSensitivity.PII                           # unknown -> PII
    assert r.get("E_SENS").data_sensitivity is DataSensitivity.PII              # SENSITIVE -> PII
    miss = r.get("E_MISS")
    assert miss.external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT       # missing -> BLOCKED_DEFAULT
    assert miss.data_sensitivity is DataSensitivity.PII                          # missing -> PII
    assert miss.is_active is False                                               # missing is_active -> False
    # ...yet no event becomes ALLOW_EXTERNAL via the fail-closed path
    assert all(row.external_send_policy is not ExternalSendPolicy.ALLOW_EXTERNAL for row in r.rows())


# ---- (iv) a feed error -> no update (fail-closed), state unchanged --------------------------------------------
@pytest.mark.parametrize("bad_feed", [
    None, [1, 2, 3], "registry", 42,                                     # not a Mapping
    {"events": [_row("X")]},                                             # missing registry_version
    {"registry_version": 1},                                            # missing events
    {"registry_version": "1", "events": []},                           # non-int version
    {"registry_version": 6.0, "events": []},                           # float version
    {"registry_version": 1, "events": {"not": "a list"}},             # events not a list
    {"registry_version": 4, "events": [{"data_sensitivity": "PII"}]},   # row missing event_code (v4 > seed 3)
    {"registry_version": 4, "events": [{"event_code": "  "}]},         # blank event_code (v4 > seed 3)
])
def test_smk_031_fixture_iv_feed_error_no_update_failclosed(bad_feed):
    """SMK-031(iv). A feed error (not a Mapping / missing registry_version or events / non-int version / a garbage
    row / a missing-or-blank event_code) is not applied and leaves the reader unchanged (fail-closed)."""
    r = RegistryFeedReader()
    r.apply(_feed(3, [_row("SEED")]))                                    # a prior valid apply (version 3)
    res = r.apply(bad_feed)
    assert res.applied is False and res.reason.startswith("feed_error:")
    assert r.current_registry_version() == 3 and len(r) == 1 and r.get("SEED") is not None   # unchanged


# ---- fail-closed non-vacuity: non-bool is_active / bool version / non-Mapping row (red-team edges) ------------
@pytest.mark.parametrize("is_active_raw", [None, "true", 1, 0, "false", "True"])
def test_smk_031_neg_non_bool_is_active_is_failclosed_false(is_active_raw):
    """Only a real True is active — every non-bool is_active (None / int / string) fails closed to False."""
    r = RegistryFeedReader()
    r.apply(_feed(1, [{"event_code": "E", "is_active": is_active_raw}]))
    assert r.get("E").is_active is False


@pytest.mark.parametrize("boolver", [True, False])
def test_smk_031_neg_bool_registry_version_is_failclosed(boolver):
    """A bool registry_version is not a valid int version (bool subclasses int) -> feed_error:bad_version, state
    unchanged; a later genuine version-1 feed is not shut out by a bool having 'counted' as version 1."""
    r = RegistryFeedReader()
    res = r.apply({"registry_version": boolver, "events": [_row("X")]})
    assert res.applied is False and res.reason == "feed_error:bad_version"
    assert r.current_registry_version() == 0 and r.get("X") is None
    assert r.apply(_feed(1, [_row("X")])).applied is True


@pytest.mark.parametrize("events", [[_row("OK"), 42], ["EVENTCODE"], [None], [_row("OK"), None]])
def test_smk_031_neg_non_mapping_row_is_failclosed_no_crash(events):
    """A garbage events[] element (an int / string / None) fails closed to feed_error:row_not_mapping with no
    AttributeError, and is never half-applied."""
    r = RegistryFeedReader()
    r.apply(_feed(1, [_row("SEED")]))
    res = r.apply(_feed(2, events))
    assert res.applied is False and res.reason == "feed_error:row_not_mapping"
    assert r.current_registry_version() == 1 and r.get("OK") is None


# ---- boundary: the reader NEVER calls a live endpoint; external_send OFF; no raw PII --------------------------
def test_smk_031_no_live_endpoint_external_send_off_and_no_pii():
    """The reader holds no HTTP client / live endpoint (reading opens no egress), EXTERNAL_SEND stays OFF, the
    posture is immutable, and to_public() is governance metadata only (no customer-PII field names)."""
    src = inspect.getsource(reader_module)
    for forbidden in ("import requests", "import httpx", "import urllib", "http.client", "import socket", "aiohttp"):
        assert forbidden not in src, f"reader must not import a live HTTP client: {forbidden}"
    assert config.EXTERNAL_SEND == "OFF"                                 # reading the registry opens no egress
    assert config.PRODUCTION_FLAG == "OFF"
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED"

    r = RegistryFeedReader()
    r.apply(_feed(1, [_row("E1")]))
    pub = r.get("E1").to_public()
    assert set(pub.keys()) == {"event_code", "data_sensitivity", "external_send_policy", "is_active",
                               "event_group", "domain", "updated_at"}
    for pii in ("customer_id", "guest_id", "psid", "phone", "email", "subject_ref"):
        assert pii not in pub                                            # governance metadata only, RULE-014
