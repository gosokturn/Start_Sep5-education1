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

    required_columns = [
        "날짜",
        "순위",
        "영화코드",
        "영화명",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "다음 열을 찾을 수 없습니다: "
            + ", ".join(missing_columns)
        )

    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str).str.replace(".0", "", regex=False),
        format="%Y%m%d",
        errors="coerce"
    )

    numeric_columns = [
        "순위",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

    df["영화명"] = (
        df["영화명"]
        .fillna("영화명 없음")
        .astype(str)
    )

    df = df.dropna(subset=["날짜"])

    df = df.sort_values(
        ["날짜", "순위", "영화코드"]
    )

    return df


df = load_data()

start_date = df["날짜"].min().strftime("%Y-%m-%d")
end_date = df["날짜"].max().strftime("%Y-%m-%d")

st.title("🎬 영화 데이터 그래프 도감 1 - 시간")

st.write(
    f"기준 기간: {start_date} ~ {end_date}"
)

st.write(
    "1년치 일별 박스오피스 10위권 기록을 이용한 시간 그래프 모음"
)

st.divider()


# ==================================================
# 그래프 1
# 질문: 영화별 날짜에 따른 일관객 변화
# ==================================================
st.header("그래프 1. 영화별 날짜에 따른 일관객 변화")

movie_list = sorted(
    df["영화명"].dropna().unique().tolist()
)

selected_movie = st.selectbox(
    "영화를 선택하세요.",
    movie_list,
    key="graph1_movie"
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
    hovertemplate=(
        "날짜: %{x|%Y-%m-%d}<br>"
        "일관객: %{y:,.0f}명"
        "<extra></extra>"
    )
)

fig1.update_layout(
    xaxis_title="날짜",
    yaxis_title="일관객 수",
    hovermode="x"
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "영화의 날짜별 일관객 변화를 통해 흥행의 증가와 감소 시점 및 관객이 많이 몰린 시기를 알 수 있다."
)

st.divider()


# ==================================================
# 그래프 2
# 질문: 일관객 합계가 큰 영화 5편의 날짜별 변화
# ==================================================
st.header(
    "그래프 2. 일관객 합계 상위 5편의 날짜별 일관객 변화"
)

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
    hovertemplate=(
        "영화명: %{fullData.name}<br>"
        "날짜: %{x|%Y-%m-%d}<br>"
        "일관객: %{y:,.0f}명"
        "<extra></extra>"
    )
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

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "일관객 합계가 높은 상위 5편을 비교하여 영화마다 흥행 규모와 흥행이 집중되는 시기의 차이를 알 수 있다."
)

st.divider()


# ==================================================
# 그래프 3
# 질문: 날짜별 10위권 일관객 합계
# ==================================================
st.header("그래프 3. 날짜별 10위권 일관객 합계")

daily_total = (
    df.groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
)

top3_days = (
    daily_total
    .nlargest(3, "일관객")
    .sort_values("일관객", ascending=False)
)

fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=daily_total["날짜"],
        y=daily_total["일관객"],
        mode="lines",
        fill="tozeroy",
        name="10위권 일관객 합계",
        hovertemplate=(
            "날짜: %{x|%Y-%m-%d}<br>"
            "일관객 합계: %{y:,.0f}명"
            "<extra></extra>"
        )
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
        hovertemplate=(
            "날짜: %{x|%Y-%m-%d}<br>"
            "일관객 합계: %{y:,.0f}명"
            "<extra></extra>"
        )
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

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "날짜별 박스오피스 10위권 전체의 관객 규모를 비교하여 관객이 가장 많이 몰린 날과 적었던 날을 알 수 있다."
)

st.divider()


# ==================================================
# 그래프 4
# 질문: 영화별 기간 일관객 TOP 10
# ==================================================
st.header("그래프 4. 영화별 기간 일관객 TOP 10")

