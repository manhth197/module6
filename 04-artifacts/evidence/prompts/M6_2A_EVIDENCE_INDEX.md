# M6.2A — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2A** — ADS Phase 1 Data Foundation |
| Assembled by | **M6-P1007** — `M6_2A_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-07-30 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1009). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`. This index flips nothing and self-certifies nothing. |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. It does **not** assert
> that slice M6.2A has passed its exit gate. Exit-gate items **6 and 7 are NOT yet met** (docs prompt M6-P1008 and
> the slice-gate Judge M6-P1009 have not run — both are the steps that *follow* this one). Entry to the slice was
> opened by a documented **owner override** (`M6-OVERRIDE-M6P1000-STAGED`), **not** by a Judge PASS — the entry-gate
> Judge verdict (M6-P1000) is **BLOCKED** and is unmodified. All of that is carried forward faithfully in
> "Unresolved blockers / carry-forwards" below. The authoritative slice verdict is the Judge's to render at
> M6-P1009, strictly from the evidence files, not from this index.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 78–87) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported status | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1000 | JUDGE | M6_2A_ENTRY_GATE_JUDGE | **SKIPPED** (owner override) | `04-artifacts/evidence/prompts/M6-P1000.json` | **BLOCKED** (fail-closed) | false | `04-artifacts/evidence/judge/M6-P1000_JUDGE_FINAL_SIGN_OFF.json` |
| M6-P1001 | CODER | M6_2A_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1001.json` | PASS | false | `04-artifacts/impl/M6.2A/PLAN.md` |
| M6-P1002 | CODER | M6_2A_CODER_IMPLEMENT | PASS (Round 4) | `04-artifacts/evidence/prompts/M6-P1002.json` | PASS | false | `04-artifacts/impl/M6.2A/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1003 | TESTER | M6_2A_TESTER_BUILD | PASS (Round 4) | `04-artifacts/evidence/prompts/M6-P1003.json` | PASS | false | `04-artifacts/impl/M6.2A/tests/TEST_MANIFEST.md` |
| M6-P1004 | TESTER | M6_2A_TESTER_RUN | PASS (Round 4) | `04-artifacts/evidence/prompts/M6-P1004.json` | PASS | false | `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md` |
| M6-P1005 | BOUNDARY_ADVERSARY | M6_2A_BOUNDARY_ADVERSARY | PASS (Round 4) | `04-artifacts/evidence/prompts/M6-P1005.json` | PASS | false | `04-artifacts/boundary-reports/M6.2A_boundary.md` |
| M6-P1006 | SECURITY_PII | M6_2A_SECURITY_REVIEW | PASS (Round 2) | `04-artifacts/evidence/prompts/M6-P1006.json` | PASS | false | `04-artifacts/security-reports/M6.2A_security.md` |
| **M6-P1007** | PM_ORCHESTRATOR | M6_2A_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1007.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2A_EVIDENCE_INDEX.md` |
| M6-P1008 | ANALYST_ARCHITECT | M6_2A_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2A_RUNBOOK.md` (pending) |
| M6-P1009 | JUDGE | M6_2A_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1009_JUDGE_FINAL_SIGN_OFF.json` (pending) |

The **seven** band evidence JSONs that exist (M6-P1000 … M6-P1006) are schema-valid and declare
`fail_gate_tripped=false`; this prompt's own `M6-P1007.json` is produced at completion (written **last**, after this
index — pack hard-rule 2). M6-P1000's self-report is **BLOCKED** (the entry-gate Judge's honest fail-closed
verdict); the ledger row is **SKIPPED** under the recorded owner override, not a Judge PASS.

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2A/`)
- `04-artifacts/impl/M6.2A/PLAN.md` — minimal staged change set + master traceability matrix + rollback per item (§5–§10).
- `04-artifacts/impl/M6.2A/IMPLEMENTATION_NOTES.md` — Round-1..4 implementation notes; §6 rollback.
- `04-artifacts/impl/M6.2A/README.md`, `pyproject.toml` — greenfield baseline (python 3.12 pin, pytest config).
- Application (measure-only seam): `app/measurement/ingest.py`, `consent/gate.py`, `registry/validator.py`,
  `identity/resolver.py`, `logs/web_event_log_store.py`, `logs/idempotency.py`, `audit.py`, `masking.py`,
  `ports.py`, `models/consumed.py`, `models/web_event_log.py`, `config.py`, `app/__main__.py`.
