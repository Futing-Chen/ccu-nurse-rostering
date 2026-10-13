# Python 版本

統一使用 Python 3.11.xx 的版本 (xx 的部分任意，例如 3.11.6 跟 3.11.13 都可以)

如果已經安裝更舊或更新的版本 (例如 3.7 或 3.13 版)，請刪除並重新安裝 3.11 版

Python 3.11.9 下載網址: https://python.club.tw/downloads/release/python-3119/

# 資料欄位名稱與格式

* 班別代碼: `BA` 白班、`CG` 小夜班、`AA` 大夜班、`OF` 休假
* 日期格式: `YYYY-MM-DD`
* 其他欄位: 以JSON檔裡面各欄位的格式為標準

# 資料庫架構

請負責資料庫的同學使用 `create_database.sql` 創建 MySQL 資料庫，並將資料庫命名為 `ccu_nurse_rostering`

資料庫架構有更新 (新增病房 `wards`、病房名單 `ward_rosters`，`employees` 多了 `is_active`，`shifts` 多了 `ward_id`)。
如果之前已經建立過資料庫，請依下列步驟重建 (會清空資料庫內的所有資料):

1. 在 MySQL 執行 `DROP DATABASE ccu_nurse_rostering;`
2. 重新執行 `create_database.sql`
3. 在專案資料夾執行 `python seed_database.py` 匯入假資料

## 護理師的三種狀態

系統支援多個病房，護理師對某個病房在某一天的狀態有三種:

| 狀態 | 判斷方式 |
|---|---|
| 值班 | 當天在該病房的名單內，且被排進班次 |
| 休假 | 當天在該病房的名單內，但沒有被排進任何班次 |
| 不啟用 | 當天不在該病房的名單內 |

這和「停用」(離職，`isActive` 為 `false`) 是兩件事: 停用是整間醫院都不再排班，不啟用只是這段期間不負責這個病房。

同一位護理師可以同時在多個病房的名單內。

# API格式

Base URL (本地測試網址): http://localhost:8000

## 1. 基礎資料管理 (前端 Streamlit 建檔與查詢用)

### 1.1 取得所有護理師名單

* 方法與網址: `GET /api/employees` (只回傳在職的護理師)
  
  管理頁面要連已停用的一起顯示時，使用 `GET /api/employees?include_inactive=true`
