import streamlit as st
import pandas as pd

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.35rem;
        font-weight: 800;
        color: #2457A6;
        margin-bottom: 0.25rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f1f6ff;
        border: 1px solid #d9e6fa;
        border-radius: 14px;
        padding: 20px 16px;
        min-height: 125px;
    }
    .metric-label {
        color: #526782;
        font-size: 0.92rem;
        margin-bottom: 10px;
    }
    .metric-value {
        color: #2457A6;
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .section-title {
        font-size: 1.35rem;
        font-weight: 750;
        margin-top: 1.8rem;
        margin-bottom: 0.6rem;
    }
    .source-box {
        background-color: #f8fafc;
        border: 1px solid #dce3ec;
        border-radius: 12px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-title">🧠 뇌졸중 예측 실습실</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-title">'
    '데이터를 탐색하고, 변수의 의미와 데이터의 특징을 발견하는 첫 번째 실습'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

st.markdown("### 🔎 데이터 소개")
st.write(
    """
    이 데이터는 여러 사람의 인구학적 특성, 건강 관련 정보와 뇌졸중 발생 여부를
    담고 있는 CSV 데이터이다.

    각 행은 한 사람의 정보를 나타내며, `stroke` 열은 뇌졸중 발생 여부를 나타낸다.
    이번 화면에서는 데이터를 학습하거나 예측하기 전에 데이터의 규모, 열의 종류,
    빈 값과 실제 기록을 먼저 확인한다.
    """
)

try:
    df = load_data()

    required_columns = [
        "id",
        "gender",
        "age",
        "hypertension",
        "heart_disease",
        "ever_married",
        "work_type",
        "Residence_type",
        "avg_glucose_level",
        "bmi",
        "smoking_status",
        "stroke"
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        st.error(
            "데이터에 필요한 열이 없습니다: "
            + ", ".join(missing_columns)
        )
        st.stop()

    total_people = len(df)
    total_columns = len(df.columns)
    stroke_count = int((df["stroke"] == 1).sum())

    stroke_rate = (
        stroke_count / total_people * 100
        if total_people > 0
        else 0
    )

    st.markdown("### 📊 데이터 핵심 정보")

    card_columns = st.columns(4)

    metrics = [
        ("전체 사람 수", f"{total_people:,}명"),
        ("열 개수", f"{total_columns:,}개"),
        ("stroke가 1인 사람 수", f"{stroke_count:,}명"),
        ("stroke가 1인 비율", f"{stroke_rate:.2f}%")
    ]

    for column, (label, value) in zip(card_columns, metrics):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.caption(
        "비율은 전체 데이터 중 stroke 값이 1인 행의 비율이다. "
        "소수점 둘째 자리까지 표시한다."
    )

    st.markdown(
        '<div class="section-title">📋 열 이름과 데이터 구조</div>',
        unsafe_allow_html=True
    )

    def get_value_type(series, column_name):
        if column_name == "id":
            return "식별자"
        elif column_name == "stroke":
            return "이진값 (0, 1)"
        elif column_name in ["hypertension", "heart_disease"]:
            return "이진값 (0, 1)"
        elif pd.api.types.is_numeric_dtype(series):
            return "수치형"
        else:
            return "범주형"

    column_info = pd.DataFrame({
        "열 이름": df.columns,
        "우리말 뜻": ["" for _ in df.columns],
        "값의 종류": [
            get_value_type(df[col], col)
            for col in df.columns
        ],
        "빈 값 개수": [
            int(df[col].isna().sum())
            for col in df.columns
        ]
    })

    st.write(
        "우리말 뜻은 교재를 참고하여 직접 채워 넣을 수 있도록 비워 두었다."
    )

    st.dataframe(
        column_info,
        use_container_width=True,
        hide_index=True,
        height=460,
        column_config={
            "열 이름": st.column_config.TextColumn(
                "열 이름",
                help="CSV 파일에 실제로 기록된 열 이름"
            ),
            "우리말 뜻": st.column_config.TextColumn(
                "우리말 뜻",
                help="교재를 참고하여 뜻을 직접 정리하는 칸"
            ),
            "값의 종류": st.column_config.TextColumn(
                "값의 종류"
            ),
            "빈 값 개수": st.column_config.NumberColumn(
                "빈 값 개수",
                format="%d"
            )
        }
    )

    st.caption(
        "표의 우리말 뜻 칸은 화면에서 직접 편집할 수 있는 입력 칸이 아니라 "
        "빈칸으로 표시한 열이다. 작성한 내용을 보관하려면 별도로 기록해야 한다."
    )

    st.markdown(
        '<div class="section-title">🗂️ 원본 데이터 미리보기</div>',
        unsafe_allow_html=True
    )

    st.write("데이터의 처음 다섯 행을 원본 열 이름과 값 그대로 표시한다.")

    st.dataframe(
        df.head(5),
        use_container_width=True,
        hide_index=True
    )

    st.markdown(
        '<div class="section-title">📚 데이터 출처</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="source-box">', unsafe_allow_html=True)

    source_text = st.text_area(
        "교재의 데이터 출처 내용을 여기에 작성하세요.",
        placeholder="교재에 적힌 데이터 출처를 입력하세요.",
        height=100,
        key="source_text"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        "원본 데이터 URL: "
        + DATA_URL
    )

    st.divider()

    st.caption(
        "학습용 데이터 탐색 화면이다. 이 데이터로 만든 예측 결과는 "
        "개인의 실제 뇌졸중 발생 여부를 진단하거나 확정하는 데 사용할 수 없다."
    )

except Exception as error:
    st.error(
        "데이터를 불러오는 중 오류가 발생했다. "
        "인터넷 연결과 데이터 URL을 확인해 주세요."
    )
    st.caption(f"오류 내용: {error}")