- Migration (staged, never applied): `04-artifacts/impl/M6.2A/migrations/0001_create_web_event_logs.sql` (up + down-DDL),
  `migrations/README.md`.

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2A/tests/TEST_MANIFEST.md`.
- Smoke: `tests/smoke/test_smk_001_event_not_in_registry.py`, `tests/smoke/test_smk_002_valid_event_missing_consent.py`.
- Units bound to legs: `tests/test_event_registry_validation.py` (L1), `tests/test_consent_fail_closed.py` (L2),
  `tests/test_identity_mapping_audit.py` (L3), `tests/test_web_event_logs_append_only.py` (RULE-007),
  `tests/test_ingest_measure_only.py`.
- Regression suites: `tests/test_round2_regressions.py`, `tests/test_round3_regressions.py`,
  `tests/test_round4_regressions.py` (input type-boundary class).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md` (full staged suite **96 passed / 0 failed**, SMK-001 4/4, SMK-002 7/7, consent matrix 6/6).
- Boundary report: `04-artifacts/boundary-reports/M6.2A_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2A_security.md`.
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1000_JUDGE_FINAL_SIGN_OFF.json` (verdict BLOCKED).

### 2.4 Governing spec / registers indexed
- `00-spec/slices/M6.2A.md` (exit-gate checklist, in/out scope, contract + smoke + entry bindings).
- `00-spec/registers/SMOKE_REGISTER.md` (M6-SMK-001, M6-SMK-002 verbatim scenario/expected).
- `00-spec/registers/CONTRACT_REGISTER.md` (M6-CTR-003/004/005/006 = **DRAFT_LOCKED**, bound to M6.2A).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status | Note |
|---|---|---|---|---|
| M6-CTR-003 | event_registry (consumed) | CONSUMED (Core Event Governance) | **DRAFT_LOCKED** | harmonization M6-P0701; judged PASS at M6-P0715 (SIGNED) |
| M6-CTR-004 | web_event_logs | **M6 (owned)** | **DRAFT_LOCKED** | harmonization M6-P0703 |
| M6-CTR-005 | guest_contacts (consumed) | CONSUMED (Customer identity) | **DRAFT_LOCKED** | harmonization M6-P0702 |
| M6-CTR-006 | guest_marketing_consent_snapshot (consumed) | CONSUMED (Consent) | **DRAFT_LOCKED** | harmonization M6-P0702 |

All four are `DRAFT_LOCKED` (not MISSING); the covering harmonization prompts were judged PASS at M6-P0715 (ledger:
SIGNED). The slice-spec condition "if MISSING, its harmonization prompt must be PASS before entry" is satisfied.
**Caveat (carry-forward B2):** the CONTRACT_REGISTER labels the CTR-003 ownership "Core Event Governance", but
ENTRY-003 records that the *live* `event_registry` is (a) still missing the per-event `attribution_channel` /
`data_sensitivity` / `external_send_policy` fields (M6-CTR-003 fields this slice consumes) and (b) actually
**Platform/P0-06-owned, not Core-owned** — an open ownership gap with registry-owner attestation **PENDING**. The
staged code treats the missing fields fail-closed (missing send-policy ⇒ BLOCKED, missing sensitivity ⇒ treat as PII).

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **PENDING** = the producing prompt has not
run yet · caveats are carry-forwards (see §5), none of which trips an in-scope fail gate (M6-FAIL-002/003).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **Event registry tests PASS** — every event validated; unknown rejected or held with clear audit | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md` (SMK-001 4/4 + `test_event_registry_validation.py` 6/6 within the 96); `04-artifacts/impl/M6.2A/app/measurement/registry/validator.py`; boundary `M6.2A_boundary.md` (FAIL-003 not tripped) | RULE-001/018; guards M6-FAIL-003. The tester (M6-P1004) calls leg **L1 "supported", not "closed"**. Caveat B3-F1: a *throwing* registry adapter currently escapes the seam un-audited — "audit rõ" not proven for that input class (armed-not-fired, routed to CODER before M6.2B). Final L1 closure is the slice-gate Judge's call. |
| 2 | **Consent tests PASS** — fail-closed: no external measurement / audience sync / CRM when consent missing/expired/opt-out | **SUPPORTED (staged)** | `SMOKE_RESULTS.md` (SMK-002 7/7 seam-driven + `test_consent_fail_closed.py` 6/6); `app/measurement/consent/gate.py`; boundary + security reports corroborate | RULE-002; guards M6-FAIL-002. The tester calls leg **L2 "supported", not "closed"**. Caveat B3-F2: a `ConsentSnapshot` subclass can bypass the seam `isinstance` guard, reopening the gate substring fail-open (egress stays bolted; armed-not-fired, routed to CODER). Final L2 closure is the slice-gate Judge's call. |
| 3 | **Identity tests PASS** — guest→customer mapping has audit and is never overwritten without evidence | **SUPPORTED (staged)** | `SMOKE_RESULTS.md` / suite (`test_identity_mapping_audit.py` 7/7 within the 96); `app/measurement/identity/resolver.py`; security report (masking + no-overwrite-without-audit confirmed) | RULE-006. Suite executed 7/7; subjects masked at the audit boundary. Caveat B3-F1 also covers the identity-resolve adapter (throwing adapter escapes un-audited). Final L3 closure is the slice-gate Judge's call. |
| 4 | **Smoke M6-SMK-001 executed** with recorded result + evidence ref | **MET** | `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1004.json` | Scenario/expected recorded verbatim; executed on frozen Round-4 code. |
| 5 | **Smoke M6-SMK-002 executed** with recorded result + evidence ref | **MET** | `04-artifacts/test-reports/M6.2A/SMOKE_RESULTS.md` (7/7, exit 0); `04-artifacts/evidence/prompts/M6-P1004.json` | Parametrized over external_measurement + audience_sync; seam-audited CONSENT_MISSING is the load-bearing proof. |
| 6 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1000.json` … `M6-P1006.json` present (7); `M6-P1007.json` produced at this prompt's completion | **Not yet complete:** M6-P1008 (Docs) and M6-P1009 (Judge) evidence not produced (both TODO). M6-P1000 evidence is present but self-reports BLOCKED (ledger SKIPPED via owner override). |
| 7 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1009_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1009 is TODO. (The existing `M6-P1000_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate, verdict **BLOCKED** — not the slice gate.) |
| 8 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2A/PLAN.md` §5–§10 (per-item Rollback columns + §10 global strategy); `IMPLEMENTATION_NOTES.md` §6; `migrations/0001_create_web_event_logs.sql` (down-DDL); `migrations/README.md` | All changes staged ⇒ non-destructive (delete staged tree to revert); append-only table revert = down-DDL `DROP TABLE`. |

**Summary:** items **4, 5 and 8 are MET**; items **1–3 are SUPPORTED at the staged level** — the bound smoke/unit
suites pass within the 96, but the tester (M6-P1004) deliberately withheld leg-*closure* on L1/L2 (calling them
"supported"), and the F1/F2 audit-integrity / fail-closed residuals remain open, so **final L1/L2/L3 closure is the
slice-gate Judge's call** (not asserted here); items **6 and 7 are PENDING** — closed by the two remaining slice
prompts (M6-P1008 docs, then M6-P1009 slice-gate Judge), the correct state at this evidence-collect step. Coverage:
**every exit-gate checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-001 | ADS-P0-001 | `Event không có trong event_registry` | `Reject/HOLD, audit rõ` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1004.json` |
| M6-SMK-002 | ADS-P0-002 | `Event hợp lệ nhưng thiếu consent` | `Không external measurement, không audience sync` | **PASS 7/7** | `SMOKE_RESULTS.md`, `M6-P1004.json` |