* 輸入 (Request): 無
* 輸出 (Response):
  ```
  [
    { "id": "1001", "name": "Alice", "isActive": true },
    { "id": "1002", "name": "Bob", "isActive": true }
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
* 輸出 (Response): `{"status": "success", "message": "需求已建立", "requestId": 31}`
* 限制: 同一位護理師對同一天 (或同一個班次) 只能有一筆需求，重複送出會回傳 409 (見錯誤格式)。
  要修改需求時，請先用 1.4 收回原本的需求，再重新送出。

### 1.3 查詢已送出的需求

* 方法與網址: `GET /api/requests?employee_id=1001` (不帶 `employee_id` 則回傳全部)
* 輸入 (Request): 無
* 輸出 (Response):
  ```
  [
    {
      "id": 31,
      "employeeId": "1001",
      "requestType": "DAY_OFF",
      "targetDate": "2026-09-15",
      "targetShiftId": null,
      "weight": 10
    }
  ]
  ```

### 1.4 收回護理師排班需求

* 方法與網址: `DELETE /api/requests/{id}` (`id` 由 1.2 的 `requestId` 或 1.3 的 `id` 取得)
* 輸入 (Request): 無
* 輸出 (Response): `{"status": "success", "message": "需求已收回"}`

### 1.5 新增護理師

* 方法與網址: `POST /api/employees`
* 輸入 (Request):
  ```
  { "id": "1016", "name": "Carol" }
  ```
* 輸出 (Response): `{"status": "success", "message": "護理師已新增"}`
* 限制: `id` (員工編號) 不可與現有的重複，包含已停用的護理師，重複時回傳 409。

### 1.6 修改護理師資料 / 停用 / 重新啟用

* 方法與網址: `PATCH /api/employees/{id}`
* 輸入 (Request): 只需要帶要修改的欄位
  ```
  { "name": "新的姓名" }
  ```
  ```
  { "isActive": false }
  ```
* 輸出 (Response): `{"status": "success", "message": "護理師資料已更新"}`
* 說明: 護理師離職時請將 `isActive` 設為 `false` (停用)。停用只是做記號，不會刪除任何資料：
  * 過去的班表與需求都會保留，`GET /api/schedule` 仍查得到
  * 停用後不會被排進新的班表，也不能再送出需求
  * 復職時將 `isActive` 設為 `true` 即可，員工編號不變

### 1.7 取得所有病房 / 新增病房

* 方法與網址: `GET /api/wards`
* 輸出 (Response):
  ```
  [
    { "id": "W01", "name": "預設病房" }
  ]
  ```
* 方法與網址: `POST /api/wards`
* 輸入 (Request):
  ```
  { "id": "W02", "name": "內科病房" }
  ```
* 輸出 (Response): `{"status": "success", "message": "病房已新增"}`
* 限制: `id` (病房代碼) 不可重複，重複時回傳 409。

### 1.8 設定病房名單

設定某個病房在一段期間內由哪些護理師負責

* 方法與網址: `PUT /api/wards/{病房代碼}/roster`
* 輸入 (Request):
  ```
  {
    "startDate": "2026-09-01",
    "endDate": "2026-09-07",
    "employeeIds": ["1001", "1002", "1003"]
  }
  ```
* 輸出 (Response): `{"status": "success", "message": "病房名單已更新"}`
* 說明:
  * 期間包含頭尾兩天，該期間原本的名單會被整個取代，期間以外的名單不受影響
  * `employeeIds` 給空陣列代表清空該期間的名單
  * 已停用的護理師不能加入名單 (400)
  * 一次最多設定 92 天

### 1.9 查詢病房名單

* 方法與網址: `GET /api/wards/{病房代碼}/roster?start_date=2026-09-01&end_date=2026-09-07`
* 輸入 (Request): 無
* 輸出 (Response):
  ```
  [
    {
      "id": "1001",
      "name": "Alice",
      "isActive": true,
      "dates": ["2026-09-01", "2026-09-02", "2026-09-03"],
      "otherWards": [
        { "id": "W02", "name": "內科病房" }
      ]
    },
    {
      "id": "1002",
      "name": "Bob",
      "isActive": true,
      "dates": ["2026-09-01", "2026-09-02"],
      "otherWards": []
    }
  ]
  ```
* 說明:
  * `dates`: 該護理師在查詢區間內，哪幾天在這個病房的名單內
  * `otherWards`: 該護理師在這些日期同時還負責哪些其他病房。
    **不是空陣列時，請前端在畫面上標註這位護理師同時負責多個病房**

## 2. 演算法與資料庫對接

### 2.1 獲取演算法所需的所有參數 
將資料庫的表組合成完整 JSON 格式

* 方法與網址: `GET /api/solver/dataset?year_month=2026-09&ward_id=W01` (兩個參數都必填)
* 輸入 (Request): 無 
* 輸出 (Response):
  ```
  {
    "masterData": { "shiftTypes": [...] },
    "ward": { "id": "W01", "name": "預設病房" },
    "employees": [...],
    "roster": [
      { "employeeId": "1001", "dates": ["2026-09-01", "2026-09-02", ...] }
    ],
    "shifts": [...],
    "requests": { "dayOff": [...], "dayOn": [...], ... }
  }
  ```
* 說明:
  * `shifts`: 只包含該病房的班次
  * `employees`: 只包含該月份在該病房名單內、且在職的護理師
  * `roster`: 每位護理師哪幾天在名單內，**不在 `dates` 裡的日期不可排班** (不啟用)
  * `requests`: 只包含上述護理師的需求

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
* 說明:
  * 整月取代: 上傳的班次所屬「病房 + 月份」的舊排班結果會先被清掉再寫入，其他病房不受影響
  * 護理師必須在該班次所屬病房當天的名單內，否則回傳 400

## 3. 最終班表查詢 (前端顯示用)

### 3.1 查詢最終班表

* 方法與網址: `GET /api/schedule?start_date=2026-09-01&end_date=2026-09-30&ward_id=W01` (三個參數都必填)
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

# 測試資料

使用 `ccu_nurse_rostering_testing.json` 作為測試用的假資料，模擬 2026 年 9 月 1 日 至 14 日共兩週的排班情況

假資料沒有病房的資訊，用 `python seed_database.py` 匯入時會自動建立一個預設病房 `W01`，
把所有班次歸到 `W01`，並把 15 位護理師放進 `W01` 在 9/1 到 9/14 的名單

# 錯誤格式

無論發生什麼錯誤，都必須以固定結構回傳狀態碼

負責後端的同學請參考 `exception_handler.py` 將錯誤格式統一

負責前端的同學請使用 `if response["status"] == "error":`，
將錯誤統一捕捉，並把 `response["message"]` 直接顯示為網頁上的警告彈出視窗

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

## 3. 資料衝突 (HTTP Status 409)
例如同一位護理師對同一天重複送出需求
   ```
   {
    "status": "error",
    "error_code": 409,
    "message": "該護理師已對同一天提出過需求",
    "details": {
     "existing_request_id": 31,
     "existing_request_type": "DAY_OFF",
     "hint": "如需修改，請先收回原本的需求再重新送出"
    }
   }
   ```

## 4. FastAPI 內建的資料驗證錯誤 (HTTP Status 422)
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

## 5. 其他錯誤

若有其他類型的錯誤，請參考: 
https://developer.mozilla.org/zh-TW/docs/Web/HTTP/Reference/Status

# 環境變數

請大家按照以下步驟操作:

1. 點擊底下的網址安裝 git

2. 在這個 repository 的首頁點選綠色的 `code` 按鈕
   
3. 複製 `https` 選項底下方框內的網址

4. 打開`命令提示字元` (Windows) 或`終端機` (macOS) 輸入 `cd desktop` (Windows) 或 `cd ~/Desktop` (macOS) 並按下 `enter` 鍵 (Windows) 或 `return` 鍵 (macOS)

6. 輸入 git clone + 剛才複製的網址 (例如 `git clone https://github.com`) 並按下 `enter` 鍵 (Windows) 或 `return` 鍵 (macOS)

8. Clone 完成以後打開桌面上的 `ccu-nurse-rostering` 資料夾
  
9.  點開 `.env.example` 檔，並將裡面的內容複製起來，接著在資料夾內創建一個 `.env` 檔

10. 在 `.env` 裡把剛剛複製的內容貼上並存檔 (完成後請負責資料庫的同學繼續執行步驟9，其他同學做到這一步就可以結束了。)
  
11. 根據註解的說明修改 .env 的內容

---
Git 下載網址: https://git-scm.com/install/

Git 安裝教學 (for Windows): https://www.youtube.com/watch?v=vXj1yyWIyrs

Git 安裝教學 (for macOS): https://www.youtube.com/watch?v=13agcqjeRBA 
