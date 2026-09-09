# M6.2Q — Slice Runbook — Ads-spend import + live-session binding + CPA/ROAS-by-session (A5, đường-tới-tiền)

> **Status: STAGED — the "money leg": ROAS/CPA now compute from *mock-in-test* ad spend, and it flips nothing.**
> M6.2Q builds the M6-side **ads-spend ingest** (maker-checker four-eyes) + **live-session-ads-binding.v1** +
> **CPA/ROAS-by-live_session**, a cumulative superset of M6.2P. Everything STAGED: in-memory stores + migration DDL
> `0014–0016` **never applied**, **mock CSV** in tests — **no real Meta network / Marketing API, no real spend data, no
> flag flipped**. `config.py` byte-identical to M6.2P (sha256 `911b3238…`).
>
> **Read the two load-bearing findings first (this is the money leg + the pack's first authz control):**
> 1. **The maker-checker four-eyes is a STRUCTURAL control, not an AUTHENTICATED one.** It fail-closed refuses a
>    self-approve (canonicalized strip+casefold, a red-team fix over raw `==`), refuses a blank checker, and materializes
>    only APPROVED (set-once) — but `uploaded_by` / `decision.actor` are **unauthenticated request-body strings**, so it
>    enforces *two distinct strings*, not *two authenticated principals* (one person can supply maker=A + checker=B
>    today). Its security value is conditional on the **M6-OD-011 server-bind + authenticated identity** — DECIDED
>    (2026-07-23) but **not yet implemented** (a forward step, a separate session — **not** an open decision). Edges
>    MC9 (Unicode homoglyph) + N4 (blank maker) are armed-not-fired until identity is real.
> 2. **The ROAS number is INFLATABLE (N1 / F-SEC-2I-1) — the highest-value finding.** `SessionRoasReader` authenticates
>    the **spend** side (campaign→session binding) but groups **revenue** by each event's own un-provenanced
>    `live_session_id` — so a verified-revenue event on a *different* campaign, tagged with the bound session's
>    `live_session_id`, inflates that session's `verified_revenue`/ROAS. **A5 turned the standing M6.2I-FUNNEL
>    F-SEC-2I-1 trace-bind gap into a money number.** Armed-not-fired (reader internal, events from the trusted store),
>    routed to owner: **bind revenue provenance before any real spend/ROAS surface.**
>
> **What is genuinely good (credited, not rosy):** the RULE-003 verified-revenue lock **held** in the new money math (a
> quote/draft contributes 0 to both the CPA denominator and the ROAS numerator); the four-eyes is the pack's **first
> real segregation-of-duties authz control**, fail-closed + red-team-hardened; the money math is fail-closed
> (`_safe_div`, campaign-binding gate, inclusive window, daily-total bucket). But **ROAS is not "real"** — it computes
> from mock spend, thresholds (M6-OD-002) + the scale-authoritative attribution model (M6-OD-005) stay OPEN, and the
> slice declares no ROAS-Pass / Scale-Ready.
>
> Posture immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all flags `False`,
> `live_migrations=false`. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**; the pack still tops at
> `OWNER_REVIEW_REQUIRED`. Evidence: full suite **631 passed / 0 failed, rc 0**; SMK-029 PASS 5/5; boundary **0**
> in-scope FAIL-007/RULE-003 breaches / 30 recorded; security **0** raw PII / **0** secrets / 274 files. Next: slice-gate
> Judge **M6-P2509**.

| Field | Value |
|---|---|
| Slice | **M6.2Q** — Ads-spend import + binding + CPA/ROAS-by-session (A5); post-pilot; depends on M6.2P; chief-auditor 2026-09-07 items A3(=old A5) + C4 |
| Prompt (this doc) | **M6-P2508** — `M6_2Q_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Rules / fail gate in scope | **RULE-003** (revenue only ORDER_VERIFIED) · **RULE-015** (no self-cert) · **FAIL-007** (no evidence) |
| Contracts | M6-CTR-015 (Dashboard KPI) DRAFT_LOCKED **formulas** (thresholds OPEN via M6-OD-002 — the slice computes *numbers*, not thresholds) · M6-CTR-002 DRAFT_LOCKED (`primary_campaign_id` additive) |
| Owner inputs (DECIDED) | **M6-OD-016** (spend source = CSV Ads Manager + maker-checker) · **M6-OD-011** (binding direction; server-bind/authN not-yet-implemented) · **M6-OD-015** (psid-no-join) |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2Q/`)

