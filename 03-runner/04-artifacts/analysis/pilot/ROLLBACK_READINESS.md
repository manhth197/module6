# M6 — Pack-Level Rollback Readiness Index

> ## Headline (read first)
> **Every slice runbook (M6.2A…M6.2K) has an executable §4 rollback section** — confirmed. The whole pack is **STAGED**:
> nothing is live, **no migration was applied**, **no flag was flipped**, **no external send occurred** (verified by
> M6-P3006 — `production_flag=OFF`, `global_gateway_state=BLOCKED`, 0 enabling assignments pack-wide). So the pack-level
> rollback is **non-destructive by construction**: delete the staged impl trees and every slice returns to its prior
> slice byte-identical; there is **no live schema, flag, or egress to unwind**.
>
> **Honest scope caveat (§6):** the *staged-artifact* rollback (delete/revert) is complete and trivially executable. The
> *real-deployment* rollback — the down-DDL `DROP TABLE`/`DROP VIEW`, a config revert, or reversing an external send —
> is **documented per slice but has never been exercised**, precisely because nothing was ever applied, flipped, or
> sent. That belongs to the owner-controlled integration step (M6-OD-011), not to this staged build. This index does not
> claim production rollback is tested; it claims the staged build is fully reversible and the forward down-migrations
> are documented.
>
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched. This index flips
> nothing.

