GINSENGFOOD
MODULE 6 - ADS MEASUREMENT / ATTRIBUTION / ROAS / SCALE GATE
V0.3 CLEAN FINAL - ADS PHASE 1-3 / DATA / CONSENT / HERO SKU / GOLDEN HOUR / DIAMOND / LEARNING ENGINE

| TRẠNG THÁI KHÓA<br>READY FOR OWNER / TECH LEAD / DEV REVIEW. NOT PRODUCTION READY. NOT ROAS PASS. NOT SCALE READY. GLOBAL GATEWAY: BLOCKED. Module 6 chỉ đo lường, attribution, dashboard, data quality và đề xuất scale theo gate; không tạo doanh thu, không tạo đơn, không xác nhận thanh toán, không tự tăng ngân sách. |
|---|

[IMAGE]

Hình 1. Cấu trúc vận hành kỹ thuật Module 6 - Ads Measurement / Attribution / ROAS / Scale Gate

## 1. Document Control

| Trường | Nội dung |
|---|---|
| Mã tài liệu | GFD-M6-ADS-ROAS-TECHDESC-003 |
| Phiên bản | V0.3 Clean Final |
| Module trực quan | Module 6 - Ads Measurement / Attribution / ROAS / Scale Gate |
| Phase canonical | Phase 6 - Ads Measurement / Attribution / ROAS / Scale Gate |
| Pack canonical | PACK-07 - Ads / ROAS / Attribution |
| Nguồn bổ sung chính | ADS Phase 1-3 Implementation Lock, ADS Execution Playbook, ADS Strategy Input Pack, Keyword/Persona/Behavior/Creative Hook Library, Financial/Live Commerce baselines |
| Không phải | Code, migration, dashboard production, Meta config thật, ngân sách ads, go-live approval, scale approval |
| Global Gate | BLOCKED until P0 evidence + Owner sign-off |

## 2. Nguồn tài liệu đầu vào và thứ tự ưu tiên

MASTER - Source-of-Truth, dependency, evidence, release control.

Phase 2 - Operational Core: Inventory, release, recall, sale lock, traceability.

Phase 3 / Module 3 - Commerce Runtime: Sellable, QuoteSnapshot, Order, Payment, Shipping, Verified Revenue.

Phase 4 / Module 4 - AI Advisor Runtime: Customer context, product recommendation, Quote/Order consumer, Final Response Guard.

Phase 5 / Module 5 - Facebook Gateway: Channel identity, public/private boundary, Messenger handoff, delivery log.

Phase 6 - Ads Measurement / ROAS: Event taxonomy, attribution, verified revenue, data quality, scale gate.

Phase 7 - MC AI Live: Live script runtime and ads-safe live signal boundary.

Phase 8 - IVR Order Confirmation: Order confirmation signal, not revenue owner.

ADS Phase 1-3 Implementation Lock: data foundation, Golden Hour conversion, Diamond/lifecycle/value optimization.

ADS Execution Playbook: Audit -> Implementation -> Verify/Gate delivery rhythm for dev and AI agents.

ADS Strategy Input Pack: persona, behavior, keyword, negative keyword, creative hook, landing, CTA, learning and publish governance.

Facebook Ads & Live Commerce Operating Model / Financial Baseline: Live Golden Hour, Messenger, Quote, ORDER_VERIFIED, CRM, Diamond and scale economics.

| SOURCE-OF-TRUTH PRIORITY<br>Nếu tài liệu ADS Strategy, Playbook hoặc Dashboard lệch với Core event_registry, Commerce Runtime, AI Runtime, CRM Messaging, Golden Hour, 24/7 hoặc Diamond policy, thì Core/Runtime owner thắng. Module 6 không được tự phát minh event, pricing, policy, trigger hoặc scale rule. |
|---|

## 3. Mục đích Module 6

Đo đúng toàn bộ tín hiệu ads, live, landing, Messenger, quote, order, CRM và Diamond theo cùng một chain attribution.

Bảo đảm mọi event đi qua event_registry và các outbox/worker được kiểm soát, không gửi trực tiếp từ runtime request nếu không được phép.

Bảo đảm consent fail-closed: thiếu consent hợp lệ thì không sync audience, không gửi external measurement, không gửi CRM.

Gắn đúng guest -> customer -> order -> verified revenue để tránh đo sai, double count hoặc scale dựa trên vanity metrics.

Chỉ tính ROAS bằng Verified Revenue / ORDER_VERIFIED, không tính bằng comment, inbox, quote, order draft, payment waiting hoặc COD waiting.

Tạo Data Quality Gate và Scale Gate để owner quyết định tăng ngân sách sau pilot, không tự động scale.

Xây khung learning engine có kiểm soát: seed đúng, chạy đúng, học đúng, review đúng, publish đúng trong safe range.

## 4. Boundary Lock - Module 6 được làm và không được làm