M6.2Q carries the **entire M6.2P tree byte-identical** (baseline verified green **before any patch: 603 passed**,
byte-parity) and adds **3 legs** — the coder's **13 new `.py` total** (the leg-1/2/3 app modules + package init + the
3 coder regression tests) + migrations `0014–0016` + 3 additive edits to carried files (the official SMK-029 smoke is
tester-authored, counted in the test tally). **No new config flag** (`config.py` byte-identical). Migrations now
`0001–0016`, all staged, never applied.

| Leg | What | Files | Gate/rule |
|---|---|---|---|
| **1 — ads-spend import + maker-checker + materialize (M6-OD-016)** | `propose()` → PROPOSED; `record_decision()` four-eyes fail-closed (an APPROVE is refused when the canonicalized checker == maker, or the checker is blank); the worker materializes **only APPROVED, set-once** campaign-level records; the API holds **no Meta/Marketing-API/network** verb. | new `models/ads_spend_import.py`, `store/ads_spend_import_store.py`, `ads_spend/import_gate.py`, `ads_spend/materializer.py`, `store/ads_spend_record_store.py`, `api/ads_spend_imports.py`; migrations `0014`+`0015` | **FAIL-007** / RULE-015 |
| **2 — live-session-ads-binding.v1 + primary_campaign_id (M6-OD-011)** | `+primary_campaign_id` first-class on `AdsAttributionContext` (**additive; NOT in `.complete`/grading**); a frozen `LiveSessionAdsBinding{live_session_id, primary_campaign_id, adset_id?, ad_id?, bound_at, bound_by}`; the store is **set-once + campaign-unambiguous** (`session_for_campaign`). | edited `models/attribution_context.py`, `attribution/resolver.py`; new `models/live_session_ads_binding.py`, `store/live_session_ads_binding_store.py`; migration `0016` (+`UNIQUE`) | RULE-015 |
| **3 — CPA/ROAS-by-live_session (M6-CTR-015; RULE-003)** | standalone `SessionRoasReader` (**not** a DataMart method, **not** a 15th metric): per session `CPA=_safe_div(spend, verified_orders)`, `ROAS=_safe_div(verified_revenue, spend)`; spend included **iff** its campaign is bound to the session **and** `spend_date ∈ [min,max event_ts]` (gates on the **campaign-binding, NOT `.mapped`**); out-of-window/unbound → `daily_total()`; verified via **ORDER_VERIFIED + set-once revenue (RULE-003)**. | edited `dashboard/data_mart.py` (`+spend_date` additive); new `dashboard/session_roas.py` | **RULE-003** / FAIL-007 |

---

## 2. Operate

M6.2Q is measure/record-only; there is no real spend, network, or egress. The staged flow:

1. **Import spend (mock CSV).** `POST /api/admin/ads/spend-imports` (create) parses CSV rows keyed by `campaign_id`
   (fail-closed `_parse_rows`: non-empty str id, numeric spend, ISO date) into a PROPOSED import. The `AdsSpendImportDeps`
   holds only the gate + worker + audit — no network connector (M6-OD-016 phase-1 CSV).
2. **Approve (maker-checker).** The decision handler requires all of `actor`/`reason`/`audit_ref`/`evidence_ref`
   (`OWNER_DECISION_INCOMPLETE` otherwise); a **distinct** checker moves PROPOSED → APPROVED; a self-approve /
   blank-checker is `APPROVAL_REFUSED`. **Caveat (§5.1):** distinctness is on *strings*, not authenticated principals.
