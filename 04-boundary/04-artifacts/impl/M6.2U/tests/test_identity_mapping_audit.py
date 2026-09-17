"""RULE-006 guest -> customer identity mapping with audit — exit-gate leg L3."""
from __future__ import annotations

import dataclasses

import pytest

from app.measurement.identity.resolver import Confidence


def test_mapped_with_audit_and_existing_customer_is_ok(resolver):
    res = resolver.resolve("guest_mapped_ok")
    assert res.confidence is Confidence.OK
    assert res.reason == "MAPPED_WITH_AUDIT"


def test_mapping_without_audit_is_held(resolver, audit):
    """RULE-006: a mapping presented without audit is NOT trusted."""
    res = resolver.resolve("guest_no_audit")
    assert res.confidence is Confidence.HOLD
    assert res.reason == "MAPPING_WITHOUT_AUDIT"
    assert audit.find("MAPPING_WITHOUT_AUDIT")


def test_unmapped_guest_is_low_never_guessed(resolver):
    res = resolver.resolve("guest_unmapped")
    assert res.confidence is Confidence.LOW
    assert res.mapped_customer_id_masked is None   # never guess a customer


def test_unknown_guest_is_held(resolver):
    res = resolver.resolve("guest_totally_unknown")
    assert res.confidence is Confidence.HOLD
    assert res.reason == "GUEST_NOT_FOUND"


def test_mapped_customer_missing_is_held(resolver):
    res = resolver.resolve("guest_bad_customer")
    assert res.confidence is Confidence.HOLD
    assert res.reason == "MAPPED_CUSTOMER_MISSING"


def test_identity_values_are_masked_in_result_and_audit(resolver, audit):
    res = resolver.resolve("guest_mapped_ok")
    assert res.guest_id_masked != "guest_mapped_ok"   # raw id never surfaced
    assert res.mapped_customer_id_masked != "cust_0001"
    for rec in audit.records:
        assert rec.subject_masked != "guest_mapped_ok"


def test_mapping_is_never_overwritten_without_evidence(guest_rows):
    """M6 has no write path; consumed rows are frozen -> cannot be overwritten in place (RULE-006)."""
    gc = guest_rows["guest_mapped_ok"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        gc.mapped_customer_id = "cust_9999"  # type: ignore[misc]
