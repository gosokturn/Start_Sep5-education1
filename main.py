import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    layout="wide"
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    df["날짜"] = pd.to_datetime(df["날짜"].astype(str), format="%Y%m%d")
    df = df.sort_values("날짜")

    return df

df = load_data()

st.title("🎬 영화 데이터 그래프 도감 1 - 시간")
st.write("2024년 박스오피스 일별 TOP10 영화 데이터를 이용한 시간 그래프 모음")

st.divider()

# ===============================
# 그래프 1
# ===============================
st.header("그래프 1. 영화별 날짜에 따른 일관객 변화")

movie_list = sorted(df["영화명"].unique())

selected_movie = st.selectbox(
    "영화를 선택하세요.",
    movie_list
)

movie_df = (
    df[df["영화명"] == selected_movie]
    .sort_values("날짜")
)

fig = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"{selected_movie}의 날짜별 일관객 변화",
    hover_data={
        "날짜": True,
        "일관객": ":,"
    }
)

fig.update_layout(
    xaxis_title="날짜",
    yaxis_title="일관객 수",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

st.info("**이 그래프로 알 수 있는 것:** (여기에 한 문장을 작성하면 됩니다.)")

st.divider()

# ===============================
# 그래프 2 (추가 예정)
# ===============================
st.header("그래프 2. (추가 예정)")
st.write("이 구역에 다음 시간 관련 그래프를 추가합니다.")

st.divider()

# ===============================
# 그래프 3 (추가 예정)
# ===============================
st.header("그래프 3. (추가 예정)")
st.write("이 구역에 다음 시간 관련 그래프를 추가합니다.")
