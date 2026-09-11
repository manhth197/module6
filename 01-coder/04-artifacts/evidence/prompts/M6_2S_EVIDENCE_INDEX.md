# M6.2S — Evidence index (registry-feed reader: event-registry-feed.v1, staleness-safe + fail-closed, RELAY_V221 §2.4, M6-OD-018)

| Field | Value |
|---|---|
| Prompt | **M6-P2707** — `M6_2S_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`, ledger row 267 RUNNING) |
| Slice | **M6.2S** — the M6-side reader for a **PROPOSED** `event-registry-feed.v1` (`GET /api/v1/internal/event-registry?since_version={n}` → `{registry_version, events:[{event_code,event_group,domain,data_sensitivity,external_send_policy,is_active,updated_at}]}`), consumed as a **value object / dict** (NOT a live HTTP call), staleness-safe by monotonic `registry_version`, fail-closed on every unknown, reusing the M6.2P `ExternalSendPolicy` enum. Cumulative superset of M6.2R under `04-artifacts/impl/M6.2S/`. STAGED. |
| Owner input | **M6-OD-018** DECIDED 2026-09-10 (owner + tech-lead); artifact `04-artifacts/evidence/decisions/M6-OD-018.json` filed (verified by the SIGNED entry judge M6-P2700 — this decision is properly recorded, unlike the carried M6-OD-013/014 hygiene gap). |
| Posture (immutable, this slice flips nothing) | `global_gateway_state=BLOCKED` · `production_flag=OFF` · `external_send=OFF` · `live_migrations=false` · `HASH_POLICY_RATIFIED=False`. `config.py`/`consumed.py`/`validator.py` **byte-identical to M6.2R** (reuse-only, no gate/config change). |
| Result | Band M6-P2700 **SIGNED** (entry) → M6-P2701..2706 all **PASS**; full staged suite **716 passed / 0 failed / 0 skipped / 0 error**; SMK-031 **28/28**; **0** in-scope FAIL-007/FAIL-008 breaches; PII/secret scan **clean** (281 files, canonical 0/0/0/0/0 incl. `client_secret`). This index does **not** self-certify; the runner gate + slice Judge M6-P2709 decide (RULE-015). |

> ## ⚠ Read this before reading "716 green" as production-ready — three honesty points
>
> **1. The reader is UNWIRED — that absence is the only thing keeping the one FAIL-008 residual (P2) out of BREACH.**
> `RegistryFeedRow.to_public()` echoes the free-text governance metadata (`event_code`/`event_group`/`domain`/`updated_at`)
> **verbatim, with no masking choke** (P2 / F-FEED-PII). It stays armed-not-fired **only** because `to_public` reaches
> **no durable sink** (N1, the load-bearing containment): `PII_FIELDS` has no `RegistryFeedRow` key **and no non-test
> `app/` module imports the reader or the feed models** (grep-clean). This is the same "M3-side adapter built ahead of
> wiring" shape as M6.2R's mapper (N8). **P2 flips to a live FAIL-008 the moment** either (a) any `app/` module
> serializes `to_public` output, **or** (b) the live M3 seam (ENTRY-003 V221) is wired — so an **input-side PII-shape
> reject** (not export-masking; security sharpened this) must land **before** the M6-OD-011 owner-controlled integration.
>
> **2. This proves capability against a MOCK of a contract that does not yet exist.** The endpoint name/shape carry a
> `TODO(contract)` marker (final = chief-issued, RELAY_V221 pending). The **two-enum reconciliation** (M6
> `{PUBLIC,INTERNAL,PII}` vs M3 `{SENSITIVE,INTERNAL}`) and the **tombstone/removal semantics** (S-08) are Core/chief-owned
> and **OPEN** — the reader consumes fail-closed but reconciles **nothing**. A green suite proves the reader handles a
> mock feed correctly; it does **not** prove the live contract, because the live contract is not finalized.
>
> **3. Classifying `external_send_policy` is NOT permitting egress.** The reader faithfully **reads** a Core-classified
> `ALLOW_EXTERNAL` row (RS5 — correct per RULE-001, M6 does not override the Core registry) yet opens **no egress**: no
> send verb, `EXTERNAL_SEND` Final **OFF**, and **which** events are permit-mapped `ALLOW_EXTERNAL` is the **OPEN**
> M6-OD-003 privacy/legal half. A Core-set `ALLOW_EXTERNAL` row is **inert** here. The egress controls are unchanged by
> this slice: `EXTERNAL_SEND=OFF` + M6-OD-003.

