# MVP Modular System Architecture

```text
MVP Modular System Architecture
│
├── 1. Client & Channel Layer（外部管道層）
│   ├── LINE User / Public Groups
│   └── Future Channels
│       ├── Telegram
│       ├── Disaster App
│       └── Other Messaging Platforms
│
├── 2. Channel Adapter Layer（管道適配器層 - 實現極致解耦）
│   ├── LINE Webhook Adapter
│   │   ├── Verify LINE Signature
│   │   └── Parse LINE Payload
│   │
│   ├── Media Fetcher & Proxy
│   │   └── 負責向 LINE 平台抓取真實語音與圖片檔案
│   │
│   └── Event Normalizer
│       └── 轉譯為 Unified Event Object
│
├── 3. Gateway & Router Layer（閘道與路由層）
│   ├── Rate Limiting & Spam Detection
│   └── Traffic Router
│       └── 判斷：
│           ├── 公務群組 @通報
│           └── 災民個人通報
│
├── 4. Workflow & State Management Layer（核心工作流與狀態機）
│   ├── Session Manager
│   │   ├── Lifecycle Management
│   │   └── Timeout Tracking
│   │
│   └── Session State Machine
│       └── RECEIVED
│           → AI_PROCESSING
│           → WAITING_CONFIRMATION
│           → CONFIRMED / FAILED / EXPIRED
│
├── 5. AI Cognitive Layer（AI 認知轉譯積木 - 核心大腦）
│   ├── Media Storage Pipeline
│   │   └── 將語音/圖片暫存至 S3 / MinIO 並提供 URL
│   │
│   ├── Multimodal Processing Engine
│   │   ├── Speech-to-Text
│   │   │   └── Voice → Text
│   │   │
│   │   ├── Vision Processor
│   │   │   └── Image → Damage/Object Recognition
│   │   │
│   │   └── NLP Processor
│   │       └── Entity Extraction（人事時地物）
│   │
│   └── Structured Data Builder
│       ├── Fallback 降級機制
│       └── AI Confidence Score Calculation
│
├── 6. Human-In-The-Loop（HITL）Layer
│   ├── Interactive Card Generator
│   │   └── 生成 LINE 互動式確認卡片
│   │
│   └── User Response Handler
│       └── 處理：
│           ├── 正確
│           ├── 修正
│           └── 取消
│
├── 7. Data & Storage Layer（資料持久層）
│   ├── Cache & Session DB
│   │   └── Redis
│   │       ├── 對話狀態
│   │       └── 暫存結構化資料
│   │
│   ├── Operational DB
│   │   └── PostgreSQL
│   │       └── 已確認災情 Report
│   │
│   └── Object Storage
│       └── 儲存：
│           ├── 原始語音
│           └── 災情照片
│
└── 8. Interoperability & Export Layer（跨系統拼裝輸出層）
    ├── Standard JSON / GeoJSON Export API
    ├── OpenAPI / Swagger Specification Documentation
    └── MCP Server Interface
        └── 支援 Model Context Protocol
            供 AI Agent 調用
```
