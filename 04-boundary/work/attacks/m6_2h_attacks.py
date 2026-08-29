"""M6-P1705 BOUNDARY_ADVERSARY executed attack harness for slice M6.2H (Strategy Libraries + Learning Engine).

READ-ONLY adversary: imports the FROZEN staged M6.2H app and drives the REAL code paths. Never modifies app code,
never writes 04-artifacts/state, never publishes anything (LEARNING_AUTOPUBLISH_ENABLED / external_send stay OFF).

In-scope fail gate ATTACKED: M6-FAIL-006 (auto scale/publish -- here: auto-publishing a learning candidate /
optimization without owner approval). In-scope rules: RULE-011 (learning guarded: seed only from canonical
sources; Learn only after seed + only DQ-passed verified signals; candidates -> review queue; publish only via
owner approval or an owner-ratified safe range), RULE-013 (never override Core policy), RULE-018 (SoT precedence).

Every claimed breach is EXECUTED here before it is recorded. Outcome classes:
  DEFENDED / OPEN_NONGATE / NOTE / BREACH (BREACH = a candidate auto-published / published without approval).

Launcher: py -3.12 -B (byte-clean). Owner/PII probes assembled at runtime, never echoed raw.
"""
from __future__ import annotations

import inspect
import math
import sys
import tokenize
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
PACK_ROOT = HERE.parents[3]
IMPL = PACK_ROOT / "04-artifacts" / "impl" / "M6.2H"
if not IMPL.exists():
    IMPL = Path(r"D:\M6\Module6-workspace\04-artifacts\impl\M6.2H")
sys.path.insert(0, str(IMPL))

from app import config
from app.measurement.audit import AuditLog
from app.measurement.models.measurement_event import DataQualityStatus
from app.measurement.learning.candidate import (
    AdsLearningCandidate,
    LearningCandidateKind,
    OwnerReviewDecision,
    ReviewState,
    SafeRangeStatus,
    TargetDim,
)
from app.measurement.learning.libraries import (
    CANONICAL_SEED_SOURCES,
    LibrarySeedViolation,
    StrategyLibraryKind,
    StrategyLibraryStore,
    is_canonical_seed,
)
from app.measurement.learning.mapping import StrategyMapping, StrategyMappingViolation
from app.measurement.learning.review_queue import ReviewQueue, ReviewQueueViolation
from app.measurement.learning.learning_engine import (
    LearningEngine,
    LearningPreconditionError,
    ReviewDecisionError,
    VerifiedSignal,
)
from app.api.learning_candidates import (
    LearningDeps,
    handle_learning_candidate_create,
    handle_learning_review_decision,
)

_PASS, _HOLD, _FAIL = DataQualityStatus.PASS, DataQualityStatus.HOLD, DataQualityStatus.FAIL
FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)

RESULTS = []
BREACHES = []


def record(attack_id, gate, klass, detail):
    assert klass in ("DEFENDED", "OPEN_NONGATE", "NOTE", "BREACH"), klass
    RESULTS.append((attack_id, gate, klass, detail))
    if klass == "BREACH":
        BREACHES.append((attack_id, gate, detail))
    print(f"[{klass:12}] {attack_id:30} {gate:9} | {detail}")


def new_engine():
    store = StrategyLibraryStore()
    queue = ReviewQueue()
    return LearningEngine(store, queue, AuditLog()), store, queue


def seed_all(store):
    for kind in StrategyLibraryKind:
        store.seed(kind, CANONICAL_SEED_SOURCES[kind][0], entry_id=f"seed_{kind.name.lower()}")
    return store


def candidate(cid="lc_1", *, target_dim="persona", kind="OPTIMIZATION", score=0.8, sku_ref="SKU_HERO_1", **over):
    base = dict(candidate_id=cid, kind=LearningCandidateKind(kind), target_dim=TargetDim(target_dim),
                score=score, sku_ref=sku_ref)
    base.update(over)
    return AdsLearningCandidate(**base)


def owner(state="APPROVED", **over):
    base = dict(actor="owner_ops", reason="reviewed against canon", audit_ref="aud_1",
                evidence_ref="ev_1", new_state=ReviewState(state))
    base.update(over)
    return OwnerReviewDecision(**base)


# ================================================================================================
# GROUP A - FAIL-006 / RULE-011 : no auto-publish; publish authorized only APPROVED+WITHIN
# ================================================================================================
_PUBLISH_ATTRS = ("publish", "auto_publish", "autopublish", "go_live", "golive", "launch", "execute",
                  "send", "dispatch", "apply", "activate", "run_live", "deploy", "rollout")


