"""Ingest seam — integrated fail-closed behaviour + measure-only boundary guard (staged posture).

Ties SMK-001 (unknown event) and SMK-002 (valid event, missing consent) through the single ingest entry point,
and asserts the slice sends/scales nothing (external_send=OFF; no dispatcher exists).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app import config
from app.measurement.ingest import IngestService, IngestResult
from app.measurement.models.consumed import ConsentScope
from app.measurement.registry.validator import EventDecision

TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _svc(validator, store, consent_gate, resolver):
    return IngestService(validator, store, consent_gate, resolver)


def test_smk_001_unknown_event_not_logged_but_audited(validator, store, consent_gate, resolver, audit):
    svc = _svc(validator, store, consent_gate, resolver)
    res = svc.ingest_event(
        event_code="UNKNOWN_X", page_id="p1", session_id="s1", source="web",
        event_ts=TS, raw_event_hash="h",
    )
    assert res.validation.decision is EventDecision.REJECT
    assert res.logged is False
    assert len(store) == 0                       # unknown event never becomes a measurement row
    assert audit.find("UNKNOWN_EVENT_NOT_IN_REGISTRY"), "still durably audited (never silently lost)"


def test_smk_002_valid_event_missing_consent_logged_but_not_eligible(
    validator, store, consent_gate, resolver, consent_rows
):
    svc = _svc(validator, store, consent_gate, resolver)
    res = svc.ingest_event(
        event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
        event_ts=TS, raw_event_hash="h",
        consent_snapshot=consent_rows["cs_missing"], consent_scope=ConsentScope.EXTERNAL_MEASUREMENT,
    )
    assert res.logged is True                    # valid event is durably logged (internal record)
    assert res.egress_eligible is False          # missing consent -> no external measurement/audience sync
    assert len(store) == 1


def test_valid_event_even_with_valid_consent_stays_framework_only(
    validator, store, consent_gate, resolver, consent_rows
):
    """Even with VALID consent, staged egress is framework-only (external_send=OFF, M6-OD-003 OPEN)."""
    svc = _svc(validator, store, consent_gate, resolver)
    res = svc.ingest_event(
        event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
        event_ts=TS, raw_event_hash="h",
        consent_snapshot=consent_rows["cs_valid"], consent_scope=ConsentScope.EXTERNAL_MEASUREMENT,
    )
    assert res.egress_eligible is False
    assert "EGRESS_FRAMEWORK_ONLY" in res.notes


def test_duplicate_ingest_is_deduped(validator, store, consent_gate, resolver, consent_rows):
    svc = _svc(validator, store, consent_gate, resolver)
    kw = dict(
        event_code="VIEW_LANDING", page_id="p1", session_id="s1", source="web",
        event_ts=TS, raw_event_hash="h", consent_snapshot=consent_rows["cs_valid"],
    )
    first = svc.ingest_event(**kw)
    second = svc.ingest_event(**kw)
    assert first.log_created is True
    assert second.log_created is False           # RULE-005 dedup through the ingest path
    assert len(store) == 1


def test_measure_only_boundary(validator, store, consent_gate, resolver):
    """Staged posture: external send OFF; the ingest result exposes eligibility, never a send/scale action."""
    assert config.EXTERNAL_SEND == "OFF"
    assert config.is_external_send_enabled() is False
    svc = _svc(validator, store, consent_gate, resolver)
    # No egress/scale/publish methods on the ingest seam.
    for forbidden in ("send", "dispatch", "publish", "scale", "sync_audience", "post"):
        assert not hasattr(svc, forbidden)
    # Result carries eligibility only.
    assert "egress_eligible" in IngestResult.__dataclass_fields__
    for forbidden_field in ("sent", "dispatched", "scaled", "published"):
        assert forbidden_field not in IngestResult.__dataclass_fields__
