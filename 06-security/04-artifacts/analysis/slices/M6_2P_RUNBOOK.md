# M6.2P — Slice Runbook — external_send_policy typed enum (B5 · M6-OD-003 vocabulary half)

> **Status: STAGED — adopts an owner-signed vocabulary as typed, fail-closed code; it OPENS NO EGRESS.**
> M6.2P adopts the owner-signed (QĐ-1, 2026-09-07) `ExternalSendPolicy` 4-value enum
> `{ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}` as typed, fail-closed code — replacing the raw
> `Optional[str]` token in `models/consumed.py` and the hard-False `permits_external_send()` in
> `registry/validator.py`. It makes the enum vocabulary **real + fail-closed**; it does **not** open egress and depends
> on nothing from M3/Sếp.
>
> **Read the crux honestly (the point of this slice):** making an `external_send_policy` enum with an `ALLOW_EXTERNAL`
> member must **not** read as "external send is now enabled". **M6-OD-003 is now PARTIAL / split:** the enum
> **vocabulary** half is owner-signed (QĐ-1, chief-confirmed) and adopted here (RULE-018 — M6 invents no value); the
> risk-bearing **permit-mapping** (which events/fields are `ALLOW_EXTERNAL`) + the Pixel/CAPI/Offline **hash policy**
> stay **OPEN** (privacy/legal, Sếp). **No registry row is `ALLOW_EXTERNAL`, and egress is airtight across four
> independent layers** (§3.3). The exit judge **M6-P2409** must confirm no row is `ALLOW_EXTERNAL` and `EXTERNAL_SEND`
> stays Final OFF.
>
> Posture immutable and untouched: `config.py` **byte-identical to M6.2O** (sha256 `911b3238…`);
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF` (**Final**), `is_external_send_enabled()`
> False, all flags `False`, `live_migrations=false`; no migration (`0001–0013`), no new flag. `M6-P1000` + `M6-P1309`
> remain **BLOCKED (not converted)**; the pack still tops at `OWNER_REVIEW_REQUIRED`. Evidence: full suite **603 passed
> / 0 failed, rc 0**; SMK-028 PASS 4/4; boundary **0** FAIL-007 breaches / 19 outcomes; security **0** raw PII / **0**
> secrets / 257 files.

| Field | Value |
|---|---|
| Slice | **M6.2P** — external_send_policy enum (B5, M6-side of the event-registry runtime); post-pilot; depends on M6.2O; chief-auditor 2026-09-07 item B5 + QĐ-1 signature |
| Prompt (this doc) | **M6-P2408** — `M6_2P_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Rules / fail gate in scope | **RULE-014** (no raw PII / egress governance) · **RULE-015** (no self-cert) · **FAIL-007** (no evidence) |
| Contract | **M6-CTR-003** `event_registry` (CONSUMED, harmonized M6.2A/M6-P0701) DRAFT_LOCKED → satisfied |
| Entry note | Entry judge M6-P2400 is a **re-judgment** after the owner filed the QĐ-1 authorization; M6-OD-003 reconciled to **PARTIAL** (enum vocabulary SIGNED; permit-mapping + hash OPEN → forward condition). |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2P/`)

M6.2P carries the **entire M6.2O tree byte-identical** (baseline verified green **before any patch: 593 passed**) and
patches **2 app files** to adopt the owner-signed vocabulary. **M6 invents no value (RULE-018)** — it operationalizes
exactly the decided QĐ-1 half. **No new migration** (`0001–0013`), **no new config flag** (`config.py` sha256
byte-identical to M6.2O). The **only** `app/` reader of `external_send_policy` is `validator.py` (grep-verified — the
field retype has no ripple).

| File | Change |
|---|---|
| `app/measurement/models/consumed.py` | `+class ExternalSendPolicy(str, Enum)` `{ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}`; retyped `EventRegistryRow.external_send_policy: Optional[ExternalSendPolicy] = None` (was `Optional[str]`; mirrors `data_sensitivity: Optional[DataSensitivity]`). |
| `app/measurement/registry/validator.py` | `+_resolve_send_policy(raw) -> ExternalSendPolicy` — real member / valid token → member; **None / blank / whitespace / unknown / non-coercible → `BLOCKED_DEFAULT`** (never auto-allow; no crash on a registry-sourced token — a hostile in-process dunder is the narrow-except N1 edge, §5.3, which fails loud, never toward send; mirrors `_resolve_sensitivity`'s MISSING→PII). Retyped `permits_external_send(policy) -> bool` → `policy is ExternalSendPolicy.ALLOW_EXTERNAL` (identity, not `==`). `validate()` coerces then gates on the coerced policy; imported the enum. `ValidationResult.external_send_permitted: bool` unchanged. |
| **new** `tests/test_m6_2p_external_send_policy.py` | 6 CODER regressions (the 4 values; the fail-closed coercion over junk; permits only ALLOW_EXTERNAL; a real ACCEPTED event → `send_permitted=False`; the non-vacuous ALLOW_EXTERNAL control). |

---

## 2. Operate

M6.2P hardens a consumed field on the ingest/validate path; there is no new operational action, and it opens nothing.

1. **The vocabulary is now real + typed.** A registry row's `external_send_policy` is coerced to the enum; an unknown /
   blank / None token resolves **fail-closed to `BLOCKED_DEFAULT`** — never auto-allow, no crash on a registry token (the hostile-dunder edge is the N1 robustness residual, §5.3, and still fails away from send).
2. **The gate permits only ALLOW_EXTERNAL.** `permits_external_send()` is True **only** for
   `ExternalSendPolicy.ALLOW_EXTERNAL`, and only on an ACCEPTED event (unknown → REJECT, de-registered/missing-owner →
   HOLD, all `send_permitted=False`).
3. **Nothing egresses.** No registry row is classified ALLOW_EXTERNAL (the permit-mapping is the OPEN M6-OD-003 half),
   and `EXTERNAL_SEND` is Final OFF with the staged transport raising `ExternalSendBlocked` unconditionally — so even a
   (hypothetical) ALLOW_EXTERNAL row opens no real send. `send_permitted` is an **inert eligibility flag**.
4. **The forward step (owner, not this slice):** the M6-OD-003 permit-mapping + Pixel/CAPI/Offline hash policy decide
   *which* events/fields may actually be sent and *how* they are hashed — until then no event is ALLOW_EXTERNAL.

---

## 3. Verify

### 3.1 The official smoke (proven by the smoke AND the coder regression)

**SMK-028 PASS 4/4** (recorded with a masked `correlation_id` + `evidence_id`, executed not waived):
- primary — each of the 4 values validates ACCEPTED; `external_send_permitted` True **iff** ALLOW_EXTERNAL.
- neg — None/`""`/`"   "`/tab/unknown (`"MAYBE"`/`"allow"`/`"ALLOW"`/`"true"`)/non-coercible (`123`/`0`/`object()`/`b"ALLOW_EXTERNAL"`) → `BLOCKED_DEFAULT` (no crash, no auto-allow) → `external_send_permitted False`.
- neg — a real ACCEPTED event (VIEW_LANDING, policy None) → `send_permitted False` (no real event is ALLOW_EXTERNAL).
- control (non-vacuity + defense-in-depth) — an explicit ALLOW_EXTERNAL row makes the policy gate genuinely True (**not**
  a dead hard-False) **yet** `config.EXTERNAL_SEND == "OFF"` → no real egress.

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2P/  (venv: 02-tester/.venv, python 3.12.13, pytest 8.4.2; -B, cache-free, no shell redirection)
python -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"   # -> RC 0 ; 603 passed / 0 failed
python -B -c "<tally; pytest.main(['tests/smoke/test_smk_028_external_send_policy_enum.py'])>"  # -> RC 0 ; 4 passed
```