| Nhóm | Module 6 được làm | Module 6 bị cấm |
|---|---|---|
| Measurement | Nhận và chuẩn hóa event; validate event_code; dedup; lưu measurement events | Tự tạo event ngoài event_registry; ghi event không rõ consent hoặc identity |
| Attribution | Gắn campaign/adset/ad/page/live/comment/Messenger/quote/order/verified revenue | Gán doanh thu theo cảm tính; sửa attribution sau khi verified mà không audit |
| Revenue | Consume Verified Revenue từ Commerce Runtime | Tính revenue từ quote, cart, order draft, payment waiting, COD waiting |
| Google/Meta | Gửi Pixel/CAPI/Offline qua outbox/worker khi consent hợp lệ | Gửi trực tiếp từ request runtime hoặc gửi dữ liệu không có consent |
| Dashboard | Báo cáo Ads Spend, Revenue Verified, ROAS, CPA, AOV, funnel rate | Làm đẹp dashboard bằng dữ liệu chưa verified |
| Scale | Tính điều kiện scale và tạo scale_request cho owner review | Tự tăng ngân sách, tự bật campaign, bỏ qua owner approval |
| Learning | Tạo candidate/recommendation trong review queue | Cho machine tự publish toàn quyền hoặc bịa persona/keyword/hook gốc |
| Core policy | Consume policy từ Core/Runtime | Override giá, chương trình, quyền lợi, CRM, Diamond, Golden Hour, 24/7 |

| CẢNH BÁO TRIỂN KHAI<br>Không được hiểu Module 6 là vài đoạn code Pixel/CAPI hoặc một dashboard ROAS. Một hệ đo lường thật phải có identity, consent, event registry, dedup, attribution, verified revenue, data quality, owner approval, audit, smoke và rollback. Copy-paste code rời rạc sẽ dẫn tới đo sai, double count, scale sai ngân sách và không truy vết được khi lỗi. |
|---|

## 5. Kiến trúc vận hành tổng thể Module 6

| Lớp | Thành phần | Vai trò |
|---|---|---|
| Source | Core event_registry, Customer/Guest identity, Consent snapshot, Commerce Verified Revenue | Nguồn sự thật để đo lường và attribution |
| Tracking | Web hooks, landing events, Facebook/Meta events, Messenger events, live events, CRM events | Thu tín hiệu đầu vào theo event code đã khóa |
| Outbox | conversion_events, marketing_measurement_outbox, marketing_audience_outbox | Tách runtime request khỏi external sync, chống mất dữ liệu và retry có kiểm soát |
| Integration | Pixel, CAPI, Offline Conversion, Google/Meta connectors | Gửi dữ liệu ra nền tảng ngoài khi consent và dedup pass |
| Attribution | Attribution Resolver, Ads Context Resolver, Live Session Resolver | Gắn nguồn ads/live/page/comment/Messenger tới quote/order/verified revenue |
| Dashboard | ROAS/CPA/AOV/Funnel/CRM/Diamond dashboards | Báo cáo hiệu quả và cảnh báo chất lượng dữ liệu |
| Gate | Data Quality Gate, Scale Gate, Owner Approval Gate | Chặn scale khi chưa đủ điều kiện |
| Learning | Strategy libraries, scoring, candidate generation, review queue, guarded publish | Tối ưu có kiểm soát theo dữ liệu thật |
| Evidence | Audit log, evidence item, smoke report, release review | Chứng minh đủ điều kiện cho từng phase |

## 6. ADS Phase Flow - Không được nhảy phase

| Phase | Mục tiêu | Core output | Không được làm |
|---|---|---|---|
| Phase 1 - Data / Tracking / Consent / Hero SKU | Dựng nền đo lường sạch, identity guest->customer, consent fail-closed, outbox measurement, audience sync, Hero SKU ads | Data Engine, Acquisition Engine cơ bản, Retargeting Engine cơ bản | Không chạy 13 SKU song song; không CRM/audience/external measurement khi thiếu consent; không scale theo doanh thu |
| Phase 2 - Golden Hour / AI Consult / Order Capture / Retargeting | Chuyển traffic thành Messenger consult, QuoteSnapshot, order capture, Golden Hour, retargeting | Conversion Machine: Ads -> Live -> Comment -> Messenger -> Quote -> Order -> Verified | Không public giá cuối; không tư vấn sâu ở comment; không gửi Core nếu stock/trust/policy chưa pass |
| Phase 3 - Diamond / Lifecycle / Repeat / Value Optimization | Giảm ads ratio bằng CRM, repeat, dormant/reactivation, Diamond/referral, value optimization | Growth Machine: Customer asset, repeat revenue, Diamond growth, learning engine | Không để Data Mart làm trigger owner; không auto-publish ngoài safe range; không vượt Core policy |

## 7. Phase 1 - Nền dữ liệu, Tracking, Consent, Hero SKU Ads

| MỤC TIÊU PHASE 1<br>Phase 1 chưa nhằm tối đa hóa sản lượng. Mục tiêu là tạo nền đo lường đúng trước khi scale tiền ads: event hợp lệ, identity đúng, consent đúng, measurement qua outbox, audience qua segment/outbox và Hero SKU ads không làm phân mảnh hệ. |
|---|

