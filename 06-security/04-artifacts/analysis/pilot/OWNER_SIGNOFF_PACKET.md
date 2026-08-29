# M6 — Owner Sign-Off Packet (PR/PILOT)

> ## ⚠ What this packet is — and the one thing it cannot do (read first)
> This packet **assembles the evidence** for the owner to review the Ginsengfood Module 6 build (Ads Measurement /
> Attribution / ROAS / Scale Gate / Growth). **It does NOT declare ROAS Pass or Scale Ready — those are owner
> declarations this pack cannot make** (doc §23). Nothing in this document flips a flag or authorizes anything.
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all scale/hash/learning flags `False`,
> `live_migrations=false` — immutable, untouched, and they stay OFF through PR/PILOT. `M6-P1000` (M6.2A entry) and
> `M6-P1309` (M6.2D exit) judge verdicts remain **BLOCKED** (not converted). The build sequence M6.2A…M6.2K is closed
> **STAGED**; the full PR/PILOT validation band (E2E chain review + smoke validation + boundary full pass + security
> full pass) is **PASS** — this proves the measurement capability is **exercisable, honest, and ready for owner
> review**, not that anything is cleared to go live.
>
> **A green matrix is not a readiness verdict.** The owner's job at PR/PILOT is to weigh §5 (OPEN decisions), §6
> (conflicts), and §7 (the honest gap/blocker list) and then — and only then, owner-side — decide ROAS Pass / Scale
> Ready. §8 is that agenda.

| Field | Value |
|---|---|
| Prompt | **M6-P3004** — `OWNER_SIGNOFF_PACKET` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE, phase PR_PILOT) |
| Entry gate | **M6-P3004=RUNNING** (order 190); dependency **M6-P3003=PASS**; the PR/PILOT band M6-P3000…3003 all PASS |
| Assembles | the 10 doc §22 evidence categories · all OPEN decisions + recommendations · the Conflict Matrix · slice-gate results · the explicit owner-only statement |
| Governance | `BLOCKED / OFF / OFF`, all flags `False` — immutable; this packet writes no enabling value anywhere |
| Sources | `M6_2K_EVIDENCE_INDEX.md`, `E2E_CHAIN_REVIEW.md`, `M6-P3001/3002/3003.json`, `DECISION_REGISTER.md`, `CONFLICT_MATRIX.md`, `FAIL_GATE_REGISTER.md`, the ledger judge rows |

---

## 1. The explicit statement (the task's centerpiece)

**ROAS Pass and Scale Ready are owner declarations. This pack cannot and does not make them.** (doc §23; M6-RULE-015 —
executors write evidence, never self-certify.) The assembled evidence package's readiness enum has **no PASS / READY /
SCALE-READY member**; it tops out at `OWNER_REVIEW_REQUIRED` and is fail-closed `NOT_READY` on any incomplete evidence
category or un-recorded smoke. Reaching `OWNER_REVIEW_REQUIRED` means *"complete and honestly evidenced, ready for the
owner to review"* — it does **not** mean ready to scale, send, auto-publish, or go to production. Every flag that would
enable a real action (`global_gateway_state`, `production_flag`, `external_send`, `SCALE_MODEL_RATIFIED`,
`SCALE_EXECUTION_ENABLED`, `HASH_POLICY_RATIFIED`, `LEARNING_AUTOPUBLISH_ENABLED`) is OFF/False and is not touched here.
The owner's PR/PILOT decision (§8) is the only place any of that changes, and `production_flag` must be verified **STILL
OFF** at sign-off.

> **Honesty note on the readiness label (surfaced by the boundary full pass, `F-EVID-5`):** `OWNER_REVIEW_REQUIRED`
> gates on *recorded + evidenced*, not on *passed* — a pack in which every smoke was recorded with a **FAIL** status
> would still read `OWNER_REVIEW_REQUIRED` (it can never read higher). In **this** pack all 18 P0 smokes are recorded
> **PASS** (and 4 of them — SMK-001/006/008/017 — were independently spot-re-run ×2, reproducible — §4), so there is
> no live misrepresentation; but the owner
> should read the actual pass/fail from the smoke report (§2, category 10), not from the readiness label alone. Fix
> routed to CODER (drop to `NOT_READY` on any recorded FAIL/HOLD).

