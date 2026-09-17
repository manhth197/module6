"""M6.2R recall-risk mapper (chief E2 §3/§5, M6-OD-017; extended M6.2U/M6-OD-020) — ops-core availability response
-> Scale-Gate risk_flags.

Consumes an ops-core /v1/availability/check response (a value object / dict — NEVER a live HTTP call; the live
client is the S1b seam / go-live) and produces the THREE ops-core-sourced risk_flags that feed the EXISTING Scale
Gate:  recall = recall_hold OR recall_case_open,  sale_lock,  quality_hold.  Those three recall booleans are derived
from the PRESENCE BOOLEANS only — NEVER from `decision` (M6 does not own the recall decision or M3 gating, RULE-018)
— so a present lock FAILs the Scale-Gate Risk row (RULE-017 hard veto) EVEN when decision == SELLABLE (a clean-lot
recall_case_open still locks).

M6.2U (M6-OD-020, E2 §3) adds ONE further, DISTINCT signal: `decision` is now read ONCE, ONLY for a sellability
no-scale veto — when it is not observed exactly "SELLABLE" the mapper sets a `not_sellable` flag that FAILs the
gate's separate `_risk` sellability check. This does NOT change how the recall booleans are derived (still presence
booleans only); `decision` feeds nothing but the sellability veto, and `block_reasons` is still never read.
`not_sellable` is NOT one of RECALL_RISK_KEYS / RISK_LOCKS. Fail-closed: a pull error / timeout / 429 / absent /
malformed / non-bool response is an INCOMPLETE read — the ops-core recall locks are left UNOBSERVED (never a False
false-clear, never a fabricated True) AND, being unverified, it is `not_sellable=True` (Risk FAIL). The strict-bool
check lives in `map_risk_flags`, the single choke BOTH the value-object and the dict paths flow through.

This module PRODUCES a risk_flags mapping; it TOUCHES NO gate code (no import of scale_gate / evaluate_conditions).
It is a PARTIAL risk contributor: its three keys are a strict SUBSET of conditions.RISK_LOCKS (the other three —
complaint_p0 / platform_spam_flag / crm_suppression — come from their own sources), plus the standalone
`not_sellable` veto key (M6-OD-020, NOT a RISK_LOCK). Safe uses: the FAIL direction (a present recall lock ⇒ the
merged map has an active lock ⇒ gate FAIL); the sellability direction (decision not observed SELLABLE ⇒
`not_sellable=True` ⇒ Risk FAIL); and the not-observed direction (an incomplete read ⇒ `not_sellable=True` ⇒ Risk
FAIL — M6.2U made this fail-closed to FAIL, replacing the prior empty-map/HOLD, so the mapper never false-clears).
The mapper's recall keys alone NEVER yield a complete 6-lock risk picture, so its output must
NOT be used to CLEAR the gate: the current gate's `_risk` reads ANY non-empty no-active map as PASS (it does not
require all 6 RISK_LOCKS present — a pre-existing gate limitation surfaced to the owner as a forward gate-hardening
finding, NOT fixed here per M6-OD-017's no-gate-change scope). A clearing decision must therefore assemble the FULL
6-lock picture and check `risk_picture_complete(flags)` before treating a map as clearing-eligible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from app.measurement.scale.conditions import RISK_LOCKS

# The three ops-core-sourced locks this mapper owns — a strict SUBSET of conditions.RISK_LOCKS.
RECALL_RISK_KEYS: Tuple[str, ...] = ("recall", "sale_lock", "quality_hold")

# Consistency guard (drift-catch, not ceremony): the mapper's keys MUST be locks the gate knows. If conditions.py
# ever renames a lock, this fails loudly at import rather than silently producing an unknown risk key.
_UNKNOWN_KEYS = tuple(k for k in RECALL_RISK_KEYS if k not in RISK_LOCKS)
if _UNKNOWN_KEYS:  # pragma: no cover - a wiring bug between the mapper and conditions.RISK_LOCKS
    raise RuntimeError(f"recall_risk_mapper keys not in conditions.RISK_LOCKS: {_UNKNOWN_KEYS}")


def _as_bool(value: Any) -> Optional[bool]:
    """Strict: a real `bool` passes through; anything else is None (unknown) — NEVER `bool()`-coerced, so a stray
    "false" string or a None can never coerce to a truthy clear/lock. Fail-closed at the read layer. `bool` is a
    subclass of `int`, so `isinstance(value, bool)` accepts only real booleans (0/1/int/np.bool_ are rejected)."""
    return value if isinstance(value, bool) else None


@dataclass(frozen=True)
class OpsCoreAvailabilityResponse:
    """A value-object view of an ops-core /v1/availability/check response (STAGED — built in tests / by the S1b
    seam, NEVER by a live HTTP call here). The mapper reads the presence booleans only; `decision` / `block_reasons`
    / `sku_ref` are RECORDED for provenance and NEVER read (M6 does not own the recall decision, RULE-018). The
    presence fields are declared `bool`; a direct construction with a non-bool is caught fail-closed in
    `map_risk_flags` (the single strict-bool choke), so this path is as fail-closed as `from_mapping`."""

    recall_hold: bool
    sale_lock: bool
    quality_hold: bool
    recall_case_open: bool = False          # additive (absent -> False); recall = recall_hold OR recall_case_open
    decision: Optional[str] = None          # RECORDED provenance only — the mapper NEVER reads it
    block_reasons: Tuple[str, ...] = ()     # RECORDED provenance only — the mapper NEVER reads it
    sku_ref: Optional[str] = None           # campaign/SKU ref (not PII); provenance only

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> Optional["OpsCoreAvailabilityResponse"]:
        """Build from a dict (the S1b seam hands the mapper either this value object or a dict). Missing presence
        keys become None (caught fail-closed by `map_risk_flags` -> INCOMPLETE); `recall_case_open` is additive
        (absent -> False). Returns None only when `mapping` is not a Mapping at all. The strict-bool validation is
        centralized in `map_risk_flags`, so a non-bool value here still fails closed there."""
        if not isinstance(mapping, Mapping):
            return None
        # N9 (M6.2T): `block_reasons` is provenance-only, but a NON-iterable (or a bare str/bytes) value would crash
        # `tuple(...)` on untrusted input — fail-closed-LOUD: a malformed block_reasons -> None (an INCOMPLETE read,
        # surfaced downstream as `malformed_response`), never a silent coerce and never an AttributeError/TypeError.
        raw_block_reasons = mapping.get("block_reasons")
        if raw_block_reasons is not None and (
            isinstance(raw_block_reasons, (str, bytes)) or not isinstance(raw_block_reasons, (list, tuple))
        ):
            return None
        decision = mapping.get("decision")
        sku_ref = mapping.get("sku_ref")
        return cls(
            recall_hold=mapping.get("recall_hold"),
            sale_lock=mapping.get("sale_lock"),
            quality_hold=mapping.get("quality_hold"),
            recall_case_open=mapping.get("recall_case_open", False),
            decision=decision if isinstance(decision, str) else None,
            block_reasons=tuple(raw_block_reasons or ()),
            sku_ref=sku_ref if isinstance(sku_ref, str) else None,
        )


@dataclass(frozen=True)
class RecallRiskRead:
    """The mapper's output. `risk_flags` carries the observed ops-core recall locks (a subset of RISK_LOCKS) when
    `complete`, PLUS a `not_sellable` sellability veto when the decision is not observed SELLABLE / the read is
    unverified (M6.2U, M6-OD-020). `sellable` records the decision-based sellability (None when not read);
    `unverified` marks a pull-error / incomplete read (E2 §1 'khong xac minh duoc' running-campaign signal)."""

    risk_flags: Mapping[str, bool] = field(default_factory=dict)
    complete: bool = False
    reason: str = ""
    sellable: Optional[bool] = None
    unverified: bool = False

    def is_active(self, lock: str) -> bool:
        return bool(self.risk_flags.get(lock))


def _incomplete(reason: str) -> RecallRiskRead:
    # M6.2U (M6-OD-020, E2 §3): a pull-error / incomplete / malformed read is UNVERIFIED -> not sellable -> Risk FAIL
    # (fail-closed, NOT the prior empty-{} HOLD). The recall booleans stay UNOBSERVED (absent); the `not_sellable`
    # veto carries the FAIL to the gate's distinct `_risk` check.
    return RecallRiskRead(risk_flags={"not_sellable": True}, complete=False, reason=reason,
                          sellable=False, unverified=True)


def map_risk_flags(response: Optional[OpsCoreAvailabilityResponse]) -> RecallRiskRead:
    """Map a (value-object) ops-core availability response -> the three ops-core risk_flags. The SINGLE strict-bool
    choke: every presence field (recall_hold / sale_lock / quality_hold / recall_case_open) must be a real `bool` —
    a None / missing / non-bool value is an INCOMPLETE read (empty, fail-closed), never `bool()`-coerced to a clear
    or a lock. So a directly-constructed value object with a non-bool field fails closed here exactly like the dict
    path. A None / absent response is INCOMPLETE. Reads PRESENCE BOOLEANS only — never decision/block_reasons.
    recall = recall_hold OR recall_case_open (additive); no other lock is fabricated."""
    if response is None:
        return _incomplete("pull_error:absent_response")
    recall_hold = _as_bool(response.recall_hold)
    sale_lock = _as_bool(response.sale_lock)
    quality_hold = _as_bool(response.quality_hold)
    recall_case_open = _as_bool(response.recall_case_open)
    if recall_hold is None or sale_lock is None or quality_hold is None or recall_case_open is None:
        return _incomplete("pull_error:malformed_response")     # any non-bool presence flag -> fail-closed
    # The 3 ops-core recall locks — derived from the PRESENCE BOOLEANS only (ops-core §4), NEVER from `decision`.
    flags: Dict[str, bool] = {
        "recall": bool(recall_hold or recall_case_open),
        "sale_lock": bool(sale_lock),
        "quality_hold": bool(quality_hold),
    }
    # M6.2U (M6-OD-020, E2 §3): a DISTINCT sellability no-scale veto. `decision` is read ONCE here, ONLY for this
    # veto (the recall booleans above are unaffected): when it is not observed EXACTLY "SELLABLE" (NOT_SELLABLE /
    # unknown / None / missing), set `not_sellable=True` -> the gate's distinct `_risk` sellability check FAILs. A
    # SELLABLE decision adds NO `not_sellable` key, so the exact-3-key recall output is preserved for a sellable read.
    # `not_sellable` is NOT one of RECALL_RISK_KEYS / RISK_LOCKS (it never merges into the 6-lock recall contribution).
    sellable = (response.decision == "SELLABLE")
    if not sellable:
        flags["not_sellable"] = True
    return RecallRiskRead(
        risk_flags=flags,
        complete=True,
        reason="mapped",
        sellable=sellable,
    )


def map_pull_outcome(response: Any = None, *, error: Optional[str] = None) -> RecallRiskRead:
    """Model the S1b seam's pull outcome WITHOUT any HTTP: a transport/protocol `error` (e.g. "TIMEOUT" / "HTTP_429"
    / "CONNECTION_ERROR") or an absent response -> INCOMPLETE (empty, fail-closed); a `dict` response is parsed via
    `from_mapping` then strictly validated by `map_risk_flags` (malformed/non-bool -> INCOMPLETE); an
    `OpsCoreAvailabilityResponse` -> `map_risk_flags` (same strict validation). NEVER a False false-clear."""
    if error:
        return _incomplete(f"pull_error:{error}")
    if response is None:
        return _incomplete("pull_error:absent_response")
    if isinstance(response, OpsCoreAvailabilityResponse):
        return map_risk_flags(response)
    if isinstance(response, Mapping):
        parsed = OpsCoreAvailabilityResponse.from_mapping(response)
        if parsed is None:
            return _incomplete("pull_error:malformed_response")
        return map_risk_flags(parsed)
    return _incomplete("pull_error:unrecognized_response")


def risk_picture_complete(flags: Mapping[str, bool]) -> bool:
    """True iff `flags` observes ALL 6 conditions.RISK_LOCKS — the caller-side completeness predicate that makes a
    CLEAR decision fail-closed WITHOUT a gate change. A clearing decision is safe only when
    `risk_picture_complete(flags)` AND no lock is active; the mapper's 3-of-6 output is NEVER complete on its own, so
    a caller must merge all lock sources and check this before treating a map as clearing-eligible. (This mirrors the
    intent of scale_gate._assert_risk_clear_at_approval's all-6 completeness test, which the gate's propose-time
    `_risk` does not enforce — the forward gate-hardening finding.)"""
    return all(lock in flags for lock in RISK_LOCKS)


class RecallRiskContributionError(ValueError):
    """N3 (M6.2T): raised when `base_flags` carries a mapper-owned RECALL_RISK_KEY — a silent overwrite would hide a
    caller's (possibly active) recall observation. Fail-closed: reject instead of overwrite."""


