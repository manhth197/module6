"""M6.2T LEG 3 + LEG 4 / M6-OD-019 / SMK-032(iii)(iv) / RULE-014 / FAIL-008: reader PII-reject + in-process residuals.

LEG 3: RegistryFeedReader.apply rejects fail-closed (feed_error) a row whose governance metadata carries a
customer-PII shape at parse (input-side, state UNCHANGED; NOT export masking). LEG 4: recall_risk_contribution
rejects a base carrying a RECALL_RISK_KEY (N3); from_mapping is fail-closed on a non-iterable block_reasons (N9);
the reader guards isinstance(str) before the enum value-lookup (N5) + surfaces malformed-sibling observability (N6).
PII-shaped test values are assembled at runtime (no literal PII in source).
"""
from __future__ import annotations

import pytest

from app.measurement.adapters.registry_feed_reader import RegistryFeedReader
from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy
from app.measurement.scale.recall_risk_mapper import (
    OpsCoreAvailabilityResponse,
    RecallRiskContributionError,
    map_pull_outcome,
    map_risk_flags,
    recall_risk_contribution,
)

# PII shapes assembled at runtime (no literal PII in source):
_EMAIL = "u" + chr(64) + "x" + "." + "yz"       # an email shape
_PHONE = "0" + "9" * 9                            # a VN-phone shape (0 + 9 digits)
_LONGID = "1" * 12                                # a long digit run (id/phone-like)


# ---- LEG 3: input-side PII-shape reject on a governance field (SMK-032(iii)) ----
@pytest.mark.parametrize("field,val", [
    ("event_code", _EMAIL), ("event_group", _PHONE), ("domain", _LONGID),
])
def test_pii_shape_in_governance_field_rejected(field, val):
    r = RegistryFeedReader()
    r.apply({"registry_version": 1, "events": [{"event_code": "SEED"}]})        # seed version 1
    res = r.apply({"registry_version": 2, "events": [dict({"event_code": "E"}, **{field: val})]})
    assert res.applied is False and res.reason == "feed_error:pii_shape_in_governance_field"
    assert r.current_registry_version() == 1 and r.get("E") is None             # state UNCHANGED (input-side reject)


def test_legit_governance_codes_do_not_trip_pii_reject():
    r = RegistryFeedReader()
    ok = r.apply({"registry_version": 1, "events": [
        {"event_code": "ORDER_VERIFIED", "event_group": "ads.core", "domain": "ads", "data_sensitivity": "INTERNAL"},
    ]})
    assert ok.applied is True and r.get("ORDER_VERIFIED") is not None


# ---- LEG 4 N5/N6: a non-str enum sibling -> fail-closed default + observable ----
def test_non_str_enum_sibling_is_failclosed_and_observable():
    r = RegistryFeedReader()
    res = r.apply({"registry_version": 1, "events": [
        {"event_code": "E", "data_sensitivity": 123, "external_send_policy": {"x": 1}},   # both non-str
    ]})
    assert res.applied is True and res.malformed_fields == 2                    # N6: observable
    row = r.get("E")
    assert row.data_sensitivity is DataSensitivity.PII                          # N5: non-str -> PII (fail-closed)
    assert row.external_send_policy is ExternalSendPolicy.BLOCKED_DEFAULT       # N5: non-str -> BLOCKED_DEFAULT
    # a well-formed feed carries no malformed sibling
    r2 = RegistryFeedReader()
    ok = r2.apply({"registry_version": 1, "events": [
        {"event_code": "E", "data_sensitivity": "INTERNAL", "external_send_policy": "INTERNAL_ONLY"},
    ]})
    assert ok.malformed_fields == 0 and ok.reason == "applied"


# ---- LEG 4 N3: recall_risk_contribution rejects a base carrying a mapper-owned recall key ----
def test_recall_risk_contribution_rejects_base_recall_key():
    read = map_risk_flags(OpsCoreAvailabilityResponse(recall_hold=False, sale_lock=False, quality_hold=False))
    for key in ("recall", "sale_lock", "quality_hold"):
        with pytest.raises(RecallRiskContributionError):
            recall_risk_contribution(read, base_flags={key: False, "complaint_p0": False})
    # a base carrying only the OTHER lock sources is accepted (no clash)
    out = recall_risk_contribution(read, base_flags={"complaint_p0": False, "platform_spam_flag": False,
                                                     "crm_suppression": False})
    assert isinstance(out, dict)


# ---- LEG 4 N9: from_mapping fail-closed-loud on a non-iterable / str block_reasons ----
def test_from_mapping_non_iterable_block_reasons_is_failclosed():
    base = {"recall_hold": False, "sale_lock": False, "quality_hold": False}
    assert OpsCoreAvailabilityResponse.from_mapping(dict(base, block_reasons=5)) is None            # int -> None
    assert OpsCoreAvailabilityResponse.from_mapping(dict(base, block_reasons="oops")) is None        # bare str -> None
    assert map_pull_outcome(dict(base, block_reasons=5)).complete is False                           # surfaced incomplete
    # a valid list/tuple / absent block_reasons still parses (provenance recorded)
    ok = OpsCoreAvailabilityResponse.from_mapping(dict(base, block_reasons=["a", "b"]))
    assert ok is not None and ok.block_reasons == ("a", "b")
    assert OpsCoreAvailabilityResponse.from_mapping(base) is not None                                # absent -> ()