---

## 1. Slice under review

M6.2S adds **two new pure modules + one regression** (NO migration, NO gate/config change, NO HTTP client, NO new secret):

- `app/measurement/models/registry_feed.py` — `PROPOSED_FEED_CONTRACT`/`_ENDPOINT` + `TODO(contract)` markers; frozen
  `RegistryFeedRow` (reusing the M6.2P `DataSensitivity` + `ExternalSendPolicy` enums) + frozen `RegistryFeed`; `to_public`
  (7 governance-metadata fields).
- `app/measurement/adapters/registry_feed_reader.py` — `RegistryFeedReader.apply(feed)`: feed-level fail-closed guards
  (`not_mapping` / `bad_version` [bool excluded from int] / `bad_events` / `row_not_mapping` / `missing_event_code` → each
  leaves version+rows **unchanged**); staleness no-downgrade (`version <= current → stale`; version bumps **only** on a
  fully-valid feed, so a malformed higher-version feed cannot poison staleness); **all-or-nothing** parse-all-first upsert;
  fail-closed resolution reusing the M6.2P coercers (`_resolve_send_policy` unknown → `BLOCKED_DEFAULT`; `_resolve_sensitivity`
  None/unknown/`SENSITIVE` → `PII`; `is_active` strict `is True` → else False; optional metadata → None, never invented);
  `current_registry_version()` / `rows()` / `get()`. **No HTTP / live-endpoint import.**

`consumed.py` / `validator.py` / `config.py` are byte-identical to M6.2R (reuse-only). The live M3 HTTP client is **out of
scope** (ENTRY-003 V221 pending) — tests use a mock/staged feed only. **No flag flipped; no egress opened.**

## 2. Band evidence (every prompt in the M6.2S band)