3. **Materialize + bind.** The worker materializes only APPROVED imports into set-once campaign-level records; a binding
   maps `live_session_id → primary_campaign_id` (set-once, campaign-unambiguous).
4. **Read CPA/ROAS-by-session.** `SessionRoasReader` computes CPA/ROAS per session from the bound+in-window APPROVED
   spend, with the RULE-003 verified-revenue lock. It writes nothing. **Caveat (§5.2):** the revenue side is joined by
   `live_session_id`, not provenance-bound to the campaign — so the ROAS number is inflatable.
5. **What stays impossible:** real Meta network, real spend, external send, a flag flip. `config.py` byte-identical.

---

## 3. Verify

### 3.1 The official smoke (proven by the smoke AND the 3 coder regressions)

**SMK-029 PASS 5/5** (recorded with a masked `correlation_id` + `evidence_id`, executed not waived):
- primary — mock-CSV import → PROPOSED → distinct checker APPROVES → worker materializes only the APPROVED
  (campaign-level, `.mapped False`) record → bind `camp_1→ls_1` → `SessionRoasReader` gives `session_spend 100000`,
  `verified_orders 2` (an in-window QUOTE_SENT contributes 0 — RULE-003), `verified_revenue 500000`, `CPA 50000`,
  `ROAS 5.0`; `EXTERNAL_SEND=="OFF"`.
- neg — self-approve (maker==checker) → `AdsSpendImportGateViolation`, stays PROPOSED, materializes nothing.
- neg — spend>0 + zero verified orders → `CPA is None` (no divide-by-zero) + `ROAS 0.0`.
- neg — out-of-window / unbound spend → `daily_total()`, not session-attributed.
- neg — a PII-shaped checker free-text never reaches the audit trail raw (FAIL-008), yet the APPROVE is audited.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2Q/  (venv: 02-tester/.venv, python 3.12.13, pytest 8.4.2; -B, cache-free, no shell redirection)
python -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 631 passed / 0 failed
python -B -c "<tally; pytest.main(['tests/smoke/test_smk_029_ads_spend_cpa_roas_by_session.py'])>"  # -> RC 0 ; 5 passed
```

**Reconciliation: 631 (tester-run final) = 603 carried (M6.2P) + 23 coder M6.2Q regressions (18 leg + 5 red-team alias,
→ 626 coder baseline) + 5 official-smoke nodes (SMK-029).** Coder baseline before any patch was 603 (byte-parity with
M6.2P); the isolated 1-leg run independently confirms 5 passed. *(pytest's terminal summary is unreliable in this harness
for a long run, so totals came from an in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0` — see
SMOKE_RESULTS.md "On counting".)*

### 3.3 The in-scope gates — FAIL-007 not tripped, RULE-003 lock held (boundary-verified; carried fixes intact)

- **RULE-003 verified lock (the money math is honest):** `SessionRoasReader._verified` filters **both** the CPA
  denominator and the ROAS numerator on `event_code == ORDER_VERIFIED` — an in-window QUOTE_SENT/ORDER_CREATED
  contributes 0; a revenue_value crafted onto a QUOTE_SENT row is excluded (boundary RO1/RO2). Fail-closed `_safe_div`:
  spend + zero verified → CPA None, ROAS 0.0; no bound spend → CPA/ROAS None (a genuine 0/0, never a fabricated 0).
- **FAIL-007 (maker-checker + evidence):** self-approve refused, only APPROVED materializes (set-once), the pack still
  tops at `OWNER_REVIEW_REQUIRED` (carried F2-6 duck-coerce intact). Boundary: **30 recorded (29 executed + 1 NOTE),
  23 DEFENDED / 6 OPEN_NONGATE / 1 NOTE, 0 in-scope breaches**.
