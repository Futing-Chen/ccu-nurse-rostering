import math
import streamlit as st

st.set_page_config(
    page_title="設定參數",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ 排班參數設定")
st.write("請設定各班別的床位數與護病比。")

st.divider()


# =========================
# 初始化 Session State
# =========================

if "day_beds" not in st.session_state:
    st.session_state.day_beds = 30

if "evening_beds" not in st.session_state:
    st.session_state.evening_beds = 30

if "night_beds" not in st.session_state:
    st.session_state.night_beds = 30

if "day_ratio" not in st.session_state:
    st.session_state.day_ratio = 7

if "evening_ratio" not in st.session_state:
    st.session_state.evening_ratio = 11

if "night_ratio" not in st.session_state:
    st.session_state.night_ratio = 13


# =========================
# 床位設定
# =========================

st.subheader("🛏️ 床位設定")

col1, col2, col3 = st.columns(3)

with col1:
    day_beds = st.number_input(
        "白班床位數",
        min_value=0,
        step=1,
        key="day_beds"
    )

with col2:
    evening_beds = st.number_input(
        "小夜班床位數",
        min_value=0,
        step=1,
        key="evening_beds"
    )

with col3:
    night_beds = st.number_input(
        "大夜班床位數",
        min_value=0,
        step=1,
        key="night_beds"
    )


# =========================
# 護病比設定
# =========================

st.subheader("👩‍⚕️ 護病比設定")

col1, col2, col3 = st.columns(3)

with col1:
    day_ratio = st.number_input(
        "白班護病比 1 :",
        min_value=1,
        step=1,
        key="day_ratio"
    )

with col2:
    evening_ratio = st.number_input(
        "小夜班護病比 1 :",
        min_value=1,
        step=1,
        key="evening_ratio"
    )

with col3:
    night_ratio = st.number_input(
        "大夜班護病比 1 :",
        min_value=1,
        step=1,
        key="night_ratio"
    )


# =========================
# 計算最低護理師需求
# =========================

day_nurses = math.ceil(day_beds / day_ratio)
evening_nurses = math.ceil(evening_beds / evening_ratio)
night_nurses = math.ceil(night_beds / night_ratio)

st.divider()

st.subheader("📊 各班最低護理師需求")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "白班最低人數",
        f"{day_nurses} 人"
    )

with col2:
    st.metric(
        "小夜班最低人數",
        f"{evening_nurses} 人"
    )

with col3:
    st.metric(
        "大夜班最低人數",
        f"{night_nurses} 人"
    )


# =========================
# 儲存設定
# =========================

if st.button("💾 儲存設定", type="primary"):

    st.session_state["schedule_settings"] = {
        "day": {
            "beds": day_beds,
            "ratio": day_ratio,
            "required_nurses": day_nurses
        },

        "evening": {
            "beds": evening_beds,
            "ratio": evening_ratio,
            "required_nurses": evening_nurses
        },

        "night": {
            "beds": night_beds,
            "ratio": night_ratio,
            "required_nurses": night_nurses
        }
    }

    st.success("✅ 排班參數已成功儲存！")