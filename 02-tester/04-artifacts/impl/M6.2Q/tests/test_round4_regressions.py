"""Round 4 regression + invariant tests — close the INPUT TYPE-BOUNDARY class at the seam entry.

Round 3 made the seam forgiving for wrong-VALUE input (a naive ts, a reader that raises). Two wrong-TYPE
holes remained, both probe-confirmed on the real seam:

  MAJOR-7  the seam never type-checked the VALUE `consent_reader.get()` RETURNS. A duck-typed object (never
           through `ConsentSnapshot.__post_init__`) whose `consent_scope` is a RAW STRING fails OPEN on the
           gate's substring membership test ("external_measurement" is a substring of
           "no_external_measurement_allowed"), and its id was written to the append-only log.
  MAJOR-6  a non-`str` channel scalar (event_code/guest_id/... as a JSON list/dict/number/None) made a callee
           raise `TypeError` straight out of the seam (0 audit); page_id/session_id/source/raw_event_hash as a
           list were silently ACCEPTED as garbage (`str(list)` baked into the RULE-005 idempotency key).
  FIX 2b   the caller-supplied `consent_snapshot` OBJECT was dereferenced (.consent_snapshot_id) with no type
           check -> AttributeError out of the seam.

Round 4 installs ONE type boundary at the head of `ingest_event()`: a required non-str -> fail-closed REJECT
(audited, early return); an optional non-str -> dropped to absent (audited); a reader/caller consent value of
the wrong type -> fail-closed (audited), its id never logged. Nothing is `str()`-coerced (that would ingest
garbage). These tests pin each hole AND sweep the whole wrong-TYPE product so the class stays closed at the
later slices (M6.2B wires this exact seam into `POST /api/ads/events/track`).

Governance is immutable here: global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF. All ids are
synthetic; no raw secret/PII.
"""
from __future__ import annotations

import itertools
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.ingest import IngestResult, IngestService
from app.measurement.models.consumed import (
    ConsentScope,
    ConsentSnapshot,
    ConsentState,
)
from app.measurement.registry.validator import EventValidator

_UTC_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- tiny local test doubles (specific to these adversarial cases) --------------------------------
class _ThrowingReader:
    """A consent system of record that is DOWN — every call raises (someone else's failing system)."""

    def get(self, _id):
        raise RuntimeError("consent store unreachable")

    def current_state(self, _subject):
        raise RuntimeError("consent store unreachable")


class _DuckReader:
    """Returns a fixed DUCK-TYPED object for any id — models a reader (another team's system) handing back a
    value that never went through `ConsentSnapshot.__post_init__` (the MAJOR-7 fail-OPEN shape)."""

    def __init__(self, duck):
        self._duck = duck

    def get(self, _id):
        return self._duck

    def current_state(self, _subject):
        return ConsentState.MISSING


class _MapReader:
    """Dict-backed reader (may hold real snapshots and/or duck-types)."""

    def __init__(self, rows):
        self._rows = rows

    def get(self, consent_snapshot_id):
        return self._rows.get(consent_snapshot_id)

    def current_state(self, _subject):
        return ConsentState.MISSING


# The exact MAJOR-7 fail-OPEN duck: a real VALID enum state (passes the gate's `is` check) but a RAW-STRING
# scope that literally says NOT allowed — the pre-fix gate substring-matched "external_measurement" inside it.
_DUCK_OPEN = SimpleNamespace(
    consent_snapshot_id="cs_duck", subject_ref="subjX", consent_state=ConsentState.VALID,
    consent_scope="no_external_measurement_allowed", captured_at=_UTC_TS,
)


def _base_kwargs(**over):
    kw = dict(
        event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
        event_ts=_UTC_TS, raw_event_hash="h",
    )
    kw.update(over)
    return kw


# ======================================================================================================
# MAJOR-7 — a reader-returned DUCK-TYPE consent value is fail-closed; its id never enters the log
# ======================================================================================================
def test_major7_reader_duck_type_snapshot_is_failclosed_and_id_not_logged(registry, store):
    """The reader returns a duck-typed snapshot with a raw-string scope (fails OPEN in the gate). The seam
    must: not raise, deny egress, audit CONSENT_SNAPSHOT_UNTRUSTED_TYPE, and NEVER write the duck id to the
    append-only log — even though the valid event itself is still durably logged."""
    audit = AuditLog()
    svc = IngestService(EventValidator(registry, audit), store, ConsentGate(audit), _DuckReader(_DUCK_OPEN), audit)
    res = svc.ingest_event(**_base_kwargs(
        consent_snapshot_id="cs_duck", guest_id="subjX",
        consent_scope=ConsentScope.EXTERNAL_MEASUREMENT,
    ))
    assert isinstance(res, IngestResult)                    # did NOT raise
    assert res.egress_eligible is False                     # a duck-typed consent never grants egress
    assert "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" in res.notes
    assert audit.find("CONSENT_SNAPSHOT_UNTRUSTED_TYPE")
    row = store.get(res.idempotency_key)
    assert row is not None, "the valid event is still durably logged"
    assert row.consent_snapshot_id is None, "a duck-typed consent id must NEVER enter the append-only log"


