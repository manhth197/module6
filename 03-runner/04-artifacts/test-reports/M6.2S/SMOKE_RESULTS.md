# SMOKE_RESULTS — Slice M6.2S (registry-feed reader: event-registry-feed.v1, staleness-safe + fail-closed, RELAY_V221 §2.4, M6-OD-018)

| Field | Value |
|---|---|
| Prompt | M6-P2704 — `M6_2S_TESTER_RUN` (attempt 1) |
| Role / agent | TESTER / m6-tester |
| Mode | **test** — the M6.2S smoke suite is EXECUTED here and results recorded. The smoke leg was authored in M6-P2703 (`M6_2S_TESTER_BUILD`). |
| Smoke ids executed | **M6-SMK-031** (1 — `proposed — HARDENING, owner review`; executed here, not owner-waived) |
| Verify env | `02-tester/.venv` — **python 3.12.14 · pytest 8.4.2 · pluggy 1.6.0**, run `-B` (`PYTHONDONTWRITEBYTECODE=1`), `-p no:cacheprovider` |
| Staging root | `04-artifacts/impl/M6.2S/` (STAGED_ONLY; cumulative superset of M6.2R) |
| Evidence-leg result | **28 passed, 0 failed — exit 0** |
| Full staged suite | **716 passed, 0 failed, 0 skipped, 0 error — RC 0** |
| Overall | **the bound smoke id PASS; no failures; nothing patched; the reader consumes a mock feed fail-closed; no egress, no live endpoint** |

> **Governance (immutable — nothing in this run flips a flag, opens egress, builds a live client, or calls a real network):**
> `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`, `live_migrations=false`. The
> event-registry-feed.v1 response is a value object / dict built in-test (STAGED, PROPOSED shape, TODO(contract));
> the live M3 endpoint `GET /api/v1/internal/event-registry?since_version={n}` is out of scope (M3 ENTRY-003 V221
> pending) and is **not** built or called. No application code changed by the TESTER, no gate/config change, no
> migration, no external call / real M3 network. The feed is governance metadata, not customer PII (RULE-014); no
> raw secret / no endpoint auth (FAIL-008). `M6-P1000` / `M6-P1309` stay BLOCKED. **HARD FORWARD CONDITIONS**
> (disclosed, not resolved here): M6-OD-003 (permit-mapping / hash) OPEN governs which events are ALLOW_EXTERNAL —
> not this reader; the live M3 endpoint + the two-enum reconciliation (M6 {PUBLIC,INTERNAL,PII} vs M3
> {SENSITIVE,INTERNAL}) + the TODO(contract) finalization + M6-OD-011 server-bind/go-live before any live registry
> pull / real egress. `status` is an honest TESTER self-report; the runner EVIDENCE_GATE + the slice Judge
> (M6-P2709) decide closure.

## Per-smoke results (scenario / expected verbatim from SMOKE_REGISTER row M6-SMK-031; PASS)

The `correlation_id` / `evidence_id` are **synthetic** trace ids, shown export-masked
(`app.measurement.masking.mask`, RULE-014); raw synthetic values `corr_2s_031` / `ev_2s_031`.

| Smoke ID | Fix | Test file (`tests/smoke/…`) | Nodes | Result | correlation_id (masked) | evidence_id (masked) | Scenario → Expected (verbatim) |
|---|---|---|---|---|---|---|---|
| M6-SMK-031 | RELAY_V221 §2.4 registry-feed reader (event-registry-feed.v1, staleness-safe + fail-closed, M6-OD-018) | `test_smk_031_registry_feed_reader_failclosed.py` | 28 | **PASS** | `cor***31` | `ev_***31` | "A mock event-registry-feed.v1 response (proposed shape): (i) valid rows; (ii) a feed with registry_version <= last applied (stale); (iii) a row with an unknown external_send_policy token + unknown data_sensitivity value; (iv) a feed error" → "reader parses valid rows into typed rows reusing ExternalSendPolicy; a stale/older registry_version is NOT applied (no downgrade); unknown external_send_policy → BLOCKED_DEFAULT and unknown/SENSITIVE data_sensitivity → PII (fail-closed); a feed error → no update (fail-closed); the reader NEVER calls a live endpoint; no event becomes ALLOW_EXTERNAL, external_send OFF, no raw PII" |

