# M6.2I — Slice Evidence Index

| Field | Value |
|---|---|
| Slice | **M6.2I** — Phase 2 Golden Hour Funnel (**first Phase-2 slice**; measure-only) |
| Assembled by | **M6-P1807** — `M6_2I_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, analysis_only) |
| Assembled on | 2026-08-28 (UTC) |
| Purpose | Index every band's evidence file / artifact / test report / boundary+security report, mapped to the slice exit-gate checklist, and list unresolved blockers — for the slice-gate Judge (M6-P1809). |
| Governance (immutable) | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, + all M6.2A–H scale/hash/learning flags False, `live_migrations=false`. This index flips nothing and self-certifies nothing; **the funnel only measures — no live-session control, no new table, no send/scale/publish/order-state.** |

> **Altitude note (read first).** This is an **index of collected evidence**, not a verdict. M6.2I is the **first
> Phase-2 slice**, opened only after the full Phase-1 chain (M6.2A–H) was complete and SIGNED. The band is clean —
> entry gate a real Judge PASS (M6-P1800 `SIGNED`), **all seven band prompts self-report PASS**, and **both
> in-scope fail gates held**: M6-FAIL-001 (revenue misuse — the funnel's verified-only revenue is *self-enforcing*)
> and M6-FAIL-010 (phase jump — the funnel is measure-only with no later-phase import). A strong design call: the
> slice adds **no new table/migration/CTR/config flag** — it is a derived read-only projection over the existing
> `ads_measurement_events` (CTR-001) + `ads_attribution_context` (CTR-002) (RULE-018). Its self-enforcing revenue
> choke **closes the M6.2F F-DASH-1 gap**. Exit-gate items **4 and 5 are NOT yet met** (M6-P1808 docs and the
> M6-P1809 slice-gate Judge have not run). The authoritative slice verdict is the Judge's, strictly from the evidence.

---

## 1. Slice prompt band — evidence status

Source: `04-artifacts/state/PROMPT_EXECUTION_LEDGER_LOCKED.csv` (rows 158–167) + each evidence JSON.

| Prompt | Role | Title | Ledger status | Evidence JSON | Self-reported | `fail_gate_tripped` | Primary artifact(s) |
|---|---|---|---|---|---|---|---|
| M6-P1800 | JUDGE | M6_2I_ENTRY_GATE_JUDGE | **SIGNED** | `04-artifacts/evidence/prompts/M6-P1800.json` | PASS | false | `04-artifacts/evidence/judge/M6-P1800_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS) |
| M6-P1801 | CODER | M6_2I_CODER_PLAN | PASS | `04-artifacts/evidence/prompts/M6-P1801.json` | PASS | false | `04-artifacts/impl/M6.2I/PLAN.md` |
| M6-P1802 | CODER | M6_2I_CODER_IMPLEMENT | PASS | `04-artifacts/evidence/prompts/M6-P1802.json` | PASS | false | `04-artifacts/impl/M6.2I/IMPLEMENTATION_NOTES.md` + staged `app/` tree |
| M6-P1803 | TESTER | M6_2I_TESTER_BUILD | PASS | `04-artifacts/evidence/prompts/M6-P1803.json` | PASS | false | `04-artifacts/impl/M6.2I/tests/TEST_MANIFEST.md` |
| M6-P1804 | TESTER | M6_2I_TESTER_RUN | PASS | `04-artifacts/evidence/prompts/M6-P1804.json` | PASS | false | `04-artifacts/test-reports/M6.2I/SMOKE_RESULTS.md` |
| M6-P1805 | BOUNDARY_ADVERSARY | M6_2I_BOUNDARY_ADVERSARY | PASS | `04-artifacts/evidence/prompts/M6-P1805.json` | PASS | false | `04-artifacts/boundary-reports/M6.2I_boundary.md` |
| M6-P1806 | SECURITY_PII | M6_2I_SECURITY_REVIEW | PASS | `04-artifacts/evidence/prompts/M6-P1806.json` | PASS | false | `04-artifacts/security-reports/M6.2I_security.md` |
| **M6-P1807** | PM_ORCHESTRATOR | M6_2I_EVIDENCE_COLLECT | **RUNNING** | `04-artifacts/evidence/prompts/M6-P1807.json` | (this index) | false | `04-artifacts/evidence/prompts/M6_2I_EVIDENCE_INDEX.md` |
| M6-P1808 | ANALYST_ARCHITECT | M6_2I_DOCS | **TODO** | — (not produced) | — | — | `04-artifacts/analysis/slices/M6_2I_RUNBOOK.md` (pending) |
| M6-P1809 | JUDGE | M6_2I_SLICE_GATE_JUDGE | **TODO** | — (not produced) | — | — | `04-artifacts/evidence/judge/M6-P1809_JUDGE_FINAL_SIGN_OFF.json` (pending) |