| Khối | Yêu cầu khóa | Acceptance |
|---|---|---|
| Identity | customers, customer_profiles, customer_addresses, customer_devices, guest_contacts; map guest -> customer khi có dữ liệu đủ | Guest/customer mapping có audit và không ghi đè thiếu bằng chứng |
| Event Registry | Mọi event phải tồn tại trong event_registry trước khi log hoặc gửi đi | Unknown event bị reject hoặc hold, có audit |
| Web Event Logs | Append-only; lưu page, session, source, consent snapshot, event_ts, idempotency | Không update/xóa lịch sử event |
| Consent | guest_marketing_consent_snapshot bắt buộc; thiếu consent hợp lệ thì fail-closed | Không external measurement, audience sync, CRM khi consent missing |
| Conversion | conversion_events là source cho marketing_measurement_outbox | External measurement chỉ đi qua worker/outbox |
| Audience | customer_segments -> customer_segment_members -> marketing_audience_outbox | Audience sync không đi trực tiếp từ runtime request |
| Hero SKU | Phase 1 chạy Hero SKU theo logic seasonal + functional + nutritional, không 13 SKU ngang hàng | Campaign không phân mảnh cold ads |

| Event nền bắt buộc | Ý nghĩa |
|---|---|
| VIEW_LANDING | Người dùng xem landing/campaign page |
| CLICK_CTA | Người dùng bấm CTA |
| SUBMIT_FORM | Người dùng gửi form/lead |
| VIEW_ITEM | Xem sản phẩm hoặc nội dung sản phẩm |
| ADD_TO_CART | Thêm vào giỏ hoặc quote cart |
| BEGIN_CHECKOUT | Bắt đầu quy trình đặt hàng |
| ORDER_SUCCESS | Order success signal theo Core, chưa dùng thay ORDER_VERIFIED |
| USER_REGISTERED | Người dùng đăng ký/tạo identity chính thức |
| ORDER_VERIFIED | Order verified - nguồn revenue hợp lệ |
| GOLDEN_HOUR_START / REMINDER | Tùy cấu hình khi mở phiên Giờ Vàng |

## 8. Phase 2 - Giờ Vàng, AI Consult, Order Capture, Retargeting

Golden Hour phải vận hành theo trạng thái PRE -> LIVE -> POST -> CLOSED.

Live comment chỉ quick reply/route, không tư vấn sâu, không báo giá cuối, không lặp PII.

Messenger là nơi deep consult, AI Advisor nhận Ads/Live context và gọi QuoteSnapshot từ Commerce.

Order capture phải validate stock, fulfillment, trust, policy và customer confirmation trước khi gửi Core.

Retargeting chỉ dựa trên event hợp lệ và consent hợp lệ.

Quote price priority phải bám Core policy: Golden Hour -> Diamond Buyer Rule -> 24/7 -> List Price nếu policy cho phép.

| Flow | Event / Object | Owner / Consumer Boundary |
|---|---|---|
| Ads -> Live | campaign_id, adset_id, ad_id, live_session_id | Module 6 đo; Gateway/Live vận hành; không tính revenue |
| Live -> Comment | LIVE_VIEW, LIVE_COMMENT | Gateway normalize; Module 6 nhận signal |
| Comment -> Messenger | MESSENGER_STARTED, messenger_thread_id | Gateway handoff; AI tư vấn private |
| Messenger -> Quote | AI_PROPOSAL_SENT, QUOTE_CART_CREATED, QUOTE_SNAPSHOT_CREATED, QUOTE_SENT | AI chỉ orchestrate; Commerce tạo QuoteSnapshot |
| Quote -> Order | ORDER_CONFIRMATION_SENT, CUSTOMER_CONFIRMED_ORDER, ORDER_CREATED | Commerce tạo order khi có customer confirmation |
| Order -> Verified | ORDER_VERIFIED, PAYMENT_COMPLETED nếu có | Commerce/Payment/Shipping xác nhận; Module 6 consume verified revenue |

## 9. Phase 3 - Diamond, Lifecycle, Repeat, Value Optimization

Phase 3 chuyển trọng tâm từ mua khách sang vận hành tài sản khách hàng: CRM lifecycle, repeat, dormant/reactivation, Diamond và value optimization.

Diamond referral phải gắn link hợp lệ, buyer identity, order verified và commission eligibility từ Core/Finance; Module 6 chỉ đo nguồn và hiệu quả.

CRM revenue phải xuất phát từ CRM eligibility, suppression pass và order verified; không dùng click/chat làm revenue.

Value optimization được phép tạo recommendation/candidate; việc publish phải qua review queue và owner approval.

Data Mart chỉ là support view để phân tích, không được lạm quyền thành trigger owner cho CRM, pricing, Diamond hoặc budget scale.

| Nhóm tăng trưởng | Signal hợp lệ | KPI |
|---|---|---|
| Repeat / Reorder | CRM_REORDER_SENT, CRM_REORDER_ORDER_CREATED, ORDER_VERIFIED | Repeat rate, CRM Revenue, AOV |
| Dormant / Reactivation | Dormant segment, consent pass, CRM eligibility pass, order verified | Reactivation rate, CPA reactivation |
| Diamond | DIAMOND_LEAD_CREATED, referral_link_id, DIAMOND_REFERRAL_ORDER_VERIFIED | Diamond lead rate, Diamond Revenue, commission-ready revenue |
| Value Optimization | High-value order, boxes/order, tier upgrade, product affinity | AOV, CLV proxy, boxes/order, ads ratio reduction |
| Learning Engine | Verified business signals + data quality pass | Candidate approval rate, uplift, drift violations |