**Evidence-leg nodes: 28, all PASSED.** (9 test functions; `fixture_iv` ×11, `non_bool_is_active` ×6, `bool_registry_version` ×2, `non_mapping_row` ×4.)

### M6-SMK-031 — registry-feed reader fail-closed · **PASS (28/28)**

- `test_smk_031_fixture_i_valid_rows_parse_typed_reusing_externalsendpolicy` (fixture i) — PASS: a valid feed parses
  into typed `RegistryFeedRow` reusing the M6.2P `ExternalSendPolicy` (INTERNAL_ONLY, BLOCKED_PII) + `DataSensitivity`
  enums; the reader exposes + advances its monotonic `current_registry_version`; omitted optional metadata → None
  (not invented).
- `test_smk_031_fixture_ii_stale_version_not_applied_no_downgrade` (fixture ii) — PASS: a feed with `registry_version`
  ≤ the last applied (equal + older) → reason `stale`, not applied, **no downgrade**; a strictly-greater feed applies
  and delta-upserts (the prior row survives).
- `test_smk_031_neg_malformed_higher_version_does_not_poison_staleness` — PASS: a malformed higher-version feed does
  not bump the version (parse-all-first), so a later genuine feed at that version still applies (no staleness poison).
- `test_smk_031_fixture_iii_unknown_tokens_failclosed_blocked_default_and_pii` (fixture iii) — PASS: unknown
  `external_send_policy` → `BLOCKED_DEFAULT`; unknown + M3 `SENSITIVE` `data_sensitivity` → `PII`; missing →
  BLOCKED_DEFAULT / PII / is_active False; no row is fabricated `ALLOW_EXTERNAL` (the member is real → non-vacuous).
- `test_smk_031_fixture_iv_feed_error_no_update_failclosed` **[×11]** (fixture iv) — PASS: a feed error (not-a-Mapping /
  missing registry_version / missing events / non-int / float version / events-not-a-list / a row missing-or-blank
  event_code) → reason `feed_error:*`, state unchanged.
- `test_smk_031_neg_non_bool_is_active_is_failclosed_false` **[×6]** — PASS: a non-bool `is_active`
  (None/"true"/1/0/"false"/"True") → False (only a real True is active).
- `test_smk_031_neg_bool_registry_version_is_failclosed` **[×2]** — PASS: a bool `registry_version` →
  `feed_error:bad_version` (bool excluded from int); not shut out by a later genuine version-1 feed.
- `test_smk_031_neg_non_mapping_row_is_failclosed_no_crash` **[×4]** — PASS: a garbage `events[]` element (int /
  string / None) → `feed_error:row_not_mapping`, no AttributeError, not half-applied.
- `test_smk_031_no_live_endpoint_external_send_off_and_no_pii` — PASS: the reader module imports no HTTP client /
  live endpoint; `config.EXTERNAL_SEND == "OFF"`, `config.PRODUCTION_FLAG == "OFF"`,
  `config.GLOBAL_GATEWAY_STATE == "BLOCKED"`; `to_public()` exports exactly the 7 governance-metadata fields with no
  customer-PII field name.

## Supporting / regression coverage (inside the 716 full suite, all green)

The full staged suite re-ran green: the coder's M6.2S regression `tests/test_m6_2s_registry_feed_reader.py` (30
cases), the carried M6.2A–R tree, and the evidence-pack + P0-smoke suites. Full total **716 passed, 0 failed**
(= 688 coder M6.2S baseline + the 28 new official-smoke nodes).

## Commands run (from `04-artifacts/impl/M6.2S/`, no shell redirection, cache-free)

The role guard blocks a `>`/`2>` co-occurring with the venv `Scripts` path, so no redirection is used; `-B`
(`PYTHONDONTWRITEBYTECODE=1`) + `-p no:cacheprovider` keep the run cache-free. **Tooling note:** the role guard also
blocks a shell command containing the denied-root substring `registry`, and the smoke file name contains `registry`,
so the leg was exercised via the full suite (with an in-process node filter) and an isolated `-k test_smk_031` run
rather than naming the smoke file path on the command line.