All seven band evidence JSONs (M6-P1800 … M6-P1806) exist, are schema-valid, self-report **PASS**, and declare
`fail_gate_tripped=false`; the entry gate M6-P1800 is a genuine Judge `SIGNED` verdict PASS (ENTRY-002 re-checked
genuinely clean; FAIL-010 phase-jump not tripped). This prompt's own `M6-P1807.json` is produced at completion
(written **last**, after this index — pack hard-rule 2).

---

## 2. Artifact inventory (existence verified on disk)

### 2.1 Implementation (staged, `04-artifacts/impl/M6.2I/`)
- `PLAN.md` — minimal staged change set + master traceability + per-item rollback.
- `IMPLEMENTATION_NOTES.md` — realized plan + the one plan-delta (dashboard wiring dropped/reverted); §6 rollback.
- Carried-forward M6.2H tree + new **funnel layer** (`app/measurement/funnel/`): `golden_hour.py` (`GoldenHourState`
  PRE/LIVE/POST/CLOSED/UNKNOWN + `observe_state` — a pure measurement projection, no controller; absent/unknown → UNKNOWN
  fail-closed), `flow.py` (the doc §8 Ads→Live→Comment→Messenger→Quote→Order→Verified chain; event codes referenced
  from canon, none invented; `REVENUE_VALID_EVENT=ORDER_VERIFIED`), `models.py` (frozen `GoldenHourFunnelView`/
  `FunnelTrace`; `to_public` masks psid), `funnel.py` (`GoldenHourFunnel` read-only assembler; per-session stage
  counts + doc §14 funnel rates reusing the kpi `_safe_div`; **self-enforcing verified-only revenue**; RULE-021
  `capture_gate_passed` consumed-flag absent⇒False), `retargeting.py` (`RetargetingMeasurement` measure-only, eligible
  only on a recognized signal + valid `ConsentScope.AUDIENCE_SYNC`; never sends).
- **No new migration and no new config flag** (RULE-018 — doc §13 defines no golden-hour/funnel/session table; the
  projection reads the existing migrations 0002 + 0006). The plan's optional dashboard wiring was **reverted to
  M6.2H byte-identical** (it broke a carried TESTER-owned smoke) → funnel ships standalone; wiring is deferred to the
  M6-OD-011 owner integration step.

### 2.2 Tests
- Manifest: `04-artifacts/impl/M6.2I/tests/TEST_MANIFEST.md`.
- Bound smoke: `tests/smoke/test_smk_004_quote_in_golden_hour_funnel_not_revenue.py` (4),
  `tests/smoke/test_smk_013_funnel_live_chain_trace.py` (4).
- Leg-supporting: `tests/test_golden_hour_funnel_chain.py` (3), `test_golden_hour_state_measure_only.py` (4),
  `test_quote_in_funnel_not_revenue.py` (4), `test_live_chain_trace_in_funnel.py` (3),
  `test_retargeting_consent_valid_only.py` (6), `test_order_capture_commerce_gate_rule021.py` (4),
  `test_funnel_measure_only_boundary.py` (3) + carried suites.
- Full staged suite **386 passed / 0 failed** = 351 carried-forward (M6.2A–H) + 35 new M6.2I nodes (27 funnel-leg + 8 bound smoke).

### 2.3 Reports
- Test report: `04-artifacts/test-reports/M6.2I/SMOKE_RESULTS.md` (SMK-004 4/4, SMK-013 4/4; full suite 386).
- Boundary report: `04-artifacts/boundary-reports/M6.2I_boundary.md`.
- Security/PII report: `04-artifacts/security-reports/M6.2I_security.md` (verdict PASS; scan clean over 186 files; no prompt-injection surface).
- Entry-gate Judge sign-off: `04-artifacts/evidence/judge/M6-P1800_JUDGE_FINAL_SIGN_OFF.json` (verdict PASS).

