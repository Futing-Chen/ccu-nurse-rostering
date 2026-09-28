import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 1. 載入根目錄的 .env 檔案，把裡面的密碼變成環境變數
load_dotenv()

# 2. 讀取資料庫連線設定
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# 3. 組裝 MySQL 連線字串 (指定使用 pymysql 驅動，並強制使用 utf8mb4 編碼防中文亂碼)
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 4. 建立 SQLAlchemy 的核心引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 5. 建立資料庫會話 (Session) 工廠，用來與資料庫進行實際的讀寫對話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6. 建立 ORM 模型的基底類別 (後續定義資料表時都要繼承它)
Base = declarative_base()

# 7. FastAPI 專用的依賴注入函數 (Dependency)
def get_db():
    """
    這是一個產生器，確保每個 API 請求進來時打開連線，
    處理完畢或發生錯誤時，自動安全地關閉資料庫連線，防止系統卡死。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