---

## 2. The ten doc §22 evidence categories (the owner review package map)

All ten categories are assembled **with mandatory content** (proven structurally in `M6_2K_EVIDENCE_INDEX.md` §4 — a
missing mandatory key ⇒ INCOMPLETE ⇒ `NOT_READY`). Each category's proof is the recorded P0 re-run plus the carried
slice that owns the behavior.

| # | Category | Evidence | Owner-review note |
|---|---|---|---|
| 1 | **Event Registry** | SMK-001 (event not in registry → Reject/HOLD, audit); registry validator (M6.2A/B); two-layer enforcement (hook + endpoint) | ✅ complete |
| 2 | **Consent** | SMK-002 (missing consent → no external measurement/audience sync), SMK-008 (CRM opt-out → no sync); fail-closed `ConsentGate` | ✅ complete |
| 3 | **Outbox** | SMK-016 (bounded retry + error_log + next_retry_at → dead-letter; no infinite retry / no silent loss — executed) | ✅ complete |
| 4 | **Dedup** | SMK-003 (duplicate Pixel/CAPI/Offline → single shared platform `event_id`, no double count) | ✅ complete |
| 5 | **Attribution** | SMK-006 (full source → dashboard), SMK-007 (missing source → LOW/HOLD), SMK-013 (live/comment/Messenger trace), SMK-018 (post-verify correction → adjustment record) | ✅ complete — trace-bind caveat in §7 (F-SEC-2I-1) |
| 6 | **Dashboard** | SMK-006 (ROAS/CPA/AOV), SMK-004 (quote → no revenue), SMK-005 (draft → not verified), SMK-015 (quote-as-revenue → Fail) | ✅ complete — verified-only caveat in §7 (F-DASH-1/3, F-GROWTH-3) |
| 7 | **Scale Gate** | SMK-009 (recall/sale-lock → FAIL/HOLD), SMK-012 (no owner approval → no scale) | ✅ complete — thresholds OPEN (M6-OD-002) |
| 8 | **Learning** | SMK-011 (candidate outside safe range → hold, no publish) | ✅ complete — safe range OPEN (M6-OD-006) |
| 9 | **Security / Privacy** | SMK-017 (external payload from raw-PII event → hash policy, no raw PII); pack-wide 0-raw-PII scan (2275 files, §4); access-control design + enforced hooks | ✅ complete — hash policy OPEN (M6-OD-003), admin authN forward (M6-OD-011) |
| 10 | **Smoke Report** | all 18 P0 smokes recorded with masked `correlation_id` + `evidence_id` (`SMOKE_RESULTS.md`) | ✅ complete — 18/18 PASS |

---

## 3. Slice-gate results (judge verdicts across the whole pack)

Pre-slice gates: **BOOTSTRAP** SIGNED · **DOC_LOCK** SIGNED · **PHASE-0** SIGNED · **HARMONIZATION** SIGNED.

| Slice | Entry-gate judge | Slice-gate judge |
|---|---|---|
| M6.2A | **M6-P1000 — BLOCKED** (ledger SKIPPED via `M6-OVERRIDE-M6P1000-STAGED`; verdict left BLOCKED, re-gate at M6.2G) | M6-P1009 SIGNED |
| M6.2B | M6-P1100 SIGNED | M6-P1109 SIGNED |
| M6.2C | M6-P1200 SIGNED | M6-P1209 SIGNED |
| M6.2D | M6-P1300 SIGNED | **M6-P1309 — BLOCKED** (ledger SKIPPED via `M6-OVERRIDE-M6P1309-STAGED`; verdict left BLOCKED) |
| M6.2E | M6-P1400 SIGNED | M6-P1409 SIGNED |
| M6.2F | M6-P1500 SIGNED | M6-P1509 SIGNED |
| M6.2G | M6-P1600 SIGNED | M6-P1609 SIGNED |
| M6.2H | M6-P1700 SIGNED | M6-P1709 SIGNED |
| M6.2I | M6-P1800 SIGNED | M6-P1809 SIGNED |
| M6.2J | M6-P1900 SIGNED | M6-P1909 SIGNED |
| M6.2K | M6-P2000 SIGNED | M6-P2009 SIGNED |

