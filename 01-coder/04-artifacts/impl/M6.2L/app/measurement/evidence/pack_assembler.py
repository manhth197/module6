"""M6.2K `EvidencePackAssembler` — assemble the doc §22 owner sign-off package (read-only, no self-cert).

`assemble(smoke_results, evidence_refs)` builds an `EvidencePack`:
  * marks each of the 10 doc §22 categories COMPLETE only when ALL its mandatory keys are present with a non-empty
    evidence ref, else INCOMPLETE (fail-closed, FAIL-007);
  * builds a `SmokeResult` for every one of the 18 registered smokes — an un-provided smoke is un-run (fail-closed);
  * ALWAYS merges the canonical `STANDING_GAP_BLOCKERS` (disclosed, never dropped) + INCOMPLETE_CATEGORY +
    UNRUN_SMOKE gaps;
  * sets readiness per the ONE rule (PLAN §4.4): `NOT_READY` iff any category INCOMPLETE OR any smoke un-recorded,
    else `OWNER_REVIEW_REQUIRED`. The standing blockers are DISCLOSED but do NOT gate readiness (production stays
    BLOCKED regardless — that is the owner's review);
  * records the immutable posture (BLOCKED/OFF/OFF + all flags).

There is DELIBERATELY no `pass` / `ready` / `certify` / `sign_off` / `approve` / `enable` / flag-flip method: this
assembler certifies nothing and declares no ROAS Pass / Scale Ready (owner-only, doc §23; RULE-015).
"""
from __future__ import annotations

from dataclasses import replace
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional

from app import config
from app.measurement.evidence.categories import CATEGORY_MANDATORY, EvidenceCategory
from app.measurement.evidence.gap_blockers import STANDING_GAP_BLOCKERS, standing_floor_ok
from app.measurement.evidence.models import (
    CategoryStatus,
    EvidencePack,
    GapBlocker,
    GapKind,
    Readiness,
    SmokeResult,
)
from app.measurement.evidence.smoke_registry import SMOKE_REGISTRY, SmokeStatus


_REF_PREFIX = "ev::"


def _ref_binding(ref: Any) -> Optional[tuple]:
    """B2 (M6.2L): parse the self-describing evidence-ref convention `ev::{category}::{key}` and return the
    (category, key) pair the ref is bound to, or None when the ref is junk / not convention-shaped. A
    fake-but-nonblank ref (e.g. "x") is unbound (None) -> it can satisfy no slot; a convention-shaped ref bound to a
    DIFFERENT category or key (e.g. `ev::Event Registry::FORGED`) does not satisfy this key (well-formed-shape +
    category-AND-key binding, not raw truthiness)."""
    if not isinstance(ref, str):
        return None
    r = ref.strip()
    if not r.startswith(_REF_PREFIX):
        return None
    parts = r.split("::")
    if len(parts) != 3 or not parts[1] or not parts[2]:
        return None
    return (parts[1], parts[2])


def _ref_valid(ref: Any, category: EvidenceCategory, key: str, counts: Mapping[str, int], known_refs: Any) -> bool:
    """A mandatory key is satisfied ONLY by a ref that (1) EXISTS — a well-formed evidence ref (or, when an injected
    `known_refs` AUTHENTICITY oracle is supplied, a member of it), never blank/whitespace/junk; (2) is BOUND to THIS
    (category, key) via the self-describing convention; (3) is pack-wide UNIQUE (used for exactly one slot). Raw
    truthiness is NOT enough (B2 / M6-OD-013 / FAIL-007): a fake ref fails existence+binding, one valid ref
    copy-pasted across slots fails uniqueness, and a convention-shaped ref with the wrong category/key fails binding.

    NOTE (residual, gated on M6-OD-013): in the DEFAULT path (no `known_refs`) "existence" means well-formed-shape +
    (category,key)-binding + uniqueness — it proves SLOT-CORRECTNESS, not AUTHENTICITY. A forger who reconstructs the
    exact canonical `ev::{category}::{key}` string for a slot would still pass in the default path; binding an actual
    issued-refs registry (the `known_refs` oracle) is the owner-integration step (M6-OD-013) that adds authenticity.
    The two SMK-021 forgeries (junk ref; one ref copy-pasted across all slots) are defeated in the default path."""
    if not isinstance(ref, str):
        return False
    r = ref.strip()
    if not r:
        return False
    if counts.get(r, 0) != 1:                          # uniqueness — defeats copy-paste-one-ref
        return False
    if known_refs is not None and r not in known_refs:  # authenticity via injected oracle (forward seam, M6-OD-013)
        return False
    return _ref_binding(r) == (category.value, key)    # well-formed-shape + (category,key)-binding


def _posture_snapshot() -> Mapping[str, str]:
    """A READ-ONLY snapshot of the staged posture (RULE-H01) — recorded in the pack, never changed here. Wrapped in
    a MappingProxyType so the recorded snapshot cannot be tampered with in-memory (e.g. production_flag flipped)."""
    return MappingProxyType({
        "global_gateway_state": config.GLOBAL_GATEWAY_STATE,
        "production_flag": config.PRODUCTION_FLAG,
        "external_send": config.EXTERNAL_SEND,
        "scale_model_ratified": str(config.SCALE_MODEL_RATIFIED),
        "scale_execution_enabled": str(config.SCALE_EXECUTION_ENABLED),
        "hash_policy_ratified": str(config.HASH_POLICY_RATIFIED),
        "learning_autopublish_enabled": str(config.LEARNING_AUTOPUBLISH_ENABLED),
        "learning_content_fill_enabled": str(config.LEARNING_CONTENT_FILL_ENABLED),
        "learning_safe_range_ratified": str(config.LEARNING_SAFE_RANGE_RATIFIED),
    })