- Security: **0** raw PII / **0** secrets / 274 files (ad spend is campaign-level, not PII; actors masked; no Meta token).
  Posture BLOCKED/OFF/OFF unchanged; byte-clean.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied (`live_migrations=false`), no flag flipped, no
egress opened. Baseline rollback = **delete the `04-artifacts/impl/M6.2Q/` tree** (M6.2P untouched, byte-identical).
Per change:

| Change | Rollback |
|---|---|
| **Leg 1 new files** — `models/ads_spend_import.py`, `store/ads_spend_import_store.py`, `ads_spend/import_gate.py`, `ads_spend/materializer.py`, `store/ads_spend_record_store.py`, `api/ads_spend_imports.py` | delete the files |
| **Leg 2 new files** — `models/live_session_ads_binding.py`, `store/live_session_ads_binding_store.py` | delete the files |
| **Leg 3 new file** — `dashboard/session_roas.py` | delete the file |
| **Edited carried files** — `models/attribution_context.py` (`+primary_campaign_id`), `attribution/resolver.py` (set it), `dashboard/data_mart.py` (`+spend_date`) | **scoped revert** of only the additive field/line to M6.2P bytes |
| **Migrations** — `0014_create_ads_spend_import.sql` (+`ads_spend_import_row` child), `0015_create_ads_spend_record.sql`, `0016_create_live_session_ads_binding.sql` (new, staged, **never applied**) | `down`-DDL per file (`DROP TABLE`); delete the files — no live migration to unwind |
| **Four-eyes canonicalization** (`import_gate.py` `_canon_actor` strip+casefold) | part of the new `import_gate.py` (delete); the plan's literal was raw `==` — the shipped canon is a strengthening, not a relaxation |
| **New tests** — 3 coder regressions (`test_m6_2q_ads_spend_import_maker_checker.py`, `_binding_primary_campaign.py`, `_cpa_roas_by_session.py`) + the official `tests/smoke/test_smk_029_*.py` + `TEST_MANIFEST.md` | delete the files |
| **Config flag** | **none** — `config.py` byte-identical to M6.2P |
| **Boundary / security analysis-only writes** (`M6.2Q_boundary.md`, `M6.2Q_security.md`, harness/scanner scripts) | delete; both recorded "no source modified" |

Every change is additive or a fail-closed control, so a revert restores prior behaviour. No posture value was ever
written.

---

## 5. Decision deltas & governance

### 5.1 B1 — the maker-checker four-eyes is structural, not authenticated (top-0.1% lens: the pack's first authz control)

M6.2Q adds the pack's **first genuine authorization control** — a maker-checker separation of duties on spend approval.
The honest bounding:
- **Structurally sound + red-team-hardened:** an APPROVE is fail-closed refused unless the **canonicalized**
  (strip+casefold) checker differs from the maker and the checker is non-blank; only APPROVED materializes; the record
  store is set-once; a re-decide is refused; the deps hold no network verb. The canonicalization is a coder red-team fix
  over the plan's raw `==` (which let a case/whitespace alias self-approve).
- **The load-bearing caveat:** `uploaded_by` / `decision.actor` are **unauthenticated request-body strings** — the gate
  enforces *two distinct strings*, not *two authenticated principals*. A single person can supply `maker="alice"` +
  `checker="bob"` today. **The control's security value is conditional on the M6-OD-011 server-bind + real
  authN/authZ** — M6-OD-011 is **DECIDED (2026-07-23)**, but the server-bind/authN implementation is the **not-yet-done
  forward step** (a separate session), **not an open decision**. Two armed-not-fired edges hold until identity is real:
  **MC9** (a Unicode full-width homoglyph of the maker bypasses `casefold`≠NFKC → treated as distinct → self-approve) and
  **N4** (a blank *maker* + any distinct checker → APPROVED; the gate refuses a blank checker but not a blank maker).

