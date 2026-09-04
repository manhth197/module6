"""Evidence-pack result models — frozen, read-only, PII-safe.

The `Readiness` enum has NO PASS / READY member (owner-only at PR/PILOT, doc §23; RULE-015): it tops out at
`OWNER_REVIEW_REQUIRED`. A `SmokeResult` is "recorded" only with a correlation_id + evidence_id (or an owner
waiver, for a proposed smoke). `to_public()` masks correlation_id/evidence_id (export choke, RULE-014/H02).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple

from app.measurement.evidence.categories import EvidenceCategory
from app.measurement.masking import mask


class Readiness(str, Enum):
    """Pack readiness — deliberately has NO PASS/READY member (owner-only, doc §23)."""

    OWNER_REVIEW_REQUIRED = "OWNER_REVIEW_REQUIRED"   # complete + honest → hand off to owner
    NOT_READY = "NOT_READY"                           # any incomplete category / un-recorded smoke (fail-closed)


class GapKind(str, Enum):
    STANDING_BLOCKER = "STANDING_BLOCKER"     # always disclosed; does NOT by itself gate readiness (§4.4)
    INCOMPLETE_CATEGORY = "INCOMPLETE_CATEGORY"
    UNRUN_SMOKE = "UNRUN_SMOKE"


@dataclass(frozen=True)
class SmokeResult:
    """One P0 smoke's recorded outcome. `waived` (proposed smokes only) records an explicit owner waiver."""

    smoke_id: str
    status: Optional[str] = None              # e.g. "PASS"/"FAIL" from the run; None if un-run
    correlation_id: Optional[str] = None
    evidence_id: Optional[str] = None
    waived: bool = False

    @property
    def recorded(self) -> bool:
        """Recorded = a real run trace (status + correlation_id + evidence_id) OR an explicit owner waiver. A waiver
        is valid ONLY for a PROPOSED smoke; the assembler STRIPS an invalid waiver on a mandatory owner smoke before
        this is read (see EvidencePackAssembler._smokes), so a mandatory smoke can never be 'recorded' un-run."""
        if self.waived:
            return True
        return bool(self.status) and bool(self.correlation_id) and bool(self.evidence_id)

    def to_public(self) -> Dict[str, Any]:
        return {
            "smoke_id": self.smoke_id,
            "status": self.status,
            "correlation_id": mask(self.correlation_id),   # export-masked (RULE-014 / H02)
            "evidence_id": mask(self.evidence_id),
            "waived": self.waived,
            "recorded": self.recorded,
        }


@dataclass(frozen=True)
class CategoryStatus:
    """One doc §22 category's completeness. COMPLETE only when every mandatory key is present (fail-closed)."""

    category: EvidenceCategory
    complete: bool
    present: Tuple[str, ...]
    missing: Tuple[str, ...]

    def to_public(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "complete": self.complete,
            "present": list(self.present),
            "missing": list(self.missing),
        }


@dataclass(frozen=True)
class GapBlocker:
    """One honest gap/blocker for the owner. `id` is a governance ref (never PII)."""

    id: str
    kind: GapKind
    description: str
    owner: str

    def to_public(self) -> Dict[str, Any]:
        return {"id": self.id, "kind": self.kind.value, "description": self.description, "owner": self.owner}


@dataclass(frozen=True)
class EvidencePack:
    """The assembled owner review package. Read-only data; NO write/trigger/pass/ready handle (RULE-015)."""

    categories: Tuple[CategoryStatus, ...]
    smokes: Tuple[SmokeResult, ...]
    gap_blockers: Tuple[GapBlocker, ...]
    readiness: Readiness
    posture: Mapping[str, str] = field(default_factory=dict)

    def category(self, category: EvidenceCategory) -> Optional[CategoryStatus]:
        for c in self.categories:
            if c.category is category:
                return c
        return None

    def incomplete_categories(self) -> Tuple[CategoryStatus, ...]:
        return tuple(c for c in self.categories if not c.complete)

    def unrecorded_smokes(self) -> Tuple[SmokeResult, ...]:
        return tuple(s for s in self.smokes if not s.recorded)

    def has_standing_blockers(self) -> bool:
        return any(g.kind is GapKind.STANDING_BLOCKER for g in self.gap_blockers)

    def to_public(self) -> Dict[str, Any]:
        return {
            "readiness": self.readiness.value,
            "posture": dict(self.posture),
            "categories": [c.to_public() for c in self.categories],
            "smokes": [s.to_public() for s in self.smokes],
            "gap_blockers": [g.to_public() for g in self.gap_blockers],
        }
