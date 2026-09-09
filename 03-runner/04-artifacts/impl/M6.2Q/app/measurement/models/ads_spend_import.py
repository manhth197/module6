"""M6.2Q ads_spend_import (A5) — the maker-checker ads-spend import model (owner decision M6-OD-016).

An AdsSpendImport is a STAGED, INERT proposal: a set of mock-CSV spend rows keyed by campaign_id, uploaded by a
MAKER (`uploaded_by`), that a DISTINCT CHECKER must APPROVE before the worker may materialize it into spend records.
The spend source is owner-decided as a phase-1 CSV export from Meta Ads Manager + maker-checker (M6-OD-016): NO
Marketing API, NO new secret, spend is CAMPAIGN-LEVEL (campaign_id), never user PII. Measure/record only — no
pricing, no order state, no commission (RULE-019). Actors (`uploaded_by` / `decided_by`) are governance refs masked
on export (RULE-014); the campaign ids + spend numbers are not PII. `approval_state` transitions only via an
explicit AdsSpendImportDecision (RULE-015); the system never approves its own import.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from app.measurement.masking import mask

CURRENCY_VND = "VND"   # locked constant (mirrors measurement_event.CURRENCY_VND)


class AdsSpendImportState(str, Enum):
    """Maker-checker lifecycle. ONLY an APPROVED import may be materialized (M6-OD-016); no state executes a send."""

    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"          # a RECORDED distinct-checker decision — NOT a real spend / send
    REJECTED = "REJECTED"


class ImportDecisionKind(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


@dataclass(frozen=True)
class AdsSpendImportRow:
    """One mock-CSV spend line, CAMPAIGN-LEVEL (M6-OD-016). `spend_value` is a money amount (VND); `spend_date`
    is the calendar day the spend was reported — the key that cuts spend to a live_session window (leg 3)."""

    campaign_id: str
    spend_value: float
    spend_date: datetime
    currency: str = CURRENCY_VND

    def to_public(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,          # campaign ref, not PII
            "spend_value": self.spend_value,
            "spend_date": self.spend_date.isoformat() if self.spend_date is not None else None,
            "currency": self.currency,
        }


@dataclass(frozen=True)
class AdsSpendImportDecision:
    """An explicit maker-checker decision on an import (mirrors scale OwnerDecision). Requires actor + reason +
    audit + evidence — the system never synthesizes one (RULE-015). `actor` is the CHECKER; masked on export, and
    MUST differ from the import's `uploaded_by` (maker) for an APPROVE (four-eyes)."""

    actor: str
    reason: str
    audit_ref: str
    evidence_ref: str
    decision: ImportDecisionKind
    at: Optional[datetime] = None

    def to_public(self) -> Dict[str, Any]:
        return {
            "actor": mask(self.actor),
            "reason": self.reason,
            "audit_ref": self.audit_ref,
            "evidence_ref": self.evidence_ref,
            "decision": self.decision.value,
            "at": self.at.isoformat() if self.at is not None else None,
        }


@dataclass(frozen=True)
class AdsSpendImport:
    """One inert ads-spend import proposal (M6-OD-016). Frozen; a lifecycle transition produces a NEW record.
    `uploaded_by` is the MAKER; `decided_by` (set on decision) is the CHECKER — a DISTINCT actor for an APPROVE."""

    import_id: str
    rows: Tuple[AdsSpendImportRow, ...]
    window_start: datetime
    window_end: datetime
    uploaded_by: str                                   # MAKER (actor) — masked on export (RULE-014)
    state: AdsSpendImportState = AdsSpendImportState.PROPOSED
    decision: Optional[AdsSpendImportDecision] = None
    decided_by: Optional[str] = None                   # CHECKER (actor) — masked on export; distinct from maker
    created_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None

    @property
    def is_materializable(self) -> bool:
        """Only an APPROVED import may be materialized into spend records (M6-OD-016). PROPOSED/REJECTED never."""
        return self.state is AdsSpendImportState.APPROVED

    def to_public(self) -> Dict[str, Any]:
        """PII-safe export. Actors masked (RULE-014); campaign ids + spend numbers are not PII."""
        return {
            "import_id": self.import_id,
            "rows": [r.to_public() for r in self.rows],
            "window_start": self.window_start.isoformat() if self.window_start is not None else None,
            "window_end": self.window_end.isoformat() if self.window_end is not None else None,
            "uploaded_by": mask(self.uploaded_by),
            "state": self.state.value,
            "decision": self.decision.to_public() if self.decision is not None else None,
            "decided_by": mask(self.decided_by),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at is not None else None,
        }
