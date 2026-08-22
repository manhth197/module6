# M4 Evidence — ASSERT-002: AI content does not leak customer PII to a public channel

> **Dossier:** `M6-ENTRY-004` (joint Module 4 + Module 5). This file covers the **M4 half only**.
> **Task:** `SAFE-001` — Public/private surface guard. **Owner decisions:** `OWN-013`, `OWN-014`.
> **Verified against execution baseline:** `79668115d79f633c97cf4490c51af35041d440f7` (branch `dev015`).
>
> **Location note.** See `m4-no-final-price-public.md` — M4 evidence lives in this directory; the
> `04-artifacts/...` path in the M6 template belongs to the M6 repository.
>
> **This file deliberately contains no commit SHA and no SHA-256 of itself.** Both are recorded in
> `SAFE-001.md` §Commit receipt after the owner-approved scoped commit.

## Assertion

> **ASSERT-002** — M4 (AI Advisor) content does not expose customer PII on a public channel.

## Status

**IMPLEMENTED — PENDING INDEPENDENT TESTER + JUDGE.** Not closed.

Two gaps existed at the reviewed baseline: two PII classes named in the assertion were not detected at
all, and — more seriously — the guard was being skipped entirely on exactly the turns that needed it.
Both are addressed and covered by tests, but this file records **Coder self-verification only**.

**Do not read this as "no customer address can leak".** Detection is pattern-based and has a stated
ceiling (see §Pattern design). It closes the forms listed below; it is not a complete address parser.
ASSERT-002 should be treated as satisfied for those forms and **open** for anything outside them.

## What was wrong

**Gap 1 — coverage.** `PIIExposureGuard` carried patterns for **phone** and **email** only. `ADDRESS`
and `PSID`, both named explicitly in ASSERT-002, were detected nowhere in the M4 tree. Every
occurrence of "address" in `ai/` was a `shippingAddressId` business identifier in the order flow, not
PII masking.

**Gap 2 — enforcement (the more serious one).** `PIIExposureGuard` and `PublicPrivateSurfaceGuard`
share the same fail-closed shape: they only apply the public-safe rules when the surface is public or
`null`. `M4AdvisorTurnService` never produced `null` — it substituted a concrete **private** surface
for any untagged turn. So on an untagged public turn the PII guard returned `pass()` at its first
line and never inspected the text.

**These two assertions share one root cause.** Adding ADDRESS and PSID patterns without fixing surface
classification would have added patterns that never run on the highest-risk turns. That is why
ASSERT-001 and ASSERT-002 were fixed in the same change; see `m4-no-final-price-public.md`.

## Fix — code path

