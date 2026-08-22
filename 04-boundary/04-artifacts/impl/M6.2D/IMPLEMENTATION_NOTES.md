# M6.2D IMPLEMENTATION NOTES — M6-P1302 (CODER, implement, STAGED)

Realizes [`PLAN.md`](PLAN.md) (M6-P1301) as staged code under `04-artifacts/impl/M6.2D/`. **Nothing shipped**:
`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`; no migration applied; no external
call; no event invented; no flag flipped; `04-artifacts/state/` not touched; no self-certification (RULE-015).

## 0. Governance & entry

- Ledger: **M6-P1302 = RUNNING** (row 110); dependency **M6-P1301 = PASS**. Target `LOCKED`/`STAGED_ONLY`;
  M6-OD-011 DECIDED.
- Entry gate M6-P1300 = SIGNED **binds fix-first** F-B/F-C/F-A (from the M6.2C review M6-P1209) — closed §2.
  Forward gates: **M6-OD-003** (hash fields) OPEN → hash mechanism fail-closed, ratified list at M6.2D exit;
  **M6-OD-004** (connector) OUT. **Governance gap (judge-escalated):** `M6-DEFER-FBC-M6.2D.json` was never
  created; the binding is in force via the M6-P1300 sign-off and is closed here regardless (creating that
  decision file is an operator/owner action — the coder cannot write to `decisions/`).

## 1. Staging model — cumulative snapshot

The whole **M6.2C** tree was carried forward byte-identical (**171 tests** — my 163 M6.2C + 8 TESTER-authored
M6.2C smokes added at M6-P1203). M6.2D **patches** the five fix-first sites and **adds** the integration layer.
The change set below is the diff; three carried-forward test artifacts were updated (F-C-mandated, §4.1).

## 2. Fix-first BINDING (consent fail-OPEN residuals) — DONE FIRST, proven green

| # | File(s) patched | What was done | Test |
|---|---|---|---|
| **F-B** | `app/measurement/consent/gate.py` | The scope membership `scope not in snapshot.consent_scope` trusted the object's `__contains__`; a `set`-**subclass** can override it to always-True (fail-OPEN) and still pass the M6.2B/F2 type check. Fix: test membership on a **materialized real** `frozenset(snapshot.consent_scope)` (built via `__iter__`, cannot be fooled by `__contains__`). Completes the MAJOR-7 fix the reviewer found incomplete. | `test_fb_set_subclass_contains_override_is_denied` |
| **F-C** | `app/measurement/outbox/enqueue.py` (checkpoint 1) + `app/measurement/outbox/audience_dispatcher.py` (checkpoint 2) | The audience path resolved a member's consent by id but never bound `member_key ↔ snapshot.subject_ref` → **borrowed consent**. Fix: only the member's OWN consent (subject_ref == member_key) yields ADD at enqueue; a borrowed/mismatched ADD is blocked at dispatch (`SYNC_BLOCKED_CONSENT_SUBJECT_MISMATCH`). | `test_fc_enqueue_borrowed_consent_is_remove_not_add`, `test_fc_dispatcher_blocks_add_with_borrowed_consent` |
| **F-A** | `app/measurement/outbox/measurement_dispatcher.py` + `audience_dispatcher.py` | `permits_send` (→ `current_state`) was unwrapped — a reader exception at send would escape. Fix: wrap it so any exception → **deny** (audited), never a crash or fail-open. | `test_fa_reader_exception_at_send_denies_not_crashes` |

**No regression**: the carried-forward 171 tests stay green (F-B/F-C/F-A are additive hardening; the two
F-C-mandated carried-test updates are §4.1).

## 3. New change set — the Integration (send-discipline) layer

| # | File(s) (new) | Purpose | Rule/Contract | Leg | Smoke |
|---|---|---|---|---|---|
| B2 | `app/measurement/integration/hash_policy.py` | Fail-closed hash mechanism: `hash_identity` (sha256) + `to_public_safe` (every identity field hashed; raw allow-list EMPTY while M6-OD-003 OPEN). | RULE-014; FAIL-008; M6-OD-003 | 2 | SMK-017 |
| B3 | `app/measurement/integration/payload.py` | `build_platform_payload` → PII-safe payload with `event_name` + the **shared** `event_id = hash(source_event_id + event_code)` (same across PIXEL/CAPI/OFFLINE of one source event → platform dedup). | RULE-005/014; FAIL-001/008 | 1,2 | SMK-003/017 |
| B4 | `app/measurement/integration/result_log.py` | `PlatformResultLog` (staged, in-memory): PII-safe records of (staged) send attempts. | RULE-014; FAIL-001/008 | 1,2 | SMK-003/017 |
| B5 | `app/measurement/integration/platform_transport.py` | `StagedPlatformTransport` (M6.2C `Transport` port): resolve conversion → OFFLINE-after-ORDER_VERIFIED guard → build PII-safe payload → log result → (`external_send=OFF`) raise `ExternalSendBlocked` (item held). NO real send. | RULE-004/005/014/003; H01 | 1,2 | SMK-003/017 |
| A1 | `app/config.py` (extended) | `MEASUREMENT_HASH_ALGO="sha256"` + `HASH_POLICY_RATIFIED=False` (fail-closed). No flag changed. | RULE-014/H01 | 2 | — |
| T1–T5 | `tests/test_platform_dedup_event_id.py`, `test_hash_policy_no_raw_pii.py`, `test_offline_after_order_verified.py`, `test_staged_no_real_send.py`, `test_m6_2d_fixfirst_regressions.py` | 14 new tests making SMK-003/SMK-017 runnable + pinning F-B/F-C/F-A. | — | 1,2 (+L3/L4 runnable) | SMK-003/017/002 |