### 5.2 B2 — the ROAS number is inflatable: revenue-provenance asymmetry (N1 / F-SEC-2I-1, highest-value)

`SessionRoasReader` authenticates the **spend** side (campaign→session binding, set-once + unambiguous) but groups
**revenue** by each event's own `live_session_id` (`_session_key`), which is **not** provenance-bound to the campaign. So
a verified-revenue event on a *different* campaign, merely tagged with the bound session's `live_session_id`, is counted
in that session's `verified_revenue` and **inflates its ROAS** (executed: 100000 + 900000 → 1000000). **A5 turned the
standing M6.2I-FUNNEL blocker F-SEC-2I-1 (single-subject / live_session bind) into a money number.** Armed-not-fired: the
reader is internal (no channel export) and events come from the trusted measurement store. **Route: owner — bind revenue
provenance before any real spend/ROAS surface.** This is the finding to weigh hardest.

### 5.3 The positive worth crediting — the RULE-003 lock held in the new money math

The verified-revenue lock the pack built across M6.2E/F/L **held** when it became money: a quote/draft in the session
window contributes 0 to both the CPA denominator (verified-order count) and the ROAS numerator (verified_revenue), the
mispair (revenue crafted onto a QUOTE_SENT row) is excluded, and the divisions are fail-closed. The money math does not
count a non-verified row — a real, boundary-verified integrity property, not a claim.

### 5.4 Coder self-fixes (M6-P2501/2502)

- **Plan red-team (1 MAJOR, fixed pre-code):** the by-session spend sum was wrongly gated on `.mapped`, but the
  campaign-level source has adset/ad `None` so `.mapped` is always False → the sum would always be None. **Fix:** re-gate
  on the **campaign-binding** (`session_for_campaign`), proven by a regression that includes a `.mapped is False`
  bound+in-window record.
- **Implement self-review (fixed):** the four-eyes raw `==` let a case/whitespace alias self-approve → canonicalized
  strip+casefold + refuse-blank-checker (5-case alias regression). Strengthens the control; relaxes nothing.

### 5.5 Residuals (armed-not-fired; none trips an in-scope gate; the reachability floor: no HTTP/durable-export surface wired [forward M6-OD-011], events from the trusted store, external_send Final OFF)

- **N1 / F-SEC-2I-1 (owner, highest-value):** the ROAS revenue-provenance asymmetry (§5.2) — bind revenue provenance.
- **Four-eyes edges (CODER):** MC9 — NFKC-normalize before strip+casefold in `_canon_actor`; N4 — require a non-blank
  **maker** too (four-eyes needs two distinct non-blank actors).
- **MC-09 (primary security; M6-OD-012 + CODER):** `AdsSpendImportDecision.to_public()` exports `reason`/`audit_ref`/
  `evidence_ref` (checker free-text) **verbatim** — same durable-export masking-scope family as F-SEC-2K-1/2M-1. **The
  audit trail is already safe** (the gate never echoes the free-text into `detail`); the gap is only the decision
  object's export. Fix: run `reason`/`audit_ref`/`evidence_ref` through the raw-PII tripwire at import (email-shaped
  reject is false-positive-safe) or mask on export; the scope is M6-OD-012.
- **Value-sanity (CODER):** RO10/N2 — neither the spend write nor the verified-revenue write checks finiteness/sign; a
  negative → negative CPA/ROAS, a NaN → NaN and `to_public` emits raw NaN (breaks the JSON export contract). The
  **verified-revenue** write is the *more reachable* twin (it has **no** maker-checker gate, unlike the
  maker-checker-approved spend write). Fix: `math.isfinite(v) and v >= 0` on **both** writes.
- **order_code double-count (owner; carried F-DASH-3):** N3 — two ORDER_VERIFIED events sharing `order_code` but distinct
  `idempotency_key` both count (denominator + numerator); the store dedups only on `idempotency_key`. Confirm order_code
  uniqueness upstream or dedup `_verified` by `order_code`.
