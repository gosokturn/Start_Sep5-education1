
import streamlit as st
import pandas as pd
import math
import plotly.express as px
import plotly.graph_objects as go

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

st.set_page_config(
    page_title="🎬 영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 유형 나누기")

URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

df = pd.read_csv(URL, encoding="utf-8")

total_movies = len(df)

numeric_cols = [
    "first_scrn",
    "total_audi",
    "days_in_top10",
    "first_week_audi"
]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ----------------------------
# 파생 변수 만들기
# ----------------------------

df["log_first_scrn"] = df["first_scrn"].apply(
    lambda x: math.log10(x) if pd.notna(x) and x > 0 else pd.NA
)

df["log_total_audi"] = df["total_audi"].apply(
    lambda x: math.log10(x) if pd.notna(x) and x > 0 else pd.NA
)

df["longrun_index"] = df["total_audi"] / df["first_week_audi"]
df.loc[df["first_week_audi"] <= 0, "longrun_index"] = pd.NA
df["longrun_index"] = df["longrun_index"].clip(upper=20)

feature_map = {
    "스크린 수(상용로그)": "log_first_scrn",
    "누적 관객(상용로그)": "log_total_audi",
    "10위권 일수": "days_in_top10",
    "롱런 지수": "longrun_index"
}

# ----------------------------
# 속성 선택
# ----------------------------

selected_labels = st.multiselect(
    "묶는 데 사용할 속성 선택",
    list(feature_map.keys()),
    default=list(feature_map.keys())
)

if len(selected_labels) < 2:
    st.warning("속성을 두 개 이상 선택하세요.")
    st.stop()

selected_features = [feature_map[x] for x in selected_labels]

# ----------------------------
# 묶음 수 선택
# ----------------------------

k = st.slider(
    "묶음 수(K)",
    min_value=2,
    max_value=7,
    value=3,
    step=1
)

cluster_df = df.dropna(subset=selected_features).copy()

clustered_movies = len(cluster_df)

st.write(
    f"**전체 영화:** {total_movies}편 | **묶은 영화:** {clustered_movies}편"
)

# ----------------------------
# 표준화
# ----------------------------

scaler = StandardScaler()
X = scaler.fit_transform(cluster_df[selected_features])

# ----------------------------
# KMeans
# ----------------------------

kmeans = KMeans(
    n_clusters=k,
    random_state=42,
    n_init=10
)

cluster_df["cluster"] = kmeans.fit_predict(X)

# 평균 누적관객 기준 정렬
cluster_order = (
    cluster_df.groupby("cluster")["total_audi"]
    .mean()
    .sort_values(ascending=False)
    .index
)

cluster_symbols = ["㉮", "㉯", "㉰", "㉱", "㉲", "㉳", "㉴"]

cluster_name_map = {
    cluster_order[i]: cluster_symbols[i]
    for i in range(k)
}

cluster_df["cluster_name"] = cluster_df["cluster"].map(cluster_name_map)

# ----------------------------
# 2차원 산점도
# ----------------------------

st.divider()
st.subheader("📍 2차원 산점도")

col1, col2 = st.columns(2)

with col1:
    x_label = st.selectbox(
        "가로축",
        selected_labels,
        index=0
    )

with col2:
    y_label = st.selectbox(
        "세로축",
        selected_labels,
        index=1
    )

fig2d = px.scatter(
    cluster_df,
    x=feature_map[x_label],
    y=feature_map[y_label],
    color="cluster_name",
    hover_name="movieNm"
)

fig2d.update_traces(marker=dict(size=8))
fig2d.update_layout(legend_title="묶음")

st.plotly_chart(fig2d, use_container_width=True)

# ----------------------------
# 3차원 산점도
# ----------------------------

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
        hover_name="movieNm"
    )

    fig3d.update_traces(marker=dict(size=3))
    fig3d.update_layout(legend_title="묶음")

    st.plotly_chart(fig3d, use_container_width=True)

# ----------------------------
# 묶음별 평균
# ----------------------------

st.divider()
st.subheader("📊 묶음별 평균")

summary = (
    cluster_df.groupby("cluster_name")
    .agg(
        편수=("movieNm", "count"),
        스크린수=("first_scrn", "mean"),
        누적관객=("total_audi", "mean"),
        일수=("days_in_top10", "mean"),
        롱런지수=("longrun_index", "mean")
    )
)

summary = summary.reindex(cluster_symbols[:k])

summary = summary.round({
    "스크린수": 1,
    "누적관객": 1,
    "일수": 1,
    "롱런지수": 2
})

st.dataframe(summary, use_container_width=True)

# ----------------------------
# TOP5 영화
# ----------------------------

st.divider()
st.subheader("🏆 묶음별 누적 관객 TOP5 영화")

for symbol in cluster_symbols[:k]:

    st.markdown(f"### {symbol}")

    top5 = (
        cluster_df[cluster_df["cluster_name"] == symbol]
        .sort_values("total_audi", ascending=False)
        [["movieNm", "total_audi"]]
        .head(5)
        .rename(columns={
            "movieNm": "영화 제목",
            "total_audi": "누적 관객 수"
        })
    )

    st.dataframe(
        top5,
        use_container_width=True,
        hide_index=True
    )

# ----------------------------
# 엘보우 그래프
# ----------------------------

st.divider()
st.subheader("📉 엘보우 그래프 (WCSS)")

wcss = []

for i in range(1, 8):

    model = KMeans(
        n_clusters=i,
        random_state=42,
        n_init=10
    )

    model.fit(X)

    wcss.append(model.inertia_)

elbow_df = pd.DataFrame({
    "묶음 수": list(range(1, 8)),
    "WCSS": wcss
})

fig_elbow = go.Figure()

fig_elbow.add_trace(
    go.Scatter(
        x=elbow_df["묶음 수"],
        y=elbow_df["WCSS"],
        mode="lines+markers",
        name="WCSS"
    )
)

fig_elbow.add_vline(
    x=k,
    line_color="red",
    line_dash="dash"
)

fig_elbow.update_layout(
    xaxis_title="묶음 수(K)",
    yaxis_title="WCSS",
    showlegend=False
)

st.plotly_chart(fig_elbow, use_container_width=True)

# ----------------------------
# WCSS 감소량 표
# ----------------------------

decrease = [""]

for i in range(1, len(wcss)):
    decrease.append(round(wcss[i - 1] - wcss[i], 2))

table = pd.DataFrame({
    "묶음 수": range(1, 8),
    "WCSS": [round(x, 2) for x in wcss],
    "앞 값보다 감소": decrease
})

st.dataframe(table, use_container_width=True)

# ----------------------------
# 실루엣 점수
# ----------------------------

st.divider()
st.subheader("✨ 실루엣 점수")

score = silhouette_score(X, cluster_df["cluster"])

st.metric(
    "현재 묶음 수의 실루엣 점수",
    f"{score:.3f}"
)

st.caption("실루엣 점수는 -1에서 1 사이이며, 1에 가까울수록 묶음이 더 뚜렷함을 의미합니다.")
