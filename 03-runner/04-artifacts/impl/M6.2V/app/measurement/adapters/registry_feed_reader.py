"""M6.2S registry-feed reader adapter (chief RELAY_V221 §2.4, M6-OD-018) — consume event-registry-feed.v1 fail-closed.

Consumes a PROPOSED event-registry-feed.v1 as a VALUE OBJECT / dict (NEVER a live HTTP call; the live M3 client is
the out-of-scope seam, ENTRY-003 V221 pending). Staleness-safe by a monotonic `registry_version` (a version <= the
last applied is NOT applied — no downgrade), and fail-closed on every unknown: an unknown `external_send_policy`
coerces to BLOCKED_DEFAULT, an unknown/SENSITIVE `data_sensitivity` to PII (reusing the M6.2P validator coercers), a
missing/non-bool `is_active` to False, and any feed error (None / not a Mapping / bad registry_version [a bool is
NOT an int here] / bad events / a NON-Mapping row / a row missing event_code) leaves the reader UNCHANGED — the
version bumps + rows apply ONLY on a fully-valid feed (all rows parsed first), so the reader never half-applies and a
malformed higher-version feed cannot poison staleness.

The reader CLASSIFIES `external_send_policy` (unknown -> BLOCKED_DEFAULT, never a fabricated ALLOW_EXTERNAL) but
exposes NO egress-permit and opens NO egress — the permit-mapping is the OPEN M6-OD-003 (owner/Sếp), and
EXTERNAL_SEND stays Final OFF. M6 READS the Core registry feed for its own validation; it never writes/invents an
event, reconciles the Core enum, or decides the permit-mapping (RULE-001/018). The feed is governance metadata, not
customer PII (RULE-014). Since the endpoint is `?since_version={n}` (a DELTA), a valid feed UPSERTs its rows onto the
prior snapshot (never dropping rows the delta omits); a de-registered event arrives as `is_active=False`
(present-but-inactive, fail-closed — never false-ALLOWed). TODO(contract): explicit tombstone/removal semantics
await chief finalization.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy
from app.measurement.models.registry_feed import RegistryFeedRow
from app.measurement.registry.validator import _resolve_send_policy, _resolve_sensitivity


@dataclass(frozen=True)
class RegistryFeedApplyResult:
    applied: bool
    registry_version: int          # the reader's CURRENT version after this call (UNCHANGED on a reject)
    rows_applied: int              # rows parsed + upserted this call (0 on a reject)
    reason: str                    # "applied" | "stale" | "feed_error:<kind>"
    malformed_fields: int = 0      # N6 (M6.2T): count of non-str sibling fields coerced to a fail-closed default


def _nonblank_str(value: Any) -> Optional[str]:
    """A real non-blank string, else None (used for the REQUIRED event_code)."""
    return value if isinstance(value, str) and value.strip() else None


def _opt_str(value: Any) -> Optional[str]:
    """Optional metadata: a real non-empty string, else None — never invented, never coerced from another type."""
    return value if isinstance(value, str) and value != "" else None


# --- leg 3 (M6.2T): input-side customer-PII shape guard on GOVERNANCE fields (RULE-014 / FAIL-008) ---
_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)0\d{9}(?!\d)")                       # VN mobile shape
_LONG_DIGITS_RE = re.compile(r"\d{9,}")                             # a long digit run (phone / id-like)
_PII_ID_PREFIX_RE = re.compile(r"(?i)(?:^|[^A-Za-z])(psid|cust|customer|guest|uid|fbid)[._-]?\d")


def _looks_like_pii(value: Any) -> bool:
    """True iff a GOVERNANCE metadata value carries a CUSTOMER-PII shape — an email, a VN phone / long digit run,
    or a psid/customer/guest-id prefix. A governance code (ORDER_VERIFIED / ads.core / a version like v20260915)
    never matches. The feed must not smuggle customer PII into a governance field; such a row is rejected fail-closed
    (input-side), never stored or exported (this is NOT export masking — DISTINCT from M6-OD-012)."""
    if not isinstance(value, str) or not value:
        return False
    return bool(
        _EMAIL_RE.search(value) or _PHONE_RE.search(value)
        or _LONG_DIGITS_RE.search(value) or _PII_ID_PREFIX_RE.search(value)
    )


def _resolve_typed(raw: Any, resolver: Callable[[Any], Any], enum_type: type) -> Tuple[Any, bool]:
    """N5/BND-01 (M6.2T): guard the raw is `str` / `<enum_type>` / `None` BEFORE the enum value-lookup — a non-str
    non-enum raw is MALFORMED. It still resolves to the resolver's fail-closed default (defense-in-depth; the
    validator stays byte-identical), and we flag it for observability (N6). Returns (resolved, was_malformed)."""
    malformed = raw is not None and not isinstance(raw, (str, enum_type))
    return resolver(raw), malformed


class RegistryFeedReader:
    """In-memory, staleness-safe, fail-closed reader over the PROPOSED event-registry-feed.v1 (value object / dict).
    Holds NO HTTP client / NO live endpoint / NO egress surface."""

    def __init__(self, initial_version: int = 0) -> None:
        self._version = int(initial_version)
        self._by_code: Dict[str, RegistryFeedRow] = {}
        self._order: List[str] = []

    # --- read surface -------------------------------------------------------------------------------
    def current_registry_version(self) -> int:
        return self._version

    def rows(self) -> Tuple[RegistryFeedRow, ...]:
        return tuple(self._by_code[c] for c in self._order)

    def get(self, event_code: str) -> Optional[RegistryFeedRow]:
        return self._by_code.get(event_code)

    def __len__(self) -> int:
        return len(self._order)

    # --- apply (fail-closed) ------------------------------------------------------------------------
    def apply(self, feed: Any) -> RegistryFeedApplyResult:
        """Apply a feed value object / dict fail-closed. Any error / staleness leaves the reader UNCHANGED."""
        # (a) feed-level fail-closed guards over an UNTRUSTED M3 source — NEVER crash, NEVER half-apply.
        if not isinstance(feed, Mapping):
            return self._reject("feed_error:not_mapping")
        version = feed.get("registry_version")
        # bool subclasses int -> exclude it explicitly (a bool is NOT a valid version; red-team fix).
        if not isinstance(version, int) or isinstance(version, bool):
            return self._reject("feed_error:bad_version")
        events = feed.get("events")
        if not isinstance(events, (list, tuple)):
            return self._reject("feed_error:bad_events")

        # (b) staleness: a version <= current is NOT applied (no downgrade, incl. equal).
        if version <= self._version:
            return self._reject("stale")

        # (c) parse ALL rows FIRST (fail-closed) — only mutate state on a fully-valid feed.
        parsed: List[RegistryFeedRow] = []
        malformed_fields = 0
        for row in events:
            if not isinstance(row, Mapping):
                return self._reject("feed_error:row_not_mapping")     # a garbage events[] element -> not applied
            event_code = _nonblank_str(row.get("event_code"))
            if event_code is None:
                return self._reject("feed_error:missing_event_code")
            # leg 3 (M6.2T): a GOVERNANCE field carrying a customer-PII shape -> fail-closed reject at PARSE,
            # version + rows UNCHANGED (input-side reject, NOT export masking; RULE-014 / FAIL-008).
            if any(_looks_like_pii(row.get(f)) for f in ("event_code", "event_group", "domain")):
                return self._reject("feed_error:pii_shape_in_governance_field")
            # N5/N6 (M6.2T): resolve the enum siblings through the typed guard (a non-str -> fail-closed default,
            # flagged for observability); the validator coercers stay byte-identical.
            sensitivity, m1 = _resolve_typed(row.get("data_sensitivity"), _resolve_sensitivity, DataSensitivity)
            policy, m2 = _resolve_typed(row.get("external_send_policy"), _resolve_send_policy, ExternalSendPolicy)
            malformed_fields += int(m1) + int(m2)
            parsed.append(RegistryFeedRow(
                event_code=event_code,
                data_sensitivity=sensitivity,          # None/unknown/SENSITIVE/non-str -> PII
                external_send_policy=policy,           # None/unknown/non-str -> BLOCKED_DEFAULT
                is_active=row.get("is_active") is True,                                      # strict bool -> fail-closed False
                event_group=_opt_str(row.get("event_group")),
                domain=_opt_str(row.get("domain")),
                updated_at=_opt_str(row.get("updated_at")),
            ))

        # fully valid -> UPSERT the delta rows (since_version) + bump the version (never half-applied).
        for r in parsed:
            if r.event_code not in self._by_code:
                self._order.append(r.event_code)
            self._by_code[r.event_code] = r
        self._version = version
        return RegistryFeedApplyResult(True, self._version, len(parsed), "applied", malformed_fields)

    def _reject(self, reason: str) -> RegistryFeedApplyResult:
        """A reject leaves version + rows UNCHANGED (fail-closed, never half-updated)."""
        return RegistryFeedApplyResult(False, self._version, 0, reason, 0)
