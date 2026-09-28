import streamlit as st
import requests
import os
from dotenv import load_dotenv

# 1. 載入環境變數 (讀取根目錄的 .env)
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# 2. 網頁標題與基本設定
st.set_page_config(page_title="護理排班系統", layout="wide")
st.title("護理排班系統 (前端測試介面)")

st.write("這是 Streamlit 前端網頁。請先確認後端 FastAPI 伺服器已經啟動。")

# 3. 測試與後端的連線 (串接 main.py 寫的根目錄 API)
st.subheader("後端連線測試")
if st.button("Ping 後端伺服器"):
    try:
        # 使用 requests 發送 HTTP GET 請求給後端
        response = requests.get(f"{API_BASE_URL}/")
        
        # 檢查 HTTP 狀態碼是否為 200 (成功)
        if response.status_code == 200:
            st.success("成功連線到後端 API！")
            st.json(response.json())
        else:
            st.error(f"連線失敗！狀態碼：{response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("無法連線！請確認 FastAPI 伺服器 (uvicorn) 是否正在執行中。")

st.divider()

# 4. 預留的核心開發區塊 (可以自由發揮)
st.subheader("核心功能區塊 (待開發)")
st.info("待開發")
