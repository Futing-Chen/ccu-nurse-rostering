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

資料庫架構有更新 (新增病房 `wards`、病房名單 `ward_rosters`，`employees` 多了 `is_active`，
`shifts` 多了 `ward_id` 與 `actual_patients`，`wards` 多了 `max_patients`)。
如果之前已經建立過資料庫，請依下列步驟重建 (會清空資料庫內的所有資料):

1. 在 MySQL 執行 `DROP DATABASE ccu_nurse_rostering;`
2. 重新執行 `create_database.sql`
3. 在專案資料夾執行 `python seed_database.py` 匯入假資料

# 護理師的三種狀態

系統支援多個病房，護理師對某個病房在某一天的狀態有三種:

| 狀態 | 判斷方式 |
|---|---|
| 值班 | 當天在該病房的名單內，且被排進班次 |
| 休假 | 當天在該病房的名單內，但沒有被排進任何班次 |
| 不啟用 | 當天不在該病房的名單內 |

這和「停用」(離職，`isActive` 為 `false`) 是兩件事: 停用是整間醫院都不再排班，不啟用只是這段期間不負責這個病房。

同一位護理師可以同時在多個病房的名單內。

# 週排班的流程

每個病房每天都有大夜班、白班、小夜班三個班次 (大夜班 00:00 開始，是一天的第一班)。排班以週為單位，但每個病房對一週從哪天開始的認定不同，
所以所有 API 都用「開始日 + 結束日」表示期間，不限定 7 天，也不限定從星期幾開始。