**Result: 20 of 22 slice gates SIGNED (11 slices × entry + slice judge; the 4 pre-slice gates above are all SIGNED);
2 stand BLOCKED** — M6-P1000 (M6.2A entry) and M6-P1309 (M6.2D exit). Both were
opened for STAGED build by an explicit **owner override** that stages but **does not convert** the BLOCKED verdict; both
are carried verbatim in the standing blocker list (§7). The final review judge **M6-P3011** (`FINAL_REVIEW_JUDGE`) is
TODO downstream. This is the honest slice-gate picture: the build proceeded under two acknowledged BLOCKED verdicts, by
owner override, with production held OFF.

---

## 4. PR/PILOT full-pass results (all PASS)

| Prompt | Role | Result |
|---|---|---|
| **M6-P3000** `E2E_CHAIN_REVIEW` | ANALYST | Chain Ads→Live→Comment→Messenger→Quote→Order→Verified is coherent; every hop measured, attribution traceable, verified-only enforced at the store/dashboard core; two OPEN chain-integrity conditions (F-SEC-2I-1 single-subject trace bind — the one channel-reachable item; F-GROWTH-3 verified-only choke not carried to the growth path). See `E2E_CHAIN_REVIEW.md`. |
| **M6-P3001** `E2E_SMOKE_VALIDATION` | TESTER | All 18 P0 smokes recorded with `correlation_id` + `evidence_id`; 4 spot-re-run ×2 (SMK-001/006/008/017, 50 nodes total per run), **reproducible** (identical, RC 0). Evidence complete + reproducible → ready for owner review, not production. |
| **M6-P3002** `BOUNDARY_FULL_PASS` | BOUNDARY | Pack-wide cross-slice adversarial pass: 22 outcomes = 12 DEFENDED / 10 OPEN_NONGATE / **0 BREACH**; **0 channel-reachable fail-gate breaches**. The four named seams (evidence-tamper FAIL-007, gate-bypass/auto-scale FAIL-009/FAIL-006, revenue-misuse FAIL-001, data-mart FAIL-005) all DEFENDED. Grep-confirmed the materializer/funnel/growth are **unwired from every `app/api` endpoint** — so the revenue-mispair and trace-stitch findings are in-process/trusted-input only. 5 new residuals surfaced (§7). |
| **M6-P3003** `SECURITY_FULL_PASS` | SECURITY | Canonical repo secret scan **CLEAN across 2275 files** (0 tokens / secret-assignments / raw-ids / emails / phones; real high-entropy tokens = 0). Hash policy fail-closed + honestly OPEN (M6-OD-003). Access-control existence satisfied by design + enforced hooks; runtime admin-API authz deferred to M6-OD-011. One OPEN item: an **imported** Spring dev-password UUID in third-party entry evidence (§7). |

---

## 5. All OPEN decisions, with the pack's recommendation (owner to ratify or overrule)

From `DECISION_REGISTER.md`. **OPEN decisions never block documentation; they block the specific implement/scale/send
legs listed, and they are the owner's to decide before any real production/scale.**

