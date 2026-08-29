# M6.2J Evidence Index — Phase 3 CRM / Diamond / Lifecycle growth machine

| Field | Value |
|---|---|
| Prompt | **M6-P1907** — `M6_2J_EVIDENCE_COLLECT` (PM_ORCHESTRATOR, `analysis_only`) |
| Slice | **M6.2J** — measure the doc §9 Phase-3 growth machine: CRM repeat/reorder, dormant/reactivation, Diamond referral + value-optimization signals; the Data Mart stays a support view |
| Depends on | M6.2I (entry judge M6-P1900 depends on the M6.2I slice judge M6-P1809 SIGNED) |
| Purpose | Assemble every band evidence file / artifact / test / boundary / security report, map each to the slice exit-gate checklist, and list unresolved blockers — a reader's map for the slice-gate Judge (**M6-P1909**) |
| Collection verdict | **complete** — all 7 band prompts (M6-P1900…1906) PASS with `fail_gate_tripped=false`; the two downstream prompts (docs M6-P1908, judge M6-P1909) are the only PENDING exit items |
| Governance | `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — immutable, untouched. `M6-P1000` + `M6-P1309` verdicts remain **BLOCKED** (not converted). This prompt writes only this index + its evidence JSON; it certifies nothing (RULE-015 — the runner EVIDENCE_GATE and the Judge decide). |

> **This is a collection artifact, not a verdict.** Its own `status=PASS` / `open_blockers=[]` means the assembly task
> is complete and unblocked — it does **not** assert the slice passes. Slice-level unresolved items live in **§5**;
> all are armed-not-fired residuals that no band marked as tripping an in-scope fail gate.

---

## 1. Band evidence (the M6.2J prompt chain — 7 of 10 prompts run)

| Prompt | Role | Evidence | Ledger | fail_gate | open_blockers | One-line result |
|---|---|---|---|---|---|---|
| **M6-P1900** | JUDGE (entry) | [M6-P1900.json](M6-P1900.json) | **SIGNED** | false | 0 | Entry gate PASS — opens M6.2J STAGED; 4 entry checks satisfied (prev gate M6-P1809 SIGNED; target LOCKED + OD-011 DECIDED; CTR-002 DRAFT_LOCKED; no entry evidence required); no owner decision names M6.2J |
| **M6-P1901** | CODER (plan) | [M6-P1901.json](M6-P1901.json) | PASS | false | 0 | Plan: a derived read-only **standalone** growth projection — **no new table/migration/CTR/flag** (RULE-018); adversarial design red-team, 2 minor reuse findings fixed |
| **M6-P1902** | CODER (implement) | [M6-P1902.json](M6-P1902.json) | PASS | false | 0 | Built `growth/` package; **414 passed** (386 carried M6.2A–I + 28 growth-leg), rc 0; no carried file patched; self-review 2 robustness fixes (+1 regression) |
| **M6-P1903** | TESTER (build) | [M6-P1903.json](M6-P1903.json) | PASS | false | 0 | Authored official SMK-008/010/014 (nodes 4/3/4), scenario verbatim; collect-only **425** (414 + 11), static verification all-CLEAN; NOT executed |
| **M6-P1904** | TESTER (run) | [M6-P1904.json](M6-P1904.json) | PASS | false | 0 | Executed: bound smokes **11 passed** (SMK-008 4/4, SMK-010 3/3, SMK-014 4/4); full staged suite **425 passed / 0 failed**, rc 0 |
| **M6-P1905** | BOUNDARY_ADVERSARY | [M6-P1905.json](M6-P1905.json) | PASS | false | 0 | 30 executed attacks (DEFENDED 23 / OPEN-non-gate 6 / note 1); **0** of FAIL-002/004/005 tripped; residuals F-GROWTH-1…5 + N-1 (all armed-not-fired) |
| **M6-P1906** | SECURITY_PII | [M6-P1906.json](M6-P1906.json) | PASS | false | 0 | Scan **204 files** — 0 raw PII, 0 secrets (3 `sk-` = carried `risk-` false positives); consent fail-closed; 4 findings F-SEC-2J-1…4 + ACCESS forward |
| M6-P1907 | PM_ORCHESTRATOR | *this collection* | RUNNING | false | 0 | This index + evidence JSON |
| M6-P1908 | ANALYST_ARCHITECT (docs) | — | **TODO** | — | — | Runbook — not yet run (exit item 6) |
| M6-P1909 | JUDGE (slice gate) | — | **TODO** | — | — | Slice-gate sign-off — not yet run (exit item 7) |

**All 7 completed band prompts are PASS with `open_blockers=[]`, `fail_gate_tripped=false`, and no `findings`/`test_results`
integrity keys asserting a tripped gate.** Ledger rows 168–174 confirm each; the entry judge (row 168) is **SIGNED**.

## 2. Artifact inventory (every file the band produced)

**Staged implementation — `04-artifacts/impl/M6.2J/`** (carried the M6.2I tree byte-identical, then added the growth layer):
- `PLAN.md` (M6-P1901) · `IMPLEMENTATION_NOTES.md` (M6-P1902)
- **`app/measurement/growth/`** — the new Phase-3 package: `signals.py` (doc §9 5-group `GrowthGroup` + verbatim valid-signal sets + doc §10 CRM/Diamond event-code constants), `reads.py` (shared read helpers, reuses `_safe_div`), `models.py` (frozen `GrowthKpi`/`GrowthReport`, fail-closed, data-only `to_public`), `crm.py` (`CrmReorderMeasurement` — gated verified-only CRM revenue), `diamond.py` (`DiamondReferralMeasurement` — referral attribution + verified/commission-ready revenue, buyer masked, **no** commission method), `reactivation.py` (`ReactivationMeasurement` — consent+eligibility gated, measure-only), `growth.py` (`GrowthReportBuilder` — the 5-group KPI assembler), `__init__.py`
- **7 growth-leg tests** + `tests/conftest.py` fixtures; **3 official smoke files** under `tests/smoke/` (`test_smk_008_crm_optout_no_sync.py`, `test_smk_010_growth_data_mart_support_view_only.py`, `test_smk_014_diamond_referral_no_commission.py`); `tests/TEST_MANIFEST.md`

**Test report — `04-artifacts/test-reports/M6.2J/`:** [`SMOKE_RESULTS.md`](../../test-reports/M6.2J/SMOKE_RESULTS.md) (M6-P1904 — per-smoke PASS tables, exact commands, exit-gate legs L1–L5)

**Boundary — `04-artifacts/boundary-reports/`:** [`M6.2J_boundary.md`](../../boundary-reports/M6.2J_boundary.md) (M6-P1905); harness `04-boundary/work/attacks/m6_2j_attacks.py`

**Security — `04-artifacts/security-reports/`:** [`M6.2J_security.md`](../../security-reports/M6.2J_security.md) (M6-P1906); scanner `06-security/work/pii_scan_2j.py`

**Entry-judge sign-off — `04-artifacts/evidence/judge/`:** `M6-P1900_JUDGE_FINAL_SIGN_OFF.json` (PASS)

**Test-count reconciliation (count discipline):** **425** full staged suite = **386** carried (M6.2A–I) **+ 28** growth-leg (coder M6-P1902) **+ 11** official smoke nodes (tester M6-P1903/1904, = 4+3+4). Coder baseline before any patch was 386 (byte-parity with the M6.2I final tree); coder final 414; tester added the 11 official smokes → 425. All green, 0 failed / 0 skipped / 0 error, rc 0.

## 3. Contract checklist (CONTRACT_REGISTER)

| Contract | Status | This slice | Resolution |
|---|---|---|---|
| **M6-CTR-002** `ads_attribution_context` | **DRAFT_LOCKED** | consumed | Not MISSING (the slice spec's condition "if MISSING, its harmonization prompt must be PASS before entry" does not fire). Owned/locked at **M6.2E** (SPEC §10.2, 19 fields, doc §11); M6.2J only reads `entry_channel`/`referral_link_id`/`diamond_id` as data. Entry judge M6-P1900 confirmed this at the gate. → **satisfied for M6.2J.** |

No new contract is introduced by M6.2J (measure-only, no new table — RULE-018).

## 4. Exit-gate checklist → evidence map (all 8 legs of `slices/M6.2J.md`)

| # | Exit-gate item | Status | Evidence |
|---|---|---|---|
| 1 | **CRM revenue verified** — counts only from CRM eligibility + suppression + ORDER_VERIFIED; clicks/chats never revenue | **SUPPORTED (staged)** | SMK-008 PASS 4/4 + `test_crm_reorder_revenue_verified_only.py` green: verified-only, consent+eligibility+suppression gated (strict `is True`), opt-out/expired/missing/wrong-scope excluded, `CRM_REORDER_SENT`/click/chat never revenue. Residuals (armed-not-fired) **B1** (subject-bind) + **B2** (ORDER_VERIFIED choke not adopted in `verified_rows`) touch this leg's integrity before real send. [SMOKE_RESULTS L1/L3](../../test-reports/M6.2J/SMOKE_RESULTS.md) |
| 2 | **Diamond revenue verified** — referral orders carry referral attribution (referral_link_id, buyer identity, ORDER_VERIFIED); commission **measured-not-computed** (Finance owns) | **SUPPORTED (staged)** | SMK-014 PASS 4/4 + `test_diamond_referral_no_commission.py` green: referral attribution recorded (`referral_link_id`, `order_code`), `diamond_revenue` + `commission_ready_revenue` measured, **no commission amount/rate/payout method** (RULE-019), buyer identity masked on export. Residuals **B2** (same `verified_rows` choke feeds the Finance-facing figure) + **B3** (raw `buyer_ref` attribute). [SMOKE_RESULTS L2/L5](../../test-reports/M6.2J/SMOKE_RESULTS.md) |
| 3 | Smoke **M6-SMK-008** executed with recorded result + evidence ref | **MET** | PASS 4/4 (CRM opt-out → no sync; control counts 250000 non-vacuous). [SMOKE_RESULTS](../../test-reports/M6.2J/SMOKE_RESULTS.md) · [M6-P1904.json](M6-P1904.json) |
| 4 | Smoke **M6-SMK-010** executed with recorded result + evidence ref | **MET** | PASS 3/3 (Data Mart + growth builder expose no trigger; report data-only; build mutates nothing — RULE-012/FAIL-005). Re-bound in M6.2J (was M6.2F); growth leg coexists with the carried dashboard smoke. |
| 5 | Smoke **M6-SMK-014** executed with recorded result + evidence ref | **MET** | PASS 4/4 (verified referral records attribution + measures revenue; no commission method; commission-ready fail-closed 0 without eligibility; buyer masked). |
| 6 | **All slice prompts** have schema-valid evidence (no raw secret/PII, `fail_gate_tripped=false`) | **PENDING** | M6-P1900…1906 present + PASS + clean; M6-P1907 (this) completing; **M6-P1908 (docs) TODO, M6-P1909 (judge) TODO** — evidence for the last two does not exist yet. Closes when both run. |
| 7 | **Slice-gate judge sign-off** exists with verdict PASS | **PENDING** | **M6-P1909 TODO** (ledger row 177). The slice-gate Judge reads this index. |
| 8 | **Rollback** documented for every change this slice made | **MET** | [IMPLEMENTATION_NOTES §6](../../impl/M6.2J/IMPLEMENTATION_NOTES.md): staged-only → delete the M6.2J tree (M6.2I untouched); new `growth/` files → delete; **no carried file patched** (nothing to revert); **no migration** to unwind. Boundary §7 + Security §11 both record "rollback: none required" for their analysis-only writes. |

**Summary:** MET = items 3, 4, 5, 8 · SUPPORTED (staged) = items 1, 2 · PENDING = items 6, 7 (the two unrun downstream prompts). No exit item is FAILED or BLOCKED.

## 5. Unresolved blockers & carry-forwards

All residuals below are **armed-not-fired**: every band self-reported `fail_gate_tripped=false`, and both the boundary
adversary (30 executed attacks, 0 in-scope breaches) and the security review (204-file scan, 0 raw PII/secrets) confirmed
none is channel-reachable. They are routed to CODER / owner and matter **before any real send/scale/surface**, not to this
measure-only staged slice. This collection prompt's own `open_blockers` is therefore **empty**.

**Slice-owned residuals (M6.2J):**

- **B1 — F-SEC-2J-1 / F-GROWTH-1 (primary; CODER).** *Borrowed consent — the CRM gate does not bind consent to the row's buyer.* `CrmReorderMeasurement._crm_gate_passes` evaluates the consent snapshot fetched by `order_code` but never asserts `snapshot.subject_ref` equals the verified row's buyer (`customer_id`/`guest_id`), so a **different** subject's VALID CRM consent keyed to the order authorizes the buyer's §9 CRM Revenue KPI — consent validated but not bound to the data subject. Not a live FAIL-002 trip: `consent_by_order` is a **consumed** Consent/CRM-owned map, not channel-injectable; fires only on an upstream mis-key or an in-process adversarial `CrmConsumed`. It still matters because the codebase **already enforces this exact bind** at the M6.2E conversion seam (`safe_subject_ref(snap)==customer_or_guest_key`, the F-D fix) and on the Diamond path here — the CRM gate just omits it (known-pattern-not-applied). **Fix:** require `snapshot.subject_ref == the row's customer_id/guest_id` before counting; consider the same explicit bind on reactivation.