---

## 3. Contract checklist (from the slice spec)

| Contract | Shape | Ownership | Status (canon) | Note |
|---|---|---|---|---|
| M6-CTR-001 | ads_measurement_event | M6 | **DRAFT_LOCKED** | 20 fields, doc §10; the funnel *reads* it (does not re-define). Resolved-for-entry directly (not MISSING). |
| M6-CTR-002 | ads_attribution_context | M6 | **DRAFT_LOCKED** | 19 fields, doc §11; the funnel *reads* it for the live/comment/messenger trace. Resolved-for-entry directly. |

Both are already `DRAFT_LOCKED` (not MISSING) — the M6.2I entry gate resolved them directly; no canon-flip pending.

---

## 4. Exit-gate checklist → evidence map

Legend: **MET** = evidence present and sufficient at the staged level · **SUPPORTED (staged)** = the bound/supporting
suites pass and the boundary adversary executed the check, with open (armed-not-fired) residuals · **PENDING** = the
producing prompt has not run yet. Caveats are carry-forwards (see §5); none trips an in-scope fail gate (M6-FAIL-001/010 — both held).

| # | Exit-gate check (slice spec) | Verdict | Evidence refs | Notes / caveats |
|---|---|---|---|---|
| 1 | **Golden Hour conversion smoke pass** — the Ads→Live→Comment→Messenger→Quote→Order→Verified chain measured end-to-end across GH states PRE→LIVE→POST→CLOSED, with the live/comment/messenger trace smoke passing | **SUPPORTED (staged)** | `04-artifacts/test-reports/M6.2I/SMOKE_RESULTS.md` (SMK-013 + `test_golden_hour_funnel_chain.py` 3 + `test_golden_hour_state_measure_only.py` 4 within the 386); `app/measurement/funnel/funnel.py`, `golden_hour.py`, `flow.py`; boundary `M6.2I_boundary.md` (measure-only; FAIL-001/010 not tripped) | RULE-003/013/016/021. Tester marks leg **L1 "met"**. Self-enforcing verified-only revenue **closes the M6.2F F-DASH-1 gap**. Caveats B3-F-FUNNEL-1/2/3 (in-process type-confusion / hostile-Mapping / TOCTOU) + **B4-F-SEC-2I-1 (cross-person trace stitch — attribution-integrity/PII)**. Final L1 closure is the slice-gate Judge's call. |
| 2 | **Smoke M6-SMK-004 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1804.json` | A quote/order-created is a funnel stage but 0 verified revenue; a quote force-carrying revenue still reports 0 (self-enforcing choke). |
| 3 | **Smoke M6-SMK-013 executed** with recorded result + evidence ref | **MET** | `SMOKE_RESULTS.md` (4/4, exit 0); `04-artifacts/evidence/prompts/M6-P1804.json` | Funnel threads live_session_id + comment_id + messenger_thread_id; psid masked on export. |
| 4 | **All slice prompts have evidence JSON** (schema-valid, no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | `04-artifacts/evidence/prompts/M6-P1800.json` … `M6-P1806.json` present (7); `M6-P1807.json` produced at this prompt's completion | **Not yet complete:** M6-P1808 (Docs) and M6-P1809 (Judge) evidence not produced (both TODO). |
| 5 | **Slice-gate Judge sign-off exists with verdict PASS** | **PENDING (not met)** | — | `04-artifacts/evidence/judge/M6-P1809_JUDGE_FINAL_SIGN_OFF.json` does **not** exist; M6-P1809 is TODO. (The existing `M6-P1800_JUDGE_FINAL_SIGN_OFF.json` is the *entry* gate.) |
| 6 | **Rollback steps documented** for every change this slice made | **MET** | `04-artifacts/impl/M6.2I/PLAN.md` (per-item Rollback) + `IMPLEMENTATION_NOTES.md` §6 (new `funnel/` files → delete; **no patched carried file** — the dashboard patch was reverted; **no migration to unwind** — none added) | All changes staged ⇒ non-destructive. |

**Summary:** items **2, 3 and 6 are MET**; item **1 is SUPPORTED at the staged level** (the tester marks leg L1
"met" and both in-scope fail gates hold, but the F-FUNNEL-1/2/3 + F-SEC-2I-1 residuals remain — armed-not-fired —
so final closure is the slice-gate Judge's call); items **4 and 5 are PENDING** (M6-P1808 docs, then M6-P1809
slice-gate Judge). Coverage: **every exit-gate checklist item is indexed** (acceptance check 1).

### 4.1 Smoke register bindings

| Smoke ID | Doc ID | Scenario (verbatim) | Expected (verbatim) | Result | Evidence |
|---|---|---|---|---|---|
| M6-SMK-004 | ADS-P0-004 | `Quote được tạo nhưng chưa order` | `Không revenue, không ROAS` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1804.json` |
| M6-SMK-013 | ADS-P0-013 | `Live/Comment/Messenger chain` | `Trace được live_session_id, comment_id, messenger_thread_id` | **PASS 4/4** | `SMOKE_RESULTS.md`, `M6-P1804.json` |

