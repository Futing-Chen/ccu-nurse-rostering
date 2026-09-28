# Python 版本

統一使用 Python 3.11.xx 的版本 (xx 的部分任意，例如 3.11.6 跟 3.11.13 都可以)

如果已經安裝更舊或更新的版本 (例如 3.7 或 3.13 版)，請刪除並重新安裝 3.11 版

# 資料欄位名稱

* 班別代碼: `BA` 白班、`CG` 小夜班、`AA` 大夜班、`OF` 休假
* 日期格式: `YYYY-MM-DD`

# 資料庫架構

請負責資料庫的同學使用 `create_database.sql` 創建 MySQL 資料庫，並將資料庫命名為 `ccu_nurse_rostering`

# API格式

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
    "targetDate": "2026-09-15",
    "targetShiftId": null,
    "weight": 10
  }
  ```
* 輸出 (Response): `{"status": "success", "message": "需求已建立"}`

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

### 2.2 上傳演算法排班結果
把排班結果存進 `shift_assignments` 資料表

* 方法與網址: `POST /api/solver/assignments`
* 輸入 (Request): (演算法算出的配對結果)
  ```
  [
    { "shiftId": "SHIFT_260912_01", "employeeId": "1001" },
    { "shiftId": "SHIFT_260912_02", "employeeId": "1004" },
    { "shiftId": "SHIFT_260912_03", "employeeId": "1002" }
  ]
  ```
* 輸出 (Response): `{"status": "success", "message": "排班結果已寫入資料庫"}`

## 3. 最終班表查詢 (前端顯示用)

### 3.1 查詢最終班表

* 方法與網址: `GET /api/schedule?start_date=2026-09-01&end_date=2026-09-30`
* 輸入 (Request): 無
* 輸出 (Response):
  ```
  [
    {
      "date": "2026-09-01",
      "shiftTypeId": "BA",
      "shiftName": "白班",
      "assignedNurses": [
        { "id": "1001", "name": "Alice" },
        { "id": "1004", "name": "David" }
      ]
    },
    {
      "date": "2026-09-01",
      "shiftTypeId": "CG",
      "shiftName": "小夜",
      "assignedNurses": [
        { "id": "1002", "name": "Bob" }
      ]
    }
  ]
  ```

# 錯誤格式

無論發生什麼錯誤，都必須以固定結構回傳狀態碼。

負責後端的組員請參考 `exception_handler.py` 將錯誤格式統一。

負責前端的組員請使用 `if response["status"] == "error":`，
將錯誤統一捕捉，並把 `response["message"]` 直接顯示為網頁上的警告彈出視窗。

以下舉例錯誤類型:

## 1. 參數錯誤或業務邏輯錯誤 (HTTP Status 400)
例如忘記輸入月份參數
   ```
   {
    "status": "error",
    "error_code": 400,
    "message": "缺少必要的查詢參數：year_month",
    "details": "請提供 YYYY-MM 格式的月份"
   }
   ```

## 2. 找不到資源 (HTTP Status 404)
例如查詢一個不存在的護理師 ID
   ```
   {
    "status": "error",
    "error_code": 404,
    "message": "找不到該護理師資料",
    "details": {"employee_id": "9999"}
   }
   ```

## 3. FastAPI 內建的資料驗證錯誤 (HTTP Status 422)
例如日期格式打錯
   ```
   {
    "status": "error",
    "error_code": 422,
    "message": "資料格式驗證失敗",
    "details": [
     {
      "loc": ["body", "targetDate"],
      "msg": "invalid date format",
      "type": "value_error.date"
      }
    ]
   }
   ```

## 4. 其他錯誤

若有其他類型的錯誤，請參考: 
https://developer.mozilla.org/zh-TW/docs/Web/HTTP/Reference/Status

# 環境變數

請大家按照以下步驟操作:

1. 點擊底下的網址安裝 git

2. 在這個 repository 的首頁點選綠色的 `code` 按鈕
   
3. 複製 `https` 選項底下方框內的網址

4. 打開`命令提示字元` (Windows) 或`終端機` (macOS) 輸入 `cd desktop` (Windows) 或 `cd ~/Desktop` (macOS) 並按下 `enter` 鍵

5. 輸入 git clone + 剛才複製的網址 (例如 `git clone https://github.com`) 並按下 `enter` 鍵 

6. Clone 完成以後打開桌面上的 `ccu-nurse-rostering` 檔案
  
7.  點開 `.env.example` 檔，並將裡面的內容複製起來，接著在資料夾內創建一個 `.env` 檔

8. 在 `.env` 裡把剛剛複製的內容貼上 (完成後請負責資料庫的同學繼續執行步驟9，其他同學做到這一步就可以結束了。)
  
9. 根據註解的說明修改 .env 的內容

---
Git 下載網址: https://git-scm.com/install/

Git 安裝教學 (for Windows): https://www.youtube.com/watch?v=vXj1yyWIyrs

Git 安裝教學 (for macOS): https://www.youtube.com/watch?v=13agcqjeRBA 
