"""M6.2Q POST /api/admin/ads/spend-imports — framework-neutral, INERT maker-checker handlers (A5, M6-OD-016).

`handle_import_create(body, deps)` records a PROPOSED ads_spend_import from a mock-CSV body (rows keyed by
campaign_id + a time window + the MAKER `uploaded_by`). `handle_import_decision(body, deps)` records an explicit
DISTINCT-checker APPROVE/REJECT — an APPROVE by the maker is REFUSED (four-eyes, SMK-029). `handle_import_materialize`
runs the worker, materializing ONLY APPROVED imports. `AdsSpendImportDeps` holds ONLY the inert gate + worker +
audit — NO Meta/Marketing-API/network/connector (M6-OD-016 phase-1 CSV only). Owner-decision fields
(actor/reason/audit/evidence) must all be present — the system never synthesizes an approval (RULE-015). PII masked;
HTTP binding is the M6-OD-011 integration step. Mirrors api/scale_requests.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Mapping, Optional, Tuple

from app.measurement.ads_spend.import_gate import AdsSpendImportGate, AdsSpendImportGateViolation
from app.measurement.ads_spend.materializer import AdsSpendMaterializer
from app.measurement.models.ads_spend_import import (
    AdsSpendImport,
    AdsSpendImportDecision,
    AdsSpendImportRow,
    ImportDecisionKind,
)


@dataclass
class AdsSpendImportDeps:
    """Create/decide/materialize-only deps. Holds ONLY the inert gate + worker + audit — NO Meta/Marketing-API,
    no network connector (M6-OD-016). The absence is the boundary the slice asserts."""

    gate: AdsSpendImportGate
    materializer: AdsSpendMaterializer
    audit: Any = None


@dataclass(frozen=True)
class ImportResponse:
    status: str                                 # CREATED | DECIDED | MATERIALIZED | REJECTED_INPUT
    import_id: Optional[str] = None
    state: Optional[str] = None
    materialized: Optional[int] = None
    error_code: Optional[str] = None
    message: Optional[str] = None


def _str(body: Mapping[str, Any], key: str) -> Optional[str]:
    v = body.get(key)
    return v if isinstance(v, str) and v else None


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _parse_rows(raw: Any) -> Tuple[Optional[Tuple[AdsSpendImportRow, ...]], Optional[str]]:
    if not isinstance(raw, (list, tuple)) or not raw:
        return None, "rows must be a non-empty list"
    rows: List[AdsSpendImportRow] = []
    for r in raw:
        if not isinstance(r, Mapping):
            return None, "each row must be an object"
        campaign_id = _str(r, "campaign_id")
        spend_value = r.get("spend_value")
        spend_date = _parse_dt(r.get("spend_date"))
        if not campaign_id:
            return None, "each row needs a campaign_id"
        if isinstance(spend_value, bool) or not isinstance(spend_value, (int, float)):
            return None, "each row needs a numeric spend_value"
        if spend_date is None:
            return None, "each row needs an ISO spend_date"
        currency = _str(r, "currency") or "VND"
        rows.append(AdsSpendImportRow(campaign_id=campaign_id, spend_value=float(spend_value),
                                      spend_date=spend_date, currency=currency))
    return tuple(rows), None


def handle_import_create(body: Any, deps: AdsSpendImportDeps, *, now: Optional[datetime] = None) -> ImportResponse:
    if not isinstance(body, Mapping):
        return ImportResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="body must be an object")
    uploaded_by = _str(body, "uploaded_by")
    if not uploaded_by:
        return ImportResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID",
                              message="uploaded_by (maker) is required")
    rows, err = _parse_rows(body.get("rows"))
    if err:
        return ImportResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message=err)
    window_start = _parse_dt(body.get("window_start")) or min(r.spend_date for r in rows)
    window_end = _parse_dt(body.get("window_end")) or max(r.spend_date for r in rows)

    import_id = "asi_" + hashlib.sha256(
        (uploaded_by + "|" + str([r.campaign_id for r in rows]) + "|" + uuid.uuid4().hex).encode("utf-8")
    ).hexdigest()[:24]

    imp = AdsSpendImport(
        import_id=import_id, rows=rows, window_start=window_start, window_end=window_end,
        uploaded_by=uploaded_by, created_at=now,
    )
    stored = deps.gate.propose(imp)
    return ImportResponse(status="CREATED", import_id=stored.import_id, state=stored.state.value)


def handle_import_decision(body: Any, deps: AdsSpendImportDeps, *, now: Optional[datetime] = None) -> ImportResponse:
    if not isinstance(body, Mapping):
        return ImportResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="body must be an object")
    import_id = _str(body, "import_id")
    if not import_id:
        return ImportResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID", message="import_id is required")
    kind = _str(body, "decision")
    if kind not in ("APPROVE", "REJECT"):
        return ImportResponse(status="REJECTED_INPUT", error_code="SCHEMA_INVALID",
                              message="decision must be APPROVE or REJECT")
    # An owner/checker decision requires ALL of actor/reason/audit_ref/evidence_ref — never synthesized (RULE-015).
    fields = {k: _str(body, k) for k in ("actor", "reason", "audit_ref", "evidence_ref")}
    missing = [k for k, v in fields.items() if not v]
    if missing:
        return ImportResponse(status="REJECTED_INPUT", error_code="OWNER_DECISION_INCOMPLETE",
                              message=f"owner decision missing: {','.join(missing)}")

    decision = AdsSpendImportDecision(
        actor=fields["actor"], reason=fields["reason"], audit_ref=fields["audit_ref"],
        evidence_ref=fields["evidence_ref"], decision=ImportDecisionKind(kind), at=now,
    )
    try:
        result = deps.gate.record_decision(import_id, decision, now=now)
    except AdsSpendImportGateViolation as exc:
        # fail-closed: a self-approve / re-decide refused by the four-eyes gate is the gate WORKING, not an error to
        # hide. Report it as a refusal — nothing was approved, nothing will materialize.
        return ImportResponse(status="REJECTED_INPUT", import_id=import_id,
                              error_code="APPROVAL_REFUSED", message=str(exc))
    return ImportResponse(status="DECIDED", import_id=result.import_id, state=result.state.value)


def handle_import_materialize(body: Any, deps: AdsSpendImportDeps) -> ImportResponse:
    """Run the worker: materialize ONLY APPROVED imports into set-once spend records. Body is unused (server-side)."""
    done = deps.materializer.run_once()
    return ImportResponse(status="MATERIALIZED", materialized=len(done))