def group_a():
    eng, store, queue = new_engine()
    deps = LearningDeps(engine=eng, audit=AuditLog())
    cand = candidate()

    # A1 no publish/auto-publish attribute on engine / queue / candidate / deps
    surfaces = {"LearningEngine": eng, "ReviewQueue": queue, "AdsLearningCandidate": cand, "LearningDeps": deps}
    present = {name: [a for a in _PUBLISH_ATTRS if hasattr(obj, a)] for name, obj in surfaces.items()}
    any_pub = any(present.values())
    record("A1-no-publish-attr", "FAIL-006",
           "BREACH" if any_pub else "DEFENDED",
           f"publish-verb attrs on engine/queue/candidate/deps: {present if any_pub else 'NONE'}; "
           f"guarded_publish_blocked={eng.guarded_publish_blocked()}")

    # A2 review() forces safe_range UNKNOWN (M6-OD-006) -> HOLD, not publishable
    q = eng.review(candidate("lc_a2"))
    record("A2-review-forces-hold", "FAIL-006",
           "DEFENDED" if q.safe_range_status is SafeRangeStatus.UNKNOWN and q.review_state is ReviewState.HOLD
           and not q.is_publish_authorized else "BREACH",
           f"review() -> safe_range={q.safe_range_status.value}, state={q.review_state.value}, "
           f"is_publish_authorized={q.is_publish_authorized}")

    # A3 an untrusted WITHIN claim is forced UNKNOWN and HELD (SMK-011 neg)
    q = eng.review(candidate("lc_a3", safe_range_status=SafeRangeStatus.WITHIN))
    record("A3-within-claim-forced-unknown", "FAIL-006",
           "DEFENDED" if q.safe_range_status is SafeRangeStatus.UNKNOWN and q.review_state is ReviewState.HOLD else "BREACH",
           f"claimed WITHIN -> forced safe_range={q.safe_range_status.value}, state={q.review_state.value}")

    # A4 even a recorded owner APPROVE -> is_publish_authorized False (safe range stays UNKNOWN)
    eng.review(candidate("lc_a4"))
    appr = eng.record_review_decision("lc_a4", owner("APPROVED"))
    record("A4-approve-not-publishable", "FAIL-006",
           "DEFENDED" if appr.review_state is ReviewState.APPROVED and appr.safe_range_status is SafeRangeStatus.UNKNOWN
           and not appr.is_publish_authorized else "BREACH",
           f"APPROVE -> state={appr.review_state.value}, safe_range={appr.safe_range_status.value}, "
           f"is_publish_authorized={appr.is_publish_authorized}")

    # A5 (config-flip) flipping BOTH learning flags + a WITHIN candidate CAN make is_publish_authorized True, BUT
    #    there is NO publish executor -> nothing publishes. The flag is immutable (M6-OD-006/007 OPEN, in-process
    #    code exec needed). Save/restore. This is the honest FAIL-006 nuance: authorization is flag-gated, but the
    #    real defense is the STRUCTURAL absence of any publish method.
    saved = (config.LEARNING_SAFE_RANGE_RATIFIED, config.LEARNING_AUTOPUBLISH_ENABLED)
    try:
        config.LEARNING_SAFE_RANGE_RATIFIED = True
        config.LEARNING_AUTOPUBLISH_ENABLED = True
        eng2, s2, q2 = new_engine()
        rq = eng2.review(candidate("lc_a5", safe_range_status=SafeRangeStatus.WITHIN))
        ap = eng2.record_review_decision("lc_a5", owner("APPROVED"))
        flipped_auth = ap.is_publish_authorized
        blocked = eng2.guarded_publish_blocked()
        has_pub = any(hasattr(eng2, a) for a in _PUBLISH_ATTRS)
    finally:
        config.LEARNING_SAFE_RANGE_RATIFIED, config.LEARNING_AUTOPUBLISH_ENABLED = saved
    record("A5-flip-flags-no-executor", "FAIL-006",
           "BREACH" if has_pub else "DEFENDED",
           f"flip BOTH flags + WITHIN candidate -> is_publish_authorized={flipped_auth}, guarded_publish_blocked="
           f"{blocked}; BUT publish method exists={has_pub} -> even authorized, NOTHING publishes (no executor); "
           f"flags immutable (M6-OD-006/007 OPEN) + restored")

    # A6 guarded_publish_blocked True while flags False; needs BOTH flags to unblock
    record("A6-guarded-publish-blocked", "FAIL-006",
           "DEFENDED" if eng.guarded_publish_blocked() else "BREACH",
           f"guarded_publish_blocked={eng.guarded_publish_blocked()} (LEARNING_AUTOPUBLISH_ENABLED="
           f"{config.LEARNING_AUTOPUBLISH_ENABLED} AND LEARNING_SAFE_RANGE_RATIFIED={config.LEARNING_SAFE_RANGE_RATIFIED})")

    # A7 frozen candidate: object.__setattr__ can forge APPROVED+WITHIN but needs in-process code exec + still no executor
    c = candidate("lc_a7")
    try:
        c.review_state = ReviewState.APPROVED   # frozen
        record("A7-frozen-candidate", "FAIL-006", "BREACH", "mutated a frozen candidate")
    except FrozenInstanceError:
        object.__setattr__(c, "review_state", ReviewState.APPROVED)
        object.__setattr__(c, "safe_range_status", SafeRangeStatus.WITHIN)
        record("A7-frozen-candidate", "FAIL-006", "NOTE",
               f"frozen blocks assignment; object.__setattr__ forges is_publish_authorized={c.is_publish_authorized} "
               f"but needs in-process code exec AND publishes nothing (no executor) -> defense-in-depth limit")