| # | What | Where |
|---|---|---|
| 1 | ADDRESS signal 1 — admin/street unit bound to a number | `back-end/src/main/java/com/ginsengfood/project/ai/runtime/consumer/finalresponse/application/guard/PIIExposureGuard.java:44-47` *(corrected: Tester finding `T5-01`. The old `:41-44` pointed at the javadoc and cut the declaration off after its first line. Re-measured: `:44` opens `ADDRESS_UNIT = Pattern.compile(`, `:47` closes it with `);`, `:48` is blank, and `:41-43` is prose.)* |
| 2 | ADDRESS signal 2 — delivery label / house number / ETA, resolved by a helper | `PIIExposureGuard.java:64-69` (`DELIVERY_LABEL`), `:72-73` (`HOUSE_NUMBER`), `:80-124` (temporal parts, incl. `UNAMBIGUOUS_TIME_UNIT` `:110-111`), `:200-208` (`TEMPORAL_SPAN`, 4 shapes), `:294-312` (`mentionsDeliveryAddress`) |
| 2b | Bare `dd/mm` delivery date vs house number — context classifier (T2-02), with whole-answer tail scope (C3-01 → C3-03) and real date validation (C3-02) | `PIIExposureGuard.java:133-134` (`BARE_SLASH_DATE`), `:137` (`POLITE_TERMINAL`), `:164-165` (`TERMINAL_TAIL`), `:333-346` (`bareDeliveryDateSpans`), `:370-384` (`isValidCalendarDate`), `:387-389` (`isGluedToLetterOrDigit`), `:398-400` (`restOfAnswerIsTerminal`), `:403-410` (`followsDeliveryLabel`) |
| 3 | PSID / page-scoped-id pattern — **two id shapes** after the label: glued (no separator) or separated by a bounded digit-free filler. The label list is factored out so both shapes reuse it | `PIIExposureGuard.java:214` (`PSID_LABEL`), `:247-248` (`PSID`) |
| 3b | **T4-01 fix (attempt 5).** The single earlier form `\blabel\b[^\d\n]{0,40}\d{10,}` contradicted itself: `{0,40}` allows zero separator characters, but the trailing `\b` needs a word/non-word transition and `D`→`1` is word→word, so the zero-separator case was unreachable and `PSID1234567890123456` passed on a public surface. Measured: every *separated* form matched; the glued form matched neither the raw text nor the whitespace-stripped `compact` view — and `compact` made it worse, since stripping whitespace turns `P S I D 1234…` into exactly the glued shape. The **leading** `\b` was not touched: it is what keeps `xpsid…`, `psidfoo…`, `psidentifier…` out, and a negative corpus pins that | `PIIExposureGuard.java:216-246` (rationale in javadoc) · `PIIExposureGuardTest.psidOnPublicFails` (6 glued probes) · `PIIExposureGuardTest.psidNegativeCorpus` (8 probes) |
| 4 | Violations raised as blocking, same mechanism as phone/email | `PIIExposureGuard.java:275`, `:280` |
| 5 | Public-surface-only application (private surfaces may legitimately echo PII) | `PIIExposureGuard.java:257` |
| 6 | Guard is wired into the chain used by `/turn`, `/chat`, `/query` | `runtime/consumer/finalresponse/application/FinalResponseGuardService.java:253` |
| 7 | The surface the chain receives is now the fail-closed resolved one | `runtime/api/M4AdvisorTurnService.java:420` (raw pair, before the defaults substituted at `:411-412`) → `runtime/consumer/finalresponse/domain/ResponseChannelSurfaceResolver.java` |

### Pattern design — and why it is anchored the way it is

**ADDRESS uses two independent signals**, each carrying its own anchor:

1. **admin/street unit + number** — "Phường 5", "Quận 3", "ngõ 45", "Tổ 12", "P.5", "Q.12".
2. **delivery-intent label + house number, minus ETAs** — "Địa chỉ nhận hàng: 12 Nguyễn Trãi",
   "Giao tới 12/3A Nguyễn Trãi", and the unaccented equivalents. Labels: `địa chỉ`,
   `giao tới/đến/về`, `gửi tới/đến`, `ship tới/đến`, `nhận hàng` (+ unaccented forms).

Signal 2 was added after review: signal 1 alone missed the most common real form, a street name with
no administrative keyword at all. That form was leaking.

**Signal 2 is a set of named patterns plus a helper, not one regex** — `DELIVERY_LABEL`,
`HOUSE_NUMBER`, a structured `TEMPORAL_SPAN` composed from `TEMPORAL_CUE` / `TIME_UNIT` /
`UNAMBIGUOUS_TIME_UNIT` / `RANGE_DELIMITER` / `NUMBER_RANGE` / `EXPLICIT_NUMBER_RANGE` /
`CALENDAR_DATE`, and `mentionsDeliveryAddress`. A number counts as a house number when it follows a
delivery label within 30 characters **and** does not sit inside a temporal span.

**`TEMPORAL_SPAN` is built structurally, not as a list of literals.** Four shapes:

| # | Shape | Grammar | Examples |
|---|---|---|---|
| 1 | cued duration / time-of-day | cue + number(-range) + **any** time unit | "trong 2-3 ngày", "khoảng 2–3 tháng", "lúc 15 giờ", "trước 17 giờ", "dự kiến 15 giờ" |
| 2 | calendar date | *(optional cue)* + `ngày` + dd/mm[/yyyy] | "ngày 05/08", "vào ngày 05/08/2026" |
| 3 | **direct range** | explicit range delimiter + **any** time unit, **no cue** | "giao tới 2-3 ngày", "ship đến 2–3 giờ", "giao tới 2 đến 3 ngày" |
| 4 | **direct single** | lone number + **unambiguous** time unit, **no cue** | "giao đến 3 ngày", "ship đến 24 giờ", "giao tới 2 tuần", "giao tới 30 phút" |

**Why shapes 3 and 4 exist.** A cue-only design missed the most ordinary ETA of all, because in
"giao tới 2-3 ngày" the word `tới` **is the delivery label**, not a separate cue — there is nothing
else in front of the number. Found by a Codex red-team pass after the cue-only version had already
gone green on 79 tests.

**Why shape 4 excludes `tháng` AND `năm` — the line between an ETA and a street.** "3 Tháng 2",
"30 Tháng Tư", "19 Tháng Năm", "2 Tháng 9", "5 Nam Kỳ Khởi Nghĩa", "8 Nam Cao", "12 Nam Đồng" are
real Vietnamese streets. A bare `<number> tháng|năm` therefore stays a house-number candidate. Both
are still recognised as a duration through shape 1 ("trong 3 tháng", "trong 2 năm") or shape 3
("khoảng 2-3 tháng", "2-3 năm"), where the cue or the range delimiter supplies the missing evidence.

`năm` was removed in Coder attempt 3, after Tester finding **T2-01**: the unaccented form `nam`
collided with `Nam`, one of the most common **first** words of a Vietnamese street name — and the
first word is exactly the position that abuts the house number. Every remaining token in shape 4
(`ngày`, `giờ`, `tuần`, `phút`, `giây`) was then put to the same question. None of them starts a
common street name; the near misses are "Cầu Giấy" and "Nguyễn Tuân", where the token is the second
word so no house number abuts it, and "Gio Linh", a district written after its unit word
("huyện Gio Linh"). This is a per-token review, not an exhaustive gazetteer check — a
counter-example would be closed the same way.

### Bare `dd/mm` — classified with context, not by pattern

A delivery date written **without** the word `ngày` ("giao tới 05/08") is deliberately **not** a
fifth arm of `TEMPORAL_SPAN`. `05/08` and `12/3` are the same token; no regex over the token can
separate a date from a house number. It is resolved by
`PIIExposureGuard.bareDeliveryDateSpans(...)`, which treats a slash token as a date only when **all
four** hold, and otherwise leaves it a house number (fail-closed):

| # | Condition | Rejects |
|---|---|---|
| 1 | a delivery label within 30 chars in front | a bare date in unrelated copy |
| 2 | **a real calendar date**, validated with `java.time` | "32/13", "31/02", "31/04", "29/02/2025", "00/08" |
| 3 | no letter or digit glued to its end | "giao tới 12/3A Nguyễn Trãi" |
| 4 | nothing behind it **to the end of the answer** but punctuation and polite particles (`ạ`, `a`, `nha`, `nhé`, `nhe`) | "12/3 Lê Lợi", "12/3, Lê Lợi", "12/3 Phường 5", "05/08 tại 12/3 Lê Lợi", **"12/3.\nLê Lợi, TP HCM."**, and any bare date with a following sentence |

Added in Coder attempt 3 after Tester finding **T2-02**; conditions 2 and 4 were then corrected after
Codex review — see below.

**Condition 4 is scoped to the WHOLE ANSWER (`C3-03` — supersedes `C3-01`).** This was got wrong in
both directions before settling, so the history is recorded rather than smoothed over:

| Revision | Scope | Why it was changed |
|---|---|---|
| base attempt 3 | whole answer | code said "answer", javadoc and this file said "clause" — a real mismatch, found as `C3-01` |
| correction pass 1 | clause (`.` `!` `?` `…` newline) | resolved the mismatch by moving the **code** to match the prose. **Wrong half to move** |
| correction pass 2 — current | **whole answer**, prose corrected to match | `C3-03`: a clause boundary is a single character, so an address only has to be **split across one** for the street to fall outside the checked region |

The two shapes that escaped the clause-scoped version, both with a delivery label and a real street:

```
"Địa chỉ nhận hàng:\n12/3\nLê Lợi, TP HCM."   -> "12/3" read as a date, street never inspected
"Dạ giao tới 12/3. Lê Lợi, TP HCM."           -> same, via the full stop
```

A formatted address is normally written across lines, so this is not an exotic input. Telling those
apart from an ordinary date would require recognising "Lê Lợi" as a street — a gazetteer, which is
precisely what this guard is built to avoid. **Privacy takes precedence over the false positive**
(SPEC-040): a bare date with any further content behind it fails closed.

**The escape hatch is the ordinary way of writing a date.** "giao tới **ngày** 05/08" is recognised by
shape 2 of `TEMPORAL_SPAN` regardless of what follows, so a multi-sentence reply keeps working:
"Dạ giao tới ngày 05/08 ạ. Em sẽ báo Mình sau." is **allowed**. What is blocked is the *bare* token
plus a continuation.

A second sentence carrying its own labelled address blocks on its own account too:
"Dạ giao tới 05/08 ạ. Địa chỉ nhận hàng: 12/3 Lê Lợi." is **blocked**.

**Condition 2 is a real date check, not a range check (`C3-02`).** The first revision tested only day
1..31 and month 1..12, which the helper name and this file both overstated as "a valid calendar
date": **"31/02", "31/04" and "29/02/2025" passed**. Now:

| Form | Validated with | Effect |
|---|---|---|
| no year — "29/02", "31/04" | `MonthDay.of(month, day)` | any day the month can ever have; "29/02" stays a date because it exists in a leap year, "31/04" never exists |
| 4-digit year — "29/02/2024", "29/02/2025" | `LocalDate.of(...)` | leap year decided for real |
| 2-digit year — "05/08/26" | `LocalDate.of(2000 + yy, ...)` | **the century mapping is fixed at 2000+yy and used for validation only**; nothing downstream reads the resolved year |

No new dependency and no hand-rolled month table. An invalid date produces **no** delivery-date span,
so the token stays a house number and the reply is blocked — fail-closed.

**`tới`/`đến` are excluded from `TEMPORAL_CUE`** (they are delivery-label words) but **are** valid
`RANGE_DELIMITER` values — "2 đến 3 ngày" is a range, "giao tới 3 Tháng 2" is not.

**Address and temporal information in the same sentence:** the address wins. Each number is judged
independently, so "Giao tới 12 Nguyễn Trãi, giao 2-3 ngày" is detected on "12" while "2-3" is
suppressed; likewise "… vào ngày 05/08", "… trước 17 giờ", "… trong 3 tháng".

**Why each signal needs both halves.** The number anchor is load-bearing in this product domain:
*đường* also means **sugar**, and "đường huyết" (blood glucose), "đường ruột" (intestines), "ít đường"
(low sugar) are ordinary advisory copy here — matching a street keyword followed by any word would
block legitimate public health replies. Symmetrically, the label alone must not fire, or
"Mình cho Em xin địa chỉ qua tin nhắn riêng ạ." — a *correct* public-safe handoff reply — would be
blocked; and a house number alone would match every quantity and order code. A bare `gửi` is
deliberately excluded from the labels because "Em gửi Mình thông tin ngày 05/08" would then match.

**PSID** requires an explicit label (`psid`, `page scoped id`, `sender id`, `recipient id`) followed,
within a bounded digit-free run, by an id of **at least 10 digits**. The gap was widened after review
because natural phrasing puts words between the two ("PSID của Mình là 1234567890123456"). A bare long
digit run is deliberately **not** matched — order codes, quantities and totals are long digit runs, and
matching them would make the guard unusable on normal commerce replies.