class EvidencePackAssembler:
    """Assemble the owner review package from recorded smoke results + evidence refs. Read-only; no self-cert."""

    def assemble(
        self,
        smoke_results: Optional[Mapping[str, SmokeResult]] = None,
        evidence_refs: Optional[Mapping[EvidenceCategory, Mapping[str, Any]]] = None,
        known_refs: Any = None,
    ) -> EvidencePack:
        smoke_results = dict(smoke_results or {})
        evidence_refs = dict(evidence_refs or {})

        categories = self._categories(evidence_refs, known_refs)
        smokes = self._smokes(smoke_results)
        gaps = self._gap_blockers(categories, smokes)
        readiness = self._readiness(categories, smokes)
        # B3 (M6.2L): defensive membership-count floor over the EMITTED gap list — if a standing-blocker id is
        # duplicated / shadowed / missing (a forged or tampered pack), fail-closed to NOT_READY instead of silently
        # passing. The canonical STANDING_GAP_BLOCKERS always passes, so normal output is unchanged (FAIL-007).
        if not standing_floor_ok(gaps):
            readiness = Readiness.NOT_READY
        return EvidencePack(
            categories=tuple(categories),
            smokes=tuple(smokes),
            gap_blockers=tuple(gaps),
            readiness=readiness,
            posture=_posture_snapshot(),
        )

    # --- category completeness (fail-closed; existence + uniqueness + category-binding, B2) ---------
    @staticmethod
    def _categories(
        evidence_refs: Mapping[EvidenceCategory, Mapping[str, Any]], known_refs: Any = None
    ) -> List[CategoryStatus]:
        # B2 (M6.2L): pack-wide uniqueness pass — count every provided ref across ALL categories; a ref used for
        # more than one (category,key) slot is a forgery vector (one valid ref copy-pasted everywhere) and
        # satisfies NONE of them. Blank/whitespace refs are ignored (never counted, never satisfying).
        counts: Dict[str, int] = {}
        for cat_refs in evidence_refs.values():
            if isinstance(cat_refs, Mapping):
                for v in cat_refs.values():
                    if isinstance(v, str) and v.strip():
                        counts[v.strip()] = counts.get(v.strip(), 0) + 1

        out: List[CategoryStatus] = []
        for category in EvidenceCategory:                       # all 10, in doc order
            required = CATEGORY_MANDATORY[category]
            provided = evidence_refs.get(category) or {}
            present = tuple(k for k in required if _ref_valid(provided.get(k), category, k, counts, known_refs))
            missing = tuple(k for k in required if not _ref_valid(provided.get(k), category, k, counts, known_refs))
            out.append(CategoryStatus(category=category, complete=not missing, present=present, missing=missing))
        return out

    # --- the 18 smokes (an un-provided smoke is un-run) --------------------------------------------
    @staticmethod
    def _smokes(smoke_results: Mapping[str, SmokeResult]) -> List[SmokeResult]:
        out: List[SmokeResult] = []
        for spec in SMOKE_REGISTRY:                             # all 18, canonical order
            result = smoke_results.get(spec.smoke_id) or SmokeResult(smoke_id=spec.smoke_id)
            # Waiver scope (fail-closed, FAIL-007): an owner waiver is honored ONLY for a PROPOSED smoke
            # (SMK-016/017/018). A waiver on a MANDATORY owner smoke (doc §21 P0) is INVALID and stripped, so the
            # smoke stays un-recorded (an actual run trace is required) — it cannot vanish from the gap list.
            if result.waived and spec.status is not SmokeStatus.PROPOSED:
                result = replace(result, waived=False)
            out.append(result)
        return out

    # --- honest gap/blocker list (standing always disclosed + derived) ----------------------------
    @staticmethod
    def _gap_blockers(categories: List[CategoryStatus], smokes: List[SmokeResult]) -> List[GapBlocker]:
        gaps: List[GapBlocker] = list(STANDING_GAP_BLOCKERS)    # ALWAYS disclosed (never dropped)
        for c in categories:
            if not c.complete:
                gaps.append(GapBlocker(
                    id=f"INCOMPLETE:{c.category.value}", kind=GapKind.INCOMPLETE_CATEGORY,
                    description=f"missing mandatory content: {', '.join(c.missing)}", owner="tester/pm",
                ))
        for s in smokes:
            if not s.recorded:
                gaps.append(GapBlocker(
                    id=f"UNRUN:{s.smoke_id}", kind=GapKind.UNRUN_SMOKE,
                    description="no recorded result (correlation_id + evidence_id) or owner waiver", owner="tester",
                ))
        return gaps

    # --- the ONE readiness rule (§4.4) -------------------------------------------------------------
    @staticmethod
    def _readiness(categories: List[CategoryStatus], smokes: List[SmokeResult]) -> Readiness:
        """NOT_READY iff any category INCOMPLETE OR any smoke un-recorded; else OWNER_REVIEW_REQUIRED. The standing
        blockers are disclosed in the gap list but do NOT gate this — production stays BLOCKED regardless, and never
        is there a Pass/Ready state here (owner-only, doc §23)."""
        if any(not c.complete for c in categories):
            return Readiness.NOT_READY
        if any(not s.recorded for s in smokes):
            return Readiness.NOT_READY
        return Readiness.OWNER_REVIEW_REQUIRED
