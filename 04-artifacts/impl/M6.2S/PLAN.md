# M6.2S PLAN — Registry-feed reader (event-registry-feed.v1, TODO(contract), fail-closed) (STAGED, plan-only)

**Prompt**: M6-P2701 (`M6_2S_CODER_PLAN`) · **Role**: CODER · **Mode**: `plan_only` (NO code) · **Gate**: EVIDENCE_GATE
**Slice**: M6.2S — the M6-side **registry-feed reader adapter**: consume a **PROPOSED** `event-registry-feed.v1`
(`GET /api/v1/internal/event-registry?since_version={n}` → `{registry_version, events:[{event_code, event_group,
domain, data_sensitivity, external_send_policy, is_active, updated_at}]}`) as a **value object / dict** (NOT a live
HTTP call), **staleness-safe** by monotonic `registry_version` and **fail-closed** on every unknown, **reusing the
M6.2P `ExternalSendPolicy` enum** + the validator's fail-closed coercion. `TODO(contract)` marks the proposed
name/shape until chief finalizes it. Cumulative superset of M6.2R. **Everything STAGED** (mock feed in tests; the
live client is the M3 seam / ENTRY-003 V221 pending). Reading the registry **opens NO egress**.

> **Posture (immutable, this slice flips nothing):** `global_gateway_state=BLOCKED`, `production_flag=OFF`,
> `external_send=OFF`, `live_migrations=false`; `app/config.py` unchanged. No self-cert (RULE-015); the runner gate +
> JUDGE (M6-P2709) decide.

Ledger verified: **M6-P2701 = RUNNING** (row 261), dependency **M6-P2700 = SIGNED** (entry gate PASS). Target
**LOCKED**, **M6-OD-011 DECIDED**, `live_migrations=false`. Owner input **DECIDED + FILED**: **M6-OD-018**
(registry-feed reader — PROPOSED feed + `TODO(contract)`, staleness-safe monotonic version + no downgrade,
fail-closed [unknown `external_send_policy` → `BLOCKED_DEFAULT`; unknown/`SENSITIVE` `data_sensitivity` → `PII`; feed
error → not applied], reuse the M6.2P `ExternalSendPolicy` enum, NO live call, opens NO egress). Contract
**M6-CTR-003** (event_registry consumed shape) DRAFT_LOCKED. Forward conditions (NOT blockers): **M6-OD-003**
(permit-mapping / hash) OPEN; the live M3 endpoint (ENTRY-003 V221 pending); the two-enum reconciliation (M6
`{PUBLIC,INTERNAL,PII}` vs M3 `{SENSITIVE,INTERNAL}`) — all out of scope.

## 0. Top-0.1% lens + owner authorization (verified on the real M6.2R code + the decision record)

The lens changed four load-bearing calls; a real adversary (the M6.2S plan red-team) re-checks each against the
running `models/consumed.py` + `registry/validator.py`:

- **[REUSE the M6.2P fail-closed primitives — invent nothing (RULE-018 + DRY)]** `registry/validator.py` already has
  **`_resolve_send_policy(raw)`** (enum/valid-token → member; None/blank/unknown → **`BLOCKED_DEFAULT`**),
  **`_resolve_sensitivity(raw)`** (enum → member; None/unknown → **`PII`**), and **`permits_external_send(policy)`**
  (True ONLY for `ALLOW_EXTERNAL`); `consumed.py` has the owner-signed **`ExternalSendPolicy`** `{ALLOW_EXTERNAL,
  INTERNAL_ONLY, BLOCKED_PII, BLOCKED_DEFAULT}` + **`DataSensitivity`** `{PUBLIC, INTERNAL, PII}`. → the reader
  **imports and reuses** these; it defines no new enum and no new coercion. **`SENSITIVE` is not an M6
  `DataSensitivity` member**, so `_resolve_sensitivity("SENSITIVE")` already returns **`PII`** (unknown-token path) —
  the slice's "unknown/`SENSITIVE` → `PII`" is satisfied by the existing primitive, verbatim.
