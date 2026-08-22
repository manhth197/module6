"""The send Transport port + the STAGED transport + the shared bounded-retry delivery mechanic.

The dispatcher workers are the ONLY holders of a Transport (the runtime holds none — RULE-004). In the staged
slice the wired transport is `StagedBlockedTransport`, which raises `ExternalSendBlocked` on every attempt, so
NO real platform send ever happens (external_send=OFF, H01). SMK-016's retry/dead-letter state machine is
exercised by INJECTING a test transport (failing/succeeding) — a test double for the port, not a real send and
not a flag flip. `attempt_delivery` is the ONE place the QUEUED->SENT|RETRY->DEAD_LETTER transitions live,
shared by both dispatchers.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional, Protocol, runtime_checkable

from app import config
from app.measurement.models.measurement_outbox import OutboxStatus


class ExternalSendBlocked(Exception):
    """Raised by the staged transport: external_send=OFF => NO real platform send (H01, RULE-004). Distinct
    from a transient failure — the dispatcher does NOT count it as a retry; the item is held, not lost."""


@runtime_checkable
class Transport(Protocol):
    def deliver(self, item: Any) -> None:
        """Deliver ONE outbox item to its platform. Return None on success; raise `ExternalSendBlocked` when
        external send is disabled; raise any other exception for a retryable (transient) failure."""
        ...


class StagedBlockedTransport:
    """The ONLY transport wired in the staged slice — refuses every send. No real platform call, ever.

    (There is no platform connector in this pack; the concrete Pixel/CAPI/Offline + audience transports bind in
    M6.2D under M6-OD-003/004. Until then external_send stays OFF and this transport enforces it.)"""

    def deliver(self, item: Any) -> None:
        raise ExternalSendBlocked(
            f"external_send={config.EXTERNAL_SEND} (staged, H01): the outbox is drained but NO real send occurs"
        )


def _append(log: Optional[str], entry: str) -> str:
    return entry if not log else f"{log};{entry}"


def attempt_delivery(
    item: Any,
    transport: Transport,
    now: datetime,
    audit: Any,
    *,
    subject_ref: Optional[str] = None,
    backoff_base_seconds: int = 60,
) -> None:
    """Apply ONE delivery attempt to a send-policy-PASSED outbox item, mutating its status/retry state:

    * `ExternalSendBlocked` -> **held** (stays QUEUED, note EXTERNAL_SEND_OFF); NOT a retry, NOT dead-letter —
      the staged reality (nothing sends while external_send=OFF). No silent loss (the row + note remain).
    * a transient error   -> bounded **RETRY** (error_log + next_retry_at + retry_count) -> **DEAD_LETTER** at
      `max_retries` (SMK-016: no infinite retry, no silent loss).
    * success             -> **SENT**.

    Every outcome is audited; `subject_ref` is masked by the audit sink (O1). Only the worker calls this."""
    try:
        transport.deliver(item)
    except ExternalSendBlocked:
        item.status = OutboxStatus.QUEUED
        item.error_log = _append(item.error_log, "EXTERNAL_SEND_OFF")
        item.next_retry_at = None
        audit.record("HOLD", "EXTERNAL_SEND_OFF", subject=subject_ref, detail=f"outbox={item.outbox_id}")
    except Exception:  # transient transport failure -> bounded retry -> dead-letter (SMK-016)
        item.retry_count += 1
        item.error_log = _append(item.error_log, f"SEND_FAILED:attempt={item.retry_count}")
        if item.retry_count >= item.max_retries:
            item.status = OutboxStatus.DEAD_LETTER
            item.next_retry_at = None
            audit.record("HOLD", "OUTBOX_DEAD_LETTER", subject=subject_ref, detail=f"outbox={item.outbox_id}")
        else:
            item.status = OutboxStatus.RETRY
            item.next_retry_at = now + timedelta(seconds=backoff_base_seconds * item.retry_count)
            audit.record(
                "HOLD", "OUTBOX_RETRY", subject=subject_ref,
                detail=f"outbox={item.outbox_id};attempt={item.retry_count}",
            )
    else:
        item.status = OutboxStatus.SENT
        item.sent_at = now
