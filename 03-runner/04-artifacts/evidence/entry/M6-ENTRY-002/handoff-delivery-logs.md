# M6-ENTRY-002 · Artifact 4/4 — HANDOFF & DELIVERY LOGS (ASSERT-005 + ASSERT-006)

- **Đơn:** M6-ENTRY-002 (Gateway / Module 5 → Module 6)
- **Claim chứng minh:**
  - ASSERT-005 — *Handoff logs tồn tại: chuyển comment → inbox / bàn giao người có log.*
  - ASSERT-006 — *Delivery logs tồn tại: trạng thái gửi/nhận message được ghi log.*
- **Nguồn (provenance):** repo M5 `Module5-workspace/01-coder/module5-app`, commit `87fad53`.
- **PII/secret:** KHÔNG có PSID/PII thô, KHÔNG có message body. Handoff row & delivery log chỉ chứa ref coded/hashed + enum; endpoint từ chối 400 nếu body có shape PII thô. `production=OFF`/gateway BLOCKED không bị đụng — đây chỉ là bằng chứng contract + log, không bật runtime gửi thật.

---

## PHẦN A — HANDOFF LOGS (ASSERT-005)

### E1 — Ledger row `comment_handoff` bền, khoá UNIQUE theo comment_id (chỉ ref coded)
`src/comment-boundary/ports/comment-handoff-writer.port.ts:11-30`
```ts
export interface CommentHandoffRow {
  handoffId: string;
  commentId: string; // UNIQUE — one durable handoff per comment
  liveSessionId?: string; // coded MOCK-LIVE ref when the comment came from a live session
  sourcePageId: string;
  targetThreadId?: string; // messenger thread ref once known (undefined at first record)
  status: HandoffStatus;
  reason: HandoffReason;
  contextSnapshot: Readonly<Record<string, string>>; // coded refs / enums ONLY — no raw text/PII
}
...
export interface CommentHandoffWriterPort {
  record(row: CommentHandoffRow): Promise<CommentHandoffRow>;
}
```
Doc (:3-9): mirror SPEC §11 `comment_handoff`; mọi field là ref coded/masked hoặc enum — KHÔNG raw comment text / PSID / phone. `commentId` UNIQUE = "no duplicate handoff".

### E2 — Writer thật (Prisma) ghi log bền, idempotent theo comment_id
`src/comment-boundary/adapters/real/prisma-comment-handoff-writer.ts:32, 45-50`
```ts
async record(row: CommentHandoffRow): Promise<CommentHandoffRow> {
  ...
  const saved = (await this.prisma.commentHandoff.upsert({
    where: { commentId: row.commentId },
    create,
    update: {},
  })) as CommentHandoffRecord;
  return PrismaCommentHandoffWriter.toRow(saved);
}
```
Upsert theo `commentId`: lần đầu tạo row; lặp lại trả row cũ (cùng `handoffId`) — DB `@unique comment_id` là cổng "no duplicate handoff". Bind khi `COMMENT_HANDOFF_STORE=prisma`; mặc định in-memory.

### E3 — Endpoint handoff comment → inbox có ghi log (RBAC, chặn PII thô, response masked)
`src/comment-boundary/http/handoff.controller.ts:46-59, 90-102`
```ts
@Controller('api/channel/handoff')
@UseGuards(RbacGuard)
export class HandoffController {
  ...
  @Post('messenger')
  @HttpCode(200)
  @RequirePermission(Permission.GATEWAY_HANDOFF_SEND)
  async messenger(@Body() body: HandoffSendBody): Promise<MaskedHandoffResponse> {
    if (containsSensitive(JSON.stringify(body ?? {}))) {
      throw new BadRequestException('RAW_PII_REJECTED: supply an already-hashed customerRef');
    }
    ...
    const recorded = await this.handoffWriter.record({ ...
      contextSnapshot: {
        capability: handoff.platformPrivateReplyCapability,
        customerRef: handoff.customerRef, // hashed cust_ref
        hubPageRef: 'page_ref:' + sha256b64(commerceHubPageId),
      },
    });
```
POST `/api/channel/handoff/messenger`: RBAC deny-by-default, từ chối 400 nếu body có PII thô, ghi durable `comment_handoff` row (idempotent), trả về masked (chỉ status coded + handoffId).

---

## PHẦN B — DELIVERY LOGS (ASSERT-006)

