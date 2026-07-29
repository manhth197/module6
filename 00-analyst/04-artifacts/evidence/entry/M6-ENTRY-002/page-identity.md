# M6-ENTRY-002 · Artifact 1/4 — PAGE IDENTITY (ASSERT-001)

- **Đơn:** M6-ENTRY-002 (Gateway / Module 5 → Module 6)
- **Claim chứng minh:** ASSERT-001 — *Page identity: mỗi page có định danh ổn định (`page_id`) trong hệ Gateway.*
- **Nguồn (provenance):** repo M5 `Module5-workspace/01-coder/module5-app`, commit `87fad536a4a18f2a6c2493c784ed719e493c182e` (short `87fad53`).
- **PII/secret:** KHÔNG có PII thô. `tokenRef` chỉ là con trỏ `secret_ref://…`; row mang token thô bị DROP. ID trong ví dụ là placeholder coded (`MOCK-PAGE-0001`), không phải page_id Meta thật.

---

## E1 — Định danh page ổn định (domain `PageContext`)
`src/channel-identity/domain/page-context.ts:8-22`
```ts
export interface PageContext {
  sourcePageId: string;
  pageName: string;
  pageRole: PageRole;
  commerceHubPageId: string;
  channelCode: ChannelCode;
  appMode: AppMode;
  hasMessagingCapability: boolean; // token capability; missing => fail closed, no delivery
  tokenRef: string; // secret_ref only
  ...
}
```
`sourcePageId` (page_id nguồn) + `commerceHubPageId` (page_id hub thương mại) là định danh page ổn định; `pageRole` = HUB|SPOKE. `tokenRef` chỉ giữ con trỏ secret_ref (không token thô).

## E2 — Port phân giải page_id → identity (unknown ⇒ null ⇒ quarantine)
`src/channel-identity/ports/page-registry.port.ts:8-10`
```ts
export interface PageRegistryPort {
  resolve(sourcePageId: string): PageContext | null;
}
```
Doc port (:3-7): *"Returns the known PageContext for a canonical source page ID, or null when the page is unknown/forged (→ quarantine, no delivery)."* → page_id có định danh → resolve ra context; page lạ/giả → `null` → cách ly, không gửi.

## E3 — Adapter thật: registry page_id do owner cấu hình (secret_ref-safe)
`src/channel-identity/adapters/real/config-page-registry.ts:45-47, 90-91`
```ts
resolve(sourcePageId: string): PageContext | null {
  return this.pages.get(sourcePageId) ?? null;
}
...
// tokenRef MUST be a secret_ref pointer — reject any row that carries a raw token.
const tokenRef = str(r.tokenRef);
if (!tokenRef.startsWith(SECRET_REF_PREFIX)) return null;
```
`ConfigPageRegistry` nạp `Map<sourcePageId, PageContext>` từ config owner (`M5_PAGE_REGISTRY_JSON`/`_FILE`); mỗi page_id → 1 PageContext ổn định. Row có token thô bị loại → page_id không bao giờ đi kèm secret thô. Bind khi `PAGE_REGISTRY_MODE=config`; mặc định vẫn MOCK.

## E4 — page_id được mang trên contract output (NCE)
`src/channel-identity/contracts/normalized-channel-event.ts:37-40`
```ts
export interface NormalizedChannelEvent {
  ...
  sourcePageId: string;
  commerceHubPageId: string;
  pageName: string;
  pageRole: PageRole;
```
Mỗi event chuẩn hoá luôn stamp `sourcePageId` + `commerceHubPageId` → định danh page bám theo toàn chuỗi.

---

### Kết luận ASSERT-001 — **PROVEN**
Gateway có định danh page ổn định (`sourcePageId`/`commerceHubPageId`) làm khoá phân giải qua `PageRegistryPort.resolve()`; adapter thật nạp từ config owner, page lạ → `null` (fail-safe), token luôn là `secret_ref`. Ví dụ ID coded ổn định: `MOCK-PAGE-0001`.
