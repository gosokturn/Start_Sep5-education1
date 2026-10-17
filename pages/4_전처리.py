
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


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

MODEL_NAMES = {
    "probability": "확률 모델(로지스틱 회귀)",
    "question": "질문 모델(결정 트리)"
}


st.title("🧹 전처리 실험실")

st.write(
    "클래스 무게 조정과 BMI 결측값 처리 방법에 따라 "
    "뇌졸중 분류 결과가 어떻게 달라지는지 비교한다."
)

st.info(
    "이 페이지는 교육용 데이터 분석 실습이다. "
    "결과를 개인의 실제 건강 상태를 판단하는 의료 진단으로 사용하면 안 된다."
)


# --------------------------------------------------
# 1. 화면 맨 위의 세 가지 선택
# --------------------------------------------------

control_col1, control_col2, control_col3 = st.columns(
    [1, 1, 2]
)

with control_col1:
    balance_enabled = st.toggle(
        "클래스 무게 맞추기",
        value=False,
        help=(
            "켜면 마지막의 놓친 환자 목록에 무게 조정 모델을 사용한다. "
            "비교 표와 그래프에는 전후 결과가 항상 모두 표시된다."
        )
    )

with control_col2:
    bmi_missing_option = st.radio(
        "BMI가 비어 있는 사람",
        options=["유지", "삭제"],
        index=0,
        help=(
            "유지는 결측값을 입력 속성으로 사용할 때 훈련용 중앙값으로 채운다. "
            "삭제는 BMI가 비어 있는 행을 훈련용·채점용 데이터에서 제외한다."
        )
    )

with control_col3:
    selected_features = st.multiselect(
        "분류 모델에 입력할 항목",
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
    st.warning("입력 항목을 두 개 이상 선택해 줘.")
    st.stop()


# --------------------------------------------------
# 2. 데이터 읽기와 분할
#    채점표 페이지와 같은 id 정렬 및 10개 중 3개 채점 방식
# --------------------------------------------------

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
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "데이터에 필요한 열이 없습니다: "
        + ", ".join(missing_columns)
    )
    st.stop()


df = df.sort_values("id").reset_index(drop=True)
df = df.dropna(subset=["stroke"]).reset_index(drop=True)

if not df["stroke"].isin([0, 1]).all():
    st.error("stroke 열에는 0과 1만 있어야 합니다.")
    st.stop()

df["stroke"] = df["stroke"].astype(int)


# BMI 삭제 선택 시 삭제 대상과 실제 뇌졸중 환자 수를 먼저 계산한다.
bmi_missing_mask = df["bmi"].isna()
bmi_deleted_count = int(bmi_missing_mask.sum())
bmi_deleted_stroke_count = int(
    ((df["bmi"].isna()) & (df["stroke"] == 1)).sum()
)

# 채점표 페이지와 동일하게 정렬된 전체 데이터에서 먼저 분할한다.
test_mask = (np.arange(len(df)) % 10) < 3

train_df = df.loc[~test_mask].copy().reset_index(drop=True)
test_df = df.loc[test_mask].copy().reset_index(drop=True)


if bmi_missing_option == "삭제":
    train_df = train_df.dropna(subset=["bmi"]).reset_index(drop=True)
    test_df = test_df.dropna(subset=["bmi"]).reset_index(drop=True)

    st.info(
        f"BMI 결측값 삭제: 전체 {bmi_deleted_count:,}명 삭제, "
        f"그중 실제 뇌졸중 환자 {bmi_deleted_stroke_count:,}명"
    )
else:
    st.info(
        "BMI 결측값 유지: BMI를 입력 항목으로 선택한 경우 "
        "훈련용 데이터의 중앙값으로 빈 값을 채운다."
    )


if len(train_df) == 0 or len(test_df) == 0:
    st.error("훈련용 또는 채점용 데이터가 부족합니다.")
    st.stop()

if train_df["stroke"].nunique() < 2:
    st.error(
        "훈련용 데이터에 뇌졸중 양성과 음성 사례가 모두 있어야 합니다."
    )
    st.stop()

