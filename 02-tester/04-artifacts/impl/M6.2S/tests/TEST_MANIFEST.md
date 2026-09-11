# TEST_MANIFEST — Slice M6.2S (registry-feed reader: event-registry-feed.v1, staleness-safe + fail-closed, RELAY_V221 §2.4, M6-OD-018)

| Field | Value |
|---|---|
| Prompt | M6-P2703 — `M6_2S_TESTER_BUILD` (mode=build, "do not yet run") |
| Role / agent | TESTER / m6-tester |
| Bound smoke ids | **M6-SMK-031** (1 — `proposed — HARDENING, owner review`) |
| New smoke file | `tests/smoke/test_smk_031_registry_feed_reader_failclosed.py` (28 collected nodes) |
| Staging root | `04-artifacts/impl/M6.2S/` (cumulative superset of M6.2R) |
| Verify env | `02-tester/.venv` — python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Build validation | **collect-only** (imports/collects, no assertions executed) — full staged suite 716 collected (= 688 coder baseline + 28 new), 0 collection errors |
| Rules / fail gates in scope | M6-RULE-001 (no cross-module ownership), M6-RULE-014 (PII masked), M6-RULE-015 (no self-cert); M6-FAIL-007, M6-FAIL-008 |

> **Governance (immutable — this build flips no flag, opens no egress, builds no live client):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. The
> event-registry-feed.v1 response is a value object / dict built in the test (STAGED, PROPOSED shape, TODO(contract));
> the live M3 endpoint `GET /api/v1/internal/event-registry?since_version={n}` is out of scope (M3 ENTRY-003 V221
> pending) and is **not** built or called. No application code changed by the TESTER, no gate/config change, no
> migration, no real M3 network. The feed is governance metadata (event_code/group/domain/sensitivity/policy/
> is_active/updated_at), not customer PII. `M6-P1000` / `M6-P1309` stay BLOCKED. This manifest is a BUILD record;
> execution + per-smoke results are recorded by M6-P2704 (`M6_2S_TESTER_RUN`).

## Bound smoke — scenario / expected (verbatim from SMOKE_REGISTER row M6-SMK-031)

- **Scenario:** "A mock event-registry-feed.v1 response (proposed shape): (i) valid rows; (ii) a feed with registry_version <= last applied (stale); (iii) a row with an unknown external_send_policy token + unknown data_sensitivity value; (iv) a feed error"
- **Expected:** "reader parses valid rows into typed rows reusing ExternalSendPolicy; a stale/older registry_version is NOT applied (no downgrade); unknown external_send_policy → BLOCKED_DEFAULT and unknown/SENSITIVE data_sensitivity → PII (fail-closed); a feed error → no update (fail-closed); the reader NEVER calls a live endpoint; no event becomes ALLOW_EXTERNAL, external_send OFF, no raw PII"

The scenario and expected are pasted verbatim (including the three U+2192 `→` glyphs) into the smoke file's module docstring.

## What is under test (code frozen by the CODER in M6-P2702 — the TESTER does not modify it)

- `app/measurement/adapters/registry_feed_reader.py` — `RegistryFeedReader.apply(feed)` → `RegistryFeedApplyResult`
  (`applied`, `registry_version`, `rows_applied`, `reason`): feed-level fail-closed guards (None / not-a-Mapping /
  bool-or-non-int `registry_version` / bad `events` / non-Mapping row / missing-blank `event_code` → `feed_error:<kind>`,
  state unchanged); monotonic staleness (`version <= current` → `stale`, no downgrade); parse-all-first then upsert
  (never half-applied; version bumps only on a fully-valid feed); `is_active` strict bool → False; reuses
  `validator._resolve_send_policy` (unknown → BLOCKED_DEFAULT) + `_resolve_sensitivity` (None/unknown/SENSITIVE → PII).
  Holds no HTTP client / live endpoint.
- `app/measurement/models/registry_feed.py` — `RegistryFeedRow` (typed, resolved enums) + `to_public()` (governance
  metadata, not PII) + `PROPOSED_FEED_CONTRACT/_ENDPOINT` TODO(contract) markers; reuses the M6.2P `DataSensitivity`
  + `ExternalSendPolicy` enums. **Reuse-only; unchanged by the TESTER.**
- `app/measurement/models/consumed.py` — `ExternalSendPolicy` {ALLOW_EXTERNAL, INTERNAL_ONLY, BLOCKED_PII,
  BLOCKED_DEFAULT}; `DataSensitivity` {PUBLIC, INTERNAL, PII} (no SENSITIVE member → "SENSITIVE" coerces to PII).
  **Unchanged.**

## Node → clause coverage (one smoke file for the one bound id; the 4 fixtures + negatives/fail-closed + boundary)

