"""Round 3 regression + invariant tests.

Round 2 closed 5 MAJOR by making sub-functions ``raise``. At a measurement seam a raised exception is NOT
fail-closed — it is DATA LOSS (no IngestResult, no log line, no audit). Round 3 keeps every ``raise`` in the
callees but makes the SEAM forgiving: it wraps each external-data call and turns every failure into an AUDITED
DENY. These tests pin that contract fix-by-fix, and — most importantly — the seam-level PROPERTY test at the
bottom closes the whole CLASS of "hostile input escapes the seam" rather than one case at a time.

Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF. All ids are
synthetic; no raw secret/PII.

Fix -> test map:
  FIX A  forgiving seam (never raise; audit every deny)          test_fixa_*  + the property test
  FIX B  consent bound to the correct SUBJECT (FAIL-002)         test_fixb_*
  FIX D  the other half of the consent vocabulary (state/scope)  test_fixd_*
  FIX E  sanitizer hardening                                     test_fixe_*
  (FIX C — the smoke/ingest suites now drive consent through the seam and assert the seam's audit — lives in
   tests/smoke/test_smk_002_*.py and tests/test_ingest_measure_only.py, not here.)
"""
from __future__ import annotations

import itertools
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.ingest import IngestResult, IngestService
from app.measurement.logs.idempotency import build_idempotency_key, normalize_ts
from app.measurement.models.consumed import (
    ConsentScope,
    ConsentSnapshot,
    ConsentState,
    DataSensitivity,
    EventRegistryRow,
    RegistrationState,
)
from app.measurement.registry.validator import EventDecision, EventValidator

_UTC_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- tiny local test doubles (kept out of conftest; specific to these adversarial cases) ----------
class _ThrowingReader:
    """A consent system of record that is DOWN — every call raises (someone else's failing system)."""

    def get(self, _id):
        raise RuntimeError("consent store unreachable")

    def current_state(self, _subject):
        raise RuntimeError("consent store unreachable")


class _StaticReader:
    """Returns a fixed snapshot object regardless of id (used to hand the seam a malformed snapshot that
    BYPASSES ConsentSnapshot.__post_init__, i.e. a junk snapshot from someone else's system)."""

    def __init__(self, snapshot):
        self._snapshot = snapshot

    def get(self, _id):
        return self._snapshot

    def current_state(self, _subject):
        return ConsentState.MISSING


class _Registry:
    def __init__(self, rows):
        self._rows = rows

    def get(self, event_code):
        return self._rows.get(event_code)


def _ingest_valid(svc, **over):
    kw = dict(
        event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
        event_ts=_UTC_TS, raw_event_hash="h",
    )
    kw.update(over)
    return svc.ingest_event(**kw)


# ======================================================================================================
# FIX A — the forgiving seam: a hostile external input becomes an AUDITED DENY, never an escaped exception
# ======================================================================================================
def test_fixa_naive_event_ts_is_audited_deny_not_raised(validator, store, consent_gate, consent_reader, audit):
    """A naive (tz-unaware) event_ts made normalize_ts() raise -> the whole request died (500, no audit).
    Now: the seam catches it, audits TS_NOT_TZ_AWARE, returns a result (not logged, not eligible)."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit)
    res = _ingest_valid(svc, event_ts=datetime(2026, 7, 29, 12, 0, 0))  # naive
    assert isinstance(res, IngestResult)              # did NOT raise
    assert res.logged is False and res.egress_eligible is False
    assert "TS_NOT_TZ_AWARE" in res.notes
    assert audit.find("TS_NOT_TZ_AWARE"), "the rejected event must still be audited (never silently lost)"


def test_fixa_string_event_ts_is_audited_deny_not_raised(validator, store, consent_gate, consent_reader, audit):
    """The single most common beacon bug: `"ts":"2026-07-29T12:00:00"` (a str, no offset) must not 500."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit)
    res = _ingest_valid(svc, event_ts="2026-07-29T12:00:00")  # a raw string from a JSON body
    assert res.logged is False
    assert audit.find("TS_NOT_TZ_AWARE")