def recall_risk_contribution(
    read: RecallRiskRead, base_flags: Optional[Mapping[str, bool]] = None
) -> Dict[str, bool]:
    """MERGE the mapper's observed recall locks ONTO a caller-supplied `base_flags` (the OTHER lock sources) and
    return a map that is FAIL-CLOSED BY CONSTRUCTION — always safe to feed to the existing Scale Gate as
    `ScaleContext.risk_flags`, in every case:

      * ANY active lock (recall/sale_lock/quality_hold from this read, or any lock in `base_flags`) -> the map is
        returned WITH the active lock, so the gate FAILs (RULE-017 hard veto) — the FAIL direction;
      * a COMPLETE 6-lock picture with no active lock (the caller merged all lock sources) -> the full map is
        returned (legitimately clearing-eligible);
      * an INCOMPLETE picture with no active lock (e.g. this mapper's clean 3-of-6 output alone, or a pull-error
        empty read) -> `{}` is returned, so the gate reads HOLD (fail-closed) and NEVER false-clears.

    So the mapper's clean output is structurally NEVER a standalone clearing map: a bare 3-of-6 clean merge collapses
    to `{}` (HOLD) rather than a partial map the gate's `_risk` would wrongly PASS. Only a caller that assembles the
    full 6-lock picture (all sources) gets a clearing-eligible map. `risk_picture_complete()` is the same predicate,
    exposed for a caller that assembles risk_flags itself. N3 (M6.2T): a `base_flags` carrying a mapper-owned recall
    key is REJECTED (no silent overwrite)."""
    # N3 (M6.2T): the base map must carry only the OTHER lock sources; a base already carrying a recall key
    # (recall/sale_lock/quality_hold) would be SILENTLY OVERWRITTEN by this read -> reject fail-closed.
    if base_flags is not None:
        clash = [k for k in RECALL_RISK_KEYS if k in base_flags]
        if clash:
            raise RecallRiskContributionError(
                f"base_flags must not carry the mapper-owned recall key(s) {clash} (no silent overwrite)"
            )
    merged: Dict[str, bool] = dict(base_flags or {})
    if read.complete:
        for k in RECALL_RISK_KEYS:
            merged[k] = bool(read.risk_flags.get(k))
    if any(merged.get(lock) for lock in RISK_LOCKS):
        return merged                       # an active lock must reach the gate (FAIL direction)
    if risk_picture_complete(merged):
        return merged                       # complete + no active: a legitimate clearing-eligible picture
    return {}                               # incomplete + no active: fail-closed (a bare partial NEVER clears)