(SMK-003 end-to-end dedup is out of scope for M6.2A — deferred to M6.2B/D; M6.2A proves store-level dedup only.)

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips an in-scope
fail gate (M6-FAIL-002/003) — each was already adjudicated by the responsible upstream prompt and is carried
forward as governance context. They **must** be visible to the slice-gate Judge (M6-P1009) and the owner.

- **B1 — Slice exit gate is not complete (expected at this step).**
  - Item 6 pending: **M6-P1008** (Docs) and **M6-P1009** (Judge) evidence JSONs not yet produced.
  - Item 7 pending: **M6-P1009** slice-gate Judge PASS sign-off does not exist.
  - *Disposition:* normal sequence — these are the prompts that follow M6-P1007.

- **B2 — Entry gate opened by OWNER OVERRIDE, not a Judge PASS.**
  - `M6-P1000` entry-gate Judge verdict = **BLOCKED** (fail-closed); ledger status = **SKIPPED** via
    `M6-OVERRIDE-M6P1000-STAGED` (staged-only; prod BLOCKED/OFF; external-send OFF; **mandatory M6.2G Scale-Gate re-gate**).
  - Underlying entry-evidence gaps are **risk-accepted, not closed**:
    - **M6-ENTRY-001** (P3 Verified-Revenue boundary): NO_RUNTIME_PROOF; FAIL_OPEN_RECALL at
      `SellableGateAdminServiceImpl:805`; **PREPAID_TO_VERIFIED_NO_E2E** (no end-to-end proof of the
      prepaid → ORDER_VERIFIED transition); QuoteSnapshot producer missing; Commerce/M3 owner confirmation **PENDING**.
    - **M6-ENTRY-003** (P6 event identity / `event_registry`): per-event `attribution_channel` +
      `data_sensitivity` + `external_send_policy` **MISSING**; owner not runtime-enforced (runtime create = UNASSIGNED);
      **registry is Platform/P0-06-owned, not Core-owned** (open ownership gap); registry-owner confirmation **PENDING**.
  - *Ref:* `04-artifacts/evidence/prompts/M6-P1000.json`, `04-artifacts/evidence/judge/M6-P1000_JUDGE_FINAL_SIGN_OFF.json`.