### Known ceiling — read before treating ASSERT-002 as closed

- **A house number with a street name and no label and no admin unit is still not detected** —
  e.g. a bare "12/3A Nguyễn Trãi" with no "địa chỉ"/"giao tới" nearby and no "Phường/Quận". This form
  is uncommon in a delivery reply (the label or the ward almost always accompanies it) but it is
  **not** covered. Do not claim total address coverage.
- **~~Known false-positive class, not fixed: delivery label + date-like number~~ — FIXED, in two
  passes.** An earlier revision of this file deferred "Em gửi đến Mình thông tin ngày 05/08" as out
  of scope. That was wrong: AC-2.4 names "ngày" in the negative corpus, so it was a failing
  acceptance case, not a gap beyond acceptance. Codex reproduced it plus six more temporal shapes;
  **those exact eight probes** are covered by the calendar-date and time-of-day arms of
  `TEMPORAL_SPAN` and pinned in `PIIExposureGuardTest.deliveryDurationIsNotAnAddress`. **That closed
  eight sentences, not the class.** An earlier revision of this bullet read "all eight are now
  covered" in a way that sounded like the whole date false-positive class was shut; Tester attempt 2
  (**T2-02**) then showed it was only the arm that carries the literal word `ngày` — "giao tới 05/08"
  was still blocked. The bare-`dd/mm` classifier above closes that second arm. Read every count in
  this file as **the probes that were run**, never as a class.
- **Ceiling from T2-01 — a bare `<number> năm|tháng` next to a delivery label is BLOCKED.** Dropping
  those two tokens from shape 4 to save street names costs the reverse case: "Dạ đơn giao tới 2 năm
  ạ." is a false positive. Fail-closed direction, chosen deliberately — a blocked reply is
  recoverable by rewording, a leaked address is not. Pinned in
  `PIIExposureGuardTest.ceilingsOfTheDateVersusHouseNumberSplit` so it stays visible.
- **Ceiling from T2-02 — a house number that ends the ANSWER with nothing after it is NOT detected**,
  provided it is also a real calendar date. "Dạ giao tới 12/3 ạ." is read as a delivery date, because
  it is lexically identical to "Dạ giao tới 05/08 ạ.". On its own such a token identifies nobody; the
  moment anything at all follows ("12/3 Lê Lợi", "12/3.\nLê Lợi") it is an address again, and a house
  number that is not a valid date ("32/13", "31/02") never gets the exemption. Pinned in the same test.
- **Ceiling from C3-03 — a BARE date followed by any further content is BLOCKED.** "Dạ giao tới 05/08
  ạ. Em sẽ báo Mình khi có mã vận đơn." is a false positive, accepted deliberately: the alternative
  is the clause-scoped rule that let a line-broken address through. **The copy is recoverable** — write
  "giao tới **ngày** 05/08" and it passes regardless of what follows. Pinned in
  `PIIExposureGuardTest.bareDateWithTrailingContentFailsClosedAndNgayIsTheEscapeHatch`, which also
  asserts the `ngày` form passes, so the test cannot go vacuous by blocking everything.