if test_df["stroke"].nunique() < 2:
    st.warning(
        "채점용 데이터에 양성 또는 음성 사례가 없을 수 있습니다. "
        "일부 평가 지표를 해석할 때 주의해 주세요."
    )


# --------------------------------------------------
# 3. 입력 데이터 전처리
#    결측값 대체 기준은 훈련용 데이터에서만 계산한다.
# --------------------------------------------------

X_train = train_df[selected_features].copy()
X_test = test_df[selected_features].copy()

y_train = train_df["stroke"].copy()
y_test = test_df["stroke"].copy()


for column in selected_features:
    if X_train[column].isna().any() or X_test[column].isna().any():
        median_value = X_train[column].median()

        if pd.isna(median_value):
            st.error(
                f"{FEATURE_LABELS[column]}의 훈련용 중앙값을 "
                "계산할 수 없습니다."
            )
            st.stop()

        X_train.loc[:, column] = X_train[column].fillna(median_value)
        X_test.loc[:, column] = X_test[column].fillna(median_value)


if X_train.isna().any().any() or X_test.isna().any().any():
    st.error("전처리 후에도 결측값이 남아 있습니다.")
    st.stop()


# --------------------------------------------------
# 4. 두 모델을 무게 조정 전후로 학습
# --------------------------------------------------

def train_models(class_weight):
    probability_model = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight=class_weight
        ))
    ])

    question_model = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=5,
        random_state=42,
        class_weight=class_weight
    )

    probability_model.fit(X_train, y_train)
    question_model.fit(X_train, y_train)

    return {
        "probability": probability_model,
        "question": question_model
    }


try:
    models_before = train_models(class_weight=None)
    models_after = train_models(class_weight="balanced")
except Exception as error:
    st.error("모델 학습 중 오류가 발생했습니다.")
    st.exception(error)
    st.stop()


predictions_before = {
    key: model.predict(X_test)
    for key, model in models_before.items()
}

predictions_after = {
    key: model.predict(X_test)
    for key, model in models_after.items()
}


# --------------------------------------------------
# 5. 혼동행렬과 평가 지표
# --------------------------------------------------