- **B3 — Boundary residuals (M6-P1005), armed-not-fired, routed to CODER before M6.2B.**
  - **F1 [MAJOR]:** the seam does not turn *every* callee exception into an audited deny — throwing
    registry / identity / store adapters and a too-narrow `normalize_ts` catch escape with 0 audit (breaks
    SMK-001 "audit rõ" for that input class); consequence is a lost row + lost audit, **not** a grant/send.
  - **F2 [MAJOR]:** the seam `isinstance(ConsentSnapshot)` guard is bypassable by a subclass that skips
    `__post_init__` (reopens the gate substring fail-open); egress stays bolted, so armed-not-fired.
  - **O2 [data-quality, owner-visible]:** a registry-VALID event with a naive / non-tz-aware `event_ts` is
    fail-closed and the **whole measurement row is dropped** (audited `TS_NOT_TZ_AWARE`) — an under-count effect
    that the boundary adversary flagged as an owner-visible DQ decision (distinct from F1(b), where the row escapes
    with *no* audit trace).
  - Plus MINOR-6..9. *Ref:* `04-artifacts/boundary-reports/M6.2A_boundary.md`.

- **B4 — Security/PII residuals (M6-P1006), forward-routed.**
  - **SEC-PII-01 residual (= boundary MINOR-9):** an identifier-shaped `event_code` is stored verbatim in the
    in-memory audit sink — latent only (nothing serialized/exported; staged); tighten before M6.2B / before any durable binding.
  - **SEC-PII-02:** `detail` is deliberately not identity-masked (contract-guarded: reason/enum/pre-masked only).
  - **O1 / M6-OD-012:** `session_id` + `correlation_id` stored raw in the in-memory `web_event_logs`;
    masking-on-export must land before any export / durable binding.
  - *Ref:* `04-artifacts/security-reports/M6.2A_security.md`.

- **B5 — Open owner decisions (forward gates).**
  - **M6-OD-003** (hash policy + permitted external-send fields): **re-scoped by M6-P1006 to NOT-in-scope-for-M6.2A**
    (belongs at M6.2D); remains a hard forward gate before M6.2C/D external send. The fail-closed egress lock is
    present and executed-verified (`permits_external_send()` hard-returns False while OD-003 is OPEN).
  - **M6-OD-012** (masking format on export): OPEN, forward.
  - (**M6-OD-011** slice-entry decision: **DECIDED** 2026-07-23 — GREENFIELD, staged-only, python 3.12.)

- **B6 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`
  are unchanged and unchangeable by this slice. The **mandatory M6.2G Scale-Gate re-gate** stands before any real
  scale or external send.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1009)

1. Start from `00-spec/slices/M6.2A.md` "Exit gate checks" (the 8 items in §4 above).
2. For legs 1–5 + 8, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. Confirm items 6 & 7 status by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1009 sign-off should
   be the Judge's own output).
4. Weigh B2 (owner-override entry with BLOCKED Judge verdict + risk-accepted ENTRY-001/003) and B3/B4 residuals as
   the governance context of any slice verdict; the M6.2G re-gate remains mandatory regardless.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