- **NOTE robustness:** ROAS-14 (rogue `event_ts` widens the derived window → M6-OD-005), ROAS-15 (tz-mismatch crash —
  fails loud, CODER normalize tz), BIND-07 (blank `primary_campaign_id` — guarded, CODER reject at bind), **EVID-10**
  (the A5 reader's RULE-003 lock is proven by SMK-029 *proposed/HARDENING*, not a registered P0 smoke → owner decide a
  P0-registry floor so a future regression that let a quote inflate CPA/ROAS-by-session would drop pack readiness).

### 5.6 New owner decisions + immutable posture

- **DECIDED (authorize this slice):** M6-OD-016 (spend source = CSV + maker-checker), M6-OD-011 (binding direction),
  M6-OD-015 (psid-no-join — tightens the B1 psid_hash cross-module-join forward condition; OD-003 stage-1 field/hash
  policy also recorded).
- **Hard forward gates (before any real spend / scale / egress):** **M6-OD-011** server-bind + authenticated identity
  (B1); **M6-OD-002** thresholds; **M6-OD-005** scale-authoritative attribution model (+ROAS-14 window); **M6-OD-012**
  durable-export masking (MC-09 + carried trace-id family); **M6-OD-003** real psid pepper + privacy/legal (carried);
  **F-SEC-2I-1** revenue provenance (B2); plus M6.2G/H/I/J. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**.
- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, all flags `False`,
  `live_migrations=false`; `config.py` byte-identical to M6.2P. Out of scope (untouched): real CSV source / Meta network /
  Marketing API (phase-2 go-live); real spend + external send; `board_id`/`segment_id` (C1/M7); DB/HTTP server-bind
  (B9/M6-OD-011). **Operator hygiene (non-blocking, carried):** register M6-OD-013/014 + the M5 `PSID_HASH_POLICY_M5_TMP`
  dependency in `DECISION_REGISTER.md`; reconcile the stale ENTRY-004 row.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Code (staged, new)** | the coder's **13 new `.py` total**: leg-1 ads_spend models/stores/gate/materializer/API, leg-2 binding model/store, leg-3 `session_roas.py` (the load-bearing app modules) + package init + the 3 coder regression files. |
| **Code (staged, edited additive)** | `models/attribution_context.py` (`+primary_campaign_id`, not in grading), `attribution/resolver.py` (set it), `dashboard/data_mart.py` (`+spend_date` on `AdsSpendRecord`). |
| **Migration** | **+`0014_create_ads_spend_import`** (+`ads_spend_import_row` child), **+`0015_create_ads_spend_record`**, **+`0016_create_live_session_ads_binding`** (+`UNIQUE`) — staged, **never applied**; migrations now `0001–0016`. |
| **Tests (staged)** | 23 coder regression **cases** (in the 3 files within the 13 `.py` above: 18 leg + 5 red-team alias) + the official **SMK-029** (5 nodes). Suite **603 → 631**. |
| **Config flag** | **none**; `config.py` byte-identical to M6.2P. |
| **Contracts** | CTR-015 DRAFT_LOCKED formulas (thresholds OPEN via M6-OD-002); CTR-002 DRAFT_LOCKED (`primary_campaign_id` additive). No new contract. |
| **Owner decisions** | M6-OD-016 / M6-OD-011 / M6-OD-015 DECIDED (authorize the slice); the money-side forward gates M6-OD-011 (authN) / M6-OD-002 / M6-OD-005 / M6-OD-012 / M6-OD-003 + F-SEC-2I-1 carried. |
| **New capability** | the pack's **first real authz control** (maker-checker four-eyes, structural-not-authenticated); CPA/ROAS-by-live_session from mock approved spend under the RULE-003 lock. |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted). |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, all flags `False`, `config.py` byte-identical. **No real spend / Meta network / egress / flag flip.** |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED`; **ROAS is mock, not real** and **not certified** (M6-OD-002/005 + provenance forward). |

