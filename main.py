
import streamlit as st
import pandas as pd

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.code(str(e))
    st.stop()


st.title("🧠 뇌졸중 예측 실습실")
st.markdown(
    """
    이 실습실에서는 뇌졸중 관련 데이터를 살펴보고,
    데이터의 특징과 뇌졸중 발생 여부 사이의 관계를 탐색한다.

    왼쪽 사이드바에서 **탐색 페이지**를 선택하면 그래프와 분석 결과를 확인할 수 있다.
    """
)

st.divider()

st.subheader("📊 데이터 한눈에 보기")

total_rows = len(df)
total_columns = len(df.columns)
stroke_count = int((df["stroke"] == 1).sum())
stroke_rate = stroke_count / total_rows * 100 if total_rows > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("전체 데이터 수", f"{total_rows:,}개")

with col2:
    st.metric("전체 변수 수", f"{total_columns}개")

with col3:
    st.metric("뇌졸중 발생 데이터", f"{stroke_count:,}개")

with col4:
    st.metric("뇌졸중 발생 비율", f"{stroke_rate:.2f}%")

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
    elif column in ["stroke", "hypertension", "heart_disease"]:
        return "이진값 (0, 1)"
    elif pd.api.types.is_numeric_dtype(df[column]):
        return "수치형"
    else:
        return "범주형"


column_info = pd.DataFrame({
    "열 이름": df.columns,
    "우리말 뜻": [meanings.get(column, "설명 없음") for column in df.columns],
    "값의 종류": [get_data_type(column) for column in df.columns],
    "빈 값 개수": [int(df[column].isna().sum()) for column in df.columns]
})

st.dataframe(
    column_info,
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("🔎 데이터 미리 보기")
st.caption("아래 표는 원본 데이터의 처음 5개 행이다.")

st.dataframe(
    df.head(5),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.subheader("🧭 다른 페이지로 이동하기")

st.info(
    "화면 왼쪽의 사이드바에서 '탐색' 페이지를 선택해. "
    "사이드바가 접혀 있다면 왼쪽 위 메뉴 아이콘을 눌러 열 수 있어."
)

with st.expander("📖 데이터 출처"):
    st.write("출처: GitHub 공개 CSV 데이터")
    st.code(DATA_URL, language=None)

st.caption(
    "주의: 이 데이터는 학습 및 탐색 실습용이다. "
    "분석 결과만으로 개인의 뇌졸중 발생 여부를 확정할 수 없다."
)
