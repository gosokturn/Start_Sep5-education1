
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import accuracy_score


DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"

FEATURES = [
    "age",
    "avg_glucose_level",
    "bmi",
    "hypertension",
    "heart_disease"
]

FEATURE_LABELS = {
    "age": "나이",
    "avg_glucose_level": "평균 혈당",
    "bmi": "체질량지수(BMI)",
    "hypertension": "고혈압",
    "heart_disease": "심장병"
}

st.title("🤖 뇌졸중 분류 모델")
st.write(
    "선택한 속성을 이용해 뇌졸중 여부를 예측하고, "
    "확률 모델과 질문 모델의 결과를 비교한다."
)

st.info(
    "stroke가 1이면 뇌졸중(양성), 0이면 뇌졸중 아님(음성)이다. "
    "이 실습은 교육용이며 의료 진단에 사용할 수 없다."
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


try:
    df = load_data()
except Exception as error:
    st.error("데이터를 불러오지 못했습니다.")
    st.exception(error)
    st.stop()


required_columns = ["id", "stroke"] + FEATURES
missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "데이터에 필요한 열이 없습니다: "
        + ", ".join(missing_columns)
    )
    st.stop()


st.subheader("1. 입력 속성 선택")

selected_features = st.multiselect(
    "모델이 사용할 속성을 선택해 줘.",
    options=FEATURES,
    default=[
        "age",
        "avg_glucose_level",
        "hypertension",
        "heart_disease"
    ],
    format_func=lambda value: FEATURE_LABELS[value]
)

if len(selected_features) < 2:
    st.warning("입력 속성을 두 개 이상 선택해야 모델을 학습할 수 있어.")
    st.stop()


st.caption(
    "데이터는 id 오름차순으로 정렬한다. "
    "10명마다 앞의 3명은 채점용, 나머지 7명은 훈련용으로 고정한다."
)

# 번호 순으로 정렬한 뒤, 10명마다 앞의 3명을 채점용으로 지정한다.
df = df.sort_values("id").reset_index(drop=True)

# 목표값이 비어 있는 행은 사용할 수 없으므로 제외한다.
df = df.dropna(subset=["stroke"]).reset_index(drop=True)

df["stroke"] = df["stroke"].astype(int)

if not set(df["stroke"].unique()).issubset({0, 1}):
    st.error("stroke 열에는 0과 1만 있어야 해.")
    st.stop()

test_mask = (np.arange(len(df)) % 10) < 3

train_df = df.loc[~test_mask].copy().reset_index(drop=True)
test_df = df.loc[test_mask].copy().reset_index(drop=True)

if len(train_df) == 0 or len(test_df) == 0:
    st.error("훈련용 또는 채점용 데이터가 부족해.")
    st.stop()

if train_df["stroke"].nunique() < 2:
    st.error("훈련용 데이터에 양성과 음성 두 클래스가 모두 있어야 해.")
    st.stop()

# 선택한 속성만 사용한다.
X_train = train_df[selected_features].copy()
X_test = test_df[selected_features].copy()

y_train = train_df["stroke"].copy()
y_test = test_df["stroke"].copy()

# BMI를 선택한 경우에만 훈련용 BMI 중앙값으로 결측값을 채운다.
if "bmi" in selected_features:
    bmi_median = X_train["bmi"].median()

    if pd.isna(bmi_median):
        st.error("훈련용 데이터에서 BMI 중앙값을 계산할 수 없어.")
        st.stop()

    X_train.loc[:, "bmi"] = X_train["bmi"].fillna(bmi_median)
    X_test.loc[:, "bmi"] = X_test["bmi"].fillna(bmi_median)

# 선택한 속성에 BMI 외 결측값이 있다면 훈련용 중앙값으로 처리한다.
# 각 열의 중앙값은 훈련용 데이터에서만 계산한다.
for column in selected_features:
    if X_train[column].isna().any() or X_test[column].isna().any():
        median_value = X_train[column].median()

        if pd.isna(median_value):
            st.error(
                f"{FEATURE_LABELS[column]} 열의 훈련용 중앙값을 "
                "계산할 수 없어."
            )
            st.stop()

        X_train.loc[:, column] = X_train[column].fillna(median_value)
        X_test.loc[:, column] = X_test[column].fillna(median_value)