**Reconciliation: 603 (tester-run final) = 599 coder M6.2P baseline (593 carried M6.2O + 6 coder regressions) + 4
official-smoke nodes (SMK-028).** Coder baseline before any patch was 593 (byte-parity with M6.2O); the isolated 1-leg
run independently confirms 4 passed. *(pytest's terminal summary is unreliable in this harness for a long run, so totals
came from an in-process `pytest_runtest_logreport` tally with `pytest.main() RC=0` — see SMOKE_RESULTS.md "On counting".)*

### 3.3 The egress crown-jewel — FAIL-007 not tripped, no egress opened (4 independent layers, boundary+security verified)

The load-bearing invariant: making the vocabulary real leaves egress **shut**, defended in **four independent layers**
(verified on the code, not assumed):
1. **`permits_external_send` returns True ONLY for `ALLOW_EXTERNAL`** (identity `is`, not `==`).
2. **Fail-closed coercion** — nothing that is not the literal `"ALLOW_EXTERNAL"` token becomes ALLOW_EXTERNAL
   (boundary P2: 24-value junk sweep all → BLOCKED_DEFAULT, never a crash).
3. **No real registry row is ALLOW_EXTERNAL** — the permit-mapping is the OPEN M6-OD-003 half; every real ACCEPTED event
   → `send_permitted=False`.
