import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

# 1. 載入根目錄的 .env 檔案
# 明確指定路徑，避免從其他目錄啟動 (或 uvicorn --reload 的子行程) 時找不到 .env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

# 2. 讀取環境變數中的資料庫連線設定
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    """
    建立並回傳一個 MySQL 資料庫連線。
    每次需要操作資料庫時呼叫此函數，操作完畢後請務必呼叫 connection.close() 關閉連線。
    """
    connection = pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT) if DB_PORT else 3306,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',  # 確保中文不亂碼
        cursorclass=pymysql.cursors.DictCursor  # 讓撈出的資料格式直接變成字典 (dict)
    )
    return connection