# ================================================================================================
# GROUP B - RULE-011 : Learn precondition (seed first) + only DQ-passed verified signals
# ================================================================================================
def group_b():
    # B1 learn() before any seed -> LearningPreconditionError
    eng, store, queue = new_engine()
    try:
        eng.learn([VerifiedSignal(TargetDim.PERSONA, 1.0, _PASS, True)])
        record("B1-learn-needs-seed", "RULE-011", "BREACH", "learn ran with no seed")
    except LearningPreconditionError as e:
        record("B1-learn-needs-seed", "RULE-011", "DEFENDED", f"learn refused without a canonical seed ({str(e)[:45]})")

    # B2 learn() consumes ONLY usable signals (DQ PASS + verified); everything else excluded
    eng, store, queue = new_engine()
    seed_all(store)
    signals = [
        VerifiedSignal(TargetDim.PERSONA, 10.0, _PASS, True),     # usable
        VerifiedSignal(TargetDim.PERSONA, 999.0, _HOLD, True),    # excluded (DQ HOLD)
        VerifiedSignal(TargetDim.PERSONA, 999.0, _FAIL, True),    # excluded (DQ FAIL)
        VerifiedSignal(TargetDim.PERSONA, 999.0, _PASS, False),   # excluded (unverified)
        VerifiedSignal(TargetDim.KEYWORD, 4.0, _PASS, True),      # usable
    ]
    scores = eng.learn(signals)
    ok = scores.get(TargetDim.PERSONA) == 10.0 and scores.get(TargetDim.KEYWORD) == 4.0
    record("B2-only-usable-signals", "RULE-011",
           "DEFENDED" if ok else "BREACH",
           f"mixed signals -> scores={ {d.value: v for d, v in scores.items()} } (persona=10 keyword=4; HOLD/FAIL/"
           f"unverified 999 excluded)")

    # B3 is_usable edge cases: PASS+unverified and HOLD+verified are both not usable
    su = [VerifiedSignal(TargetDim.HOOK, 1.0, _PASS, False).is_usable,
          VerifiedSignal(TargetDim.HOOK, 1.0, _HOLD, True).is_usable,
          VerifiedSignal(TargetDim.HOOK, 1.0, _PASS, True).is_usable]
    record("B3-is-usable-logic", "RULE-011",
           "DEFENDED" if su == [False, False, True] else "BREACH",
           f"is_usable [PASS+unverified, HOLD+verified, PASS+verified] = {su}")

    # B4 seed from a NON-canonical source -> LibrarySeedViolation (no fabricated origin)
    eng, store, queue = new_engine()
    bad = []
    for kind in StrategyLibraryKind:
        try:
            store.seed(kind, "fabricated_origin_strategy", entry_id="x")
            bad.append(kind.value)
        except LibrarySeedViolation:
            pass
    record("B4-non-canonical-seed-rejected", "RULE-011",
           "DEFENDED" if not bad else "BREACH",
           f"all 6 libraries reject a fabricated seed_source" if not bad else f"accepted fabricated seed: {bad}")

    # B5 content fill while M6-OD-007 OPEN -> rejected (framework-only)
    eng, store, queue = new_engine()
    try:
        store.seed(StrategyLibraryKind.PERSONA, CANONICAL_SEED_SOURCES[StrategyLibraryKind.PERSONA][0],
                   entry_id="p", content="machine-fabricated persona copy")
        record("B5-content-fill-blocked", "RULE-011", "BREACH", "content accepted while M6-OD-007 OPEN")
    except LibrarySeedViolation as e:
        record("B5-content-fill-blocked", "RULE-011", "DEFENDED", f"content rejected (framework-only, M6-OD-007) ({str(e)[:40]})")

    # B6 case/substring variants of a canonical token are NOT canonical (exact-match only)
    k = StrategyLibraryKind.PERSONA
    canon = CANONICAL_SEED_SOURCES[k][0]
    variants = [canon.upper(), " " + canon, canon + "_evil", canon[:-1], ""]
    accepted = [v for v in variants if is_canonical_seed(k, v)]
    record("B6-seed-exact-match", "RULE-011",
           "DEFENDED" if not accepted else "NOTE",
           f"case/whitespace/substring variants of a canonical token accepted: {accepted or 'NONE'} (exact-match only)")