> **Phạm vi (trung thực):** `delivery_log` ghi trạng thái **GỬI / kết-quả terminal** của message outbound (SENT + provider send-receipt, hoặc BLOCKED/FAILED/RETRYING/DEAD_LETTER…). Enum KHÔNG có trạng thái *read-receipt* của người nhận. Chiều **NHẬN** (message/comment inbound tới) được ghi log RIÊNG ở đường ingest (`ingest_forward`/`ingest_deadletter`) — xem E9. Hai log tách bạch, không gộp claim.

### E4 — Shape bản ghi `delivery_log` (SENT chỉ khi thật gửi, recipient masked, no body)
`src/outbound-guard/contracts/delivery-log.ts:11-25`
```ts
export interface DeliveryLog {
  deliveryId: string;
  status: DeliveryStatus;
  failReasonCode?: FailReasonCode; // required for every non-SENT terminal
  recipientRef: string; // masked/internal
  providerMessageId?: string; // set only on SENT
  sentAt?: string; // set only on SENT
  correlationId: string;
  idempotencyKey: string; // scope=OUTBOUND
  checkpoint: Checkpoint; // the terminal re-check checkpoint the status reflects
  retryCount?: number;
  evidenceRef: string;
  createdAt: string; // ISO-8601
}
```
Doc (:3-9): *"SENT (with provider_message_id + sent_at) is recorded ONLY on an actual send after a FinalGuard-PASS … a blocked/failed delivery NEVER records SENT … stores NO message body … only a MASKED recipient ref — no raw PSID/token (V8)."* `providerMessageId`+`sentAt` trên SENT = provider đã **nhận** lệnh gửi (send-receipt).

### E5 — Taxonomy trạng thái GỬI/terminal (không read-receipt)
`src/outbound-guard/domain/enums.ts:16-28`
```ts
/** CON-008 delivery_log status. Only SENT is an actual send (after guard PASS). */
export enum DeliveryStatus {
  QUEUED = 'QUEUED',
  SENT = 'SENT',
  FAILED = 'FAILED',
  RETRYING = 'RETRYING',
  DEAD_LETTER = 'DEAD_LETTER',
  SUPPRESSED = 'SUPPRESSED',
  BLOCKED_GUARD = 'BLOCKED_GUARD',
  BLOCKED_SUPPRESSION = 'BLOCKED_SUPPRESSION',
  BLOCKED_WINDOW = 'BLOCKED_WINDOW',
  BLOCKED_POLICY = 'BLOCKED_POLICY',
}
```
Toàn bộ là trạng thái **outbound gửi/terminal**; mỗi terminal không-SENT mang `FailReasonCode` (enums.ts:31-50).

### E6 — Nơi delivery_log được **TẠO + GHI** ở MỌI terminal (không chỉ contract)
`src/outbound-guard/outbound-dispatcher.ts:325-335` (build) + `:269,251,288,294,303` (emit mỗi terminal)
```ts
// buildLog — tạo 1 DeliveryLog cho mọi terminal:
private buildLog(
  deliveryId: string, status: DeliveryStatus, failReasonCode: FailReasonCode | undefined, recipientRef: string,
  correlationId: string, outboundKey: string, providerMessageId: string | undefined, sentAt: string | undefined,
  checkpoint: Checkpoint, retryCount?: number,
): DeliveryLog {
  return {
    deliveryId, status, failReasonCode, recipientRef, providerMessageId, sentAt,
    correlationId, idempotencyKey: outboundKey, checkpoint, retryCount, // DEV-18: set only on RETRYING/DEAD_LETTER
    evidenceRef: 'ev_ref:' + safeId('e'), createdAt: new Date().toISOString(),
  };
}
// SENT terminal (:268-270):
const log = this.buildLog(deliveryId, DeliveryStatus.SENT, undefined, recipientRef, correlationId, outboundKey, receipt.providerMessageId, receipt.sentAt, checkpoint);
await this.emit('delivery_command', correlationId, command);
await this.emit('delivery_log', correlationId, log);
await this.audit('DELIVER', 'SENT', recipientRef);
// Blocked terminal (:302-304): await this.emit('delivery_log', correlationId, log); await this.audit('DELIVER', blockedStatus, recipientRef);
// RETRYING/DEAD_LETTER terminal (:293-295): await this.emit('delivery_log', correlationId, retryLog);
```
Mọi nhánh terminal (SENT / BLOCKED_POLICY self-gate :251 / retry-paused :288 / retry :294 / blocked :303) đều build 1 `delivery_log` và `emit('delivery_log', …)` — bằng chứng log THỰC SỰ được sinh, không phải chỉ khai báo type.

