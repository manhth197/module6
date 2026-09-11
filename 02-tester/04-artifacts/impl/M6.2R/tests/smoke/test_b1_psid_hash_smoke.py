"""Official smoke — slice M6.2O — M6-SMK-026 (proposed — HARDENING, owner review): B1 PSID hash policy
(M6-OD-003 / M5 PSID_HASH_POLICY_M5_TMP).

Authored by TESTER, now formalized on the ledger (M6-P2303 build / M6-P2304 run). B1 landed out-of-band in
impl/M6.2N, carried into impl/M6.2O; slice M6.2O retro-certifies the shipped code. EXECUTED + recorded in M6-P2304
(-> 04-artifacts/test-reports/M6.2O/SMOKE_RESULTS.md).

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (proposed additions row M6-SMK-026):

    Scenario (verbatim):   "A raw PSID supplied at the resolve seam is stored/exported (B1 psid_hash)"
    Expected (verbatim):   "no raw psid on any durable/export surface — as_stored() carries only a one-way `psid_hash:`
                           HMAC value (deterministic per pepper, collision-sensitive); production with the pepper env
                           unset fails closed (PsidHashPolicyError)"

Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below
flips a flag (the fail-closed case injects `production=True` as a call argument; the immutable posture is untouched).

B1 closes the last raw-PII surface on the attribution/live path: a raw PSID is NEVER stored (not even durably) —
`mask()` (abc***xy) is REVERSIBLE and is NOT sufficient, so a PSID is one-way, salted-hashed to
`psid_hash:` + base64url(HMAC-SHA256(pepper, psid)). The pepper is a SECRET (env `M6_PSID_HASH_PEPPER`, a secret_ref
at deploy); production fail-closes when it is unset. The raw psid lives only inside the `hash_psid` call (RAM).

Covers: (a) no-raw-in-store; (b) one-way + `psid_hash:` prefix + deterministic (same pepper) + collision-sensitive;
(c) fail-closed (production + pepper unset -> PsidHashPolicyError); (d) non-vacuity (None/blank psid -> None). All ids
are synthetic and assembled at runtime (no literal PII in source; the pack secret scan forbids it). RULE-014 /
RULE-009 / FAIL-008. Reuses the shared conftest fixtures (make_measurement_event, make_conversion,
attribution_resolver). (Filename `_smoke` suffix keeps a unique pytest basename vs the coder's tests/test_b1_psid_hash.py.)
"""
from __future__ import annotations

import pytest

from app import config
from app.measurement.identity.psid_hash import (
    HASH_PREFIX,
    PEPPER_ENV,
    PsidHashPolicyError,
    hash_psid,
    resolve_pepper,
)

# synthetic psid markers assembled at runtime (no literal PII/id in source; the pack secret scan forbids it):
_PSID = "ps" + "_syn_" + "wxyz"
_PSID2 = "ps" + "_syn_" + "abcd"   # a DISTINCT synthetic psid, for the collision-sensitivity assertion


# --- (a) no-raw-in-store: a raw PSID at the ingest/resolve seam is hashed; as_stored() never carries it ---
def test_b1_no_raw_psid_in_store(make_measurement_event, make_conversion, attribution_resolver):
    """(a) A raw PSID supplied at the resolve seam (`signals["psid"]`) is one-way hashed into the attribution
    context; `as_stored()` (the durable mapping) carries `psid_hash:...` and NEVER the raw psid — not as a value,
    not as a key. `assert _PSID not in str(as_stored())`."""
    event = make_measurement_event("evt_b1", event_code="ORDER_VERIFIED", page_id="p", live_session_id="ls_b1")
    ctx = attribution_resolver.resolve(
        event, make_conversion("ORDER_VERIFIED", source_event_id="evt_b1"),
        signals={"comment_id": "cmt_b1", "psid": _PSID},
    )
    stored = ctx.as_stored()
    assert ctx.psid_hash is not None and ctx.psid_hash.startswith(HASH_PREFIX)   # one-way hash, not raw
    assert stored["psid_hash"] == ctx.psid_hash
    assert "psid" not in stored                                                  # no raw-psid key on the durable row
    assert _PSID not in str(stored), "no raw psid on the durable (as_stored) surface"


# --- (b) one-way + prefix + deterministic (same pepper) + collision-sensitive --------------------
def test_b1_hash_is_one_way_prefixed_deterministic_collision_sensitive():
    """(b) hash_psid: `psid_hash:`-prefixed; one-way (output != input, raw not recoverable from the hash);
    deterministic for a given pepper (a stable trace-join key); collision-sensitive (distinct psids -> distinct
    hashes)."""
    h = hash_psid(_PSID)
    assert h.startswith(HASH_PREFIX)                            # prefix
    assert h != _PSID and _PSID not in h                        # one-way: raw never present in / equal to the hash
    assert hash_psid(_PSID) == h                                # deterministic (same pepper)
    assert hash_psid(_PSID2) != h                               # collision-sensitive: distinct psid -> distinct hash


# --- (c) fail-closed: production + pepper unset -> PsidHashPolicyError (no flag flipped) ----------
def test_b1_fail_closed_production_without_pepper_raises(monkeypatch):
    """(c) Fail-closed (FAIL-008): with the posture PRODUCTION injected True AND the pepper env unset, resolving the
    pepper / hashing REFUSES (raises PsidHashPolicyError) rather than hashing with an absent salt. `production` is
    passed as a call ARGUMENT — the immutable governance flag is NOT flipped (config.PRODUCTION_FLAG stays OFF)."""
    monkeypatch.delenv(PEPPER_ENV, raising=False)               # pepper unset (test-only; ambient env not persistently mutated)
    with pytest.raises(PsidHashPolicyError):
        resolve_pepper(production=True)
    with pytest.raises(PsidHashPolicyError):
        hash_psid(_PSID, production=True)
    assert config.PRODUCTION_FLAG == "OFF"                      # immutable posture untouched by this test


# --- (d) non-vacuity: a None/blank psid hashes to None (nothing to hash) --------------------------
def test_b1_none_or_blank_psid_is_none(make_measurement_event, make_conversion, attribution_resolver):
    """(d) Non-vacuity / fail-safe: a None or blank psid yields None (no hash fabricated); and a context resolved
    with NO psid signal has `psid_hash is None` — so `psid_hash` appears only when a real psid is present (proving
    the hash above is not an always-on artifact)."""
    assert hash_psid(None) is None
    assert hash_psid("") is None
    assert hash_psid("   ") is None
    event = make_measurement_event("evt_b1n", event_code="ORDER_VERIFIED", page_id="p")
    ctx = attribution_resolver.resolve(event, make_conversion("ORDER_VERIFIED", source_event_id="evt_b1n"))
    assert ctx.psid_hash is None
