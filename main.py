
import streamlit as st

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

home_page = st.Page(
    "home.py",
    title="소개",
    icon="🧠",
    default=True
)

explore_page = st.Page(
    "pages/1_탐색.py",
    title="탐색",
    icon="🔎"
)

navigation = st.navigation(
    {
        "뇌졸중 예측 실습실": [
            home_page,
            explore_page
        ]
    },
    position="sidebar",
    expanded=True
)

navigation.run()
