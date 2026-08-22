# M4 Evidence — ASSERT-003: AI does not spam or send in bulk outside an approved flow

> **Dossier:** `M6-ENTRY-004` (joint Module 4 + Module 5). This file covers the **M4 half only**.
> **Task:** `SAFE-001` — evidence-only deliverable (`OWN-013`). **No code change was required.**
> **Verified against execution baseline:** `79668115d79f633c97cf4490c51af35041d440f7` (branch `dev015`).
>
> **Location note.** See `m4-no-final-price-public.md` — M4 evidence lives in this directory; the
> `04-artifacts/...` path in the M6 template belongs to the M6 repository.
>
> **This file deliberately contains no commit SHA and no SHA-256 of itself.** Both are recorded in
> `SAFE-001.md` §Commit receipt after the owner-approved scoped commit.

## Assertion

> **ASSERT-003** — M4 (AI Advisor) does not spam or send messages in bulk outside an approved flow.

## Status

**SATISFIED BY STRUCTURE, no code change.** M4 has no scheduler, no asynchronous trigger, no message
queue listener, no retry sender and no platform client capable of sending a message to a customer.
Every entry point is a synchronous single-turn request/response. The evidence below is structural —
counts and file references — not an assurance statement.

## Evidence 1 — no automatic trigger exists

Scan over `back-end/src/main/java/com/ginsengfood/project/ai/` (the entire M4 main tree):

| Pattern | Occurrences | Pattern | Occurrences |
|---|---:|---|---:|
| `@Scheduled` | **0** | `ExecutorService` | **0** |
| `@Async` | **0** | `CompletableFuture` | **0** |
| `@EventListener` | **0** | `new Thread` | **0** |
| `@TransactionalEventListener` | **0** | `TaskScheduler` | **0** |
| `@KafkaListener` | **0** | `@Retryable` | **0** |
| `@RabbitListener` | **0** | `RestTemplate` | **0** |
| `@JmsListener` | **0** | `WebClient` | **0** |
| `ApplicationRunner` | **0** | `FeignClient` | **0** |
| `CommandLineRunner` | **0** | `@EnableScheduling` | **0** |
| `@PostConstruct` | **0** | `@EnableAsync` | **0** |

**0 occurrences across all 20 patterns.** There is no mechanism by which M4 can initiate work without
an inbound request.

This count is enforced as a test, not left as a claim:
`ResponseChannelSurfaceStructuralTest.noOutboundOrScheduledTriggerExists` fails the build if any of
the 20 patterns appears. If one ever does, ASSERT-003 stops being an evidence-only deliverable and
must go back to the owner.

## Evidence 2 — every entry point is synchronous and single-turn

M4 exposes **14** `@RestController` classes in `ai/`: **3 runtime** and **11 admin/CRUD**.

*(The earlier M6 review note referred to "2 endpoints". That count was low; the full inventory is
below.)*

### Runtime controllers — the customer-facing surface

| Controller | Endpoints | Shape |
|---|---|---|
| `runtime/api/M4AdvisorTurnController.java` | `POST /api/v1/m4/advisor/turn` | synchronous, one turn per call |
| `runtime/api/AiCustomerAdvisorChatController.java` | `POST /api/v1/ai/advisor/chat`, `/query`, `/cart-actions/add` | synchronous, one turn per call |
| `runtime/api/AiInternalInformationalChatController.java` | `POST /api/v1/internal/ai/informational-chat` | synchronous, internal-facing |

Each returns its response directly to the caller. None schedules follow-up work, enqueues a message,
or writes to an outbox for another process to deliver.

### Admin controllers — no send path

`api/AdminAiConsultationLeadController` · `api/AiBrandKnowledgeAdminController` ·
`api/AiConsultationLeadController` · `api/AiContentBindingAdminController` ·
`api/AiContentBlockAdminController` · `api/AiCustomerAdvisorChatHistoryController` ·
`api/AiDecisionLogAdminController` · `api/AiIntentRegistryAdminController` ·
`api/AiProductApprovedContentAdminController` · `api/AiProductEffectivenessAdminController` ·
`api/AiSkuRuleAdminController`

These manage knowledge, content, intents and review records. None of them delivers a message to a
customer channel.

## Evidence 3 — the only outbound client is the LLM adapter

The single outbound HTTP client in the M4 tree is `java.net.http.HttpClient` in:

- `runtime/adapter/gemini/GeminiRealProviderClient.java:5, 64`
- `runtime/adapter/gemini/JdkGeminiHttpTransport.java:4, 12, 14`

This calls the **Gemini LLM provider** to generate advisory text. It is not a messaging client: it has
no customer recipient, no channel, and no send semantics. Enforced by
`ResponseChannelSurfaceStructuralTest.onlyOutboundHttpClientIsTheLlmAdapter`, which fails if an HTTP
client appears anywhere outside `runtime/adapter/gemini/`.

## Evidence 4 — delivery is not M4's responsibility, and the gateway port is closed

Per owner decision `OWN-008`, M4 decides and M5/M7 execute delivery. The one gateway-facing port in
M4, `GatewayChannelPortImpl`, returns a blocked envelope on every path — there is no code path in
which it calls a real provider.

## Conclusion

M4 cannot, by construction, emit unsolicited or bulk messages:

1. nothing can trigger M4 without an inbound HTTP request (Evidence 1);
2. every inbound request produces exactly one synchronous response (Evidence 2);
3. M4 owns no client capable of sending a message to a customer (Evidence 3);
4. delivery belongs to M5/M7, and M4's gateway port is closed (Evidence 4).

## Scope and limits — read before citing this file

- **This is a structural argument about M4's source tree**, not a runtime observation. It states what
  the code cannot do, not what a deployed system was observed doing.
- **Rate limiting, deduplication and allow-listing on the actual send path are M5's controls**
  (ASSERT-006), not M4's. M4 having no sender is not a substitute for those; both halves of
  `M6-ENTRY-004` are required.
- **M5/M7 are in a different repository and were not read.** Any statement about their behaviour is
  `EXTERNAL_NOT_VERIFIED` (`OWN-009`).
- **Live/M7 routing:** M4 supports `LIVE_COMMENT`/`LIVE_MC` at `/turn`; whether M7 actually routes
  through `/turn` is `EXTERNAL_NOT_VERIFIED`.
- **CI is currently disabled** in this repository (task `FND-005`), so the structural tests backing
  Evidence 1 and 3 do not re-run automatically yet.

## Sign-off

| Role | Status |
|---|---|
| Coder (M4) | **attempt 4 — correction pass `C3-03`** (Codex: a clause-scoped tail check let a line-broken or punctuation-split address pass as a delivery date). Together with attempt 3 and the `C3-01`/`C3-02` pass this closes Tester `T2-01`/`T2-02`/`T2-03`, **all inside `PIIExposureGuard`** — the PII detector, which ASSERT-003 does not rely on. **This assertion stays evidence-only and no file it covers has changed in any pass**; the structural counts below are unaffected. Self-verified only |
| Tester (M4) | **attempt 1 = `FAIL`** — finding `T-01` (AC-2.4 false positive) reproduced 5/5; see `SAFE-001.md` §16. **attempt 2 = `FAIL`** — 13 AC PASS / 2 FAIL; both failures (`T2-01`, `T2-02`) are in the PII guard. The no-spam claims of this file were re-verified independently and still hold: **0/20** outbound/scheduler patterns, **14** controllers, `HttpClient` only under `runtime/adapter/gemini/`. See `SAFE-001.md` §20. **attempt 3 = never opened** — the owner held it back when Codex raised `C3-03`. **attempt 4 = `FAIL`** — the blocker (`T4-01`, P1) is in the PII guard, **not** in the no-spam claims of this file. Those were re-measured independently once more and still hold: **0/20** outbound/scheduler patterns (per-pattern count), **14** controllers = 11 admin + 3 runtime, `java.net.http.HttpClient` only in `runtime/adapter/gemini/` (2 files). See `SAFE-001.md` §24. **attempt 5 = `PASS`** — ASSERT-003 re-measured independently a third time, per-pattern, and unchanged: **0/20**, **14** controllers (11 admin + 3 runtime, all named), `HttpClient` only in the two Gemini adapter files. Noted for precision: `GeminiHttpTransport.java` imports `HttpRequest` but **not** `HttpClient`, and this file correctly does not cite it. Every citation in this file verified. See `SAFE-001.md` §27 |
| Judge (M4) | pending |
| Owner (M4) | pending |
| Joint `M6-ENTRY-004` gate | **BLOCKED** — the M5 half (ASSERT-004/005/006) is `EXTERNAL_NOT_VERIFIED`; both halves are required |
