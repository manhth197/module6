# M6.2B — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2B** — Tracking & Event Contract (depends on M6.2A) |
| Assembled by | **M6-P1107** — `M6_2B_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-07-30 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1109). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`. This index flips nothing and self-certifies nothing. |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. It does **not** assert
> that slice M6.2B has passed its exit gate. Exit-gate items **5 and 6 are NOT yet met** (docs prompt M6-P1108 and
> the slice-gate Judge M6-P1109 have not run — the steps that *follow* this one). Unlike M6.2A, the M6.2B **entry
> gate is a real Judge PASS** (M6-P1100 `SIGNED`, not an owner override), and the four M6.2A boundary residuals
> **F1/F2/MINOR-9/O1 were closed fix-first** in this slice (executed-verified by both M6-P1105 and M6-P1106). The
> authoritative slice verdict is the Judge's to render at M6-P1109, strictly from the evidence files, not from this index.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 88–97) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1100 | JUDGE | M6_2B_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1100.json` | PASS | false | `04-artifacts/evidence/judge/M6-P1100_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1101 | CODER | M6_2B_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1101.json` | PASS | false | `04-artifacts/impl/M6.2B/PLAN.md` |
| M6-P1102 | CODER | M6_2B_CODER_IMPLEMENT | PASS | `04-artifacts/evidence/prompts/M6-P1102.json` | PASS | false | `04-artifacts/impl/M6.2B/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1103 | TESTER | M6_2B_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1103.json` | PASS | false | `04-artifacts/impl/M6.2B/tests/TEST_MANIFEST.md` |
| M6-P1104 | TESTER | M6_2B_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1104.json` | PASS | false | `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md` |
| M6-P1105 | BOUNDARY_ADVERSARY | M6_2B_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1105.json` | PASS | false | `04-artifacts/boundary-reports/M6.2B_boundary.md` |
| M6-P1106 | SECURITY_PII | M6_2B_SECURITY_REVIEW | PASS | `04-artifacts/evidence/prompts/M6-P1106.json` | PASS | false | `04-artifacts/security-reports/M6.2B_security.md` |
| **M6-P1107** | PM_ORCHESTRATOR | M6_2B_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1107.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2B_EVIDENCE_INDEX.md` |
| M6-P1108 | ANALYST_ARCHITECT | M6_2B_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2B_RUNBOOK.md` (pending) |
| M6-P1109 | JUDGE | M6_2B_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1109_JUDGE_FINAL_SIGN_OFF.json` (pending) |

The **seven** band evidence JSONs that exist (M6-P1100 … M6-P1106) are schema-valid and declare
`fail_gate_tripped=false`; every one self-reports PASS and the entry gate M6-P1100 is a genuine Judge `SIGNED`
verdict PASS. This prompt's own `M6-P1107.json` is produced at completion (written **last**, after this index —
pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2B/`)
- `PLAN.md` — minimal staged change set + fix-first §5.1 items + master traceability + per-item rollback (§ legs 1–7).
- `IMPLEMENTATION_NOTES.md` — realized plan + deltas; §7 rollback.
- Carried-forward M6.2A tree + M6.2B additions. New/patched modules: `app/measurement/tracking/base_events.py`
  (9 LOCKED base events VIEW_LANDING..ORDER_VERIFIED, verbatim), `tracking/hooks.py` (client hook = unknown-event layer 1),
  `app/api/track.py` (framework-neutral `handle_track_request` = layer 2 + server-derived RULE-005 key),
  `models/measurement_event.py` (CTR-001, 20 fields), `store/measurement_event_store.py` (append-only + UNIQUE dedup),
  `normalize.py`, `adapters/consent_reader.py` (staged in-memory), and fix-first patches to
  `ingest.py` / `consent/gate.py` / `audit.py` / `masking.py`.