4. **Defense-in-depth** — `EXTERNAL_SEND` Final OFF + the staged transport raises `ExternalSendBlocked` unconditionally
   (an independent choke, unchanged).

Boundary: **19 outcomes (16 DEFENDED / 3 OPEN_NONGATE / 0 NOTE), 0 FAIL-007 breaches**; the egress crown-jewel verified
(P4/P7/P8/P9/P10). Security: **0** raw PII / **0** secrets / 257 files; `BLOCKED_PII` is a **RULE-014 positive** (PII-egress
governance made explicit + fail-closed). Carried M6.2O F2-6 duck-coerce intact (boundary F7-1); the pack still caps at
`OWNER_REVIEW_REQUIRED` (F7-2).

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied, no flag flipped, no egress opened. Baseline
rollback = **delete the `04-artifacts/impl/M6.2P/` tree** (M6.2O untouched, carried byte-identical). Per change:

| Change | Rollback |
|---|---|
| `models/consumed.py` (+`ExternalSendPolicy` enum; `EventRegistryRow.external_send_policy` retype) | **scoped revert** to M6.2O bytes (restores the raw `Optional[str]` token) |
| `registry/validator.py` (+`_resolve_send_policy`; typed `permits_external_send`; `validate()` coerce+gate; enum import) | **scoped revert** to M6.2O bytes (restores the hard-False `permits_external_send`) |
| **New test** — `tests/test_m6_2p_external_send_policy.py` (+ the official `tests/smoke/test_smk_028_*.py` + `TEST_MANIFEST.md`) | delete the files |
| **Migration** | **none added** (migrations stay `0001–0013`) — nothing to unwind |
| **Config flag** | **none** — `config.py` byte-identical to M6.2O |
| **Boundary / security analysis-only writes** (`M6.2P_boundary.md`, `M6.2P_security.md`, harness/scanner scripts) | delete; both recorded "no source modified" |

A revert restores the raw-token / hard-False behaviour — which **permits no more egress than the enum does** (both fail
closed). No posture value was ever written; nothing to revert on `global_gateway_state` / `production_flag` /
`external_send`.

---

## 5. Decision deltas & governance

### 5.1 The crux — M6-OD-003 is now split; only the signed half is adopted (top-0.1% lens)

The dominant failure mode of this slice is letting "owner-signed external_send_policy enum adopted" read as "external
send now enabled". It is not, and the runbook states so plainly:
- **Vocabulary half — SIGNED (QĐ-1, 2026-09-07, chief-confirmed).** The 4-value `ExternalSendPolicy` is an owner-ratified
  decision; M6.2P adopts it faithfully as typed, fail-closed code (RULE-018 — invents nothing). This is honest,
  incremental progress on M6-OD-003.
- **Permit-mapping + Pixel/CAPI/Offline field-hash half — stays OPEN** (privacy/legal, Sếp). **No event is classified
  ALLOW_EXTERNAL by this slice**, `EXTERNAL_SEND` stays Final OFF, and egress is airtight across the four layers (§3.3).
