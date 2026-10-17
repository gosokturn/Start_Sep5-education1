
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

classification_page = st.Page(
    "pages/2_분류_모델.py",
    title="분류 모델",
    icon="🤖"
)

navigation = st.navigation(
    {
        "뇌졸중 예측 실습실": [
            home_page,
            explore_page,
            classification_page
        ]
    },
    position="sidebar",
    expanded=True
)

navigation.run()

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


score_page = st.Page(
    "pages/3_채점표.py",
    title="채점표",
    icon="📋"
)

navigation = st.navigation(
    {
        "뇌졸중 예측 실습실": [
            home_page,
            explore_page,
            classification_page,
            score_page
        ]
    },
    position="sidebar",
    expanded=True
)

navigation.run()


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

classification_page = st.Page(
    "pages/2_분류_모델.py",
    title="분류 모델",
    icon="🤖"
)

score_page = st.Page(
    "pages/3_채점표.py",
    title="채점표",
    icon="📋"
)

preprocessing_page = st.Page(
    "pages/4_전처리.py",
    title="전처리",
    icon="🧹"
)

navigation = st.navigation(
    {
        "뇌졸중 예측 실습실": [
            home_page,
            explore_page,
            classification_page,
            score_page,
            preprocessing_page
        ]
    },
    position="sidebar",
    expanded=True
)

navigation.run()