## 10. Event Taxonomy và Measurement Event Contract

| Nhóm Event | Event Code | Quy tắc |
|---|---|---|
| Awareness / Live | LIVE_VIEW, LIVE_COMMENT, PUBLIC_REPLY_SENT | Không tính revenue; dùng funnel và attribution |
| Messenger / AI | MESSENGER_STARTED, AI_ADVISORY_SENT, AI_PROPOSAL_SENT | Chỉ là engagement/consult signal |
| Quote | QUOTE_CART_CREATED, QUOTE_SNAPSHOT_CREATED, QUOTE_SENT | Quote không phải doanh thu; QuoteSnapshot là price truth |
| Order | ORDER_CONFIRMATION_SENT, CUSTOMER_CONFIRMED_ORDER, ORDER_CREATED | Order Created chưa chắc verified revenue |
| Verified Revenue | ORDER_VERIFIED, PAYMENT_COMPLETED nếu Core policy cho phép | Chỉ ORDER_VERIFIED revenue được dùng cho ROAS |
| CRM | CRM_REORDER_SENT, CRM_REORDER_ORDER_CREATED | CRM chỉ khi suppression/consent pass |
| Diamond | DIAMOND_LEAD_CREATED, DIAMOND_REFERRAL_ORDER_VERIFIED | Diamond attribution không lẫn với Ads thường |

ads_measurement_event:
  event_id: string
  event_code: string
  event_ts: datetime
  customer_id: optional string
  guest_id: optional string
  page_id: optional string
  live_session_id: optional string
  campaign_id: optional string
  adset_id: optional string
  ad_id: optional string
  sales_session_id: optional string
  quote_snapshot_id: optional string
  order_code: optional string
  revenue_value: optional number
  currency: VND
  attribution_context: object
  consent_snapshot_id: optional string
  idempotency_key: string
  correlation_id: string
  data_quality_status: PASS | HOLD | FAIL

## 11. Ads Attribution Context

ads_attribution_context:
  campaign_id: optional string
  campaign_name: optional string
  adset_id: optional string
  adset_name: optional string
  ad_id: optional string
  ad_name: optional string
  page_id: string
  live_session_id: optional string
  comment_id: optional string
  messenger_thread_id: optional string
  psid: optional string
  referral_link_id: optional string
  diamond_id: optional string
  entry_channel: FACEBOOK_AD | LIVE_ORGANIC | DIAMOND_LINK | CRM | DIRECT
  attribution_window: string
  first_touch_event_id: optional string
  last_touch_event_id: optional string
  source_confidence: HIGH | MEDIUM | LOW
  conflict_status: NONE | MULTI_TOUCH | MISSING_SOURCE | DUPLICATE_RISK

Attribution phải truy ngược được từ campaign/adset/ad/page/live/comment/Messenger tới quote/order/ORDER_VERIFIED.

Nếu có Diamond link và Ads cùng xuất hiện, Module 6 phải lưu attribution context đầy đủ; Finance/Commission owner quyết định hoa hồng, không phải Ads Measurement.

Nếu thiếu nguồn hoặc dữ liệu conflict, dashboard phải đánh dấu LOW confidence hoặc HOLD, không dùng làm scale evidence.

Attribution snapshot phải immutable sau khi order verified; mọi correction phải có adjustment record, actor, reason, audit và evidence.

## 12. Pixel / CAPI / Offline Conversion / Dedup

| Luồng | Điều kiện gửi | Không được làm |
|---|---|---|
| Pixel Browser | Chỉ gửi event public-safe, có consent và idempotency key | Không gửi PII thô, không gửi khi consent missing |
| CAPI Server | Gửi từ marketing_measurement_outbox worker, có hash policy và dedup key | Không gửi trực tiếp từ request runtime |
| Offline Conversion | Chỉ gửi conversion sau ORDER_VERIFIED hoặc event được owner phê duyệt | Không gửi quote/order draft như purchase |
| Audience Sync | Gửi từ customer_segments + marketing_audience_outbox + consent pass | Không sync audience từ ad hoc query hoặc data mart |
| Retry / Dead Letter | Retry có giới hạn, lưu error_log và next_retry_at | Không retry vô hạn, không mất event không dấu vết |

dedup_key = platform + event_code + customer_or_guest_key + event_ts_bucket + source_event_id
idempotency_key = event_code + page_id + session_id + raw_event_hash + normalized_ts
revenue_value_source = Commerce Verified Revenue only
send_policy = consent_valid AND event_in_registry AND data_quality_pass AND not_duplicate

## 13. Data Object Contract tối thiểu