# ================================================================================================
# GROUP C - RULE-013 / RULE-018 : no Core override; SKU anchor; skeleton run is inert
# ================================================================================================
def group_c():
    # C1 mapping requires a sellable SKU anchor (LEX-005)
    try:
        StrategyMapping(sku_ref="")
        record("C1-sku-anchor-required", "RULE-013", "BREACH", "a mapping with no SKU anchor was accepted")
    except StrategyMappingViolation as e:
        record("C1-sku-anchor-required", "RULE-013", "DEFENDED", f"unanchored mapping rejected (LEX-005) ({str(e)[:40]})")

    # C2 run() is a skeleton: records a mapping, nothing runs (no campaign/scale/publish side effect)
    eng, store, queue = new_engine()
    m = eng.run(StrategyMapping(sku_ref="SKU_HERO_1", persona="p1"))
    record("C2-run-is-skeleton", "RULE-013",
           "DEFENDED" if eng.active_mappings == (m,) and len(queue) == 0 else "BREACH",
           f"run() recorded {len(eng.active_mappings)} mapping; queue={len(queue)}; nothing ran/published")

    # C3 no Core-owned write surface on mapping / libraries (no pricing/program/policy/crm/diamond/golden_hour method)
    core_verbs = ("set_price", "write_price", "set_program", "member_right", "crm", "diamond", "golden_hour",
                  "policy", "order_state", "commission", "budget")
    surfaces = {"StrategyMapping": StrategyMapping(sku_ref="SKU_HERO_1"), "StrategyLibraryStore": store}
    hits = {n: [v for v in core_verbs if hasattr(o, v)] for n, o in surfaces.items()}
    any_hit = any(hits.values())
    record("C3-no-core-write", "RULE-013",
           "BREACH" if any_hit else "DEFENDED",
           f"Core-owned write methods on mapping/library store: {hits if any_hit else 'NONE'} (RULE-013/018)")