1. 設定病房最大容量 (1.7)，容量有變時再修改
2. 設定這週的病房名單 (1.8)
3. 產生這週的班次 (1.10)，需求人數依病房最大容量與護病比計算。需要重新產生時先刪除 (1.11)
4. 演算法取得資料 (2.1)、排班後上傳結果 (2.2)
5. 實際病人數較少時，護理長填入實際病人數 (4.1)，再把多出來的人移出班次 (4.2)

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
    { "id": "W01", "name": "預設病房", "maxPatients": 35 }
  ]
  ```
* 方法與網址: `POST /api/wards`
* 輸入 (Request): `maxPatients` 為病房最大容量 (最多能收幾位病人)
  ```
  { "id": "W02", "name": "內科病房", "maxPatients": 40 }
  ```
* 輸出 (Response): `{"status": "success", "message": "病房已新增"}`
* 限制: `id` (病房代碼) 不可重複，重複時回傳 409。
* 方法與網址: `PATCH /api/wards/{病房代碼}` (修改名稱或最大容量，只需要帶要修改的欄位)
* 輸入 (Request):
  ```
  { "maxPatients": 38 }
  ```
* 輸出 (Response): `{"status": "success", "message": "病房資料已更新"}`
* 說明: 最大容量修改後**只影響之後產生的班次**，已經產生的班次維持產生當時的數字。

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

### 1.10 產生班次

為病房產生一段期間內每天的大夜班、白班、小夜班

* 方法與網址: `POST /api/wards/{病房代碼}/shifts`
* 輸入 (Request):
  ```
  { "startDate": "2026-09-20", "endDate": "2026-09-26" }
  ```
* 輸出 (Response): `{"status": "success", "message": "已產生 21 個班次"}`
* 說明:
  * 每個班次的預期病人數 = 病房目前的最大容量；需求人數 = 最大容量 ÷ 護病比，無條件進位
  * 班次 ID 格式為 `病房代碼_年月日_班別`，例如 `W01_260920_BA`
  * **期間內只要已經有任何班次就整批拒絕 (409)**，回應會列出已有班次的日期。
    要重新產生時，請先用 1.11 刪除那段期間的班次

### 1.11 刪除班次

刪除病房在一段期間內的所有班次，例如病房容量改了、想重新產生某一週時使用

* 方法與網址: `DELETE /api/wards/{病房代碼}/shifts?start_date=2026-09-20&end_date=2026-09-26`
* 輸入 (Request): 無
* 輸出 (Response): `{"status": "success", "message": "已刪除 21 個班次"}`
* 說明:
  * **只要有任何一個班次已經排了人，或有護理師針對它提出指定班次的需求 (`SHIFT_OFF` / `SHIFT_ON`)，就整批拒絕 (409)**，
    回應的 `details` 會列出已排人的班次 (`assigned_shift_ids`) 與相關需求 (`requests`)
  * 要刪除的話，請先用 2.2 上傳空的 `assignments` 清空那段期間的排班，再用 1.4 收回那些需求
  * 期間內沒有任何班次時回傳 404

## 2. 演算法與資料庫對接

### 2.1 獲取演算法所需的所有參數 
將資料庫的表組合成完整 JSON 格式

* 方法與網址: `GET /api/solver/dataset?start_date=2026-09-20&end_date=2026-09-26&ward_id=W01` (三個參數都必填)
* 輸入 (Request): 無 
* 輸出 (Response):
  ```
  {
    "masterData": { "shiftTypes": [...] },
    "ward": { "id": "W01", "name": "預設病房", "maxPatients": 35 },
    "employees": [...],
    "roster": [
      { "employeeId": "1001", "dates": ["2026-09-20", "2026-09-21", ...] }
    ],
    "shifts": [...],
    "requests": { "dayOff": [...], "dayOn": [...], ... },
    "previousAssignments": [
      { "employeeId": "1002", "date": "2026-09-19", "shiftTypeId": "AA", "wardId": "W01" }
    ]
  }
  ```
* 說明:
  * `shifts`: 只包含該病房在期間內的班次
  * `employees`: 只包含期間內在該病房名單內、且在職的護理師
  * `roster`: 每位護理師哪幾天在名單內，**不在 `dates` 裡的日期不可排班** (不啟用)
  * `requests`: 只包含上述護理師的需求
  * `previousAssignments`: 上述護理師在開始日之前 7 天的排班紀錄 (包含其他病房)，
    演算法用來檢查跨週的休息規則，例如上週六上小夜班 (到 24:00)，這週日就不能接大夜班 (00:00 開始)

### 2.2 上傳演算法排班結果
把排班結果存進 `shift_assignments` 資料表

* 方法與網址: `POST /api/solver/assignments`
* 輸入 (Request): (演算法算出的配對結果)
  ```
  {
    "wardId": "W01",
    "startDate": "2026-09-20",
    "endDate": "2026-09-26",
    "assignments": [
      { "shiftId": "W01_260920_BA", "employeeId": "1001" },
      { "shiftId": "W01_260920_CG", "employeeId": "1004" },
      { "shiftId": "W01_260920_AA", "employeeId": "1002" }
    ]
  }
  ```
* 輸出 (Response): `{"status": "success", "message": "排班結果已寫入資料庫"}`
* 說明:
  * 該病房在 `startDate` 到 `endDate` 之間的舊排班結果會先被清掉再寫入，期間以外與其他病房都不受影響
  * `assignments` 給空陣列代表清空該期間的排班
  * 每個班次都必須屬於 `wardId` 且在期間內，否則回傳 400
  * 護理師必須在該病房當天的名單內，否則回傳 400

## 3. 最終班表查詢 (前端顯示用)

### 3.1 查詢最終班表

* 方法與網址: `GET /api/schedule?start_date=2026-09-20&end_date=2026-09-26&ward_id=W01` (三個參數都必填)
* 輸入 (Request): 無
* 輸出 (Response): (同一天依時間先後排序：大夜班、白班、小夜班)
  ```
  [
    {
      "shiftId": "W01_260920_BA",
      "date": "2026-09-20",
      "shiftTypeId": "BA",
      "shiftName": "白班",
      "expectedPatients": 35,
      "requiredNurses": 5,
      "actualPatients": 28,
      "actualRequiredNurses": 4,
      "assignedNurses": [
        { "id": "1001", "name": "Alice" },
        { "id": "1004", "name": "David" }
      ]
    },
    {
      "shiftId": "W01_260920_CG",
      "date": "2026-09-20",
      "shiftTypeId": "CG",
      "shiftName": "小夜班",
      "expectedPatients": 35,
      "requiredNurses": 4,
      "actualPatients": null,
      "actualRequiredNurses": null,
      "assignedNurses": [
        { "id": "1002", "name": "Bob" }
      ]
    }
  ]
  ```
* 說明:
  * `expectedPatients`、`requiredNurses`: 排班時的預期病人數 (病房最大容量) 與需求人數
  * `actualPatients`、`actualRequiredNurses`: 護理長填入的實際病人數與依此算出的需求人數，未填時為 `null`

## 4. 排班後調整 (護理長用)

### 4.1 填入實際病人數

* 方法與網址: `PATCH /api/shifts/{班次ID}`
* 輸入 (Request): (填 `null` 代表清除)
  ```
  { "actualPatients": 28 }
  ```
* 輸出 (Response): 附上這個班次目前的人力狀況
  ```
  {
    "status": "success",
    "message": "實際病人數已更新",
    "shift": {
      "shiftId": "W01_260920_BA",
      "wardId": "W01",
      "date": "2026-09-20",
      "shiftTypeId": "BA",
      "expectedPatients": 35,
      "requiredNurses": 5,
      "actualPatients": 28,
      "actualRequiredNurses": 4,
      "assignedCount": 5,
      "staffingDifference": 1,
      "staffingStatus": "SURPLUS"
    }
  }
  ```
* 說明:
  * 排班時的預期病人數與需求人數不會被改動，實際病人數另外記錄
  * `staffingStatus`: `SURPLUS` (人力多餘)、`OK` (剛好)、`SHORTAGE` (不足)。
    有填實際病人數時以實際需求人數為準，否則以排班時的需求人數為準
  * `staffingDifference`: 已排人數減去需求人數，正數代表多出幾人，負數代表缺幾人

### 4.2 把護理師移出班次

實際病人數較少、有人自願放假時使用

* 方法與網址: `DELETE /api/shifts/{班次ID}/assignments/{員工編號}`
* 輸入 (Request): 無
* 輸出 (Response): `{"status": "success", "message": "已將護理師移出班次", "shift": {...}}`
  (`shift` 的格式同 4.1)
* 說明: 移除後人力低於需求時**仍會執行**，但 `message` 會提醒缺幾人，`staffingStatus` 為 `SHORTAGE`，由護理長決定是否補人

# 測試資料


# 錯誤格式

無論發生什麼錯誤，都必須以固定結構回傳狀態碼

負責後端的同學請參考 `exception_handler.py` 將錯誤格式統一

負責前端的同學請使用 `if response["status"] == "error":`，
將錯誤統一捕捉，並把 `response["message"]` 直接顯示為網頁上的警告彈出視窗

以下舉例錯誤類型:

## 1. 參數錯誤或業務邏輯錯誤 (HTTP Status 400)
例如忘記輸入開始日期參數
   ```
   {
    "status": "error",
    "error_code": 400,
    "message": "缺少必要的查詢參數：start_date",
    "details": "請提供 YYYY-MM-DD 格式的日期"
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
