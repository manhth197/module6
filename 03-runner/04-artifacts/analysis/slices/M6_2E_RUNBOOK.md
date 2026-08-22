# M6.2E Runbook — Attribution Resolver & Materializer

| Field | Value |
|---|---|
| Slice | **M6.2E** — resolve the attribution chain to verified revenue; missing/conflicting → LOW/HOLD, never scale evidence (RULE-009); snapshots immutable after verify, corrections via adjustment record (RULE-008); doc §11; depends on M6.2D |
| Produced by | **M6-P1408** `M6_2E_DOCS` (ANALYST_ARCHITECT, `analysis_only`) |
| Sources | `00-spec/slices/M6.2E.md`, `M6-P1407.json`, `M6_2E_EVIDENCE_INDEX.md`, `M6.2E/PLAN.md`, `M6.2E/IMPLEMENTATION_NOTES.md` |
| Posture (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `HASH_POLICY_RATIFIED=False`, `SCALE_MODEL_RATIFIED=False` |

> **Read first — this is a runbook, not a verdict.** It self-certifies nothing and advances no gate (RULE-015);
> the authoritative slice verdict is the slice-gate Judge's at **M6-P1409**. **This is the cleanest band so far,
> stated accurately (not as a pass):** entry is a real Judge PASS (M6-P1400 `SIGNED`), all seven band prompts
> self-report PASS, **both in-scope fail gates held** (FAIL-001 revenue, FAIL-004 core override), and the M6.2D
> consent/robustness residuals **F-D/F-E/F-F were closed** here (F-D now MANDATORY), executed-verified by both
> M6-P1405 and M6-P1406. **What is still open:** exit-gate leg 1 is **"supported (staged), not closed"** (tester
> withheld closure); new residuals (F-G + O-1/O-3/O-4/O-5) and a **new privacy question O-2b** route to CODER/owner;
> one M6.2D governance decision file (`M6-DEFER-FBC-M6.2D.json`) is **still missing**; and — inherited — the **M6.2D
> slice exit itself was via owner override** (M6-P1309 verdict BLOCKED, not converted). The mandatory M6.2G re-gate
> and `SCALE_MODEL_RATIFIED=False` (no row is scale evidence yet) are unchanged.

---

## 1. What this slice built

The **attribution layer** — resolve an ORDER_VERIFIED back to its source chain, materialize the snapshot set-once,
and correct only via an audited adjustment record — plus the **fix-first closure** of the M6.2D residuals.

| Capability | Rule | Contract | Where (staged under `04-artifacts/impl/M6.2E/`) |
|---|---|---|---|
| **Fix-first** F-D — conversions endpoint MANDATORY-binds `customer_or_guest_key ↔ consent subject_ref`, rejects borrowed consent, fails closed on a missing reader | RULE-002, FAIL-002 | CTR-017/006 | patched `app/api/conversions.py` |
| **Fix-first** F-E — `platform_event_id` escaped join → injective (no under-count) | RULE-005 | CTR-008 | patched `integration/payload.py` |
| **Fix-first** F-F — `safe_subject_ref` (`type(x) is str` only) so a hostile subject can't crash a worker | seam | CTR-021/022 | patched `outbox/transport.py` + both dispatchers + `enqueue.py` |
| Attribution context (19 DRAFT_LOCKED fields; `psid` masked on export; grading HIGH/MEDIUM/LOW + conflict) | RULE-009/014 | **CTR-002 (DRAFT_LOCKED)** | `models/attribution_context.py` |
| Attribution / Ads-context / Live-session **resolvers** — missing/conflicting → LOW/HOLD (RULE-009), never a Core override | RULE-009, FAIL-004 | CTR-002 | `attribution/resolver.py` |
| `attribution_materializer` worker — Zone-B **set-once**, revenue ONLY from ORDER_VERIFIED, idempotent, no commission | RULE-003/008/009/019 | **CTR-023** | `attribution/materializer.py`, `store/measurement_event_store.py` (+`materialize()`) |
| Adjustment-record path — post-verify correction is an audited append-only `AdjustmentRecord{actor,reason,audit,evidence}`, never a mutation | RULE-008 | — | `attribution/adjustment.py` |
| Config fail-closed markers `SCALE_MODEL_RATIFIED=False`, `SCALE_EVIDENCE_MIN_CONFIDENCE=HIGH` | RULE-009 | — | `config.py` (extended) |

Everything is **staged** — no live system, no applied migration, no external call, no flag flipped. Cumulative
snapshot: the M6.2D tree is carried forward byte-identical except the fix-first patches; the attribution layer is
added; migration `0006_create_ads_attribution_context.sql` is staged (never applied).

**How F-D was closed (honest note):** the coder's Round 1 correctly returned **BLOCKED** on F-D — it could not be
made mandatory by default without editing a carried TESTER smoke (a cross-role change a coder must not make
unilaterally). **Round 2, under explicit owner authorization**, realigned two carried hash-policy fixtures
(subject↔key only, **without changing what the smoke proves**) and closed F-D **mandatory** (bind always runs; a
missing reader is a wiring error → reject; the false "checkpoint-2 compensates" docstring was removed). Both
adversaries then executed-confirmed the closure; **M6-P1409 re-verifies it.**

**Scope boundary (carried, not bled):** commission is Finance-owned (RULE-019 — Diamond/referral recorded only,
never a number); the **attribution model final choice is M6-OD-005** (multi-model *display* implemented;
single-model *scale evidence* fail-closed pending owner); dashboards/DQ-checker → M6.2F; real send → M6.2D gates + M6.2G.

---

## 2. Operate (staged)

No production service (BLOCKED/OFF); nothing sends.

```bash
cd 04-artifacts/impl/M6.2E
python -m app        # prints the staged posture (BLOCKED / OFF / OFF), exit 0 — no server, no egress
```

- **Resolve → materialize (set-once):** the `AttributionResolver` builds an `ads_attribution_context` from an
  `ads_measurement_event` + `conversion_event` — tracing campaign/adset/ad/page/live/comment/messenger — and grades
  it: a **missing source → `MISSING_SOURCE` / `LOW`**, a conflict → `MULTI_TOUCH`/`DUPLICATE_RISK` / `LOW`-`HOLD`;
  only a complete single channel → `HIGH`/`NONE`. The `attribution_materializer` writes **Zone B** via the store's
  **set-once** `materialize()` — `revenue_value` **only** when the source is ORDER_VERIFIED (RULE-003).
- **Immutable after verify:** a direct Zone-B overwrite of a verified row is **rejected** (`MeasurementStoreViolation`);
  a correction is an audited append-only `AdjustmentRecord` — verified revenue is **never silently overwritten** (RULE-008).
- **Never scale evidence yet:** a LOW/HOLD row is flagged not-scale-evidence (RULE-009); and even a clean HIGH/NONE
  row is not scale evidence because **`SCALE_MODEL_RATIFIED=False`** (no attribution model is scale-authoritative
  until M6-OD-005) — doubly fail-closed.
- **No commission, no Core override** (RULE-019/FAIL-004): referral (`referral_link_id`/`diamond_id`) is recorded, never priced.

---

## 3. Verify

```bash
cd 04-artifacts/impl/M6.2E
python -m pytest -q          # expect: 239 passed / 0 failed (final tester run, M6-P1404)
```

| Check | Expected | Evidence |
|---|---|---|
| Full staged suite (223 carried M6.2D+coder + 16 tester smoke nodes) | **239 passed / 0 failed**, exit 0 | `04-artifacts/test-reports/M6.2E/SMOKE_RESULTS.md`; `M6-P1404.json` |
| **M6-SMK-006** — ORDER_VERIFIED with full campaign/adset/ad → dashboard input materialized (HIGH/NONE) | **PASS 4/4** | `SMOKE_RESULTS.md` |
| **M6-SMK-007** — ORDER_VERIFIED missing source → `Revenue vẫn lưu, attribution confidence LOW/HOLD` (never scale evidence) | **PASS 4/4** | `SMOKE_RESULTS.md` |
| **M6-SMK-013** — live/comment/messenger chain → `live_session_id, comment_id, messenger_thread_id` traced (psid masked) | **PASS 4/4** | `SMOKE_RESULTS.md` |
| **M6-SMK-018** (proposed HARDENING) — post-verify correction → direct mutation rejected, `AdjustmentRecord{actor,reason,audit,evidence}` created | **PASS 4/4 (EXECUTED, not waived)** | `SMOKE_RESULTS.md` |
| Fail-closed grading across all 12 confidence×conflict combos | pass | `04-artifacts/boundary-reports/M6.2E_boundary.md` |
| Fix-first regressions F-D/F-E/F-F (borrowed-consent refused; injective id; hostile subject → no crash) | pass | `tests/test_m6_2e_fixfirst_regressions.py` |
| No raw PII (scan) | **CLEAN over 117 files** (incl. a psid-literal probe) | `04-artifacts/security-reports/M6.2E_security.md` |
| Carried-forward M6.2D suite (no regression from the fix-first patches) | green | `IMPLEMENTATION_NOTES.md` §1 |

> **Verify does NOT assert leg closure.** The suites pass within the 239-test run and the boundary adversary
> executed the fail-closed grading, but exit-gate **leg 1 (Order Verified trace to source)** is **SUPPORTED
> (staged), not closed** — the tester withheld closure. Whether leg 1 closes is the **M6-P1409 Judge's** call.

---

## 4. Rollback — every change

**Baseline rollback is non-destructive: nothing is live.** All artifacts are staged under `04-artifacts/impl/M6.2E/`;
no migration, no external call, no flag written. Cumulative snapshot ⇒ **new** files revert by deletion; **patched**
carried-forward files revert to their M6.2D version; deleting the M6.2E tree returns to M6.2D (untouched). Per-item
detail: `PLAN.md` §5/§8, `IMPLEMENTATION_NOTES.md` §6.

| Change group | Files | Rollback |
|---|---|---|
| **Fix-first patches** (F-D bind, F-E injective id, F-F safe_subject_ref) | `app/api/conversions.py`, `integration/payload.py`, `outbox/transport.py`, `outbox/measurement_dispatcher.py`, `outbox/audience_dispatcher.py`, `outbox/enqueue.py` | **Revert each to its M6.2D version** |
| Attribution context model | `models/attribution_context.py` (CTR-002, 19 fields) | Delete (new) |
| Resolvers (ads/live) | `attribution/resolver.py` (+ `__init__.py`) | Delete (new) |
| Materializer (set-once) | `attribution/materializer.py` | Delete (new) |
| Adjustment-record path | `attribution/adjustment.py` | Delete (new) |
| Store Zone-B set-once method | `store/measurement_event_store.py` (+`materialize()`) | **Revert to M6.2D** (patched; insert-guard + forbidden update/delete unchanged) |
| Config markers | `app/config.py` (+`SCALE_MODEL_RATIFIED=False`, +`SCALE_EVIDENCE_MIN_CONFIDENCE=HIGH`) | **Revert to M6.2D** (no flag changed) |
| **Staged migration (the new owned table)** | `migrations/0006_create_ads_attribution_context.sql` (up + down) | **Never applied.** Delete staged file to revert now. **After a real apply, revert = down-DDL `DROP TABLE ads_attribution_context`** (Zone-B set-once → drop, not row-edit) |
| Owner-authorized fixture/test realignment | `tests/conftest.py`, `tests/smoke/test_smk_017_*`, `tests/test_hash_policy_no_raw_pii.py`, `tests/test_conversions_endpoint.py`, `tests/test_no_direct_external_send.py` | **Revert to M6.2D** (re-keyed subject↔key only; NO assertion loosened) |
| Tests | `tests/test_attribution_*`, `test_live_session_chain_trace.py`, `test_verified_immutable_adjustment.py`, `test_materializer_revenue_and_scale_rules.py`, `test_m6_2e_fixfirst_regressions.py` | Delete; test doubles only, no raw PII in fixtures |

**Consumed tables (customer_segments/members, event_registry, consent, guest_contacts) are never mutated by M6** →
nothing to roll back on the CRM/Core/Consent side. (Exit-gate leg **8** = this rollback documentation.)

---

## 5. Decision deltas + governance-file status

### 5.1 GOVERNANCE / DECISION-FILE STATUS — update to what M6.2D flagged (operator/owner)
> Two-directional: one previously-flagged gap is now **RESOLVED**; one is **still open.** The analyst cannot write
> to `evidence/decisions/` — surfaced so it is tracked.
- **RESOLVED — `M6-DEFER-OD003-M6.2D.json` now EXISTS** in `04-artifacts/evidence/decisions/` (owner filed it; its
  retro-note legitimizes the earlier phantom-referenced M6-P1306 SKIP that the M6.2D runbook flagged). The owner also
  filed **`M6-OVERRIDE-M6P1309-STAGED.json`**, which opened M6.2E STAGED after the **M6.2D slice-gate Judge (M6-P1309)
  returned BLOCKED** (verdict unmodified, **not** converted to PASS — same mechanism as M6.2A's override).
- **STILL OPEN — `M6-DEFER-FBC-M6.2D.json` was never created.** Recommended by M6-P1209/M6-P1300 and re-escalated by
  M6-P1400/1401 to bind F-B/F-C/F-A + F-D into the **M6.2G gate (M6-P1600) `RequiredInputs`** (so a real send can
  never be enabled with an open consent fail-open). The substance is now largely carried by
  `M6-OVERRIDE-M6P1309-STAGED` and F-D/F-E/F-F are closed — but the dedicated decision file + the M6-P1600 wiring
  **remain an operator/owner TODO.**

### 5.2 Owner decisions (parameters, for DECISION_REGISTER reconciliation)
| Decision | State | Effect |
|---|---|---|
| **M6-OD-005** (attribution model final choice) | **OPEN — the live scale-evidence gate** | Multi-model DISPLAY implemented (first/last touch recorded); **no model is scale-authoritative** (`SCALE_MODEL_RATIFIED=False` + `SCALE_EVIDENCE_MIN_CONFIDENCE=HIGH`) — even a clean HIGH/NONE row is not scale evidence until the owner ratifies |
| **M6-OD-012** (masking format) | OPEN — now includes the **O-2b** question | Should the policy mask `messenger_thread_id`/`comment_id`/`live_session_id` on export alongside `psid`? (§7.2) |
| **M6-OD-003** (hash) | OPEN — recorded at M6.2D; **N/A for M6.2E** (no external-send data path here) | — |
| **M6-OD-004** (connector) / **M6-OD-008** (revenue) | OPEN | Connector before real send; revenue ORDER_VERIFIED-only default (RULE-003) |
| **M6-OD-011** (stack) | Carried DECIDED | Attribution table + materializer service-account binding at owner integration |
| **ENTRY-001 / ENTRY-003** (inherited) | RISK-ACCEPTED under `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000 **BLOCKED**, not converted) | Bound to the mandatory M6.2G re-gate; not checked at M6.2E |

---

## 6. Changelog delta produced by this slice

**One deferred housekeeping item; no in-band schema change.** The slice adds **no schema change beyond the
harmonized contracts** (SCHEMA_CHANGELOG rows 9–33, judged PASS at M6-P0715 SIGNED). It **realizes** the DRAFT_LOCKED
`ads_attribution_context` (CTR-002, 19 fields) as staged code + a staged (un-applied) `0006` DDL.

- **CTR-023 canon-flip (operator, out-of-band):** `M6-CTR-023` (`attribution_materializer` worker) is still
  `MISSING / OWNER_DECISION_REQUIRED` in canon but **satisfied-for-entry** (producer M6-P0713 PASS; gate M6-P0715
  SIGNED). Canon-flip is **deferred, non-blocking operator housekeeping**. (`M6-CTR-002` is already DRAFT_LOCKED — no flip.)
- New tokens (`SourceConfidence`/`ConflictStatus` enums, `AdjustmentRecord` fields, `SCALE_MODEL_RATIFIED`,
  `SCALE_EVIDENCE_MIN_CONFIDENCE`, `safe_subject_ref`) are **implementation-internal vocabulary**, not owner-facing
  schema → **no** SCHEMA_CHANGELOG row.

---

## 7. Handoff to M6.2F (and the forward gates)

**M6.2F adds the dashboards + the data-quality checker (CTR-024, PASS/HOLD/FAIL transitions).** M6.2E materialized
the **Zone B** that feeds ROAS/CPA/AOV — but does not render it. The O-2/O-4 DQ items land at M6.2F.

### 7.1 MUST-FIX (routed to CODER; none trips an in-scope fail gate — armed-not-fired)
- **F-G [MINOR] — adjustment-path under-validation (RULE-008 completeness):** the adjustment path (a) accepts empty
  `actor`/`reason`/`audit_ref`/`evidence_ref`; (b) never checks the target row exists/verified; (c) stores `proposed`
  as a plain **mutable** dict. In every case the verified row is **unchanged** (the overlay is never applied) → **not
  FAIL-004** — a data-quality / accountability / immutability-completeness gap. Fix: require non-empty fields; assert
  the target row exists+verified; store `proposed` immutably.
- **O-1:** `AdjustmentRecord.proposed` has no field allow-list — a caller can park e.g. `commission_value` (stored,
  never computed/applied, so RULE-019 still holds); constrain to attribution/revenue fields.
- **O-5:** a `NaN`/`Inf` `revenue_value` breaks the set-once idempotent replay (`NaN != NaN`) → reject non-finite
  (`math.isfinite`); DQ gap → **M6.2F**.
- **O-4:** `materializer.verified_event_codes` is a constructor default (ORDER_VERIFIED is correct) — a mis-wire could
  book non-verified revenue; wiring discipline, not channel-reachable.
- **O-3 [carried M6.2A ingest, later hardening]:** the ingest path compares `snapshot.subject_ref == guest_id` on the
  **raw** value (not via `safe_subject_ref`) — a hostile `ConsentSnapshot` subclass could raise there
  (FAIL-002-adjacent, armed-not-fired; the ingest-path analogue of F-D/F-F). Route it through `safe_subject_ref`.

### 7.2 Privacy — for the owner / M6-OD-012 (routed)
- **O-2b [NEW]:** export masks **only** `psid` — `messenger_thread_id` / `comment_id` / `live_session_id` are
  exported **raw**. Defensible (object ids vs a user id), but a `messenger_thread_id` can resolve to a person, so
  **whether M6-OD-012's masking policy covers conversation/thread identifiers is an owner / privacy-legal call worth
  making explicit.** Not a present leak (in-memory/staged, no sink). (O-2: durable Zone-B keeps raw `psid`, masked on export.)
- Forward at the M6-OD-011 binding: the `attribution_materializer` worker must run under a **scoped service account**
  distinct from the runtime API.

### 7.3 Hard forward gates (immovable)
- **M6-OD-005** must be decided before any row is **scale evidence**; **M6-OD-003/004** before any **real send**.
- **`M6-DEFER-FBC-M6.2D.json`** should be filed and wired into the M6.2G gate (M6-P1600) `RequiredInputs` (§5.1).
- **M6.2G Scale-Gate re-gate (MANDATORY):** ENTRY-001/002/003 re-checked before any scale/send; **both M6-P1000 and
  M6-P1309 verdicts stay BLOCKED, not converted.** Posture stays `BLOCKED`/`OFF`/`OFF` + `HASH_POLICY_RATIFIED=False`
  + `SCALE_MODEL_RATIFIED=False`.

---

## 8. Pointers for the slice-gate Judge (M6-P1409)

This runbook and `M6_2E_EVIDENCE_INDEX.md` are **descriptive**. The slice verdict is the Judge's, from the evidence.
1. **What holds (executed):** genuine entry Judge PASS (M6-P1400 `SIGNED`); both fail gates held; SMK-006/007/013/018
   all 4/4 (SMK-018 executed, not waived); the fail-closed grading executed across all 12 confidence×conflict combos.
2. **Explicitly re-verify F-D closure** (the M6-OVERRIDE-M6P1309-STAGED condition + the M6.2D coder commitment):
   confirm the conversions endpoint **mandatorily** binds `customer_or_guest_key ↔ consent subject_ref` and fails
   closed (M6-P1405/M6-P1406 executed-confirmed it; note the honest Round-1-BLOCKED → Round-2-closed path).
3. **Leg 1** is "supported (staged), not closed" — read `M6.2E_boundary.md` + `SMOKE_RESULTS.md` directly.
4. **Forward items:** F-G/O-1/O-3/O-4/O-5 (before scale/real send), O-2b (owner/privacy-legal, M6-OD-012), M6-OD-005
   (before scale evidence); the still-open **`M6-DEFER-FBC-M6.2D.json`** governance TODO; the inherited
   risk-acceptances (M6-P1000 + M6-P1309 both BLOCKED, not converted); the **mandatory M6.2G re-gate** stands
   regardless — nothing here authorizes real scale or send.

*Analysis-only: no code, no migration, no flag, no external call, no self-certification. `04-artifacts/state/` untouched.*
