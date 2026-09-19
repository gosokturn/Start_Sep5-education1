
import streamlit as st
import pandas as pd
import math
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

st.set_page_config(
    page_title="🎬 영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 유형 나누기")

URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

df = pd.read_csv(URL, encoding="utf-8")

total_movies = len(df)

numeric_cols = ["first_scrn", "total_audi", "days_in_top10", "first_week_audi"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 상용로그 계산
df["log_first_scrn"] = df["first_scrn"].apply(
    lambda x: math.log10(x) if pd.notna(x) and x > 0 else pd.NA
)

df["log_total_audi"] = df["total_audi"].apply(
    lambda x: math.log10(x) if pd.notna(x) and x > 0 else pd.NA
)

# 롱런 지수 계산
df["longrun_index"] = df["total_audi"] / df["first_week_audi"]
df.loc[df["first_week_audi"] <= 0, "longrun_index"] = pd.NA
df["longrun_index"] = df["longrun_index"].clip(upper=20)

feature_map = {
    "스크린 수(상용로그)": "log_first_scrn",
    "누적 관객(상용로그)": "log_total_audi",
    "10위권 일수": "days_in_top10",
    "롱런 지수": "longrun_index",
}

selected_labels = st.multiselect(
    "묶는 데 사용할 속성 선택",
    options=list(feature_map.keys()),
    default=list(feature_map.keys())
)

if len(selected_labels) < 2:
    st.warning("속성을 두 개 이상 선택하세요.")
    st.stop()

selected_features = [feature_map[label] for label in selected_labels]

cluster_df = df.dropna(subset=selected_features).copy()

total_clustered = len(cluster_df)

st.write(f"**전체 영화:** {total_movies}편 | **묶은 영화:** {total_clustered}편")

# 표준화
scaler = StandardScaler()
X = scaler.fit_transform(cluster_df[selected_features])

# KMeans
kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)

cluster_df["cluster"] = kmeans.fit_predict(X)

# 평균 누적관객 기준으로 ㉮, ㉯, ㉰ 부여
cluster_order = (
    cluster_df.groupby("cluster")["total_audi"]
    .mean()
    .sort_values(ascending=False)
    .index
)

cluster_name_map = {
    cluster_order[0]: "㉮",
    cluster_order[1]: "㉯",
    cluster_order[2]: "㉰",
}

cluster_df["cluster_name"] = cluster_df["cluster"].map(cluster_name_map)

# --------------------------
# 2차원 산점도
# --------------------------

st.divider()
st.subheader("📍 2차원 산점도")

col1, col2 = st.columns(2)

with col1:
    x_axis = st.selectbox("가로축", selected_labels, index=0)

with col2:
    y_axis = st.selectbox("세로축", selected_labels, index=1)

fig2d = px.scatter(
    cluster_df,
    x=feature_map[x_axis],
    y=feature_map[y_axis],
    color="cluster_name",
    hover_name="movieNm",
    color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
)

fig2d.update_traces(marker=dict(size=8))
fig2d.update_layout(legend_title="묶음")

st.plotly_chart(fig2d, use_container_width=True)

# --------------------------
# 3차원 산점도
# --------------------------

st.divider()
st.subheader("🌐 3차원 산점도")

if len(selected_labels) < 3:
    st.info("속성을 3개 이상 선택하면 3차원 산점도가 표시됩니다.")
else:
    c1, c2, c3 = st.columns(3)

    with c1:
        x3 = st.selectbox("X축", selected_labels, index=0, key="x3")

    with c2:
        y3 = st.selectbox("Y축", selected_labels, index=1, key="y3")

    with c3:
        z3 = st.selectbox("Z축", selected_labels, index=2, key="z3")

    fig3d = px.scatter_3d(
        cluster_df,
        x=feature_map[x3],
        y=feature_map[y3],
        z=feature_map[z3],
        color="cluster_name",
        hover_name="movieNm",
        color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )

    fig3d.update_traces(marker=dict(size=3))
    fig3d.update_layout(legend_title="묶음")

    st.plotly_chart(fig3d, use_container_width=True)

# --------------------------
# 묶음별 평균 표
# --------------------------

st.divider()
st.subheader("📊 묶음별 평균")

summary = (
    cluster_df.groupby("cluster_name")
    .agg(
        편수=("movieNm", "count"),
        스크린수=("first_scrn", "mean"),
        누적관객=("total_audi", "mean"),
        일수=("days_in_top10", "mean"),
        롱런지수=("longrun_index", "mean"),
    )
    .loc[["㉮", "㉯", "㉰"]]
)

summary = summary.round({
    "스크린수": 1,
    "누적관객": 1,
    "일수": 1,
    "롱런지수": 2,
})

st.dataframe(summary, use_container_width=True)

# --------------------------
# 묶음별 TOP5 영화
# --------------------------

st.divider()
st.subheader("🏆 묶음별 누적 관객 TOP5 영화")

for name in ["㉮", "㉯", "㉰"]:
    st.markdown(f"### {name}")

    top5 = (
        cluster_df[cluster_df["cluster_name"] == name]
        .sort_values("total_audi", ascending=False)
        [["movieNm", "total_audi"]]
        .head(5)
        .rename(
            columns={
                "movieNm": "영화 제목",
                "total_audi": "누적 관객 수"
            }
        )
    )

    st.dataframe(top5, use_container_width=True, hide_index=True)
