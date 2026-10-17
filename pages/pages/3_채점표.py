
import streamlit as st
import pandas as pd
import numpy as np

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
    "question": "질문 모델(결정 트리)",
    "baseline": "훈련용 다수 클래스 기준 모델"
}

st.title("📋 모델 채점표")

st.write(
    "채점용 데이터의 실제 결과와 모델의 예측 결과를 비교한다. "
    "혼동행렬, 정확도, 정밀도, 재현율, F1 점수를 확인할 수 있다."
)

st.info(
    "stroke가 1이면 뇌졸중(양성), 0이면 뇌졸중 아님(음성)이다. "
    "이 결과는 교육용 분석이며 의료 진단에 사용할 수 없다."
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


def make_confusion_values(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tp = int(((y_true == 1) & (y_pred == 1)).sum())

    return {
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "TP": tp
    }


def make_confusion_table(counts):
    tn = counts["TN"]
    fp = counts["FP"]
    fn = counts["FN"]
    tp = counts["TP"]

    actual_0_total = tn + fp
    actual_1_total = fn + tp
    predicted_0_total = tn + fn
    predicted_1_total = fp + tp
    total = tn + fp + fn + tp

    return pd.DataFrame(
        [
            [
                f"TN: {tn}명",
                f"FP: {fp}명",
                f"{actual_0_total}명"
            ],
            [
                f"FN: {fn}명",
                f"TP: {tp}명",
                f"{actual_1_total}명"
            ],
            [
                f"{predicted_0_total}명",
                f"{predicted_1_total}명",
                f"{total}명"
            ]
        ],
        index=[
            "실제 0 (뇌졸중 아님)",
            "실제 1 (뇌졸중)",
            "열 합계"
        ],
        columns=[
            "예측 0 (뇌졸중 아님)",
            "예측 1 (뇌졸중)",
            "행 합계"
        ]
    )


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
        (tp + tn) / total
        if total > 0
        else np.nan
    )

    if predicted_positive == 0:
        precision = "계산할 수 없음"
    else:
        precision = f"{tp / predicted_positive * 100:.2f}%"

    recall = (
        f"{tp / actual_positive * 100:.2f}%"
        if actual_positive > 0
        else "계산할 수 없음"
    )

    # F1은 정밀도와 별도로 공식에 직접 대입해 계산한다.
    # 분모가 0인 경우에만 계산할 수 없는 값으로 표시한다.
    if f1_denominator == 0:
        f1 = "계산할 수 없음"
    else:
        f1 = f"{2 * tp / f1_denominator * 100:.2f}%"

    return {
        "정확도": (
            f"{accuracy * 100:.2f}%"
            if not np.isnan(accuracy)
            else "계산할 수 없음"
        ),
        "정밀도": precision,
        "재현율": recall,
        "F1": f1
    }


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
    "분류 모델에서 사용할 속성을 선택해 줘.",
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
    st.warning("입력 속성을 두 개 이상 선택해야 채점할 수 있어.")
    st.stop()


# 분류 모델 페이지와 동일한 순서 및 분리 방법
df = df.sort_values("id").reset_index(drop=True)
df = df.dropna(subset=["stroke"]).reset_index(drop=True)

if not df["stroke"].isin([0, 1]).all():
    st.error("stroke 열에는 0과 1만 있어야 해.")
    st.stop()

df["stroke"] = df["stroke"].astype(int)

test_mask = (np.arange(len(df)) % 10) < 3

train_df = df.loc[~test_mask].copy().reset_index(drop=True)
test_df = df.loc[test_mask].copy().reset_index(drop=True)

if len(train_df) == 0 or len(test_df) == 0:
    st.error("훈련용 또는 채점용 데이터가 부족해.")
    st.stop()

if train_df["stroke"].nunique() < 2:
    st.error("훈련용 데이터에 양성과 음성 두 클래스가 모두 있어야 해.")
    st.stop()


X_train = train_df[selected_features].copy()
X_test = test_df[selected_features].copy()

y_train = train_df["stroke"].copy()
y_test = test_df["stroke"].copy()


# BMI는 선택했을 때만 훈련용 중앙값으로 결측값을 채운다.
if "bmi" in selected_features:
    bmi_median = X_train["bmi"].median()

    if pd.isna(bmi_median):
        st.error("훈련용 데이터에서 BMI 중앙값을 계산할 수 없어.")
        st.stop()

    X_train.loc[:, "bmi"] = X_train["bmi"].fillna(bmi_median)
    X_test.loc[:, "bmi"] = X_test["bmi"].fillna(bmi_median)


# 선택한 속성의 결측값이 있다면 훈련용 중앙값만 이용한다.
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


# 모델 1: 로지스틱 회귀
probability_model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        max_iter=1000,
        random_state=42
    ))
])

probability_model.fit(X_train, y_train)
probability_predictions = probability_model.predict(X_test)


# 모델 2: 결정 트리
question_model = DecisionTreeClassifier(
    max_depth=3,
    min_samples_leaf=5,
    random_state=42
)

question_model.fit(X_train, y_train)
question_predictions = question_model.predict(X_test)


# 기준 모델: 훈련용 데이터에서 다수인 클래스만 예측
majority_class = int(y_train.value_counts().idxmax())
baseline_predictions = np.full(len(y_test), majority_class)


predictions_by_model = {
    "probability": probability_predictions,
    "question": question_predictions,
    "baseline": baseline_predictions
}

counts_by_model = {
    model_key: make_confusion_values(y_test, predictions)
    for model_key, predictions in predictions_by_model.items()
}


st.divider()
st.subheader("2. 채점용 데이터")

test_people = len(test_df)
actual_positive_people = int((y_test == 1).sum())

