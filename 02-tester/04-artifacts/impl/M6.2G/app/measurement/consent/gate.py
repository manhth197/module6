"""RULE-002 consent fail-closed gate.

Without valid consent there is NO external measurement, NO audience sync, NO CRM send. Only a snapshot whose
`consent_state == VALID` and whose `consent_scope` includes the requested egress kind is eligible. Everything
else — MISSING, EXPIRED, OPT_OUT, an absent snapshot, or a scope not granted — is denied.

This gate marks EGRESS ELIGIBILITY ONLY; it never sends anything (external_send=OFF; no dispatcher in M6.2A).
Prevents M6-FAIL-002 (consent violation). Backs smoke M6-SMK-002. Exit-gate leg L2.
"""
from __future__ import annotations

from typing import Optional

from app.measurement.audit import AuditLog
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
from app.measurement.ports import ConsentReader


class ConsentGate:
    def __init__(self, audit: AuditLog) -> None:
        self._audit = audit

    def evaluate(
        self, snapshot: Optional[ConsentSnapshot], scope: ConsentScope
    ) -> bool:
        """Event-time checkpoint. Return True ONLY when egress is permitted; fail-closed otherwise."""
        # Harden the REQUESTED scope. A raw string is dangerous BOTH ways: it can hash/substring-match into
        # the ALLOW branch, and it blows up `scope.value` in every DENY audit (AttributeError). Coerce to a
        # ConsentScope member; an unrecognized scope is denied, not trusted and not crashed.
        try:
            scope = ConsentScope(scope)
        except (ValueError, TypeError):
            self._audit.record("HOLD", "CONSENT_SCOPE_MALFORMED")
            return False

        # Absent snapshot -> fail-closed (never infer/upgrade consent).
        if snapshot is None:
            self._audit.record(
                "HOLD", "CONSENT_SNAPSHOT_ABSENT", detail=scope.value
            )
            return False

        if snapshot.consent_state is not ConsentState.VALID:
            self._audit.record(
                "HOLD", f"CONSENT_{snapshot.consent_state.value.upper()}",
                subject=snapshot.subject_ref, detail=scope.value,
            )
            return False

        # F2 (M6.2B): harden the DECISION POINT, not just the seam. A ConsentSnapshot SUBCLASS that overrides
        # __post_init__ to a no-op keeps `consent_scope` as a RAW STRING and still passes the seam's
        # `isinstance(x, ConsentSnapshot)` guard (Round-4 FIX 2). Here `scope not in <raw str>` would degrade
        # to SUBSTRING matching -> fail-OPEN (a scope the snapshot never granted would read as granted).
        # Require the scope collection to be a real set/frozenset of ConsentScope members; coerce-or-DENY. The
        # gate is now correct regardless of what type the seam hands it (the gate-level half of MAJOR-7).
        scopes = snapshot.consent_scope
        if (
            isinstance(scopes, (str, bytes))
            or not isinstance(scopes, (set, frozenset))
            or not all(isinstance(s, ConsentScope) for s in scopes)
        ):
            self._audit.record(
                "HOLD", "CONSENT_SCOPE_UNTRUSTED_TYPE",
                subject=snapshot.subject_ref, detail=scope.value,
            )
            return False

        # F-B (M6.2D): materialize a REAL frozenset before the membership test. A `set`-SUBCLASS can override
        # __contains__ to return True for ANY scope (fail-OPEN) and still pass the F2 type check above (it IS a
        # set of ConsentScope members). Testing membership on a genuine frozenset built via __iter__ cannot be
        # fooled by a __contains__ override. (Completes the M6.2B/Round-4 MAJOR-7 fix — the reviewer M6-P1209
        # found the F2 type check alone was insufficient.)
        if scope not in frozenset(snapshot.consent_scope):
            self._audit.record(
                "HOLD", "CONSENT_SCOPE_NOT_GRANTED",
                subject=snapshot.subject_ref, detail=scope.value,
            )
            return False

        return True

    def permits_send(
        self,
        snapshot: Optional[ConsentSnapshot],
        scope: ConsentScope,
        consent_reader: ConsentReader,
    ) -> bool:
        """Two-checkpoint send gate for the FUTURE dispatcher (out of scope in M6.2A).

        Requires BOTH the event-time snapshot to be eligible AND current consent to still be VALID at send time.
        Kept here to document the contract; no caller in this slice sends anything (external_send=OFF).
        """
        if not self.evaluate(snapshot, scope):
            return False
        assert snapshot is not None  # evaluate() already rejected None
        current = consent_reader.current_state(snapshot.subject_ref)
        if current is not ConsentState.VALID:
            self._audit.record(
                "HOLD", "CONSENT_LAPSED_AT_SEND_TIME",
                subject=snapshot.subject_ref, detail=scope.value,
            )
            return False
        return True
