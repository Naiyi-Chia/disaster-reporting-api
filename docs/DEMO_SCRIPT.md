# Demo Script: 通報積木 API

本文件提供「通報積木 API」的展示測試腳本，可用於評委展示、隊友測試或 API 功能驗收。

本 API 是一個災情通報 Workflow API 元件，目標是將 LINE、Web 或其他前端來源的自然語言通報訊息，轉換為可供後續救災派工、Dashboard、GIS 或物資調度系統使用的結構化 report。

---

## 0. Demo 前準備

### 0.1 啟動 API Server

在專案根目錄執行：

```powershell
uvicorn app.main:app --reload
```

看到以下訊息代表啟動成功：

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete
```

### 0.2 打開 Swagger UI

瀏覽器開啟：

```text
http://127.0.0.1:8000/docs
```

本 Demo 主要使用以下 API：

```text
POST /webhook/report
POST /sessions/{session_id}/confirm
GET /reports
```

---

# Demo 1：公務群組完整通報 Official Flow

## 展示目的

驗證第一線公務人員或救災群組可以用自然語言快速通報，系統會自動解析：

* 通報來源
* 地點
* 災情類型
* 需求資源
* 數量

並進入等待確認狀態。

---

## Step 1.1 建立公務群組通報

Endpoint:

```text
POST /webhook/report
```

Request Body:

```json
{
  "platform": "LINE",
  "sender_id": "firefighter_demo_001",
  "group_id": "official_group_001",
  "message_type": "text",
  "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
  "timestamp": "2026-05-26T10:00:00Z"
}
```

Expected Response 重點：

```text
status = waiting_confirmation
current_state = WAITING_CONFIRMATION
source_type = official
source_context = OFFICIAL_GROUP
missing_fields = []
location.address = 馬太鞍溪橋
incident.type = bridge_damage 或 bridge_collapse
needs[0].item = 怪手
needs[0].quantity = 2
```

請複製 response 裡的：

```text
session_id
```

下一步確認通報時會用到。

---

## Step 1.2 確認公務通報

Endpoint:

```text
POST /sessions/{session_id}/confirm
```

Path Parameter:

```text
session_id = 貼上 Step 1.1 回傳的 session_id
```

Request Body:

```json
{
  "sender_id": "firefighter_demo_001",
  "action": "confirm"
}
```

Expected Response 重點：

```text
status = confirmed
current_state = EXPORTED
final_report exists
final_report.source_type = official
final_report.route = A_official
final_report.location = 馬太鞍溪橋
final_report.requested_resource = 怪手
final_report.quantity = 2
```

---

# Demo 2：一般民眾資訊不足通報 Citizen Flow

## 展示目的

驗證一般民眾可以用不完整的自然語言通報，系統不會直接失敗，也不會要求使用者填固定表單，而是會建立 session 並補問缺漏資訊。

---

## Step 2.1 民眾送出不完整通報

Endpoint:

```text
POST /webhook/report
```

Request Body:

```json
{
  "platform": "LINE",
  "sender_id": "citizen_demo_001",
  "group_id": null,
  "message_type": "text",
  "content": "我這邊缺水，家裡淹水了",
  "timestamp": "2026-05-26T10:05:00Z"
}
```

Expected Response 重點：

```text
status = need_more_info
current_state = LOW_CONFIDENCE_REVIEW
source_type = citizen
source_context = CITIZEN_DIRECT
incident.type = flood
needs[0].item = 水
missing_fields includes:
- location
- reporter.name
- reporter.phone
reply_message.text = 中文補問訊息
```

Expected reply_message 範例：

```text
為了完成通報，請提供詳細地址或地點。請提供聯絡人姓名。請提供聯絡電話。
```

請複製 response 裡的：

```text
session_id
```

下一步確認是否沿用同一個 session。

---

## Step 2.2 民眾補充缺漏資訊

Endpoint:

```text
POST /webhook/report
```

注意：`sender_id` 必須與 Step 2.1 相同，系統才會沿用同一個 session。

Request Body:

```json
{
  "platform": "LINE",
  "sender_id": "citizen_demo_001",
  "group_id": null,
  "message_type": "text",
  "content": "地址是花蓮縣光復鄉中山路 10 號，我叫王小明，電話 0912-345-678",
  "timestamp": "2026-05-26T10:06:00Z"
}
```

Expected Response 重點：

```text
session_id = 與 Step 2.1 相同
status = waiting_confirmation
current_state = WAITING_CONFIRMATION
missing_fields = []
location.address = 花蓮縣光復鄉中山路 10 號
reporter.name = 王小明
reporter.phone = 0912-345-678
```

---

## Step 2.3 確認民眾通報

Endpoint:

```text
POST /sessions/{session_id}/confirm
```

Path Parameter:

```text
session_id = 貼上 Step 2.1 或 Step 2.2 回傳的 session_id
```

Request Body:

```json
{
  "sender_id": "citizen_demo_001",
  "action": "confirm"
}
```

Expected Response 重點：

```text
status = confirmed
current_state = EXPORTED
final_report exists
final_report.source_type = citizen
final_report.route = B_citizen
final_report.location = 花蓮縣光復鄉中山路 10 號
final_report.hazard_type = flood
final_report.requested_resource = 水
final_report.state = confirmed
```

---

# Demo 3：查詢正式通報 Reports

## 展示目的

驗證確認後的通報會被轉成正式 report，可供後續 Dashboard、GIS、派工系統或物資調度系統讀取。

---

## Step 3.1 查詢 Reports

Endpoint:

```text
GET /reports
```

Request Body:

```text
No request body
```

Expected Response 重點：

```text
回傳 report list
可看到剛剛 confirmed 的 official report
可看到剛剛 confirmed 的 citizen report
state = confirmed
```

Official report 應包含：

```text
source_type = official
route = A_official
location = 馬太鞍溪橋
requested_resource = 怪手
quantity = 2
state = confirmed
```

Citizen report 應包含：

```text
source_type = citizen
route = B_citizen
location = 花蓮縣光復鄉中山路 10 號
hazard_type = flood
requested_resource = 水
state = confirmed
```

---

# Demo 4：權限鎖 Permission Lock

## 展示目的

驗證 session 操作具有基本權限限制。不同 sender_id 不可確認他人的通報，避免通報被非原始通報者誤確認。

---

## Step 4.1 建立一筆公務通報

Endpoint:

```text
POST /webhook/report
```

Request Body:

```json
{
  "platform": "LINE",
  "sender_id": "firefighter_A",
  "group_id": "official_group_001",
  "message_type": "text",
  "content": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
  "timestamp": "2026-05-26T10:10:00Z"
}
```

Expected Response 重點：

```text
status = waiting_confirmation
current_state = WAITING_CONFIRMATION
```

請複製 response 裡的：

```text
session_id
```

---

## Step 4.2 使用不同 sender_id 嘗試 confirm

Endpoint:

```text
POST /sessions/{session_id}/confirm
```

Path Parameter:

```text
session_id = 貼上 Step 4.1 回傳的 session_id
```

Request Body:

```json
{
  "sender_id": "firefighter_B",
  "action": "confirm"
}
```

Expected Response 重點：

```text
HTTP 403
Only original sender can confirm the session
```

---

# Demo 5：Legacy Endpoint 相容性

## 展示目的

驗證舊有測試入口仍可使用，且已透過 adapter 共用 centralized extraction_service，避免不同 endpoint 解析邏輯發散。

---

## Step 5.1 測試 direct ingest endpoint

Endpoint:

```text
POST /report/ingest
```

Request Body 可依 Swagger schema 填入，例如：

```json
{
  "message_id": "demo-ingest-001",
  "source_type": "official_group",
  "raw_text": "@通報 馬太鞍溪橋斷裂，需要 2 台怪手",
  "timestamp": "2026-05-26T10:15:00Z",
  "contact": null
}
```

Expected Response 重點：

```text
成功建立 report
location = 馬太鞍溪橋
requested_resource = 怪手 或 excavator
quantity = 2
```

注意：

```text
/report/ingest 是 legacy direct report endpoint，不是 session workflow。
它不會進入補問流程，主要用於驗證舊入口相容性。
```

---

# Demo Summary

本 Demo 證明通報積木 API 已完成以下 MVP 能力：

```text
1. 自然語言災情通報
2. 公務端 official route 與民眾端 citizen route 分流
3. Session-based 補問流程
4. Missing fields detection
5. Human-in-the-loop confirmation
6. Permission lock
7. Final structured report output
8. GET /reports 查詢正式通報
9. Legacy endpoint adapter compatibility
```

---

# MVP 限制與下一階段

目前版本為 MVP Prototype，尚未等同 production-ready system。

目前限制：

```text
1. 尚未串接真實 LINE Developers Webhook
2. 尚未部署至雲端
3. 目前使用 SQLite 作為本機資料庫
4. 自然語言解析目前為 rule-based / heuristic parser
5. 尚未加入完整災防知識庫或大型語言模型
6. 尚未實作完整 timeout / correction workflow
7. 尚未建立 Dashboard / GIS 視覺化介面
```

下一階段規劃：

```text
1. 串接 LINE Webhook 與 reply message
2. 加入 ngrok 或雲端部署
3. 強化 correction / cancel / timeout 流程
4. 導入 LLM 或 AI Agent 作為 extraction_service 的替換模組
5. 建立 Dashboard / GIS / 派工系統串接
6. 加入 audit log、權限管理與資安檢查
```
