import streamlit as st

st.set_page_config(
    page_title="智慧護理排班系統",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 智慧護理排班系統")

st.write(
    """
    歡迎使用智慧護理排班系統。

    請利用左側選單進行操作：
    - ⚙️ 設定參數
    - 📋 排班輸入
    - 📊 結果檢視
    """
)

st.divider()

st.subheader("系統功能")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("⚙️ 設定排班參數與護病比")

with col2:
    st.info("📋 輸入排班相關資料")

with col3:
    st.info("📊 查看排班結果")