"""B1 (M6-OD-003 / M5 PSID hash policy PSID_HASH_POLICY_M5_TMP): PSID is stored ONLY as a one-way salted hash.

(a) no raw PSID on any durable row (as_stored) — only `psid_hash:`...;
(b) one-way + prefix + deterministic for a given pepper;
(c) fail-closed: production + pepper unset ⇒ raise (never hash with an absent salt);
(d) non-vacuity: None/blank PSID ⇒ psid_hash None.
The pepper and the raw psid are never logged/emitted; all id values are synthetic + runtime-assembled.
"""
from __future__ import annotations

import pytest

from app.measurement.identity.psid_hash import (
    HASH_PREFIX,
    PEPPER_ENV,
    PsidHashPolicyError,
    hash_psid,
    resolve_pepper,
)

_PSID = "ps" + "_syn_" + "b1test"          # synthetic PSID, assembled at runtime (no literal PII/id in source)


def test_no_raw_psid_in_durable_store(make_measurement_event, make_conversion, attribution_resolver):
    event = make_measurement_event("evt_b1", event_code="ORDER_VERIFIED", page_id="p", live_session_id="ls")
    ctx = attribution_resolver.resolve(
        event, make_conversion("ORDER_VERIFIED", source_event_id="evt_b1"),
        signals={"comment_id": "c", "psid": _PSID},
    )
    stored = ctx.as_stored()                                  # the DURABLE Zone-B mapping
    assert "psid" not in stored                               # no raw-psid key on the durable row
    assert stored["psid_hash"].startswith(HASH_PREFIX)        # a one-way salted hash
    assert _PSID not in stored["psid_hash"] and _PSID not in str(stored)   # raw psid never durable
    assert not hasattr(ctx, "psid")                           # the model no longer carries a raw-psid field


def test_hash_is_one_way_prefixed_and_deterministic():
    h1 = hash_psid(_PSID)
    h2 = hash_psid(_PSID)
    assert h1 is not None and h1.startswith(HASH_PREFIX)
    assert h1 == h2                                           # deterministic for a given pepper (a stable join key)
    assert _PSID not in h1                                    # one-way: the raw psid is not embedded / recoverable
    assert hash_psid("other" + _PSID) != h1                  # different input -> different hash


def test_fail_closed_production_unset_pepper_raises(monkeypatch):
    monkeypatch.delenv(PEPPER_ENV, raising=False)            # no real pepper resolvable
    with pytest.raises(PsidHashPolicyError):
        resolve_pepper(production=True)                      # production + unset -> refuse (fail-closed)
    with pytest.raises(PsidHashPolicyError):
        hash_psid(_PSID, production=True)


def test_none_or_blank_psid_hashes_to_none():
    assert hash_psid(None) is None
    assert hash_psid("") is None
    assert hash_psid("   ") is None                          # whitespace is not a real PSID


def test_non_str_psid_is_coerced_and_hashed_not_dropped():
    # a numeric psid identity (not a str) is coerced + hashed (a legit join key is not silently dropped), still one-way
    h = hash_psid(1234567890)
    assert h is not None and h == hash_psid("1234567890") and "1234567890" not in h


def test_env_pepper_actually_salts_the_hash(monkeypatch):
    monkeypatch.setenv(PEPPER_ENV, "test-pepper-A")         # a test pepper value (NOT a real secret)
    h_env = hash_psid(_PSID)
    monkeypatch.delenv(PEPPER_ENV, raising=False)
    h_mock = hash_psid(_PSID)                                # dev/staged mock pepper (posture is not production)
    assert h_env != h_mock                                   # the pepper genuinely salts the hash
    assert h_env.startswith(HASH_PREFIX) and h_mock.startswith(HASH_PREFIX)