| Field | Value |
|---|---|
| Prompt | **M6-P3007** — `ROLLBACK_READINESS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE, phase PR_PILOT) |
| Entry gate | **M6-P3007=RUNNING** (order 193); dependency **M6-P3006=PASS** (production_flag verified STILL OFF; 0 enabling assignments) |
| Task | Consolidate rollback readiness — confirm every slice runbook has executable rollback steps; produce the pack-level rollback index |
| Sources | the 11 slice runbook §4 sections (`M6_2A…M6_2K_RUNBOOK.md`); `M6-P3006.json` (nothing live); `DECISION_REGISTER.md` |

---

## 1. Scope & method

`analysis_only` consolidation. I confirmed (by grep) that **all 11 slice runbooks carry a §4 "Rollback" section**, then
read each §4 in full (directly + via two read-only extraction passes) to build the per-slice index below. The
verification asks two things per slice: (a) are the steps **executable** (concrete delete / revert-to-prior / down-DDL),
and (b) does §4 cover **every change** (new files + patched carried files + staged migrations + config). This index adds
nothing to the pack; it flips no flag, applies no migration, and writes no enabling value.

---

## 2. The pack-level rollback model

The build is a **cumulative carry-forward chain**: each slice's impl tree **starts from a byte-identical copy** of the
prior slice, then adds its own layer and applies its in-place patches (so the prior slice's own tree stays untouched).
That makes rollback **composable and non-destructive**:

- **Whole-pack rollback** = delete `04-artifacts/impl/M6.2A/…/M6.2K/`. The canonical `00-spec/` and the state ledger
  `04-artifacts/state/` are **operator-owned and were never written by any executor** (hooks enforce) — nothing there to
  revert.
- **Single-slice rollback** = delete `04-artifacts/impl/M6.2X/` ⇒ returns to `M6.2(X-1)` byte-identical (the prior good
  state). Within a slice: new files → delete; patched carried files → revert to the prior slice's version; staged
  migration → delete the file now (or, only after a real owner-controlled apply, run its down-DDL).
- **Nothing live to unwind:** no migration was applied (`live_migrations=false`), no posture flag was flipped, no
  external send occurred, no in-memory store persisted (result logs / review queues / scale-request lifecycle are inert
  and discarded). M6-P3006 confirmed this as a null result.

---

## 3. Per-slice rollback index (all 11 slices — every §4 executable, covers every change)

| Slice | Baseline rollback | Staged migrations (never applied; down-DDL exists) | Patched/extended carried files → revert to prior | Config markers added (all fail-closed; no enabling value) | §4 executable + every-change |
|---|---|---|---|---|---|
| **M6.2A** | delete `impl/M6.2A/` (foundation; nothing prior) | `0001_create_web_event_logs.sql` → `DROP TABLE web_event_logs` | none (foundation) | `config.py` added new; no flag; no live setting | ✅ (leg L8) |
| **M6.2B** | delete `impl/M6.2B/` → M6.2A | `0002_create_ads_measurement_events.sql` → `DROP TABLE ads_measurement_events` | `ingest.py`, `consent/gate.py`, `audit.py`, `masking.py`, `migrations/README.md` → M6.2A | carried verbatim (no change) | ✅ (leg 7) |
| **M6.2C** | delete `impl/M6.2C/` → M6.2B | `0003_create_conversion_events.sql`, `0004_create_marketing_measurement_outbox.sql`, `0005_create_marketing_audience_outbox.sql` → `DROP TABLE` each | `ports.py`, `config.py`, `migrations/README.md` → M6.2B (additive) | `OUTBOX_MAX_RETRIES` (operational, default 5) | ✅ (leg 7) |
| **M6.2D** | delete `impl/M6.2D/` → M6.2C | **none** (send-discipline layer; no new table → no down-DDL, RULE-018) | `consent/gate.py`, `outbox/enqueue.py`, `outbox/measurement_dispatcher.py`, `outbox/audience_dispatcher.py`, `config.py`, carried fixtures/tests → M6.2C | `HASH_POLICY_RATIFIED=False`, `MEASUREMENT_HASH_ALGO=sha256` | ✅ (leg 7) |
| **M6.2E** | delete `impl/M6.2E/` → M6.2D | `0006_create_ads_attribution_context.sql` → `DROP TABLE ads_attribution_context` | `api/conversions.py`, `integration/payload.py`, `outbox/transport.py`, `outbox/measurement_dispatcher.py`, `outbox/audience_dispatcher.py`, `outbox/enqueue.py`, `store/measurement_event_store.py` (+`materialize()`), `config.py`, fixtures/tests → M6.2D | `SCALE_MODEL_RATIFIED=False`, `SCALE_EVIDENCE_MIN_CONFIDENCE=HIGH` | ✅ (leg 8) |
| **M6.2F** | delete `impl/M6.2F/` → M6.2E | `0007_create_ads_data_quality_check.sql` → `DROP TABLE`; `0008_create_ads_dashboard_support_view.sql` → **`DROP VIEW`** | `store/measurement_event_store.py` (+`set_data_quality_status()`), `config.py`, `conftest.py` → M6.2E | `DQ_STATUS_ORDER`, `DASHBOARD_ALERT_THRESHOLDS_DEFINED=False` | ✅ (leg 9) |
| **M6.2G** | delete `impl/M6.2G/` → M6.2F | `0009_create_ads_scale_request.sql` → `DROP TABLE ads_scale_request`; `0010_create_ads_scale_approval.sql` → `DROP TABLE ads_scale_approval` | `config.py` → M6.2F | `SCALE_EXECUTION_ENABLED=False` | ✅ (acceptance check 1) |
| **M6.2H** | delete `impl/M6.2H/` → M6.2G | `0011_create_ads_strategy_libraries.sql` → `DROP TABLE ads_strategy_library_entry` + `ads_strategy_mapping` (six library kinds = one kind-discriminated table + mapping); `0012_create_ads_learning_candidate.sql` → `DROP TABLE ads_learning_candidate` | `config.py` → M6.2G | `LEARNING_AUTOPUBLISH_ENABLED=False`, `LEARNING_CONTENT_FILL_ENABLED=False`, `LEARNING_SAFE_RANGE_RATIFIED=False` | ✅ (acceptance check 1) |
| **M6.2I** | delete `impl/M6.2I/` → M6.2H | **none** (measure-only projection; reads existing 0002+0006, RULE-018) | **none** (planned dashboard wiring reverted to M6.2H byte-identical) | **none** (measure-only ⇒ no new posture flag) | ✅ (acceptance check 1) |
| **M6.2J** | delete `impl/M6.2J/` → M6.2I | **none** (growth projection; no new table, RULE-018) | **none** (standalone growth projection) | **none** | ✅ (acceptance check 1) |
| **M6.2K** | delete `impl/M6.2K/` → M6.2J | **none** (evidence assembler; no evidence-pack table, RULE-018) | **none** (assembly-only) | **none** | ✅ (acceptance check 1) |

*Terminology note:* M6.2C/2D label their carried-file modifications "extended/additive" rather than "patched"; the
rollback category is the same — prior-slice files modified in place that revert to the prior slice's version.

---

## 4. The 12 staged migrations, consolidated (all `up`+`down`, **all NEVER applied**)

| # | Migration | Slice | Down-DDL |
|---|---|---|---|
| 0001 | `create_web_event_logs` | M6.2A | `DROP TABLE web_event_logs` |
| 0002 | `create_ads_measurement_events` | M6.2B | `DROP TABLE ads_measurement_events` |
| 0003 | `create_conversion_events` | M6.2C | `DROP TABLE conversion_events` |
| 0004 | `create_marketing_measurement_outbox` | M6.2C | `DROP TABLE marketing_measurement_outbox` |
| 0005 | `create_marketing_audience_outbox` | M6.2C | `DROP TABLE marketing_audience_outbox` |
| 0006 | `create_ads_attribution_context` | M6.2E | `DROP TABLE ads_attribution_context` |
| 0007 | `create_ads_data_quality_check` | M6.2F | `DROP TABLE ads_data_quality_check` |
| 0008 | `create_ads_dashboard_support_view` | M6.2F | **`DROP VIEW`** (a support view, not a table) |
| 0009 | `create_ads_scale_request` | M6.2G | `DROP TABLE ads_scale_request` |
| 0010 | `create_ads_scale_approval` | M6.2G | `DROP TABLE ads_scale_approval` |
| 0011 | `create_ads_strategy_libraries` | M6.2H | `DROP TABLE ads_strategy_library_entry` + `ads_strategy_mapping` (six library kinds = one kind-discriminated table + mapping) |
| 0012 | `create_ads_learning_candidate` | M6.2H | `DROP TABLE ads_learning_candidate` |

Slices adding **no** migration (RULE-018 — no invented table): **M6.2D** (send discipline), **M6.2I** (funnel
projection), **M6.2J** (growth projection), **M6.2K** (evidence assembler). Every migration file carries its own
`down`-DDL for the eventual owner-controlled apply; **none has been applied to any database**, so today's rollback for
each is simply "delete the staged file."

---

## 5. PR/PILOT analysis-only artifacts (rollback = delete the file)

These carry **no impl, no migration, no flag** — rollback is deleting the markdown + its evidence JSON:

- `E2E_CHAIN_REVIEW.md` (M6-P3000) · `OWNER_SIGNOFF_PACKET.md` (M6-P3004) · `PILOT_READINESS_REVIEW.md` (M6-P3005) ·
  this `ROLLBACK_READINESS.md` (M6-P3007). The pack-wide validation prompts (M6-P3001/3002/3003/3006) wrote only
  evidence JSON + read-only harness scripts (delete to revert). The M6.2K evidence package (`app/measurement/evidence/`)
  rolls back inside the M6.2K tree (§3).

---

## 6. Honest OPEN / BLOCKED reporting

**What is rollback-ready now (COMPLETE + executable):**
- Every slice's staged rollback is concrete and executable — delete the impl tree (→ prior slice byte-identical), revert
  the named patched files to the prior slice, revert the config markers, delete new files. The revert chain
  A→B→…→K is composable, so any slice can be unwound to its predecessor.
- Nothing live exists to unwind: no migration applied, no flag flipped, no external send, no persisted store (M6-P3006).

**What is documented but NOT exercised (the honest caveat — not a defect, a consequence of staged posture):**
- The **down-DDL `DROP TABLE`/`DROP VIEW`** for the 12 migrations has **never been run against a live database**
  (staged-never-applied). It is documented per migration but unexercised; it becomes real only at the owner-controlled
  integration step.
- **Reversing a real external send or a real scale** is out of scope of this staged build — `external_send=OFF`,
  `SCALE_EXECUTION_ENABLED=False`, no executor is wired (the scale gate is propose-only). A production rollback runbook
  for those actions is owner/M6-OD-011 work, not proven here.
- **In-memory inert stores** (outbox result logs, learning review queue, scale-request lifecycle) hold no durable state;
  rollback = discard. They have never been backed by a live store.

**Standing governance (unchanged):** `M6-P1000` (M6.2A entry) + `M6-P1309` (M6.2D exit) verdicts remain **BLOCKED (not
converted)**; the OPEN owner decisions and the M6.2G/H/I/J forward conditions remain in force. None of these affects the
staged rollback (which is delete-based and needs no owner decision); they gate the *forward* real deployment whose
production rollback is the documented-but-unexercised part above.

---

## 7. Immutable posture & verdict

- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `live_migrations=false`, and all scale/hash/learning/dashboard flags `False`. This index writes no enabling value.
- **Verdict (honest):** rollback readiness for the **staged build is COMPLETE** — all 11 slice runbooks carry an
  executable §4 that covers every change, and the pack-level rollback is a non-destructive delete of the staged trees
  with a composable prior-good-state revert chain and per-migration down-DDL on file. The **real-deployment rollback**
  (running the down-DDL against a live DB, reverting a live flag, reversing an external send) is **documented per slice
  but unexercised**, because nothing was ever applied/flipped/sent — that is owner-controlled integration work
  (M6-OD-011), honestly flagged, not claimed done here.

*Assembly note: `analysis_only` — read the 11 slice §4 sections + M6-P3006 + registers and wrote only this file and its
evidence JSON. Touched no `04-artifacts/state/`, applied no migration, flipped no flag, wrote no enabling value.
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` verdicts
remain BLOCKED (not converted).*
