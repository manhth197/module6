# M4 Evidence — ASSERT-001: AI does not publish a FINAL PRICE to a public channel

> **Dossier:** `M6-ENTRY-004` (joint Module 4 + Module 5). This file covers the **M4 half only**.
> **Task:** `SAFE-001` — Public/private surface guard. **Owner decisions:** `OWN-013`, `OWN-014`.
> **Verified against execution baseline:** `79668115d79f633c97cf4490c51af35041d440f7` (branch `dev015`).
>
> **Location note.** M4 evidence lives in this directory
> (`docs/ai/analytics-v0.2/module-4-gate-0-1/evidence/`), which is the only evidence directory in the
> repository. The `04-artifacts/evidence/entry/M6-ENTRY-004/` path in the M6 template does not exist
> in this repository (top-level directories are `back-end`, `contracts`, `docs`, `front-end`,
> `ginsengfood-contracts`); it belongs to the M6 repository. M6 receives a copy and files it there.
>
> **This file deliberately contains no commit SHA and no SHA-256 of itself** — either would be a
> self-reference. The commit SHA and the SHA-256 manifest are recorded in the task report
> (`SAFE-001.md` §Commit receipt) after the owner-approved scoped commit, and handed to M6 from there.

## Assertion

> **ASSERT-001** — M4 (AI Advisor) does not publish a final price to a public channel; it advises
> within boundaries and does not settle a price publicly.

## Status

**IMPLEMENTED — PENDING INDEPENDENT TESTER + JUDGE.** Not closed.

The assertion did **not** hold at the reviewed baseline. A fail-open in surface classification has been
fixed and is covered by the tests below, but this file records **Coder self-verification only**. It
becomes evidence for the gate after an independent Tester `PASS` and a Judge `ACCEPTED`, and after the
owner-approved scoped commit. Do not cite it as a closed control before then.

## What was wrong (defect, not a documentation gap)

`/api/v1/m4/advisor/turn` classified the delivery surface with a substring heuristic that fell back
to a **private** surface for blank or unrecognised input:

| Input `channelSurface` | Resolved surface (before) | Guard outcome (before) | Final price published? |
|---|---|---|---|
| field absent / `""` / `"   "` | `WEB_CHAT_PRIVATE` | short-circuit `pass()` | **yes** |
| `STORE_FRONT_CHAT` (service default) | `WEB_CHAT_PRIVATE` | short-circuit `pass()` | **yes** |
| `FEED`, `FANPAGE`, `STREAM`, any unknown token | `WEB_CHAT_PRIVATE` | short-circuit `pass()` | **yes** |
| `POST_COMMENT` paired with `MESSENGER` (spoof) | private, from the surface field | short-circuit `pass()` | **yes** |

Both `PublicPrivateSurfaceGuard` and `PIIExposureGuard` are wired and do fail closed — but only on a
`null` surface. Their own javadoc states the intent: *"a null surface means the delivery target is
unknown, so we must NOT guess private"*. The caller never produced `null`; it substituted a concrete
private surface. **The fail-closed branch was unreachable from this endpoint.** A guard that is wired
and unit-tested is not the same as a guard that protects the endpoint.

The same heuristic shape existed in **six** places overall. Three were on the surface-routing path and
are fixed here; the other three feed only a trace record and are recorded as follow-up (see
§Scope and limits). Fixing only the endpoint named in the report would have left the other routing
copies open.

## Fix — code path