| Object / Table | Mục đích | Owner / Ghi chú |
|---|---|---|
| event_registry | Danh sách event hợp lệ, owner, channel, data sensitivity, external send policy | Core Event Governance |
| web_event_logs | Append-only web/landing/tracking logs | Module 6, không sửa lịch sử |
| guest_contacts | Guest lead identity và contact fingerprint | Customer identity |
| guest_marketing_consent_snapshot | Consent tại thời điểm event | Consent fail-closed |
| conversion_events | Source chuyển đổi nội bộ trước khi gửi measurement | Module 6/Core |
| marketing_measurement_outbox | Hàng đợi gửi Pixel/CAPI/Offline | Worker only |
| customer_segments | Nguồn segment được duyệt | CRM/Ads segmentation |
| customer_segment_members | Thành viên trong segment | Không lạm dụng làm trigger owner |
| marketing_audience_outbox | Hàng đợi sync audience | Worker only |
| ads_attribution_context | Chain campaign/adset/ad/page/live/comment/messenger/referral | Attribution source |
| ads_measurement_events | Event đã chuẩn hóa phục vụ dashboard/ROAS | Module 6 |
| ads_data_quality_check | Kết quả kiểm dữ liệu | Data Quality Gate |
| ads_scale_request | Đề nghị scale ngân sách | Owner approval required |
| ads_learning_candidate | Candidate keyword/persona/hook/creative/landing/CTA | Learning review queue |

## 14. Dashboard KPI Contract

| Chỉ số | Công thức / nguồn | Ghi chú |
|---|---|---|
| Ads Spend | Từ Ads platform / approved spend import | Phải có campaign/adset/ad mapping |
| Revenue Verified | SUM(verified_revenue) | Chỉ ORDER_VERIFIED |
| ROAS | Revenue Verified / Ads Spend | Không dùng order chưa verified |
| CPA | Ads Spend / number_of_ORDER_VERIFIED | Theo campaign/adset/ad/live/session |
| AOV | Revenue Verified / verified_orders | Theo verified order |
| Boxes per Order | Verified boxes / verified_orders | Mục tiêu tăng AOV |
| Comment Rate | LIVE_COMMENT / LIVE_VIEW | Top funnel |
| Inbox Rate | MESSENGER_STARTED / LIVE_COMMENT | Handoff quality |
| Quote Rate | QUOTE_SENT / MESSENGER_STARTED | AI + Commerce quote efficiency |
| Order Rate | ORDER_CREATED / QUOTE_SENT | Sales conversion |
| Verified Rate | ORDER_VERIFIED / ORDER_CREATED | Payment/COD/fulfillment quality |
| COD Fail Rate | COD fail / COD orders | Rủi ro vận hành |
| CRM Revenue | Verified revenue từ CRM attribution | Lifecycle value |
| Diamond Revenue | Verified revenue từ referral/Diamond attribution | Growth multiplier |

## 15. Data Quality Gate

| Gate Item | PASS khi | FAIL/HOLD khi |
|---|---|---|
| Event Registry | Event code tồn tại, owner rõ, schema đúng | Unknown event, event không có owner |
| Consent | Consent valid tại thời điểm event/external send | Missing/expired/opt-out |
| Dedup | No duplicate hoặc duplicate được merge chính xác | Pixel/CAPI/Offline double count |
| Identity | guest/customer/order mapping rõ | Guest merge sai hoặc order không map được |
| Attribution | campaign/adset/ad/page/live/messenger chain đủ | Nguồn mơ hồ, conflict không xử lý |
| Verified Revenue | Revenue lấy từ Commerce Verified Revenue | Quote/order draft/unpaid được tính revenue |
| Suppression | Recall/Sale Lock/CRM suppression được phản ánh | Scale khi đang bị lock/suppression |
| Dashboard | Metric có sample evidence và trace | Dashboard chỉ là visual không có source trace |

## 16. Scale Gate

| SCALE GATE LÀ QUYẾT ĐỊNH CỦA OWNER<br>Module 6 chỉ tính toán và đề xuất. Tăng ngân sách, bật campaign scale, mở audience scale hoặc publish optimization đều cần owner approval, có evidence, có rollback và có giới hạn rủi ro. |
|---|

| Điều kiện scale | Yêu cầu tối thiểu |
|---|---|
| P3/P5/P6 evidence | Verified Revenue boundary, Payment/COD/Order Verified, Channel identity, event identity có evidence |
| Quote/Order | QuoteSnapshot hoạt động đúng, order tạo đúng, không tạo order khi chưa xác nhận |
| Public/Privacy | AI/Gateway không public giá cuối, không leak PII, không spam |
| Funnel | AOV tối thiểu 2 hộp/đơn, CPA trong ngưỡng, verified rate đạt ngưỡng owner đặt |
| Dashboard | ROAS đo bằng ORDER_VERIFIED, attribution đủ campaign/adset/ad/live/messenger |
| Quality | Data Quality Gate PASS, duplicate thấp, consent pass, outbox ổn định |
| Risk | Không recall, không sale lock, không quality hold, không complaint P0, không platform spam flag |
| Approval | Owner duyệt scale request, có budget cap, có rollback condition |

## 17. ADS Strategy Input Pack và Learning Engine

Chiến lược đầu vào không được tạo theo cảm tính. Persona, behavior, keyword, negative keyword, creative hook, landing và CTA phải được seed từ Content Block canonical, SKU Master, Phase ADS rule và business truth.

Learning Engine chỉ được học sau khi có seed chuẩn và dữ liệu verified business signal đủ sạch.

Learning Engine được đề xuất candidate, delta recommendation và safe-range optimization; không được tự publish toàn quyền từ đầu.

Mọi optimization phải gắn với sellable SKU, program, Golden Hour/24/7 policy, product public claim và brand wording.

