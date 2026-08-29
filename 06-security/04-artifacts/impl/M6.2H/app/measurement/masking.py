"""PII masking (RULE-014 / H02).

No raw secret/PII (phone, email, address, raw guest_id/customer_id/psid, tokens) may enter a log or evidence.
`mask()` produces the M6-OD-012 pack-default format `abc***xy` (first 3 + *** + last 2); values too short to
reveal any prefix/suffix without leaking are fully masked. M6-OD-012 is OPEN — this is the parameterized default.

O1 (M6.2B): `session_id` and `correlation_id` are export-masked through this SAME choke point whenever they
cross an export surface (audit `detail`, evidence, server-side error/response logs). The DURABLE row keeps the
raw value (needed for dedup / trace joins); only the exported copy is masked. Callers — the track endpoint and
any audit usage — mask via `mask()`; the durable stores (`web_event_logs`, `ads_measurement_events`) are
unchanged. `mask()` behaviour is unchanged; O1 is enforced at the export callers with this as the choke point.
"""
from __future__ import annotations

from typing import Optional

from app.config import MASK_INFIX, MASK_SHORT


def mask(value: Optional[str]) -> Optional[str]:
    """Return a masked representation safe for logs/evidence. None stays None (absence is not PII)."""
    if value is None:
        return None
    # Strip control / non-printable chars FIRST so a masked value can never carry a raw control char into a
    # log or evidence (e.g. `subject`, the one PII field previously passed to mask() unstripped). Stripping
    # before the length test also prevents padding a short id past the reveal threshold with control chars.
    s = "".join(ch for ch in str(value) if ch.isprintable())
    # Reveal at most 3 leading + 2 trailing chars, and only when doing so leaves >=1 char hidden.
    if len(s) <= 5:
        return MASK_SHORT
    return f"{s[:3]}{MASK_INFIX}{s[-2:]}"