- **Disposition:** not BLOCKED (the signed half is adopted correctly, opens no egress, `production_flag` OFF, review
  completes cleanly), but the OPEN half is a **HARD forward gate** — no event may be ALLOW_EXTERNAL and no real egress
  may open until owner/privacy-legal decide the permit-mapping + hash policy. The exit judge **M6-P2409** must confirm
  no registry row is ALLOW_EXTERNAL and `EXTERNAL_SEND` stays Final OFF. **The residual risk sits in the decision, not
  the code.**

### 5.2 Positives (worth the Judge's note)

- **`BLOCKED_PII` is a RULE-014 positive:** a category can now be typed "blocked because it carries PII" — PII-egress
  governance is explicit + fail-closed, strengthening the posture vs the prior raw `Optional[str]` (which could be any
  string and had no typed "blocked-for-PII" concept).
- **The gate is non-vacuous:** proven genuinely True for an ALLOW_EXTERNAL control row (not a dead hard-False), yet no
  real row is ALLOW_EXTERNAL and `EXTERNAL_SEND` is OFF — so the vocabulary is real *and* egress stays shut.
- **Net egress-governance improvement:** a raw token becomes a typed enum with fail-closed coercion, owner-ratified and
  un-forgeable toward "allow".

### 5.3 Residuals (armed-not-fired; `external_send_policy` is registry-SOURCED from M3, not channel-reachable)

- **M6-OD-003 permit-mapping + field-hash (PRIMARY HARD forward gate; owner + exit judge).** §5.1 — no event
  ALLOW_EXTERNAL, `EXTERNAL_SEND` Final OFF until owner/privacy-legal decide. A **decision, not a code fix**.