Mapping là lõi để Ads không chạy cảm tính: SKU/Product line -> Persona -> Behavior -> Keyword -> Creative Hook -> Landing -> CTA -> Event -> Verified Revenue.

| Thư viện | Mục đích | Nguồn seed |
|---|---|---|
| Persona Library | Nhóm khách mục tiêu | Content Block 20 SKU, customer context, CRM lifecycle |
| Behavior Library | Hành vi số và hành vi mua | Web/Messenger/Live/CRM events đã pass data quality |
| Keyword Library | Từ khóa acquisition/intent | Content Block, product public view, search/ads history |
| Negative Keyword Library | Chặn tệp/ý định không phù hợp | Spam/troll/low-intent/fake order signals |
| Creative Hook Library | Hook không sale sốc, đúng brand, đúng claim | Product effectiveness, Meta-safe wording, Golden Hour Tri Ân |
| Landing / CTA Library | Mapping landing và CTA theo intent | Hero SKU, Golden Hour, Diamond, CRM/reorder |

| Giai đoạn | Mô tả |
|---|---|
| Seed | Fill thư viện từ Content Block/SKU/Rule đã khóa; không để machine tự bịa chiến lược gốc |
| Run | Chạy acquisition/retargeting theo mapping active và sellable SKU |
| Learn | Đọc signal hiệu quả, score persona/keyword/hook/landing/CTA |
| Review | Sinh candidate vào review queue; owner/marketing approve/reject/hold |
| Publish | Guarded auto-publish trong safe range, có rollback và audit |

## 18. Tích hợp với Module 3, 4, 5, 7, 8

| Module | Module 6 consume gì | Module 6 không được làm gì |
|---|---|---|
| Module 3 Commerce | QuoteSnapshot, Order, Payment, Shipping, ORDER_VERIFIED, Verified Revenue | Không tính giá, tạo đơn, xác nhận payment hoặc doanh thu |
| Module 4 AI Advisor | AI advisory/proposal/quote sent/order confirmation events, sales_session context | Không can thiệp nội dung tư vấn hoặc tự gợi ý sản phẩm ngoài AI |
| Module 5 Gateway | Page, live, comment, messenger, handoff, delivery logs | Không xử lý raw webhook hoặc public reply |
| Module 7 MC AI Live | Live session, script segment, board_id, segment signal | Không dùng live signal làm doanh thu/ROAS |
| Module 8 IVR | IVR result only when Order Core accepts as confirmation signal | Không tự chuyển order state hoặc verified revenue |
| CRM / Member | CRM reorder, suppression state, lifecycle events | Không gửi CRM hoặc quyết định member rights |
| Finance / Diamond | Commission-ready/verified revenue signals, referral attribution context | Không tính final commission hoặc payout |

## 19. API / Worker / Queue Boundary

| Contract | Mục đích | Ghi chú |
|---|---|---|
| POST /api/ads/events/track | Nhận event nội bộ đã qua client/server validation | Không gửi external trực tiếp |
| POST /api/ads/conversions | Tạo conversion_event nội bộ | Nguồn cho measurement outbox |
| GET /api/admin/ads/dashboard | Dashboard ROAS/CPA/AOV/funnel | Chỉ đọc data mart/support view |
| POST /api/admin/ads/scale-requests | Tạo đề nghị scale | Owner approval required |
| POST /api/admin/ads/learning-candidates | Review candidate/hook/keyword/audience | Không auto-publish nếu chưa safe range |
| worker: marketing_measurement_dispatcher | Gửi Pixel/CAPI/Offline | Retry, dedup, error log |
| worker: marketing_audience_dispatcher | Sync audience | Consent fail-closed |
| worker: attribution_materializer | Tổng hợp attribution snapshots | Không ghi đè verified revenue |
| worker: data_quality_checker | Kiểm data quality và scale readiness | Output PASS/HOLD/FAIL |

## 20. Implementation Roadmap theo Slice

| Slice | Tên | Scope | Done Gate |
|---|---|---|---|
| M6.2A | ADS Phase 1 Data Foundation | customers/guest identity/consent/event registry/web logs | Event + consent + identity tests PASS |
| M6.2B | Tracking & Event Contract | frontend hooks, backend event validation, append-only logs | Unknown event fail, duplicate event handled |
| M6.2C | Outbox Workers | conversion_events, measurement_outbox, audience_outbox | No direct external send, retry/dead-letter pass |
| M6.2D | Pixel/CAPI/Offline Dedup | Dedup key, hash policy, platform result logs | No double count, no PII thô |
| M6.2E | Attribution Resolver | campaign/adset/ad/page/live/comment/messenger/quote/order/verified | Order Verified trace to source |
| M6.2F | Dashboard & Data Quality | ROAS/CPA/AOV/funnel/data quality gate | Dashboard shows verified-only revenue |
| M6.2G | Scale Request | scale threshold, approval, rollback | No auto scale, owner approval required |
| M6.2H | ADS Strategy Libraries | persona/behavior/keyword/hook/landing/CTA mapping | Seed framework pass, no auto-publish |
| M6.2I | Phase 2 Golden Hour Funnel | live/comment/Messenger/quote/order retargeting measurement | Golden Hour conversion smoke pass |
| M6.2J | Phase 3 CRM/Diamond/Lifecycle | repeat/CRM/Diamond/value attribution | CRM/Diamond revenue verified |
| M6.2K | Smoke & Evidence Pack | P0 tests, evidence registry, owner review package | Evidence pack ready for review |

