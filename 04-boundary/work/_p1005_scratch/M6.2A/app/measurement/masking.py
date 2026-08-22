"""PII masking (RULE-014 / H02).

No raw secret/PII (phone, email, address, raw guest_id/customer_id/psid, tokens) may enter a log or evidence.
`mask()` produces the M6-OD-012 pack-default format `abc***xy` (first 3 + *** + last 2); values too short to
reveal any prefix/suffix without leaking are fully masked. M6-OD-012 is OPEN — this is the parameterized default.
"""
from __future__ import annotations

from typing import Optional

from app.config import MASK_INFIX, MASK_SHORT


def mask(value: Optional[str]) -> Optional[str]:
    """Return a masked representation safe for logs/evidence. None stays None (absence is not PII)."""
    if value is None:
        return None
    s = str(value)
    # Reveal at most 3 leading + 2 trailing chars, and only when doing so leaves >=1 char hidden.
    if len(s) <= 5:
        return MASK_SHORT
    return f"{s[:3]}{MASK_INFIX}{s[-2:]}"
