
import streamlit as st
import pandas as pd


st.title("📝 내가 만든 모델 소개")

st.write(
    "모델을 어떻게 만들었는지 설명하고, "
    "고치기 전과 고친 뒤의 평가 결과를 직접 정리하는 작성지다."
)

st.info(
    "이 페이지는 데이터를 불러오거나 모델을 학습하지 않는다. "
    "앞 페이지에서 확인한 값을 직접 옮겨 적으면 된다."
)


# --------------------------------------------------
# 작성 항목과 결과 표의 초기 상태
# --------------------------------------------------

questions = [
    ("data_description", "무슨 데이터입니까"),
    ("prediction_features", "무엇을 보고 맞힙니까"),
    ("preprocessing_changes", "무엇을 고쳤습니까"),
    ("screening_center_use", "이 모델을 검진센터가 사용해도 됩니까"),
    ("model_limit", "이 모델이 못 하는 것 한 가지")
]

metric_names = [
    "정확도",
    "재현율",
    "F1",
    "찾아낸 환자",
    "헛짚은 사람"
]

if "model_intro_answers" not in st.session_state:
    st.session_state["model_intro_answers"] = {
        key: "" for key, _ in questions
    }

if "model_intro_results" not in st.session_state:
    st.session_state["model_intro_results"] = pd.DataFrame({
        "평가 항목": metric_names,
        "고치기 전": [""] * len(metric_names),
        "고친 뒤": [""] * len(metric_names)
    })


# --------------------------------------------------
# 탭 구성
# --------------------------------------------------

write_tab, summary_tab = st.tabs([
    "✍️ 작성하기",
    "📄 한 장으로 보기"
])


# --------------------------------------------------
# 탭 1: 작성하기
# --------------------------------------------------

with write_tab:
    st.subheader("1. 내가 만든 모델 설명")

    st.caption(
        "각 질문에 답을 여러 줄로 작성해 줘. "
        "아직 정하지 못한 항목은 비워 두어도 돼."
    )

    for key, question in questions:
        st.text_area(
            question,
            key=f"answer_{key}",
            height=120,
            placeholder=f"{question}에 대한 내용을 적어 줘."
        )

    st.divider()
    st.subheader("2. 평가 결과 비교")

    st.write(
        "앞 페이지에서 확인한 값을 직접 옮겨 적어 줘. "
        "인원수는 명 단위로, 비율은 백분율이나 소수 등 "
        "확인하기 쉬운 형식으로 적으면 돼."
    )

    edited_results = st.data_editor(
        st.session_state["model_intro_results"],
        key="model_intro_results_editor",
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=["평가 항목"],
        column_config={
            "평가 항목": st.column_config.TextColumn(
                "평가 항목",
                width="medium"
            ),
            "고치기 전": st.column_config.TextColumn(
                "고치기 전",
                width="large"
            ),
            "고친 뒤": st.column_config.TextColumn(
                "고친 뒤",
                width="large"
            )
        }
    )

    # 사용자가 편집한 표를 현재 세션 상태에 반영한다.
    st.session_state["model_intro_results"] = edited_results

    st.caption(
        "입력 내용은 이 페이지의 현재 세션에서만 사용한다. "
        "파일 저장이나 외부 전송 기능은 없다."
    )


# --------------------------------------------------
# 탭 2: 한 장으로 보기
# --------------------------------------------------

with summary_tab:
    st.subheader("내가 만든 모델 소개")

    st.caption(
        "작성하기 탭에 입력한 내용을 한 화면에 모아 본다."
    )

    for index, (key, question) in enumerate(questions, start=1):
        st.markdown(f"#### {index}. {question}")

        answer = st.session_state.get(
            f"answer_{key}",
            ""
        )

        if answer and answer.strip():
            st.markdown(answer)
        else:
            st.caption("아직 적지 않음")

        st.divider()

    st.markdown("#### 6. 평가 결과 비교")

    results = st.session_state.get(
        "model_intro_results",
        pd.DataFrame({
            "평가 항목": metric_names,
            "고치기 전": [""] * len(metric_names),
            "고친 뒤": [""] * len(metric_names)
        })
    )

    display_results = results.copy()

    for column in ["고치기 전", "고친 뒤"]:
        display_results[column] = display_results[column].apply(
            lambda value: (
                "아직 적지 않음"
                if pd.isna(value) or not str(value).strip()
                else str(value)
            )
        )

    st.dataframe(
        display_results,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.caption(
        "이 화면은 작성한 내용을 확인하기 위한 것이다. "
        "입력한 내용은 외부로 보내거나 파일로 저장하지 않는다."
    )