*(No new migration: M6.2D adds no M6-owned table; the result log is a staged in-memory store, physical binding
at M6-OD-011.)*

## 4. Plan-deltas (deviations require a note)

### 4.1 F-C-mandated carried-forward test updates (additive; kept member keys)
F-C requires `member_key == consent snapshot subject_ref`. The carried M6.2C audience fixture modeled the
**unbound** (borrowed-consent) case (`member_key` = "mem_consented"/"mem_optout" but the consent subjects were
"guest_mapped_ok"/"guest_x"). Rather than rename the member keys (which the **TESTER-authored** M6.2C smoke
`tests/smoke/test_smk_002_outbox_consent_failclosed.py` depends on), I **added two correctly-bound consent
snapshots** (`cs_mem_consented` subject "mem_consented" VALID+AUDIENCE_SYNC, `cs_mem_optout` subject "mem_optout"
OPT_OUT) to the `consent_rows` fixture, pointed the segment members at them, and added `"mem_consented": VALID`
to `app_consent_reader.current`. All additive — the TESTER smoke and the M6.2C audience tests still pass with
their original keys/assertions. No test was loosened.

### 4.2 Other deltas
- **`StagedPlatformTransport` is the M6.2D wiring** for the send-discipline tests (builds+logs+blocks); the bare
  M6.2C `StagedBlockedTransport` remains available. Both make no real send.
- **`event_id` is derived from the source event identity** (`hash(source_event_id+event_code)`), SHARED across
  platforms (dedup), while the internal `dedup_key` stays per-platform (two dedup layers).
- **Hash policy fail-closed with M6-OD-003 OPEN**: every identity field hashed, raw allow-list empty; SMK-017
  proves no raw PII; the ratified field list is the leg-2 forward gate.

### 4.3 ⚠️ FLAGGED OBSERVATION (out-of-scope; NOT self-fixed) — measurement-path symmetric borrowed-consent
F-C (bound) is the **audience** borrowed-consent fix. The **measurement** conversion path has the SAME class of
gap and I did **not** self-fix it (it is outside the named binding, and closing it would change the conversions
endpoint signature + ripple into carried M6.2C tests — an unplanned scope change). **Precisely**: the M6.2C
conversions endpoint (`app/api/conversions.py`) requires a `consent_snapshot_id` but never binds the snapshot's
`subject_ref` to the conversion's `customer_or_guest_key`; and the measurement dispatcher's send-time
`permits_send` checks the snapshot's own subject state but not that the snapshot belongs to the conversion's
subject. So a conversion can reference **another subject's** valid consent (borrowed consent) — the measurement
analogue of F-C. It is **armed-not-fired** today (external_send=OFF; staged transport never sends). **Surfaced
here for the M6.2D boundary/security reviewers (M6-P1305/1306) and the owner** to decide — recommended to bind
it fix-first at M6.2E (as F-C was bound for M6.2D), and to formalize it in the same decision file as
`M6-DEFER-FBC-M6.2D.json` (§0 governance gap). Not silently patched, per minimal-diff / in-scope discipline.

## 5. Fail-closed branches (acceptance check)

- **Consent**: gate F-B (frozenset membership) + F-C (audience subject binding) + F-A (reader-exception deny) +
  the M6.2C two-checkpoint send policy. **Dedup**: internal `dedup_key` UNIQUE per platform + shared platform
  `event_id`. **Registry/revenue**: conversions endpoint gates event_code + revenue-only-ORDER_VERIFIED (M6.2C).
  **PII**: hash mechanism fail-closed (no raw PII in payload/log), mask-on-export. **No send**: staged transport
  refuses (external_send=OFF); OFFLINE only after ORDER_VERIFIED.

## 6. Verification (this prompt actually ran)

Pinned interpreter, cwd `04-artifacts/impl/M6.2D`, python 3.12; counts captured in-process (authoritative):

| Step | Result |
|---|---|
| Baseline (carried-forward M6.2C tree incl. TESTER smokes) | green (rc 0), **171 tests** |
| After fix-first F-B/F-C/F-A + F-C fixture updates | **171 passed** (no regression) |
| Green-after (full suite) | **185 passed**, rc 0 (171 carried + 14 new) |
| Entrypoint `python -m app` | prints staged posture BLOCKED/OFF/OFF, exit 0 |
| Handoff hygiene | 0 `__pycache__`/`.pytest_cache` remaining (`PYTHONDONTWRITEBYTECODE=1`) |

## 7. Rollback

Staged ⇒ non-destructive. New files → delete; patched carried-forward files (`gate.py`, `enqueue.py`, both
dispatchers, `config.py`) + the updated test fixtures/tests → revert to their M6.2C version; baseline rollback =
delete the M6.2D tree (M6.2C untouched). No new table → no down-DDL.

## 8. Governance carried forward (unchanged)

`global_gateway_state=BLOCKED`, `production_flag=OFF`, `external_send=OFF`. M6-OD-003 (hash) + M6-OD-004
(connector) remain HARD FORWARD gates before any real send; leg 2 stays conditionally blocked on M6-OD-003 where
the ratified field list is unresolved. The MANDATORY M6.2G Scale-Gate re-gate (ENTRY-001/002/003) stands before
any real scale or external send. No self-certification (RULE-015) — the runner EVIDENCE_GATE and the
boundary/security adversaries (M6-P1305/1306, FAIL-002 in scope) decide closure and must verify F-B/F-C/F-A +
review the flagged measurement-path observation (§4.3).
