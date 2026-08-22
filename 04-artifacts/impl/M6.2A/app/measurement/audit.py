"""Audit trail for reject/hold and identity-mapping decisions (RULE-001 / RULE-006 / RULE-015).

Every rejected/held ingress and every identity resolution is recorded here so nothing is silently lost. Subjects
are masked at the boundary (RULE-014/H02) — a raw identity value never enters an AuditRecord. In-memory sink;
durable persistence is bound at the M6-OD-011 integration step.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple

from app.measurement.masking import mask

# An event_code that matches the Core registry contract shape is safe to record verbatim; anything else
# is attacker-shaped channel DATA (event_code is channel-origin) and is neutralized before it is stored.
# `\A..\Z` (NOT `^..$`): `$` also matches just before a trailing newline, so a code ending in "\n" would
# otherwise pass and be stored with the newline intact. Lower-case is allowed too: a legitimately
# lower-cased event_code is diagnostic (it names the rejected event) and must NOT be masked away, or
# SMK-001's "audit rõ" loses the very code it rejected — control chars / oversize / spaces still fail.
_EVENT_CODE_SHAPE = re.compile(r"\A[A-Za-z0-9_.:\-]{1,64}\Z")
_DETAIL_MAX = 120
_CODE_MAX = 64        # bound for controlled-vocabulary tokens (action / reason)


def _safe_event_code(value: Optional[str]) -> Optional[str]:
    """Store a registry-shaped event_code as-is; otherwise wrap it so a raw attacker payload never lands
    verbatim in the audit trail. The wrapped form strips control chars, bounds length, masks, and keeps a
    short content hash for correlation. The reject/HOLD REASON is a separate field and is untouched, so
    SMK-001 "audit rõ" (a clear reject reason) is preserved. Fixes SEC-PII-01."""
    if value is None:
        return None
    if _EVENT_CODE_SHAPE.match(value):
        return value
    printable = "".join(ch for ch in value if ch.isprintable())[:64]
    digest = hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:8]
    return f"INVALID_EVENT_CODE[{mask(printable)}#{digest}]"


def _bound_code(value: str) -> str:
    """Bound a controlled-vocabulary token (`action` / `reason`).

    These are OUR machine codes from a controlled vocabulary, never channel data, but bounding length and
    stripping control chars is cheap defense-in-depth so a careless internal caller cannot bloat or corrupt
    the sink. Every legitimate code (short, printable) passes through unchanged, so `AuditLog.find(reason)`
    lookups are unaffected."""
    printable = "".join(ch for ch in str(value) if ch.isprintable())
    if len(printable) > _CODE_MAX:
        printable = printable[:_CODE_MAX] + "...[truncated]"
    return printable


def _safe_detail(value: Optional[str]) -> Optional[str]:
    """Bound and control-char-strip the free-text `detail`.

    CONTRACT: `detail` carries a machine reason / enum value / already-masked token — never raw PII. This
    helper is defense-in-depth for a careless caller: it strips control chars and bounds length so a blob
    cannot poison the audit sink. It deliberately does NOT identity-mask (that would corrupt the legitimate
    enum text the field is meant to hold). Fixes SEC-PII-02 (latent)."""
    if value is None:
        return None
    printable = "".join(ch for ch in value if ch.isprintable())
    if len(printable) > _DETAIL_MAX:
        printable = printable[:_DETAIL_MAX] + "...[truncated]"
    return printable


@dataclass(frozen=True)
class AuditRecord:
    action: str                       # e.g. REJECT / HOLD / IDENTITY_RESOLVE
    reason: str                       # machine reason code, e.g. UNKNOWN_EVENT_NOT_IN_REGISTRY
    at: datetime
    event_code: Optional[str] = None
    subject_masked: Optional[str] = None   # already masked; never a raw identity value
    detail: Optional[str] = None


class AuditLog:
    """Append-only in-memory audit sink."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def record(
        self,
        action: str,
        reason: str,
        *,
        event_code: Optional[str] = None,
        subject: Optional[str] = None,
        detail: Optional[str] = None,
        at: Optional[datetime] = None,
    ) -> AuditRecord:
        """Record one audited decision. The sink neutralizes untrusted fields at the boundary so a caller
        cannot leak raw PII or an attacker payload by accident: `subject` is PII-masked, `event_code` is
        shape-checked (registry-shaped kept as-is, else wrapped), and `detail` is control-char-stripped and
        length-bounded. `reason` is a machine code from our own controlled vocabulary and is stored as-is."""
        rec = AuditRecord(
            action=_bound_code(action),
            reason=_bound_code(reason),
            at=at or datetime.now(timezone.utc),
            event_code=_safe_event_code(event_code),
            subject_masked=mask(subject),
            detail=_safe_detail(detail),
        )
        self._records.append(rec)
        return rec

    @property
    def records(self) -> Tuple[AuditRecord, ...]:
        return tuple(self._records)

    def find(self, reason: str) -> Tuple[AuditRecord, ...]:
        return tuple(r for r in self._records if r.reason == reason)

    def __len__(self) -> int:
        return len(self._records)