---

## 5. Unresolved blockers / carry-forwards (acceptance check 2)

None of the following is an open blocker of the **evidence-collection** task itself, and none trips an in-scope
fail gate (M6-FAIL-001/010 — both held). Each was already adjudicated by the responsible upstream prompt and is
carried forward for the slice-gate Judge (M6-P1809) and the owner. **B4-F-SEC-2I-1 is the finding most worth the
Judge's attention.**

- **B1 — Slice exit gate is not complete (expected at this step).** Item 4 pending M6-P1808/M6-P1809 evidence;
  item 5 pending the M6-P1809 slice-gate Judge PASS sign-off.

- **B2 — Positive posture (for context).** The funnel is a **derived read-only projection** — no new
  table/migration/CTR/config flag (RULE-018), Golden Hour state measure-only (RULE-013; no session controller —
  Gateway/Live operates the session), verified-only revenue **self-enforcing** (re-checks the row's own
  `event_code==ORDER_VERIFIED`, which **closes the M6.2F F-DASH-1 gap**), RULE-021 order-capture recorded-not-owned
  (Commerce-owned gate; `capture_gate_passed` fail-closed to False), retargeting consent-valid-only under the
  existing AUDIENCE_SYNC scope. **FAIL-010 (phase jump) not tripped** — measure-only, no scale/learning/outbox/Phase-3
  transitive import, and Phase 1 A–H is complete/SIGNED before this first Phase-2 slice.

- **B3 — Boundary residuals (M6-P1805), armed-not-fired, none trips M6-FAIL-001/010; routed to CODER.**
  - **F-FUNNEL-1 [primary]:** the revenue-choke `event_code == REVENUE_VALID_EVENT` equality dispatches to the left
    operand's `__eq__`, so a `str`-subclass with an override-True `__eq__` (plus an `object.__setattr__` bypass of the
    store guard) could count a quote-content row as verified revenue. **Not channel-reachable** (both require arbitrary
    in-process code execution; ingest yields plain JSON strings, RULE-001) — a defense-in-depth *inconsistency* vs the
    consent-scope type-hardening (the M6.2B/D MAJOR-7 F2 fix). Fix: compare via `type(x) is str AND == …` (and the
    same on `stage_for`/`_count_code`).
  - **F-FUNNEL-2:** the funnel reads each event's `attribution_context` **live** (unsnapshotted), so a hostile
    `Mapping.get` could execute attacker code inside `assemble()`. In-process only. Fix: `ctx = dict(ctx)` before reading.
  - **F-FUNNEL-3:** the same unsnapshotted `ctx` makes the projection non-deterministic (measurement drift /
    non-repeatable evidence). Same `dict(ctx)` fix.
  - N-1 (non-finite verified revenue not guarded — DQ robustness; fix `math.isfinite(v) and v>=0`) and N-2
    (frozen-view / str-subclass forge — in-process code exec only, not channel-reachable).
  - *Ref:* `04-artifacts/boundary-reports/M6.2I_boundary.md`.

