"""Faithful prototype of PLAN.md M6.2S section 2 apply() logic.

Reuses the REAL M6.2R primitives (_resolve_send_policy / _resolve_sensitivity and the
consumed enums) exactly as the plan promises. Implements apply() per the plan's literal
enumeration of feed-error kinds:
  (a) feed error / fail-closed: feed is None / not a Mapping / registry_version missing or
      not an int / events missing or not a list / a row missing a non-blank event_code
      -> NOT applied, version+rows unchanged, reason='feed_error:<kind>'
  (b) staleness: registry_version <= current -> NOT applied (reason='stale')
  (c) apply: parse each event -> row; only then bump current + store rows.

The plan guards the FEED as a Mapping (a) but lists NO 'row not a Mapping' kind, so the
natural row-level access is row.get('event_code') / row.get('external_send_policy') with no
isinstance(row, Mapping) guard. This prototype implements exactly that -- nothing more, nothing
less than the plan's enumeration.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional, Tuple

from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy
from app.measurement.registry.validator import _resolve_send_policy, _resolve_sensitivity


@dataclass(frozen=True)
class RegistryFeedRow:
    event_code: str
    data_sensitivity: DataSensitivity
    external_send_policy: ExternalSendPolicy
    is_active: bool
    event_group: Optional[str] = None
    domain: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass(frozen=True)
class RegistryFeedApplyResult:
    applied: bool
    registry_version: int
    rows_applied: int
    reason: str


class RegistryFeedReader:
    def __init__(self, initial_version: int = 0) -> None:
        self._current = initial_version
        self._rows: Tuple[RegistryFeedRow, ...] = ()

    def current_registry_version(self) -> int:
        return self._current

    def rows(self) -> Tuple[RegistryFeedRow, ...]:
        return self._rows

    def _unchanged(self, reason: str) -> RegistryFeedApplyResult:
        return RegistryFeedApplyResult(False, self._current, 0, reason)

    def apply(self, feed) -> RegistryFeedApplyResult:
        # (a) feed error / fail-closed -----------------------------------------------------
        if feed is None:
            return self._unchanged("feed_error:none")
        if not isinstance(feed, Mapping):
            return self._unchanged("feed_error:not_mapping")
        rv = feed.get("registry_version")
        if rv is None or not isinstance(rv, int) or isinstance(rv, bool):
            return self._unchanged("feed_error:registry_version")
        events = feed.get("events")
        if events is None or not isinstance(events, list):
            return self._unchanged("feed_error:events")
        # "a row missing a non-blank event_code" -> feed error. Natural impl: row.get(...).
        for row in events:
            code = row.get("event_code")          # <-- NO Mapping guard (plan lists none)
            if not code or not str(code).strip():
                return self._unchanged("feed_error:event_code")

        # (b) staleness --------------------------------------------------------------------
        if rv <= self._current:
            return self._unchanged("stale")

        # (c) apply ------------------------------------------------------------------------
        parsed = []
        for row in events:
            esp = _resolve_send_policy(row.get("external_send_policy"))
            ds = _resolve_sensitivity(row.get("data_sensitivity"))
            raw_active = row.get("is_active")
            is_active = raw_active is True
            parsed.append(RegistryFeedRow(
                event_code=str(row.get("event_code")),
                data_sensitivity=ds,
                external_send_policy=esp,
                is_active=is_active,
                event_group=row.get("event_group"),
                domain=row.get("domain"),
                updated_at=row.get("updated_at"),
            ))
        self._current = rv
        self._rows = tuple(parsed)
        return RegistryFeedApplyResult(True, rv, len(parsed), "applied")


def probe(label, feed):
    r = RegistryFeedReader(initial_version=0)
    try:
        res = r.apply(feed)
        print(f"[{label}] applied={res.applied} reason={res.reason!r} "
              f"version_after={r.current_registry_version()} rows_after={len(r.rows())}")
    except Exception as exc:
        print(f"[{label}] RAISED {type(exc).__name__}: {exc}  "
              f"version_after={r.current_registry_version()} rows_after={len(r.rows())}")


if __name__ == "__main__":
    print("=== REPRO: non-Mapping element inside events[] ===")
    probe("row=int(42) after a good row", {"registry_version": 1, "events": [{"event_code": "OK"}, 42]})
    probe("row=bare str", {"registry_version": 1, "events": ["EVENTCODE"]})
    probe("row=None", {"registry_version": 1, "events": [None]})

    print("\n=== CONTRAST: feed-level not-a-Mapping (claimed to work) ===")
    probe("feed=list", [1, 2, 3])
    probe("feed=str", "registry")

    print("\n=== CONTRAST: other feed-error inputs (claimed graceful) ===")
    probe("feed=None", None)
    probe("registry_version missing", {"events": [{"event_code": "OK"}]})
    probe("registry_version=float", {"registry_version": 1.5, "events": [{"event_code": "OK"}]})
    probe("events missing", {"registry_version": 1})
    probe("events not list", {"registry_version": 1, "events": {"event_code": "OK"}})
    probe("row missing event_code", {"registry_version": 1, "events": [{"data_sensitivity": "PII"}]})
    probe("row blank event_code", {"registry_version": 1, "events": [{"event_code": "   "}]})

    print("\n=== SANITY: a fully valid feed applies ===")
    probe("valid unknown esp -> BLOCKED_DEFAULT", {"registry_version": 1, "events": [
        {"event_code": "purchase", "external_send_policy": "WAT", "data_sensitivity": "SENSITIVE"}]})
