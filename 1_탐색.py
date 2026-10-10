
import streamlit as st
import pandas as pd
import plotly.express as px

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"

st.set_page_config(
    page_title="탐색 | 뇌졸중 예측 실습실",
    page_icon="🔎",
    layout="wide"
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #2457A6;
        margin-bottom: 0.3rem;
    }
    .sub-title {
        color: #64748b;
        margin-bottom: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


def stroke_label(value):
    if value == 1:
        return "뇌졸중 경험 있음"
    return "뇌졸중 경험 없음"


def binary_label(value):
    if pd.isna(value):
        return "결측값"
    if value == 1:
        return "있음"
    if value == 0:
        return "없음"
    return str(value)


def make_rate_table(data, column):
    grouped = data.groupby(column, dropna=False)["stroke"].agg(
        ["count", "mean"]
    ).reset_index()

    grouped.columns = [column, "사람 수", "뇌졸중 비율"]

    if column in ["hypertension", "heart_disease"]:
        grouped[column] = grouped[column].map(binary_label)
        order = ["없음", "있음", "결측값"]
        grouped[column] = pd.Categorical(
            grouped[column],
            categories=order,
            ordered=True
        )
        grouped = grouped.sort_values(column)

    grouped["뇌졸중 비율"] = grouped["뇌졸중 비율"] * 100

    return grouped


try:
    df = load_data()

    required_columns = [
        "age",
        "avg_glucose_level",
        "hypertension",
        "heart_disease",
        "bmi",
        "smoking_status",
        "stroke"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        st.error(
            "필요한 열이 데이터에 없습니다: "
            + ", ".join(missing_columns)
        )
        st.stop()

    st.markdown(
        '<div class="main-title">🔎 데이터 탐색</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">'
        '그래프와 표를 통해 뇌졸중 데이터의 특징을 살펴본다.'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("## 1. 나이와 평균 혈당의 분포")

    st.write(
        "히스토그램을 이용해 사람들의 나이와 평균 혈당 값이 "
        "어느 구간에 많이 분포하는지 확인한다."
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_age_hist = px.histogram(
            df,
            x="age",
            nbins=30,
            title="나이 분포",
            labels={
                "age": "나이",
                "count": "사람 수"
            },
            color_discrete_sequence=["#4C78A8"]
        )

        fig_age_hist.update_layout(
            xaxis_title="나이",
            yaxis_title="사람 수",
            bargap=0.08
        )

        st.plotly_chart(
            fig_age_hist,
            use_container_width=True
        )

    with col2:
        fig_glucose_hist = px.histogram(
            df,
            x="avg_glucose_level",
            nbins=30,
            title="평균 혈당 분포",
            labels={
                "avg_glucose_level": "평균 혈당",
                "count": "사람 수"
            },
            color_discrete_sequence=["#F58518"]
        )

        fig_glucose_hist.update_layout(
            xaxis_title="평균 혈당",
            yaxis_title="사람 수",
            bargap=0.08
        )

        st.plotly_chart(
            fig_glucose_hist,
            use_container_width=True
        )

    st.divider()

    st.markdown("## 2. 뇌졸중 경험 유무에 따른 비교")

    st.write(
        "뇌졸중을 겪은 사람과 겪지 않은 사람의 나이와 평균 혈당을 "
        "상자그림으로 비교한다. 상자그림은 중앙값과 데이터의 분포를 "
        "살펴보는 데 도움이 된다."
    )

    df["stroke_group"] = df["stroke"].map(stroke_label)

    group_order = [
        "뇌졸중 경험 없음",
        "뇌졸중 경험 있음"
    ]

    col1, col2 = st.columns(2)

    with col1:
        fig_age_box = px.box(
            df,
            x="stroke_group",
            y="age",
            color="stroke_group",
            category_orders={"stroke_group": group_order},
            title="뇌졸중 경험 유무에 따른 나이",
            labels={
                "stroke_group": "뇌졸중 경험",
                "age": "나이",
                "stroke_group": "뇌졸중 경험"
            },
            color_discrete_map={
                "뇌졸중 경험 없음": "#4C78A8",
                "뇌졸중 경험 있음": "#E45756"
            }
        )

        fig_age_box.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="나이"
        )

        st.plotly_chart(
            fig_age_box,
            use_container_width=True
        )

    with col2:
        fig_glucose_box = px.box(
            df,
            x="stroke_group",
            y="avg_glucose_level",
            color="stroke_group",
            category_orders={"stroke_group": group_order},
            title="뇌졸중 경험 유무에 따른 평균 혈당",
            labels={
                "stroke_group": "뇌졸중 경험",
                "avg_glucose_level": "평균 혈당"
            },
            color_discrete_map={
                "뇌졸중 경험 없음": "#4C78A8",
                "뇌졸중 경험 있음": "#E45756"
            }
        )

        fig_glucose_box.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="평균 혈당"
        )

        st.plotly_chart(
            fig_glucose_box,
            use_container_width=True
        )

    st.markdown("### 두 집단의 평균값")

    mean_table = (
        df.groupby("stroke_group")[
            ["age", "avg_glucose_level"]
        ]
        .mean()
        .reindex(group_order)
        .reset_index()
    )

    mean_table.columns = [
        "뇌졸중 경험",
        "평균 나이",
        "평균 혈당"
    ]

    mean_table["평균 나이"] = mean_table["평균 나이"].round(2)
    mean_table["평균 혈당"] = mean_table["평균 혈당"].round(2)

    st.dataframe(
        mean_table,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "평균은 각 집단에 속한 사람들의 산술평균이다. "
        "두 집단의 평균 차이만으로 원인과 결과를 단정할 수는 없다."
    )

    st.divider()

    st.markdown("## 3. 고혈압과 심장병에 따른 뇌졸중 비율")

    st.write(
        "고혈압과 심장병이 있는 집단과 없는 집단의 뇌졸중 비율을 비교한다. "
        "비율은 각 집단의 전체 사람 수 중 stroke가 1인 사람의 비율이다."
    )

    hypertension_table = make_rate_table(df, "hypertension")
    heart_disease_table = make_rate_table(df, "heart_disease")

    col1, col2 = st.columns(2)

    with col1:
        fig_hypertension = px.bar(
            hypertension_table,
            x="hypertension",
            y="뇌졸중 비율",
            text="뇌졸중 비율",
            title="고혈압 유무에 따른 뇌졸중 비율",
            labels={
                "hypertension": "고혈압",
                "뇌졸중 비율": "뇌졸중 비율 (%)"
            },
            color="hypertension",
            color_discrete_map={
                "없음": "#4C78A8",
                "있음": "#E45756",
                "결측값": "#9D9DA0"
            }
        )

        fig_hypertension.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_hypertension.update_layout(
            yaxis_title="뇌졸중 비율 (%)",
            xaxis_title="고혈압",
            yaxis_range=[
                0,
                max(
                    5,
                    float(hypertension_table["뇌졸중 비율"].max()) * 1.2
                )
            ],
            showlegend=False
        )

        st.plotly_chart(
            fig_hypertension,
            use_container_width=True
        )

        st.dataframe(
            hypertension_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "hypertension": "고혈압",
                "사람 수": st.column_config.NumberColumn(
                    "사람 수",
                    format="%d"
                ),
                "뇌졸중 비율": st.column_config.NumberColumn(
                    "뇌졸중 비율 (%)",
                    format="%.2f"
                )
            }
        )

    with col2:
        fig_heart_disease = px.bar(
            heart_disease_table,
            x="heart_disease",
            y="뇌졸중 비율",
            text="뇌졸중 비율",
            title="심장병 유무에 따른 뇌졸중 비율",
            labels={
                "heart_disease": "심장병",
                "뇌졸중 비율": "뇌졸중 비율 (%)"
            },
            color="heart_disease",
            color_discrete_map={
                "없음": "#4C78A8",
                "있음": "#E45756",
                "결측값": "#9D9DA0"
            }
        )

        fig_heart_disease.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig_heart_disease.update_layout(
            yaxis_title="뇌졸중 비율 (%)",
            xaxis_title="심장병",
            yaxis_range=[
                0,
                max(
                    5,
                    float(heart_disease_table["뇌졸중 비율"].max()) * 1.2
                )
            ],
            showlegend=False
        )

        st.plotly_chart(
            fig_heart_disease,
            use_container_width=True
        )

        st.dataframe(
            heart_disease_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "heart_disease": "심장병",
                "사람 수": st.column_config.NumberColumn(
                    "사람 수",
                    format="%d"
                ),
                "뇌졸중 비율": st.column_config.NumberColumn(
                    "뇌졸중 비율 (%)",
                    format="%.2f"
                )
            }
        )

    st.caption(
        "이 그래프는 집단별 비율의 차이를 보여준다. "
        "고혈압이나 심장병이 뇌졸중의 원인이라고 이 그래프만으로 "
        "확정할 수는 없다."
    )

    st.divider()

    st.markdown("## 4. BMI가 비어 있는 사람들의 뇌졸중 비율")

    st.write(
        "bmi 값이 비어 있는 사람들만 따로 살펴보고, "
        "그 집단의 뇌졸중 비율을 전체 데이터의 비율과 비교한다."
    )

    missing_bmi = df[df["bmi"].isna()]

    missing_bmi_people = len(missing_bmi)
    missing_bmi_stroke = int((missing_bmi["stroke"] == 1).sum())

    missing_bmi_rate = (
        missing_bmi_stroke / missing_bmi_people * 100
        if missing_bmi_people > 0
        else 0
    )

    total_stroke_people = int((df["stroke"] == 1).sum())

    total_stroke_rate = (
        total_stroke_people / len(df) * 100
        if len(df) > 0
        else 0
    )

    bmi_table = pd.DataFrame({
        "비교 대상": [
            "BMI가 비어 있는 사람",
            "전체 사람"
        ],
        "사람 수": [
            missing_bmi_people,
            len(df)
        ],
        "뇌졸중 경험자 수": [
            missing_bmi_stroke,
            total_stroke_people
        ],
        "뇌졸중 비율 (%)": [
            round(missing_bmi_rate, 2),
            round(total_stroke_rate, 2)
        ]
    })

    st.dataframe(
        bmi_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "사람 수": st.column_config.NumberColumn(
                "사람 수",
                format="%d"
            ),
            "뇌졸중 경험자 수": st.column_config.NumberColumn(
                "뇌졸중 경험자 수",
                format="%d"
            ),
            "뇌졸중 비율 (%)": st.column_config.NumberColumn(
                "뇌졸중 비율 (%)",
                format="%.2f"
            )
        }
    )

    st.caption(
        "BMI가 비어 있다는 사실만으로 뇌졸중 위험이 높거나 낮다고 "
        "판단할 수는 없다. 두 집단의 차이는 추가적인 분석이 필요하다."
    )

    st.divider()

    st.markdown("## 5. 흡연 상태별 사람 수")

    st.write(
        "흡연 상태에 기록된 값마다 사람 수를 세어 비교한다. "
        "Unknown은 흡연 상태를 알 수 없는 경우이며, "
        "실제 빈 값이 있다면 결측값으로 별도 표시한다."
    )

    smoking_counts = (
        df["smoking_status"]
        .fillna("결측값")
        .astype(str)
        .value_counts()
        .rename_axis("흡연 상태")
        .reset_index(name="사람 수")
    )

    smoking_counts = smoking_counts.sort_values(
        "사람 수",
        ascending=False
    ).reset_index(drop=True)

    st.dataframe(
        smoking_counts,
        use_container_width=True,
        hide_index=True,
        column_config={
            "흡연 상태": st.column_config.TextColumn("흡연 상태"),
            "사람 수": st.column_config.NumberColumn(
                "사람 수",
                format="%d"
            )
        }
    )

    fig_smoking = px.bar(
        smoking_counts,
        x="흡연 상태",
        y="사람 수",
        text="사람 수",
        title="흡연 상태별 사람 수",
        labels={
            "흡연 상태": "흡연 상태",
            "사람 수": "사람 수"
        },
        color="흡연 상태",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_smoking.update_traces(
        textposition="outside"
    )

    fig_smoking.update_layout(
        xaxis_title="흡연 상태",
        yaxis_title="사람 수",
        showlegend=False
    )

    st.plotly_chart(
        fig_smoking,
        use_container_width=True
    )

    st.divider()

    st.markdown("### 💡 탐색 결과를 해석할 때")

    st.info(
        "그래프에서 발견한 차이는 데이터의 특징을 설명하지만, "
        "그 자체로 인과관계를 증명하지는 않는다. "
        "집단별 사람 수와 비율을 함께 살펴보고 해석하는 것이 중요하다."
    )

    st.caption(
        "데이터 출처: "
        + DATA_URL
    )

except Exception as error:
    st.error(
        "데이터를 불러오거나 분석하는 중 오류가 발생했다. "
        "데이터 주소, 열 이름과 인터넷 연결을 확인해 주세요."
    )
    st.exception(error)
