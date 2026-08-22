"""Hash-policy MECHANISM (RULE-014, FAIL-008) — fail-closed while M6-OD-003 is OPEN.

No raw PII ever leaves Module 6. Every identity field is one-way hashed (config.MEASUREMENT_HASH_ALGO). The set
of fields that MAY be sent RAW is governed by M6-OD-003 (hash policy + permitted send fields, privacy/legal) —
which is OPEN — so the raw allow-list is EMPTY and `HASH_POLICY_RATIFIED` is False: NOTHING is ever emitted raw.
This is the MECHANISM (proven by SMK-017); the ratified policy resolves at the M6.2D exit / owner decision.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, FrozenSet, Mapping

from app import config

# M6-OD-003 OPEN: no field may be sent raw yet -> fail-closed empty allow-list.
_RAW_ALLOWED_FIELDS: FrozenSet[str] = frozenset()


def hash_identity(value: Any) -> str:
    """One-way hash of an identity value (customer/guest key, phone, email, user id, ...). Deterministic; the
    raw value is never recoverable and never emitted."""
    digest = hashlib.new(config.MEASUREMENT_HASH_ALGO, str(value).encode("utf-8")).hexdigest()
    return "h_" + digest


def to_public_safe(user_data: Mapping[str, Any]) -> Dict[str, str]:
    """Map identity `user_data` to a PUBLIC-SAFE payload: hash every value; emit a field raw ONLY if it is on
    the M6-OD-003 ratified allow-list AND the policy is ratified (never true today). Fail-closed by default."""
    out: Dict[str, str] = {}
    for key, value in user_data.items():
        if value is None:
            continue
        if config.HASH_POLICY_RATIFIED and key in _RAW_ALLOWED_FIELDS:
            out[key] = str(value)          # unreachable while M6-OD-003 is OPEN (fail-closed)
        else:
            out[key] = hash_identity(value)
    return out