---

## 7. Handoff

- **Immediate next (JUDGE, fresh session): M6-P2509 `M6_2Q_SLICE_GATE_JUDGE`.** Checks the 7 exit-gate legs (spend
  import + maker-checker, binding + primary_campaign_id, CPA/ROAS-by-session under RULE-003, SMK-029 recorded,
  every-prompt evidence, judge sign-off, rollback) **AND confirms no flag flip / no real spend / no Meta network /
  posture OFF-BLOCKED-OFF.** Judges never modify what they judge. See §8.
- **OWNER (the load-bearing forward steps):** **M6-OD-011** authenticated-identity binding for the maker-checker actors
  (the four-eyes is structural until then, B1); **F-SEC-2I-1** revenue-provenance bind (ROAS inflatable until then, B2);
  **M6-OD-002** thresholds; **M6-OD-005** scale-authoritative attribution model; **M6-OD-012** durable-export masking
  (MC-09 + carried family); **M6-OD-003** real psid pepper + privacy/legal (carried); the order_code-uniqueness question;
  and whether the A5 reader needs a P0-registry floor (EVID-10).
- **CODER:** NFKC-normalize + require non-blank maker in the four-eyes gate (MC9/N4); `math.isfinite && >= 0` on the
  spend + verified-revenue writes (RO10/N2); run `reason`/`audit_ref` through the raw-PII tripwire (MC-09); tz-normalize
  (ROAS-15); reject blank `primary_campaign_id` at bind (BIND-07); order_code dedup.
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2509)

1. **Read order:** `M6_2Q_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2500…2506) → the two review reports
   (`M6.2Q_boundary.md` §2–3 the four-eyes + RULE-003 locks + residuals, `M6.2Q_security.md` §4–7 MC-09 + access-control +
   RULE-003 + N1) → `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (rollback §5). The 7-leg exit-gate map is index §4.
2. **What is proven (executed + boundary/security-verified):** the maker-checker four-eyes is fail-closed +
   red-team-hardened; only APPROVED materializes (set-once); the binding is set-once + campaign-unambiguous; the
   CPA/ROAS-by-session math keeps the RULE-003 verified-revenue lock (quote/draft → 0; fail-closed `_safe_div`). Full
   suite **631 passed**; SMK-029 5/5; boundary **0** in-scope FAIL-007/RULE-003 breaches / 30 recorded; security **0** raw
   PII/secrets / 274 files; `config.py` byte-identical.
3. **The two findings to weigh hardest (this is the money leg):** **B1** — the four-eyes is a **structural** control
   (two distinct strings), not authenticated (two principals); real authz is the **M6-OD-011 server-bind (DECIDED but
   not yet implemented — a forward step, not an open decision)**; edges MC9/N4 armed-not-fired until identity is real.
   **B2 (N1 / F-SEC-2I-1)** — the ROAS **revenue** side is joined by an un-provenanced `live_session_id` while the
   **spend** side is authenticated, so ROAS is **inflatable**; A5 turned the standing M6.2I-FUNNEL bind into a money
   number → owner, bind revenue provenance before any real spend/ROAS surface.
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING only because this docs prompt (M6-P2508) and the judge
   (M6-P2509) are the last two to run. Legs 1–4 + 7 (rollback) are MET. ROAS is **mock, not real**, and **not certified**
   — thresholds (M6-OD-002) + the scale-authoritative model (M6-OD-005) stay OPEN; no ROAS-Pass/Scale-Ready here.
5. **Confirm the posture:** no flag flip, no real spend, no Meta network, `config.py` byte-identical, migrations
   `0014–0016` staged-never-applied, `M6-P1000` + `M6-P1309` BLOCKED (not converted).
6. **Boundary integrity of this docs prompt (M6-P2508):** `analysis_only` — it read the band evidence and wrote only this
   runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it documented,
   opened no egress, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
   `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