# ================================================================================================
# GROUP D - API / RULE-H03 : untrusted body cannot publish or synthesize a decision
# ================================================================================================
def group_d():
    eng, store, queue = new_engine()
    deps = LearningDeps(engine=eng, audit=AuditLog())

    # D1 create body claiming APPROVED/WITHIN/publishable -> candidate built server-side, HELD, safe_range UNKNOWN
    evil = {"target_dim": "persona", "sku_ref": "SKU_HERO_1", "score": 0.9, "kind": "OPTIMIZATION",
            "review_state": "APPROVED", "safe_range_status": "WITHIN", "is_publish_authorized": True}
    resp = handle_learning_candidate_create(evil, deps)
    c = queue.get(resp.candidate_id)
    record("D1-body-cannot-fake-state", "FAIL-006",
           "DEFENDED" if resp.review_state == "HOLD" and resp.safe_range_status == "UNKNOWN"
           and not c.is_publish_authorized else "BREACH",
           f"malicious create body -> state={resp.review_state}, safe_range={resp.safe_range_status}, "
           f"is_publish_authorized={c.is_publish_authorized}; body claims ignored")

    # D2 review decision requires all owner fields; partial / bad kind rejected; APPROVE still not publishable
    partial = handle_learning_review_decision({"candidate_id": resp.candidate_id, "decision": "APPROVE", "actor": "o"}, deps)
    badkind = handle_learning_review_decision({"candidate_id": resp.candidate_id, "decision": "PUBLISH", "actor": "o",
                                               "reason": "r", "audit_ref": "a", "evidence_ref": "e"}, deps)
    good = handle_learning_review_decision({"candidate_id": resp.candidate_id, "decision": "APPROVE", "actor": "o",
                                            "reason": "r", "audit_ref": "a", "evidence_ref": "e"}, deps)
    after = queue.get(resp.candidate_id)
    record("D2-owner-fields-required", "RULE-011",
           "DEFENDED" if partial.error_code == "OWNER_DECISION_INCOMPLETE" and badkind.error_code == "SCHEMA_INVALID"
           and good.review_state == "APPROVED" and not after.is_publish_authorized else "BREACH",
           f"partial -> {partial.error_code}; bad kind -> {badkind.error_code}; APPROVE -> {good.review_state} but "
           f"is_publish_authorized={after.is_publish_authorized} (safe range UNKNOWN)")

    # D3 cannot re-decide a terminal candidate
    redo = handle_learning_review_decision({"candidate_id": resp.candidate_id, "decision": "APPROVE", "actor": "o",
                                            "reason": "r", "audit_ref": "a", "evidence_ref": "e"}, deps)
    record("D3-no-redecide", "RULE-011",
           "DEFENDED" if redo.error_code == "REVIEW_DECISION_REFUSED" else "BREACH",
           f"re-decide an APPROVED candidate -> {redo.status}/{redo.error_code}")

    # D4 score type guard + sku_ref required + target_dim validated
    s_bool = handle_learning_candidate_create({"target_dim": "persona", "sku_ref": "S", "score": True}, deps)
    no_sku = handle_learning_candidate_create({"target_dim": "persona", "score": 0.5}, deps)
    bad_dim = handle_learning_candidate_create({"target_dim": "pricing", "sku_ref": "S", "score": 0.5}, deps)
    record("D4-input-guards", "FAIL-006",
           "DEFENDED" if s_bool.error_code == "SCHEMA_INVALID" and no_sku.error_code == "SCHEMA_INVALID"
           and bad_dim.error_code == "SCHEMA_INVALID" else "NOTE",
           f"score bool -> {s_bool.error_code}; no sku_ref -> {no_sku.error_code}; bad target_dim -> {bad_dim.error_code}")

    # D5 audit machine-safe: untrusted owner reason/audit_ref absent from audit detail; actor masked
    eng2, s2, q2 = new_engine()
    audit2 = AuditLog()
    eng2._audit = audit2
    eng2.review(candidate("lc_d5"))
    pii_reason = "call" + "".join(str(d) for d in (9, 8, 7, 6, 5, 4, 3, 2, 1, 0)) + "urgent"
    eng2.record_review_decision("lc_d5", owner("APPROVED", actor="owner_secretid", reason=pii_reason, audit_ref="aud_secret"))
    details = " ".join((r.detail or "") for r in audit2.records)
    subjects = " ".join((r.subject_masked or "") for r in audit2.records)
    leaked = pii_reason in details or "aud_secret" in details or "owner_secretid" in subjects
    record("D5-audit-machine-safe", "RULE-014",
           "DEFENDED" if not leaked else "BREACH",
           f"owner free-text reason/audit_ref absent from audit detail; actor masked; leaked={leaked}")


