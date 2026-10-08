import streamlit as st

st.set_page_config(
    page_title="設定參數",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ 排班參數設定")

st.write("請設定各班別的床位數與護病比。")

st.divider()

st.subheader("床位設定")

col1, col2, col3 = st.columns(3)

with col1:
    day_beds = st.number_input(
        "白班床位數",
        min_value=0,
        value=30,
        step=1
    )

with col2:
    evening_beds = st.number_input(
        "小夜班床位數",
        min_value=0,
        value=30,
        step=1
    )

with col3:
    night_beds = st.number_input(
        "大夜班床位數",
        min_value=0,
        value=30,
        step=1
    )

st.subheader("護病比設定")

col1, col2, col3 = st.columns(3)

with col1:
    day_ratio = st.number_input(
        "白班護病比 1 :",
        min_value=1,
        value=7,
        step=1
    )

with col2:
    evening_ratio = st.number_input(
        "小夜班護病比 1 :",
        min_value=1,
        value=11,
        step=1
    )

with col3:
    night_ratio = st.number_input(
        "大夜班護病比 1 :",
        min_value=1,
        value=13,
        step=1
    )

if st.button("💾 儲存設定"):
    st.session_state["schedule_settings"] = {
        "day_beds": day_beds,
        "evening_beds": evening_beds,
        "night_beds": night_beds,
        "day_ratio": day_ratio,
        "evening_ratio": evening_ratio,
        "night_ratio": night_ratio,
    }

    st.success("設定已儲存")