st.markdown(
    f"**채점용 사람 수: {test_people:,}명 · "
    f"그중 실제 뇌졸중인 사람 수: {actual_positive_people:,}명**"
)


st.divider()
st.subheader("3. 혼동행렬 비교")

st.write(
    "행은 실제 결과, 열은 예측 결과다. "
    "네 칸에는 약자와 사람 수를 표시하고, 오른쪽과 아래쪽에는 합계를 표시한다."
)

matrix_col1, matrix_col2 = st.columns(2)

with matrix_col1:
    st.markdown("#### 확률 모델")
    st.dataframe(
        make_confusion_table(counts_by_model["probability"]),
        use_container_width=True
    )

with matrix_col2:
    st.markdown("#### 질문 모델")
    st.dataframe(
        make_confusion_table(counts_by_model["question"]),
        use_container_width=True
    )

st.caption(
    "TN: 실제 음성을 음성으로 예측 · "
    "FP: 실제 음성을 양성으로 예측 · "
    "FN: 실제 양성을 음성으로 예측 · "
    "TP: 실제 양성을 양성으로 예측"
)


st.markdown("#### 기준 모델")
st.dataframe(
    make_confusion_table(counts_by_model["baseline"]),
    use_container_width=True
)

st.divider()
st.subheader("4. 평가 지표 비교")

st.write(
    "정확도는 전체 중 맞힌 비율, 정밀도는 양성이라고 예측한 사람 중 "
    "실제 양성인 비율, 재현율은 실제 양성 중 찾아낸 비율이다. "
    "F1은 TP, FP, FN을 이용한 공식으로 직접 계산한다."
)

metric_rows = []

for model_key in ["probability", "question", "baseline"]:
    metrics = calculate_metrics(counts_by_model[model_key])

    metric_rows.append({
        "모델": MODEL_NAMES[model_key],
        "정확도": metrics["정확도"],
        "정밀도": metrics["정밀도"],
        "재현율": metrics["재현율"],
        "F1": metrics["F1"]
    })

metric_table = pd.DataFrame(metric_rows)

st.dataframe(
    metric_table,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "양성 예측이 0명이면 정밀도는 계산할 수 없다고 표시한다. "
    "이 경우에도 F1은 2×TP ÷ (2×TP + FP + FN) 공식으로 계산한다."
)


st.divider()
st.subheader("5. 놓친 환자와 헛짚은 사람")

st.write(
    "비교할 모델을 선택하면 왼쪽에는 실제 뇌졸중인데 음성으로 예측한 사람(FN), "
    "오른쪽에는 실제 뇌졸중이 아닌데 양성으로 예측한 사람(FP)을 표시한다."
)

selected_model_key = st.selectbox(
    "목록을 확인할 모델",
    options=["probability", "question", "baseline"],
    format_func=lambda key: MODEL_NAMES[key]
)

selected_predictions = predictions_by_model[selected_model_key]

mistakes_df = test_df[
    ["id", "age", "avg_glucose_level", "hypertension", "heart_disease", "stroke"]
].copy()

mistakes_df["예측"] = selected_predictions

# FN: 실제 1, 예측 0
missed_people = mistakes_df[
    (mistakes_df["stroke"] == 1)
    & (mistakes_df["예측"] == 0)
].copy()

# FP: 실제 0, 예측 1
false_alarm_people = mistakes_df[
    (mistakes_df["stroke"] == 0)
    & (mistakes_df["예측"] == 1)
].copy()

missed_people = missed_people.sort_values(
    "age",
    ascending=False
)

false_alarm_people = false_alarm_people.sort_values(
    "age",
    ascending=False
)


def format_people_table(data):
    display = data[
        [
            "id",
            "age",
            "avg_glucose_level",
            "hypertension",
            "heart_disease"
        ]
    ].copy()

    display.columns = [
        "번호",
        "나이",
        "평균 혈당",
        "고혈압 여부",
        "심장병 여부"
    ]

    display["고혈압 여부"] = display["고혈압 여부"].map({
        0: "없음",
        1: "있음"
    }).fillna("알 수 없음")

    display["심장병 여부"] = display["심장병 여부"].map({
        0: "없음",
        1: "있음"
    }).fillna("알 수 없음")

    display = display.head(20)

    return display


left_col, right_col = st.columns(2)

with left_col:
    st.markdown(
        f"#### 놓친 환자(FN): {len(missed_people):,}명"
    )

    if len(missed_people) > 20:
        st.caption("나이가 많은 순서로 앞의 20명만 표시한다.")

    if len(missed_people) == 0:
        st.success("놓친 환자가 없어.")
    else:
        st.dataframe(
            format_people_table(missed_people),
            use_container_width=True,
            hide_index=True
        )

with right_col:
    st.markdown(
        f"#### 헛짚은 사람(FP): {len(false_alarm_people):,}명"
    )

    if len(false_alarm_people) > 20:
        st.caption("나이가 많은 순서로 앞의 20명만 표시한다.")

    if len(false_alarm_people) == 0:
        st.success("헛짚은 사람이 없어.")
    else:
        st.dataframe(
            format_people_table(false_alarm_people),
            use_container_width=True,
            hide_index=True
        )


fn_count = counts_by_model[selected_model_key]["FN"]
fp_count = counts_by_model[selected_model_key]["FP"]

st.info(
    f"목록의 전체 인원수 확인: 놓친 환자 {len(missed_people)}명 = "
    f"혼동행렬 FN {fn_count}명 · 헛짚은 사람 {len(false_alarm_people)}명 = "
    f"혼동행렬 FP {fp_count}명"
)

st.caption(
    "목록은 선택한 모델의 채점용 예측 결과를 기준으로 만들었다. "
    "번호는 데이터의 id이며 개인 식별 정보가 아닌 데이터셋의 식별 번호다."
)
