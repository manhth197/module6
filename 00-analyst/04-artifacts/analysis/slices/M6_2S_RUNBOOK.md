# M6.2S — Slice Runbook — Registry-feed reader (event-registry-feed.v1, TODO(contract), staleness-safe + fail-closed)

> **Status: STAGED — the registry-feed reader is built and fail-closed, but it is UNWIRED, reads a mock of a not-final
> contract, and it opens no egress.**
> M6.2S adds the M6-side **registry-feed reader adapter** (chief RELAY_V221 §2.4, M6-OD-018): `RegistryFeedReader.apply()`
> consumes a **PROPOSED** `event-registry-feed.v1` (a value object / dict — **not a live HTTP call**) into typed
> `RegistryFeedRow`, staleness-safe by monotonic `registry_version` and fail-closed on every unknown, **reusing the M6.2P
> `ExternalSendPolicy` + `DataSensitivity` enums** and the validator's fail-closed coercers. Cumulative superset of
> M6.2R. Everything STAGED: mock feed in tests; the live M3 endpoint (`GET /api/v1/internal/event-registry?since_version={n}`,
> ENTRY-003 V221) is out of scope. **No gate/config change** — `config.py`, `models/consumed.py`, `registry/validator.py`
> are **byte-identical to M6.2R** (independently sha256-verified; `config.py` = `911b3238…`); migrations stay `0001–0016`,
> none applied.
>
> **Read the three honesty points first — a naive "reader built + parses the feed + staleness-safe + 716 green" reading
> would imply M6 now ingests the M3 registry and governs external-send policy live, which is false:**
> 1. **The reader is UNWIRED, and the one FAIL-008 residual (P2 / F-FEED-PII) is contained *only* by the absence of a
>    durable sink (N1).** `RegistryFeedRow.to_public()` exports the free-text governance metadata
>    (`event_code`/`event_group`/`domain`/`updated_at`) **verbatim**, with no masking choke; a contract-violating M3 feed
>    that smuggled a PII-shaped value into `domain`/`event_group` would export it raw. It is armed-not-fired **only**
>    because (a) the feed is a trusted Core-owned governance source, (b) `PII_FIELDS` has no `RegistryFeedRow` key (empty
>    by contract), and (c) **no non-test `app/` module imports the reader or the feed models** (grep-clean). It flips to a
>    **live FAIL-008** the moment any `app/` module serializes `to_public` or the live M3 seam is wired. **The right fix
>    is an input-side PII-shape reject at parse, NOT export-masking** — these are governance identifiers that must export
>    as-is (masking `event_code`/`domain` would break their purpose, the same reasoning as `campaign_id`), so this is the
>    *opposite* resolution from the M6-OD-012 decision-export masking family, and must not be conflated with it. Same
>    adapter-ahead-of-wiring shape as M6.2R's mapper (N8).
> 2. **This proves a MOCK of a contract that is not final.** `TODO(contract)` marks the proposed endpoint name/shape
>    (RELAY_V221 pending); the two-enum reconciliation (M6 `{PUBLIC,INTERNAL,PII}` vs M3 `{SENSITIVE,INTERNAL}`) and the
>    tombstone/removal semantics are **Core/chief-owned and OPEN**. The reader consumes fail-closed but **reconciles
>    nothing** — and per RULE-001 it never self-resolves Core registry semantics (two residuals below route to CHIEF, not
>    to a local fix).
> 3. **Classifying `external_send_policy` is NOT permitting egress.** The reader faithfully reads a Core-classified
>    `ALLOW_EXTERNAL` row (RS5 — correct per RULE-001, M6 does not override the Core registry) yet opens **no egress**: no
>    send verb, `external_send` Final OFF, and *which* events are permit-mapped to `ALLOW_EXTERNAL` is the OPEN
>    **M6-OD-003** privacy/legal half. So a Core-set `ALLOW_EXTERNAL` row is **inert** here.
>
> **What is genuinely good (credited, not rosy):** the reader is fail-closed at **every** layer — feed-level guards
> (None / not-a-Mapping / bad `registry_version` [a `bool` is not an int] / bad `events` / non-Mapping row / missing-blank
> `event_code` → `feed_error:<kind>`, state **unchanged**), staleness no-downgrade + no-poison (parse-all-first; version
> bumps only on a fully-valid feed), all-or-nothing **for malformed rows** (the upsert phase is not exception-atomic
> under a hostile `__hash__` — the in-process-only N2 residual, §5.5), unknown `external_send_policy` → `BLOCKED_DEFAULT`,
> unknown / `SENSITIVE` `data_sensitivity` → `PII` (most restrictive), `is_active` strict-bool, optional metadata →
> `None` (never invented). It is **reuse, not change** (no new enum; `consumed.py`/`validator.py` byte-identical). The plan red-team
> fixed **2 gaps pre-code** (non-Mapping row → `feed_error:row_not_mapping`; `bool` version → `feed_error:bad_version`);
> the impl red-team's fail-closed-correctness dimension returned **CLEAN** and **refuted** a false delta-upsert MINOR. And
> the delta-UPSERT semantics are **more** fail-closed than replace-snapshot: a de-registered event arrives as
> `is_active=False` and stays present-but-inactive (never false-`ALLOW`ed).
>
> Posture immutable: `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
> `is_external_send_enabled()=False`, `live_migrations=false`. `M6-P1000` + `M6-P1309` remain **BLOCKED (not converted)**;
> the pack still tops at `OWNER_REVIEW_REQUIRED`. Evidence: full staged suite **716 passed / 0 failed, rc 0**; SMK-031
> PASS 28/28; boundary **0** in-scope FAIL-007/008 breaches / 34 recorded; security **0** raw PII / **0** secrets (incl.
> **0** `client_secret`) / 281 files. Next: slice-gate Judge **M6-P2709**.

| Field | Value |
|---|---|
| Slice | **M6.2S** — Registry-feed reader (event-registry-feed.v1, TODO(contract), fail-closed); post-pilot; depends on M6.2R; chief RELAY_V221_M3_2026-09-10 §2.4 + QĐ-B registry branch (PhucApu canonical, V221, signed 2026-09-08) |
| Prompt (this doc) | **M6-P2708** — `M6_2S_DOCS` (ANALYST_ARCHITECT, `analysis_only`, EVIDENCE_GATE) |
| Rules / fail gates in scope | **RULE-001** (Core owns the event registry — M6 never writes/invents/reconciles) · **RULE-014** (no raw PII) · **RULE-015** (no self-cert) · **FAIL-007** (no false progress) · **FAIL-008** (raw secret / PII on a durable/export surface) |
| Smoke in scope | **M6-SMK-031** (valid parse / stale-no-downgrade / unknown-token fail-closed / feed-error) — proposed HARDENING, **executed 28/28** (not owner-waived) |
| Contract | M6-CTR-003 (event-registry validation) DRAFT_LOCKED → **resolved-for-entry**; the proposed feed name/shape carry `TODO(contract)` (final = chief-issued) |
| Owner inputs (DECIDED) | **M6-OD-018** (registry-feed reader consumer — DECIDED 2026-09-10, owner+tech-lead; artifact `M6-OD-018.json` filed) |

---

## 1. What this slice built (staged under `04-artifacts/impl/M6.2S/`)

M6.2S carries the **entire M6.2R tree byte-identical** (baseline verified green **before any patch: 658 passed**,
byte-parity, `247 .py == 247 .py`, `16 .sql == 16 .sql`) and adds **2 new modules + 1 regression test** (the tester then
adds the official SMK-031 smoke). **No gate/config change** (`config.py`/`consumed.py`/`validator.py` byte-identical —
independently sha256-verified this turn), **no migration** (still `0001–0016`), **no HTTP client**, **no new secret**,
**no edited carried application/gate file** (the only carried-file delta is `tests/TEST_MANIFEST.md` — smoke
registration; see §4).

| Piece | What | File |
|---|---|---|
| **Feed model (M6-OD-018)** | `PROPOSED_FEED_CONTRACT`/`PROPOSED_FEED_ENDPOINT` + module `TODO(contract)` markers (final name/shape is chief-issued) · frozen `RegistryFeedRow{event_code, data_sensitivity: DataSensitivity, external_send_policy: ExternalSendPolicy, is_active: bool, event_group?, domain?, updated_at?}` **reusing** the M6.2P `DataSensitivity` + `ExternalSendPolicy` enums (imported from `models.consumed`) · frozen `RegistryFeed{registry_version, rows}` · `to_public()` (governance metadata, not PII) | **new** `app/measurement/models/registry_feed.py` |
| **Reader adapter** | `RegistryFeedReader.apply()` — fail-closed feed guards (None / not-a-Mapping / bad `registry_version` [`bool` is not an int] / bad `events` / non-Mapping row / missing-blank `event_code` → `feed_error:<kind>`, state UNCHANGED); staleness-safe monotonic `registry_version` (≤ current → `stale`, no downgrade); **parse ALL rows first, then upsert** (never half-applied; version bumps only on a fully-valid feed); reuses `validator._resolve_send_policy` (unknown → `BLOCKED_DEFAULT`) + `_resolve_sensitivity` (None/unknown/`SENSITIVE` → `PII`); `is_active` strict-bool; optional metadata → `None`; `current_registry_version()`/`rows()`/`get()`. **No HTTP import, no live endpoint, no egress surface.** | **new** `app/measurement/adapters/registry_feed_reader.py` |
| **Regression test** | 30 cases: SMK-031's four fixtures (valid / stale / unknown-token / feed-error) + the two red-team regressions (non-Mapping row, bool version) + delta-upsert / de-registration + no-live-endpoint import + `EXTERNAL_SEND` OFF + no raw PII | **new** `tests/test_m6_2s_registry_feed_reader.py` |

The three in-scope legs (per the slice done-gate), all proven staged:

| Leg | What | Gate/rule |
|---|---|---|
| **1 — proposed-shape parse + `TODO(contract)`** | `RegistryFeedRow` reuses `ExternalSendPolicy`; `PROPOSED_FEED_CONTRACT`/`_ENDPOINT` + a module `TODO(contract)` marker flag the proposed name/shape; optional metadata absent → `None` (never invented, never a fabricated field). | RULE-001 / M6-OD-018 |
| **2 — staleness-safe by `registry_version`** | monotonic `current_registry_version`; `registry_version ≤ current` → `stale` (no downgrade); the version bumps only on a fully-valid apply, so a malformed higher-version feed cannot poison staleness (regression-verified). | FAIL-007 |
| **3 — fail-closed + no live call + no egress** | unknown `external_send_policy` → `BLOCKED_DEFAULT`, unknown/`SENSITIVE` `data_sensitivity` → `PII`; feed error → not applied; the path never fabricates `ALLOW_EXTERNAL`; the reader has no live-endpoint import and no egress surface; `EXTERNAL_SEND` stays `OFF`. | **FAIL-008** / RULE-001 |

---

## 2. Operate

M6.2S is a pure read/parse adapter; there is no live call, no network, no egress, and **no caller in the shipped path**
(see §5.1). The staged flow the tests exercise:

1. **Obtain a feed (STAGED).** A caller constructs a `RegistryFeed` value object, or passes a dict of the proposed shape
   `{registry_version, events:[{event_code, event_group, domain, data_sensitivity, external_send_policy, is_active,
   updated_at}]}`. In this slice the feed is **built in-test** — the live M3 endpoint
   (`GET /api/v1/internal/event-registry?since_version={n}`, ENTRY-003 V221) is **not built**. The reader imports no
   HTTP client / transport surface.
2. **Apply, fail-closed.** `RegistryFeedReader.apply(feed)` runs the feed-level guards (any bad shape → `feed_error:<kind>`,
   state **unchanged**), then the staleness gate (`version ≤ current` → `stale`, no downgrade), then parses **all** rows
   before upserting. Unknown `external_send_policy` → `BLOCKED_DEFAULT`; unknown/`SENSITIVE` `data_sensitivity` → `PII`;
   `is_active` strict-bool; optional metadata → `None`. The version bumps only on a fully-valid, strictly-greater feed.
3. **Delta-UPSERT (`since_version`).** A valid feed upserts its rows (keyed by `event_code`) onto the prior snapshot,
   never dropping rows the delta omits; a de-registered event arrives as `is_active=False` and stays present-but-inactive
   (never false-`ALLOW`ed). *`TODO(contract)`:* explicit tombstone/removal semantics await chief finalization (§5.3).
4. **Read.** `current_registry_version()` / `rows()` / `get()` expose the applied snapshot. **Caveat (§5.1):** nothing in
   `app/` calls this reader yet; `to_public()` echoes governance metadata verbatim and its input-side PII-reject is not
   yet built.
5. **What stays impossible:** a live M3 call, a real network, external send, a flag flip, a gate/config change, an event
   write/invent/reconcile. `config.py`/`consumed.py`/`validator.py` byte-identical to M6.2R.

---

## 3. Verify

### 3.1 The official smoke (SMK-031 PASS 28/28, executed not waived; masked `correlation_id`+`evidence_id`)

28 nodes across 9 test functions (`fixture_iv` ×11, `non_bool_is_active` ×6, `bool_registry_version` ×2,
`non_mapping_row` ×4, + 5 single functions):
- fixture i — a valid feed parses into typed `RegistryFeedRow` reusing `ExternalSendPolicy` (`INTERNAL_ONLY`,
  `BLOCKED_PII`) + `DataSensitivity`; the monotonic `current_registry_version` advances; omitted optional metadata →
  `None` (not invented).
- fixture ii — a `registry_version ≤` the last applied (equal + older) → `stale`, not applied, **no downgrade**; a
  strictly-greater feed applies and delta-upserts (the prior row survives).
- malformed-higher-version neg — a malformed higher-version feed does not bump the version (parse-all-first), so a later
  genuine feed at that version still applies (no staleness poison).
- fixture iii — unknown `external_send_policy` → `BLOCKED_DEFAULT`; unknown + M3 `SENSITIVE` `data_sensitivity` → `PII`;
  missing → `BLOCKED_DEFAULT`/`PII`/`is_active False`; no row fabricated `ALLOW_EXTERNAL` (the member is real →
  non-vacuous).
- fixture iv ×11 — a feed error (not-a-Mapping / missing `registry_version` / missing `events` / non-int / float version
  / events-not-a-list / a row missing-or-blank `event_code`) → `feed_error:*`, state unchanged.
- non-bool `is_active` ×6, bool `registry_version` ×2, non-Mapping row ×4 — all fail-closed (`False` / `bad_version` /
  `row_not_mapping`, no crash, not half-applied).
- no-live-endpoint / posture — the reader imports no HTTP client; `EXTERNAL_SEND=="OFF"`, `PRODUCTION_FLAG=="OFF"`,
  `GLOBAL_GATEWAY_STATE=="BLOCKED"`; `to_public()` exports exactly the 7 governance fields (no customer-PII field name).
  **Caveat:** this smoke asserts the 7 field **names** only, not their **values** — a PII-shaped *value* smuggled into
  `event_group`/`domain` by a contract-violating feed passes this check and exports raw. That is exactly the P2 residual
  (§5.1); the green smoke is not a values-level PII gate.
- version edges — `registry_version` of `0` or negative resolves `stale` (only a strictly-greater version applies); a
  within-feed duplicate `event_code` is last-wins (one order entry, no crash); a valid huge version applies once then
  pins later feeds `stale` (the V2 NOTE, §5.5).

### 3.2 Full staged suite (count discipline)

```
# from 04-artifacts/impl/M6.2S/  (venv: 02-tester/.venv, python 3.12.14, pytest 8.4.2; -B, cache-free, no shell redirection)
python -B -c "<pytest_runtest_logreport tally; pytest.main(['-p','no:cacheprovider'])>"          # -> RC 0 ; 716 passed / 0 failed
python -B -c "<tally; pytest.main(['-k','test_smk_031','-p','no:cacheprovider'])>"                # -> RC 0 ; 28 passed
```

**Reconciliation: 716 (tester-run final) = 658 carried (M6.2R SIGNED) + 30 coder M6.2S regressions (→ 688 coder
baseline) + 28 official-smoke nodes (SMK-031).** Coder baseline before any patch was 658 (byte-parity with the SIGNED
M6.2R tree); the gate invariant `baseline ≤ final (658 ≤ 716)` holds, 0 carried test dropped, 0 skip; the isolated `-k`
run independently confirms 28 passed; the build-side collect-only count (M6-P2703) was also 716. **Baseline-figure note
(carried from the impl red-team):** `PLAN.md` cites the M6.2R baseline as **647** — that was M6.2R's count at the end of
its *implement* prompt, before the M6.2R tester added SMK-030; the SIGNED M6.2R tree actually collects **658**, the real
parity baseline used here. The SIGNED plan is left unedited to preserve the audit trail. *(pytest's terminal summary is
unreliable in this harness for a long run, so totals came from an in-process `pytest_runtest_logreport` tally with
`pytest.main() RC=0` — see SMOKE_RESULTS.md "On counting". Tooling note: the role guard blocks a shell command carrying
the denied-root substring `registry`, and the smoke file name contains it, so the leg was run via the full suite + an
isolated `-k` filter rather than by naming the smoke path.)*

### 3.3 The in-scope gates — FAIL-007/008 not tripped, RULE-001 held (boundary + security-verified)

- **Boundary (M6-P2705): 34 outcomes = 28 DEFENDED / 5 OPEN_NONGATE / 1 NOTE / 0 in-scope FAIL-007/008 breaches.** The
  feed-level fail-closed guards, the staleness no-downgrade + no-poison + all-or-nothing **for malformed rows** (the
  upsert phase is not exception-atomic under a hostile `__hash__` — the in-process-only N2 residual, §5.5), the
  fail-closed token resolution (no fabricated `ALLOW_EXTERNAL`, no invented vocabulary), the Core-owned
  no-write/no-reconcile/no-self-cert discipline, and the no-HTTP/no-secret/governance-only export all held under executed
  attack. Posture unchanged;
  byte-clean.
- **Security (M6-P2706): 0 raw PII / 0 real secrets / 281 files** (canonical `0/0/0/0/0`, incl. **0** `client_secret`;
  the 4 non-canonical hits are all carried from M6.2O, benign — the reader adds none). The feed is **Core-owned
  governance metadata** (event codes / groups / domains / enum tokens / ISO timestamps) — **not customer PII**. No HTTP
  client and no endpoint credential (the live M3 endpoint is not built). Posture BLOCKED/OFF/OFF unchanged.
- **Reuse-only byte-identity (independently verified this turn):** `config.py` (sha256[:16]=`911b32381368f355`),
  `models/consumed.py`, and `registry/validator.py` are **byte-identical R↔S** — no enum, coercer, gate, or config
  change. Migrations `0001–0016` unchanged.

---

## 4. Rollback (every change this slice made) — *acceptance check 1*

Staged-only and non-destructive: nothing live, no migration applied (`live_migrations=false`), no flag flipped, no
egress opened, **no carried application/gate file edited**.

| Change | Rollback |
|---|---|
| **Whole slice** | delete the `04-artifacts/impl/M6.2S/` tree — M6.2R is byte-identical and untouched; no live migration to unwind |
| **New file** — `app/measurement/models/registry_feed.py` | delete the file |
| **New file** — `app/measurement/adapters/registry_feed_reader.py` | delete the file |
| **New file** — `tests/test_m6_2s_registry_feed_reader.py` | delete the file |
| **New official smoke** — `tests/smoke/test_smk_031_registry_feed_reader_failclosed.py` (+ `tests/TEST_MANIFEST.md` delta) | delete the file / revert the manifest delta |
| **Edited carried files (application / gate code)** | **none** — `config.py`/`consumed.py`/`validator.py` byte-identical to M6.2R (each sha256-verified); nothing to scoped-revert. The only carried-file delta is `tests/TEST_MANIFEST.md` (smoke registration — see the row above) |
| **Migration** | **none** — migrations stay `0001–0016`, none applied |
| **Config flag** | **none** — `config.py` byte-identical to M6.2R (sha256 `911b3238…`) |
| **Boundary / security analysis-only writes** (`M6.2S_boundary.md`, `M6.2S_security.md`, harness/scanner scripts under `work/`) | delete; both recorded "no source modified" |
| **Tester / PM / docs analysis-only + evidence writes** (`test-reports/M6.2S/SMOKE_RESULTS.md`; `evidence/prompts/M6_2S_EVIDENCE_INDEX.md` + band `M6-P2700…2708.json`; this `analysis/slices/M6_2S_RUNBOOK.md` + `M6-P2708.json`) | delete / revert — all are analysis-only or evidence-collection writes; none modified any source, gate, migration, or `04-artifacts/state/` |

Every change is a pure additive read adapter + its tests, so deleting the three new files (and the tester's smoke)
restores M6.2R exactly. No posture value was ever written.

---

## 5. Decision deltas & governance

### 5.1 Honesty point 1 — the reader is UNWIRED, and the one FAIL-008 residual (P2) is contained only by the no-durable-sink (N1); the fix is an input-side reject, not export-masking

**No non-test `app/` module imports the reader or the feed models** (grep-clean, confirmed by boundary N1 + security §7)
— the reader's fail-closed defenses are real but **dormant in the shipped path**. `RegistryFeedRow.to_public()`
(`models/registry_feed.py`) exports the free-text governance metadata (`event_code`/`event_group`/`domain`/`updated_at`)
**verbatim**, with no masking choke — a contract-violating M3 feed that smuggled a PII-shaped value into `domain`/
`event_group` would export it raw. This is the **one FAIL-008 residual (P2 / F-FEED-PII)**, armed-not-fired **only**
because (a) the feed is a trusted Core-owned governance source, (b) `PII_FIELDS` has no `RegistryFeedRow` key (empty by
contract), and (c) `to_public` reaches **no durable sink** (N1). It flips to a **live FAIL-008** the moment any `app/`
module serializes `to_public` or the live M3 seam is wired.

**The right fix is an input-side PII-shape reject at parse, NOT export-masking** (the security review's sharpening of the
boundary's "reject or mask"): these are **governance identifiers** that must export as-is (masking `event_code`/`domain`
would break their purpose — you validate against them, the same reasoning as `campaign_id`; `PII_FIELDS['EventRegistryRow']=()`
is correct). So this is the **opposite** resolution from the M6-OD-012 decision-export masking family (`OwnerDecision`/
`AdsSpendImportDecision` `reason`/`audit_ref`) and **must not be conflated with it**. Same adapter-ahead-of-wiring shape
as M6.2R's mapper (N8). **Route (SECURITY/owner):** land the input-side PII-shape reject (an email-shaped reject on the
free-text metadata at parse, false-positive-safe) **before** wiring the reader to any durable sink / the live M3 seam.

### 5.2 Honesty point 2 — this proves a MOCK of a contract that is not final

`TODO(contract)` marks the proposed endpoint name/shape (RELAY_V221 pending). Two Core/chief-owned semantics are **OPEN**
and the reader **reconciles nothing**: the **two-enum reconciliation** (M6 `{PUBLIC,INTERNAL,PII}` vs M3
`{SENSITIVE,INTERNAL}` — the reader fail-closes `SENSITIVE` → `PII`, but the canonical mapping is Core's), and the
**tombstone/removal semantics** (the delta-upsert has no removal path — an event Core removes by *omitting* it from a
later delta is retained at its last-seen state). Per **RULE-001**, M6 surfaces these but does **not** self-resolve Core
registry semantics: N4 (untrimmed `event_code`) and N6/S-08 (tombstone-by-omission) route to **CHIEF**, not to a local
fix (§5.5). A future contract finalization is a hard gate before any live registry pull.

### 5.3 Honesty point 3 — classifying `external_send_policy` is not permitting egress

The registry feed is the path by which `external_send_policy` values (including `ALLOW_EXTERNAL`) flow into Module 6 from
the Core registry. The reader's posture is exactly right: it fail-closes unknowns to `BLOCKED_DEFAULT` (never fabricates
`ALLOW_EXTERNAL` from a junk/near-miss token), and it **faithfully reads a Core-classified `ALLOW_EXTERNAL`** row (RS5 —
correct per RULE-001; M6 classifies, it does not decide the permit-mapping). **Reading opens no egress:** no send verb,
`EXTERNAL_SEND` Final OFF, and *which* events are actually permit-mapped to `ALLOW_EXTERNAL` is the OPEN **M6-OD-003**
privacy/legal half. So even a Core-set `ALLOW_EXTERNAL` row is **inert** here — the hard egress controls remain
`EXTERNAL_SEND` OFF + the M6-OD-003 permit decision, unchanged by this slice. M6.2S also adds **no** admin/worker
authorization surface and **no** consent enforcement point (security §9); the live M3 feed endpoint's authz is
forward-only (ENTRY-003 V221 + M6-OD-011).

### 5.4 The positive worth crediting — fail-closed by construction, reuse-not-change, red-team-hardened

- **Fail-closed at every layer (boundary-executed, security-verified):** feed-level guards leave state unchanged on any
  bad shape (`bool` version excluded from int, non-Mapping row rejected, missing/blank `event_code` rejected); staleness
  is no-downgrade + no-poison (version bumps only on a fully-valid feed, parse-all-first); unknown `external_send_policy`
  → `BLOCKED_DEFAULT`, unknown/`SENSITIVE` `data_sensitivity` → `PII`, `is_active` strict-bool, optional metadata →
  `None`; no fabricated `ALLOW_EXTERNAL`, no invented vocabulary.
- **Reuse, not change (independently sha256-verified):** the reader reuses the M6.2P `ExternalSendPolicy`/`DataSensitivity`
  enums + the validator coercers; `consumed.py`/`validator.py`/`config.py` are byte-identical to M6.2R — no new enum, no
  gate/config change, migrations unchanged.
- **Red-team-hardened pre-code:** the plan red-team fixed **2 gaps before code** (non-Mapping row → `feed_error:row_not_mapping`;
  `bool` `registry_version` → `feed_error:bad_version`); the impl red-team's fail-closed-correctness dimension returned
  **CLEAN**, **refuted** a false delta-upsert MINOR (a stale feed is rejected whole, so no stale rows ever enter), and
  caught the 647→658 baseline NIT.
- **Delta-UPSERT is more fail-closed than replace-snapshot:** a since_version feed never drops omitted rows; a
  de-registered event arrives as `is_active=False` and stays present-but-inactive (never false-`ALLOW`ed), honoring the
  ARCH_BASELINE asymmetric-staleness finding.

### 5.5 Residuals (armed-not-fired; none trips an in-scope gate; reachability floor: reader reads Core governance metadata, no HTTP, no durable sink, `external_send` Final OFF)

- **P2 / F-FEED-PII (SECURITY/owner — the load-bearing one):** the `to_public` free-text echo; **input-side PII-shape
  reject before wiring**, not export-masking (§5.1). Contained today only by the no-durable-sink N1 standing watch-item.
  The one FAIL-008 residual.
- **N5 / BND-01 (CODER — carried M6.2P):** `_resolve_send_policy`/`_resolve_sensitivity` have no `isinstance(str)` gate
  before the enum value-lookup, so a hostile `__eq__`/`__hash__` object could coerce to `ALLOW_EXTERNAL`/`PUBLIC` —
  **in-process code-exec only** (a JSON feed off the wire yields `str`/`None`/`int`, all fail-closed). Add the
  `isinstance(str)` gate.
- **N2 / CRIT-02 (CODER):** the mutation phase is not exception-atomic — a 2nd-row `event_code` whose `__hash__` raises
  commits the 1st row and propagates the exception; in-process only (a dict feed yields plain `str` whose hash never
  raises). Build the upsert into local copies + swap in one guarded block.
- **N3 / CRIT-03 (CODER):** an `int` subclass with hostile `__le__` defeats the `<=` staleness guard — in-process only
  (a JSON feed gives a plain int). Canonicalize (`version = int(version)` / `type(version) is int`).
- **N4 / CRIT-04 (CHIEF/CODER — do not self-resolve, RULE-001):** `event_code` is stored **untrimmed**, so `'purchase '`
  and `'purchase'` are distinct keys — a de-registration delta for `'purchase'` misses the padded stale-active row.
  Channel-reachable in value but no in-scope trip (no egress, no durable sink); canonicalizing the key touches
  Core-owned registry semantics → CHIEF.
- **N6 / S-08 tombstone-by-omission (CHIEF — contract finalization):** the upsert has no removal path; if Core signals
  de-registration by *dropping* a row rather than resending `is_active=False`, M6 overstates liveness. `TODO(contract)`
  already flags tombstone semantics as chief-owned.
- **V2 huge-version staleness-pin (owner/contract — NOTE):** a valid huge version (e.g. `2**62`) applies once then pins
  every later genuine feed as `stale` (denial-of-progress, not an in-scope FAIL gate). Bound the version range.
- **Secret-handover forward (owner M6-OD-011):** when the live M3 client is built, its credential must be a `secret_ref`
  (never raw), and the M6.2O AST import-scan gate (no HTTP client in `app/`) will need its allow-list updated
  **deliberately** for that one client. Verified now: no endpoint credential is in the code (`client_secret` scan = 0).
  Same shape as the M6.2R ops-core client_secret handover.

### 5.6 Owner decisions + immutable posture

- **DECIDED (authorizes this slice):** **M6-OD-018** (registry-feed reader consumer — DECIDED 2026-09-10, owner+tech-lead;
  `M6-OD-018.json` filed — properly recorded, unlike the carried M6-OD-013/014 hygiene gap). M6 **reads** the Core
  registry fail-closed for its own validation; it does not write/invent/reconcile an event, decide the permit-mapping,
  send CRM, or open egress (RULE-001/018).
- **Hard forward gates (before any live registry pull / real egress):** the **live M3 endpoint** (ENTRY-003 V221) + the
  **`TODO(contract)` finalization** + the **two-enum reconciliation** + the **tombstone semantics** (Core/chief-owned);
  **M6-OD-003** (permit-mapping / hash — governs which events are `ALLOW_EXTERNAL`, not this reader); **M6-OD-011**
  (server-bind + go-live + the M3 feed credential as `secret_ref` + the import-gate allow-list update). `M6-P1000` +
  `M6-P1309` remain **BLOCKED (not converted)**.
- **Carried residuals (unaffected):** the **M6-OD-012** decision-export masking family — `OwnerDecision` (M6.2R
  F-SEC-2R-1) + `AdsSpendImportDecision` (M6.2Q MC-09) `reason`/`audit_ref` — plus the trace-id family + F-EVID-4/5/6;
  the psid_hash real-pepper + privacy/legal (M6-OD-003). *(These are the export-mask family — distinct from this slice's
  P2, whose correct fix is an input-side reject, not masking; see §5.1.)*
- **Posture (untouched):** `global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`,
  `is_external_send_enabled()=False`, all flags `False`, `live_migrations=false`; `config.py`/`consumed.py`/`validator.py`
  byte-identical to M6.2R. **Operator hygiene (non-blocking, carried):** register M6-OD-013/014 + the M5
  `PSID_HASH_POLICY_M5_TMP` dependency in `DECISION_REGISTER.md`; reconcile the stale ENTRY-004 row.

---

## 6. Changelog delta — *acceptance check 2*

| Kind | Delta this slice introduced |
|---|---|
| **Code (staged, new)** | **2 new modules + 1 regression**: `app/measurement/models/registry_feed.py` (`RegistryFeedRow`/`RegistryFeed`/`to_public` + `TODO(contract)` markers), `app/measurement/adapters/registry_feed_reader.py` (`RegistryFeedReader.apply`), `tests/test_m6_2s_registry_feed_reader.py` (30 cases). |
| **Code (staged, edited)** | **none** — no carried application/gate file edited (`consumed.py`/`validator.py`/`config.py` byte-identical, sha256-verified). |
| **Migration** | **none** — migrations stay `0001–0016`, none applied. |
| **Tests (staged)** | 30 coder regression cases + the official **SMK-031** (28 nodes = 9 functions, `fixture_iv` ×11 / `non_bool_is_active` ×6 / `bool_registry_version` ×2 / `non_mapping_row` ×4). Suite **658 → 716** (688 coder baseline + 28 smoke). |
| **Config flag / gate logic** | **none**; `config.py`/`consumed.py`/`validator.py` byte-identical to M6.2R. No new enum (reuses `ExternalSendPolicy`/`DataSensitivity`). |
| **Contract** | M6-CTR-003 (event-registry validation) DRAFT_LOCKED → resolved-for-entry; the proposed feed name/shape carry `TODO(contract)` (final = chief-issued). No new contract; the two-enum reconciliation + tombstone stay OPEN (Core/chief). |
| **Owner decisions** | **M6-OD-018** DECIDED (authorizes the slice); forward gates M6-OD-003 / M6-OD-011 + the live M3 endpoint / TODO(contract) / two-enum reconciliation carried. |
| **New capability** | the registry-feed **reader mechanism** (proposed `event-registry-feed.v1` → typed rows, staleness-safe, fail-closed, reusing the M6.2P vocabulary) — **staged and unwired** (no `app/` caller). |
| **Governance verdicts** | `M6-P1000` + `M6-P1309` **remain BLOCKED** (not converted). |
| **Posture** | unchanged — `BLOCKED / OFF / OFF`, all flags `False`, gate/config byte-identical. **No live M3 call / real network / egress / flag flip / gate change / event write-invent-reconcile.** |
| **Readiness** | assembled pack still `OWNER_REVIEW_REQUIRED`; the reader is a **mechanism, not a live registry ingest**, reads a **mock of a not-final contract**, and this slice declares no ROAS-Pass / Scale-Ready (owner-only). |

---

## 7. Handoff

**Exit-gate status (7 legs, per the slice done-gate — the full map is `M6_2S_EVIDENCE_INDEX.md`):**

| Exit leg | Status | Evidence |
|---|---|---|
| 1 — proposed-shape parse + `TODO(contract)` (reuse `ExternalSendPolicy`, invent no field) | **MET** | SMK-031 fixture i + boundary node + coder regression |
| 2 — staleness-safe by `registry_version` (monotonic, no-downgrade, current exposed) | **MET** | SMK-031 fixture ii + malformed-higher neg |
| 3 — fail-closed + no live call + no egress (unknown → `BLOCKED_DEFAULT`/`PII`, feed error → not applied, no `ALLOW_EXTERNAL`, `EXTERNAL_SEND` OFF) | **MET** | SMK-031 fixtures iii + iv + non-bool/bool-version/non-mapping negs + boundary node |
| 4 — SMK-031 executed or owner-waived | **MET** | executed 28/28, not waived |
| 5 — all slice prompts have evidence JSON | **PENDING** | M6-P2708 (this doc) + Judge M6-P2709 still to produce evidence |
| 6 — slice-gate judge sign-off PASS | **PENDING** | M6-P2709 to run (fresh session) |
| 7 — rollback documented for every change | **MET** | §4 + IMPLEMENTATION_NOTES §5 |

Legs 1–4 + 7 are MET; legs 5–6 are PENDING only because this docs prompt and the judge are the last two to run. None is FAILED/BLOCKED.

- **Immediate next (JUDGE, fresh session): M6-P2709 `M6_2S_SLICE_GATE_JUDGE`.** Checks the M6.2S exit legs (proposed-shape
  parse + `TODO(contract)`; staleness-safe no-downgrade; fail-closed unknown/feed-error, no live call, no egress; SMK-031
  executed; rollback) **AND confirms no flag flip / no live HTTP / no egress / no gate change / posture OFF-BLOCKED-OFF.**
  The judge must weigh the **three honesty points**, not the green count. Judges never modify what they judge. See §8.
- **OWNER (the load-bearing forward steps):** land the **P2 input-side PII-shape reject** (not export-masking) before
  wiring the reader to any durable sink / the live M3 seam (§5.1); **M6-OD-011** the live M3 feed credential as a
  `secret_ref` + the import-gate allow-list update before the live client; **M6-OD-003** permit-mapping stays the egress
  control; **M6-OD-012** the carried decision-export masking family; the **`TODO(contract)` finalization + two-enum
  reconciliation + tombstone semantics** (Core/chief).
- **CHIEF (RULE-001 — do not self-resolve):** `event_code` canonicalization (N4) + tombstone-by-omission semantics (N6).
- **CODER:** `isinstance(str)` gate (N5); version canonicalization (N3); mutation-phase atomicity (N2).
- **Posture carried forward unchanged:** `BLOCKED / OFF / OFF`, all flags `False`; `M6-P1000` + `M6-P1309` BLOCKED.

---

## 8. Pointers for the slice-gate Judge (M6-P2709)

1. **Read order:** `M6_2S_EVIDENCE_INDEX.md` → the 7 band JSONs (M6-P2700…2706) → the two review reports
   (`M6.2S_boundary.md` §2–4 the fail-closed feed/staleness/resolve locks + residuals, `M6.2S_security.md` §4–8 the
   fail-closed/PII-safe reader + P2 input-side-reject + RS5 classify-not-egress + the honest wiring note) →
   `SMOKE_RESULTS.md` (SMK-031 28/28) → `IMPLEMENTATION_NOTES.md` (**rollback §5**; scope/governance §6). The 7-leg
   exit-gate map is the index.
2. **What is proven (executed + boundary/security-verified):** the reader is fail-closed at every layer (feed guards,
   staleness no-downgrade + no-poison, all-or-nothing, unknown → `BLOCKED_DEFAULT`/`PII`, `is_active` strict-bool); it
   reuses the M6.2P vocabulary with `consumed.py`/`validator.py`/`config.py` byte-identical (sha256-verified); it reads a
   Core-classified `ALLOW_EXTERNAL` faithfully (RULE-001) yet opens no egress (the "all-or-nothing" guarantee is scoped
   to malformed rows — the upsert phase is not exception-atomic under a hostile `__hash__`, the in-process-only N2
   residual, §5.5). Full suite **716 passed**; SMK-031 28/28; boundary **0** in-scope FAIL-007/008 breaches / 34
   recorded; security **0** raw PII / **0** secrets (incl. **0** `client_secret`) / 281 files.
3. **The three honesty points to weigh hardest (not the green count):** **(1)** the reader is **UNWIRED** and the one
   FAIL-008 residual (P2 `to_public` free-text echo) is contained **only** by the no-durable-sink (N1); the fix is an
   **input-side reject, not export-masking** (governance identifiers must export as-is — the opposite of the M6-OD-012
   family). **(2)** this is a **mock of a not-final contract** (`TODO(contract)`, two-enum reconciliation + tombstone
   OPEN, Core/chief-owned; M6 reconciles nothing and per RULE-001 self-resolves nothing). **(3)** **classifying
   `external_send_policy` ≠ permitting egress** (a Core-set `ALLOW_EXTERNAL` row is inert; permit-mapping is the OPEN
   M6-OD-003; `EXTERNAL_SEND` Final OFF).
4. **What is NOT yet closed:** exit items **5 & 6** are PENDING only because this docs prompt (M6-P2708) and the judge
   (M6-P2709) are the last two to run. Legs 1–4 + 7 (rollback) are MET. The reader is **staged + unwired** and this slice
   declares no ROAS-Pass / Scale-Ready — the live M3 endpoint + `TODO(contract)` finalization + two-enum reconciliation +
   M6-OD-003 + M6-OD-011 stay OPEN.
5. **Confirm the posture:** no flag flip, no live M3 HTTP, no egress, no gate/config change, `config.py`/`consumed.py`/
   `validator.py` byte-identical, migrations `0001–0016` unchanged, `M6-P1000` + `M6-P1309` BLOCKED (not converted).
6. **Boundary integrity of this docs prompt (M6-P2708):** `analysis_only` — it read the band evidence and wrote only this
   runbook + its evidence JSON. It touched no `04-artifacts/state/`, marked no ledger row, modified no file it documents,
   opened no egress, computed no verdict, and declared no readiness. `global_gateway_state=BLOCKED`, `production_flag=OFF`,
   `external_send=OFF` — untouched; `M6-P1000` + `M6-P1309` remain BLOCKED (not converted).
