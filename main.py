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

    df["genre"] = (
        df["genre"]
        .fillna("미상")
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
    )

    df["genre"] = df["genre"].replace("", "미상")

    return df


df = load_data()

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.write("1년간 박스오피스 10위권에 든 영화 가운데 이 기간에 개봉한 216편의 영화 데이터를 이용한 그래프 모음")

st.divider()


# ===============================
# 그래프 1
# ===============================
st.header("그래프 1. 장르별 영화 편수")

genre_counts = (
    df["genre"]
    .value_counts()
    .reset_index()
)

genre_counts.columns = ["장르", "영화 편수"]

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
    "(여기에 한 문장을 작성하면 됩니다.)"
)

st.divider()


# ===============================
# 그래프 2
# ===============================
st.header("그래프 2. (추가 예정)")
st.write("이 구역에 다음 분포 관련 그래프를 추가합니다.")

st.divider()


# ===============================
# 그래프 3
# ===============================
st.header("그래프 3. (추가 예정)")
st.write("이 구역에 다음 관계 관련 그래프를 추가합니다.")

st.divider()

```python
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

    return df


df = load_data()

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 "
    "이 기간에 개봉한 216편의 영화 데이터를 이용한 그래프 모음"
)

st.divider()


# ==================================================
# 그래프 1. 도넛 그래프
# 질문: 10위권에 든 영화의 장르 구성은 어떠한가?
# ==================================================
st.header("그래프 1. 장르별 영화 구성")

genre_counts = (
    df["genre"]
    .value_counts()
    .reset_index()
)

genre_counts.columns = ["장르", "영화 편수"]

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

st.plotly_chart(fig1, use_container_width=True)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "(10위권에 든 영화의 장르 구성을 한 문장으로 작성하세요.)"
)

st.divider()


# ==================================================
# 그래프 2. 트리맵
# 질문: 장르 안에서 어떤 영화가 컸나?
# ==================================================
st.header("그래프 2. 장르별 영화 총 관객 트리맵")

treemap_df = df[
    ["genre", "movieNm", "total_audi"]
].copy()

treemap_df["total_audi"] = pd.to_numeric(
    treemap_df["total_audi"],
    errors="coerce"
)

treemap_df = treemap_df.dropna(subset=["total_audi"])

fig2 = px.treemap(
    treemap_df,
    path=["genre", "movieNm"],
    values="total_audi",
    color="total_audi",
    title="장르 안에서 영화별 총 관객 규모",
    color_continuous_scale="Blues"
)

fig2.update_traces(
    hovertemplate=(
        "장르: %{parent}<br>"
        "영화명: %{label}<br>"
        "총 관객: %{value:,}명"
        "<extra></extra>"
    )
)

st.plotly_chart(fig2, use_container_width=True)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "(각 장르 안에서 총 관객이 많은 영화가 무엇인지 한 문장으로 작성하세요.)"
)

st.divider()


# ==================================================
# 그래프 3. 히스토그램
# 질문: 영화 대부분은 관객이 몇 명쯤인가?
# ==================================================
st.header("그래프 3. 총 관객 수 분포")

hist_df = df[["movieNm", "total_audi"]].copy()

hist_df["total_audi"] = pd.to_numeric(
    hist_df["total_audi"],
    errors="coerce"
)

hist_df = hist_df.dropna(subset=["total_audi"])

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

st.plotly_chart(fig3, use_container_width=True)

most_common_bin = None

if len(hist_df) > 0:
    counts, bins = pd.cut(
        hist_df["total_audi"],
        bins=20,
        include_lowest=True
    ).value_counts().sort_index().items()

    max_bin_count = 0

    for bin_range, count in pd.cut(
        hist_df["total_audi"],
        bins=20,
        include_lowest=True
    ).value_counts().items():
        if count > max_bin_count:
            max_bin_count = count
            most_common_bin = bin_range

most_watched_movie = (
    hist_df.loc[
        hist_df["total_audi"].idxmax(),
        "movieNm"
    ]
)

most_watched_audi = (
    hist_df["total_audi"].max()
)

if most_common_bin is not None:
    st.info(
        f"**이 그래프로 알 수 있는 것:** "
        f"영화 대부분은 약 {most_common_bin.left:,.0f}~"
        f"{most_common_bin.right:,.0f}명 구간에 몰려 있으며, "
        f"가장 관객이 많은 영화는 {most_watched_movie}이다."
    )
else:
    st.info(
        f"**이 그래프로 알 수 있는 것:** "
        f"가장 관객이 많은 영화는 {most_watched_movie}이다."
    )

st.divider()


# ==================================================
# 그래프 4. 산점도
# 질문: 스크린을 많이 받은 영화가 관객도 많나?
# ==================================================
st.header("그래프 4. 개봉일 스크린수와 총 관객의 관계")

scatter_df = df[
    ["movieNm", "genre", "first_scrn", "total_audi"]
].copy()

scatter_df["first_scrn"] = pd.to_numeric(
    scatter_df["first_scrn"],
    errors="coerce"
)

scatter_df["total_audi"] = pd.to_numeric(
    scatter_df["total_audi"],
    errors="coerce"
)

scatter_df = scatter_df.dropna(
    subset=["first_scrn", "total_audi"]
)

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
        "개봉일 스크린수: %{x:,}개<br>"
        "총 관객: %{y:,}명"
        "<extra></extra>"
    )
)

fig4.update_layout(
    xaxis_title="개봉일 스크린수",
    yaxis_title="총 관객 수"
)

st.plotly_chart(fig4, use_container_width=True)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "(개봉일 스크린수와 총 관객 사이의 관계를 한 문장으로 작성하세요.)"
)

st.divider()


# ==================================================
# 그래프 5. 박스플롯
# 질문: 장르별 관객 분포는 어떻게 다른가?
# ==================================================
st.header("그래프 5. 장르별 총 관객 분포")

genre_counts_for_box = (
    df["genre"]
    .value_counts()
)

valid_genres = genre_counts_for_box[
    genre_counts_for_box >= 10
].index

box_df = df[
    df["genre"].isin(valid_genres)
][
    ["genre", "movieNm", "total_audi"]
].copy()

box_df["total_audi"] = pd.to_numeric(
    box_df["total_audi"],
    errors="coerce"
)

box_df = box_df.dropna(
    subset=["total_audi"]
)

fig5 = px.box(
    box_df,
    x="genre",
    y="total_audi",
    points="outliers",
    hover_name="movieNm",
    title="영화 10편 이상인 장르의 총 관객 분포"
)

fig5.update_traces(
    hovertemplate=(
        "영화명: %{hovertext}<br>"
        "총 관객: %{y:,}명"
        "<extra></extra>"
    )
)

fig5.update_layout(
    xaxis_title="장르",
    yaxis_title="총 관객 수"
)

st.plotly_chart(fig5, use_container_width=True)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "(장르별 총 관객의 중앙값과 분포의 차이를 한 문장으로 작성하세요.)"
)

st.divider()


# ==================================================
# 그래프 6. 버블 그래프
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
].copy()

bubble_df["first_scrn"] = pd.to_numeric(
    bubble_df["first_scrn"],
    errors="coerce"
)

bubble_df["total_audi"] = pd.to_numeric(
    bubble_df["total_audi"],
    errors="coerce"
)

bubble_df["first_week_audi"] = pd.to_numeric(
    bubble_df["first_week_audi"],
    errors="coerce"
)

bubble_df = bubble_df.dropna(
    subset=[
        "first_scrn",
        "total_audi",
        "first_week_audi"
    ]
)

bubble_df["버블크기"] = bubble_df["first_week_audi"].clip(lower=1)

fig6 = px.scatter(
    bubble_df,
    x="first_scrn",
    y="total_audi",
    size="버블크기",
    color="genre",
    hover_name="movieNm",
    size_max=55,
    title="개봉일 스크린수 × 총 관객 × 첫 주 관객"
)

fig6.update_traces(
    hovertemplate=(
        "영화명: %{hovertext}<br>"
        "개봉일 스크린수: %{x:,}개<br>"
        "총 관객: %{y:,}명<br>"
        "첫 주 관객: %{marker.size:,}명"
        "<extra></extra>"
    )
)

fig6.update_layout(
    xaxis_title="개봉일 스크린수",
    yaxis_title="총 관객 수"
)

st.plotly_chart(fig6, use_container_width=True)

st.info(
    "**이 그래프로 알 수 있는 것:** "
    "(스크린수와 총 관객의 관계에 첫 주 관객이라는 변수를 추가했을 때 보이는 특징을 한 문장으로 작성하세요.)"
)

st.divider()


# ==================================================
# 그래프 7. 선버스트
# 질문: 국가에서 장르로 내려가면 보이나?
# ==================================================
st.header("그래프 7. 국가 → 장르 선버스트")

sunburst_df = df[
    ["nation", "genre", "movieNm"]
].copy()

sunburst_df["nation"] = (
    sunburst_df["nation"]
    .fillna("미상")
    .astype(str)
    .str.strip()
)

sunburst_df["genre"] = (
    sunburst_df["genre"]
    .fillna("미상")
    .astype(str)
    .str.strip()
)

sunburst_df["nation"] = sunburst_df["nation"].replace("", "미상")
sunburst_df["genre"] = sunburst_df["genre"].replace("", "미상")

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
    "(제작 국가별 장르 구성을 통해 어떤 국가와 장르의 조합이 많이 나타나는지 한 문장으로 작성하세요.)"
)
```