# ======================================================================================================
# MAJOR-6 — a non-str REQUIRED channel scalar is a fail-closed REJECT, never raised, never junk-accepted
# ======================================================================================================
@pytest.mark.parametrize("bad_code", [["x"], {"a": 1}, 123, None])
def test_major6_non_str_event_code_is_rejected_not_raised(registry, store, bad_code):
    audit = AuditLog()
    svc = IngestService(EventValidator(registry, audit), store, ConsentGate(audit), _MapReader({}), audit)
    res = svc.ingest_event(**_base_kwargs(event_code=bad_code))
    assert isinstance(res, IngestResult)                    # never raises
    assert res.logged is False and res.egress_eligible is False
    assert res.idempotency_key is None
    assert "FIELD_TYPE_INVALID" in res.notes
    assert audit.find("FIELD_TYPE_INVALID")
    assert len(store) == 0, "a non-str event_code must never become a measurement row"


@pytest.mark.parametrize("field", ["page_id", "session_id", "source", "raw_event_hash"])
@pytest.mark.parametrize("bad", [["x"], 123, None])
def test_major6_non_str_required_field_is_rejected_not_junk_accepted(
    validator, store, consent_gate, consent_reader, audit, field, bad
):
    """Probe found these 4 as a LIST were silently ACCEPTED (`str(list)` baked into the RULE-005 key,
    logged=True). They must be REJECTed fail-closed, never ingested as garbage."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit)
    res = svc.ingest_event(**_base_kwargs(**{field: bad}))
    assert isinstance(res, IngestResult)
    assert res.logged is False, f"{field}={bad!r} must not be junk-accepted into a row"
    assert res.log_created is False
    assert res.idempotency_key is None
    assert "FIELD_TYPE_INVALID" in res.notes
    assert audit.find("FIELD_TYPE_INVALID")
    assert len(store) == 0


@pytest.mark.parametrize("bad_guest", [["g"], {"g": 1}, 123])
def test_major6_non_str_guest_id_is_dropped_before_the_resolver(
    validator, store, consent_gate, consent_reader, audit, resolver, bad_guest
):
    """A non-str guest_id must be dropped to absent AT THE BOUNDARY — the resolver (which would call
    `mask()` / `contacts.get()`) must NEVER see it, so it cannot raise. The valid event is still logged."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit, resolver=resolver)
    res = svc.ingest_event(**_base_kwargs(guest_id=bad_guest))
    assert isinstance(res, IngestResult)                    # never raises
    assert "FIELD_TYPE_INVALID" in res.notes
    assert audit.find("FIELD_TYPE_INVALID")
    assert res.identity is None, "a non-str guest is absent -> no identity resolution attempted"
    assert res.logged is True and res.egress_eligible is False


@pytest.mark.parametrize("bad_optional", [["x"], {"x": 1}, 123])
def test_major6_non_str_optional_ids_are_dropped_absent_not_raised(
    validator, store, consent_gate, consent_reader, audit, bad_optional
):
    """`consent_snapshot_id` and `correlation_id` of the wrong type are dropped to absent (audited), never
    used — a non-str consent handle must not reach the reader, a non-str correlation_id must not reach the
    log row."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit)
    res = svc.ingest_event(**_base_kwargs(
        consent_snapshot_id=bad_optional, correlation_id=bad_optional, guest_id="guest_x",
    ))
    assert isinstance(res, IngestResult)                    # never raises
    assert "FIELD_TYPE_INVALID" in res.notes
    assert audit.find("FIELD_TYPE_INVALID")
    assert res.logged is True                               # valid event logged; bad optionals absent
    row = store.get(res.idempotency_key)
    assert row is not None
    assert row.consent_snapshot_id is None                 # a non-str consent handle never enters the log
    assert row.correlation_id is None                      # a non-str correlation_id never enters the log


# ======================================================================================================
# FIX 2b — the caller-supplied consent_snapshot OBJECT is type-checked before dereference
# ======================================================================================================
def test_fix2b_consent_snapshot_object_without_id_attr_is_absent_not_raised(
    validator, store, consent_gate, consent_reader, audit
):
    """A stray object passed as `consent_snapshot=` (no `.consent_snapshot_id`) blew up the seam with
    AttributeError. Now: wrong type -> treated absent + audited, never raises."""
    svc = IngestService(validator, store, consent_gate, consent_reader, audit)
    res = svc.ingest_event(**_base_kwargs(
        consent_snapshot=object(), guest_id="guest_x",  # type: ignore[arg-type]
    ))
    assert isinstance(res, IngestResult)                    # did NOT raise
    assert res.egress_eligible is False
    assert "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" in res.notes
    assert audit.find("CONSENT_SNAPSHOT_UNTRUSTED_TYPE")


def test_fix2b_real_consent_snapshot_object_is_still_accepted(
    validator, store, consent_gate, consent_reader, audit
):
    """Control (do not over-reject): a REAL ConsentSnapshot passed as the object param still resolves via its
    id — `cs_valid`'s subject is `guest_mapped_ok`, so the event carries that guest and the id binds."""
    snap = ConsentSnapshot(
        "cs_valid", "guest_mapped_ok", ConsentState.VALID, _UTC_TS,
        frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
    )
    svc = IngestService(validator, store, consent_gate, consent_reader, audit)
    res = svc.ingest_event(**_base_kwargs(consent_snapshot=snap, guest_id="guest_mapped_ok"))
    assert "CONSENT_SNAPSHOT_UNTRUSTED_TYPE" not in res.notes
    row = store.get(res.idempotency_key)
    assert row is not None and row.consent_snapshot_id == "cs_valid"