st.divider()

st.subheader("2. 데이터 분리 결과")

data_col1, data_col2, data_col3 = st.columns(3)

data_col1.metric("전체 사용 데이터", f"{len(df):,}명")
data_col2.metric("훈련용 데이터", f"{len(train_df):,}명")
data_col3.metric("채점용 데이터", f"{len(test_df):,}명")

with st.expander("훈련용과 채점용 데이터 확인"):
    st.write("훈련용 데이터의 앞 5명")
    st.dataframe(
        train_df[["id"] + selected_features + ["stroke"]].head(),
        use_container_width=True,
        hide_index=True
    )

    st.write("채점용 데이터의 앞 5명")
    st.dataframe(
        test_df[["id"] + selected_features + ["stroke"]].head(),
        use_container_width=True,
        hide_index=True
    )

st.divider()

st.subheader("3. 세 가지 모델 학습")

# 모델 1: 표준화와 로지스틱 회귀를 훈련용 데이터로만 학습한다.
probability_model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        max_iter=1000,
        random_state=42
    ))
])

probability_model.fit(X_train, y_train)
probability_predictions = probability_model.predict(X_test)

# 모델 2: 질문을 최대 세 단계까지 하고,
# 리프 노드에 최소 5명의 훈련용 데이터가 있도록 제한한다.
question_model = DecisionTreeClassifier(
    max_depth=3,
    min_samples_leaf=5,
    random_state=42
)

question_model.fit(X_train, y_train)
question_predictions = question_model.predict(X_test)

# 모델 3: 입력 속성을 보지 않고 훈련용에서 다수인 클래스를 예측한다.
majority_class = int(y_train.value_counts().idxmax())
baseline_predictions = np.full(len(y_test), majority_class)

probability_accuracy = accuracy_score(
    y_test, probability_predictions
)
question_accuracy = accuracy_score(
    y_test, question_predictions
)
baseline_accuracy = accuracy_score(
    y_test, baseline_predictions
)

st.markdown("### 채점용 데이터 정확도")

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "확률 모델",
    f"{probability_accuracy * 100:.2f}%"
)

metric2.metric(
    "질문 모델",
    f"{question_accuracy * 100:.2f}%"
)

metric3.metric(
    "입력 없는 기준 모델",
    f"{baseline_accuracy * 100:.2f}%"
)

st.caption(
    f"기준 모델은 훈련용 데이터에서 더 많은 클래스인 "
    f"{'뇌졸중(양성)' if majority_class == 1 else '뇌졸중 아님(음성)'}"
    "만 항상 예측한다."
)

comparison = pd.DataFrame({
    "모델": [
        "확률 모델(로지스틱 회귀)",
        "질문 모델(결정 트리)",
        "입력 없는 기준 모델"
    ],
    "정확도 (%)": [
        round(probability_accuracy * 100, 2),
        round(question_accuracy * 100, 2),
        round(baseline_accuracy * 100, 2)
    ]
})

st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "정확도는 전체 채점용 사람 중 예측과 실제 결과가 일치한 비율이다. "
    "양성 데이터가 적으면 정확도만으로 모델을 판단하기 어려울 수 있다."
)

st.divider()

st.subheader("4. 질문 모델은 어떤 순서로 질문할까?")

tree_rules = export_text(
    question_model,
    feature_names=[
        FEATURE_LABELS[feature]
        for feature in selected_features
    ],
    max_depth=3,
    decimals=2
)

st.code(tree_rules, language="text")

st.caption(
    "각 분기 조건은 훈련용 데이터에서 학습한 것이다. "
    "질문은 최대 3단계까지 가능하며, 각 마지막 마디에는 "
    "최소 5명의 훈련용 데이터가 남도록 제한했다."
)