movie_summary = (
    df.groupby("영화명")
    .agg(
        기간_일관객=("일관객", "sum"),
        top10_일수=("날짜", "nunique")
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
    custom_data=["top10_일수"]
)

fig4.update_traces(
    hovertemplate=(
        "영화명: %{y}<br>"
        "기간 일관객: %{x:,.0f}명<br>"
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

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "전체 기간 동안 관객을 많이 동원한 영화와 각 영화가 10위권에 머문 날수를 비교할 수 있다."
)

st.divider()


# ==================================================
# 그래프 5
# 질문: 월 × 요일별 일관객 합계
# ==================================================
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
    df.groupby(
        ["월", "요일"],
        as_index=False
    )["일관객"]
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
        "일관객 합계: %{z:,.0f}명"
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

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "월별·요일별 관객 수를 비교하여 어느 시기의 어느 요일에 영화 관람객이 많이 몰리는지 파악할 수 있다."
)
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    layout="wide"
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    required_columns = [
        "movieCd",
        "movieNm",
        "openDt",
        "genre",
        "nation",
        "first_scrn",
        "first_show",
        "first_week_audi",
        "total_audi",
        "days_in_top10"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "다음 열을 찾을 수 없습니다: "
            + ", ".join(missing_columns)
        )

    df["genre"] = (
        df["genre"]
        .fillna("미상")
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
    )

    df["genre"] = df["genre"].replace("", "미상")

    df["nation"] = (
        df["nation"]
        .fillna("미상")
        .astype(str)
        .str.strip()
    )

    df["nation"] = df["nation"].replace("", "미상")

    numeric_columns = [
        "first_scrn",
        "first_show",
        "first_week_audi",
        "total_audi",
        "days_in_top10"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

    return df


df = load_data()

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")

st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 "
    "이 기간에 개봉한 영화의 요약 데이터를 이용한 그래프 모음"
)

st.divider()


# ==================================================
# 그래프 1. 도넛 그래프
# 질문: 10위권에 든 영화의 장르 구성은 어떠한가?
# ==================================================
st.header("그래프 1. 장르별 영화 편수")

genre_counts = (
    df["genre"]
    .value_counts()
    .rename_axis("장르")
    .reset_index(name="영화 편수")
)

fig1 = px.pie(
    genre_counts,
    names="장르",
    values="영화 편수",
    hole=0.45,
    title="장르별 영화 편수"
)

fig1.update_traces(
    hovertemplate=(
        "장르: %{label}<br>"
        "영화 편수: %{value}편<br>"
        "비율: %{percent}"
        "<extra></extra>"
    )
)

fig1.update_layout(
    showlegend=True
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "10위권에 든 영화의 장르 구성과 장르별 비율을 확인할 수 있다."
)

st.divider()


# ==================================================
# 그래프 2. 트리맵
# 질문: 장르 안에서 어떤 영화가 컸나?
# ==================================================
st.header("그래프 2. 장르별 영화 총 관객 트리맵")

treemap_df = df[
    ["genre", "movieNm", "total_audi"]
].dropna(
    subset=["total_audi"]
).copy()

treemap_df = treemap_df[
    treemap_df["total_audi"] > 0
]

fig2 = px.treemap(
    treemap_df,
    path=["genre", "movieNm"],
    values="total_audi",
    color="total_audi",
    color_continuous_scale="Blues",
    title="장르 안에서 영화별 총 관객 규모"
)

fig2.update_traces(
    hovertemplate=(
        "영화명: %{label}<br>"
        "총 관객: %{value:,.0f}명"
        "<extra></extra>"
    )
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "각 장르 안에서 총 관객을 많이 모은 영화가 무엇인지 비교할 수 있다."
)

st.divider()


# ==================================================
# 그래프 3. 히스토그램
# 질문: 영화 대부분은 관객이 몇 명쯤인가?
# ==================================================
st.header("그래프 3. 총 관객 수 분포")

hist_df = df[
    ["movieNm", "total_audi"]
].dropna(
    subset=["total_audi"]
).copy()

fig3 = px.histogram(
    hist_df,
    x="total_audi",
    nbins=20,
    title="영화별 총 관객 수 분포"
)

fig3.update_traces(
    hovertemplate=(
        "총 관객 구간: %{x}<br>"
        "영화 수: %{y}편"
        "<extra></extra>"
    )
)

fig3.update_layout(
    xaxis_title="총 관객 수",
    yaxis_title="영화 편수"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

hist_bins = pd.cut(
    hist_df["total_audi"],
    bins=20,
    include_lowest=True
)

bin_counts = hist_bins.value_counts()

if not bin_counts.empty:
    most_common_bin = bin_counts.idxmax()

    most_watched_index = hist_df[
        "total_audi"
    ].idxmax()

    most_watched_movie = hist_df.loc[
        most_watched_index,
        "movieNm"
    ]

    most_watched_audi = hist_df.loc[
        most_watched_index,
        "total_audi"
    ]

    st.info(
        f"**이 그래프로 알 수 있는 것:** "
        f"영화 대부분은 약 "
        f"{most_common_bin.left:,.0f}~"
        f"{most_common_bin.right:,.0f}명 구간에 몰려 있으며, "
        f"가장 관객이 많은 영화는 "
        f"{most_watched_movie}"
        f"({most_watched_audi:,.0f}명)이다."
    )
else:
    st.info(
        "**이 그래프로 알 수 있는 것:** "
        "총 관객 수의 분포를 확인할 수 있다."
    )

st.divider()


# ==================================================
# 그래프 4. 산점도
# 질문: 스크린을 많이 받은 영화가 관객도 많나?
# ==================================================
st.header("그래프 4. 개봉일 스크린수와 총 관객의 관계")

scatter_df = df[
    [
        "movieNm",
        "genre",
        "first_scrn",
        "total_audi"
    ]
].dropna(
    subset=[
        "first_scrn",
        "total_audi"
    ]
).copy()

fig4 = px.scatter(
    scatter_df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    title="개봉일 스크린수와 총 관객의 관계"
)

fig4.update_traces(
    hovertemplate=(
        "영화명: %{hovertext}<br>"
        "개봉일 스크린수: %{x:,.0f}개<br>"
        "총 관객: %{y:,.0f}명"
        "<extra></extra>"
    )
)

fig4.update_layout(
    xaxis_title="개봉일 스크린수",
    yaxis_title="총 관객 수"
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "개봉일 스크린수가 많은 영화가 더 많은 관객을 모으는지 관계를 확인할 수 있다."
)

st.divider()


# ==================================================
# 그래프 5. 박스플롯
# 질문: 장르별 관객 분포는 어떻게 다른가?
# ==================================================
st.header("그래프 5. 장르별 총 관객 분포")

genre_counts_box = df["genre"].value_counts()

valid_genres = genre_counts_box[
    genre_counts_box >= 10
].index

box_df = df[
    df["genre"].isin(valid_genres)
][
    [
        "genre",
        "movieNm",
        "total_audi"
    ]
].dropna(
    subset=["total_audi"]
).copy()

fig5 = px.box(
    box_df,
    x="genre",
    y="total_audi",
    points="outliers",
    hover_name="movieNm",
    title="영화가 10편 이상인 장르의 총 관객 분포"
)

fig5.update_traces(
    hovertemplate=(
        "영화명: %{hovertext}<br>"
        "장르: %{x}<br>"
        "총 관객: %{y:,.0f}명"
        "<extra></extra>"
    )
)

fig5.update_layout(
    xaxis_title="장르",
    yaxis_title="총 관객 수"
)

st.plotly_chart(
    fig5,
    use_container_width=True
)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "영화가 10편 이상인 장르별로 총 관객의 중앙값과 분포가 어떻게 다른지 비교할 수 있다."
)

st.divider()


# ==================================================
# 그래프 6. 버블
# 질문: 첫 주 관객까지 넣으면 무엇이 더 보이나?
# ==================================================
st.header("그래프 6. 첫 주 관객을 포함한 버블 그래프")

bubble_df = df[
    [
        "movieNm",
        "genre",
        "first_scrn",
        "total_audi",
        "first_week_audi"
    ]
].dropna(
    subset=[
        "first_scrn",
        "total_audi",
        "first_week_audi"
    ]
).copy()

bubble_df["first_week_audi_size"] = (
    bubble_df["first_week_audi"].clip(lower=1)
)

fig6 = px.scatter(
    bubble_df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi_size",
    color="genre",
    hover_name="movieNm",
    size_max=55,
    title="개봉일 스크린수 × 총 관객 × 첫 주 관객"
)

fig6.update_traces(
    customdata=bubble_df[
        ["first_week_audi"]
    ],
    hovertemplate=(
        "영화명: %{hovertext}<br>"
        "개봉일 스크린수: %{x:,.0f}개<br>"
        "총 관객: %{y:,.0f}명<br>"
        "첫 주 관객: %{customdata[0]:,.0f}명"
        "<extra></extra>"
    )
)

fig6.update_layout(
    xaxis_title="개봉일 스크린수",
    yaxis_title="총 관객 수"
)

st.plotly_chart(
    fig6,
    use_container_width=True
)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "스크린수와 총 관객의 관계에 첫 주 관객 규모를 추가하여 영화별 흥행 양상을 더 자세히 비교할 수 있다."
)

st.divider()


# ==================================================
# 그래프 7. 선버스트
# 질문: 국가에서 장르로 내려가면 보이나?
# ==================================================
st.header("그래프 7. 국가 → 장르 선버스트")

sunburst_df = df[
    [
        "nation",
        "genre"
    ]
].dropna(
    subset=[
        "nation",
        "genre"
    ]
).copy()

fig7 = px.sunburst(
    sunburst_df,
    path=["nation", "genre"],
    title="제작 국가에서 장르로 내려가는 영화 구성"
)

fig7.update_traces(
    hovertemplate=(
        "항목: %{label}<br>"
        "영화 편수: %{value}편"
        "<extra></extra>"
    )
)

st.plotly_chart(
    fig7,
    use_container_width=True
)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "제작 국가에서 장르로 내려가며 각 국가의 영화 장르 구성을 확인할 수 있다."
)
