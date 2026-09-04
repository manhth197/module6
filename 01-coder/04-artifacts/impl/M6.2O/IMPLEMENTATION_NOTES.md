# M6.2O IMPLEMENTATION NOTES — B1 (psid_hash) + F2-6 (duck-coerce) record (STAGED)

**Kind**: coder-role **record** (documentation) of an already-staged, operator-directed out-of-band change-set — NOT
a re-implement. Consolidates B1 + F2-6 (both live under `04-artifacts/impl/M6.2O/`, the cumulative superset
**M6.2M → M6.2N (B1) → M6.2O (F2-6)**) + the C7 doc. See [PLAN.md](PLAN.md) for the file:line change-set + rollback.

> **Governance framing:** operator-directed, out-of-band (no ledger row / slice-spec yet — operator/analyst should
> register it; last ledger-RUNNING prompt is M6-P2202). Posture immutable & **verified untouched**:
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. No self-cert
> (RULE-015); the runner gate + JUDGE decide.

## 1. Minimal-change & scope (VERIFIED, not asserted)

- **`config.py` sha256 `911b3238…` — byte-identical to M6.2M** (posture constants untouched: BLOCKED/OFF/OFF + all
  flags `False`).
- **The B2/B3/B4 fix-logic files are whole-file byte-identical to M6.2M**: `evidence/gap_blockers.py` (B3),
  `dashboard/data_mart.py` + `store/measurement_event_store.py` + `growth/reads.py` (B4), `evidence/models.py`
  (B2/B3 twin), `evidence/categories.py` (B2). Neither B1 nor F2-6 touched them.
- **The A3/A4/B2/B3 fix LOGIC is unchanged inside the files B1/F2-6 did touch**: B1 edited
  `models/attribution_context.py` (28 changed lines) and `attribution/resolver.py` (13) — a diff confirms **no**
  `attribution_id` / `derive_attribution_id` / `_entry_channels` / `ads.complete` / `LIVE_ORGANIC` line changed
  (A3 trace + A4 resolver rule intact); F2-6 edited `evidence/pack_assembler.py` (16 changed lines) — a diff
  confirms **no** `_ref_valid` / `_ref_binding` / `_categories` / `standing_floor_ok` / `known_refs` line changed
  (B2 ref-authenticity + B3 floor intact); the F2-6 change is `_smokes` only.
- **Files changed** (see PLAN.md): B1 → `identity/psid_hash.py` (new), `models/attribution_context.py`,
  `attribution/resolver.py`, `funnel/funnel.py`, `funnel/models.py`, `migrations/0013_*` (new),
  `migrations/0006_*` (**comment-only** — verified: 0 non-comment/non-psid-column diff lines); F2-6 →
  `evidence/pack_assembler.py` (`_smokes`) + `tests/test_duck_smoke_recorded.py` (new). Migrations `0001–0013`.

## 2. B1 — no raw PSID anywhere; pepper is a secret (VERIFIED)

- **0 raw PSID in the durable store**: `grep` of `app/` for a raw `.psid` field / `["psid"]` key (excluding
  `psid_hash`) ⇒ **NONE**; the sole raw-psid touch is the single hash-on-ingest point
  (`resolver.resolve_live_session`, raw psid in RAM only). `as_stored()` / `to_public()` carry `psid_hash` and no
  `psid` key. The hash is one-way (HMAC-SHA256 with the **pepper as the KEY**) + deterministic + `psid_hash:`-prefixed.
- **Pepper is secret**: resolved from env `M6_PSID_HASH_PEPPER` (a secret_ref at deploy); **fail-closed in
  production** when unset (`resolve_pepper(production=True)` raises `PsidHashPolicyError`); the only pepper literal in
  source is the **labelled non-secret dev mock** (`_MOCK_PEPPER`, reachable only in a non-production posture). The
  real pepper and any raw psid are **never** committed / logged / emitted / put in evidence.
- **Migration 0006 change is comment-only** (the raw-`psid` column comment forward-noted to `psid_hash` +
  "mask() not sufficient"); `0013` is the append-only rename. Cross-module PSID joins (M6↔M3/M7) remain a separate
  owner+chief decision (out of scope).

## 3. F2-6 — `_smokes` coerces to a canonical SmokeResult (VERIFIED)

`_smokes` (`pack_assembler.py:157–170`) rebuilds every provided object as a canonical frozen `SmokeResult` from its
**fields**, so `recorded` is recomputed by `SmokeResult.recorded` (fail-closed) — a duck object with `.recorded=True`
+ blank fields can no longer mark a mandatory smoke recorded (FAIL-007). **`models.py` unchanged**; strip-waiver +
whitespace-normalize run after, unchanged. Code-exec-only, not channel-reachable, no production risk.

## 4. Acceptance checklist (all confirmed)

- [x] `grep app/ + migrations/` ⇒ **0 raw psid store** (only `psid_hash`; 0006 keeps a historical `psid` column that
  `0013` renames — the effective durable schema + the running store are `psid_hash`-only).
- [x] pepper **only** via env/secret_ref; the mock is labelled **non-secret dev-only** (never used in production).
- [x] `_smokes` **coerces** to a field-built SmokeResult (caller `.recorded` not trusted).
- [x] posture **OFF/BLOCKED** intact; `config.py` sha256 identical to M6.2M; no B2/B3/B4/A3/A4 fix-logic change;
  migration 0006 comment-only; **no raw psid/pepper** in code or evidence.
- [x] full suite **584 passed** (`PYTHONDONTWRITEBYTECODE=1 python -B`), no skips, no regress (baseline 581).

## 5. C7 (doc-only, present in this tree)

[INVARIANTS_M5_RUNTIME_CONTROLS.md](INVARIANTS_M5_RUNTIME_CONTROLS.md) records the "no `external_send`/real Graph sink
until the 4 M5 controls close + owner signs" invariant (M6 fail-closed enforcement M6-verified; the 4-control status
is M5-reported DATA). Canonical placement (Scale-Gate/go-live checklist + `_OWNER_RISK_ACCEPTANCE.md`) is
owner/analyst-owned — ANALYST/PM to merge.

## 6. Boundary of THIS record step

This step wrote **only** `PLAN.md`, this `IMPLEMENTATION_NOTES.md`, and the evidence JSON — **no impl code changed**;
no `00-spec/` or `04-artifacts/state/` touched; posture flags not flipped. The B1/F2-6 code + tests are as staged.