# ======================================================================================================
# §4 — the seam TYPE-BOUNDARY invariant (closes the whole class, not the case): for EVERY wrong-type
#      input combination, ingest_event() never raises, never junk-accepts a non-str into a row, never
#      grants egress on a wrong-typed consent value, and every non-logged event carries >=1 audit record.
# ======================================================================================================
def _assert_seam_invariants(res, audit, before, code):
    # 1. we reached this line for every combination => the seam NEVER raised on wrong-type input.
    assert isinstance(res, IngestResult)
    # 2. every non-logged (denied/held) event carries >=1 audit record (never silently lost).
    if not res.logged:
        assert len(audit) > before, f"a non-logged event must be audited (code={code!r})"
    # 3. NEVER junk-accept: a logged row must have had a genuine str event_code (no str()-coercion of a
    #    list/dict/number/None into a row).
    if res.logged:
        assert isinstance(code, str), f"a non-str event_code must never be logged (code={code!r})"
    # 4. a duck-typed / wrong-typed consent value never grants egress in this staged slice.
    assert res.egress_eligible is False


def test_seam_type_boundary_never_raises_no_junk_accept_every_deny_audited(registry, store):
    aware = _UTC_TS
    real_same = ConsentSnapshot(
        "cs_real", "subjX", ConsentState.VALID, aware, frozenset({ConsentScope.EXTERNAL_MEASUREMENT})
    )
    reader_rows = {"cs_real": real_same, "cs_duck": _DUCK_OPEN}

    # §4 domains -------------------------------------------------------------------------------------
    code_values = ["VIEW_LANDING", "", "view_landing", "EVT\n", "X" * 500, ["x"], {"a": 1}, 123, None]
    guest_values = ["subjX", None, ["g"], {"g": 1}, 123]
    # (consent_snapshot_id, consent_snapshot object) — covers the id path AND the FIX 2b object param
    # (including object() without .consent_snapshot_id and a real snapshot passed as the object).
    consent_inputs = [
        (None, None),
        (None, real_same),
        (None, object()),           # FIX 2b: object without .consent_snapshot_id
        ("cs_real", None),
        ("cs_duck", None),          # reader may return a duck-type for this id
        ("cs_never", None),
        ("", None),
    ]
    reader_values = [_MapReader(reader_rows), _ThrowingReader(), _DuckReader(_DUCK_OPEN)]

    combos = 0
    # (A) fuzz event_code x guest_id x consent-source(object+id) x reader; required scalars stay valid.
    for code, guest, (cid, cobj), reader in itertools.product(
        code_values, guest_values, consent_inputs, reader_values
    ):
        audit = AuditLog()
        svc = IngestService(EventValidator(registry, audit), store, ConsentGate(audit), reader, audit)
        before = len(audit)
        res = svc.ingest_event(
            event_code=code, page_id="p", session_id="s", source="web",
            event_ts=aware, raw_event_hash="h",
            consent_snapshot_id=cid, consent_snapshot=cobj, guest_id=guest,
        )
        _assert_seam_invariants(res, audit, before, code)
        combos += 1

    # (B) fuzz each REQUIRED scalar field as a wrong type, one at a time -> always a hard reject.
    for field, bad in itertools.product(
        ("page_id", "session_id", "source", "raw_event_hash"), (["x"], 123, None)
    ):
        audit = AuditLog()
        svc = IngestService(EventValidator(registry, audit), store, ConsentGate(audit), _MapReader(reader_rows), audit)
        kw = _base_kwargs(**{field: bad})
        before = len(audit)
        res = svc.ingest_event(**kw)
        _assert_seam_invariants(res, audit, before, kw["event_code"])
        assert res.logged is False and res.idempotency_key is None, (
            f"a wrong-typed required scalar {field}={bad!r} must never be logged"
        )
        combos += 1

    assert combos == (9 * 5 * 7 * 3) + (4 * 3)   # 945 + 12 = 957 combinations swept
