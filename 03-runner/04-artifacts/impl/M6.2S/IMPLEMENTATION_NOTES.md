# M6.2S IMPLEMENTATION_NOTES — Registry-feed reader (event-registry-feed.v1, TODO(contract), fail-closed) (STAGED)

**Prompt**: M6-P2702 (`M6_2S_CODER_IMPLEMENT`) · **Role**: CODER · **Mode**: `implement` · **Gate**: EVIDENCE_GATE
**Slice**: M6.2S — the M6-side **registry-feed reader adapter**: consume a **PROPOSED** `event-registry-feed.v1` as a
value object / dict (**NOT a live HTTP call**), staleness-safe by monotonic `registry_version` and fail-closed on
every unknown, **reusing the M6.2P `ExternalSendPolicy` enum** + the validator's fail-closed coercers. Cumulative
superset of M6.2R. **Everything STAGED** (mock feed; the live M3 client is the out-of-scope seam). Reading the
registry **opens NO egress**.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`. `app/config.py` **unchanged** (sha256[:16] = `911b32381368f355`) —
> and `models/consumed.py` + `registry/validator.py` are **byte-identical to M6.2R** (reuse-only, no change). No
> self-cert (RULE-015); the runner gate + JUDGE (M6-P2709) decide.

Ledger verified before acting: **M6-P2702 = RUNNING** (row 262), dependency **M6-P2701 = PASS** (row 261). Built to
the approved `PLAN.md` item-by-item; owner input **M6-OD-018** DECIDED.

## 1. Carry-forward + baseline discipline

- Carried the whole **M6.2R** tree byte-identical into `04-artifacts/impl/M6.2S/` (excluded caches + the prior
  `PLAN.md`/`IMPLEMENTATION_NOTES.md`; kept this slice's `PLAN.md`). Result: **247 .py = 247 .py, 16 .sql = 16 .sql**.
- **Baseline + parity BEFORE any patch**: `PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q` →
  **M6.2R 658 passed == M6.2S carried 658 passed** (0 fail/error/skip), identical → clean byte-identical carry.
- **After the build**: full suite **688 passed, 0 fail / 0 error / 0 skip** (658 baseline + 30 new reader tests). The
  gate invariant **baseline ≤ final (658 ≤ 688)** holds; no carried test dropped. No test was skipped/relaxed/deleted.

## 2. What was built (2 new modules + 1 regression; NO migration, NO gate change, NO HTTP client, NO config change)

| File | What |
|---|---|
| **new** `app/measurement/models/registry_feed.py` | `PROPOSED_FEED_CONTRACT`/`PROPOSED_FEED_ENDPOINT` + `TODO(contract)` markers (final name/shape is chief-issued) · frozen `RegistryFeedRow{event_code, data_sensitivity: DataSensitivity, external_send_policy: ExternalSendPolicy, is_active: bool, event_group?, domain?, updated_at?}` reusing the M6.2P `DataSensitivity` + `ExternalSendPolicy` enums (imported from `models.consumed`) · frozen `RegistryFeed{registry_version, rows}` · `to_public()` (governance metadata, not PII) |
| **new** `app/measurement/adapters/registry_feed_reader.py` | `RegistryFeedApplyResult` + `RegistryFeedReader.apply()` — fail-closed feed guards (None / not-a-Mapping / bad `registry_version` [**a `bool` is not an int**] / bad `events` / **a non-Mapping row** / missing/blank `event_code` → `feed_error:<kind>`, state UNCHANGED); staleness-safe monotonic `registry_version` (≤ current → `stale`, no downgrade); parse ALL rows first then apply (never half-applied; version bumps only on a fully-valid feed) reusing `registry.validator._resolve_send_policy` (unknown → `BLOCKED_DEFAULT`) + `_resolve_sensitivity` (None/unknown/`SENSITIVE` → `PII`), `is_active` strict bool → fail-closed `False`, optional metadata → `None`; `current_registry_version()`/`rows()`/`get()`. **No HTTP import, no live endpoint, no egress surface** |
| **new** `tests/test_m6_2s_registry_feed_reader.py` | 30 cases covering SMK-031's four fixtures (valid / stale / unknown-token / feed-error) + the two red-team regressions (non-Mapping row, bool version) + delta-upsert / de-registration + no-live-endpoint import + `EXTERNAL_SEND` OFF + no raw PII |

- **Leg 1 (proposed-shape parse + TODO(contract))** — `RegistryFeedRow` reuses `ExternalSendPolicy`; the
  `PROPOSED_FEED_CONTRACT`/`_ENDPOINT` + module `TODO(contract)` marker flag the proposed name/shape; optional
  metadata absent → `None` (never invented).
- **Leg 2 (staleness-safe)** — monotonic `current_registry_version`; `registry_version ≤ current` → `stale` (no
  downgrade); the version bumps only on a fully-valid apply, so a malformed higher-version feed cannot poison
  staleness (regression-verified).
- **Leg 3 (fail-closed + no live call + no egress)** — unknown `external_send_policy` → `BLOCKED_DEFAULT`,
  unknown/`SENSITIVE` `data_sensitivity` → `PII`; feed error → not applied; the fail-closed path never fabricates
  `ALLOW_EXTERNAL`; the reader has no live-endpoint import and no egress surface; `EXTERNAL_SEND` stays `OFF`.

## 3. Plan deltas (documented per the prompt)

1. **Delta-UPSERT (`since_version`) merge semantics** — the plan said "store rows" (ambiguous). Since the endpoint
   is `GET /api/v1/internal/event-registry?**since_version={n}**` (a **delta**), a valid feed **UPSERTs** its rows
   onto the prior snapshot (keyed by `event_code`), never dropping rows the delta omits. This is the faithful
   `since_version` reading and is **more fail-closed** than replace-snapshot: a de-registered event arrives as
   `is_active=False` and stays **present-but-inactive** (never false-ALLOWed, honoring ARCH_BASELINE §1.1's
   asymmetric-staleness finding), rather than being silently dropped. **Why safe** (impl red-team: this delta was
   raised MINOR then **REFUTED** by an independent skeptic running the real code): staleness is by monotonic
   `registry_version`, so a stale feed is rejected whole — no stale rows ever enter; within an applied
   higher-version feed the rows are the authoritative changes. `TODO(contract)`: explicit tombstone/removal
   semantics await chief finalization. A regression asserts a prior row survives a later delta that omits it.
2. **Baseline figure correction (647 → 658)** — `PLAN.md` (§0/§1/§5) cites the M6.2R baseline as **647**; that was
   M6.2R's count at the end of its *implement* prompt, **before** the M6.2R TESTER added the official SMK-030 smoke.
   The **SIGNED** M6.2R tree actually collects **658** — the real baseline used for parity here (658 == 658 before
   patch; 688 after). The plan number is stale by 11; the implementation and the parity check use the **real 658**.
   (Surfaced by the impl red-team as a NIT; the SIGNED plan is left unedited to preserve the audit trail — the
   correct figures are recorded here.)

The impl red-team's **failclosed-correctness dimension returned CLEAN** (no findings): the coercion, staleness,
feed-error handling, delta-upsert, and boundary all verified fail-closed on the running code.

## 4. Backward-compat (verified green, not asserted)

- **Reuse, not change** → `models/consumed.py` (`ExternalSendPolicy`/`DataSensitivity`) + `registry/validator.py`
  (`_resolve_send_policy`/`_resolve_sensitivity`/`permits_external_send`) + `config.py` are **byte-identical** to
  M6.2R (sha256 checked); SMK-028 (external_send_policy enum) + SMK-001 (event-registry validation) + every carried
  registry/consumed test stay green (part of the 688). The reader adds no field to `EventRegistryRow` (it uses a new
  `RegistryFeedRow`).
- **New modules + new test only** → no carried test imports the feed model/reader; nothing to break. Migrations stay
  `0001–0016`.

## 5. Rollback (staged only — M6.2R untouched)

- **Whole slice**: delete the `04-artifacts/impl/M6.2S/` tree. M6.2R is byte-identical and untouched; no live
  migration to unwind (`live_migrations=false`).
- **Per item**: the three new files → delete. **No carried file is edited** (reuse-only imports; no gate/config/
  migration change), so there is nothing to scoped-revert.

## 6. Scope, boundary & governance

- **In scope**: the feed reader/parser (proposed shape → typed rows) + staleness-safe monotonic version + fail-closed
  resolution. **Out of scope (untouched)**: the live HTTP client to the M3 endpoint (ENTRY-003 V221 pending); the
  two-enum reconciliation (M6 `{PUBLIC,INTERNAL,PII}` vs M3 `{SENSITIVE,INTERNAL}`); the Sếp permit-mapping /
  hash policy (M6-OD-003 OPEN). No flag flip; posture stays OFF/BLOCKED/OFF.
- **Boundary intact**: M6 **reads** the Core registry feed fail-closed **for its own validation**; it does **not**
  write/invent an event, reconcile the Core enum, decide the permit-mapping, send CRM, or open egress (RULE-001/018).
  The reader **classifies** `external_send_policy` (unknown → `BLOCKED_DEFAULT`, never a fabricated `ALLOW_EXTERNAL`)
  and opens **no egress**; `EXTERNAL_SEND` stays `OFF`. The feed is governance metadata, not customer PII (RULE-014);
  no secret / no endpoint auth (FAIL-008). `M6-P1000` / `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, NOT resolved)**: M6-OD-003 (permit-mapping / hash) OPEN governs which events are
  actually `ALLOW_EXTERNAL`-permitted (not this reader); the live M3 endpoint + the two-enum reconciliation + the
  `TODO(contract)` finalization + M6-OD-011 server-bind/go-live remain hard gates before any **live** registry pull /
  real egress.

## 7. Verification commands

```
# carry (excludes caches + prior PLAN/NOTES); baseline + parity BEFORE patch:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # M6.2R 658 == M6.2S 658
# after build:
PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider -q     # 688 passed, 0 fail/error/skip
# reuse-only: sha256[:16] of config.py/consumed.py/validator.py identical M6.2R<->M6.2S
# migrations 0001..0016 unchanged; caches clean; reader has no HTTP/live-endpoint import; EXTERNAL_SEND OFF; PII scan clean
```

*Implemented an owner-authorized (M6-OD-018), STAGED, mock-feed registry reader that reuses the M6.2P fail-closed
vocabulary. No application flag flipped, no migration applied, no live HTTP call, no egress opened, no owner decision
resolved, no gate/config change. The runner gate + JUDGE decide (RULE-015).*