- **B2 — F-GROWTH-3 (CODER; boundary + security cross-ref).** *`verified_rows` choke keys off revenue presence, not `ORDER_VERIFIED`.* `reads.verified_rows` filters on `revenue_value is not None` (the M6.2F-style choke), **not** `event_code == 'ORDER_VERIFIED'` (the M6.2I self-enforcing choke). Combined with the materializer deriving `verified` from `conversion.event_code`, a mispaired (ORDER_VERIFIED conversion, QUOTE_SENT event) call stamps revenue onto a quote-content row that surfaces as CRM/Diamond **and** the Finance-facing commission-ready figure. Not channel-reachable (the materializer is constructed only in tests); a **RULE-003 cross-slice consistency regression vs M6.2I** that bears directly on the "+ ORDER_VERIFIED" clause of exit items 1 & 2. **Fix:** AND `event_code == 'ORDER_VERIFIED'` with revenue presence in `verified_rows` (adopt the M6.2I lesson).

- **B3 — F-SEC-2J-2 / N-1 (CODER + owner, M6-OD-012).** *Raw `buyer_ref` on the public dataclass attribute.* `ReferralAttribution.buyer_ref` holds the raw `customer_id`/`guest_id`; masking is applied only in `to_public()`, and `referral_attributions()` returns the raw-bearing objects, so a future consumer serializing a `ReferralAttribution` directly (evidence/log/per-referral export) leaks a raw first-party id. Not exposed by the shipped aggregate report (latent), but `buyer_ref` is a **direct customer/guest id** (higher sensitivity than a platform psid), so opt-in masking is the weaker posture. **Fix/decision:** make masking non-optional at the identity boundary (store masked, or gate raw access) and ratify the export masking scope under **M6-OD-012** (same class as M6.2I F-SEC-2I-2; the carried short-id / M6.2E-context masking items also route here).

