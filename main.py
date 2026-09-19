import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="기온 예측기", page_icon="🌡️")

st.title("🌡️ 서울 기온 예측기")

URL = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(URL, encoding="utf-8")

    df.columns = ["날짜", "지점", "평균기온", "최저기온", "최고기온"]

    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year

    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df = df.dropna(subset=["평균기온"])

    df = df[df["연도"] <= 2025]

    count_df = df.groupby("연도").size().reset_index(name="관측일수")
    valid_years = count_df[count_df["관측일수"] >= 300]["연도"]

    yearly = (
        df[df["연도"].isin(valid_years)]
        .groupby("연도")["평균기온"]
        .mean()
        .reset_index()
    )

    yearly["지난연수"] = yearly["연도"] - 1908

    return yearly

yearly = load_data()

x = yearly["지난연수"].values
y = yearly["평균기온"].values

a, b = np.polyfit(x, y, 1)

yearly["회귀기온"] = a * yearly["지난연수"] + b

corr = np.corrcoef(yearly["연도"], yearly["평균기온"])[0, 1]

st.subheader("📊 데이터 정보")

col1, col2, col3 = st.columns(3)

col1.metric("사용한 연도 수", len(yearly))
col2.metric("시작 연도", int(yearly["연도"].min()))
col3.metric("끝 연도", int(yearly["연도"].max()))

st.metric("상관계수 (Pearson)", f"{corr:.4f}")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["평균기온"],
        mode="markers",
        name="연평균기온",
        marker=dict(size=8)
    )
)

fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["회귀기온"],
        mode="lines",
        name="회귀직선",
        line=dict(width=3)
    )
)

fig.update_layout(
    title="서울 연도별 평균기온과 회귀직선",
    xaxis_title="연도",
    yaxis_title="평균기온(℃)",
    height=550
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("🔮 미래 평균기온 예측")

year = st.slider("연도를 선택하세요.", 1900, 2100, 2025)

years_from_1908 = year - 1908
prediction = a * years_from_1908 + b

st.markdown("### 선택한 연도의 예상 평균기온")

st.markdown(
    f"""
    <div style="text-align:center;
                padding:20px;
                border-radius:15px;
                background:#EAF4FF;">
        <h1 style="font-size:56px; color:#1565C0;">{prediction:.2f} ℃</h1>
        <h2>{year}년</h2>
    </div>
    """,
    unsafe_allow_html=True
)

st.subheader("📐 회귀식")

st.write(f"평균기온 = {a:.5f} × (연도 - 1908) + {b:.5f}")

st.caption("회귀 직선은 1908년부터 지난 연수를 독립 변수로 하여 계산했습니다.")
