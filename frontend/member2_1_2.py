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
#-----------------------
#護理師請假輸入介面
st.header(" 護理師請假輸入介面")

col_a, col_b = st.columns(2)

with col_a:
  # 下拉選單選擇護理師
  nurse_names = df_employees["name"].tolist()
  selected_nurse = st.selectbox("選擇護理師", options=nurse_names)
  # 取得選擇的護理師 ID
  selected_emp_id = df_employees[df_employees["name"] == selected_nurse][
      "id"
  ].values[0]

with col_b:
  # 日期選擇器
  selected_date = st.date_input("選擇休假日期")

if st.button("提交請假申請"):
  st.info(
      f"登記成功！護理師：**{selected_nurse}** (ID: {selected_emp_id})，日期：**{selected_date}**"
  )

st.divider()
