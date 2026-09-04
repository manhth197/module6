"""Staged platform transport (M6.2D) — the Integration-layer Transport that builds + logs but NEVER sends.

Implements the M6.2C `Transport` port (`deliver(item)`): resolve the source conversion (read-only), enforce the
OFFLINE-after-ORDER_VERIFIED guard (RULE-003, defense-in-depth over the fan-out), build a PII-safe payload with
the SHARED platform event_id (hash policy — no raw PII), record a `PlatformResultLog` entry, then —
`external_send=OFF` (H01) — raise `ExternalSendBlocked` so the dispatcher HOLDS the item. NO real platform call,
ever. Platform auth tokens would be `secret_ref`-only (none used while staged; no connector = M6-OD-004).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import config
from app.measurement.integration.payload import build_platform_payload
from app.measurement.integration.result_log import PlatformResultLog, PlatformResultRecord, SendResult
from app.measurement.models.measurement_outbox import MeasurementPlatform
from app.measurement.outbox.transport import ExternalSendBlocked

_ORDER_VERIFIED = "ORDER_VERIFIED"


class OfflineNotVerified(Exception):
    """OFFLINE conversion attempted for a non-ORDER_VERIFIED source (RULE-003, FAIL-001)."""


class StagedPlatformTransport:
    """The M6.2D staged transport wired into the measurement dispatcher. Builds the discipline; sends nothing."""

    def __init__(self, conversion_store: Any, result_log: PlatformResultLog) -> None:
        self._conversions = conversion_store
        self._log = result_log

    def deliver(self, item: Any) -> None:
        conversion = self._conversions.get_by_id(item.source_event_id)
        if conversion is None:
            # cannot build a payload without the source -> fail-closed (the dispatcher treats a raise as a
            # transient failure -> bounded retry -> dead-letter; nothing sent, nothing leaked).
            raise RuntimeError("conversion source not found for outbox item")
        # OFFLINE only after ORDER_VERIFIED (RULE-003, FAIL-001) — defense-in-depth over the M6.2C fan-out guard.
        if item.platform is MeasurementPlatform.OFFLINE and conversion.event_code != _ORDER_VERIFIED:
            raise OfflineNotVerified("OFFLINE requires an ORDER_VERIFIED source (RULE-003)")
        payload = build_platform_payload(conversion, item.platform)   # PII-safe; shared event_id
        blocked = not config.is_external_send_enabled()               # True while staged (external_send=OFF)
        self._log.record(PlatformResultRecord(
            platform=payload.platform,
            event_id=payload.event_id,
            event_name=payload.event_name,
            dedup_key=item.dedup_key,
            result=SendResult.BLOCKED_EXTERNAL_SEND_OFF if blocked else SendResult.WOULD_SEND,
            at=datetime.now(timezone.utc),
        ))
        if blocked:
            # staged: the payload was BUILT (PII-safe) and LOGGED, but NO real send happens.
            raise ExternalSendBlocked("external_send=OFF: payload built + logged (PII-safe), NO real send")
        # (unreachable while staged) a real connector send would go here — M6.2D never reaches it.