def test_fixa_consent_reader_failure_is_audited_deny_not_raised(validator, store, consent_gate, audit):
    """Any failure of the consent store (someone else's system) becomes a Module-6 DENY, not a crash.
    The valid event is still logged, but egress is denied and the id is not written."""
    svc = IngestService(validator, store, consent_gate, _ThrowingReader(), audit)
    res = _ingest_valid(svc, consent_snapshot_id="cs_anything", guest_id="guest_mapped_ok")
    assert isinstance(res, IngestResult)              # did NOT raise
    assert res.logged is True                         # valid event still durably logged
    assert res.egress_eligible is False
    assert "CONSENT_READER_FAILED" in res.notes
    assert audit.find("CONSENT_READER_FAILED")
    row = store.get(res.idempotency_key)
    assert row.consent_snapshot_id is None            # an unverifiable consent ref never enters the log


def test_fixa_malformed_consent_state_is_audited_deny_not_raised(validator, store, consent_gate, audit):
    """A snapshot the reader hands back that BYPASSES ConsentSnapshot construction (raw-string consent_state)
    must never crash the seam. Round 3 caught it at the gate (`CONSENT_STATE_MALFORMED`); **Round 4's type
    boundary (FIX 2) now catches it EARLIER** — a reader value that is not a real ConsentSnapshot is refused
    at `isinstance` (`CONSENT_SNAPSHOT_UNTRUSTED_TYPE`) before it can reach the gate's fail-OPEN membership
    test. The security invariant is unchanged: no raise, egress denied, and the deny is audited (the reason
    code is now the stronger, earlier one). See `tests/test_round4_regressions.py` for the MAJOR-7 proof."""
    junk = SimpleNamespace(
        consent_snapshot_id="cs_junk", subject_ref="guest_mapped_ok",
        consent_state="VALID", consent_scope=frozenset(), captured_at=_UTC_TS,
    )
    svc = IngestService(validator, store, consent_gate, _StaticReader(junk), audit)
    res = _ingest_valid(svc, consent_snapshot_id="cs_junk", guest_id="guest_mapped_ok")
    assert isinstance(res, IngestResult)              # did NOT raise
    assert res.egress_eligible is False
    assert "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" in res.notes
    assert audit.find("CONSENT_SNAPSHOT_UNTRUSTED_TYPE")


# ======================================================================================================
# FIX B — consent must be bound to the event's SUBJECT (FAIL-002): one person's consent may not authorize
#          another's event, even when the id is genuinely reader-issued
# ======================================================================================================
def test_fixb_consent_issued_for_another_subject_is_denied_and_id_not_logged(
    validator, store, consent_gate, consent_reader, audit, resolver
):
    """`cs_valid_b` is a VALID, reader-issued consent for subject guest_B. Attached to an event for guest_A
    it must be refused: egress denied, CONSENT_SUBJECT_MISMATCH audited, and the id NEVER written to the
    append-only (RULE-007, un-editable) log. The event itself is still logged."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit, resolver=resolver)
    res = _ingest_valid(svc, consent_snapshot_id="cs_valid_b", guest_id="guest_A")
    assert res.logged is True
    assert res.egress_eligible is False
    assert "CONSENT_SUBJECT_MISMATCH" in res.notes
    assert audit.find("CONSENT_SUBJECT_MISMATCH")
    row = store.get(res.idempotency_key)
    assert row.consent_snapshot_id is None, "a consent id for a different subject must never enter the log"


def test_fixb_consent_keyed_by_trusted_customer_mapping_is_bound(
    validator, store, consent_gate, consent_reader, audit, resolver
):
    """Control (do not over-deny): consent keyed by a CUSTOMER id (cust_0001) binds for a guest that is
    trustedly mapped to that customer (guest_mapped_ok -> cust_0001, with audit)."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit, resolver=resolver)
    res = _ingest_valid(svc, consent_snapshot_id="cs_valid_cust", guest_id="guest_mapped_ok")
    assert "CONSENT_SUBJECT_MISMATCH" not in res.notes
    row = store.get(res.idempotency_key)
    assert row.consent_snapshot_id == "cs_valid_cust"


