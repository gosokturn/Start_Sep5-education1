
import streamlit as st
import pandas as pd

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.exception(e)
    st.stop()


st.title("🧠 뇌졸중 예측 실습실")

st.markdown(
    """
    뇌졸중 관련 데이터를 탐색하고 분류 모델을 실습하는 공간이다.

    왼쪽 사이드바에서 **탐색** 또는 **분류 모델**을 선택할 수 있다.
    """
)

st.divider()
st.subheader("📊 데이터 한눈에 보기")

total_rows = len(df)
total_columns = len(df.columns)
stroke_count = int((df["stroke"] == 1).sum())
stroke_rate = stroke_count / total_rows * 100 if total_rows else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("전체 데이터 수", f"{total_rows:,}개")
col2.metric("전체 변수 수", f"{total_columns}개")
col3.metric("뇌졸중 데이터", f"{stroke_count:,}개")
col4.metric("뇌졸중 비율", f"{stroke_rate:.2f}%")

st.divider()
st.subheader("📋 변수 설명")

meanings = {
    "id": "번호",
    "gender": "성별",
    "age": "나이",
    "hypertension": "고혈압",
    "heart_disease": "심장병",
    "ever_married": "결혼 경험",
    "work_type": "직업 형태",
    "Residence_type": "거주 지역",
    "avg_glucose_level": "평균 혈당",
    "bmi": "체질량지수",
    "smoking_status": "흡연 상태",
    "stroke": "뇌졸중 발생 여부"
}


def get_data_type(column):
    if column == "id":
        return "식별자"
    if column in ["stroke", "hypertension", "heart_disease"]:
        return "이진값 (0, 1)"
    if pd.api.types.is_numeric_dtype(df[column]):
        return "수치형"
    return "범주형"


column_info = pd.DataFrame({
    "열 이름": df.columns,
    "우리말 뜻": [
        meanings.get(column, "설명 없음")
        for column in df.columns
    ],
    "값의 종류": [
        get_data_type(column)
        for column in df.columns
    ],
    "빈 값 개수": [
        int(df[column].isna().sum())
        for column in df.columns
    ]
})

st.dataframe(
    column_info,
    use_container_width=True,
    hide_index=True
)

st.divider()
st.subheader("🔎 데이터 미리 보기")

st.dataframe(
    df.head(5),
    use_container_width=True,
    hide_index=True
)

with st.expander("📖 데이터 출처"):
    st.code(DATA_URL, language=None)

st.caption(
    "이 데이터는 학습 및 탐색 실습용이며, "
    "모델의 예측만으로 개인의 뇌졸중 여부를 확정할 수 없다."
)
