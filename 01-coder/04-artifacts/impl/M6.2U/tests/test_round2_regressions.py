"""Round 2 regression tests — one (or more) test per finding from the adversarial reviews
M6-P1005 (boundary) and M6-P1006 (security/PII).

Each test below is RED against the pre-fix (Round 1) code and GREEN after the M6-P1002 Round 2
fixes. The original 38-test suite structurally could not catch these: it used a single aware-UTC
timestamp, no id containing the join delimiter, and consent fixtures built only from enum scopes.

Finding -> test map:
  MAJOR-1   consent scope fail-open on a raw-string consent_scope        test_major1_*
  MAJOR-3   caller-owned mutable scope set retroactively grants a scope  test_major3_*
  MAJOR-2   an unissued consent_snapshot_id reaches the immutable log    test_major2_*
  MAJOR-4   missing UTC normalization -> revenue double-count            test_major4_*
  MAJOR-5   unescaped '|' delimiter -> event swallowed / mislabelled     test_major5_*
  SEC-PII-01 raw attacker-shaped event_code stored in the audit trail    test_secpii01_*
  SEC-PII-02 free-text audit `detail` never bounded / stripped           test_secpii02_*

Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF.
All ids are synthetic; no raw secret/PII.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.measurement.audit import AuditLog
from app.measurement.ingest import IngestService
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState

_UTC_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- MAJOR-1: a raw-string consent_scope must be REJECTED, never substring-matched ----------------
def test_major1_raw_string_consent_scope_is_rejected_not_granted():
    """A raw string "no_external_measurement_allowed" literally denies; the pre-fix code substring-
    matched "external_measurement" INSIDE it (ConsentScope subclasses str) and granted egress. The
    snapshot must now refuse to be built from a raw string at all (fail-closed at construction)."""
    with pytest.raises(TypeError):
        ConsentSnapshot(
            "cs_rawstr", "subj", ConsentState.VALID, _UTC_TS,
            "no_external_measurement_allowed",  # type: ignore[arg-type]
        )


def test_major1_raw_string_element_in_scope_is_rejected():
    """Even a set that CONTAINS a raw string (not a ConsentScope member) must be rejected."""
    with pytest.raises(TypeError):
        ConsentSnapshot(
            "cs_strelem", "subj", ConsentState.VALID, _UTC_TS,
            frozenset({"external_measurement"}),  # type: ignore[arg-type]
        )


# --- MAJOR-3: a caller-owned mutable set must not retroactively grant a scope ---------------------
def test_major3_mutating_source_set_after_construction_does_not_grant(consent_gate):
    """The snapshot must hold an immutable COPY of the scope set. Mutating the caller's original set
    after construction must not change the gate's decision (pre-fix: it aliased and granted)."""
    shared = {ConsentScope.CRM}
    snap = ConsentSnapshot("cs_share", "subj", ConsentState.VALID, _UTC_TS, shared)
    assert consent_gate.evaluate(snap, ConsentScope.EXTERNAL_MEASUREMENT) is False
    shared.add(ConsentScope.EXTERNAL_MEASUREMENT)  # mutate the ORIGINAL set the caller still holds
    assert consent_gate.evaluate(snap, ConsentScope.EXTERNAL_MEASUREMENT) is False, (
        "a later mutation of the source set must not retroactively grant a scope"
    )


# --- MAJOR-2: an unissued consent_snapshot_id must never reach the append-only log ----------------
def test_major2_unresolved_snapshot_id_is_failclosed_and_not_logged(
    validator, store, consent_gate, consent_reader, audit
):
    """A consent_snapshot_id the ConsentReader never issued must be dropped fail-closed: the valid
    event is still logged, but egress is denied and the unverified id is NOT written to the immutable
    web_event_logs row (pre-fix: the caller-supplied id was written verbatim, permanently)."""
    svc = IngestService(
        validator, store, consent_gate,
        resolver=None, consent_reader=consent_reader, audit=audit,
    )
    res = svc.ingest_event(
        event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
        event_ts=_UTC_TS, raw_event_hash="h",
        consent_snapshot_id="cs_never_issued",
    )
    assert res.logged is True                 # the valid event is still durably logged
    assert res.egress_eligible is False        # fail-closed: an unverifiable consent ref -> deny
    assert "CONSENT_SNAPSHOT_UNRESOLVED" in res.notes
    assert audit.find("CONSENT_SNAPSHOT_UNRESOLVED"), "the dropped id must be audited"
    row = store.get(res.idempotency_key)
    assert row is not None
    assert row.consent_snapshot_id is None, "an unissued id must NOT enter the immutable log"


