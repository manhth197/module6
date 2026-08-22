# M6.2E IMPLEMENTATION NOTES — Attribution Resolver & Materializer (STAGED)

**Prompt**: M6-P1402 (`M6_2E_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Follows**: [PLAN.md](PLAN.md) (M6-P1401, JUDGE-signed entry M6-P1400). Built item-by-item against the plan; the
one plan-delta is noted in §5. **Posture unchanged & immutable**: `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False`. No code
applies a migration, calls anything external, or flips any flag.

> ## EVIDENCE STATUS: Round 1 = BLOCKED → **Round 2 = resolved (self-reported PASS; gate/downstream decide)**
> **Round 1** delivered the attribution layer (complete, clean) + F-E/F-F, but marked **BLOCKED** because the
> mandated fix-first **F-D** could not be closed-by-default without editing a carried TESTER smoke — a cross-role
> contradiction I correctly refused to resolve unilaterally.
> **Round 2** (owner-authorized, `D:\M6\BRIEF_M6-P1402_ROUND2.md` — the owner explicitly authorized realigning
> the two carried hash-policy test fixtures, subject↔key, WITHOUT changing what they prove) closes all three
> open items: **F-D is now MANDATORY** (bind always runs; a missing reader fails closed; the two hash-policy
> tests were re-keyed to a self-key consent so they still prove PII-hashing); **FF-1/FF-2** (two bind sites I had
> missed — `/conversions` and audience `enqueue` — now route through `safe_subject_ref`). Full suite **223 tests,
> rc 0**. F-D closed → no open_blockers. Posture immutable (BLOCKED/OFF/OFF/False/False). See §Round 2. One
> out-of-scope observation surfaced (carried M6.2A ingest subject compares raw — not a Round-2 site).

## 1. Staging model — cumulative carry-forward

The entire **M6.2D** tree (201 tests) was carried forward byte-identical into `04-artifacts/impl/M6.2E/`
(caches excluded; `PLAN.md` kept from M6-P1401, this file added). M6.2E then **patched** the F-D/F-E/F-F sites and
**added** the attribution layer. Baseline verified green (201 passed, rc 0) BEFORE any patch; final suite is
**214 passed, rc 0** (201 carried + 13 new). Test counts captured via subprocess (not dot-counting).

## 2. Fix-first BINDING — closed FIRST, carried suite stays green

| Fix | Files (patched, carried-forward) | What changed | Regression guard |
|---|---|---|---|
| **F-D** measurement borrowed-consent ⚠️ **NOT closed-by-default (BLOCKED)** | `app/api/conversions.py` | `ConversionDeps` gains a read-only `consent_reader` (**default `None`**). When wired, the endpoint binds `customer_or_guest_key ↔ consent snapshot `subject_ref`` at creation (checkpoint-1); mismatch/absence → `CONSENT_MISSING_OR_INVALID` (**borrowed consent refused**), mirroring the F-C audience fix. Subject extraction is fail-closed (F-F discipline). The bind LOGIC is correct and proven in T6. **BUT** it is enforced only when a reader is wired, and there is no production wiring point + no send-time subject-bind → **F-D is not closed by default** (see status banner + §7 + open_blockers). | Shared `conversion_deps` fixture keeps `consent_reader=None` → carried conversion tests (incl. the two PII tests that set `customer_or_guest_key`≠consent-subject) are unchanged. F-D is enforced+tested via a dedicated deps in T6 (borrowed refused, bound accepted). |
| **F-E** non-injective platform event_id | `app/measurement/integration/payload.py` | `platform_event_id` now **escapes** the `source_event_id\|event_code` join (`\\` then `\|`, same discipline as `enqueue._hash_key`) → injective → two distinct events never share an id (no platform under-count, FAIL-001-adjacent). | For ids without `\|`/`\\` the serialization is **byte-identical** to before → M6.2D dedup tests (`test_platform_dedup_event_id`, SMK-003) unchanged. |
| **F-F** raising `subject_ref` crashes worker (+ round 2) | `app/measurement/outbox/transport.py` (+ both dispatchers) | New `safe_subject_ref(snap)` catches ANY exception on access → `None`; both dispatchers extract the subject through it. **Round 2** (adversarial review): it now returns a value ONLY when `type(subject) is str` — a hostile str-SUBCLASS (raising `__eq__/__ne__`, which would crash the audience `subject != member_key` bind) and a raising `__class__` property (which would crash `isinstance`) both map to `None` → fail-closed, no crash. | Normal snapshots (plain-str `subject_ref`) behave identically → carried tests unchanged; 4 F-F regressions in T6 (raising-access, str-subclass, raising-`__class__`, both dispatchers). |

> **Test accommodation (not a loosened assertion)**: `tests/test_no_direct_external_send.py` field-set whitelist
> gained `"consent_reader"` — the deps legitimately gained a **read-only** port (like `validator`). The RULE-004
> guard (forbidden `transport`/`send`/`dispatch`/`deliver`/`sync` attrs) is **unchanged**; no assertion weakened.

## 3. Attribution layer (new)

| # | File | Purpose |
|---|---|---|
| B1 | `app/measurement/models/attribution_context.py` | `AdsAttributionContext` (CTR-002, **19 DRAFT_LOCKED fields verbatim, SPEC §10.2**) + `EntryChannel`/`SourceConfidence`/`ConflictStatus`; frozen; `psid` masked on export (`to_public`); durable `as_stored` keeps raw (Zone-A discipline). `is_scale_evidence_eligible()` = HIGH ∧ conflict NONE (RULE-009 data-quality bar). |
| B2 | `app/measurement/attribution/resolver.py` (+ `__init__.py`) | `AttributionResolver` + `resolve_ads_context` + `resolve_live_session`. Deterministic (no clock/random → idempotent). Grading: no source → `MISSING_SOURCE`/LOW; duplicate-risk signal → `DUPLICATE_RISK`/LOW; >1 entry channel → `MULTI_TOUCH`/LOW; single clear channel → NONE + HIGH iff fully identified else MEDIUM. Traces live/comment/messenger (SMK-013). Read-only over consumed sources (no Core override, FAIL-004). |
| B3 | `app/measurement/attribution/materializer.py` | `AttributionMaterializer` (CTR-023 worker). `materialize()` resolves + writes Zone B via the store's set-once method; `revenue_value` ONLY when ORDER_VERIFIED (RULE-003); idempotent; two fail-closed scale facets (`scale_evidence_eligible` = RULE-009 bar; `scale_evidence` = that ∧ `SCALE_MODEL_RATIFIED`, always False while M6-OD-005 OPEN). `request_adjustment()` = the ONLY post-verify correction (audited `AdjustmentRecord`, never a mutation). No commission (RULE-019). |
| B4 | `app/measurement/attribution/adjustment.py` | `AdjustmentRecord{event_id, actor, reason, audit_ref, evidence_ref, proposed, at}` + append-only `AdjustmentLog`; `actor` masked on export. |
| B5 | `app/measurement/store/measurement_event_store.py` (patched) | New `materialize(event_id, *, attribution_context, revenue_value, order_code, verified)` — the ONLY Zone-B write, **set-once**: identical re-materialize is an idempotent no-op; a change to already-verified revenue/attribution raises `MeasurementStoreViolation` (→ caller must use an adjustment record, RULE-008). Revenue only alongside `order_code` and only when `verified`. Zone-A insert guard + forbidden update/delete unchanged. |
| M1 | `migrations/0006_create_ads_attribution_context.sql` | Staged engine-neutral DDL (up+down), CTR-002 19 fields + keys/indexes + immutability/RULE-009 comments; **never applied**. |
| A1 | `app/config.py` (extended) | `SCALE_MODEL_RATIFIED=False` (M6-OD-005 OPEN → no model scale-authoritative, fail-closed) + `SCALE_EVIDENCE_MIN_CONFIDENCE="HIGH"`. Not enabling flags. |

## 4. Tests → smoke/leg mapping (TESTER executes L2–L5)

| Test | Proves | Smoke |
|---|---|---|
| `test_attribution_trace_to_source.py` (T1) | ORDER_VERIFIED full campaign/adset/ad+page → HIGH/NONE, Zone B revenue set, traces to source | **SMK-006** |
| `test_attribution_missing_source_low_hold.py` (T2) | ORDER_VERIFIED, no source → revenue STILL stored, LOW/MISSING_SOURCE, not scale evidence | **SMK-007** |
| `test_live_session_chain_trace.py` (T3) | live/comment/messenger traced; psid masked on export | **SMK-013** |
| `test_verified_immutable_adjustment.py` (T4) | direct Zone-B overwrite rejected; correction = AdjustmentRecord; verified revenue never overwritten | **SMK-018** |
| `test_materializer_revenue_and_scale_rules.py` (T5) | revenue only ORDER_VERIFIED; MULTI_TOUCH→LOW not scale; no commission; idempotent re-materialize | SMK-006/007 |
| `test_m6_2e_fixfirst_regressions.py` (T6) | F-D borrowed-consent refused (+ bound accepted + no-reader backward-compat); F-E injective id; F-F both dispatchers survive a raising `subject_ref` | (SMK-002/003) |

Smoke **execution** with recorded results/evidence (legs L2–L5) is the **TESTER**'s (M6-P1403/1404) — no self-run.

## 5. Plan-deltas

- **F-D reader NOT wired into the shared `conversion_deps` fixture** (plan §5.1 implied wiring it for enforcement).
  Reason: two carried PII tests (`test_result_log_has_no_raw_pii`, SMK-017) deliberately set
  `customer_or_guest_key`≠consent-subject and MUST still enqueue to prove the hash/result-log path; strict binding
  there would wrongly reject them. F-D is still fully enforced+tested via a dedicated `ConversionDeps(consent_reader=…)`
  in T6 (borrowed refused, bound accepted, no-reader backward-compat). This preserves the plan's intent (F-D
  enforced + tested) without loosening any carried test.
- Everything else matches PLAN.md §5 (B1–B5, M1, A1, T1–T6).

## 6. Rollback

Staged only — baseline rollback = delete the M6.2E tree (M6.2D untouched). Per-item: new files → delete; patched
carried-forward files (`conversions.py`, `payload.py`, `transport.py`, both dispatchers,
`measurement_event_store.py`, `config.py`, `conftest.py`, `test_no_direct_external_send.py`) → revert to M6.2D.
Migration 0006 → down-DDL DROP (staged; not applied).

## 7. Adversarial self-review (ultracode) — 4 CONFIRMED findings, acted on

A read-only adversarial review ran over this change set: 5 independent reviewers (one per dimension), each
candidate finding then refuted-or-confirmed by an independent skeptic that drove the ACTUAL code (9 agents total).
Result: **F-E clean, attribution-invariants clean, PII/posture clean; 4 CONFIRMED findings** (all verified by
running the code) — 2 on F-F, 2 on F-D.

| # | Dim | Finding (confirmed) | Action |
|---|---|---|---|
| 1 | F-F | `safe_subject_ref` used `isinstance` → returned a str-SUBCLASS unchanged; a subclass with a raising `__ne__` crashes the audience `subject != member_key` bind. | **FIXED**: `type(subject) is str` (plain str only) → subclass maps to None → fail-closed. Regression `test_ff_audience_survives_str_subclass_raising_comparison`. |
| 2 | F-F | `isinstance` consults `__class__`; a hostile raising `__class__` property crashes `safe_subject_ref` outside the try. | **FIXED**: `type()` reads the C type slot, never `__class__`. Regression `test_ff_measurement_survives_raising_class_property`. |
| 3 | F-D | The borrowed-consent bind is opt-in (`consent_reader` default None); in the default wiring it is skipped → a conversion citing another subject's valid consent is CREATED. | **SURFACED → BLOCKED** (open_blocker B1). Bind logic kept + proven in T6; cannot be made mandatory without editing the carried TESTER smoke. |
| 4 | F-D | The docstring's compensating control ("send-time checkpoint-2 gates consent") is FALSE — the measurement dispatcher does no subject-bind and `MeasurementOutboxItem` carries no `customer_or_guest_key`. | **Docstring corrected** (honest); **BLOCKED** (open_blocker B2 — a CTR-008 contract change is needed for a send-time bind; out of CODER scope). |

This is a coder self-check, NOT a gate sign-off — the runner gate and JUDGE (M6-P1409, which verifies F-D) decide.
The two F-F fixes are landed and green; the two F-D findings are the reason this slice's evidence is **BLOCKED**.

## 8. Governance (unchanged)

`M6-DEFER-FBC-M6.2D.json` (binding F-B/F-C/F-A + F-D) still not filed — operator/owner action; wire into the M6.2G
gate (M6-P1600). This slice closes F-D/F-E/F-F under the M6-OVERRIDE-M6P1309-STAGED binding regardless. O-1 folds
into M6-OD-003; O-2/O-4 (DQ) → M6.2F. Real send/scale gated forward (M6-OD-003/004/005, mandatory M6.2G re-gate).
`M6-P1309` verdict stays BLOCKED (not converted). Nothing here authorizes scale or external send.

## Round 2 — F-D closed mandatory + FF-1/FF-2 (owner-authorized)

Round 1 was BLOCKED on the mandated fix-first F-D (couldn't be closed without touching a carried TESTER smoke).
The owner (`D:\M6\BRIEF_M6-P1402_ROUND2.md`) **explicitly authorized** realigning the two carried hash-policy
test fixtures — subject↔key only, NOT changing what the smoke proves — and downstream P1403–P1406 re-verify.
Round 2 closes three items; the attribution layer + F-E are untouched (were CLEAN).

**FIX 1 — FF-1 / FF-2 (crash fail-closed; two bind sites Round 1 missed).** The Round-1 review confirmed
`safe_subject_ref` was correct, but two NEW comparison sites I wrote read the RAW `subject_ref` (so a str-subclass
with a raising `__ne__`, or a raising `__class__`, still crashed):
- **FF-1** `app/api/conversions.py` (F-D bind): `subject != customer_or_guest_key` on raw getattr → now
  `safe_subject_ref(snap)` (plain str or None) → comparison can't touch a hostile object.
- **FF-2** `app/measurement/outbox/enqueue.py` (F-C eligibility bind): `getattr(snap,'subject_ref',None) ==
  member_key` → now `safe_subject_ref(snap)`.

**FIX 2 — F-D MANDATORY.** `handle_conversions_request` now ALWAYS binds `subject_ref ↔ customer_or_guest_key`
and refuses fail-closed on mismatch/absence; a missing `consent_reader` is a WIRING ERROR → reject (not skip).
The false "checkpoint-2 compensates" docstring is gone. Enabling changes, all owner-authorized:
- `tests/conftest.py`: added self-key consent snapshots `cs_selfkey_pii` / `cs_selfkey_email` (subject == the
  raw-PII key each hash-policy test uses; markers assembled at runtime — no literal PII in source); added those
  subjects to `app_consent_reader.current` (send-time VALID); wired `consent_reader=app_consent_reader` into the
  shared `conversion_deps` fixture.
- `tests/smoke/test_smk_017_hash_policy_no_raw_pii.py` (TESTER smoke) + `tests/test_hash_policy_no_raw_pii.py`
  (CODER): **re-keyed only** the cited `consent_snapshot_id` → `cs_selfkey_*`; the raw-PII `customer_or_guest_key`
  and every hashing / no-raw-PII assertion are UNCHANGED (the smoke still proves exactly what it proved).
- `tests/test_conversions_endpoint.py`: `_deps_with_events` gained a `consent_reader` param (mandatory bind).
- **T6** updated: removed the Round-1 `..._skipped_when_no_reader_wired` (no more skip); added
  `test_fd_default_deps_reject_borrowed_accept_matching` (§3.1 probe), `test_fd_no_reader_fails_closed`, and
  parametrized `test_ff1_*` / `test_ff2_*` over three hostile-subject shapes.

**Definition-of-done probes (§3 of the brief), all green:** (1) default deps reject borrowed consent
(`attacker_XYZ` citing `cs_valid`) / accept matching; (2) FF-1/FF-2 hostile subjects fail-closed, no crash;
(3) SMK-017 + test_hash_policy still green (hash path live, result log no raw PII); (4) full suite **223, rc 0**;
(5) attribution layer + F-E untouched.

**Out-of-scope observation (surfaced, NOT fixed):** the carried M6.2A **ingest** path
(`app/measurement/ingest.py` ~L311 + `identity/resolver.py`) compares `snapshot.subject_ref == guest_id` on the
RAW value. It operates on `isinstance(ConsentSnapshot)`-validated snapshots (a real dataclass field, plain str),
so it is not a live vector under the current trust model, and it is NOT one of the Round-2 sites the brief named.
A hostile `ConsentSnapshot` SUBCLASS with a `subject_ref` property could in principle raise there — flagging for
the owner/TESTER to decide whether to route it through `safe_subject_ref` in a later hardening (out of scope here).

Posture unchanged: BLOCKED/OFF/OFF/HASH_POLICY_RATIFIED=False/SCALE_MODEL_RATIFIED=False; no migration applied,
nothing sent, no flag flipped. Not a self-certified gate PASS — the runner gate + JUDGE (M6-P1409 verifies F-D)
decide.
