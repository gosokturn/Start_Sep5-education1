import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error,
)

st.set_page_config(page_title="영화 흥행 예측기", layout="wide")

st.title("🎬 영화 흥행 예측기 (다중 회귀)")

MOVIES_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
DAILY_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

@st.cache_data
def load_data():
    movies = pd.read_csv(MOVIES_URL, encoding="utf-8")
    daily = pd.read_csv(DAILY_URL, encoding="utf-8")
    return movies, daily

movies, daily = load_data()

daily["날짜"] = pd.to_datetime(daily["날짜"].astype(str), format="%Y%m%d")
start_date = daily["날짜"].min().date()
end_date = daily["날짜"].max().date()

st.subheader("📅 데이터 기준 기간")
st.write(f"**{start_date} ~ {end_date}**")

st.subheader("🎞 영화 정보 표 (맨 위 10줄)")
st.dataframe(movies.head(10), use_container_width=True)

movies = movies.sort_values("movieCd").reset_index(drop=True)

feature_candidates = {
    "first_scrn": "첫 관측일 스크린수",
    "first_show": "첫 관측일 상영횟수",
    "peak": "성수기 개봉 여부",
    "first_week_audi": "첫 주 관객 수",
    "days_in_top10": "TOP10 진입 일수",
    "genre": "장르",
    "nation": "국가",
}

st.subheader("✅ 사용할 변수 선택")

selected_features = []

cols = st.columns(2)

for i, (col, label) in enumerate(feature_candidates.items()):
    if cols[i % 2].checkbox(label, value=True):
        selected_features.append(col)

if len(selected_features) == 0:
    st.warning("최소 하나 이상의 변수를 선택하세요.")
    st.stop()

X = movies[selected_features].copy()
y = movies["total_audi"]

categorical = [c for c in ["genre", "nation"] if c in selected_features]

if categorical:
    X = pd.get_dummies(X, columns=categorical)

X = X.fillna(0)

test_mask = np.zeros(len(movies), dtype=bool)

for start in range(0, len(movies), 10):
    test_mask[start:start+3] = True

train_mask = ~test_mask

X_train = X[train_mask]
X_test = X[test_mask]

y_train = y[train_mask]
y_test = y[test_mask]

test_movies = movies[test_mask][["movieCd", "movieNm", "total_audi"]].copy()

model = LinearRegression()
model.fit(X_train, y_train)

pred = model.predict(X_test)
pred = np.maximum(pred, 0)

r2 = r2_score(y_test, pred)
mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))

st.subheader("📊 학습 정보")

c1, c2, c3 = st.columns(3)

c1.metric("학습 영화 수", len(X_train))
c2.metric("평가 영화 수", len(X_test))
c3.metric("사용 변수 수", len(selected_features))

st.write("**사용한 변수**")
st.write(", ".join([feature_candidates[f] for f in selected_features]))

st.subheader("📈 모델 평가")

m1, m2, m3 = st.columns(3)

m1.metric("R² 점수", f"{r2:.3f}")
m2.metric("MAE", f"{mae:,.0f} 명")
m3.metric("RMSE", f"{rmse:,.0f} 명")

result = test_movies.copy()
result["예측 총관객"] = pred.round().astype(int)
result["오차(명)"] = result["예측 총관객"] - result["total_audi"]
result["오차율(%)"] = (
    result["오차(명)"] / result["total_audi"] * 100
).round(2)

st.subheader("🎯 테스트 영화 예측 결과")

st.dataframe(
    result.rename(
        columns={
            "movieCd": "영화코드",
            "movieNm": "영화명",
            "total_audi": "실제 총관객",
        }
    ),
    use_container_width=True,
)

plot_y = result["예측 총관객"].clip(lower=1000)
small_pred = (result["예측 총관객"] < 1000).sum()

st.subheader("📉 실제 총관객 vs 예측 총관객")

st.write(f"예측값이 **1,000명보다 작은 영화: {small_pred}편**")

min_axis = max(1000, int(result["total_audi"].min()))
max_axis = int(
    max(result["total_audi"].max(), result["예측 총관객"].max())
)

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=result["total_audi"],
        y=plot_y,
        mode="markers",
        text=result["movieNm"],
        customdata=result["예측 총관객"],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "실제: %{x:,}명<br>"
            "예측: %{customdata:,}명<extra></extra>"
        ),
    )
)

fig.add_trace(
    go.Scatter(
        x=[min_axis, max_axis],
        y=[min_axis, max_axis],
        mode="lines",
        name="실제 = 예측",
        line=dict(dash="dash"),
    )
)

fig.update_layout(
    height=650,
    xaxis=dict(
        title="실제 총관객 수",
        type="log",
    ),
    yaxis=dict(
        title="예측 총관객 수",
        type="log",
    ),
    legend=dict(orientation="h"),
)

st.plotly_chart(fig, use_container_width=True)

coef = pd.DataFrame(
    {
        "변수": X.columns,
        "회귀계수": model.coef_,
    }
).sort_values("회귀계수", key=np.abs, ascending=False)

st.subheader("📌 회귀계수")

st.dataframe(coef, use_container_width=True)

st.caption("모든 영화(kobis_movies.csv)를 사용하며 movieCd 오름차순으로 정렬 후 매 10편마다 앞의 3편을 테스트용으로 분리하여 평가했습니다.")

st.info(
    """
    **안내**

    이 모델은 `kobis_movies.csv`에 사후 집계된 정보를 이용해 학습합니다.
    특히 `첫 주 관객 수(first_week_audi)`, `TOP10 진입 일수(days_in_top10)` 등은
    영화가 개봉한 이후에 알 수 있는 값입니다.

    따라서 이 결과는 **실제 개봉 전 흥행 예측 성능이 아니라,
    사후 집계 데이터를 이용한 회귀 모델의 예측 성능**입니다.
    """
)