- **B4 — F-SEC-2J-3 / F-GROWTH-2 (CODER + owner).** *Ungated `crm_revenue` twin.* Two `crm_revenue` methods exist — the gated growth one (used by the §9 KPI, `=0` without consent, correct) and the consent-blind `DataMart.crm_revenue` (a carried M6.2F channel-breakdown aggregate, `=800000`) reachable via `builder._mart`; only naming keeps the ungated number out of the §9 figure. The shipped report is correct. **Fix:** rename/mark the ungated aggregate (e.g. `crm_channel_revenue`) or gate it.

- **B5 — F-SEC-2J-4 / F-GROWTH-4 (CODER).** *Approval-rate measurement integrity.* The Learning-Engine "Candidate approval rate" KPI counts `review_state.value == 'APPROVED'` only, never `is_publish_authorized` or the audited `OwnerReviewDecision`, so a candidate marked APPROVED at construction (no decision, safe-range UNKNOWN) inflates the rate. A measurement-integrity gap only — it publishes nothing (the M6.2H `is_publish_authorized` still gates the real publish). **Fix:** count only candidates with a bound audited decision.

- **B6 — F-GROWTH-5 (CODER).** *Builder duck-types its collaborators.* `GrowthReportBuilder.build()` invokes injected `queue.all()`/`store.all()`/mart reads with no `isinstance`/Protocol guard, so a mis-wired side-effecting collaborator would run during `build()`. Needs control of the composition root (the shipped `ReviewQueue`/`MeasurementEventStore` `.all()` are pure reads). **Fix:** an `isinstance`/Protocol assertion.

