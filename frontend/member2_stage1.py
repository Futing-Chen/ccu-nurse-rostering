import json
import pandas as pd
import streamlit as st

#假資料讀取模組
st.header("假資料讀取模組")


@st.cache_data
def load_data(filepath):
  with open(filepath, "r", encoding="utf-8") as f:
    data = json.load(f)

  df_emp = pd.DataFrame(data["employees"])
  df_shifts = pd.DataFrame(data["shifts"])
  df_requests = pd.DataFrame(data["requests"]["dayOff"])
  return df_emp, df_shifts, df_requests


# 載入 JSON 資料
try:
  df_employees, df_shifts, df_day_off = load_data(
      "ccu_nurse_rostering_testing.json" #資料路徑
  )
  st.success("假資料讀取成功！")

  with st.expander("點擊檢視解析後的 DataFrame 資料"):
    col1, col2 = st.columns(2)
    with col1:
      st.subheader("護理師名單")
      st.dataframe(df_employees, use_container_width=True)
    with col2:
      st.subheader("原始請假需求 (dayOff)")
      st.dataframe(df_day_off, use_container_width=True)
except Exception as e:
  st.error(f"資料讀取失敗，請檢查 JSON 檔案路徑：{e}")

st.divider()