- **N1 — narrow-except coercion-totality (NEW robustness; CODER).** `_resolve_send_policy`'s `except (ValueError,
  TypeError)` (and the mirrored `_resolve_sensitivity`) is narrower than the consent-coercion's bare `except Exception`;
  a hostile dunder (`__hash__`/`__eq__`/`.strip()`) raising a non-`(ValueError,TypeError)` exception propagates uncaught
  → the coercion **crashes**. It **fails LOUD, never open-toward-send** (never ALLOW_EXTERNAL, no permit, no egress) and
  is **not channel-reachable** (registry-sourced tokens, not crafted objects). **Fix:** broaden **both** coercions to
  `except Exception → fail-closed default` (mirror-parity).
- **P6 / N2 — intended token coercion (no action).** A value that IS `"ALLOW_EXTERNAL"` (str-subclass / hostile-`__eq__`
  / a foreign enum with that value) coerces to ALLOW_EXTERNAL — the **intended** coercion of the genuine owner-signed
  token; the fail-closed direction is unaffected (no non-`"ALLOW_EXTERNAL"` value becomes ALLOW_EXTERNAL). Trusted-input
  only; a str-exact-type guard would wrongly reject a valid token. Matches the coder's 1-candidate/0-surviving self-review.
- **Carried (unaffected by this slice; M6.2P touches only the enum):** the **F-SEC-2O-1 masking-scope family**
  (`messenger_thread_id` / `live_session_id` / `comment_id` + `SmokeResult.status` still export raw → **M6-OD-012**);
  **B1 psid_hash** real-pepper + privacy/legal (**M6-OD-003**, carried from M6.2O); **F-EVID-4/5/6**, **known_refs
  untyped param**, **F-GROWTH-1 + reactivation N6** consent subject-bind → CODER/owner.

### 5.4 Doc-sync: the contract annotation is already reconciled (source-vs-source note)

The coder (IMPLEMENTATION_NOTES §5) and security (§8) reports say `CONTRACT_EVENT_REGISTRY.contract.yaml` "still
annotates `external_send_policy` 'values OPEN; NOT invented'" and should be reconciled. **That was a pre-reconciliation
view.** Per the PM index (M6-P2407) checked against the **current file** + **SCHEMA_CHANGELOG row 20 (2026-09-08)**: the
`external_send_policy` **field annotation is already reconciled** (contract lines 78-79 — vocabulary SIGNED 2026-09-07,
RULE-018; only the permit-mapping/hash half marked OPEN). The **current canonical file wins** over the earlier reports;
the only residual is a **stale historical note at contract line 137** (non-blocking operator hygiene).

### 5.5 New owner decision + housekeeping

- **QĐ-1 (2026-09-07) — M6-OD-003 PARTIAL:** the enum vocabulary half is owner-signed (evidence
  `decisions/M6-OD-003-enum.json`, `decisions/XAC_NHAN_QD1-QD3_2026-09-07.md`); the permit-mapping + hash half stays OPEN.
- **Operator/PM hygiene (non-blocking):** reconcile the **stale historical note at contract line 137**; record **QĐ-1
  (M6-OD-003 PARTIAL)** in `DECISION_REGISTER.md`; and (standing across M6.2L/M6.2M/M6.2O) register **M6-OD-013** +
  **M6-OD-014** + the **M5 `PSID_HASH_POLICY_M5_TMP`** dependency as DECISION_REGISTER rows; reconcile the stale ENTRY-004 row.

### 5.6 Immutable posture & forward gates

`config.py` byte-identical to M6.2O (sha256 `911b3238…`); `global_gateway_state=BLOCKED`, `production_flag=OFF`,
`external_send=OFF` (**Final**), `is_external_send_enabled()` False, `HASH_POLICY_RATIFIED=False`, all flags `False`,
`live_migrations=false` — unchanged. **M6-P1000 + M6-P1309 verdicts remain BLOCKED (not converted)**; the M6.2G/H/I/J +
M6-OD-011/012 + **M6-OD-003 (permit/hash half)** forward conditions remain hard gates. Out of scope (untouched): the M3
registry-runtime SOURCE + reader adapter (event-registry-feed.v1 / ENTRY-003 V221); the `data_sensitivity` enum
reconciliation (M6 {PUBLIC,INTERNAL,PII} vs M3 {SENSITIVE,INTERNAL}); the Sếp permit-mapping + hash policy; any flag flip.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Code (staged, patched)** | 2 files: `models/consumed.py` (+`ExternalSendPolicy` enum; `EventRegistryRow` retype), `registry/validator.py` (+`_resolve_send_policy` fail-closed coercion; typed `permits_external_send` → True only for ALLOW_EXTERNAL; `validate()` coerce+gate). |
| **Tests (staged, new)** | 6 coder regressions + 1 official smoke (SMK-028, 4 nodes). Suite **593 → 603** (+6 coder, +4 smoke). |
| **Migration** | **none** (migrations stay `0001–0013`, RULE-018 — no new table). |
| **Config flag** | **none**; `config.py` byte-identical to M6.2O. |
| **Contract** | CTR-003 DRAFT_LOCKED → satisfied. The `CONTRACT_EVENT_REGISTRY` `external_send_policy` field annotation is **already reconciled** (lines 78-79; SCHEMA_CHANGELOG row 20, 2026-09-08); residual = the stale historical note at line 137 (hygiene). No new contract. |
| **Owner decisions** | **QĐ-1 (2026-09-07): M6-OD-003 PARTIAL** — enum vocabulary SIGNED (adopted here); permit-mapping + hash half OPEN (HARD forward gate). M6-OD-012 masking family carried. |
| **Vocabulary delta** | raw `Optional[str]` external_send_policy → typed `ExternalSendPolicy` enum with `BLOCKED_PII`/`BLOCKED_DEFAULT` fail-closed defaults (RULE-014 positive). |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted). |
| **Posture** | unchanged — `BLOCKED / OFF / OFF` (Final), all flags `False`, `config.py` byte-identical. **No egress opened; no event ALLOW_EXTERNAL.** |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED`; **egress remains closed** (M6-OD-003 permit/hash half forward). |

---

## 7. Handoff