# ================================================================================================
# GROUP E - belt sweeps: no publish/action identifiers / no posture-flag writes; PII masking
# ================================================================================================
def group_e():
    action_verbs = ("publish", "auto_publish", "autopublish", "go_live", "golive", "launch", "deploy",
                    "rollout", "execute_publish", "raise_budget", "enable_campaign", "order_state",
                    "crm_send", "set_price", "commission")
    posture_flags = ("LEARNING_AUTOPUBLISH_ENABLED", "LEARNING_SAFE_RANGE_RATIFIED", "LEARNING_CONTENT_FILL_ENABLED",
                     "GLOBAL_GATEWAY_STATE", "PRODUCTION_FLAG", "EXTERNAL_SEND")
    targets = [
        IMPL / "app" / "measurement" / "learning" / "learning_engine.py",
        IMPL / "app" / "measurement" / "learning" / "candidate.py",
        IMPL / "app" / "measurement" / "learning" / "libraries.py",
        IMPL / "app" / "measurement" / "learning" / "mapping.py",
        IMPL / "app" / "measurement" / "learning" / "review_queue.py",
        IMPL / "app" / "api" / "learning_candidates.py",
    ]
    action_hits, flag_writes = [], []
    for p in targets:
        with tokenize.open(str(p)) as fh:
            toks = list(tokenize.generate_tokens(fh.readline))
        for i, tok in enumerate(toks):
            if tok.type == tokenize.NAME and tok.string.lower() in action_verbs:
                action_hits.append(f"{p.name}:{tok.start[0]}:{tok.string}")
            if tok.type == tokenize.NAME and tok.string in posture_flags:
                nxt = toks[i + 1] if i + 1 < len(toks) else None
                if nxt is not None and nxt.type == tokenize.OP and nxt.string == "=":
                    flag_writes.append(f"{p.name}:{tok.start[0]}:{tok.string}=")
    record("E1-no-action-no-flagwrite", "RULE-011",
           "DEFENDED" if not action_hits and not flag_writes else "NOTE",
           f"token sweep of 6 learning modules: publish/action defs={action_hits or 'NONE'}; posture-flag writes="
           f"{flag_writes or 'NONE'}")

    # E2 owner actor masked on export; sku_ref is a SKU ref (not PII); no raw actor in candidate.to_public
    eng, store, queue = new_engine()
    eng.review(candidate("lc_e2"))
    eng.record_review_decision("lc_e2", owner("APPROVED", actor="owner_distinctid"))
    pub = repr(queue.get("lc_e2").to_public())
    masked = "own***id" in pub
    record("E2-export-masking", "RULE-014",
           "DEFENDED" if "owner_distinctid" not in pub and masked else "NOTE",
           f"candidate.to_public: raw actor absent={'owner_distinctid' not in pub}, masked-present={masked} "
           f"(sku_ref is a SKU ref, not PII); belt -> M6-P1706")


