import requests
import json

# =====================================================================
# 【通報積木】跨社群災情轉譯 API 服務 - Client 调用範例 (Sample Code)
# 
# 本腳本模擬外部管道（如 LINE Webhook Adapter）將規格化後的資料
# 拋轉至通報積木核心 API 的過程。
# =====================================================================

# 1. 設定 API 端點 (依據實際部署環境修改，此處以本地測試為例)
API_URL = "http://localhost:8000/api/v1/reports"

# 2. 準備符合標準 JSON Schema 的災情通報資料 (以花蓮馬太鞍溪事件為例)
payload = {
    "report_id": "REQ-20250915-002",
    "source_type": "official",
    "status": "verified_by_user",
    "emergency_level": "緊急",
    "timestamp": "2025-09-15T16:05:00Z",
    "contact": {
        "name": "林隊長",
        "phone": "09xx-xxx-xxx"
    },
    "location": {
        "gps_provided": True,
        "latitude": 23.7123,
        "longitude": 121.3456,
        "address": "花蓮縣馬太鞍溪橋"
    },
    "needs": {
        "disaster_type": "橋樑斷裂",
        "supplies": [
            {
                "item": "怪手",
                "quantity": 2
            }
        ],
        "manpower": 0
    }
}

# 3. 設定 HTTP Header (宣告傳送格式為 JSON，並可在此處加入 API 認證密鑰)
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_MOCK_API_TOKEN" # 安全層（Security Layer）驗證
}

def send_disaster_report():
    print(f"[*] 正在拋轉災情案件 {payload['report_id']} 至通報積木 API...")
    
    try:
        # 發送 HTTP POST 請求
        response = requests.post(API_URL, data=json.dumps(payload), headers=headers, timeout=10)
        
        # 檢查伺服器回應狀態
        if response.status_code == 200 or response.status_code == 201:
            print("[+] 災情資料拋轉成功！")
            print(f"[+] 伺服器回應資料: {response.json()}")
        else:
            print(f"[-] 拋轉失敗，伺服器回應錯誤碼: {response.status_code}")
            print(f"[-] 錯誤訊息: {response.text}")
            
    except requests.exceptions.Timeout:
        print("[-] 錯誤：連線逾時，伺服器未在時間內回應。")
    except requests.exceptions.ConnectionError:
        print("[-] 錯誤：無法連線至 API 伺服器，請檢查本地服務是否已啟動。")
    except Exception as e:
        print(f"[-] 發生未預期的錯誤: {e}")

if __name__ == "__main__":
    # 執行通報測試
    send_disaster_report()
