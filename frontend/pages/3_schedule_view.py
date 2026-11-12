import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="結果檢視",
    page_icon="📊",
    layout="wide"
)

st.title("📊 排班結果檢視")

st.write("目前使用假資料展示排班結果。")

data = {
    "日期": [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
        "2026-10-04",
        "2026-10-05",
    ],
    "白班": [
        "護理師A、護理師B",
        "護理師C、護理師D",
        "護理師A、護理師E",
        "護理師B、護理師C",
        "護理師D、護理師E",
    ],
    "小夜": [
        "護理師C",
        "護理師A",
        "護理師B",
        "護理師D",
        "護理師A",
    ],
    "大夜": [
        "護理師D",
        "護理師E",
        "護理師C",
        "護理師A",
        "護理師B",
    ],
}

df = pd.DataFrame(data)

st.subheader("班表")

st.dataframe(
    df,
    use_container_width=True
)