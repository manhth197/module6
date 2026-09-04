"""M6.2I retargeting MEASUREMENT — consent-valid-only eligibility, measure-only (doc §8 L143).

`Retargeting chỉ dựa trên event hợp lệ và consent hợp lệ.` This classifier MEASURES which events are
retargeting-eligible: an event is eligible iff (a) it is a recognized engagement signal (doc §8/§10 — a "valid
event", registry-validated upstream at ingest, RULE-001) AND (b) consent is VALID for the AUDIENCE_SYNC egress
kind. It reuses `ConsentGate.evaluate(snapshot, ConsentScope.AUDIENCE_SYNC)` — the EXISTING audience-sync scope
(retargeting is audience; NO new consent scope is invented, RULE-018). Missing / expired / opt-out / scope-not-
granted ⇒ not eligible (fail-closed).

It is MEASURE-ONLY: it counts eligibles; it NEVER enqueues to the audience outbox and NEVER sends. External send /
audience sync is the M6.2C/D outbox+dispatcher's job (consent fail-closed there too); `external_send=OFF`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Tuple

from app.measurement.models.consumed import ConsentScope, ConsentSnapshot

# Recognized engagement / intent signals used to build retargeting audiences (doc §8 flow + §10 taxonomy +
# §8.1 base events). Referenced from canon, none invented. A verified purchase / order-state code is NOT an
# acquisition-retargeting signal and is deliberately excluded; an unrecognized code is never eligible (fail-closed).
RETARGETING_SIGNAL_EVENTS = frozenset({
    "VIEW_LANDING", "CLICK_CTA", "VIEW_ITEM", "ADD_TO_CART", "BEGIN_CHECKOUT",
    "LIVE_VIEW", "LIVE_COMMENT", "MESSENGER_STARTED",
    "AI_PROPOSAL_SENT", "QUOTE_CART_CREATED", "QUOTE_SNAPSHOT_CREATED", "QUOTE_SENT",
})


@dataclass(frozen=True)
class RetargetingReach:
    """The measured retargeting reach — counts only; NO audience payload, NO send target list is produced here."""

    eligible: int
    ineligible: int
    considered: int

    @property
    def eligibility_rate(self) -> Optional[float]:
        return (self.eligible / self.considered) if self.considered else None   # fail-closed (0 considered → None)


class RetargetingMeasurement:
    """Measure-only retargeting-eligibility classifier. Holds only the consent gate — no Transport / outbox /
    connector handle (it cannot send)."""

    def __init__(self, consent_gate: Any) -> None:
        self._gate = consent_gate

    def is_eligible(self, event_code: Any, consent_snapshot: Optional[ConsentSnapshot]) -> bool:
        """Eligible iff a recognized engagement signal AND consent VALID for AUDIENCE_SYNC (fail-closed)."""
        if not isinstance(event_code, str) or event_code not in RETARGETING_SIGNAL_EVENTS:
            return False   # unrecognized / non-engagement event → never eligible (fail-closed, RULE-001-aligned)
        return self._gate.evaluate(consent_snapshot, ConsentScope.AUDIENCE_SYNC)

    def measure(self, events_with_consent: Iterable[Tuple[Any, Optional[ConsentSnapshot]]]) -> RetargetingReach:
        """Count eligible / ineligible over (event_code, consent_snapshot) pairs. Measure-only — produces counts,
        never an audience list and never a send."""
        eligible = 0
        considered = 0
        for event_code, snapshot in events_with_consent:
            considered += 1
            if self.is_eligible(event_code, snapshot):
                eligible += 1
        return RetargetingReach(eligible=eligible, ineligible=considered - eligible, considered=considered)

    def eligible_event_codes(self, events_with_consent: Iterable[Tuple[Any, Optional[ConsentSnapshot]]]) -> List[str]:
        """The distinct eligible event codes (a measurement view for evidence) — NOT a send/audience target list."""
        seen: List[str] = []
        for event_code, snapshot in events_with_consent:
            if self.is_eligible(event_code, snapshot) and event_code not in seen:
                seen.append(event_code)
        return seen
