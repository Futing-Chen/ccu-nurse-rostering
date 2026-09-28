from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 匯入在 api 資料夾寫好的路由器
from api.endpoints import router as api_router

# 1. 初始化 FastAPI 應用程式
app = FastAPI(
    title="護理排班系統 API",
    description="提供給 Streamlit 前端與 n8n 自動化串接的核心後端服務",
    version="1.0.0"
)

# 2. 設定 CORS (跨來源資源共用) - 防雷機制
# 因為 Streamlit 網頁 (通常在 port 8501) 和 n8n 
# 要呼叫這台 FastAPI (通常在 port 8000)，不同 port 會被瀏覽器當作「跨網域」阻擋。
# 加上這段設定才能順利拿到資料。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發測試期先允許所有網域連線，上線後可限縮
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法 (GET, POST 等)
    allow_headers=["*"],  # 允許所有標頭
)

# 3. 註冊 API 路由
# 加上 prefix="/api" 後，endpoints.py 裡的 "/generate-schedule" 
# 完整網址就會變成 "http://127.0.0.1:8000/api/generate-schedule"
app.include_router(api_router, prefix="/api")

# 4. 根目錄預設回應 (確認伺服器存活的最基本頁面)
@app.get("/")
def read_root():
    return {
        "status": "success", 
        "message": "歡迎來到護理排班系統 API 伺服器！請在網址後方加上 /docs 查看自動化文件。"
    }