## 21. P0 Smoke Test Matrix

| Test ID | Kịch bản | Kết quả phải đạt |
|---|---|---|
| ADS-P0-001 | Event không có trong event_registry | Reject/HOLD, audit rõ |
| ADS-P0-002 | Event hợp lệ nhưng thiếu consent | Không external measurement, không audience sync |
| ADS-P0-003 | Duplicate Pixel/CAPI/Offline | Dedup, không double count |
| ADS-P0-004 | Quote được tạo nhưng chưa order | Không revenue, không ROAS |
| ADS-P0-005 | Order Draft / Order Created chưa verified | Không tính Revenue Verified |
| ADS-P0-006 | ORDER_VERIFIED có campaign/adset/ad đầy đủ | ROAS/CPA/AOV dashboard cập nhật |
| ADS-P0-007 | ORDER_VERIFIED thiếu source | Revenue vẫn lưu, attribution confidence LOW/HOLD |
| ADS-P0-008 | CRM opt-out | Không sync CRM audience/CRM event outbound |
| ADS-P0-009 | Recall/Sale Lock active | Scale Gate FAIL/HOLD |
| ADS-P0-010 | Data Mart tạo trigger CRM/scale | Fail - Data Mart chỉ support view |
| ADS-P0-011 | Learning candidate ngoài safe range | Hold review, không publish |
| ADS-P0-012 | Scale request không owner approval | Không scale |
| ADS-P0-013 | Live/Comment/Messenger chain | Trace được live_session_id, comment_id, messenger_thread_id |
| ADS-P0-014 | Diamond referral order verified | Gắn referral attribution, không tự tính commission |
| ADS-P0-015 | Dashboard hiển thị quote/order draft như revenue | Fail |

## 22. Evidence Plan

| Evidence | Nội dung bắt buộc |
|---|---|
| Event Registry Evidence | Screenshot/API/DB record chứng minh event codes, owner, policy |
| Consent Evidence | Case consent pass/fail-closed, opt-out handling |
| Outbox Evidence | conversion/audience outbox queued, sent, retry, error, dead-letter |
| Dedup Evidence | Pixel/CAPI/Offline duplicate event xử lý đúng |
| Attribution Evidence | Order Verified trace ngược campaign/adset/ad/page/live/comment/Messenger |
| Dashboard Evidence | Revenue Verified, ROAS, CPA, AOV lấy đúng nguồn |
| Scale Gate Evidence | PASS/HOLD/FAIL with owner approval flow |
| Learning Evidence | candidate -> review -> approve/reject/hold -> rollback |
| Security/Privacy Evidence | No PII thô, consent, hash policy, access control |
| Smoke Report | P0 smoke result with correlation_id and evidence_id |

## 23. Done Gate / Fail Gate

| Done Gate | Điều kiện |
|---|---|
| Documentation Done | Source-of-truth, boundary, phase flow, data model, event taxonomy, gates, smoke/evidence đầy đủ |
| Technical Design Done | API/object/worker/dashboard contracts được review, không conflict Core owner |
| Implementation Slice Done | Mỗi slice có Audit -> Implementation -> Verify/Gate, test pass, rollback ready |
| ROAS Pass | Chỉ khi ORDER_VERIFIED revenue, attribution pass, dashboard pass, data quality pass |
| Scale Ready | Chỉ khi pilot pass, no P0, AOV/CPA/ROAS đạt, owner approve |

| Fail Gate | Chặn ngay nếu |
|---|---|
| Revenue misuse | Quote/cart/order draft/payment waiting/COD waiting bị tính revenue |
| Consent violation | External measurement hoặc audience sync khi thiếu consent |
| Event drift | Tự phát minh event ngoài event_registry |
| Core override | Override pricing/policy/Golden Hour/24-7/Diamond/CRM owner |
| Data Mart abuse | Dùng Data Mart làm trigger owner |
| Auto scale | Tự tăng ngân sách hoặc publish optimization không approval |
| No evidence | Không có audit/evidence/smoke mà gọi PASS |

## 24. Dev / AI Agent Handoff Playbook

| NHỊP THI CÔNG BẮT BUỘC<br>Mỗi phase chạy 3 prompt riêng: Audit Prompt -> Implementation Prompt -> Verify/Gate Prompt. Không dùng một prompt làm hết. Không nhảy Phase 2 nếu Phase 1 chưa pass. Không nhảy Phase 3 nếu Phase 2 chưa pass. |
|---|

| Bước | Yêu cầu output |
|---|---|
| Audit | Đọc repo hiện tại, mapping file/table/service/test, gap report, conflict report, owner decision required |
| Implementation | Liệt kê exact files, migrations, configs, workers, services, tests; thay đổi tối thiểu đúng phase |
| Verify/Gate | Chạy test, output PASS/FAIL từng item, evidence, rollback, không mark done nếu thiếu acceptance |