st.divider()

st.subheader("5. 두 속성으로 보는 채점용 데이터")

st.write(
    "가로축과 세로축을 선택하면 채점용 사람들의 실제 결과를 표시한다. "
    "배경은 질문 모델의 분할 영역이고, 선은 선택한 두 속성만으로 "
    "새로 학습한 확률 모델의 0.5 경계선이다."
)

axis_col1, axis_col2 = st.columns(2)

with axis_col1:
    x_feature = st.selectbox(
        "가로축",
        options=selected_features,
        index=0,
        format_func=lambda value: FEATURE_LABELS[value]
    )

y_candidates = [
    feature for feature in selected_features
    if feature != x_feature
]

default_y_index = 0

if len(y_candidates) > 1:
    default_y_index = 0

with axis_col2:
    y_feature = st.selectbox(
        "세로축",
        options=y_candidates,
        index=default_y_index,
        format_func=lambda value: FEATURE_LABELS[value]
    )

# 선택한 두 축만 사용해 확률 모델을 새로 학습한다.
two_axis_features = [x_feature, y_feature]

X_train_2d = X_train[two_axis_features].copy()
X_test_2d = X_test[two_axis_features].copy()

two_axis_model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        max_iter=1000,
        random_state=42
    ))
])

two_axis_model.fit(X_train_2d, y_train)

# 두 축의 범위를 만든다.
x_min = float(df[x_feature].min())
x_max = float(df[x_feature].max())
y_min = float(df[y_feature].min())
y_max = float(df[y_feature].max())

x_padding = (x_max - x_min) * 0.05
y_padding = (y_max - y_min) * 0.05

if x_padding == 0:
    x_padding = 1.0
if y_padding == 0:
    y_padding = 1.0

x_min -= x_padding
x_max += x_padding
y_min -= y_padding
y_max += y_padding

x_grid = np.linspace(x_min, x_max, 100)
y_grid = np.linspace(y_min, y_max, 100)
xx, yy = np.meshgrid(x_grid, y_grid)

# 질문 모델의 다른 입력 속성은 훈련용 중앙값에 고정한다.
# 선택한 두 축만 격자에서 변화시켜 결정 트리 영역을 확인한다.
grid_data = {}

for feature in selected_features:
    grid_data[feature] = np.full(
        xx.size,
        float(X_train[feature].median())
    )

grid_data[x_feature] = xx.ravel()
grid_data[y_feature] = yy.ravel()

grid_df = pd.DataFrame(
    grid_data,
    columns=selected_features
)

tree_region = question_model.predict(grid_df).reshape(xx.shape)

fig = go.Figure()

# 결정 트리의 예측 영역을 옅은 색으로 표시한다.
fig.add_trace(go.Heatmap(
    x=x_grid,
    y=y_grid,
    z=tree_region,
    colorscale=[
        [0.0, "rgba(76, 120, 168, 0.18)"],
        [0.499, "rgba(76, 120, 168, 0.18)"],
        [0.5, "rgba(228, 87, 86, 0.18)"],
        [1.0, "rgba(228, 87, 86, 0.18)"]
    ],
    zmin=0,
    zmax=1,
    showscale=False,
    hoverinfo="skip",
    name="질문 모델 분할 영역"
))

# 확률 모델의 0.5 경계선을 계산한다.
grid_points = pd.DataFrame({
    x_feature: xx.ravel(),
    y_feature: yy.ravel()
})

grid_probabilities = two_axis_model.predict_proba(grid_points)
positive_index = list(
    two_axis_model.named_steps["classifier"].classes_
).index(1)

probability_grid = grid_probabilities[
    :, positive_index
].reshape(xx.shape)

# 0.5 경계선은 확률이 0.5인 지점이다.
fig.add_trace(go.Contour(
    x=x_grid,
    y=y_grid,
    z=probability_grid,
    contours=dict(
        start=0.5,
        end=0.5,
        size=1,
        coloring="lines"
    ),
    line=dict(color="#222222", width=3),
    showscale=False,
    hoverinfo="skip",
    name="확률 0.5 경계선"
))