### E7 — `emit()` → persist qua EvidenceService (fail-closed mask) + mirror sang Audit
`src/outbound-guard/outbound-dispatcher.ts:361-363, 371-373`
```ts
private async emit(kind: string, correlationId: string, payload: unknown): Promise<void> {
  await this.evidence.emit({ correlationId, kind, payload });
}
private async audit(action: string, decision: string, targetRef: string): Promise<void> {
  await this.auditService.record({ correlationId: this.correlation.current(), actorRole: Role.GATEWAY, action, decision, targetRef });
}
```
`EvidenceService.emit` `deepMask` payload rồi persist vào repository, **FAIL CLOSED** nếu còn shape nhạy cảm (`evidence.service.ts:17-21`) → delivery_log được lưu bền, đã mask. Song song `audit('DELIVER', status, recipientRef)` ghi 1 dòng audit append-only mỗi terminal.

### E8 — Endpoint delivery đi qua 1 chokepoint dispatcher (self-gate chặn sink thật khi production OFF)
`src/outbound-guard/http/delivery.controller.ts:57-72, 97-98`
```ts
@Controller('api/channel/delivery')
@UseGuards(RbacGuard)
export class DeliveryController {
  ...
  @Post('send')
  @HttpCode(200)
  @RequirePermission(Permission.GATEWAY_DELIVERY_SEND)
  async send(@Body() body: DeliverySendBody): Promise<MaskedDeliveryResponse> {
    if (containsSensitive(JSON.stringify(body ?? {}))) {
      throw new BadRequestException('RAW_PII_REJECTED: ...');
    }
    const result = await this.dispatcher.dispatch(this.buildRequest(body));
    return this.mask(result);
  }
  ...
  const status = r.deliveryLog?.status ?? ...;
```
Doc (:51-55): *"every send flows through the single `OutboundDispatcher` chokepoint, whose DEV-12 self-gate hard-blocks a REAL-tier sink while production is OFF … The DEFAULT bound sink is the MOCK, so no real send is possible here."* Response masked, không body/PSID thô.

### E9 — Chiều NHẬN (inbound) được log riêng ở ingest (`ingest_forward` / `ingest_deadletter`)
`src/channel-identity/ingest-pipeline.service.ts:76, 72, 82, 88-92`
```ts
// forward thành công:
await this.emit(correlationId, { commentRef: this.commentRefFor(nce), forwarded: true, reason: 'FORWARDED' });
// bị skip:
await this.emit(correlationId, { commentRef: this.commentRefFor(nce), forwarded: false, reason: mapped.reason });
// dead-letter:
await this.evidence.emit({ correlationId, kind: 'ingest_deadletter', payload: { commentRef, reason, forwarded: false } });
private async emit(correlationId, payload): Promise<void> {
  await this.evidence.emit({ correlationId, kind: 'ingest_forward', payload });
}
```
Message/comment **nhận về** (inbound) qua `ingest()` được ghi evidence `ingest_forward` (forwarded + reason) / `ingest_deadletter` — log inbound tách bạch với `delivery_log` outbound.

### E10 — Audit append-only chỉ ref coded
`src/foundation/audit/audit.types.ts:1-8`
```ts
/** A single append-only audit entry. Carries refs + coded fields only — never PII/secret. */
export interface AuditEntry {
  correlationId: string;
  actorRole: string;
  action: string;
  decision: string;
  targetRef?: string;
}
```

---

### Kết luận ASSERT-005 — **PROVEN**
Handoff comment → inbox/bàn giao người có log bền: ledger `comment_handoff` (UNIQUE comment_id), writer Prisma thật idempotent (upsert), endpoint `/api/channel/handoff/messenger` RBAC + ghi row masked.

### Kết luận ASSERT-006 — **PROVEN (phạm vi nêu rõ)**
Trạng thái **gửi/terminal** của message được ghi log THỰC SỰ: dispatcher `buildLog` + `emit('delivery_log')` ở mọi terminal → `EvidenceService.emit` persist (fail-closed mask) + `audit('DELIVER', …)` append-only; SENT mang provider send-receipt (`providerMessageId`/`sentAt`), recipient masked, no body. Chiều **nhận (inbound)** được log riêng qua `ingest_forward`/`ingest_deadletter`. Enum `DeliveryStatus` là trạng thái outbound/terminal (không có read-receipt) — claim đã thu hẹp đúng thực tế code.