- **Immediate next (JUDGE, fresh session): M6-P2409 `M6_2P_SLICE_GATE_JUDGE`.** Checks the 5 exit-gate legs (typed enum
  + fail-closed, SMK-028 recorded, every-prompt evidence, judge sign-off, rollback) **AND — the load-bearing confirm —
  MUST verify no registry row is classified `ALLOW_EXTERNAL` and `EXTERNAL_SEND` stays Final OFF.** Judges never modify
  what they judge. See §8.
- **OWNER (the load-bearing forward step):** **M6-OD-003 permit-mapping** (which events/fields are ALLOW_EXTERNAL) +
  the Pixel/CAPI/Offline **field-hash policy** (privacy/legal, Sếp) — no event ALLOW_EXTERNAL and no real egress until
  decided; plus **M6-OD-012** (the residual trace-join masking family) and the standing M6.2G/H/I/J + M6-OD-011 +
  B1-psid-pepper (M6-OD-003) forward conditions.
- **CODER:** broaden `_resolve_send_policy` / `_resolve_sensitivity` `except` to `Exception → fail-closed default` (N1
  coercion totality); F-EVID-4/5/6; the carried `known_refs` untyped-param robustness; F-GROWTH-1 + reactivation N6
  subject-bind; the carried M6-OD-012 masking work.
- **OPERATOR / PM (doc-sync, non-blocking):** reconcile the stale historical note at `CONTRACT_EVENT_REGISTRY` line 137;
  record QĐ-1 (M6-OD-003 PARTIAL) + M6-OD-013/014 + the M5 `PSID_HASH_POLICY_M5_TMP` dependency in `DECISION_REGISTER.md`;
  reconcile the stale ENTRY-004 row.
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF` (Final), all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2409)

1. **Read order:** `M6_2P_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2400…2406) → the two review reports
   (`M6.2P_boundary.md` §4 egress crown-jewel, `M6.2P_security.md` §4–5 egress-safety + M6-OD-003 split) →
   `SMOKE_RESULTS.md` → `IMPLEMENTATION_NOTES.md` (§4 egress-safety, §7 rollback). The 5-leg exit-gate map is index §4.
2. **What is proven (executed + verified):** the `ExternalSendPolicy` enum is fail-closed (SMK-028 4/4; boundary 24-value
   junk sweep all → BLOCKED_DEFAULT; permits only ALLOW_EXTERNAL) and opens **no egress** across four independent layers.
   Full suite **603 passed**; boundary **0** FAIL-007 breaches / 19 outcomes; security **0** raw PII/secrets / 257 files;
   `config.py` byte-identical; carried M6.2O fixes intact.
3. **Your load-bearing confirm (the crux):** M6-OD-003 is **PARTIAL** — the vocabulary half is signed (QĐ-1) and adopted;
   the permit-mapping + hash half stays OPEN. **Confirm no registry row is `ALLOW_EXTERNAL` and `EXTERNAL_SEND` stays
   Final OFF.** "Owner-signed enum adopted" is **not** "external send enabled" — the slice opens nothing.
4. **What is NOT yet closed:** exit items **3 & 4** are PENDING only because this docs prompt (M6-P2408) and the judge
   (M6-P2409) are the last two to run. Legs 1, 2, 5 (rollback) are MET. The N1 narrow-except robustness (fails loud, not
   open) + P6/N2 intended token coercion are armed-not-fired, none channel-reachable.
5. **A source-vs-source note (already reconciled):** the coder/security reports flag the `CONTRACT_EVENT_REGISTRY`
   annotation as still "values OPEN", but that was pre-reconciliation — the current file (lines 78-79) + SCHEMA_CHANGELOG
   row 20 (2026-09-08) show the field annotation is reconciled; the canonical file wins; only the stale historical note at
   line 137 remains (operator hygiene, §5.4).
6. **Boundary integrity of this docs prompt (M6-P2408):** `analysis_only` — it read the band evidence and wrote only this
   runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it documented,
   opened no egress, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
   `external_send=OFF` (Final) — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