def test_fixb_no_guest_id_cannot_verify_subject_so_consent_is_dropped(
    validator, store, consent_gate, consent_reader, audit
):
    """With no guest_id there is nothing to verify a consent id against -> fail-closed: id not written."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit)
    res = _ingest_valid(svc, consent_snapshot_id="cs_valid")  # no guest_id
    assert "CONSENT_SUBJECT_MISMATCH" in res.notes
    row = store.get(res.idempotency_key)
    assert row.consent_snapshot_id is None


def test_fixb_consent_reader_is_now_mandatory(validator, store, consent_gate):
    """R2.3's decision to leave consent_reader Optional is REVERSED: it (and the audit sink) are required."""
    with pytest.raises(TypeError):
        IngestService(validator, store, consent_gate)  # type: ignore[call-arg]


# ======================================================================================================
# FIX D — harden the OTHER half of the consent vocabulary: consent_state (snapshot) + requested scope
# ======================================================================================================
def test_fixd_raw_string_consent_state_is_rejected_at_construction():
    """A raw "VALID"/"MISSING" string state constructs a snapshot that later explodes `.value.upper()`."""
    with pytest.raises(TypeError):
        ConsentSnapshot(
            "cs_rawstate", "subj", "VALID", _UTC_TS,  # type: ignore[arg-type]
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        )


def test_fixd_none_consent_state_is_rejected_at_construction():
    with pytest.raises(TypeError):
        ConsentSnapshot("cs_nonestate", "subj", None, _UTC_TS, frozenset())  # type: ignore[arg-type]


def test_fixd_malformed_requested_scope_is_denied_not_crashed(consent_gate, consent_rows):
    """A raw, unrecognized requested scope is denied (CONSENT_SCOPE_MALFORMED), never trusted, never crashed."""
    assert consent_gate.evaluate(consent_rows["cs_valid"], "not_a_real_scope") is False  # type: ignore[arg-type]
    assert consent_gate._audit.find("CONSENT_SCOPE_MALFORMED")  # noqa: SLF001 (white-box on the shared sink)


def test_fixd_raw_scope_on_a_deny_path_does_not_crash(consent_gate, consent_rows):
    """A raw *valid-value* scope string on a DENY path (missing consent) is coerced, denied via
    CONSENT_MISSING, and does NOT crash `scope.value` in the deny audit."""
    assert consent_gate.evaluate(consent_rows["cs_missing"], "external_measurement") is False  # type: ignore[arg-type]
    assert consent_gate._audit.find("CONSENT_MISSING")  # noqa: SLF001


# ======================================================================================================
# FIX E — sanitizer hardening (cheap but real)
# ======================================================================================================
def test_fixe_event_code_with_trailing_newline_is_not_stored_raw():
    """`$` matched before a trailing newline, so "VIEW_LANDING\\n" passed and was stored with the newline.
    `\\Z` fixes it: the code is wrapped, not kept verbatim."""
    a = AuditLog()
    a.record("REJECT", "UNKNOWN_EVENT_NOT_IN_REGISTRY", event_code="VIEW_LANDING\n")
    rec = a.records[-1]
    assert rec.event_code != "VIEW_LANDING\n"
    assert "\n" not in (rec.event_code or "")


def test_fixe_lowercase_event_code_is_kept_diagnostic():
    """A legitimately lower-cased event_code must NOT be masked away — SMK-001 must still name the code."""
    a = AuditLog()
    a.record("REJECT", "UNKNOWN_EVENT_NOT_IN_REGISTRY", event_code="view_landing")
    assert a.records[-1].event_code == "view_landing"


def test_fixe_none_key_component_is_distinct_from_literal_none():
    """An ABSENT (None) component and the literal string "None" are different events -> different keys."""
    ts = normalize_ts(_UTC_TS)
    k_absent = build_idempotency_key("E", None, "s", "h", ts)   # type: ignore[arg-type]
    k_literal = build_idempotency_key("E", "None", "s", "h", ts)
    assert k_absent != k_literal


def test_fixe_subject_control_chars_are_stripped_in_the_audit_sink():
    """`subject` was the one PII field not control-char stripped before masking."""
    a = AuditLog()
    a.record("HOLD", "CONSENT_SUBJECT_MISMATCH", subject="gu\x00st\n_secret")
    sm = a.records[-1].subject_masked or ""
    assert "\n" not in sm and "\x00" not in sm


