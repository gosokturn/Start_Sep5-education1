import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    layout="wide"
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d"
    )

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

fig1 = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"{selected_movie}의 날짜별 일관객 변화"
)

fig1.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra></extra>"
)

fig1.update_layout(
    xaxis_title="날짜",
    yaxis_title="일관객 수",
    hovermode="x"
)

st.plotly_chart(fig1, use_container_width=True)

st.info("**이 그래프로 알 수 있는 것:** (여기에 한 문장을 작성하면 됩니다.)")

st.divider()


# ===============================
# 그래프 2
# ===============================
st.header("그래프 2. 일관객 합계 상위 5편의 날짜별 일관객 변화")

top5_movies = (
    df.groupby("영화명", as_index=False)["일관객"]
    .sum()
    .sort_values("일관객", ascending=False)
    .head(5)["영화명"]
    .tolist()
)

top5_df = (
    df[df["영화명"].isin(top5_movies)]
    .sort_values(["영화명", "날짜"])
)

fig2 = px.line(
    top5_df,
    x="날짜",
    y="일관객",
    color="영화명",
    markers=True,
    title="일관객 합계가 가장 큰 5편의 날짜별 일관객 변화"
)

fig2.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra></extra>"
)

fig2.update_layout(
    xaxis_title="날짜",
    yaxis_title="일관객 수",
    hovermode="x"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

st.info("**이 그래프로 알 수 있는 것:** (여기에 한 문장을 작성하면 됩니다.)")

st.divider()


# ===============================
# 그래프 3
# ===============================
st.header("그래프 3. 날짜별 10위권 일관객 합계")

daily_total = (
    df.groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
)

top3_days = (
    daily_total
    .nlargest(3, "일관객")
    .sort_values("날짜")
)

fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=daily_total["날짜"],
        y=daily_total["일관객"],
        mode="lines",
        fill="tozeroy",
        name="10위권 일관객 합계",
        hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객 합계: %{y:,}명<extra></extra>"
    )
)

fig3.add_trace(
    go.Scatter(
        x=top3_days["날짜"],
        y=top3_days["일관객"],
        mode="markers+text",
        text=top3_days["날짜"].dt.strftime("%Y-%m-%d"),
        textposition="top center",
        name="일관객 합계 상위 3일",
        hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객 합계: %{y:,}명<extra></extra>"
    )
)

fig3.update_layout(
    title="날짜별 10위권 일관객 합계",
    xaxis_title="날짜",
    yaxis_title="일관객 합계",
    hovermode="x"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

st.info("**이 그래프로 알 수 있는 것:** (여기에 한 문장을 작성하면 됩니다.)")

st.divider()


# ===============================
# 그래프 4 (추가 예정)
# ===============================
st.header("그래프 4. (추가 예정)")
st.write("이 구역에 다음 시간 관련 그래프를 추가합니다.")

st.divider()

# ===============================
# 그래프 4
# ===============================
st.header("그래프 4. 영화별 기간 일관객 TOP 10")

movie_summary = (
    df.groupby("영화명")
    .agg(
        기간_일관객=("일관객", "sum"),
        top10_일수=("날짜", "count")
    )
    .reset_index()
)

top10_movies = (
    movie_summary
    .sort_values("기간_일관객", ascending=False)
    .head(10)
    .sort_values("기간_일관객", ascending=True)
)

fig4 = px.bar(
    top10_movies,
    x="기간_일관객",
    y="영화명",
    orientation="h",
    title="이 기간 일관객 합계 TOP 10",
    text="기간_일관객",
    custom_data=["top10_일수"]
)

fig4.update_traces(
    hovertemplate=(
        "영화: %{y}<br>"
        "기간 일관객: %{x:,}명<br>"
        "10위권에 든 날수: %{customdata[0]}일"
        "<extra></extra>"
    )
)

fig4.update_layout(
    xaxis_title="기간 일관객 합계",
    yaxis_title="영화명"
)

fig4.update_xaxes(
    tickformat=","
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

st.info("**이 그래프로 알 수 있는 것:** (여기에 한 문장을 작성하면 됩니다.)")

st.divider()


# ===============================
# 그래프 5 (추가 예정)
# ===============================
st.header("그래프 5. (추가 예정)")
st.write("이 구역에 다음 그래프를 추가합니다.")

st.divider()
# ===============================
# 그래프 5
# ===============================
st.header("그래프 5. 월 × 요일별 일관객 합계")

weekday_order = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일",
    "일요일"
]

df["월"] = df["날짜"].dt.month
df["요일"] = df["날짜"].dt.dayofweek.map(
    dict(enumerate(weekday_order))
)

month_weekday = (
    df.groupby(["월", "요일"], as_index=False)["일관객"]
    .sum()
)

heatmap_data = (
    month_weekday
    .pivot(
        index="월",
        columns="요일",
        values="일관객"
    )
    .reindex(columns=weekday_order)
    .fillna(0)
)

fig5 = px.imshow(
    heatmap_data,
    labels={
        "x": "요일",
        "y": "월",
        "color": "일관객 합계"
    },
    x=weekday_order,
    y=heatmap_data.index,
    text_auto=",",
    aspect="auto",
    color_continuous_scale="Blues",
    title="월 × 요일별 일관객 합계"
)

fig5.update_traces(
    hovertemplate=(
        "%{y}월 %{x}<br>"
        "일관객 합계: %{z:,}명"
        "<extra></extra>"
    )
)

fig5.update_layout(
    xaxis_title="요일",
    yaxis_title="월"
)

st.plotly_chart(
    fig5,
    use_container_width=True
)

st.info("**이 그래프로 알 수 있는 것:** (여기에 한 문장을 작성하면 됩니다.)")

st.divider()


# ===============================
# 그래프 6 (추가 예정)
# ===============================
st.header("그래프 6. (추가 예정)")
st.write("이 구역에 다음 그래프를 추가합니다.")

st.divider()
