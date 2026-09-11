"""Faithful prototype of the M6.2S PLAN section-2 RegistryFeedReader.

Built STRICTLY from PLAN.md section 2 wording, reusing the REAL M6.2R primitives
(_resolve_send_policy / _resolve_sensitivity + the enums). Run with the M6.2R
impl dir on sys.path so `app...` imports resolve.

PLAN section 2, apply(feed):
  (a) feed error / fail-closed: feed is None / not a Mapping / registry_version
      missing or NOT AN INT / events missing or not a list / a row missing a
      non-blank event_code -> NOT applied, version+rows unchanged,
      reason="feed_error:<kind>"
  (b) staleness: registry_version <= current -> NOT applied (reason="stale")
  (c) apply: parse each event -> RegistryFeedRow ... -> only then bump current + store rows
"""
from __future__ import annotations

import os
import sys

M62R = r"D:/M6/Module6-workspace/01-coder/04-artifacts/impl/M6.2R"
sys.path.insert(0, M62R)

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
    registry_version: object          # PLAN types it int; we store what the guard lets through
    rows_applied: int
    reason: str


class RegistryFeedReader:
    def __init__(self, initial_version: int = 0, *, int_guard: str = "isinstance") -> None:
        self._version = initial_version
        self._rows: Tuple[RegistryFeedRow, ...] = ()
        self._int_guard = int_guard   # "isinstance" = the natural way; "strict" = isinstance int and not bool

    def current_registry_version(self):
        return self._version

    def rows(self) -> Tuple[RegistryFeedRow, ...]:
        return self._rows

    def _is_int_version(self, ver: object) -> bool:
        if self._int_guard == "isinstance":
            return isinstance(ver, int)                       # PLAN "natural way": bool passes (bool<:int)
        return isinstance(ver, int) and not isinstance(ver, bool)  # a strict guard the PLAN does NOT state

    def apply(self, feed) -> RegistryFeedApplyResult:
        # (a) feed error / fail-closed
        if feed is None:
            return RegistryFeedApplyResult(False, self._version, 0, "feed_error:none")
        if not isinstance(feed, Mapping):
            return RegistryFeedApplyResult(False, self._version, 0, "feed_error:not_mapping")
        if "registry_version" not in feed:
            return RegistryFeedApplyResult(False, self._version, 0, "feed_error:missing_version")
        ver = feed["registry_version"]
        if not self._is_int_version(ver):
            return RegistryFeedApplyResult(False, self._version, 0, "feed_error:bad_version")
        events = feed.get("events")
        if events is None or not isinstance(events, list):
            return RegistryFeedApplyResult(False, self._version, 0, "feed_error:bad_events")
        for ev in events:
            if not isinstance(ev, Mapping):
                return RegistryFeedApplyResult(False, self._version, 0, "feed_error:bad_row")
            ec = ev.get("event_code")
            if not isinstance(ec, str) or not ec.strip():
                return RegistryFeedApplyResult(False, self._version, 0, "feed_error:missing_event_code")

        # (b) staleness
        if ver <= self._version:
            return RegistryFeedApplyResult(False, self._version, 0, "stale")

        # (c) apply
        parsed = []
        for ev in events:
            raw_active = ev.get("is_active")
            is_active = raw_active if isinstance(raw_active, bool) else False
            parsed.append(RegistryFeedRow(
                event_code=ev["event_code"],
                data_sensitivity=_resolve_sensitivity(ev.get("data_sensitivity")),
                external_send_policy=_resolve_send_policy(ev.get("external_send_policy")),
                is_active=is_active,
                event_group=ev.get("event_group"),
                domain=ev.get("domain"),
                updated_at=ev.get("updated_at"),
            ))
        self._version = ver
        self._rows = tuple(parsed)
        return RegistryFeedApplyResult(True, self._version, len(parsed), "applied")


def show(label, r, reader):
    print(f"{label}: applied={r.applied} registry_version={r.registry_version!r} "
          f"rows_applied={r.rows_applied} reason={r.reason!r} | "
          f"current()={reader.current_registry_version()!r} "
          f"type={type(reader.current_registry_version()).__name__}")


print("=== NATURAL IMPLEMENTATION: isinstance(ver, int) (the way the PLAN reads) ===")
r = RegistryFeedReader()                        # initial_version=0
res = r.apply({"registry_version": True, "events": [{"event_code": "X"}]})
show("REPRO bool True", res, r)
print(f"  isinstance(True, int) = {isinstance(True, int)} ; True == 1 -> {True == 1}")

res2 = r.apply({"registry_version": 1, "events": [{"event_code": "Y"}]})
show("then version=1 ", res2, r)
print(f"  staleness compare 1 <= True -> {1 <= True}")

print()
print("=== CONTRAST: float 6.0 on a fresh reader ===")
r2 = RegistryFeedReader()
res3 = r2.apply({"registry_version": 6.0, "events": [{"event_code": "X"}]})
show("float 6.0     ", res3, r2)

print()
print("=== CONTROL: legit int 1 on a fresh reader ===")
r3 = RegistryFeedReader()
res4 = r3.apply({"registry_version": 1, "events": [{"event_code": "X"}]})
show("int 1         ", res4, r3)

print()
print("=== STRICT guard the PLAN does NOT state: isinstance(int) and not bool ===")
r4 = RegistryFeedReader(int_guard="strict")
res5 = r4.apply({"registry_version": True, "events": [{"event_code": "X"}]})
show("bool True     ", res5, r4)
