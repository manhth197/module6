"""B1 (M6-OD-003 / M5 PSID hash policy `DAP-M5-cho-M6`, PSID_HASH_POLICY_M5_TMP): one-way, salted PSID hashing.

Per the M5-issued policy: a raw PSID is NEVER stored on any durable row (not even Zone B) — `mask()` (abc***xy)
hides but is REVERSIBLE and is NOT sufficient. A PSID is hashed to
    `psid_hash:` + base64url(HMAC-SHA256(pepper, psid))
which is one-way (non-reversible without the pepper) and salted (per-environment pepper).

Pepper policy (the pepper is a SECRET — NEVER commit / log / emit / put in evidence):
  * resolved from env `M6_PSID_HASH_PEPPER` (a secret_ref at deploy) — an M6-OWN pepper (no shared pepper with M5;
    cross-module joins are a separate owner+chief decision, OUT OF SCOPE here);
  * fail-closed in production: unset ⇒ REFUSE (raise) rather than hash with an absent salt;
  * a FIXED mock pepper is used ONLY in dev/staged tests (never in production) so the staged suite is deterministic.
This module never logs/returns the pepper or the raw psid; the raw psid lives only inside a `hash_psid` call (RAM).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Optional

from app import config

PEPPER_ENV = "M6_PSID_HASH_PEPPER"   # env holding the real per-environment secret pepper (a secret_ref at deploy)
HASH_PREFIX = "psid_hash:"

# Dev/staged mock pepper — a FIXED, NON-SECRET test constant used ONLY when the real pepper is unset AND the posture
# is not production. It keeps the staged suite deterministic; production fail-closes instead of ever using it.
_MOCK_PEPPER = b"m6-staged-mock-pepper-not-a-secret-dev-only"


class PsidHashPolicyError(RuntimeError):
    """Raised when the PSID hash policy cannot be satisfied fail-closed (e.g. no pepper resolvable in production)."""


def resolve_pepper(*, production: Optional[bool] = None) -> bytes:
    """Resolve the HMAC pepper. Real value from env `M6_PSID_HASH_PEPPER` (a secret_ref). Fail-closed in production
    when unset (raise `PsidHashPolicyError`); dev/staged falls back to the fixed mock pepper. `production` defaults
    to the immutable posture (`config.PRODUCTION_FLAG == "ON"`); it is INJECTABLE so the fail-closed branch is
    testable WITHOUT flipping the (immutable) governance flag. The pepper is never logged or emitted."""
    is_prod = (config.PRODUCTION_FLAG == "ON") if production is None else bool(production)
    raw = os.environ.get(PEPPER_ENV)
    if raw:
        return raw.encode("utf-8")
    if is_prod:
        raise PsidHashPolicyError(
            f"{PEPPER_ENV} is unset in production — refusing to hash PSID with an absent pepper (fail-closed)"
        )
    return _MOCK_PEPPER


def hash_psid(psid: Optional[str], *, production: Optional[bool] = None) -> Optional[str]:
    """One-way, salted PSID hash per PSID_HASH_POLICY_M5_TMP. Returns None for a None/blank psid (nothing to hash);
    otherwise `psid_hash:` + base64url(HMAC-SHA256(pepper, psid)). DETERMINISTIC for a given pepper (a stable join
    key) and NON-reversible (the raw psid is never recoverable without the secret pepper). The raw psid exists only
    as this call's argument (RAM) and is never persisted, logged, or emitted."""
    if psid is None:
        return None
    # A PSID is conventionally a numeric string; coerce a non-str identity (int / UUID object) rather than silently
    # dropping a legitimately-present join key — still one-way hashed, so the raw value is never stored/leaked.
    s = psid if isinstance(psid, str) else str(psid)
    if not s.strip():
        return None
    pepper = resolve_pepper(production=production)
    digest = hmac.new(pepper, s.encode("utf-8"), hashlib.sha256).digest()
    return HASH_PREFIX + base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