| ID | Question | Pack recommendation | Blocks |
|---|---|---|---|
| **M6-OD-001** | Official Phase-1 Hero SKU list? | Lock the Hero SKU list before running 13/20 SKUs in parallel | M6.2A pilot config; PR/PILOT |
| **M6-OD-002** | Official CPA/ROAS/AOV/Verified-Rate thresholds per stage? | Owner sets thresholds; used by Scale Gate + dashboard alerts | scale gate, dashboard alerts (M6.2G) |
| **M6-OD-003** | Hash policy + permitted Pixel/CAPI/Offline fields? | Keep fail-closed (empty raw allow-list, everything hashed) until privacy/legal ratifies the field list | M6.2D exit send, SMK-017 (mechanism only) |
| **M6-OD-004** | Which connector first in pilot (Meta/Google)? | Owner chooses; no connector is built/called yet | M6.2D scope, PR/PILOT |
| **M6-OD-005** | Official attribution model (first/last/weighted/cohort)? | Dashboard may display several; the scale gate needs one authoritative model — none is scale-authoritative while `SCALE_MODEL_RATIFIED=False` | M6.2E design, M6.2G scale evidence |
| **M6-OD-006** | Safe range for guarded auto-publish? | Required before learning-engine publish; today fail-closed HOLD | M6.2H publish leg, SMK-011 |
| **M6-OD-007** | Persona/keyword/hook content fill locked? | Framework may proceed; only seed content waits | M6.2H seed content |
| **M6-OD-008** | PAYMENT_COMPLETED as a revenue signal? | Treat as non-revenue telemetry until Core policy evidence; ORDER_VERIFIED stays the sole revenue source (RULE-003) | M6.2E/M6.2F edge handling |
| **M6-OD-009** | GOLDEN_HOUR_START/REMINDER enabled for pilot, owned by whom? | Register both as optional/disabled by default; Gateway/Live owns emission config | M6.2I event set |
| **M6-OD-010** | Slice execution model (parallelism)? | Strictly sequential A→…→K (honors "no phase jump"); owner may later approve parallel bands | prompt DAG (pack proceeds sequential) |
| **M6-OD-012** | Evidence masking format? | `abc***xy` (first 3 + last 2) + `secret_ref` indirection everywhere | evidence format (pack proceeds with recommendation) |

**DECIDED (for completeness):** **M6-OD-011** — target repo/stack — **DECIDED 2026-07-23** (GREENFIELD; `IMPLEMENTATION_TARGET_LOCKED.json`=LOCKED).
Its downstream **admin-endpoint authN/authZ integration step** (runtime framework/DB/authN still unresolved in the
manifest) remains a forward condition and appears in the standing blocker list (§7) as the shorthand "M6-OD-011". The two
**owner overrides** (`M6-OVERRIDE-M6P1000-STAGED` 2026-07-29, `M6-OVERRIDE-M6P1309-STAGED`) stage the BLOCKED M6.2A/M6.2D
verdicts for the build but do **not** convert them.

---

## 6. Conflict Matrix (doc contradictions — each carries a recommendation, never silently resolved by code; RULE-018)

| Conflict | The tension | Pack recommendation | Status |
|---|---|---|---|
| **M6-CONF-001** | `ads_measurement_event` (singular contract, §10) vs `ads_measurement_events` (plural table, §13) | Read the singular as the row contract of the plural table; no rename | OPEN (low risk) |
| **M6-CONF-002** | "PAYMENT_COMPLETED nếu Core policy cho phép" — conditional revenue, policy not in doc | Non-revenue telemetry until Core policy; ORDER_VERIFIED sole revenue | OPEN → M6-OD-008 |
| **M6-CONF-003** | "Retargeting Engine cơ bản" (Phase 1) vs retargeting measurement scoped to M6.2I | M6.2A–D build only the data foundation; M6.2I owns retargeting funnel; no retargeting logic before M6.2I | OPEN |
| **M6-CONF-004** | GOLDEN_HOUR_START/REMINDER "Tùy cấu hình" — optional, no config owner | Register optional/disabled by default; Gateway/Live owns config | OPEN → M6-OD-009 |
| **M6-CONF-005** | §1 says the deliverable is not code/migration, yet slices prescribe implementation | No real conflict: §1 describes the DOCUMENT; slices govern gated future implementation | RESOLVED-BY-READING (owner may veto) |
| **M6-CONF-006** | "24-7" vs "24/7" spelling | One entity; keep verbatim spellings in quotes; no normalization | RESOLVED-BY-READING (cosmetic) |
| **M6-CONF-007** | Scale-condition row cites "P6 evidence" — Module 6's own phase (self-referencing) | Read P6 = M6's own event-identity evidence (M6.2A/B), re-checked at the Scale Gate; not an external dependency | OPEN |

---

## 7. Honest gap / blocker list (the payload the owner must weigh — RULE-015 / FAIL-007)