Working mode for dev / AI agents:
- Do not guess.
- Read the current repository structure first.
- Reuse existing conventions and test patterns.
- Keep owner and boundary aligned with ADS phase lock.
- Do not invent event codes outside Core event_registry.
- Do not invent pricing or policy outside Core policy resolver.
- Do not override Core, AI Runtime, CRM Messaging, Golden Hour, 24/7 or Diamond.
- Do not jump ahead to future phase scope except safe extension seams.
- Output required: repo summary, files touched, code/migration/config/jobs/tests, commands, PASS/FAIL checklist, rollback steps.

## 25. Open Decision Register

| ID | Câu hỏi Owner cần chốt | Ghi chú |
|---|---|---|
| M6-OD-001 | Danh sách Hero SKU Phase 1 chính thức là gì? | Không chạy 13/20 SKU song song nếu chưa có Hero SKU lock |
| M6-OD-002 | Ngưỡng CPA/ROAS/AOV/Verified Rate chính thức cho từng giai đoạn? | Dùng cho Scale Gate và dashboard alert |
| M6-OD-003 | Hash policy và trường dữ liệu được phép gửi Pixel/CAPI/Offline? | Cần privacy/legal review |
| M6-OD-004 | Google/Meta connector nào dùng trước trong pilot? | Meta trước hay Google song song |
| M6-OD-005 | Attribution model chính thức: first touch, last touch, weighted hay cohort? | Dashboard có thể hiển thị nhiều model nhưng scale gate cần một model chính |
| M6-OD-006 | Safe range cho guarded auto-publish là gì? | Cần trước khi bật learning engine publish |
| M6-OD-007 | Danh sách persona/keyword/hook fill từ Content Block 20 SKU đã khóa chưa? | Nếu chưa khóa, chỉ dừng ở framework |

## 26. Phụ lục A - Checklist bàn giao nhanh cho Dev

Không bắt đầu Module 6 implementation nếu chưa có P3 Verified Revenue boundary và P5 channel/event identity evidence.

Tạo/kiểm event_registry trước mọi tracking hook.

Thiếu consent hợp lệ = fail-closed, không gửi external measurement hoặc audience sync.

Tất cả external measurement đi qua outbox/worker, không gửi trực tiếp từ request runtime.

Tất cả revenue trong dashboard lấy từ ORDER_VERIFIED / Verified Revenue.

Scale request chỉ là đề xuất, owner approval mới được tăng ngân sách.

Learning engine chỉ recommend; publish phải review/approval hoặc guarded auto-publish trong safe range.

Data Mart là support view, không làm trigger owner.

Không bỏ qua recall, sale lock, quality hold, suppression để scale.

Không gọi Module 6 PASS nếu chưa có evidence, smoke, dashboard trace và rollback.

## 27. Kết luận khóa Module 6

| KẾT LUẬN<br>Module 6 là lớp đo lường, attribution, data quality, dashboard, learning và scale governance cho hệ ADS Ginsengfood. Module này giúp biến Ads từ hoạt động đốt ngân sách thành hệ tăng trưởng có đo lường, có kiểm soát và có học máy an toàn. Tuy nhiên, Module 6 không phải Commerce, không phải AI Advisor, không phải Gateway, không phải CRM, không phải Finance và không được tự scale. Mọi quyết định doanh thu, quote, order, payment, shipping, member, Diamond và payout phải quay về Core owner tương ứng. |
|---|


---

## EXTRACTION NOTES (appendix added by the build pack, NOT owner content)

This appendix is generated documentation about the extraction itself. Everything ABOVE the `---` separator is the faithful extract of the owner document; nothing below this line is owner content.

1. Source: MODULE_6_ADS_MEASUREMENT_ROAS_V0.3_CLEAN_FINAL.docx, sha256 c2b03a3e34c5a519eb8b52a201390ff398ee1f653c5b2a07702547d19350fc26 (483,752 bytes). Archived at D:\M6\source-archive\ (archive-only after Phase A).
2. Page footer (word/footer1.xml), repeated page furniture, verbatim: "Ginsengfood - Module 6 Ads Measurement / Attribution / ROAS / Scale Gate V0.3 Clean Final - Internal Technical Document".
3. Page header (word/header1.xml): page-number textbox only ("Page" + PAGE field). No document content.
4. The single image (line 8 [IMAGE], caption line 10) is a raster PNG (word/media/image1.png, original name GINSENGFOOD_MODULE_6_ADS_ARCHITECTURE_V0.3.png, 426,979 bytes). Its text is baked into pixels and is NOT extractable; consult the archived .docx for the figure (audit/conflict resolution only).
5. Footnotes/endnotes/comments: empty stubs, no content. docProps metadata: empty (creator "python-docx").
6. Rendering conventions used by this extract: Heading1 -> "##"; single-cell banner tables -> one-cell markdown tables; in-cell line breaks -> <br>; multi-paragraph table cells joined with " / "; source ListBullet paragraphs rendered as plain paragraphs (text verbatim); "- " prefixes in section 24 are literal source text.
7. Verification: deterministic coverage check 707/707 source blocks present in order (scripts/extract_verify.py, verdict FAITHFUL); 8/8 independent adversarial section verifications FAITHFUL with zero deviations; hidden-content sweep found no missing body content.