- **Known false-positive class:** a *store* address on a public surface ("địa chỉ cửa hàng là 123 Lê
  Lợi") is blocked even though it is not customer PII. Chosen deliberately — privacy outranks
  commercial copy in SPEC-040's precedence, and a blocked reply is recoverable by rewording.
- Widen either pattern only together with a negative corpus that stays green.

## Behaviour after the fix

| Draft answer | Surface | Outcome |
|---|---|---|
| contains phone / email / address / PSID | `PUBLIC_COMMENT`, `LIVE_COMMENT` | **blocked**, reason `PII_EXPOSURE` |
| contains phone / email / address / PSID | untagged turn (resolves to `PUBLIC_COMMENT`) | **blocked**, reason `PII_EXPOSURE` |
| contains address / PSID | `PRIVATE_MESSENGER`, `WEB_CHAT_PRIVATE` | allowed — confirming a delivery address privately is legitimate |
| health copy ("đường huyết", "ít đường"), order codes, quantities, prices | `PUBLIC_COMMENT` | allowed — no false positive on the corpus run below |
| delivery date written with `ngày` — `ngày 05/08[/2026]` — regardless of what follows | `PUBLIC_COMMENT` | allowed |
| a **bare** `05/08` / `12/8` that ends the whole answer | `PUBLIC_COMMENT` | allowed |
| a **bare** `05/08` with any further content behind it (another sentence, a line-broken street) | `PUBLIC_COMMENT` | **blocked** — fail-closed, see the C3-03 ceiling |
| a slash token that is not a real date (`31/02`, `31/04`, `29/02/2025`, `32/13`, `00/08`) | `PUBLIC_COMMENT` | **blocked** — fail-closed, it is not a date so it stays a house number |
| a slash token with a street or admin tail (`12/3 Lê Lợi`, `12/3A Nguyễn Trãi`, `12/3 Phường 5`) | `PUBLIC_COMMENT` | **blocked** — address |
| a bare `<number> năm` / `<number> tháng` with no cue and no range, next to a delivery label | `PUBLIC_COMMENT` | **blocked** — known false positive, see the ceilings above |

*(The first row read "…, dates, … — no false positive" before Coder attempt 3. That was wider than
what had been measured: dates written without the word `ngày` were being blocked. T2-02.)*

## Tests

| Test | Covers |
|---|---|
| `PIIExposureGuardTest.addressOnPublicFails` | 52 Vietnamese address forms blocked on a public surface, including the **line-broken and punctuation-split** forms from C3-03 (`"Địa chỉ nhận hàng:\n12/3\nLê Lợi, TP HCM."`, LF / CRLF / blank-line variants) — keyword-less street names, unaccented equivalents, date-named streets ("3 Tháng 2", "30 Tháng 4", "2 Tháng 9"), **`Nam`-named streets ("5 Nam Kỳ Khởi Nghĩa", "8 Nam Cao", "12 Nam Đồng" — T2-01)**, **slash tokens with a street/admin/second-clause tail ("12/3 Lê Lợi", "12/3A Nguyễn Trãi", "12/3, Lê Lợi", "12/3 Phường 5", "32/13 Lê Lợi", "05/08 tại 12/3 Lê Lợi" — T2-02 counterweight)**, and address+temporal in one sentence |
| `PIIExposureGuardTest.psidOnPublicFails` | 9 PSID / page-scoped-id / sender-id / recipient-id forms blocked, including phrasing with words between the label and the id |
| `PIIExposureGuardTest.addressAndPsidFailClosedOnNullSurface` | undetermined surface treated as public |
| `PIIExposureGuardTest.addressAndPsidOnPrivatePasses` | no regression on private surfaces |
| `PIIExposureGuardTest.negativeCorpusPassesOnPublic` | 11-entry negative corpus: health copy, quantities, order codes, dates, sizes, public-safe handoff wording |
| `PIIExposureGuardTest.longDigitRunAloneIsNotPsid` | an order code is not a PSID |
| `PIIExposureGuardTest.untaggedSurfaceIsEnforcedThroughTheFullGuardChain` | **enforcement**: the surface an untagged turn now resolves to, run through the real `FinalResponseGuardService`, blocks phone + address + PSID |
| `PIIExposureGuardTest.recognisedPrivatePairIsNotBlockedByTheChain` | anti-vacuity for the test above — the chain blocks because of the surface, not unconditionally |
| `PIIExposureGuardTest.deliveryDurationIsNotAnAddress` | 55 delivery-time / delivery-date phrasings that must NOT be an address: the five bare-date forms from T2-02, the year-duration forms (`trong 2 năm`, `2-3 năm`) that must survive `năm` leaving shape 4, the **`ngày` multi-sentence** forms from C3-03, and the **real dates** from C3-02 (`29/02`, `29/02/2024`, `30/04`, `31/01`) |
| `PIIExposureGuardTest.ceilingsOfTheDateVersusHouseNumberSplit` | the first two ceilings this design costs, pinned rather than left to be rediscovered |
| `PIIExposureGuardTest.bareDateWithTrailingContentFailsClosedAndNgayIsTheEscapeHatch` | the third ceiling (C3-03) — a bare date with a continuation fails closed, **and** the same sentences with `ngày` pass, so the test cannot go vacuous by blocking everything |
| `PIIExposureGuardTest.phoneOnPublicFails`, `emailOnPublicFails`, `phoneOnPrivatePasses`, `phoneOnNullSurfaceFailsClosed` | pre-existing coverage, unchanged |

**147 tests in `PIIExposureGuardTest`, all passing** (4 before this task; 97 before Coder attempt 3;
120 before the C3-01/C3-02 correction pass; 138 before the C3-03 correction pass).

## Test run

Same run as `m4-no-final-price-public.md`: `./mvnw -o test -Dtest=com.ginsengfood.project.ai.**` ⇒
**3462 run · 0 failures · 26 errors · 4 skipped**, self-summed over 374 Surefire XML files rather
than read off the tally line. The 26 errors are Docker-absent `NOT_RUNNABLE` Testcontainers classes
(5 classes), 0 of them in this task's scope.

**Non-vacuity — mutations run on a copy outside the repo.** Coder attempt 3: putting `nam` back into
shape 4 ⇒ **6** tests red; treating every slash token near a label as a date ⇒ **13** red; dropping
the terminal-tail check ⇒ **5** red. Correction pass 1: reverting the tail check to the whole answer
⇒ **4** red; reverting date validation to a 1..31 / 1..12 range check ⇒ **3** red; admitting the
comma as a clause boundary ⇒ **1** red. Correction pass 2: **reintroducing the clause-boundary
exemption ⇒ 9 red**. Every check that this classifier rests on is therefore load-bearing, not
decoration.

## Scope and limits — read before citing this file

- **Enforcement is now proven THROUGH `M4AdvisorTurnService.turn()`, not only by composition**
  (AC-2.2, closed at attempt 5; Tester attempt 4 had recorded it `NOT_VERIFIED`). No new seam was
  added to `src/main`. `M4AdvisorTurnService:1054-1059` (`recommendationText`) joins
  `productPublicName` / `productEffectivenessSummary` / `heroIngredients` / `recommendationReason` /
  `suitableContext` **verbatim** and hands the result to the real `FinalResponseGuardService` at
  `:637`; those fields come from `ProductKnowledgeSourcePort`, which is already a constructor
  parameter. So a test can taint the generated answer through the production path with nothing
  mocked, stubbed out or bypassed — see
  `M4AdvisorTurnServiceTest.piiInGeneratedAnswerIsBlockedThroughTurn` (phone, address, glued PSID,
  email; asserts `deliveryAllowed=false`, `blockedReason=PII_EXPOSURE`,
  `blockedActions` contains `FINAL_RESPONSE_DELIVERY`, and that the PII is absent from the returned
  answer). Non-vacuity is pinned by
  `M4AdvisorTurnServiceTest.cleanAnswerOnUntaggedSurfaceIsStillDelivered` — the identical turn with
  clean text **is** delivered, so the block is caused by the PII and not by the untagged surface.
  AC-2.3 is pinned through the same path by
  `M4AdvisorTurnServiceTest.privatePairStillDeliversAddressThroughTurn`.
- **Still no HTTP-level test.** There is no `@SpringBootTest` in the M4 test tree, so nothing asserts
  at the controller/HTTP boundary — a pre-existing baseline gap, not introduced here. The claim above
  is bounded to the service boundary.
- **The guard blocks; it does not mask.** ASSERT-002 is satisfied by refusing to publish the reply.
  Masking/redacting instead of blocking would be a separate behaviour change, not requested here.
- **PII detection is pattern-based** and therefore bounded by the patterns listed above. It is one
  layer of the guard chain, not a complete PII classifier.
- **Structured-field leak** (as opposed to text leak) is `SAFE-003` scope.
- **CI is currently disabled** in this repository (task `FND-005`), so these tests do not re-run
  automatically yet.

## Sign-off

| Role | Status |
|---|---|
| Coder (M4) | **attempt 5** — closes Tester `T4-01` (P1/P0: a PSID glued to its label escaped the guard; the pattern now covers both id shapes, with a negative corpus pinning the untouched leading `\b`) and closes **AC-2.2** through `M4AdvisorTurnService.turn()` **without adding any seam to `src/main`**. Line citations in the table above were re-measured after the guard grew (+22 lines below the PSID block). Self-verified only. History: **attempt 4 — correction pass `C3-03`** after Codex review. History: attempt 3 closed Tester `T2-01`/`T2-02`/`T2-03`; correction pass 1 closed `C3-01` (tail scope) and `C3-02` (real date validation); **attempt 4 reverses the `C3-01` resolution** — Codex `C3-03` showed the clause-scoped tail let a **line-broken or punctuation-split address** through as a date (P0, AC-2.1). Scope is now the whole answer, with `ngày` as the documented escape hatch. Self-verified only |
| Tester (M4) | **attempt 1 = `FAIL`** — finding `T-01` (AC-2.4 false positive) reproduced 5/5; see `SAFE-001.md` §16. **attempt 2 = `FAIL`** — 13 AC PASS / 2 FAIL: `T2-01` (P0, AC-2.1 — a labelled real address is **not** detected: `giao tới 5 Nam Kỳ Khởi Nghĩa`, `8 Nam Cao`, `địa chỉ 12 Nam Đồng`, 3/3) and `T2-02` (P0, AC-2.4 — a delivery date without the word `ngày` is blocked: `giao tới 05/08`, `ship đến 12/8`, 3/3); `T2-03` (P2) records that parts of **this file** claim more than was measured. See `SAFE-001.md` §20. **attempt 3 = never opened** — the owner held it back when Codex raised `C3-03`. **attempt 4 = `FAIL`** — finding `T4-01` (P1, AC-2.1): a PSID written with the label glued to the digits (`PSID1234567890123456`, `psid1234567890123456 nha Mình`, `P S I D 1234567890123456`) is **not** detected, 3/3 reproduced. Root cause is inside the pattern this file documents: `\b` after the label makes the zero-separator case that `[^\d\n]{0,40}` explicitly allows unreachable. Every separated form (`PSID: `, `psid=`, `sender_id `) is still caught. The address work of §21–§23 was re-verified independently and holds. See `SAFE-001.md` §24. **attempt 5 = `PASS`** — `T4-01` closed and verified independently on a **fresh 95-probe corpus**: every label variant glued and separated, `P S I D` via the compact view, case/underscore/hyphen/punctuation, the **9-digit ⇒ pass / 10-digit ⇒ block** boundary, and the filler bound at 40 vs 41 for both whitespace and non-whitespace filler. Negative corpus (label as prefix/suffix/inside a word, order codes, dates, prices, quantities, bare long numbers) does not fire. **AC-2.2 now PASSES** through `M4AdvisorTurnService.turn()` and is proven non-vacuous by a mutation that drops the tainted field before the guard — the unit-level guard tests stay green under it while both service-path suites go red. One P2 finding against **this file**: `T5-01`, the ADDRESS signal 1 citation below (see the table row). See `SAFE-001.md` §27 |
| Judge (M4) | pending |
| Owner (M4) | pending |
| Joint `M6-ENTRY-004` gate | **BLOCKED** — the M5 half (ASSERT-004/005/006) is `EXTERNAL_NOT_VERIFIED`; both halves are required |