def test_major2_reader_issued_snapshot_id_is_recorded(
    validator, store, consent_gate, consent_reader, audit
):
    """Control (the fix must not over-block): a real, reader-issued id whose subject matches the event IS
    recorded. `cs_valid`'s subject is `guest_mapped_ok`, so the event must carry that guest_id (Round 3
    subject binding — a reader-issued id alone is no longer sufficient; it must belong to this subject)."""
    svc = IngestService(
        validator, store, consent_gate,
        consent_reader=consent_reader, audit=audit,
    )
    res = svc.ingest_event(
        event_code="VIEW_LANDING", page_id="p2", session_id="s2", source="web",
        event_ts=_UTC_TS, raw_event_hash="h",
        consent_snapshot_id="cs_valid", guest_id="guest_mapped_ok",
    )
    row = store.get(res.idempotency_key)
    assert row is not None
    assert row.consent_snapshot_id == "cs_valid"
    assert "CONSENT_SNAPSHOT_UNRESOLVED" not in res.notes
    assert "CONSENT_SUBJECT_MISMATCH" not in res.notes


# --- MAJOR-4: the same instant at different offsets must yield ONE idempotency key -----------------
def test_major4_same_instant_at_different_offset_yields_same_key():
    """05:00Z and 12:00+07:00 are the SAME instant; they must produce the SAME idempotency key,
    otherwise one event is counted twice (revenue double-count). Pre-fix: no astimezone(utc)."""
    utc_ts = datetime(2026, 7, 29, 5, 0, 0, tzinfo=timezone.utc)
    plus7 = timezone(timedelta(hours=7))
    same_instant_plus7 = utc_ts.astimezone(plus7)  # 2026-07-29T12:00:00+07:00 == 05:00Z
    key_utc = build_idempotency_key("E", "p", "s", "h", normalize_ts(utc_ts))
    key_p7 = build_idempotency_key("E", "p", "s", "h", normalize_ts(same_instant_plus7))
    assert key_utc == key_p7, "the same instant must map to exactly one idempotency key"


def test_major4_naive_datetime_is_rejected_failclosed():
    """A naive (tz-unaware) datetime is ambiguous and must be rejected, not silently normalized."""
    with pytest.raises(ValueError):
        normalize_ts(datetime(2026, 7, 29, 12, 0, 0))  # no tzinfo


# --- MAJOR-5: an id containing the delimiter must not collide two different events ----------------
def test_major5_delimiter_in_id_does_not_collapse_two_events():
    """Two DIFFERENT events must not share a key just because an id contains the join delimiter '|'.
    page_id/session_id are channel-origin. Pre-fix both serialized to 'E|a|b|c|h|ts' -> one key ->
    the second event swallowed and mislabelled DEDUP_NO_DOUBLE_LOG (data loss disguised as dedup)."""
    ts = normalize_ts(_UTC_TS)
    key_a = build_idempotency_key("E", "a|b", "c", "h", ts)   # page_id="a|b", session_id="c"
    key_b = build_idempotency_key("E", "a", "b|c", "h", ts)   # page_id="a",   session_id="b|c"
    assert key_a != key_b, "a '|' in an id must not forge an idempotency-key collision"


# --- SEC-PII-01: an attacker-shaped event_code must not be stored raw in the audit trail ----------
def test_secpii01_malformed_event_code_is_not_stored_raw():
    """event_code is channel-origin, untrusted DATA. A non-registry-shaped code (control chars,
    oversized, lowercase) must be neutralized before it lands in the audit trail — while the reject
    REASON stays clear (SMK-001 'audit rõ' preserved)."""
    audit = AuditLog()
    nasty = "evt\ninjected: " + ("x" * 200)  # control char + oversized + non-registry shape
    audit.record("REJECT", "UNKNOWN_EVENT_NOT_IN_REGISTRY", event_code=nasty)
    rec = audit.records[-1]
    assert rec.reason == "UNKNOWN_EVENT_NOT_IN_REGISTRY"     # reject reason preserved (audit rõ)
    assert rec.event_code != nasty                            # never stored verbatim
    assert "\n" not in (rec.event_code or "")                # control chars stripped
    assert len(rec.event_code or "") <= 100                  # length bounded


def test_secpii01_registry_shaped_event_code_is_preserved():
    """Control: a well-formed registry event_code passes through unchanged (no over-sanitization)."""
    audit = AuditLog()
    audit.record("REJECT", "UNKNOWN_EVENT_NOT_IN_REGISTRY", event_code="VIEW_LANDING")
    assert audit.records[-1].event_code == "VIEW_LANDING"


# --- SEC-PII-02: free-text audit `detail` is bounded and control-char stripped --------------------
def test_secpii02_detail_is_control_char_stripped_and_bounded():
    """`detail` is enum/machine-reason text by contract; as defense-in-depth the sink strips control
    chars and bounds length so a careless caller cannot inject a control-char / oversized blob."""
    audit = AuditLog()
    audit.record("HOLD", "SOME_REASON", detail="line1\nline2" + ("y" * 300))
    detail = audit.records[-1].detail or ""
    assert "\n" not in detail
    assert len(detail) <= 140
