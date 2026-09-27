# API格式與JSON輸入輸出固定

Base URL (本地測試網址): http://localhost:8000

## 1. 基礎資料管理 (前端 Streamlit 建檔與查詢用)

### 1.1 取得所有護理師名單

* 方法與網址: `GET /api/employees`
* 輸入 (Request): 無
* 輸出 (Response):
  ```
  [
    { "id": "1001", "name": "Alice" },
    { "id": "1002", "name": "Bob" }
  ]
  ```

### 1.2 新增員工需求 (預假/排休)

* 方法與網址: `POST /api/requests`
* 輸入 (Request): (前端送出的預假表單)
  ```
  {
    "employeeId": "1001",
    "requestType": "DAY_OFF",
    "targetDate": "2026-10-15",
    "targetShiftId": null,
    "weight": 10
  }
  ```
* 輸出 (Response): `{"status": "success", "message": "願望已建立"}`

## 2. 演算法與資料庫對接

### 2.1 獲取演算法所需的所有參數 
將資料庫的表組合成完整 JSON 格式

* 方法與網址: `GET /api/solver/dataset?year_month=2026-09`
* 輸入 (Request): 無 
* 輸出 (Response):
  ```
  {
    "masterData": { "shiftTypes": [...] },
    "employees": [...],
    "shifts": [...],
    "requests": { "dayOff": [...], "dayOn": [...], ... }
  }
  ```