### 7a. The 8 standing blockers (carried inside every assembled evidence pack; never dropped)

| # | Blocker | What must clear before any real scale / send / auto-publish / surface |
|---|---|---|
| 1 | **M6-P1000** | M6.2A entry-judge verdict **BLOCKED** (not converted; staged via override, re-gate at M6.2G) |
| 2 | **M6-P1309** | M6.2D exit-judge verdict **BLOCKED** (not converted; staged via override) — leg-2 (no raw PII) deferred on OPEN M6-OD-003 |
| 3 | **M6.2G-SCALE** | ENTRY-001/003 real-scale conditions, the four M6-P1600 attestation true-ups, ENTRY-004 M5 DEBT-1…4 + the adversarial P4 re-gate, scale ACCESS-1/F-SCALE-\*, and M6-OD-002/003/004/005 |
| 4 | **M6.2H-LEARN** | M6-OD-006 (safe range), M6-OD-007 (content fill), F-LEARN-\* |
| 5 | **M6.2I-FUNNEL** | F-SEC-2I-1 single-subject trace bind (the "F-FUNNEL-4" label; **the one channel-reachable chain finding**), F-SEC-2I-2 raw `messenger_thread_id` |
| 6 | **M6.2J-GROWTH** | F-GROWTH-1 CRM subject-bind, F-GROWTH-3 verified-only choke, F-SEC-2J-\* |
| 7 | **M6-OD-011** | admin-endpoint authN/authZ integration step (+ MISSING CTR-018/019/020) — must fix F-SEC-2I-1/2 before any surface |
| 8 | **M6-OD-012** | PII masking scope — the F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 export-masking-scope family ratifies here |

### 7b. Chain-integrity conditions (from the E2E chain review, M6-P3000)

- **F-SEC-2I-1 (single-subject trace bind) — the one channel-reachable chain finding.** A multi-subject live session can
  stitch different people's `comment_id` / `messenger_thread_id` into one trace. Armed-not-fired only because tests are
  single-subject and the funnel is unwired to any endpoint. Must be fixed before any admin export (M6-OD-011). *Label:*
  the pack calls it "F-FUNNEL-4"; the M6.2I runbook calls it F-SEC-2I-1 — same defect.
- **F-GROWTH-3 (verified-only choke not carried to the Finance-facing growth path).** The `event_code=='ORDER_VERIFIED'`
  choke M6.2I adopted (to close F-DASH-1 on the funnel surface) was not carried into the M6.2J growth reads
  (`revenue_value is not None`). Trusted-input/code-exec-only; reaches a commission-ready figure. Plus F-DASH-1 still
  stands on the M6.2F dashboard materializer write path (never retrofitted).
- **F-GROWTH-1 (CRM subject-bind / borrowed consent).** The CRM gate is keyed by `order_code` and never binds
  `subject_ref` to the buyer; a different subject's VALID CRM consent authorized the buyer's CRM Revenue KPI.
  Trusted-input; FAIL-002 held. Fix mirrors the M6.2E F-D bind.
- **F-DASH-3 / F-VIEW-1 / F-DASH-4** (M6.2F chain-surface residuals not in the 8 standing blockers): verified-revenue
  double-count by `order_code`; raw psid in the staged dashboard support view; scale-eligibility eligibility incomplete.

### 7c. Newly surfaced by the pack-wide boundary full pass (M6-P3002) — armed-not-fired, none channel-reachable to a gate trip

- **`order_code` consumed-fact fan-out (N2):** one per-order eligibility/consent/commission/boxes/capture decision
  multiplies across duplicate-`order_code` rows (every consumed map is `order_code`-keyed). Trusted-input + in-process.
- **F-EVID-5 (N3):** a pack of all-FAIL recorded smokes still reaches `OWNER_REVIEW_REQUIRED` (readiness gates on
  recorded, not passed) — §1 note. Caps at OWNER_REVIEW_REQUIRED, never a Pass.
- **DQ-FAIL banks revenue (N4):** a verified row marked `data_quality_status=FAIL` still banks revenue in
  `verified_rows()` (RULE-009 bars HOLD/FAIL only as *scale* evidence; the report is not scale evidence, so no gate trips).
