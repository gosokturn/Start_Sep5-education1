import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

st.set_page_config(page_title="영화 흥행 예측기", layout="wide")

MOVIES_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
DAILY_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

@st.cache_data
def load_data():
    movies = pd.read_csv(MOVIES_URL, encoding="utf-8")
    daily = pd.read_csv(DAILY_URL, encoding="utf-8")
    return movies, daily

movies, daily = load_data()

daily["날짜"] = pd.to_datetime(daily["날짜"].astype(str), format="%Y%m%d")
start_date = daily["날짜"].min().strftime("%Y-%m-%d")
end_date = daily["날짜"].max().strftime("%Y-%m-%d")

st.title("🎬 영화 흥행 예측기 (다중 회귀)")

st.write(f"**기준 기간:** {start_date} ~ {end_date}")

st.subheader("영화 정보 표(kobis_movies.csv) 맨 위 10줄")
st.dataframe(movies.head(10), use_container_width=True)

data = movies.copy()

data["openDt"] = pd.to_datetime(data["openDt"], errors="coerce")
data["open_year"] = data["openDt"].dt.year
data["open_month"] = data["openDt"].dt.month
data["open_day"] = data["openDt"].dt.day

feature_candidates = [
    "genre",
    "nation",
    "first_scrn",
    "first_show",
    "peak",
    "first_week_audi",
    "days_in_top10",
    "open_year",
    "open_month",
    "open_day",
]

st.sidebar.header("사용할 변수 선택")

selected_features = []
for col in feature_candidates:
    if st.sidebar.checkbox(col, value=True):
        selected_features.append(col)

if len(selected_features) == 0:
    st.warning("변수를 하나 이상 선택하세요.")
    st.stop()

data = data.sort_values("movieCd").reset_index(drop=True)

test_mask = np.zeros(len(data), dtype=bool)
for i in range(0, len(data), 10):
    test_mask[i:i+3] = True

train_df = data[~test_mask].copy()
test_df = data[test_mask].copy()

X_train = train_df[selected_features]
y_train = train_df["total_audi"]

X_test = test_df[selected_features]
y_test = test_df["total_audi"]

numeric_cols = X_train.select_dtypes(include=["number"]).columns.tolist()
categorical_cols = X_train.select_dtypes(exclude=["number"]).columns.tolist()

numeric_transformer = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="median"))
    ]
)

categorical_transformer = Pipeline(
    [
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore"))
    ]
)

preprocessor = ColumnTransformer(
    [
        ("num", numeric_transformer, numeric_cols),
        ("cat", categorical_transformer, categorical_cols),
    ]
)

model = Pipeline(
    [
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression()),
    ]
)

model.fit(X_train, y_train)

pred = model.predict(X_test)
pred = np.maximum(pred, 0)

r2 = r2_score(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
mae = mean_absolute_error(y_test, pred)
mape = np.mean(np.abs((y_test - pred) / y_test)) * 100

st.subheader("학습 정보")

col1, col2, col3 = st.columns(3)
col1.metric("학습 영화 수", len(train_df))
col2.metric("평가 영화 수", len(test_df))
col3.metric("사용 변수 수", len(selected_features))

st.subheader("평가 점수")

m1, m2, m3, m4 = st.columns(4)
m1.metric("R²", f"{r2:.3f}")
m2.metric("RMSE", f"{rmse:,.0f}")
m3.metric("MAE", f"{mae:,.0f}")
m4.metric("MAPE", f"{mape:.2f}%")

result = test_df[["movieCd", "movieNm"]].copy()
result["실제 총관객"] = y_test.values
result["예측 총관객"] = pred.astype(int)
result["오차"] = result["예측 총관객"] - result["실제 총관객"]
result["절대 오차"] = np.abs(result["오차"])
result["오차율(%)"] = (
    result["절대 오차"] / result["실제 총관객"] * 100
).round(2)

st.subheader("테스트 영화 예측 결과")
st.dataframe(result, use_container_width=True)

floor = 1000
pred_plot = pred.copy()
small_count = np.sum(pred_plot < floor)
pred_plot[pred_plot < floor] = floor

diag_min = max(floor, min(y_test.min(), pred_plot.min()))
diag_max = max(y_test.max(), pred_plot.max())

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=y_test,
        y=pred_plot,
        mode="markers",
        text=test_df["movieNm"],
        hovertemplate="<b>%{text}</b><br>실제: %{x:,}<br>예측: %{y:,}<extra></extra>",
        name="영화",
    )
)

fig.add_trace(
    go.Scatter(
        x=[diag_min, diag_max],
        y=[diag_min, diag_max],
        mode="lines",
        name="실제 = 예측",
    )
)

fig.update_layout(
    title="실제 총관객 vs 예측 총관객",
    xaxis_title="실제 총관객 수",
    yaxis_title="예측 총관객 수",
    height=650,
)

fig.update_xaxes(type="log")
fig.update_yaxes(type="log")

st.subheader("예측 산점도")
st.write(f"**예측값이 1,000명보다 작아 바닥에 표시된 영화 수:** {small_count}편")
st.plotly_chart(fig, use_container_width=True)

st.subheader("선택된 변수")
st.write(selected_features)
