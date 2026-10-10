import streamlit as st


st.set_page_config(
    page_title="智慧護理排班系統",
    page_icon="🏥",
    layout="wide"
)


# =========================
# 首頁
# =========================

def home():
    st.title("🏥 智慧護理排班系統")

    st.write("歡迎使用智慧護理排班系統。")

    st.write("請利用左側選單進行操作：")

    st.markdown(
        """
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


# =========================
# 頁面設定
# =========================

home_page = st.Page(
    home,
    title="首頁",
    icon="🏠",
    default=True
)

settings_page = st.Page(
    "pages/1_settings.py",
    title="設定參數",
    icon="⚙️"
)

schedule_requests_page = st.Page(
    "pages/2_schedule_requests.py",
    title="排班輸入",
    icon="📋"
)

schedule_view_page = st.Page(
    "pages/3_schedule_view.py",
    title="結果檢視",
    icon="📊"
)


# =========================
# Sidebar Navigation
# =========================

pg = st.navigation(
    [
        home_page,
        settings_page,
        schedule_requests_page,
        schedule_view_page
    ]
)

pg.run()