# 채점용 사람들을 실제 결과에 따라 나누어 표시한다.
test_plot = test_df.copy()
test_plot["실제 결과"] = test_plot["stroke"].map({
    0: "뇌졸중 아님 (0)",
    1: "뇌졸중 (1)"
})

for stroke_value, label, color in [
    (0, "뇌졸중 아님 (0)", "#4C78A8"),
    (1, "뇌졸중 (1)", "#E45756")
]:
    subset = test_plot[test_plot["stroke"] == stroke_value]

    fig.add_trace(go.Scatter(
        x=subset[x_feature],
        y=subset[y_feature],
        mode="markers",
        name=label,
        marker=dict(
            size=9,
            color=color,
            line=dict(color="white", width=1)
        ),
        customdata=np.column_stack([
            subset["id"].astype(str),
            subset["stroke"].astype(str)
        ]),
        hovertemplate=(
            "번호: %{customdata[0]}<br>"
            + FEATURE_LABELS[x_feature] + ": %{x}<br>"
            + FEATURE_LABELS[y_feature] + ": %{y}<br>"
            + "실제 stroke: %{customdata[1]}"
            + "<extra></extra>"
        )
    ))

fig.update_layout(
    title="채점용 데이터와 두 모델의 경계",
    xaxis_title=FEATURE_LABELS[x_feature],
    yaxis_title=FEATURE_LABELS[y_feature],
    legend_title="실제 결과",
    template="plotly_white",
    height=650
)

st.plotly_chart(fig, use_container_width=True)

# 확률 0.5 경계선이 표시 범위 안에 있는지 확인한다.
corner_points = pd.DataFrame({
    x_feature: [x_min, x_min, x_max, x_max],
    y_feature: [y_min, y_max, y_min, y_max]
})

corner_probabilities = two_axis_model.predict_proba(corner_points)[
    :, positive_index
]

boundary_inside = (
    float(corner_probabilities.min()) <= 0.5
    and float(corner_probabilities.max()) >= 0.5
)

if boundary_inside:
    st.success(
        "확률 모델의 0.5 경계선이 현재 그림의 표시 범위 안에 있다."
    )
else:
    st.warning(
        "확률 모델의 0.5 경계선이 현재 그림의 표시 범위 밖에 있다. "
        "현재 축 범위에서는 경계선이 보이지 않는다."
    )

st.caption(
    "배경 영역은 질문 모델에 두 축의 값만 바꾸어 넣고, "
    "나머지 선택 속성은 훈련용 중앙값으로 고정해 계산한 결과다. "
    "따라서 실제 다섯 속성 전체를 사용하는 질문 모델의 모든 분할을 "
    "2차원 그림에 그대로 표현한 것은 아니다."
)

st.divider()

st.subheader("6. 채점용 사람의 예측 결과")

result_table = test_df[["id"] + selected_features + ["stroke"]].copy()
result_table["실제 결과"] = result_table["stroke"].map({
    0: "뇌졸중 아님",
    1: "뇌졸중"
})
result_table["확률 모델 예측"] = pd.Series(
    probability_predictions
).map({
    0: "뇌졸중 아님",
    1: "뇌졸중"
})
result_table["질문 모델 예측"] = pd.Series(
    question_predictions
).map({
    0: "뇌졸중 아님",
    1: "뇌졸중"
})
result_table["기준 모델 예측"] = pd.Series(
    baseline_predictions
).map({
    0: "뇌졸중 아님",
    1: "뇌졸중"
})

result_table = result_table.drop(columns=["stroke"])

st.dataframe(
    result_table,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "채점용 데이터는 모델 학습이나 표준화에 사용하지 않았다. "
    "다만 모델의 성능은 데이터 분리 방식과 표본 구성에 따라 달라질 수 있다."
)
