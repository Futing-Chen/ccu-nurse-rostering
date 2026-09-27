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

For more details, check the [getting started guide]().

## Useful Resources

Include here any other links that are relevant for the project, such as more docs, tutorials, and demos.