| Prompt | Role | Task | Ledger | Evidence file |
|---|---|---|---|---|
| **M6-P2700** | JUDGE | entry-gate judge | **SIGNED** | `M6-P2700.json` + `judge/M6-P2700_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS: 4 checks satisfied; M6-OD-018 DECIDED+filed authorizes the slice; M6-CTR-003 DRAFT_LOCKED resolved-for-entry; M6-OD-003 OPEN + ENTRY-003 RISK-ACCEPTED + two-enum reconciliation are forward/out-of-scope) |
| **M6-P2701** | CODER | plan | **PASS** | `M6-P2701.json` + `impl/M6.2S/PLAN.md` (lean 2-module plan; plan red-team fixed 2 gaps pre-code: non-Mapping row crash → `row_not_mapping`; bool `registry_version` bypass → `bad_version`) |
| **M6-P2702** | CODER | implement | **PASS** | `M6-P2702.json` + `impl/M6.2S/IMPLEMENTATION_NOTES.md` (carried M6.2R byte-identical; baseline+parity 658==658 before patch; final 688; impl red-team CLEAN on fail-closed, refuted a false "delta-upsert" MINOR, confirmed a baseline-figure NIT) |
| **M6-P2703** | TESTER | build smoke | **PASS** | `M6-P2703.json` + `impl/M6.2S/tests/TEST_MANIFEST.md` (authored SMK-031 = 28 collected nodes; scenario/expected verbatim incl. the three U+2192 arrows; collect-only, 716 collected; static-verification workflow all-CLEAN) |
| **M6-P2704** | TESTER | run smoke | **PASS** | `M6-P2704.json` + `test-reports/M6.2S/SMOKE_RESULTS.md` (executed: full staged suite **716 passed/0 failed/0 skipped/0 error RC0**; SMK-031 **28/28**, isolated `-k` cross-check 28 passed; not owner-waived) |
| **M6-P2705** | BOUNDARY_ADVERSARY | attack | **PASS** | `M6-P2705.json` + `boundary-reports/M6.2S_boundary.md` (executed harness, 34 outcomes = 28 DEFENDED / 5 OPEN_NONGATE / 1 NOTE [N6, bundling S-08 + V2] / **0 in-scope BREACH**; posture BLOCKED/OFF/OFF unchanged; byte-clean) |
| **M6-P2706** | SECURITY_PII | security/PII | **PASS** | `M6-P2706.json` + `security-reports/M6.2S_security.md` (281 files scanned, canonical 0 token/0 secret [incl. 0 `client_secret`]/0 user-id/0 email/0 phone; reader fail-closed/PII-safe/no-HTTP/no-secret; sharpened P2 → input-side reject, not export-mask) |
| **M6-P2707** | PM_ORCHESTRATOR | **this evidence-collect** | **RUNNING** | `M6-P2707.json` (this index's evidence, written last) + this file |
| M6-P2708 | ANALYST_ARCHITECT | docs | TODO | pending (`M6_2S_RUNBOOK.md`) |
| M6-P2709 | JUDGE | slice-gate judge | TODO | pending (`judge/M6-P2709_JUDGE_FINAL_SIGN_OFF.json`) |

## 3. Artifacts / test reports / boundary + security reports

| Kind | Path | Note |
|---|---|---|
| Impl — models | `04-artifacts/impl/M6.2S/app/measurement/models/registry_feed.py` | new: `RegistryFeedRow`/`RegistryFeed`/`to_public` + `TODO(contract)` |
| Impl — adapter | `04-artifacts/impl/M6.2S/app/measurement/adapters/registry_feed_reader.py` | new: `RegistryFeedReader.apply()` fail-closed + staleness-safe; no HTTP import |
| Impl — plan/notes | `04-artifacts/impl/M6.2S/PLAN.md`, `.../IMPLEMENTATION_NOTES.md` | plan + implementation record (incl. §5 rollback) |
| Coder regression | `04-artifacts/impl/M6.2S/tests/test_m6_2s_registry_feed_reader.py` | 30 cases (SMK-031 fixtures + 2 red-team + delta-upsert/de-registration + boundary) |
| Official smoke | `04-artifacts/impl/M6.2S/tests/smoke/test_smk_031_registry_feed_reader_failclosed.py` | SMK-031, 28 nodes; scenario/expected verbatim |
| Test manifest | `04-artifacts/impl/M6.2S/tests/TEST_MANIFEST.md` | node→clause coverage, code-under-test, exit-gate legs |
| Smoke results | `04-artifacts/test-reports/M6.2S/SMOKE_RESULTS.md` | 716 full suite / SMK-031 28/28; per-node detail; masked synthetic trace ids |
| Boundary report | `04-artifacts/boundary-reports/M6.2S_boundary.md` | 34 outcomes, 0 in-scope breach; harness `04-boundary/work/attacks/m6_2s_attacks.py` |
| Security report | `04-artifacts/security-reports/M6.2S_security.md` | PII/secret scan clean; scanner `06-security/work/pii_scan_2s.py` |

## 4. Exit-gate checklist mapping (every leg of the M6.2S done-gate, `00-spec/slices/M6.2S.md` §"Exit gate checks")

| # | Exit-gate leg | Status | Evidence |
|---|---|---|---|
| 1 | proposed-shape parse + `TODO(contract)` (M6-OD-018): typed rows reusing `ExternalSendPolicy`; no invented field | **MET** | `registry_feed.py` (`TODO(contract)`, reuse enums) + reader; SMK-031 fixture i; coder regression; boundary FE7/R4 |
| 2 | staleness-safe by `registry_version` (monotonic; `<= last` not applied, no downgrade; current exposed) | **MET** | reader staleness guard; SMK-031 fixture ii + malformed-higher-no-poison neg; boundary ST1/ST2 |
| 3 | fail-closed + no live call + no egress (unknown → `BLOCKED_DEFAULT`/`PII`, feed error → not applied, no `ALLOW_EXTERNAL`, `EXTERNAL_SEND` OFF, no live endpoint) | **MET** | SMK-031 fixtures iii+iv + negatives + boundary node (no HTTP import; `EXTERNAL_SEND`/`PRODUCTION_FLAG`/`GLOBAL_GATEWAY_STATE` asserted OFF/OFF/BLOCKED); boundary FE/RS groups; security scan |
| 4 | Proposed smoke M6-SMK-031 executed OR owner-waived | **MET (executed, not waived)** | `SMOKE_RESULTS.md` — 28/28, RC0; isolated `-k` cross-check |
| 5 | All slice prompts have evidence JSON (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P2700..2706 done + schema-valid + clean; **M6-P2707 completing now**; **M6-P2708 (DOCS) still TODO** |
| 6 | Slice gate judge sign-off exists with verdict PASS | **PENDING** | **M6-P2709 TODO** (owner-run; not my task) |
| 7 | Rollback steps documented for every change this slice made | **MET** | `IMPLEMENTATION_NOTES.md` §5 "Rollback" (whole-slice: delete the `impl/M6.2S/` tree, M6.2R byte-identical & untouched, no live migration; per-item: delete the 3 new files [2 modules + the regression test]; no carried file edited) |

**MET = legs 1, 2, 3, 4, 7. PENDING = legs 5 (in progress — DOCS M6-P2708 + this JSON close it), 6 (judge M6-P2709).** Both pending legs are the normal remaining band tail, not defects.

## 5. Unresolved blockers / residuals (slice/owner-level — listed per the acceptance check; none blocks *this collection* prompt)

None of these blocks M6-P2707 (the collection is complete and unblocked). They are the routed items the slice Judge and the owner must weigh; **all are armed-not-fired in the staged posture (0 in-scope FAIL-007/008 breach).**

**Load-bearing (decide before wiring):**

- **P2 / F-FEED-PII → SECURITY/owner. The one FAIL-008 residual, contained today only by absence of a sink.**
  `to_public()` echoes free-text governance metadata verbatim with no masking choke. Security's adjudication (sharper than
  "reject or mask"): these are **governance identifiers, not PII** — they must export as-is (masking `event_code`/`event_group`/`domain`
  would break validation; the already-shipped `EventRegistryRow` sets `PII_FIELDS['EventRegistryRow']=()` as the
  governance-model **precedent**, and this slice's new `RegistryFeedRow` has **no `PII_FIELDS` entry at all** — consistent
  with N1, and the exact fact the security report §6's looser `EventRegistryRow=()` citation was pointing at). So the
  defense-in-depth is an **input-side reject of a PII-shaped value at parse** (an email-shaped reject on `event_group`/`domain`),
  **not** export-masking. Must land **before** any durable sink or the live M3 seam is wired (see N1).
- **N1 / no-durable-sink → the standing watch-item (judge + owner).** The single fact keeping P2 out of a live FAIL-008: no
  `app/` module imports the reader/feed models and `PII_FIELDS` has no `RegistryFeedRow` key. Flips the moment (a) an `app/`
  module serializes `to_public`, or (b) the live M3 seam (ENTRY-003 V221) is wired. Lock the P2 input-side reject + a
  `PII_FIELDS['RegistryFeedRow']` entry into the M6-OD-011 owner-controlled integration step.

**Code-hardening (CODER, all in-process-only today — a JSON feed off the wire yields `str`/`None`/`int`, all fail-closed):**

- **N5 / BND-01 (carried M6.2P) → CODER.** `_resolve_send_policy`/`_resolve_sensitivity` have no `isinstance(raw, str)` gate
  before the enum value-lookup, so a hostile `__eq__`/`__hash__` object could coerce to `ALLOW_EXTERNAL`/`PUBLIC`. Carried
  M6.2P hardening; reading opens no egress.
- **N2 / CRIT-02 → CODER.** The upsert mutation phase is not exception-atomic (a 2nd-row `event_code` whose `__hash__` raises
  commits the 1st row + propagates the exception → half-apply + crash). Fix: build into local copies + swap in one guarded
  block. Robustness caveat on the all-or-nothing claim (parse-phase rejection is atomic; upsert-phase is not).
- **N3 / CRIT-03 → CODER.** An `int` **subclass** with hostile `__le__` defeats the `<=` staleness guard (replay/downgrade);
  the guard excludes `bool` but does not canonicalize. Fix: `int(version)` / `type(version) is int`.

**Contract / Core-owned (CHIEF — do NOT self-resolve, RULE-001):**

- **N4 / CRIT-04 → CHIEF/CODER.** `event_code` stored **untrimmed** (`'purchase '` ≠ `'purchase'`), so a de-registration
  delta can miss a padded stale-active row (overstates liveness). Canonicalize/reject non-canonical `event_code` — a Core
  registry-semantics decision, not self-resolved.
- **N6 → CHIEF / owner (NOTE — one ref bundling two observations, per the M6-P2705 evidence of record).** (i) **S-08
  tombstone-by-omission** — the upsert has no removal path; an event Core removes by *omitting* it is retained at its
  last-seen state (overstates liveness); `TODO(contract)` already flags tombstone semantics as chief-owned. (ii) **V2
  huge-version staleness-pin** — a valid huge version applies once then pins later feeds `stale` (denial-of-progress /
  availability, not an in-scope FAIL gate). *(Counting note: M6-P2705.json + the boundary report header record "1 NOTE
  / 34 outcomes" treating N6 as one bundled ref; the boundary report §6-verdict prose counts these two observations as
  "2 NOTE" — a source-side counting-style difference that leaves the 0-in-scope-BREACH posture unchanged.)*

**Hard forward conditions (recorded, NOT resolved — gate any live registry pull / real scale / egress):**

- **M6-OD-003** (permit-mapping / hash policy) privacy/legal half **OPEN** — governs which events are `ALLOW_EXTERNAL`-permitted
  (not this reader); the egress control alongside `EXTERNAL_SEND` OFF.
- **The live M3 endpoint** (ENTRY-003 V221 pending) + the **two-enum reconciliation** + the **`TODO(contract)` finalization** +
  **M6-OD-011** server-bind/go-live.
- **Secret handover (forward):** when the live M3 client to `GET /api/v1/internal/event-registry?since_version={n}` is built,
  its credential must be a `secret_ref` (never raw) and the **M6.2O AST import-scan gate** (no HTTP client in `app/`) needs a
  **deliberate** allow-list update for that one client — owner-controlled (M6-OD-011), same shape as the M6.2R ops-core
  `client_secret` handover. Not this slice (no client built; `client_secret` scan = 0).

**Carried, unaffected by this slice:**

- **M6-OD-012** — the decision-export masking family (`OwnerDecision` M6.2R F-SEC-2R-1 + `AdsSpendImportDecision` M6.2Q MC-09
  `reason`/`audit_ref`). Still OPEN; M6.2S adds no new instance.
- **Trace-id family + F-EVID-4/5/6** — carried open evidence-trace-id residuals (per security report §10/§12); M6.2S adds no
  new instance (this slice's `SMOKE_RESULTS` trace ids are synthetic + export-masked, a separate clean fact).
- **B1 real-pepper + privacy/legal** — carried, covered above via the **M6-OD-003** forward-conditions bullet.
- **Operator hygiene (non-blocking; PM/JUDGE denied write root):** register **M6-OD-013** + **M6-OD-014** + the M5
  `PSID_HASH_POLICY_M5_TMP` dependency in `DECISION_REGISTER.md`; reconcile the stale **ENTRY-004** row. (Contrast: **M6-OD-018**
  for this slice **is** properly filed — `04-artifacts/evidence/decisions/M6-OD-018.json` exists.)

## 6. Count reconciliation + governance

- **Full staged suite 716 = 658 (M6.2R SIGNED carried) + 30 (coder regression `test_m6_2s_registry_feed_reader.py`) + 28
  (official SMK-031 nodes).** Gate invariant baseline ≤ final (658 ≤ 716) holds; 0 carried test dropped; 0 skip. Migrations
  stay `0001–0016`. `config.py` sha256[:16] = `911b32381368f355` unchanged.
- **Governance posture unchanged and immutable:** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `live_migrations=false`, `HASH_POLICY_RATIFIED=False`. **M6-P1000** (M6.2A entry) + **M6-P1309** (M6.2D exit) verdicts remain
  **BLOCKED** (not converted). No flag flip, no live HTTP, no egress, no gate/config change, no migration, no new secret, no
  write to `04-artifacts/state/`.
- **Boundary intact:** M6 **reads** the Core-owned governance feed fail-closed for its own validation; it does not write/invent
  an event, reconcile the Core enum, decide the permit-mapping, send CRM, or open egress (RULE-001/014/018). This slice proves
  the reader with staged mock-feed evidence only; it declares no ROAS Pass / Scale Ready (owner-only).

---

*PM_ORCHESTRATOR evidence-collect, `analysis_only`. Every band evidence file, artifact, test/boundary/security report is
indexed and mapped to the 7 exit-gate legs; unresolved slice/owner-level items are listed in §5. No self-certification
(RULE-015): `status=PASS` on M6-P2707 means the **collection** task is complete and unblocked — it does **not** assert the
slice passes. The runner EVIDENCE_GATE and the slice Judge (M6-P2709) decide slice closure.*