| # | What | Where |
|---|---|---|
| 1 | Canonical surface classifier: exact tokens only, unknown/blank/`null` ⇒ `PUBLIC_COMMENT` | `back-end/src/main/java/com/ginsengfood/project/ai/runtime/consumer/finalresponse/domain/ResponseChannelSurfaceResolver.java:67-76` (`classify`), `:74` (fail-closed default) |
| 2 | Role-aware, pair-aware resolution, most-restrictive-wins (`OWN-014`) | `ResponseChannelSurfaceResolver.java:83-92` (`classifyChannelCode`, the narrower channel-role table), `:106-118` (`resolve`) |
| 3 | Resolved from the **raw** request pair, **before** the defaults are substituted at `:411-412` (`firstNonBlank(request.channelCode(), DEFAULT_CHANNEL)` / `…, DEFAULT_SURFACE`). The constants are only *declared* at `:95-96`; the assignment at `:411-412` is the line that mattered | `runtime/api/M4AdvisorTurnService.java:420` |
| 4 | Commerce surface derived from the same decision, not re-parsed | `M4AdvisorTurnService.java:918-920` (`quoteSurfaceOf`), used at `:693`, `:737`, `:987`, `:992` |
| 5 | The two sibling copies on the `/turn` path delegate to the canonical classifier — no second opinion | `runtime/consumer/knowledge/application/R2AnswerGateService.java:196` · `runtime/consumer/recommendation/application/SkuComparisonGateService.java:250, 344` |
| 5b | `CustomerFacingFinalGuardBridge.mapSurface` (`/chat`, `/query`) keeps its **own** legacy token table, deliberately **not** shared — see §Scope and limits | `runtime/internalchat/CustomerFacingFinalGuardBridge.java:233-242` |
| 6 | Enforcement on **`ChannelSurface`** (commerce enum) — the complete set, **5 branches** | `runtime/consumer/commerce/application/guard/NoFinalPriceWithoutQuoteSnapshotGuard.java:16` · `runtime/consumer/commerce/application/OrderDraftDisplayModelBuilder.java:42` · `runtime/consumer/commerce/application/guard/CustomerConfirmationEligibilityGuard.java:16` · `runtime/consumer/commerce/domain/QuoteSnapshotReference.java:91` · `runtime/consumer/commerce/adapter/PreviewOrderCommerceRuntimePort.java:350` |
| 6b | Enforcement on **`ResponseChannelSurface`** (guard-chain enum) — a **separate** inventory, do not merge with row 6 | `runtime/consumer/finalresponse/application/FinalResponseGuardService.java:252` (`publicPrivateSurfaceGuard`), `:253` (`piiExposureGuard`) |

### Resolution rules (`OWN-014`)

- Public in **either** field wins. `POST_COMMENT`, `LIVE_COMMENT`, `LIVE_MC` cannot be downgraded to
  private by a self-declared private surface.
- **The two fields have different private token sets, and a token is honoured only in its own role:**

  | Family | accepted as `channelCode` | accepted as `channelSurface` |
  |---|---|---|
  | web | `WEB_CHAT`, `WEBSITE_CHAT` | those + `WEB_CHAT_PRIVATE`, `STORE_FRONT_CHAT` |
  | inbox | `MESSENGER`, `PAGE_INBOX` | those + `PRIVATE_MESSENGER` |

- Private **only** when both fields name the same family **in their own role**. A surface-only alias
  parked in the `channelCode` slot is not a channel: `STORE_FRONT_CHAT × STORE_FRONT_CHAT`,
  `WEB_CHAT_PRIVATE × STORE_FRONT_CHAT` and `PRIVATE_MESSENGER × PAGE_INBOX` all fail closed.
- A lone private token, a cross-family pair, a missing field or an unknown token ⇒ public.
- `CRM`/`INTERNAL`/`ADMIN` are not mapped: a customer-facing turn cannot self-declare an internal
  surface without a trusted source.

> **Correction note.** An earlier revision classified both fields with the same single-field function
> and compared the results for equality. That is **not** equivalent to the table above — it accepted a
> surface-only alias in the channel slot, so `STORE_FRONT_CHAT × STORE_FRONT_CHAT` resolved private.
> Corrected after owner/Codex review.

## Behaviour after the fix

