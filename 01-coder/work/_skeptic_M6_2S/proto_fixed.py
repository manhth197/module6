"""Same prototype but WITH the reviewer's proposed fix: guard isinstance(row, Mapping)
before row.get(...). Confirms the fix converts the crash into the documented graceful return.
"""
from collections.abc import Mapping
import importlib.util, sys

# reuse the real primitives
from app.measurement.models.consumed import DataSensitivity, ExternalSendPolicy
from app.measurement.registry.validator import _resolve_send_policy, _resolve_sensitivity


class Reader:
    def __init__(self, initial_version=0):
        self._current = initial_version
        self._rows = ()

    def current_registry_version(self):
        return self._current

    def apply(self, feed):
        if feed is None:
            return ("feed_error:none", False, self._current)
        if not isinstance(feed, Mapping):
            return ("feed_error:not_mapping", False, self._current)
        rv = feed.get("registry_version")
        if rv is None or not isinstance(rv, int) or isinstance(rv, bool):
            return ("feed_error:registry_version", False, self._current)
        events = feed.get("events")
        if events is None or not isinstance(events, list):
            return ("feed_error:events", False, self._current)
        for row in events:
            if not isinstance(row, Mapping):                    # <-- THE FIX
                return ("feed_error:row_not_mapping", False, self._current)
            code = row.get("event_code")
            if not code or not str(code).strip():
                return ("feed_error:event_code", False, self._current)
        if rv <= self._current:
            return ("stale", False, self._current)
        # (c) apply
        n = 0
        for row in events:
            _resolve_send_policy(row.get("external_send_policy"))
            _resolve_sensitivity(row.get("data_sensitivity"))
            n += 1
        self._current = rv
        self._rows = tuple(events)
        return ("applied", True, self._current)


def probe(label, feed):
    r = Reader(0)
    try:
        reason, applied, ver = r.apply(feed)
        print(f"[{label}] applied={applied} reason={reason!r} version_after={ver}")
    except Exception as exc:
        print(f"[{label}] RAISED {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    probe("row=int(42)", {"registry_version": 1, "events": [{"event_code": "OK"}, 42]})
    probe("row=bare str", {"registry_version": 1, "events": ["EVENTCODE"]})
    probe("row=None", {"registry_version": 1, "events": [None]})
    probe("valid", {"registry_version": 1, "events": [{"event_code": "purchase"}]})