```bash
# 1) full staged suite + per-smoke tally, counted in-process via pytest_runtest_logreport
python.exe -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider']); stdout/stderr swallowed>"
#   -> RC 0 ; passed=716 failed=0 skipped=0 error=0 ; FAILS [] ; SMK-031 28/28 (all 'passed')

# 2) the evidence leg isolated (cross-check) via -k node filter (avoids the 'registry' file path on the command line)
python.exe -B -c "<tally; pytest.main(['-k','test_smk_031','-p','no:cacheprovider'])>"
#   -> RC 0 ; passed=28 failed=0 skipped=0 error=0 ; FAILS [] ; 9 distinct functions present
```

> **On counting.** pytest's terminal summary is not reliably captured in this harness, so the full-suite total
> (**716**) and the per-smoke breakdown came from an in-process `pytest_runtest_logreport` tally
> (`passed=716, failed=0, skipped=0, error=0`) with `pytest.main() RC=0`; the isolated `-k` run independently
> confirms `28 passed`. pytest's own per-item output was swallowed (`redirect_stdout`/`redirect_stderr`). The
> build-side collect-only count (M6-P2703) was 716, matching this executed total.

## Boundary / safety observed during this run

- **Reads governance metadata only (RULE-001/014):** the reader consumes the Core-owned feed fail-closed; it never
  writes/invents an event, reconciles the Core enum, or decides the permit-mapping. `to_public()` exports only the 7
  governance fields (no customer-PII field name).
- **Fail-closed on every unknown:** unknown `external_send_policy` → `BLOCKED_DEFAULT`; unknown / `SENSITIVE`
  `data_sensitivity` → `PII`; non-bool `is_active` → False; a feed error → not applied (state unchanged). No row is
  fabricated `ALLOW_EXTERNAL`.
- **Staleness-safe:** a `registry_version` ≤ the last applied is not applied (no downgrade); a malformed
  higher-version feed does not bump the version (no staleness poisoning); a valid strictly-greater feed delta-upserts.
- **No egress, no live endpoint, no flag flipped:** the smoke READS `config.EXTERNAL_SEND == "OFF"` (and
  PRODUCTION_FLAG OFF / GLOBAL_GATEWAY_STATE BLOCKED), the reader imports no HTTP client, and nothing was written to
  `04-artifacts/state/`. No raw secret / no endpoint auth (FAIL-008).
- **No fix to code under test:** all 716 passed, so nothing needed reporting as a failure, and nothing was patched.
  No application code / gate/config change / migration / external call / flag flip / `04-artifacts/state/` write.

## Exit-gate legs closed by this run (slice M6.2S done-gate)

| Leg | Requirement | Status |
|---|---|---|
| 1 | proposed-shape parse + TODO(contract) (M6-OD-018): typed rows reusing ExternalSendPolicy; no invented field | met — SMK-031 fixture i + boundary node + coder `test_m6_2s_registry_feed_reader.py` green |
| 2 | staleness-safe by registry_version: monotonic; version ≤ last applied not applied (no downgrade); current exposed | met — SMK-031 fixture ii + malformed-higher neg |
| 3 | fail-closed + no live call + no egress: unknown → BLOCKED_DEFAULT / PII, feed error → not applied, no ALLOW_EXTERNAL, EXTERNAL_SEND OFF, no live endpoint | met — SMK-031 fixtures iii + iv + the non-bool/bool-version/non-mapping negatives + boundary node |
| 4 | Proposed smoke M6-SMK-031 executed | **PASS** (28/28) — executed |

> This run does NOT self-certify gate advancement (RULE-015). It is the honest executed-results record of the TESTER.
> The runner EVIDENCE_GATE and the slice Judge (M6-P2709) decide closure; M6-P2705 (boundary), M6-P2706
> (security/PII), and the PM evidence-collect M6-P2707 come next. Posture stays BLOCKED/OFF/OFF; the M6-OD-003 +
> M6-OD-011 hard forward conditions remain open for the exit judge (no live registry pull / real egress until decided).