def confusion_counts(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    return {
        "TN": int(((y_true == 0) & (y_pred == 0)).sum()),
        "FP": int(((y_true == 0) & (y_pred == 1)).sum()),
        "FN": int(((y_true == 1) & (y_pred == 0)).sum()),
        "TP": int(((y_true == 1) & (y_pred == 1)).sum())
    }


def calculate_metrics(counts):
    tn = counts["TN"]
    fp = counts["FP"]
    fn = counts["FN"]
    tp = counts["TP"]

    total = tn + fp + fn + tp
    predicted_positive = tp + fp
    actual_positive = tp + fn
    f1_denominator = 2 * tp + fp + fn

    accuracy = (
        f"{(tp + tn) / total * 100:.2f}%"
        if total > 0
        else "계산할 수 없음"
    )

    precision = (
        f"{tp / predicted_positive * 100:.2f}%"
        if predicted_positive > 0
        else "계산할 수 없음"
    )

    recall = (
        f"{tp / actual_positive * 100:.2f}%"
        if actual_positive > 0
        else "계산할 수 없음"
    )

    f1 = (
        f"{2 * tp / f1_denominator * 100:.2f}%"
        if f1_denominator > 0
        else "계산할 수 없음"
    )

    return {
        "정확도": accuracy,
        "정밀도": precision,
        "재현율": recall,
        "F1": f1
    }


def make_matrix_table(counts):
    return pd.DataFrame(
        [
            [
                f"TN: {counts['TN']}명",
                f"FP: {counts['FP']}명"
            ],
            [
                f"FN: {counts['FN']}명",
                f"TP: {counts['TP']}명"
            ]
        ],
        index=[
            "실제 0 (뇌졸중 아님)",
            "실제 1 (뇌졸중)"
        ],
        columns=[
            "예측 0 (뇌졸중 아님)",
            "예측 1 (뇌졸중)"
        ]
    )


counts_before = {
    key: confusion_counts(y_test, predictions_before[key])
    for key in models_before
}

counts_after = {
    key: confusion_counts(y_test, predictions_after[key])
    for key in models_after
}


st.divider()
st.subheader("1. 데이터 분할 결과")

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric("훈련용 인원", f"{len(train_df):,}명")
metric_col2.metric("채점용 인원", f"{len(test_df):,}명")
metric_col3.metric(
    "채점용 실제 뇌졸중 환자",
    f"{int((y_test == 1).sum()):,}명"
)

st.caption(
    "전체 데이터를 id 순서로 정렬한 뒤, 10개 중 앞의 3개를 채점용으로 "
    "분리했다. BMI 삭제를 선택하면 분할 후 BMI 결측 행을 제외한다."
)


st.divider()
st.subheader("2. 혼동행렬과 지표 전후 비교")

st.write(
    "무게 조정 전은 기본 가중치로 학습한 모델이고, "
    "무게 조정 후는 `class_weight='balanced'`로 학습한 모델이다."
)

for model_key in ["probability", "question"]:
    st.markdown(f"### {MODEL_NAMES[model_key]}")

    before_col, after_col = st.columns(2)

    with before_col:
        st.markdown("#### 무게 조정 전")
        st.dataframe(
            make_matrix_table(counts_before[model_key]),
            use_container_width=True
        )

    with after_col:
        st.markdown("#### 무게 조정 후")
        st.dataframe(
            make_matrix_table(counts_after[model_key]),
            use_container_width=True
        )

    before_metrics = calculate_metrics(counts_before[model_key])
    after_metrics = calculate_metrics(counts_after[model_key])

    metrics_table = pd.DataFrame([
        {
            "평가 지표": "정확도",
            "무게 조정 전": before_metrics["정확도"],
            "무게 조정 후": after_metrics["정확도"]
        },
        {
            "평가 지표": "정밀도",
            "무게 조정 전": before_metrics["정밀도"],
            "무게 조정 후": after_metrics["정밀도"]
        },
        {
            "평가 지표": "재현율",
            "무게 조정 전": before_metrics["재현율"],
            "무게 조정 후": after_metrics["재현율"]
        },
        {
            "평가 지표": "F1",
            "무게 조정 전": before_metrics["F1"],
            "무게 조정 후": after_metrics["F1"]
        }
    ])

    st.dataframe(
        metrics_table,
        use_container_width=True,
        hide_index=True
    )

    before = counts_before[model_key]
    after = counts_after[model_key]

    found_before = before["TP"]
    found_after = after["TP"]
    missed_before = before["FN"]
    missed_after = after["FN"]
    false_before = before["FP"]
    false_after = after["FP"]

    st.markdown(
        f"**찾아낸 환자:** {found_before:,}명 → {found_after:,}명 · "
        f"**놓친 환자:** {missed_before:,}명 → {missed_after:,}명 · "
        f"**헛짚은 사람:** {false_before:,}명 → {false_after:,}명"
    )

    st.caption(
        "TN: 음성을 음성으로 예측 · FP: 음성을 양성으로 예측 · "
        "FN: 양성을 음성으로 예측 · TP: 양성을 양성으로 예측"
    )

    st.divider()


# --------------------------------------------------
# 6. 로지스틱 회귀의 0.5 확률 경계
# --------------------------------------------------

st.subheader("3. 산점도와 확률 0.5 경계")

st.write(
    "점 색은 실제 뇌졸중 여부를 뜻한다. 선이나 평면은 확률 모델의 "
    "예측 확률이 0.5가 되는 경계다. 무게 조정 전후의 경계를 "
    "서로 다른 색으로 표시한다."
)

if len(selected_features) >= 3:
    axis_col1, axis_col2, axis_col3 = st.columns(3)

    with axis_col1:
        x_axis = st.selectbox(
            "가로축",
            options=selected_features,
            index=0,
            format_func=lambda value: FEATURE_LABELS[value],
            key="preprocess_x_3d"
        )

    y_options = [
        feature for feature in selected_features
        if feature != x_axis
    ]

    with axis_col2:
        y_axis = st.selectbox(
            "세로축",
            options=y_options,
            index=0,
            format_func=lambda value: FEATURE_LABELS[value],
            key="preprocess_y_3d"
        )

    z_options = [
        feature for feature in selected_features
        if feature not in [x_axis, y_axis]
    ]

    with axis_col3:
        z_axis = st.selectbox(
            "깊이축",
            options=z_options,
            index=0,
            format_func=lambda value: FEATURE_LABELS[value],
            key="preprocess_z_3d"
        )
else:
    axis_col1, axis_col2 = st.columns(2)

    with axis_col1:
        x_axis = st.selectbox(
            "가로축",
            options=selected_features,
            index=0,
            format_func=lambda value: FEATURE_LABELS[value],
            key="preprocess_x_2d"
        )

    y_options = [
        feature for feature in selected_features
        if feature != x_axis
    ]

    with axis_col2:
        y_axis = st.selectbox(
            "세로축",
            options=y_options,
            index=0,
            format_func=lambda value: FEATURE_LABELS[value],
            key="preprocess_y_2d"
        )


def raw_logistic_coefficients(model, feature_names):
    scaler = model.named_steps["scaler"]
    classifier = model.named_steps["classifier"]

    coefficients = classifier.coef_[0] / scaler.scale_

    intercept = classifier.intercept_[0] - np.sum(
        classifier.coef_[0] * scaler.mean_ / scaler.scale_
    )

    return dict(zip(feature_names, coefficients)), float(intercept)


def make_ranges(values):
    low = float(np.nanmin(values))
    high = float(np.nanmax(values))

    if np.isclose(low, high):
        padding = max(abs(low) * 0.05, 0.5)
        return low - padding, high + padding

    padding = (high - low) * 0.04
    return low - padding, high + padding


def boundary_equation(model, axes):
    coefficients, intercept = raw_logistic_coefficients(
        model,
        selected_features
    )

    # 그래프 축으로 선택하지 않은 입력은 훈련용 중앙값에 고정한다.
    for feature in selected_features:
        if feature not in axes:
            intercept += (
                coefficients[feature]
                * float(X_train[feature].median())
            )

    axis_coefficients = [
        coefficients[axis]
        for axis in axes
    ]

    return axis_coefficients, intercept


def add_2d_boundary(fig, model, axes, color, label, x_range, y_range):
    coeffs, intercept = boundary_equation(model, axes)
    a, b = coeffs

    eps = 1e-10
    intersects = False

    if abs(b) > eps:
        x_values = np.linspace(x_range[0], x_range[1], 250)
        y_values = -(a * x_values + intercept) / b

        visible = (
            np.isfinite(y_values)
            & (y_values >= y_range[0])
            & (y_values <= y_range[1])
        )

        if visible.any():
            fig.add_trace(go.Scatter(
                x=x_values[visible],
                y=y_values[visible],
                mode="lines",
                name=label,
                line=dict(color=color, width=3)
            ))
            intersects = True

    elif abs(a) > eps:
        x_value = -intercept / a

        if x_range[0] <= x_value <= x_range[1]:
            fig.add_trace(go.Scatter(
                x=[x_value, x_value],
                y=[y_range[0], y_range[1]],
                mode="lines",
                name=label,
                line=dict(color=color, width=3)
            ))
            intersects = True

    return intersects


def add_3d_boundary(fig, model, axes, color, label, ranges):
    coeffs, intercept = boundary_equation(model, axes)
    a, b, c = coeffs

    corners = []

    for x_value in ranges[0]:
        for y_value in ranges[1]:
            for z_value in ranges[2]:
                corners.append(
                    a * x_value + b * y_value + c * z_value + intercept
                )

    # 경계 평면이 보이는 데이터 범위 안을 통과하는지 확인한다.
    if min(corners) > 0 or max(corners) < 0:
        return False

    coefficients = np.array([a, b, c], dtype=float)

    if np.all(np.abs(coefficients) < 1e-10):
        return False

    solve_axis = int(np.argmax(np.abs(coefficients)))
    grid_size = 25

    if solve_axis == 2 and abs(c) > 1e-10:
        x_grid = np.linspace(*ranges[0], grid_size)
        y_grid = np.linspace(*ranges[1], grid_size)
        xx, yy = np.meshgrid(x_grid, y_grid)
        zz = -(a * xx + b * yy + intercept) / c

    elif solve_axis == 1 and abs(b) > 1e-10:
        x_grid = np.linspace(*ranges[0], grid_size)
        z_grid = np.linspace(*ranges[2], grid_size)
        xx, zz = np.meshgrid(x_grid, z_grid)
        yy = -(a * xx + c * zz + intercept) / b

    elif abs(a) > 1e-10:
        y_grid = np.linspace(*ranges[1], grid_size)
        z_grid = np.linspace(*ranges[2], grid_size)
        yy, zz = np.meshgrid(y_grid, z_grid)
        xx = -(b * yy + c * zz + intercept) / a

    else:
        return False

    # 계산한 평면 중 표시 범위를 벗어난 부분은 숨긴다.
    in_range = (
        (xx >= ranges[0][0]) & (xx <= ranges[0][1])
        & (yy >= ranges[1][0]) & (yy <= ranges[1][1])
        & (zz >= ranges[2][0]) & (zz <= ranges[2][1])
    )

    zz_plot = np.where(in_range, zz, np.nan)

    fig.add_trace(go.Surface(
        x=xx,
        y=yy,
        z=zz_plot,
        name=label,
        showscale=False,
        opacity=0.38,
        colorscale=[[0, color], [1, color]],
        hovertemplate=(
            f"{label}<br>"
            f"{FEATURE_LABELS[axes[0]]}: %{{x:.2f}}<br>"
            f"{FEATURE_LABELS[axes[1]]}: %{{y:.2f}}<br>"
            f"{FEATURE_LABELS[axes[2]]}: %{{z:.2f}}"
            "<extra></extra>"
        )
    ))

    return True


plot_df = test_df[
    ["stroke"] + selected_features
].copy()

before_probability_model = models_before["probability"]
after_probability_model = models_after["probability"]

if len(selected_features) == 2:
    x_range = make_ranges(plot_df[x_axis])
    y_range = make_ranges(plot_df[y_axis])

    fig = go.Figure()

    for label, value, color in [
        ("실제 뇌졸중 아님", 0, "#2878B5"),
        ("실제 뇌졸중", 1, "#D94F4F")
    ]:
        group = plot_df[plot_df["stroke"] == value]

        fig.add_trace(go.Scatter(
            x=group[x_axis],
            y=group[y_axis],
            mode="markers",
            name=label,
            marker=dict(
                color=color,
                size=7,
                opacity=0.7
            ),
            customdata=group[["stroke"]].to_numpy(),
            hovertemplate=(
                f"{FEATURE_LABELS[x_axis]}: %{{x}}<br>"
                f"{FEATURE_LABELS[y_axis]}: %{{y}}<br>"
                f"실제 뇌졸중 여부: {value}"
                "<extra></extra>"
            )
        ))

    before_visible = add_2d_boundary(
        fig,
        before_probability_model,
        [x_axis, y_axis],
        "#E69500",
        "무게 조정 전: 확률 0.5",
        x_range,
        y_range
    )

    after_visible = add_2d_boundary(
        fig,
        after_probability_model,
        [x_axis, y_axis],
        "#8A4FFF",
        "무게 조정 후: 확률 0.5",
        x_range,
        y_range
    )

    fig.update_layout(
        title="실제 결과와 확률 0.5 경계선",
        xaxis_title=FEATURE_LABELS[x_axis],
        yaxis_title=FEATURE_LABELS[y_axis],
        legend_title="실제 결과",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    if not before_visible:
        st.write(
            "무게 조정 전 경계선은 현재 그림의 범위 밖에 있거나 "
            "표시할 수 있는 선 형태가 아니다."
        )

    if not after_visible:
        st.write(
            "무게 조정 후 경계선은 현재 그림의 범위 밖에 있거나 "
            "표시할 수 있는 선 형태가 아니다."
        )

    if len(selected_features) > 2:
        st.caption(
            "경계선 계산에서는 그래프의 두 축 이외 입력 항목을 "
            "훈련용 데이터의 중앙값으로 고정한다."
        )

else:
    axes = [x_axis, y_axis, z_axis]

    ranges = [
        make_ranges(plot_df[axis])
        for axis in axes
    ]

    fig = go.Figure()

    for label, value, color in [
        ("실제 뇌졸중 아님", 0, "#2878B5"),
        ("실제 뇌졸중", 1, "#D94F4F")
    ]:
        group = plot_df[plot_df["stroke"] == value]

        fig.add_trace(go.Scatter3d(
            x=group[x_axis],
            y=group[y_axis],
            z=group[z_axis],
            mode="markers",
            name=label,
            marker=dict(
                color=color,
                size=4,
                opacity=0.7
            ),
            hovertemplate=(
                f"{FEATURE_LABELS[x_axis]}: %{{x}}<br>"
                f"{FEATURE_LABELS[y_axis]}: %{{y}}<br>"
                f"{FEATURE_LABELS[z_axis]}: %{{z}}<br>"
                f"실제 뇌졸중 여부: {value}"
                "<extra></extra>"
            )
        ))

    before_visible = add_3d_boundary(
        fig,
        before_probability_model,
        axes,
        "#E69500",
        "무게 조정 전: 확률 0.5",
        ranges
    )

    after_visible = add_3d_boundary(
        fig,
        after_probability_model,
        axes,
        "#8A4FFF",
        "무게 조정 후: 확률 0.5",
        ranges
    )

    fig.update_layout(
        title="실제 결과와 확률 0.5 경계 평면",
        scene=dict(
            xaxis_title=FEATURE_LABELS[x_axis],
            yaxis_title=FEATURE_LABELS[y_axis],
            zaxis_title=FEATURE_LABELS[z_axis]
        ),
        height=700,
        legend_title="실제 결과"
    )

    st.plotly_chart(fig, use_container_width=True)

    if not before_visible:
        st.write(
            "무게 조정 전 경계 평면은 현재 그림의 범위 안에 "
            "나타나지 않습니다."
        )

    if not after_visible:
        st.write(
            "무게 조정 후 경계 평면은 현재 그림의 범위 안에 "
            "나타나지 않습니다."
        )

    st.caption(
        "입력 항목을 4개 이상 골랐다면 그래프의 세 축에 선택한 "
        "세 항목만 사용한다. 나머지 항목은 훈련용 중앙값으로 고정한다. "
        "그래프를 마우스로 드래그해 회전할 수 있다."
    )


# --------------------------------------------------
# 7. 확률 모델이 놓친 환자 목록
# --------------------------------------------------

st.divider()
st.subheader("4. 확률 모델이 놓친 환자")

if balance_enabled:
    selected_predictions = predictions_after["probability"]
    selected_counts = counts_after["probability"]
    list_label = "무게 조정 후"
else:
    selected_predictions = predictions_before["probability"]
    selected_counts = counts_before["probability"]
    list_label = "무게 조정 전"


st.write(
    f"현재 무게 조정 스위치가 "
    f"{'켜져 있어' if balance_enabled else '꺼져 있어'} "
    f"**{list_label} 모델**의 결과를 표시한다."
)

missed_df = test_df[
    ["id", "age", "hypertension", "heart_disease", "stroke"]
].copy()

missed_df["prediction"] = selected_predictions

missed_df = missed_df[
    (missed_df["stroke"] == 1)
    & (missed_df["prediction"] == 0)
].copy()

missed_df = missed_df.sort_values(
    "age",
    ascending=True
).reset_index(drop=True)

display_df = missed_df[
    ["id", "age", "hypertension", "heart_disease"]
].copy()

display_df.columns = [
    "번호",
    "나이",
    "고혈압 여부",
    "심장병 여부"
]

display_df["고혈압 여부"] = display_df["고혈압 여부"].map({
    0: "없음",
    1: "있음"
}).fillna("알 수 없음")

display_df["심장병 여부"] = display_df["심장병 여부"].map({
    0: "없음",
    1: "있음"
}).fillna("알 수 없음")


st.markdown(
    f"**놓친 환자 수: {len(display_df):,}명**"
)

if len(display_df) == 0:
    st.success("이 모델이 놓친 환자가 없습니다.")
else:
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


st.caption(
    f"확인: 목록 {len(display_df):,}명 · "
    f"혼동행렬 FN {selected_counts['FN']:,}명. "
    "두 수는 같아야 한다. 목록은 나이가 적은 순서로 정렬했다."
)