| Request (`channelCode` × `channelSurface`) | Effective surface | `finalPriceDisplayed` | Blocked reason |
|---|---|---|---|
| both absent | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| `WEB_CHAT` × absent | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| `FEED` / `FANPAGE` / `STREAM` | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| `POST_COMMENT` × `STORE_FRONT_CHAT` | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| `LIVE_COMMENT` × `MESSENGER` | `LIVE_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| `MESSENGER` × `STORE_FRONT_CHAT` (cross-family) | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| **`STORE_FRONT_CHAT` × `WEB_CHAT`** (alias in the channel slot) | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| **`STORE_FRONT_CHAT` × `STORE_FRONT_CHAT`** | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| **`WEB_CHAT_PRIVATE` × `STORE_FRONT_CHAT`** | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| **`PRIVATE_MESSENGER` × `PAGE_INBOX`** | `PUBLIC_COMMENT` | `false` | `PUBLIC_SURFACE_REQUIRES_PRIVATE_HANDOFF` |
| `WEB_CHAT` × `STORE_FRONT_CHAT` (legacy web pair) | `WEB_CHAT_PRIVATE` | `true` | — (unchanged) |
| `WEBSITE_CHAT` × `WEB_CHAT_PRIVATE` | `WEB_CHAT_PRIVATE` | `true` | — (unchanged) |
| `MESSENGER` × `PAGE_INBOX` | `PRIVATE_MESSENGER` | `true` | — (unchanged) |
| `PAGE_INBOX` × `PRIVATE_MESSENGER` | `PRIVATE_MESSENGER` | `true` | — (unchanged) |

## Tests

| Test | Covers |
|---|---|
| `M4AdvisorTurnServiceTest.quoteSurfaceMatchesResolverDecisionForEveryPair` | **feed proof**: 24 pairs through the real turn service, asserting the observed quote outcome equals the resolver's decision (resolver used as an oracle) |
| `M4AdvisorTurnServiceTest.quoteOnUntaggedOrPublicSurfaceNeverPublishesFinalPrice` | 16 cases: missing/blank/unknown/public/spoof/cross-family/alias-in-wrong-role ⇒ no final price |
| `M4AdvisorTurnServiceTest.quoteOnRecognisedPrivatePairStillDisplaysFinalPrice` | 7 cases: recognised private pairs still show the runtime total (no regression) |
| `ResponseChannelSurfaceResolverTest.surfaceOnlyAliasInChannelCodeSlotFailsClosed` | 7 role-violation pairs ⇒ public |
| `ResponseChannelSurfaceResolverTest.ownerApprovedPrivatePairsStayPrivate` | 11 pairs — the exact set `OWN-014` allows |
| `ResponseChannelSurfaceResolverTest.unknownTokensFailClosed` | 22 unknown/blank/internal tokens ⇒ public |
| `ResponseChannelSurfaceResolverTest.pairResolution` | 22-row pair matrix, most-restrictive-wins |
| `ResponseChannelSurfaceResolverTest.lonePrivateTokenFailsClosed` | a private token without its channel ⇒ public |
| `ResponseChannelSurfaceResolverTest.neverMatchesOnSubstring` | exact-token, not `contains()` |
| `ResponseChannelSurfaceStructuralTest.noSurfaceSubstringHeuristicSurvives` | no new copy of the heuristic can be added |
| `ResponseChannelSurfaceStructuralTest.channelSurfaceEnforcementBranchInventory` | **inventory only** — where enforcement branches live. Explicitly *not* a feed proof; see the note in that test |
| `CustomerFacingFinalGuardBridgeTest.mapSurface_storeFrontChat_staysPublicForChatAndQuery` · `…_legacyTokenSet_isUnchangedBySafe001` | `/chat` + `/query` behaviour pinned unchanged |

### Mutation proof (the tests are not vacuous)

| Mutation | Result |
|---|---|
| `classify()` default ⇒ `WEB_CHAT_PRIVATE` (restores the original fail-open) | **36 failures** across 3 classes, including **8** in the end-to-end turn test |
| `resolve()` returns the private surface field even when the channel is public | **13 failures**, including **5** end-to-end |
| `quoteSurfaceOf()` always returns `ChannelSurface.PRIVATE` (breaks the feed without touching the resolver) | **34 failures**; the feed proof fails from its first row |

Each mutation was applied to the working copy, measured, then reverted, and the suite re-run green.

> **Correction note.** The first revision of this file claimed the bridge behaviour was preserved and
> claimed "every enforcement branch is fed from the resolver". Both were wrong: the bridge behaviour
> had in fact been *changed*, and the feed claim rested on a file-path scan. Both are corrected above,
> and the feed claim is now backed by the behavioural oracle test.

## Test run

`./mvnw -o test -Dtest=com.ginsengfood.project.ai.**` at the baseline above:

- **3462 run · 0 failures · 26 errors · 4 skipped** (Coder attempt 4, correction pass `C3-03`).
  Earlier marks: 3453 after the `C3-01`/`C3-02` pass, 3435 after base attempt 3, 3412 before it.
  **The whole delta — including the +9 of this pass — is cases added to `PIIExposureGuardTest`**, for
  `T2-01`/`T2-02`, then `C3-01`/`C3-02`, then `C3-03`. Every one of those findings sits inside
  `PIIExposureGuard`, the PII detector. **No file this evidence covers has changed at any point**:
  the final-price / channel-surface routing described below is byte-identical to the version the
  Tester verified exhaustively in attempt 2 (446 pairs ⇒ exactly 14 private).
- The 26 errors are `NOT_RUNNABLE`, not defects: 5 Testcontainers-backed repository classes
  (`AiProductApprovedContentRepositoryTest`, `AiProductEffectivenessReviewRepositoryDataJpaTest`,
  `AiPolicyVersionRuntimeSourceRepositoryTest`, `MemberLifecycleOutcomeLogTest`,
  `CustomerMemoryRecordTest`) fail to initialise because no Docker environment is available on the
  build host. **0 of the 5 are in this task's scope.** Manual tally of the surefire XML matches the
  Maven summary exactly.

## Scope and limits — read before citing this file

- **Not full end-to-end.** There is no `@SpringBootTest` anywhere in the M4 test tree, so these are
  service-level and guard-chain-level tests, not HTTP-level. This is a pre-existing baseline gap.
- **The request contract is unchanged.** `channelSurface` is still an untyped `String`
  (`maxLength 64`). Making it a typed enum with `@NotBlank` is a breaking wire-contract change and
  belongs to `API-002`. This fix closes the leak without it.
- **`/chat` and `/query` are untouched.** Their single legacy `channel` field has its own historical
  token table, which never contained `STORE_FRONT_CHAT` and has always failed closed to
  `PUBLIC_COMMENT` for anything unknown. A `SAFE-001` revision briefly routed them through the new
  resolver, which would have turned `STORE_FRONT_CHAT` on those two endpoints from public into
  private — a relaxation outside this task's remit. That was reverted; reconciling the two token sets
  is `API-002` scope.
- **Three trace-only copies of the old heuristic remain**, in `DailyCommercialRuntimePipeline`,
  `Customer360RuntimePipeline` and `ProductPublicViewRuntimePipeline`. They write a `ChannelSurface`
  into a `DecisionEnvelope`. Re-verified at `79668115`: `DecisionEnvelope.surface` is read at exactly
  **two** sites in `ai/`, and they are **not** equivalent to each other:
  - `RuntimeFailClosedPolicy:149` — a pure copy into a new envelope, no branch.
  - `RecommendationPreflightRuntimePipeline:141` — **this one does branch**:
    `primaryDecision(decisions).surface() == null ? ChannelSurface.PRIVATE : ...`. It is a
    null-coalesce to `PRIVATE`, i.e. the same fail-open shape `SAFE-001` exists to remove.

  **Correction (Tester `T4-02`, attempt 4).** An earlier revision of this bullet said the two readers
  *"copy it into another envelope and neither branches on it"*. That was wrong for
  `RecommendationPreflightRuntimePipeline:141`. `T2-03` had already corrected the same sentence in
  `ResponseChannelSurfaceStructuralTest`'s javadoc but not here — one claim, two copies, only one
  fixed.

  **What is still true, and bounded to what was measured:** the substituted value does not reach a
  security decision. `M4AdvisorTurnResponse` exposes no surface field (grepped: zero hits), and no
  consumer branches on `DecisionEnvelope.surface` to grant or deny anything — the branch at `:141`
  only decides which value gets *recorded*. So these three copies remain **trace-only in effect**,
  and this is not a `CONTRACT_CONFLICT`.

  **Residual risk, stated rather than hidden:** the value recorded is a *wrong* one — `PRIVATE` for a
  surface that was actually unknown. Any future consumer that starts branching on this field inherits
  a fail-open default. That is why the three copies stay registered as owner-visible follow-up,
  frozen by `ResponseChannelSurfaceStructuralTest.noSurfaceSubstringHeuristicSurvives` so a further
  copy cannot appear unnoticed. They are outside this task's write scope.
- **Two separate inventories — do not merge them.** `ChannelSurface` (commerce enum) is branched on in
  exactly **five** places: `NoFinalPriceWithoutQuoteSnapshotGuard:16` ·
  `CustomerConfirmationEligibilityGuard:16` · `OrderDraftDisplayModelBuilder:42` ·
  `QuoteSnapshotReference:91` · `PreviewOrderCommerceRuntimePort:350` — all under
  `runtime/consumer/commerce/`, all fed from `quoteSurfaceOf(resolve(...))`, pinned as an exact set by
  `channelSurfaceEnforcementBranchInventory`. `ResponseChannelSurface` is a **different** enum with a
  different consumer set (the guard chain in `FinalResponseGuardService`). An earlier revision of this
  file reported "4 branches" by conflating the two counts and omitting
  `PreviewOrderCommerceRuntimePort`; corrected here.
- **`NoPublicQuoteOnPublicSurfaceGuard` was dead code and has been deleted** (`OWN-014` §4) after a
  zero-reference proof: 0 callers in `src/main` beyond its own declaration, 0 references in
  `src/test`. It never enforced anything at runtime. **Do not cite it as evidence.** The real
  enforcement is `PublicPrivateSurfaceGuard` and `NoFinalPriceWithoutQuoteSnapshotGuard`.
- **Live/M7:** M4 supports `LIVE_COMMENT`/`LIVE_MC` at `/turn`; whether M7 actually routes through
  `/turn` is `EXTERNAL_NOT_VERIFIED` (`OWN-009`).
- **CI is currently disabled** in this repository, so nothing re-runs these tests automatically yet
  (task `FND-005`).

## Sign-off

| Role | Status |
|---|---|
| Coder (M4) | **attempt 5** — closes Tester `T4-02` **in this file**: the §Scope sentence *"neither branches on it"* is corrected above, bounded to what was re-measured (`DecisionEnvelope.surface` has exactly two readers; `RecommendationPreflightRuntimePipeline:141` **does** branch `null → PRIVATE`; no consumer branches on it to grant or deny, and `M4AdvisorTurnResponse` exposes no surface field, so the *trace-only* conclusion survives while the wording did not). **This is the one change to this file** — the routing and quote-surface behaviour it documents is still byte-identical. Self-verified only. History: **attempt 4 — correction pass `C3-03`** (Codex: a clause-scoped tail check let a line-broken or punctuation-split address pass as a delivery date). Together with attempt 3 and the `C3-01`/`C3-02` pass this closes Tester `T2-01`/`T2-02`/`T2-03`; **every one of those changes is inside `PIIExposureGuard`**. **No file covered by this evidence changed in any pass** — the routing and quote-surface behaviour described here is byte-identical to what the Tester verified. Self-verified only |
| Tester (M4) | **attempt 1 = `FAIL`** — finding `T-01` (AC-2.4 false positive) reproduced 5/5; see `SAFE-001.md` §16. **attempt 2 = `FAIL`** — 13 AC PASS / 2 FAIL; both failures (`T2-01`, `T2-02`) are in the PII guard, **not** in the price/surface routing this file covers: routing was re-verified exhaustively (446 pairs ⇒ exactly 14 private) and all 5 mutations were killed. See `SAFE-001.md` §20. **attempt 3 = never opened** — the owner held it back when Codex raised `C3-03`. **attempt 4 = `FAIL`** — the blocker (`T4-01`, P1) is in the PII guard, **not** in the price/surface routing this file covers: routing was re-verified independently on a **1225-pair** matrix plus 20 near-miss/substring tokens ⇒ still exactly **14** private, and mutations M1/M2 killed **143**/**119** tests. But `T4-02` (P2) **is** about this file: the §Scope line *"neither branches on it"* is contradicted by `RecommendationPreflightRuntimePipeline:141`, which branches `null → ChannelSurface.PRIVATE`. Not corrected here — the Tester records findings rather than editing evidence prose. See `SAFE-001.md` §24. **attempt 5 = `PASS`** — the corrected §Scope wording was re-verified independently and the word *trace-only* is **earned**: `DecisionEnvelope.surface` is read at exactly **two** sites across all of `back-end/src/main` (zero outside `ai/`), `M4AdvisorTurnResponse` exposes **no** surface field (`M4AdvisorTurnDecisionView.from` maps 14 fields, surface is not one), `AiDecisionLog` has no surface column, and both the guard chain and the commerce guards take their surface from `ResponseChannelSurfaceResolver`, independent of this field. The residual risk stated in §Scope is confirmed, not softened. Routing re-verified again: 1225-pair matrix ⇒ still exactly **14** private. Every citation in this file verified. See `SAFE-001.md` §27 |
| Judge (M4) | pending |
| Owner (M4) | pending |
| Joint `M6-ENTRY-004` gate | **BLOCKED** — the M5 half (ASSERT-004/005/006) is `EXTERNAL_NOT_VERIFIED`; both halves are required |