- **B7 — ACCESS forward requirement (owner integration, M6-OD-011).** When the growth report is surfaced through the admin dashboard endpoint, the binding step must (a) **authenticate/authorize an admin caller** per doc §22 line 429 — the carried `handle_dashboard_request` does not itself authenticate (the HTTP/auth mapping is deferred to M6-OD-011), so caller identity must be enforced at that seam, never trusted from the request body; and (b) apply the `buyer_ref` masking discipline (B3) at that export boundary. Mirrors the ACCESS-1 forward requirement raised at M6.2G/H/I — a standing hard forward gate.

**Standing cross-slice governance (not this slice's task; carried forward):**

- **`M6-P1000` + `M6-P1309` verdicts remain BLOCKED** (not converted) — the global gateway + hash-policy blockers stand.
- **Hard forward gates before any real scale / send / auto-publish / surface:** the M6.2G Scale-Gate (mandatory re-gate), the M6.2H learning-publish conditions, and the M6.2I funnel single-subject trace-bind (F-FUNNEL-4) all remain in force. `SCALE_MODEL_RATIFIED` / `SCALE_EXECUTION_ENABLED` / `LEARNING_AUTOPUBLISH_ENABLED` / `HASH_POLICY_RATIFIED` stay `False`.
- **Open owner decision this slice's fixes depend on:** **M6-OD-012** (export masking scope — B3). **M6-OD-003** (external-send hash policy) is N/A to this measure-only slice (builds no external payload; `HASH_POLICY_RATIFIED=False` stays correctly fail-closed).
- **Governance chain — resolved this period (worth the Judge's note):** the standing `M6-DEFER-FBC-M6.2D.json` — the cross-slice consent-binding record flagged ABSENT in the M6.2D–M6.2I indexes — is now **FILED** (`04-artifacts/evidence/decisions/`, owner-confirmed 2026-08-07). It records the consent fail-open class (F-A…F-F: entry-gate/audience/CRM bind, measurement borrowed-consent, `platform_event_id` injective escape, `safe_subject_ref` type-safety) as **CLOSED** (code-verified + adversary-confirmed) and wires the binding as a M6-P1600 Scale-Gate RequiredInput. One residual canon step remains — adding the file path to M6-P1600 `inputs_expected` in `00-spec/` is an operator/generator edit (advisor cannot write `00-spec`); the file notes the M6-P1600 judge already globs the decisions dir, so the on-disk filing is what the gate checks. (`M6-DEFER-F1F2-M6.2B.json` and `M6-DEFER-OD003-M6.2D.json` are likewise on disk.)

## 6. Reader's guide for the slice-gate Judge (M6-P1909)

1. **Read order:** this index → the 7 band JSONs (§1) → the two review reports (`M6.2J_boundary.md`, `M6.2J_security.md`) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback). The exit-gate map is **§4**; the residuals are **§5**.
2. **What is proven (executed):** the Phase-3 growth machine is a **derived, read-only, standalone projection** — no new table/migration/CTR/config flag (RULE-018), no carried file patched. CRM revenue is verified-only + consent/eligibility/suppression gated (SMK-008); Diamond commission is **measured-not-computed** (SMK-014, RULE-019); the Data Mart stays a support view with no trigger (SMK-010, RULE-012/FAIL-005). Full staged suite **425 passed / 0 failed**, bound smokes **11 passed**. Boundary: **0** of FAIL-002/004/005 tripped across 30 executed attacks. Security: **0** raw PII / secrets across 204 files, consent fail-closed on both gated paths, `member_key`/`buyer_ref` never reach the aggregate report, **no new access surface** (the growth package is wired to no endpoint).
3. **What is NOT yet closed:** exit items **6 & 7** are PENDING purely because the docs prompt (M6-P1908) and this judge (M6-P1909) have not run — not because of any defect. Items 1 & 2 are SUPPORTED (staged), carrying the B1/B2/B3 integrity residuals to harden before any real send.
4. **The one finding to weigh hardest:** **B1 (borrowed consent, F-SEC-2J-1)** — a consent checkpoint that validates consent by `order_code` without binding it to the data subject, while the identical bind is already enforced two seams over (M6.2E F-D) and on the sibling Diamond path. Armed-not-fired today (consumed map, not channel-reachable), but it is the sharpest consent finding and the pattern to require before the report is ever surfaced. **B2** (the `ORDER_VERIFIED` choke regression) is the second, because it bears on the literal "+ ORDER_VERIFIED" wording of exit items 1 & 2 and feeds a Finance-facing figure.
5. **Boundary integrity of this collection:** this prompt is `analysis_only` — it read the band evidence and wrote only this index + its evidence JSON. It did not touch `04-artifacts/state/`, did not mark any ledger row, did not modify any file it indexed, and computed no verdict. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` — untouched.