def test_fixe_action_and_reason_are_length_bounded():
    a = AuditLog()
    a.record("A" * 200, "R" * 200)
    rec = a.records[-1]
    assert len(rec.action) <= 80 and len(rec.reason) <= 80


def test_fixe_whitespace_only_owner_is_held_not_accepted():
    """An owner that is only whitespace is NOT an owner -> HOLD (fail-closed), not ACCEPT."""
    audit = AuditLog()
    reg = _Registry({"WS": EventRegistryRow("WS", RegistrationState.ACTIVE, owner="   ")})
    result = EventValidator(reg, audit).validate("WS")
    assert result.decision is EventDecision.HOLD
    assert result.reason == "MISSING_OWNER"


def test_fixe_raw_data_sensitivity_token_defaults_to_pii():
    """A raw/unknown data_sensitivity token must not defeat the MISSING=>PII default -> normalized to PII."""
    audit = AuditLog()
    reg = _Registry({
        "RAW": EventRegistryRow(
            "RAW", RegistrationState.ACTIVE, owner="core.tracking",
            data_sensitivity="weird_level",  # type: ignore[arg-type]
        )
    })
    result = EventValidator(reg, audit).validate("RAW")
    assert result.decision is EventDecision.ACCEPT
    assert result.data_sensitivity is DataSensitivity.PII


# ======================================================================================================
# §7 — the seam INVARIANT (closes the whole class, not one case): for EVERY hostile input combination,
#      ingest_event() never raises, and every non-logged (denied/held) event carries at least one audit.
# ======================================================================================================
def test_seam_never_raises_and_every_denial_is_audited(registry, store):
    aware = _UTC_TS
    naive = datetime(2026, 7, 29, 12, 0, 0)

    # snapshots a reader can return; the two SimpleNamespace ones deliberately bypass __post_init__ to model
    # a junk snapshot handed back by someone else's system.
    good_same = ConsentSnapshot(
        "cs_good", "subjX", ConsentState.VALID, aware, frozenset({ConsentScope.EXTERNAL_MEASUREMENT})
    )
    good_other = ConsentSnapshot(
        "cs_other", "subjY", ConsentState.VALID, aware, frozenset({ConsentScope.EXTERNAL_MEASUREMENT})
    )
    junk_state = SimpleNamespace(
        consent_snapshot_id="cs_junk", subject_ref="subjX",
        consent_state="VALID", consent_scope=frozenset(), captured_at=aware,
    )
    none_state = SimpleNamespace(
        consent_snapshot_id="cs_none", subject_ref="subjX",
        consent_state=None, consent_scope=frozenset(), captured_at=aware,
    )
    rows = {"cs_good": good_same, "cs_other": good_other, "cs_junk": junk_state, "cs_none": none_state}

    ts_values = [aware, naive, "2026-07-29T12:00:00", None, 123]
    id_values = ["cs_good", "cs_other", "cs_never", None, "", "cs_junk", "cs_none"]
    reader_values = [_StaticReaderMap(rows), _ThrowingReader()]
    code_values = ["VIEW_LANDING", "view_landing", "EVT\n", "X" * 500, "EVT\x00X"]

    for ts, cid, reader, code in itertools.product(ts_values, id_values, reader_values, code_values):
        audit = AuditLog()
        svc = IngestService(EventValidator(registry, audit), store, ConsentGate(audit), reader, audit)
        before = len(audit)
        res = svc.ingest_event(
            event_code=code, page_id="p", session_id="s", source="web",
            event_ts=ts, raw_event_hash="h",
            consent_snapshot_id=cid, guest_id="subjX",
        )
        # We reached this line for every combination => the seam NEVER raised on hostile input.
        assert isinstance(res, IngestResult)
        if not res.logged:
            assert len(audit) > before, (
                f"a non-logged (denied/held) event must be audited: "
                f"ts={ts!r} cid={cid!r} reader={type(reader).__name__} code={code!r}"
            )


class _StaticReaderMap:
    """Dict-backed reader for the property test (distinct from _StaticReader which returns one fixed object)."""

    def __init__(self, rows):
        self._rows = rows

    def get(self, consent_snapshot_id):
        return self._rows.get(consent_snapshot_id)

    def current_state(self, _subject):
        return ConsentState.MISSING
