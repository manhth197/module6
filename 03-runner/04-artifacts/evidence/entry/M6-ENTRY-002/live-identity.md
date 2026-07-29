# M6-ENTRY-002 · Artifact 2/4 — LIVE IDENTITY (ASSERT-002)

- **Đơn:** M6-ENTRY-002 (Gateway / Module 5 → Module 6)
- **Claim chứng minh:** ASSERT-002 — *Live identity: live session có định danh (`live_id`/session) map về page.*
- **Nguồn (provenance):** repo M5 `Module5-workspace/01-coder/module5-app`, commit `87fad53`.
- **PII/secret:** KHÔNG có PII thô. `live_session_id` bắt buộc là ref coded (vd `MOCK-LIVE-0001`); một run ≥10 chữ số (shape id/PSID/phone Meta thật) bị DROP nên id Meta thô không thể bị stamp/forward. `primaryCampaignId` là INTERNAL_ONLY — không nạp, không surface.

---

## E1 — Định danh live session + map về page (domain `LiveSessionContext`)
`src/channel-identity/domain/live-session-context.ts:9-16`
```ts
export interface LiveSessionContext {
  liveSessionId: string;
  pageId: string;
  liveType: string;
  title: string;
  status: string;
  primaryCampaignId?: string; // INTERNAL_ONLY — never public, never on the NCE
}
```
`liveSessionId` = định danh live; `pageId` = map live → page. Doc (:1-8): mirror SPEC §11 `live_session`, mock dùng `MOCK-LIVE-####` (không bao giờ id live-video/PSID Meta thật).

## E2 — Port phân giải live_id → identity (unknown ⇒ null ⇒ fail-safe)
`src/channel-identity/ports/live-session-registry.port.ts:9-11`
```ts
export interface LiveSessionRegistryPort {
  resolve(liveSessionId: string): LiveSessionContext | null;
}
```
Doc (:3-8): *"Returns the known LiveSessionContext for a live-session id, or null when the id is unknown/absent (→ no stamp, FAIL-SAFE: the pipeline continues, nothing throws)."*

## E3 — Adapter thật: map REAL Meta live-video-id → coded live_session_id
`src/channel-identity/adapters/real/config-live-session-registry.ts:61-63, 106-110`
```ts
resolve(liveKey: string): LiveSessionContext | null {
  return this.sessions.get(liveKey) ?? null;
}
...
// The STAMPED session id must be a coded ref: non-empty, ≤36 chars, and NOT a raw ≥10-digit Meta id.
const liveSessionId = toIdStr(r.liveSessionId);
if (!liveSessionId || liveSessionId.length > MAX_LIVE_SESSION_ID_LEN || LONG_DIGIT_RUN.test(liveSessionId)) {
  return null;
}
```
Doc (:38-39): *"maps a REAL Meta live-video-id (the KEY) → a coded live_session_id (the VALUE, e.g. the M7-seeded `MOCK-LIVE-0001`) so a real Facebook live comment stamps a session M7 recognises."* → live_id thật được phân giải thành session coded ổn định; id ≥10 chữ số bị loại; `primaryCampaignId` cố ý KHÔNG nạp (:44-45). Bind khi `LIVE_REGISTRY_MODE=config`; mặc định MOCK.

## E4 — live_session_id mang trên contract output (NCE)
`src/channel-identity/contracts/normalized-channel-event.ts:46`
```ts
  liveSessionId?: string;
```
Live-comment được stamp `liveSessionId` (undefined cho comment không-live → egress tự nhiên bỏ qua M7).

---

### Kết luận ASSERT-002 — **PROVEN**
Live session có định danh coded ổn định (`liveSessionId`) map về `pageId`, phân giải qua `LiveSessionRegistryPort.resolve()`; adapter thật map id Meta thật → session coded (loại id ≥10 chữ số), id lạ → `null` (fail-safe). Ví dụ ID coded: `MOCK-LIVE-0001` → `pageId` tương ứng.
