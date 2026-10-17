
import streamlit as st

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

pages = [
    {
        "path": "home.py",
        "title": "소개",
        "icon": "🧠",
        "default": True
    },
    {
        "path": "pages/1_탐색.py",
        "title": "탐색",
        "icon": "🔎"
    },
    {
        "path": "pages/2_분류_모델.py",
        "title": "분류 모델",
        "icon": "🤖"
    },
    {
        "path": "pages/3_채점표.py",
        "title": "채점표",
        "icon": "📋"
    },
    {
        "path": "pages/4_전처리.py",
        "title": "전처리",
        "icon": "🧹"
    }
]

page_objects = [
    st.Page(
        page["path"],
        title=page["title"],
        icon=page["icon"],
        default=page.get("default", False)
    )
    for page in pages
]

navigation = st.navigation(
    {"뇌졸중 예측 실습실": page_objects},
    position="sidebar",
    expanded=True
)

navigation.run()