# ================================================================================================
# GROUP W - workflow-harvested vectors (6-agent adversarial ideation + completeness critic; 49 vectors).
#           Every claimed breach EXECUTED here before recording; reachability checked against the real wiring.
# ================================================================================================
def group_w():
    # W1 (CC-01) ReviewQueue.update() is a SECOND, unguarded write path: it only checks the id EXISTS -- no
    #    transition/safe-range validation -- so a forged APPROVED+WITHIN record with the same id can be swapped in,
    #    defeating both review()'s UNKNOWN-forcing and record_review_decision's terminal guard at once. In-process
    #    only (_queue is a private handle; the API never exposes update()) and inert (no consumer publishes).
    eng, store, queue = new_engine()
    honest = eng.review(candidate("lc_swap"))
    forged = candidate("lc_swap", review_state=ReviewState.APPROVED, safe_range_status=SafeRangeStatus.WITHIN)
    eng._queue.update(forged)
    got = queue.get("lc_swap")
    record("W1-queue-update-swap", "FAIL-006",
           "OPEN_NONGATE" if honest.review_state is ReviewState.HOLD and got.is_publish_authorized else "NOTE",
           f"ReviewQueue.update() swaps a forged APPROVED+WITHIN record (same id) with NO transition/safe-range "
           f"validation -> is_publish_authorized={got.is_publish_authorized} (no OwnerReviewDecision, flag never "
           f"ratified); in-process only (_queue private, API never exposes update), no consumer publishes -> route "
           f"CODER (update() must reject an illegal transition / re-force UNKNOWN) + M6-OD-011")

    # W2 (CC-02/CC-03/PEP-05) the decisive FAIL-006 negative: is_publish_authorized has ZERO non-test consumers,
    #    the learning package is NOT imported by the outbox/scale/dispatcher layers, and even a forged-authorized
    #    record driven through EVERY entrypoint publishes nothing (no SENT/PUBLISH).
    app_root = IMPL / "app"
    consumers = []
    for p in app_root.rglob("*.py"):
        if p.name == "candidate.py":
            continue  # the property definition
        with tokenize.open(str(p)) as fh:   # NAME tokens only -> excludes docstrings/comments
            for tok in tokenize.generate_tokens(fh.readline):
                if tok.type == tokenize.NAME and tok.string == "is_publish_authorized":
                    consumers.append(f"{p.name}:{tok.start[0]}")
                    break
    cross_wire = []
    for sub in ("outbox", "scale"):
        d = app_root / "measurement" / sub
        if d.exists():
            for p in d.rglob("*.py"):
                if "app.measurement.learning" in p.read_text(encoding="utf-8"):
                    cross_wire.append(f"{sub}/{p.name}")
    # drive every entrypoint against a forged-authorized record; assert no publish audit
    eng, store, queue = new_engine()
    audit = eng._audit
    queue.enqueue(candidate("lc_auth", review_state=ReviewState.APPROVED, safe_range_status=SafeRangeStatus.WITHIN))
    deps = LearningDeps(engine=eng, audit=audit)
    eng.guarded_publish_blocked()
    _ = eng.active_mappings
    handle_learning_candidate_create({"target_dim": "persona", "sku_ref": "SKU_HERO_1", "score": 0.5}, deps)
    handle_learning_review_decision({"candidate_id": "lc_auth", "decision": "APPROVE", "actor": "x", "reason": "r",
                                     "audit_ref": "a", "evidence_ref": "e"}, deps)
    published = [r for r in audit.records if any(t in (r.action + r.reason) for t in ("PUBLISH", "SENT", "DELIVER", "SEND"))]
    record("W2-no-consumer-no-crosswire", "FAIL-006",
           "DEFENDED" if not consumers and not cross_wire and not published else "BREACH",
           f"is_publish_authorized non-test consumers in app/={consumers or 'NONE'}; learning imported by "
           f"outbox/scale={cross_wire or 'NONE'}; forged-authorized record driven through all entrypoints -> "
           f"publish/sent audit lines={len(published)} -> the FAIL-006 boundary is structural absence-of-consumer")

    # W3 (CC-04) score validation gap on the LIVE API: NaN/inf pass isinstance(float); a huge int (10**400) makes
    #    float(score) raise an UNHANDLED OverflowError -> the untrusted body escapes the handler's REJECTED_INPUT
    #    fail-closed contract with a crash. score is not read by is_publish_authorized -> not FAIL-006.
    eng, store, queue = new_engine()
    deps = LearningDeps(engine=eng, audit=AuditLog())
    r_nan = handle_learning_candidate_create({"target_dim": "persona", "sku_ref": "S", "score": float("nan")}, deps)
    nan_stored = math.isnan(queue.get(r_nan.candidate_id).score) if r_nan.candidate_id else False
    overflow = None
    try:
        handle_learning_candidate_create({"target_dim": "persona", "sku_ref": "S", "score": 10 ** 400}, deps)
        overflow = "no-crash"
    except OverflowError:
        overflow = "UNHANDLED OverflowError"
    except Exception as e:  # any other unhandled type is also a fail-open crash
        overflow = f"unhandled {type(e).__name__}"
    record("W3-score-unvalidated-crash", "FAIL-006",
           "OPEN_NONGATE" if nan_stored and overflow != "no-crash" else "NOTE",
           f"NaN score CREATED (stored non-finite={nan_stored}); score=10**400 -> {overflow} on the live create "
           f"handler (escapes the REJECTED_INPUT fail-closed contract); score not gate-read (not FAIL-006) -> route "
           f"CODER/M6-P1706 (reject non-finite + bound magnitude + wrap float())")

    # W4 (CC-05) review() re-derives review_state from safe_range (discards a forged APPROVED) -- GOOD -- but does
    #    NOT scrub the incoming `decision`, so a forged OwnerReviewDecision rides onto a CANDIDATE record (inert).
    saved = config.LEARNING_SAFE_RANGE_RATIFIED
    try:
        config.LEARNING_SAFE_RANGE_RATIFIED = True
        eng, store, queue = new_engine()
        forged = candidate("lc_r", review_state=ReviewState.APPROVED, safe_range_status=SafeRangeStatus.WITHIN,
                           decision=owner("APPROVED"))
        out = eng.review(forged)
        state_rederived = out.review_state is ReviewState.CANDIDATE and not out.is_publish_authorized
        decision_survived = out.decision is not None
    finally:
        config.LEARNING_SAFE_RANGE_RATIFIED = saved
    record("W4-review-rederives-state", "FAIL-006",
           "OPEN_NONGATE" if state_rederived and decision_survived else ("DEFENDED" if state_rederived else "NOTE"),
           f"review() re-derives review_state=CANDIDATE (forged APPROVED discarded, is_publish_authorized False) -- "
           f"the review_state axis holds; BUT the forged `decision` survives replace() (rides onto a CANDIDATE "
           f"record, inert) -> route CODER (scrub decision on review); flag restored")

    # W5 (CC-07) StrategyMapping anchors on truthiness only: a monetary VALUE / Core object / policy token passes as
    #    the 'sellable SKU'; verified_revenue_ref accepts a literal value despite 'never a value'. BUT run() writes
    #    NO Core value (only appends in-memory) -> RULE-013 not violated in effect; input-validation gap only.
    eng, store, queue = new_engine()
    m_val = StrategyMapping(sku_ref=12000000)                         # a revenue VALUE as the anchor
    m_obj = StrategyMapping(sku_ref={"program": "Diamond"})           # a Core program object as the anchor
    m_rev = StrategyMapping(sku_ref="SKU_1", verified_revenue_ref="12000000 VND")  # a value in a 'ref' field
    eng.run(m_val); eng.run(m_obj); eng.run(m_rev)
    falsy_rejected = 0
    for bad in (0, False, "", [], None):
        try:
            StrategyMapping(sku_ref=bad)
        except StrategyMappingViolation:
            falsy_rejected += 1
    record("W5-mapping-anchor-validation", "FAIL-006",
           "OPEN_NONGATE" if eng.active_mappings[0].sku_ref == 12000000 and falsy_rejected == 5 else "NOTE",
           f"StrategyMapping anchor accepts a value/Core-object (truthiness only; falsy {falsy_rejected}/5 rejected); "
           f"verified_revenue_ref accepts a literal value; BUT run() appends in-memory only, writes NO Core value "
           f"(RULE-013 intact in effect) -> input-validation gap, route CODER/M6-P1706 (validate sellable SKU, "
           f"reject value-shaped ref)")

    # W6 (CC-06) no learn->publish bridge: learn() returns a plain dict (no candidate/promote/emit); a top-scoring
    #    learned score hand-fed through review+approve is STILL not publishable (score never gates publish).
    eng, store, queue = new_engine()
    seed_all(store)
    scores = eng.learn([VerifiedSignal(TargetDim.PERSONA, 0.99, _PASS, True)])
    no_bridge = not any(hasattr(eng, m) for m in ("to_candidate", "promote", "emit_candidate", "publish_scores"))
    eng.review(candidate("lc_learned", target_dim="persona", score=scores[TargetDim.PERSONA]))
    decided = eng.record_review_decision("lc_learned", owner("APPROVED"))
    record("W6-no-learn-publish-bridge", "FAIL-006",
           "DEFENDED" if isinstance(scores, dict) and no_bridge and not decided.is_publish_authorized else "BREACH",
           f"learn() returns a dict {{persona:0.99}} (no candidate/promote/emit method={no_bridge}); a 0.99 learned "
           f"score routed through review+approve -> is_publish_authorized={decided.is_publish_authorized} (score "
           f"never gates publish; handoff is owner-mediated)")


