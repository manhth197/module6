# M6-ENTRY-002 · Artifact 3/4 — COMMENT & MESSENGER IDENTITY (ASSERT-003 + ASSERT-004)

- **Đơn:** M6-ENTRY-002 (Gateway / Module 5 → Module 6)
- **Claim chứng minh:**
  - ASSERT-003 — *Comment identity: comment có định danh (`comment_id`) + map về page/live/người dùng (PSID **đã mask**).*
  - ASSERT-004 — *Messenger identity: thread/PSID messenger có định danh (**đã mask**).*
- **Nguồn (provenance):** repo M5 `Module5-workspace/01-coder/module5-app`, commit `87fad53`.
- **PII/secret:** KHÔNG có PSID/PII thô. `psidHash` là hash keyed page-scoped (không bao giờ PSID thô); `userRef`/`customerRef` là ref hashed/internal; mapper fail-closed nếu author ref không phải hashed-ref hợp lệ.

---

## PHẦN A — COMMENT IDENTITY (ASSERT-003)

### E1 — comment_id + map page/live/user trên contract (NCE)
`src/channel-identity/contracts/normalized-channel-event.ts:16-21, 44-60`
```ts
export enum ChannelCode {
  COMMENT = 'COMMENT',
  MESSENGER = 'MESSENGER',
  LIVE_COMMENT = 'LIVE_COMMENT', // C0-S3 (SPEC §9.2): a comment on a live video (FB-03 seam → M7)
  POST_COMMENT = 'POST_COMMENT', // C0-S3 (SPEC §9.2): a comment on a page post
}
...
  userRef: string; // masked/internal user ref; NEVER a raw PSID
  ...
  liveSessionId?: string;
  commentId?: string;
  messengerThreadId?: string;
  ...
  psidHash?: string; // page-scoped keyed hash; never raw PSID
```
`commentId` định danh comment; cùng event mang `sourcePageId`/`commerceHubPageId` (→ page), `liveSessionId` (→ live), `userRef`/`psidHash` (→ user, đã mask). `channelCode` phân biệt COMMENT vs LIVE_COMMENT vs POST_COMMENT.

### E2 — comment_id là khoá bắt buộc + author ref chỉ hashed (fail-closed)
`src/channel-identity/mappers/public-comment-event.mapper.ts:16-21, 25-34`
```ts
const ALLOWED_AUTHOR_REF_PREFIXES = ['user_ref:', 'cust_ref:', 'psid_hash:', 'psid_ref:', 'hmac-'];
function isSafeAuthorRef(ref: string): boolean {
  return ref.length > 0 && ALLOWED_AUTHOR_REF_PREFIXES.some((p) => ref.startsWith(p)) && !containsSensitive(ref);
}
...
  const commentId = nce.commentId ?? '';
  if (commentId.trim().length === 0) {
    return { ok: false, reason: 'M5_MAP_SKIP:NO_COMMENT_ID' };
  }
  const authorRef = nce.psidHash ?? nce.userRef ?? '';
  if (!isSafeAuthorRef(authorRef)) {
    return { ok: false, reason: 'M5_MAP_SKIP:UNSAFE_AUTHOR_REF' };
  }
```
Comment thiếu `commentId` → skip có tên (không bao giờ `commentId = eventId`). Author ref phải là hashed-ref hợp lệ + không còn shape PII, ngược lại fail-closed (không PSID thô nào vượt biên).

---

## PHẦN B — MESSENGER IDENTITY (ASSERT-004)

### E3 — thread messenger + PSID hashed trên NCE
`src/channel-identity/contracts/normalized-channel-event.ts:17, 48, 60`
```ts
  MESSENGER = 'MESSENGER',
  ...
  messengerThreadId?: string;
  ...
  psidHash?: string; // page-scoped keyed hash; never raw PSID
```
`messengerThreadId` định danh thread; `psidHash` định danh người dùng messenger dạng hash page-scoped.

### E4 — customerRef + targetThreadId trên handoff messenger (không PSID thô)
`src/comment-boundary/contracts/messenger-handoff-request.ts:14-33`
```ts
export interface MessengerHandoffRequest {
  handoffId: string;
  ...
  commentId: string; // idempotency source
  handoffReason: HandoffReason;
  customerRef: string; // hashed/internal ref; never raw PSID
  ...
  liveSessionId?: string;
  targetThreadId?: string;
  handoffStatus: HandoffStatus;
  ...
}
```
Doc (:10-12): *"`customerRef` is a masked/hashed internal ref, NEVER a raw PSID (V7)."* `targetThreadId` = ref thread messenger.

### E5 — Port map PSID → customer_ref (không bao giờ trả PSID thô)
`src/comment-boundary/ports/identity-map.port.ts:6-9`
```ts
export interface IdentityMapPort {
  /** Return a stable, hashed/internal customer ref for a (mock) author ref. Never returns a raw PSID. */
  toCustomerRef(authorRef: string): string;
}
```

---

### Kết luận ASSERT-003 — **PROVEN**
Comment có định danh `commentId` (khoá bắt buộc), map về page (`sourcePageId`/`commerceHubPageId`), live (`liveSessionId`), user (`userRef`/`psidHash` đã mask); mapper fail-closed chặn author ref không hashed.

### Kết luận ASSERT-004 — **PROVEN**
Thread/PSID messenger có định danh (`messengerThreadId`/`targetThreadId` + `psidHash`/`customerRef`), tất cả ở dạng hashed/masked; `IdentityMapPort` không bao giờ trả PSID thô.