- **Learning→growth-KPI compose (N5) — the single channel-reachable acceptance found.** An unauthenticated learning-approve
  moves the J growth "Candidate approval rate" display KPI. Armed-not-fired: display-only, `is_publish_authorized` stays
  False (M6-OD-006 OPEN → nothing publishes/scales/sends); **gated behind the OPEN M6-OD-011 admin-authN**.
- **Reactivation borrowed consent (N6):** the F-GROWTH-1 class on the J reactivation surface (`_member_eligible` never
  binds `subject_ref==member_key`). Trusted-input, measure-only, no CRM send.

### 7d. Security items (from the security full pass, M6-P3003)

- **Imported dev-password UUID (OPEN, low severity, owner/entry-evidence-owner decision):** the imported M6-ENTRY-001
  order JUnit log carries a Spring-Boot **auto-generated ephemeral dev password** (masked `73b***92`) — disposable
  (regenerated every boot), third-party test scaffolding (not M6-authored), and not flagged by the canonical gate
  (unquoted). Owner decides: accept as non-sensitive or re-import a scrubbed log (M6-ENTRY-001 is a locked entry
  artifact). Plus a scanner-hardening note (extend the pattern to unquoted `password: <value>` forms).
- **Masking-scope family** F-SEC-2I-2 / F-SEC-2J-2 / F-SEC-2K-1 → ratify together under **M6-OD-012**.
- **Consent subject-bind family** F-GROWTH-1 + N6 reactivation → CODER subject-bind.

All items in §7b–§7d are **armed-not-fired**; none is channel-reachable to a fail-gate trip while the funnel/growth/
materializer are unwired and `external_send=OFF`. They are routed to CODER/owner and are the hardening + decision agenda
before any real surface — **not** defects that a green run papered over.

---

## 8. The owner's PR/PILOT decision agenda (what must be decided before any production / scale)

1. **The ROAS Pass / Scale Ready declaration itself** — owner-only (doc §23); this pack cannot make it (§1). Confirm
   `production_flag` is **STILL OFF** at sign-off (the downstream prompt M6-P3006 verifies this).
2. **Convert or re-gate the two BLOCKED verdicts** — M6-P1000 (M6.2A entry; re-gate bound at M6.2G) and M6-P1309 (M6.2D
   exit) stand BLOCKED under owner override; a real production/scale requires the owner to resolve them, not the override.
3. **Ratify the OPEN owner decisions** (§5): thresholds (OD-002), hash policy + fields (OD-003, privacy/legal), connector
   (OD-004), attribution model (OD-005), learning safe range (OD-006) + content fill (OD-007), Hero SKU lock (OD-001),
   PAYMENT_COMPLETED (OD-008), Golden Hour (OD-009), execution model (OD-010), masking format (OD-012); and complete the
   **M6-OD-011 admin-endpoint authN/authZ integration** (+ CTR-018/019/020).
4. **Direct the CODER hardening** (§7b–§7d): the chain-integrity binds (F-SEC-2I-1 single-subject trace bind before any
   export; F-GROWTH-3 carry the verified-only choke to growth; F-GROWTH-1/N6 subject-bind), the verified-revenue
   integrity items (F-DASH-1/3, DQ-FAIL, order_code fan-out), F-EVID-5 readiness-on-FAIL, and the export-masking-scope
   family — all armed-not-fired today.
5. **Decide the imported dev-password-UUID hygiene item** (§7d) and the scanner-hardening note.

Until the owner records these decisions, `global_gateway_state` stays **BLOCKED**, `production_flag` stays **OFF**,
`external_send` stays **OFF**, and nothing scales, sends, auto-publishes, computes commission, or is declared ROAS Pass /
Scale Ready. This packet's role ends at handing the owner the evidence to decide — it makes no such declaration.

---

*Assembly note: this packet is `analysis_only` — it read the band evidence + registers and wrote only this file and its
evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it assembled, computed no
verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` —
untouched; `M6-P1000` + `M6-P1309` verdicts remain BLOCKED (not converted).*