- Migrations (staged, never applied): `migrations/0001_create_web_event_logs.sql`,
  `migrations/0002_create_ads_measurement_events.sql` (up + down-DDL), `migrations/README.md`.

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2B/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_001_track_unknown_event.py` (6), `tests/smoke/test_smk_003_duplicate_dedup.py` (4).
- Leg-supporting: `tests/test_track_unknown_event.py` (L1), `tests/test_track_idempotency_dedup.py` (L2),
  `tests/test_measurement_event_store.py` (RULE-005/007), `tests/test_track_contract_and_validation.py`,
  `tests/test_m6_2b_fixfirst_regressions.py` (F1/F2/MINOR-9/O1) + carried-forward M6.2A suites.

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md` (full staged suite **139 passed / 0 failed**; SMK-001 6/6, SMK-003 4/4; L1/L2 supporting legs 14/14).
- Boundary report: `04-artifacts/boundary-reports/M6.2B_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2B_security.md`.
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1100_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS).

### 2.4 Governing spec / registers / decisions indexed
- `00-spec/slices/M6.2B.md` (exit-gate checklist, in/out scope, contract + smoke bindings).
- `00-spec/registers/SMOKE_REGISTER.md` (M6-SMK-001, M6-SMK-003 verbatim scenario/expected).
- `00-spec/registers/CONTRACT_REGISTER.md` (M6-CTR-001, M6-CTR-016).
- `04-artifacts/evidence/decisions/M6-DEFER-F1F2-M6.2B.json` (fix-first binding), `M6-OVERRIDE-M6P1000-STAGED.json` (inherited from M6.2A).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status | Note |
|---|---|---|---|---|
| M6-CTR-001 | ads_measurement_event (row contract of `ads_measurement_events`) | **M6 (owned)** | **DRAFT_LOCKED** | 20 fields, doc §10 / SPEC §10.1; enforced by `models/measurement_event.py` + store |
| M6-CTR-016 | POST /api/ads/events/track | **M6 (owned)** | **MISSING / OWNER_DECISION_REQUIRED** | **satisfied-for-entry** per the slice checklist ("if MISSING, its harmonization prompt must be PASS"): producer M6-P0711 = PASS, gate M6-P0715 = SIGNED, complete schema staged at `04-artifacts/analysis/contracts/CONTRACT_TRACK_APIS.contract.yaml`. **Canon-flip is deferred, non-blocking operator housekeeping** (see B4). |

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound
suites pass but the tester withheld leg-*closure* (called the leg "supported") and residuals remain, so final
closure is the slice-gate Judge's call · **PENDING** = the producing prompt has not run yet. Caveats are
carry-forwards (see §5); none trips the in-scope fail gate (M6-FAIL-003).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **Unknown event fails** — absent-from-registry event rejected/held with audit at **both** frontend-hook and backend-validation layers | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md` (SMK-001 6/6 — proves both layers independent + HOLD arm) + `tests/test_track_unknown_event.py` (6/6); `app/measurement/tracking/hooks.py`, `app/api/track.py`, `app/measurement/registry/validator.py`; boundary `M6.2B_boundary.md` (FAIL-003 not tripped, two-layer independence executed) | RULE-001/018; guards M6-FAIL-003. Tester (M6-P1104) calls leg **L1 "supported", not "closed"**. Caveat MINOR-6: `validator.validate` doesn't assert `row.event_code==requested` (needs a hostile/loose adapter; the shipped strict registry closes it). Robustness residual F-A routed to CODER. Final L1 closure is the slice-gate Judge's call. |
| 2 | **Duplicate event handled** — idempotency_key formula applied; replayed events create no duplicate rows | **SUPPORTED (staged)** | `SMOKE_RESULTS.md` (SMK-003 4/4) + `tests/test_track_idempotency_dedup.py` (4/4) + `tests/test_measurement_event_store.py` (4/4); `app/measurement/logs/idempotency.py`, `store/measurement_event_store.py`, `app/api/track.py` (server-derived RULE-005 key); boundary confirmed exact-replay dedup + key injective (0 collisions) | RULE-005/007. Tester calls leg **L2 "supported", not "closed"**. Caveat F-B: the server-side `raw_event_hash` is over-broad → cosmetic ts/field variants **over-count** (dedup quality, not drift; not FAIL-003). Scope: cross-source Pixel/CAPI/Offline dedup-by-content is **deferred to M6.2D**; M6.2B proves exact-replay dedup only. Final L2 closure is the slice-gate Judge's call. |
| 3 | **Smoke M6-SMK-001 executed** with recorded result + evidence ref | **MET** | `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md` (6/6, exit 0); `04-artifacts/evidence/prompts/M6-P1104.json` | Scenario/expected recorded verbatim; executed end-to-end through hook + endpoint. |
| 4 | **Smoke M6-SMK-003 executed** with recorded result + evidence ref | **MET** | `04-artifacts/test-reports/M6.2B/SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1104.json` | Exact-replay dedup proven end-to-end across both append-only stores. |
| 5 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1100.json` … `M6-P1106.json` present (7); `M6-P1107.json` produced at this prompt's completion | **Not yet complete:** M6-P1108 (Docs) and M6-P1109 (Judge) evidence not produced (both TODO). |
| 6 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1109_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1109 is TODO. (The existing `M6-P1100_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate, verdict PASS — not the slice gate.) |
| 7 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2B/PLAN.md` (per-item Rollback columns: patched files → revert to M6.2A version, new files → delete) + `IMPLEMENTATION_NOTES.md` §7; `migrations/0002_create_ads_measurement_events.sql` (down-DDL); `migrations/README.md` | All changes staged ⇒ non-destructive; append-only table revert = down-DDL `DROP TABLE`. |

**Summary:** items **3, 4 and 7 are MET**; items **1 and 2 are SUPPORTED at the staged level** — the bound
smoke + supporting suites pass within the 139-test run and the boundary adversary executed both the two-layer
unknown-event check and exact-replay dedup, but the tester deliberately withheld leg-*closure* on L1/L2 and the
MINOR-6 / F-A / F-B residuals remain, so **final L1/L2 closure is the slice-gate Judge's call**; items **5 and 6
are PENDING** (M6-P1108 docs, then M6-P1109 slice-gate Judge). Coverage: **every exit-gate checklist item is
indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | `Event không có trong event_registry` | `Reject/HOLD, audit rõ` | **PASS 6/6** | `SMOKE_RESULTS.md`, `M6-P1104.json` |
| M6-SMK-003 | ADS-P0-003 | `Duplicate Pixel/CAPI/Offline` | `Dedup, không double count` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1104.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips the in-scope
fail gate (M6-FAIL-003) — each was already adjudicated by the responsible upstream prompt and is carried forward
as governance context for the slice-gate Judge (M6-P1109) and the owner.

- **Closed this slice (positive, for context).** The four M6.2A residuals bound as fix-first preconditions by the
  entry gate (`M6-DEFER-F1F2-M6.2B.json`) were **closed and executed-verified** by both M6-P1105 (boundary) and
  M6-P1106 (security): **F1** (forgiving seam never raises — validate/resolve/subject_matches/store.append wrapped
  as audited denies; ts guard widened to OverflowError/tzinfo-raise), **F2** (gate asserts `consent_scope` is a
  real `frozenset[ConsentScope]`, closing the subclass fail-open), **MINOR-9** (closed for flagged shapes),
  **O1** (correlation_id masked on export).

- **B1 — Slice exit gate is not complete (expected at this step).**
  - Item 5 pending: **M6-P1108** (Docs) and **M6-P1109** (Judge) evidence JSONs not yet produced.
  - Item 6 pending: **M6-P1109** slice-gate Judge PASS sign-off does not exist.
  - *Disposition:* normal sequence — these are the prompts that follow M6-P1107.

- **B2 — CODER fix-first / hardening residuals introduced or observed at M6.2B, routed forward before the HTTP
  binding (armed-not-fired; none trips M6-FAIL-003).**
  - **F-A [MINOR]:** the endpoint's pre-seam `_contains_raw_pii` + `_raw_event_hash` run **before** the hardened
    seam and are unwrapped — a deeply-nested JSON body (~4000 deep) → `RecursionError` escapes the handler
    unaudited (a 500 / DoS + lost-audit gap). Wrap in the audited-deny pattern and bound payload nesting depth.
  - **F-B [MINOR]:** over-broad `raw_event_hash` over-counts cosmetic `event_ts` / field variants (dedup quality).
    Hash a canonical projection (`normalize_ts`, restricted to the CTR-016 contract fields).
  - **MINOR-6:** `validator.validate` doesn't assert `row.event_code == requested` (needs a hostile/normalizing adapter).
  - **MINOR-9-residual:** the audit event_code **denylist** (`\d{6,}` + finite id-prefix list) still leaves a
    <6-digit / unlisted-prefix identifier-shaped code verbatim in the in-memory audit sink (latent). Replace the
    denylist with an **allowlist** of the real registry base-event grammar.
  - *Ref:* `04-artifacts/boundary-reports/M6.2B_boundary.md`.

- **B3 — Security residual (M6-P1106), forward-routed.**
  - **O-1 [MEDIUM, latent]:** the endpoint PII tripwire scans the **payload only**; a raw email / VN-phone in the
    top-level `session_id` / `page_id` / `source` / `guest_id` bypasses it and is stored **raw** in the durable
    `web_event_logs` + `ads_measurement_events` rows (masked on export/audit). Latent while the stores are
    in-memory/staged; becomes a FAIL-008-class issue at durable binding. Extend the guard / add pseudonymous-id
    charset validation before durable binding.
  - Forward at the M6-OD-011 HTTP-binding step: request **authN/authZ**, **rate limiting**, and payload size/depth bounds.
  - *Ref:* `04-artifacts/security-reports/M6.2B_security.md`.

- **B4 — Contract housekeeping (non-blocking).** M6-CTR-016 (POST /api/ads/events/track) is
  **MISSING / OWNER_DECISION_REQUIRED** in canon but satisfied-for-entry (schema staged at
  `CONTRACT_TRACK_APIS.contract.yaml`; producer M6-P0711 PASS; gate M6-P0715 SIGNED). The canon-flip
  (apply to `00-spec/contracts/` + `CONTRACT_REGISTER` DRAFT_LOCKED + SCHEMA_CHANGELOG row; CTR-016 only —
  CTR-017 is M6.2C) is deferred operator housekeeping, flagged by M6-P1100.

- **B5 — Inherited cross-slice carry-forwards (from M6.2A, still in force).** ENTRY-001 (P3 verified-revenue
  boundary) and ENTRY-003 (event_registry gaps; Platform/P0-06-owned) remain **risk-accepted** under
  `M6-OVERRIDE-M6P1000-STAGED` (M6-P1000 verdict stays **BLOCKED**, not converted to PASS); they are bound to
  M6.2A entry + the **mandatory M6.2G Scale-Gate re-gate**, and were **not** checked at M6.2B. Open owner
  decisions carried forward: **M6-OD-003** (hash policy — M6.2D exit / M6-SMK-017), **M6-OD-012** (masking
  format), **M6-OD-009** (GOLDEN_HOUR_* events — OPEN; excluded from `base_events.py`).

- **B6 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`
  are unchanged and unchangeable by this slice; external platform sends / audience sync / dashboard are **out of
  scope** for M6.2B. The **mandatory M6.2G Scale-Gate re-gate** stands before any real scale or external send.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1109)

1. Start from `00-spec/slices/M6.2B.md` "Exit gate checks" (the 7 items in §4 above).
2. For legs 1–4 + 7, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. Confirm items 5 & 6 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1109 sign-off should be
   the Judge's own output).
4. Note the healthy posture (real entry-gate PASS; F1/F2/MINOR-9/O1 closed fix-first) **and** weigh the B2/B3
   forward residuals (F-A/F-B/MINOR-6/MINOR-9-res/O-1) as "close before the HTTP/durable binding", plus the
   inherited B5 risk-acceptances and the mandatory M6.2G re-gate.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