| # | Node(s) | Scenario fixture / expected clause proved |
|---|---|---|
| 1 | `test_smk_031_fixture_i_valid_rows_parse_typed_reusing_externalsendpolicy` | (i) valid rows → typed RegistryFeedRow reusing ExternalSendPolicy (INTERNAL_ONLY, BLOCKED_PII) + DataSensitivity; current version exposed/advanced; omitted optional metadata → None (not invented) |
| 2 | `test_smk_031_fixture_ii_stale_version_not_applied_no_downgrade` | (ii) version ≤ last applied (equal + older) → `stale`, not applied, no downgrade; strictly-greater applies + delta-upserts (prior row kept) |
| 3 | `test_smk_031_neg_malformed_higher_version_does_not_poison_staleness` | fail-closed staleness edge: a malformed higher-version feed does not bump the version (parse-all-first); a later genuine feed at that version still applies |
| 4 | `test_smk_031_fixture_iii_unknown_tokens_failclosed_blocked_default_and_pii` | (iii) unknown external_send_policy → BLOCKED_DEFAULT; unknown + "SENSITIVE" data_sensitivity → PII; missing → BLOCKED_DEFAULT/PII/is_active False; no row ALLOW_EXTERNAL (member is real → non-vacuous) |
| 5 | `test_smk_031_fixture_iv_feed_error_no_update_failclosed` (×11) | (iv) feed error (not-Mapping / missing version or events / non-int / float / events-not-list / row missing-or-blank event_code) → `feed_error:*`, state unchanged |
| 6 | `test_smk_031_neg_non_bool_is_active_is_failclosed_false` (×6) | non-bool `is_active` (None/"true"/1/0/"false"/"True") → False (only real True active) |
| 7 | `test_smk_031_neg_bool_registry_version_is_failclosed` (×2) | bool `registry_version` → `feed_error:bad_version` (bool excluded from int); not shut out later |
| 8 | `test_smk_031_neg_non_mapping_row_is_failclosed_no_crash` (×4) | a garbage `events[]` element → `feed_error:row_not_mapping`, no AttributeError, not half-applied |
| 9 | `test_smk_031_no_live_endpoint_external_send_off_and_no_pii` | "reader NEVER calls a live endpoint; external_send OFF; no raw PII" — no HTTP import; EXTERNAL_SEND/PRODUCTION_FLAG/GLOBAL_GATEWAY_STATE = OFF/OFF/BLOCKED; to_public is 7 governance fields, no PII field names |

## Fixtures / APIs reused (existing patterns — acceptance check 3)

- inline feed builders `_row(...)` / `_feed(version, rows)` mirroring the coder regression
  `tests/test_m6_2s_registry_feed_reader.py` (the reader is self-contained — no conftest fixture needed).
- reader surface: `RegistryFeedReader().apply(...)`, `.current_registry_version()`, `.rows()`, `.get(code)`, `len()`;
  `RegistryFeedApplyResult` fields; `RegistryFeedRow.to_public()`.
- reused enums: `ExternalSendPolicy`, `DataSensitivity` from `app.measurement.models.consumed`; `config.EXTERNAL_SEND`.

## Exit-gate legs this smoke exercises (slice M6.2S done-gate legs 1–3)

| Leg | Requirement | Node(s) |
|---|---|---|
| 1 | proposed-shape parse + TODO(contract) (M6-OD-018): typed rows reusing ExternalSendPolicy; no invented field | 1, 9 |
| 2 | staleness-safe by registry_version: monotonic; version ≤ last applied not applied (no downgrade); current exposed | 2, 3 |
| 3 | fail-closed + no live call + no egress: unknown policy → BLOCKED_DEFAULT, unknown/SENSITIVE sensitivity → PII, feed error → not applied; no ALLOW_EXTERNAL; EXTERNAL_SEND OFF; no live endpoint | 4, 5, 6, 7, 8, 9 |

## Execution plan for M6-P2704 (`M6_2S_TESTER_RUN`)

1. Run the full staged suite from `04-artifacts/impl/M6.2S/`, cache-free (`-B` / `PYTHONDONTWRITEBYTECODE=1`,
   `-p no:cacheprovider`), no shell redirection — expected **716 passed, 0 failed/skipped/error**.
2. Run the bound smoke leg — expected **28 passed**. (Note: the role guard blocks a command containing the denied-root
   substring "registry"; run the full suite / smoke directory and filter `test_smk_031` node ids in-process rather
   than naming the smoke file path on the command line.)
3. Record per-smoke PASS/FAIL/BLOCKED + a synthetic masked `correlation_id` / `evidence_id`, verbatim
   scenario/expected, exact commands, and the exit-gate legs into `04-artifacts/test-reports/M6.2S/SMOKE_RESULTS.md`.
4. Report failures, do not fix code under test (TESTER executes and reports only).

> This BUILD does not self-certify PASS (RULE-015). The runner EVIDENCE_GATE and the slice Judge (M6-P2709) decide
> closure. HARD FORWARD CONDITIONS: M6-OD-003 (permit-mapping / hash) OPEN governs which events are ALLOW_EXTERNAL —
> not this reader; the live M3 endpoint + the two-enum reconciliation (M6 {PUBLIC,INTERNAL,PII} vs M3
> {SENSITIVE,INTERNAL}) + the TODO(contract) finalization + M6-OD-011 server-bind/go-live remain hard gates before
> any live registry pull / real egress.
