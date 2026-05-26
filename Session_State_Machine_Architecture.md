# Session & State Machine Architecture

```text
Session & State Machine Architecture
│
├── 1. Session Model（會話模型）
│   ├── session_id
│   │   ├── 系統內唯一會話 ID
│   │   ├── 用於追蹤整個災情回報流程
│   │   └── Example: sess_01HZXA92
│   │
│   ├── report_id
│   │   ├── 已確認災情案件 ID
│   │   ├── 一個 Session 最終可產生一份 Report
│   │   └── Example: report_000231
│   │
│   ├── channel_type
│   │   ├── LINE
│   │   ├── Telegram
│   │   └── Future Disaster App
│   │
│   ├── source_context
│   │   ├── PERSONAL_CHAT
│   │   ├── PUBLIC_GROUP
│   │   └── OFFICIAL_GROUP
│   │
│   ├── sender_id
│   │   ├── LINE User ID
│   │   └── 匿名化後 Internal User ID
│   │
│   ├── group_id
│   │   ├── LINE Group ID
│   │   └── Nullable
│   │
│   ├── created_at
│   ├── updated_at
│   ├── expired_at
│   └── current_state
│
├── 2. Session Lifecycle（Session 生命週期）
│   ├── Session Creation Rules
│   │   ├── 新使用者首次通報
│   │   ├── 舊 Session 已 CLOSED
│   │   ├── Session Timeout 超時
│   │   └── 不同群組視為不同 Session
│   │
│   ├── Session Reuse Rules
│   │   ├── 同一 sender_id
│   │   ├── 同一 group_id
│   │   ├── 在有效時間內
│   │   └── current_state ≠ CLOSED
│   │
│   ├── Session Timeout Policy
│   │   ├── WAITING_CONFIRMATION → 10 mins
│   │   ├── AI_PROCESSING → 2 mins
│   │   └── INACTIVE_SESSION → 30 mins
│   │
│   └── Session Expiration
│       ├── Auto Close Expired Session
│       ├── Release Cache Memory
│       └── Archive Session Metadata
│
├── 3. Session Context Object（工作流上下文）
│   ├── raw_events[]
│   │   ├── 原始 webhook payload
│   │   └── media metadata
│   │
│   ├── normalized_messages[]
│   │   ├── text
│   │   ├── image_url
│   │   └── transcript
│   │
│   ├── extracted_entities
│   │   ├── location
│   │   ├── disaster_type
│   │   ├── severity
│   │   ├── victims
│   │   └── requested_resources
│   │
│   ├── ai_confidence_score
│   │
│   ├── user_confirmation
│   │   ├── approved
│   │   ├── corrected
│   │   └── rejected
│   │
│   └── final_structured_report
│
├── 4. Session State Machine（狀態機核心）
│   ├── RECEIVED
│   │   ├── 收到 webhook event
│   │   ├── 建立 Unified Event Object
│   │   └── 等待進入 AI pipeline
│   │
│   ├── MEDIA_FETCHING
│   │   ├── 從 LINE 抓取原始照片/語音
│   │   ├── 上傳至 Object Storage
│   │   └── 建立 temporary signed URL
│   │
│   ├── AI_PROCESSING
│   │   ├── Speech-to-Text
│   │   ├── OCR / Vision Processing
│   │   ├── NLP Extraction
│   │   └── Structured Data Building
│   │
│   ├── LOW_CONFIDENCE_REVIEW
│   │   ├── AI confidence below threshold
│   │   ├── 啟動 fallback extraction
│   │   └── 要求更多資訊
│   │
│   ├── WAITING_CONFIRMATION
│   │   ├── 發送 LINE 確認卡片
│   │   ├── 等待使用者確認
│   │   └── 等待使用者修正
│   │
│   ├── USER_CORRECTION
│   │   ├── 使用者修正 AI 結果
│   │   ├── 回寫 Session Context
│   │   └── 重新進入 AI normalization
│   │
│   ├── CONFIRMED
│   │   ├── 使用者確認資料正確
│   │   ├── 鎖定 Report
│   │   └── 準備輸出
│   │
│   ├── EXPORTED
│   │   ├── JSON Export 完成
│   │   ├── 寫入 Operational DB
│   │   └── 通知外部系統
│   │
│   ├── TIMEOUT
│   │   ├── 超過等待時間
│   │   ├── Session 自動終止
│   │   └── 保留 partial data
│   │
│   ├── CANCELLED
│   │   ├── 使用者取消通報
│   │   ├── 中止 workflow
│   │   └── 保留 audit log
│   │
│   └── FAILED
│       ├── AI processing failure
│       ├── Media fetch failure
│       ├── Invalid payload
│       └── System exception
│
├── 5. State Transition Rules（狀態轉移規則）
│   ├── RECEIVED
│   │   └── → MEDIA_FETCHING
│   │
│   ├── MEDIA_FETCHING
│   │   ├── success → AI_PROCESSING
│   │   └── failed → FAILED
│   │
│   ├── AI_PROCESSING
│   │   ├── high_confidence → WAITING_CONFIRMATION
│   │   ├── low_confidence → LOW_CONFIDENCE_REVIEW
│   │   └── exception → FAILED
│   │
│   ├── LOW_CONFIDENCE_REVIEW
│   │   ├── enough_info → WAITING_CONFIRMATION
│   │   ├── insufficient_info → TIMEOUT
│   │   └── user_cancel → CANCELLED
│   │
│   ├── WAITING_CONFIRMATION
│   │   ├── approve → CONFIRMED
│   │   ├── correction → USER_CORRECTION
│   │   ├── timeout → TIMEOUT
│   │   └── cancel → CANCELLED
│   │
│   ├── USER_CORRECTION
│   │   └── → WAITING_CONFIRMATION
│   │
│   ├── CONFIRMED
│   │   └── → EXPORTED
│   │
│   └── EXPORTED
│       └── → CLOSED
│
├── 6. State Ownership & Responsibility
│   ├── Session Manager
│   │   ├── lifecycle tracking
│   │   ├── timeout scheduler
│   │   └── state persistence
│   │
│   ├── AI Cognitive Layer
│   │   ├── AI_PROCESSING
│   │   ├── LOW_CONFIDENCE_REVIEW
│   │   └── structured data generation
│   │
│   ├── HITL Layer
│   │   ├── WAITING_CONFIRMATION
│   │   ├── USER_CORRECTION
│   │   └── CONFIRMED
│   │
│   └── Export Layer
│       ├── EXPORTED
│       └── external API integration
│
└── 7. Failure Recovery & Resilience
    ├── Idempotency Protection
    │   ├── dedupe_key
    │   ├── webhook_event_id
    │   └── retry-safe processing
    │
    ├── Retry Policy
    │   ├── media fetch retry
    │   ├── AI retry
    │   └── export retry
    │
    ├── Dead Letter Handling
    │   ├── corrupted payload
    │   ├── unsupported media
    │   └── repeated failures
    │
    └── Audit Trail
        ├── state transition logs
        ├── user correction history
        ├── AI decision logs
        └── export history
```