- **B4 — Security residuals (M6-P1806), forward-routed.**
  - **F-SEC-2I-1 [PRIMARY; = boundary F-FUNNEL-4]:** the funnel `_trace` folds `comment_id`/`messenger_thread_id`/
    `psid` each **independently** (`x = x or ctx.get(x)`) across **all** events grouped under one `live_session_id` —
    a *session-level shared key* (one live broadcast, many people) — with **no subject binding**. So a multi-subject
    session stitches person A's `comment_id` next to person B's `messenger_thread_id` (+ person C's psid) into **one
    exported `FunnelTrace`, asserting a false association between distinct identifiable people** (attribution-integrity
    + PII; masking psid does not cure it, since `comment_id`/`messenger_thread_id` are exported raw). Armed-not-fired
    for a hard breach only because the canonical tests use one-subject sessions. Fix: bind the trace to a single
    subject (`customer_or_guest_key`) or record per-subject traces.
  - **F-SEC-2I-2 [→ M6-OD-012]:** `FunnelTrace.to_public` masks **only** `psid`; `comment_id`/`messenger_thread_id`/
    `live_session_id` are exported **raw** — but a `messenger_thread_id` is a per-person Messenger conversation handle
    (same identity-boundary family as psid). Masking-scope inconsistency; ratify under M6-OD-012 (at minimum bring
    `messenger_thread_id` to psid parity). Parallels the M6.2E O-2b observation; interacts with F-SEC-2I-1.
  - **ACCESS (forward, M6-OD-011):** the funnel is **not wired to any endpoint** today (the dashboard wiring was
    reverted), so there is no access-control regression. When it is eventually surfaced through
    `GET /api/admin/ads/dashboard`, the M6-OD-011 binding must authenticate/authorize the admin caller (doc §22 line
    429; never trust a body-supplied identity) **and** apply the trace-id masking (F-SEC-2I-1/2). Mirrors the ACCESS-1
    forward requirement from M6.2G/M6.2H.
  - **Positive:** PII/secret scan clean over 186 files; channel-derived values stay **DATA** (no prompt-injection
    surface); consent enforcement fail-closed + PII-safe (subject masked at the audit boundary).
  - *Ref:* `04-artifacts/security-reports/M6.2I_security.md`.

- **B5 — Contract housekeeping.** CTR-001 and CTR-002 are both `DRAFT_LOCKED` (the funnel reads them, does not
  re-define) — resolved-for-entry directly; no canon-flip pending for this slice.

- **B6 — Open owner decisions + inherited forward gates.** **M6-OD-009** (GOLDEN_HOUR_START/REMINDER event set —
  optional / disabled-by-default; Gateway/Live owns emission config; absent → state UNKNOWN fail-closed) and
  **M6-OD-012** (masking scope — now with F-SEC-2I-2) are the decisions touching M6.2I. The full **M6.2G + M6.2H
  before-real-scale/send/auto-publish forward-gate chain** remains in force: the four attestation true-ups;
  ENTRY-001/003/004 real-scale/M5 conditions; M6-OD-002/003/004/005; the M6.2G F-SCALE-* + M6.2H F-LEARN-* residuals
  + the OD-006/OD-007 learning gates; and the ACCESS-1/authN + store/queue-laundering fixes at M6-OD-011.

- **B7 — Immutable governance posture.** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  and all M6.2A–H scale/hash/learning flags remain **False**; `live_migrations=false`. `M6-P1000` + `M6-P1309`
  verdicts remain **BLOCKED (not converted)**. FAIL-001/010 not tripped; the funnel measures only — nothing is sent,
  scaled, published, or live-operated; the mandatory M6.2G Scale-Gate re-gate stands before any real scale/publish/send.

---

## 6. Reader's guide for the slice-gate Judge (M6-P1809)

1. Start from `00-spec/slices/M6.2I.md` "Exit gate checks" (the 6 items in §4 above).
2. For legs 1–3 + 6, read the reports/evidence in the §4 "Evidence refs" cells directly (do not rely on this index).
3. Confirm the **measure-only** posture (no new table/migration/CTR/flag; no live-session control) and that the
   verified-only revenue choke is **self-enforcing** (closing the M6.2F F-DASH-1 gap).
4. Confirm items 4 & 5 by re-reading the ledger and `04-artifacts/evidence/judge/` (M6-P1809 sign-off is the Judge's own output).
5. Weigh **F-SEC-2I-1** (cross-person trace stitch) and F-SEC-2I-2 (trace-id masking scope) as the load-bearing
   attribution-integrity/PII items to close before the funnel is bound to any admin export at M6-OD-011; the
   F-FUNNEL-1/2/3 items are in-process-only defense-in-depth; and the inherited B6 forward-gate chain + the standing
   BLOCKED `M6-P1000`/`M6-P1309` verdicts remain in force.

*This index is descriptive. It advances no gate and self-certifies nothing; the runner EVIDENCE_GATE and the
slice-gate Judge decide closure.*
