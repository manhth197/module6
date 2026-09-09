"""M6.2Q ads-spend import maker-checker gate (A5, M6-OD-016) — the four-eyes control SMK-029 tests.

`propose(import_)` records a PROPOSED import (audited). `record_decision(import_id, decision)` records an EXPLICIT
maker-checker decision: an APPROVE is FAIL-CLOSED REFUSED when the checker is the maker — `decision.actor ==
import_.uploaded_by` (self-approve / single-actor) — so ONLY a DISTINCT checker can move an import to APPROVED, and
only an APPROVED import is ever materialized (materializer). The system never synthesizes a decision (RULE-015).
This gate has NO method that fetches spend from a network or calls the Marketing API (M6-OD-016 phase-1 CSV only).
Every outcome is audited MACHINE-SAFE (import id + decision enum; the untrusted checker free-text reason/audit_ref
is NOT echoed into the audit detail; the checker actor is masked by the audit sink) — mirrors scale_gate.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any, Optional

from app.measurement.models.ads_spend_import import (
    AdsSpendImport,
    AdsSpendImportDecision,
    AdsSpendImportState,
    ImportDecisionKind,
)
from app.measurement.store.ads_spend_import_store import AdsSpendImportStore


def _canon_actor(value: Optional[str]) -> str:
    """Canonical form of an actor ref for the four-eyes DISTINCTNESS test: strip surrounding whitespace + casefold.
    So `alice`, `Alice`, and `alice ` all resolve to the SAME principal (a checker cannot defeat maker != checker
    with a trivial case/whitespace alias). The RAW `decision.actor` is still what gets recorded — only the
    comparison is normalized. (Adversarial red-team fix: a raw `==` let a case/whitespace variant of the maker's own
    ref self-approve.) Identity/auth binding is deferred to M6-OD-011; canonicalizing here keeps the control
    fail-closed for when a real case/whitespace-variant identity is bound to this field."""
    return (value or "").strip().casefold()


class AdsSpendImportGateViolation(Exception):
    """Raised when a decision is REFUSED — a self-approve (maker == checker, canonicalized), a missing/blank checker,
    or a re-decide of an already-decided import. A fail-closed hard stop: NOT approved, nothing materialized."""


class AdsSpendImportGate:
    def __init__(self, store: AdsSpendImportStore, audit: Any = None) -> None:
        # M6-OD-016: no Marketing API, no network connector — this gate holds only the inert import store.
        self._store = store
        self._audit = audit

    def propose(self, import_: AdsSpendImport) -> AdsSpendImport:
        """Record a PROPOSED import (inert). Never fetches / materializes anything."""
        stored = self._store.create(import_)
        if self._audit is not None:
            self._audit.record(
                "HOLD", "ADS_SPEND_IMPORT_PROPOSED", subject=import_.uploaded_by,
                detail=f"import={import_.import_id};rows={len(import_.rows)}",
            )
        return stored

    def record_decision(
        self,
        import_id: str,
        decision: AdsSpendImportDecision,
        *,
        now: Optional[datetime] = None,
    ) -> AdsSpendImport:
        """Record an EXPLICIT maker-checker decision. An APPROVE requires a DISTINCT checker (four-eyes):
        `decision.actor` MUST differ from the import's `uploaded_by` — a self-approve / single-actor / missing-actor
        approve is REFUSED (AdsSpendImportGateViolation). REJECT is always recordable. Never synthesized."""
        imp = self._store.get(import_id)
        if imp is None:
            raise AdsSpendImportGateViolation(f"unknown ads_spend_import {import_id}")
        if imp.state in (AdsSpendImportState.APPROVED, AdsSpendImportState.REJECTED):
            raise AdsSpendImportGateViolation(f"ads_spend_import {import_id} already {imp.state.value}")

        if decision.decision is ImportDecisionKind.REJECT:
            new = replace(imp, state=AdsSpendImportState.REJECTED, decision=decision,
                          decided_by=decision.actor, decided_at=now)
            self._store.update_state(new)
            self._audit_decision("ADS_SPEND_IMPORT_REJECTED", decision, import_id)
            return new

        # APPROVE — four-eyes fail-closed gate BEFORE recording the approval (maker != checker, RULE-015). The
        # distinctness test is CANONICALIZED (strip + casefold) so a case/whitespace alias of the maker cannot
        # self-approve; a blank / whitespace-only checker is refused outright (its canonical form is empty).
        checker = _canon_actor(decision.actor)
        if not checker or checker == _canon_actor(imp.uploaded_by):
            raise AdsSpendImportGateViolation(
                "self-approve rejected: the approver (checker) must be a DISTINCT actor from the uploader (maker)"
            )
        new = replace(imp, state=AdsSpendImportState.APPROVED, decision=decision,
                      decided_by=decision.actor, decided_at=now)
        self._store.update_state(new)
        self._audit_decision("ADS_SPEND_IMPORT_APPROVED", decision, import_id)
        return new

    def _audit_decision(self, code: str, decision: AdsSpendImportDecision, import_id: str) -> None:
        if self._audit is not None:
            # Machine-safe detail only (mirror scale_gate._audit_decision): the untrusted checker-supplied
            # free-text reason / audit_ref are NOT echoed into the audit `detail` (they could carry PII, and the
            # sink does not identity-mask `detail`). `import_id` is a hash id and `decision` is an enum; the full
            # decision lives in the durable record. `subject` (checker actor) is masked by the audit sink.
            self._audit.record(
                "HOLD", code, subject=decision.actor,
                detail=f"import={import_id};decision={decision.decision.value}",
            )
