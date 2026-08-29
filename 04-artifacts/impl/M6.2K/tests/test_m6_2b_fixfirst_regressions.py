"""M6.2B fix-first BINDING regressions (per 04-artifacts/evidence/decisions/M6-DEFER-F1F2-M6.2B.json).

These pin the four preconditions the M6.2B entry gate BOUND to the coder — closed BEFORE the endpoint is wired:
  F1       the ingest seam NEVER raises: OverflowError / tzinfo-raise ts, and a raising validate / resolve /
           subject_matches / store.append each become an AUDITED DENY.
  F2       the consent gate cannot fail-OPEN via a ConsentSnapshot SUBCLASS that no-ops __post_init__ (raw-str
           scope) — hardened at the decision point (coerce-or-deny).
  MINOR-9  an identifier/PII-shaped token is NOT stored verbatim in the audit sink (a genuine code stays
           diagnostic — SMK-001 audit rõ).
  O1       session_id / correlation_id are masked on every export surface (audit).

All markers below are assembled to avoid any literal PII (no email / phone) in this source.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo

from app.api.track import handle_track_request
from app.measurement.audit import _safe_event_code  # noqa: SLF001 (white-box on the sink policy)
from app.measurement.consent.gate import ConsentGate
from app.measurement.ingest import IngestResult, IngestService
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
from app.measurement.registry.validator import EventValidator

_UTC = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- tiny raising doubles ------------------------------------------------------------------------
class _RaisingValidator:
    def validate(self, event_code):
        raise RuntimeError("registry backend down")


class _RaisingStore:
    def append(self, row):
        raise RuntimeError("store backend down")

    def get(self, key):
        return None


class _RaisingResolver:
    def resolve(self, guest_id):
        raise RuntimeError("guest_contacts down")

    def subject_matches(self, guest_id, subject_ref):
        raise RuntimeError("guest_contacts down")


class _RaisingTz(tzinfo):
    def utcoffset(self, dt):
        raise RuntimeError("tzinfo boom")

    def tzname(self, dt):
        return "BOOM"

    def dst(self, dt):
        return None


def _ev(guest_id=None):
    return dict(
        event_code="VIEW_LANDING", page_id="p", session_id="s", source="web",
        event_ts=_UTC, raw_event_hash="h", guest_id=guest_id,
    )


# ================================================================ F1 — the seam never raises
def test_f1_overflow_event_ts_is_audited_not_raised(registry, store, consent_gate, app_consent_reader, audit):
    svc = IngestService(EventValidator(registry, audit), store, consent_gate, app_consent_reader, audit)
    overflow_ts = datetime.max.replace(tzinfo=timezone(timedelta(hours=-2)))  # -> OverflowError on astimezone
    kw = _ev()
    kw["event_ts"] = overflow_ts
    res = svc.ingest_event(**kw)
    assert isinstance(res, IngestResult) and res.logged is False          # did NOT raise
    assert audit.find("TS_NORMALIZE_FAILED")


def test_f1_tzinfo_that_raises_is_audited_not_raised(registry, store, consent_gate, app_consent_reader, audit):
    svc = IngestService(EventValidator(registry, audit), store, consent_gate, app_consent_reader, audit)
    kw = _ev()
    kw["event_ts"] = datetime(2026, 7, 29, 12, 0, 0, tzinfo=_RaisingTz())
    res = svc.ingest_event(**kw)
    assert isinstance(res, IngestResult) and res.logged is False
    assert audit.find("TS_NORMALIZE_FAILED")


def test_f1_validator_raise_is_audited_not_raised(store, consent_gate, app_consent_reader, audit):
    svc = IngestService(_RaisingValidator(), store, consent_gate, app_consent_reader, audit)
    res = svc.ingest_event(**_ev())
    assert isinstance(res, IngestResult) and res.logged is False
    assert audit.find("VALIDATION_FAILED")


def test_f1_store_append_raise_is_audited_not_raised(registry, consent_gate, app_consent_reader, audit):
    svc = IngestService(EventValidator(registry, audit), _RaisingStore(), consent_gate, app_consent_reader, audit)
    res = svc.ingest_event(**_ev())
    assert isinstance(res, IngestResult) and res.logged is False
    assert res.idempotency_key is None
    assert audit.find("STORE_APPEND_FAILED")


def test_f1_resolver_raise_is_audited_not_raised(registry, store, consent_gate, app_consent_reader, audit):
    svc = IngestService(
        EventValidator(registry, audit), store, consent_gate, app_consent_reader, audit,
        resolver=_RaisingResolver(),
    )
    res = svc.ingest_event(**_ev(guest_id="guest_x"))
    assert isinstance(res, IngestResult)                                  # resolve() raised -> caught
    assert audit.find("IDENTITY_RESOLVE_FAILED")


# ================================================================ F2 — gate cannot fail-open on a subclass
class _EvilSnapshot(ConsentSnapshot):
    """A ConsentSnapshot subclass that SKIPS __post_init__, keeping consent_scope as a RAW STRING (the exact
    F2 attack: it still passes `isinstance(x, ConsentSnapshot)`)."""

    def __post_init__(self) -> None:  # no-op: skip the hardening that would coerce/validate consent_scope
        pass


def test_f2_subclass_raw_scope_is_denied_not_failopen(audit):
    gate = ConsentGate(audit)
    evil = _EvilSnapshot("cs_evil", "subjX", ConsentState.VALID, _UTC, "no_external_measurement_allowed")
    # Pre-F2 this fail-OPEN (substring "external_measurement" in the raw string). F2 denies at the decision point.
    assert gate.evaluate(evil, ConsentScope.EXTERNAL_MEASUREMENT) is False
    assert audit.find("CONSENT_SCOPE_UNTRUSTED_TYPE")


def test_f2_subclass_through_seam_is_egress_ineligible(registry, store, consent_gate, audit):
    from app.measurement.adapters.consent_reader import InMemoryConsentReader
    evil = _EvilSnapshot("cs_evil", "subjX", ConsentState.VALID, _UTC, "no_external_measurement_allowed")
    reader = InMemoryConsentReader(snapshots={"cs_evil": evil})
    svc = IngestService(EventValidator(registry, audit), store, consent_gate, reader, audit)
    kw = _ev(guest_id="subjX")
    kw["consent_snapshot_id"] = "cs_evil"
    res = svc.ingest_event(**kw)
    assert isinstance(res, IngestResult)
    assert res.egress_eligible is False                                   # NOT fail-open
    assert audit.find("CONSENT_SCOPE_UNTRUSTED_TYPE")


# ================================================================ MINOR-9 — audit event_code shape
def test_minor9_identifier_shaped_code_is_wrapped_not_verbatim():
    id_prefix = "cust_" + "9" * 7            # cust_ prefix + a digit run -> identifier-shaped
    digit_run = "REF" + "9" * 7 + "XY"       # embedded 6+ digit run -> identifier-shaped
    assert _safe_event_code(id_prefix) != id_prefix
    assert _safe_event_code(id_prefix).startswith("INVALID_EVENT_CODE[")
    assert _safe_event_code(digit_run) != digit_run


def test_minor9_genuine_codes_stay_diagnostic():
    assert _safe_event_code("VIEW_LANDING") == "VIEW_LANDING"             # SMK-001 audit rõ preserved
    assert _safe_event_code("view_landing") == "view_landing"            # lowercase kept diagnostic
    assert _safe_event_code("ORDER_VERIFIED") == "ORDER_VERIFIED"


# ================================================================ O1 — mask on export
def test_o1_session_and_correlation_masked_on_export(track_deps, make_track_body, audit):
    session_marker = "sess_UNIQUEMARKER_zzz"
    corr_marker = "corr_UNIQUEMARKER_yyy"
    # a REJECTED path makes the endpoint write an audit that references correlation_id (masked, O1).
    body = make_track_body(event_code="HACKME_NOT_REAL", session_id=session_marker, correlation_id=corr_marker)
    res = handle_track_request(body, track_deps)
    assert res.status == "REJECTED"
    blob = " ".join(
        f"{r.action} {r.reason} {r.event_code} {r.subject_masked} {r.detail}" for r in audit.records
    )
    assert session_marker not in blob, "raw session_id must not appear in the audit sink (O1)"
    assert corr_marker not in blob, "raw correlation_id must not appear in the audit sink (O1)"
    # the response returns the caller's OWN correlation_id (their trace id) — not an export surface
    assert res.correlation_id == corr_marker