def main():
    print("=" * 100)
    print("M6-P1705 BOUNDARY_ADVERSARY - executed attacks vs FROZEN staged M6.2H (Learning Engine)")
    print(f"impl root: {IMPL}")
    print(f"posture: gateway={config.GLOBAL_GATEWAY_STATE} prod={config.PRODUCTION_FLAG} "
          f"external_send={config.EXTERNAL_SEND} LEARNING_AUTOPUBLISH_ENABLED={config.LEARNING_AUTOPUBLISH_ENABLED} "
          f"LEARNING_SAFE_RANGE_RATIFIED={config.LEARNING_SAFE_RANGE_RATIFIED} "
          f"LEARNING_CONTENT_FILL_ENABLED={config.LEARNING_CONTENT_FILL_ENABLED}")
    print("=" * 100)
    for grp in (group_a, group_b, group_c, group_d, group_e, group_w):
        print(f"\n----- {grp.__name__} -----")
        grp()

    from collections import Counter
    tally = Counter(k for _, _, k, _ in RESULTS)
    print("\n" + "=" * 100)
    print(f"SUMMARY: {dict(tally)}")
    print(f"TOTAL RECORDED OUTCOMES: {len(RESULTS)}")
    print(f"IN-SCOPE FAIL-GATE BREACHES (FAIL-006): {len(BREACHES)}")
    for b in BREACHES:
        print(f"   !!! BREACH {b}")
    print("=" * 100)
    assert config.GLOBAL_GATEWAY_STATE == "BLOCKED" and config.PRODUCTION_FLAG == "OFF"
    assert config.LEARNING_AUTOPUBLISH_ENABLED is False and config.LEARNING_SAFE_RANGE_RATIFIED is False
    assert config.LEARNING_CONTENT_FILL_ENABLED is False


if __name__ == "__main__":
    main()