- **[staleness is monotonic AND fail-closed on the version bump]** the reader tracks `current_registry_version`
  (starts 0) and applies a feed **only** when it is fully valid **and** `registry_version > current`. A
  `registry_version <= current` (incl. equal) → **NOT applied** (no downgrade). **Critical**: the version is bumped
  and the rows stored **only on a fully-valid apply** — ANY fail-closed reject (malformed feed, missing required
  field, unknown-that-coerces is fine but a MISSING `event_code` / non-int `registry_version` / absent `events`) →
  **version + rows UNCHANGED**, so a malformed **higher**-version feed can never bump the counter and shut out later
  valid feeds. (A red-team trap: bumping the version before validating would let a bad feed poison staleness.)
- **[classify vs permit — the reader CLASSIFIES, it never permits egress]** the reader resolves
  `external_send_policy` **faithfully** via `_resolve_send_policy` (a Core `ALLOW_EXTERNAL` token stays
  `ALLOW_EXTERNAL`; an **unknown** token → `BLOCKED_DEFAULT`, **never fabricated `ALLOW_EXTERNAL`**). It exposes **no
  egress-permit surface and opens no egress** — whether an event is actually `ALLOW_EXTERNAL`-permitted is the **OPEN
  M6-OD-003** permit-mapping (owner/Sếp, out of scope), and `config.EXTERNAL_SEND` is Final `OFF` (defense-in-depth).
  So SMK-031's "no event becomes `ALLOW_EXTERNAL`" is realized as: the **fail-closed path never yields
  `ALLOW_EXTERNAL`** (unknown → `BLOCKED_DEFAULT`), and the reader takes **no egress action** (RULE-018: M6 records
  Core's classification, it neither reconciles the enum nor decides the permit-mapping).
- **[`TODO(contract)` on the PROPOSED shape; invent no omitted field]** the endpoint name/path + the row shape carry
  a `TODO(contract)` marker (final = chief-issued); **required** fields absent (`registry_version`, a row's
  `event_code`) → fail-closed **not applied**; **optional-with-default** fields absent (`data_sensitivity` → `PII`,
  `external_send_policy` → `BLOCKED_DEFAULT`, `is_active` → fail-closed **False**); **optional-metadata** absent
  (`event_group` / `domain` / `updated_at`) → **`None`**, never fabricated (RULE-001: never invent a field/event).
- **[adversarial red-team fix — the untrusted feed is type-guarded ROW-by-row, and `bool` is not an int]** the M6.2S
  plan red-team (skeptics prototyping `apply()` against the real M6.2R primitives) caught two fail-closed gaps: **(a
  MAJOR)** guarding only the *feed* as a `Mapping` but calling `row.get(...)` on each element lets a **non-Mapping
  element inside `events[]`** (an `int` / bare `str` / `None` from the untrusted M3 source) raise `AttributeError`
  and propagate — violating the "feed error → graceful `applied=False`, state unchanged" contract (state is not
  poisoned since the bump is last, but the reader must not crash on untrusted data). → **guard `isinstance(row,
  Mapping)` before any `row.get(...)`; a non-Mapping row → `feed_error:row_not_mapping` (NOT applied).** **(b MINOR)**
  a bare `isinstance(registry_version, int)` admits a **`bool`** (`bool` subclasses `int`), so `registry_version=True`
  applies as version `True (==1)`, stores un-normalized, and then shuts out a later genuine `registry_version=1`
  (`1 <= True` → stale). → **validate `isinstance(v, int) and not isinstance(v, bool)`; a `bool` version →
  `feed_error:bad_version` (NOT applied).** Both fixes are reflected in the §2 `apply()` enumeration + the regression
  spec + the §5 checklist.

**This slice is LEAN**: two new pure modules (feed model + reader adapter) + one regression test. **No migration**
(the reader is a pure in-memory consumer of a value object; no new table, no store), **no gate change**, **no
API/HTTP client** (the live M3 client is the out-of-scope seam), **no config change**, **no new secret**, **no flag
flip**. The feed is governance metadata (`event_code`/`event_group`/`domain`/`data_sensitivity`/`external_send_policy`
/`is_active`/`updated_at`) — **not customer PII** (RULE-014); the reader handles no secret / no endpoint auth.

## 1. Repo summary & staging model (cumulative carry-forward)

- **Base**: the whole **M6.2R** tree (app + 16 migrations `0001–0016` + the full carried suite, 647 green). M6.2S is
  a **superset**: carry M6.2R byte-identical, add the feed model + reader adapter + CODER regression. (The carry runs
  in **M6-P2702 implement**, not this plan.)
- **Stack** (locked target): Python 3.12, `framework=""` pure functions, `pytest -q`, stdlib only; in-memory only.
- **Layer touched** (ARCH_BASELINE §1.1 **Source**): a new CONSUMED **event_registry (CTR-003)** feed adapter —
  fail-closed, staleness-safe, honoring the §1.1 accepted finding *"a de-registered event code must never be
  false-ALLOWed / asymmetric cache staleness"*. M6 **consumes** the Core registry feed for its own validation; it
  never writes/invents an event, reconciles the Core enum, or decides the permit-mapping (RULE-001/018).
- **Baseline discipline (M6-P2702)**: verify green **before** any patch (subprocess `pytest`, parity with the M6.2R
  collect = 647), then green again after; **no skips**; actual `N passed` is the count.

## 2. The change — mapped to each exit-gate leg + SMK-031 (minimal change, rollback per item)

Legend: **Leg** = M6.2S.md "Exit gate checks" number · **Smoke** = SMK-031 · file:anchor are M6.2R-current.

### The registry-feed model + reader → **legs 1 + 2 + 3 · SMK-031(i)(ii)(iii)(iv) · RULE-001 · RULE-014 · RULE-015 · FAIL-007 · FAIL-008**

| File : anchor | Change | Rollback (staged) |
|---|---|---|
| **new** `app/measurement/models/registry_feed.py` | `PROPOSED_FEED_CONTRACT = "event-registry-feed.v1"` + `PROPOSED_FEED_ENDPOINT = "GET /api/v1/internal/event-registry?since_version={n}"` — module docstring carries a **`TODO(contract)`** note (final name/shape is chief-issued, not M6-invented). Frozen `RegistryFeedRow{event_code: str, data_sensitivity: DataSensitivity, external_send_policy: ExternalSendPolicy, is_active: bool, event_group: Optional[str] = None, domain: Optional[str] = None, updated_at: Optional[str] = None}` — reuses the M6.2P `DataSensitivity` + `ExternalSendPolicy` enums (imported from `models.consumed`); the resolved (coerced) enums are stored. Frozen `RegistryFeed{registry_version: int, rows: Tuple[RegistryFeedRow, ...]}`. `to_public()` on both (governance metadata, not PII — RULE-014). | delete the file |
| **new** `app/measurement/adapters/registry_feed_reader.py` | `RegistryFeedApplyResult{applied: bool, registry_version: int, rows_applied: int, reason: str}`. `RegistryFeedReader(initial_version: int = 0)`: **`apply(feed) -> RegistryFeedApplyResult`** — (a) **feed error / fail-closed**: `feed is None` / not a `Mapping` / `registry_version` missing or not an `int` (validate `isinstance(v, int) and not isinstance(v, bool)` — a `bool` is NOT a valid version, red-team fix) / `events` missing or not a list / **a row that is not a `Mapping`** (guard `isinstance(row, Mapping)` before any `row.get(...)` — red-team fix) / a row missing a non-blank `event_code` → **NOT applied**, version + rows **unchanged**, `reason="feed_error:<kind>"` (kinds: `not_mapping` / `bad_version` / `bad_events` / `row_not_mapping` / `missing_event_code`); (b) **staleness**: `registry_version <= current` → **NOT applied** (`reason="stale"`, no downgrade); (c) **apply**: parse each event → `RegistryFeedRow` with `external_send_policy = _resolve_send_policy(raw)` (unknown → `BLOCKED_DEFAULT`), `data_sensitivity = _resolve_sensitivity(raw)` (None/unknown/`SENSITIVE` → `PII`), `is_active` = strict bool (missing/non-bool → fail-closed **False**), optional `event_group`/`domain`/`updated_at` → `None` (never invented) → **only then** bump `current` + store rows. `current_registry_version() -> int`; `rows() -> Tuple[RegistryFeedRow, ...]`; `get(event_code) -> Optional[RegistryFeedRow]`. **No HTTP import, no live endpoint** — input is a value object / dict. Reuses `registry.validator._resolve_send_policy` / `_resolve_sensitivity` (no reinvention). | delete the file |

- **Leg 1 (proposed-shape parse + TODO(contract), M6-OD-018)** — the reader parses the feed into `RegistryFeedRow`
  reusing `ExternalSendPolicy`; `PROPOSED_FEED_CONTRACT`/`_ENDPOINT` + the module `TODO(contract)` marker flag the
  proposed name/shape; the reader invents no field the feed omits (optional metadata → `None`). ← SMK-031(i).
- **Leg 2 (staleness-safe by registry_version)** — monotonic `current_registry_version`; a feed with
  `registry_version <= current` is **NOT applied** (no downgrade); the version bumps **only on a fully-valid apply**,
  so a malformed higher-version feed never advances staleness. ← SMK-031(ii).
- **Leg 3 (fail-closed + no live call + no egress)** — unknown `external_send_policy` → `BLOCKED_DEFAULT`,
  unknown/`SENSITIVE` `data_sensitivity` → `PII`; a feed error / missing required field → **not applied**; the reader
  calls **no live endpoint** (mock/staged feed); the fail-closed path never yields `ALLOW_EXTERNAL`, the reader adds
  no egress surface, `EXTERNAL_SEND` stays `OFF`. ← SMK-031(iii)(iv).

### CODER regression (net-new test, no carried behaviour touched)

| File | Change | Rollback |
|---|---|---|
| **new** `tests/test_m6_2s_registry_feed_reader.py` | **(i) valid rows**: a feed (version 1) parses into typed `RegistryFeedRow`s reusing `ExternalSendPolicy`; `current_registry_version()==1`; optional metadata absent → `None` (not invented). **(ii) staleness**: a later feed with `registry_version <= current` → `applied=False`, version + rows **unchanged**; a **malformed higher**-version feed → version **NOT** bumped (staleness not poisoned); a strictly-greater valid feed → applied, version advances. **(iii) fail-closed tokens**: a row with an **unknown** `external_send_policy` → `BLOCKED_DEFAULT`; an **unknown or `SENSITIVE`** `data_sensitivity` → `PII`; **no** unknown coerces to `ALLOW_EXTERNAL`; a missing `data_sensitivity`/`external_send_policy` → `PII`/`BLOCKED_DEFAULT`; a missing/`non-bool` `is_active` → fail-closed `False`. **(iv) feed error**: `None` / not-a-Mapping / missing `registry_version` / a row missing `event_code` → `applied=False`, state **unchanged** (fail-closed); **(red-team) a non-Mapping row** (`events=[{...}, 42]` / `["X"]` / `[None]`) → `applied=False` (`feed_error:row_not_mapping`), **no `AttributeError`**, state unchanged; **(red-team) a `bool` `registry_version`** (`True`/`False`) → `applied=False` (`feed_error:bad_version`), state unchanged (never applies as version 1). Plus: the reader imports **no** HTTP/live-endpoint symbol; `config.EXTERNAL_SEND` stays `OFF`; no raw PII in any parsed row / result. Reuses the carried `models.consumed` enums + `registry.validator` coercers. | delete the file |

### LEGS 4–7 (other roles)

4 SMK-031 executed-or-waived (**TESTER** M6-P2703/2704). 5 all evidence schema-valid. 6 judge PASS (M6-P2709).
7 rollback documented (this §2 + §5). The coder legs never self-run/self-certify the smoke (RULE-015).

## 3. Backward-compat & the reused surfaces (verified on real code)

- **Reuse, not change** → `models/consumed.py` (`ExternalSendPolicy`/`DataSensitivity`/`EventRegistryRow`) +
  `registry/validator.py` (`_resolve_send_policy`/`_resolve_sensitivity`/`permits_external_send`) are **imported
  read-only, byte-identical to M6.2R**; SMK-028 (external_send_policy enum) + SMK-001 (event-registry validation) +
  every carried registry/consumed test stay green. The reader adds no field to `EventRegistryRow` (it uses a NEW
  `RegistryFeedRow`), so no carried shape changes.
- **New modules + new test only** → no carried test imports the feed model/reader; nothing to break. `config.py`
  untouched; migrations stay `0001–0016`.

## 4. Rules / fail gates, scope & governance

- **RULE-001** (event-registry validation, fail-closed): the reader never invents an event/field, never auto-allows
  an unknown token, and honors the de-registration/staleness fail-closed default (`is_active` false / stale → not
  ALLOWed). **RULE-014** (no raw PII): the feed is governance metadata, not customer PII; `to_public()` carries no
  identity value; no masking gap. **RULE-015** (no self-cert): proven by the SMK-031 regressions.
- **FAIL-007** (no evidence) + **FAIL-008** (raw PII/secret exposure): the reader handles no secret / no endpoint
  auth / no PII; the regression asserts no raw PII in any parsed row or result.
- **In scope**: the feed reader/parser (proposed shape → typed rows) + staleness-safe monotonic version + fail-closed
  resolution. **Out of scope (untouched)**: the live HTTP client to the M3 endpoint (ENTRY-003 V221 pending); the
  two-enum reconciliation (M6 `{PUBLIC,INTERNAL,PII}` vs M3 `{SENSITIVE,INTERNAL}` — Sếp/Core registry-branch); the
  Sếp permit-mapping (which events are `ALLOW_EXTERNAL`) + hash policy (M6-OD-003 OPEN). No flag flip; posture stays
  OFF/BLOCKED/OFF.
- **Boundary intact**: M6 **reads** the Core registry feed fail-closed **for its own validation**; it does **not**
  write/invent an event, reconcile the Core enum, decide the permit-mapping, send CRM, or open egress (RULE-001/018).
  The reader **classifies** `external_send_policy` (unknown → `BLOCKED_DEFAULT`, never fabricated `ALLOW_EXTERNAL`)
  and opens **no egress**; `EXTERNAL_SEND` stays `OFF`. `M6-P1000` / `M6-P1309` stay BLOCKED.
- **Forward conditions (recorded, NOT blockers)**: **M6-OD-003** (permit-mapping / hash) OPEN governs which events
  are actually `ALLOW_EXTERNAL`-permitted (not this reader); the live M3 endpoint + the two-enum reconciliation + the
  `TODO(contract)` finalization + M6-OD-011 server-bind/go-live remain hard gates before any **live** registry pull /
  real egress. The exit judge M6-P2709 confirms no flag flip, no live HTTP, no egress, posture OFF/BLOCKED/OFF.

## 5. Verification plan for M6-P2702 (commands + PASS/FAIL + rollback)

**Commands** (`PYTHONDONTWRITEBYTECODE=1 python -B -m pytest -p no:cacheprovider`): carry M6.2R → `impl/M6.2S/`
(exclude caches; keep this `PLAN.md`), baseline green + parity **before** any patch (expect 647); add the feed model
+ reader adapter + the regression; re-run green (no skips); confirm `config.py` unchanged, `consumed.py`/`validator.py`
byte-identical, migrations `0001–0016` unchanged, no new flag/secret, clean caches, PII scan.

**PASS/FAIL checklist**: proposed shape → typed rows reusing `ExternalSendPolicy` + `TODO(contract)` markers + no
invented field ✓/✗ · staleness monotonic (version `<=` last not applied; malformed higher-version does not bump)
✓/✗ · unknown `external_send_policy` → `BLOCKED_DEFAULT` + unknown/`SENSITIVE` `data_sensitivity` → `PII` + no unknown
→ `ALLOW_EXTERNAL` ✓/✗ · feed error/missing field → not applied (state unchanged) ✓/✗ · a non-Mapping row → graceful
`applied=False` (no `AttributeError`) + a `bool` `registry_version` → `feed_error:bad_version` (red-team fixes) ✓/✗ ·
no live endpoint import + `EXTERNAL_SEND` OFF + no raw PII ✓/✗ · carried consumed/registry tests + SMK-028/001 still green + `consumed.py`/
`validator.py` byte-identical ✓/✗ · full suite green (baseline ≤ final) ✓/✗ · posture + no flag/secret + no migration
✓/✗.

**Rollback**: staged only — delete the `04-artifacts/impl/M6.2S/` tree (M6.2R untouched). Per item: the three new
files → delete. **No carried file is edited** (reuse-only imports; no gate/config/migration change), so there is
nothing to scoped-revert. No live migration to unwind (`live_migrations=false`). Every change is additive; a revert
restores prior behaviour.

---

*Plan-only: this document writes no application code, applies no migration, opens no egress, makes no live HTTP
call, resolves no owner decision, and flips no flag. It plans an owner-authorized (M6-OD-018), STAGED, mock-feed
registry reader that reuses the M6.2P fail-closed vocabulary. `global_gateway_state=BLOCKED`,
`production_flag=OFF`, `external_send=OFF`. The runner gate + JUDGE decide (RULE-015).*
