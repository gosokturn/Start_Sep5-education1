
import re
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="급식 규칙 찾기",
    page_icon="🍱",
    layout="wide"
)

st.title("🍱 급식 규칙 찾기")
st.caption("1년치 급식 데이터에서 함께 등장하는 메뉴의 규칙을 발견해 보세요.")

DEFAULT_URL = (
    "https://raw.githubusercontent.com/teacher188-netizen/"
    "2026-datascience/refs/heads/main/sangok_meals.csv"
)

with st.sidebar:
    st.header("데이터 설정")
    data_url = st.text_input(
        "CSV 데이터 주소",
        value=DEFAULT_URL,
        help="UTF-8 인코딩이며 날짜, 식사, 메뉴 열이 있어야 합니다."
    )
    st.caption("주소를 변경하면 해당 CSV를 분석합니다.")

@st.cache_data
def load_data(url):
    df = pd.read_csv(url, encoding="utf-8")
    df.columns = [str(c).strip() for c in df.columns]

    required = ["날짜", "식사", "메뉴"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"필수 열이 없습니다: {', '.join(missing)}"
        )

    df = df[required].copy()
    df = df.dropna(subset=["메뉴"])
    df["메뉴"] = df["메뉴"].astype(str)
    df["식사"] = df["식사"].fillna("").astype(str).str.strip()

    return df


def clean_menu(name):
    name = str(name).strip()

    # 괄호 및 괄호 안의 내용 제거
    previous = None
    while previous != name:
        previous = name
        name = re.sub(r"\([^()]*\)", "", name)
        name = re.sub(r"\[[^\[\]]*\]", "", name)
        name = re.sub(r"（[^（）]*）", "", name)
        name = re.sub(r"\{[^{}]*\}", "", name)

    return re.sub(r"\s+", " ", name).strip()


def prepare_baskets(df):
    baskets = []

    for _, row in df.iterrows():
        menus = {
            clean_menu(item)
            for item in row["메뉴"].split("|")
            if clean_menu(item)
        }

        if menus:
            baskets.append(menus)

    return baskets


def find_rules(baskets):
    total_days = len(baskets)

    if total_days == 0:
        return pd.DataFrame(), 0, 0

    menu_counts = {}
    pair_counts = {}

    for basket in baskets:
        for menu in basket:
            menu_counts[menu] = menu_counts.get(menu, 0) + 1

        for a, b in combinations(sorted(basket), 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    rules = []

    for (a, b), together in pair_counts.items():
        support = together / total_days
        confidence_ab = together / menu_counts[a]
        confidence_ba = together / menu_counts[b]

        expected_ab = (menu_counts[a] / total_days) * (
            menu_counts[b] / total_days
        )
        lift = support / expected_ab if expected_ab else 0

        rules.append({
            "조건": a,
            "결과": b,
            "동시": together,
            "지지도": support,
            "신뢰도": confidence_ab,
            "향상도": lift
        })

        rules.append({
            "조건": b,
            "결과": a,
            "동시": together,
            "지지도": support,
            "신뢰도": confidence_ba,
            "향상도": lift
        })

    rules_df = pd.DataFrame(
        rules,
        columns=["조건", "결과", "동시", "지지도", "신뢰도", "향상도"]
    )

    return rules_df, len(menu_counts), len(pair_counts)


try:
    if not data_url.strip():
        st.info("사이드바에 CSV 주소를 입력해 주세요.")
        st.stop()

    with st.spinner("급식 데이터를 분석하고 있습니다..."):
        df = load_data(data_url.strip())

    lunch = df[
        df["식사"].str.contains("중식", case=False, na=False)
    ].copy()

    if lunch.empty:
        st.warning(
            "식사 열에서 '중식'을 찾지 못했습니다. "
            "전체 데이터로 분석합니다."
        )
        selected_df = df
    else:
        selected_df = lunch

    baskets = prepare_baskets(selected_df)
    rules_df, menu_count, pair_count = find_rules(baskets)

except Exception as e:
    st.error(f"데이터를 불러오거나 분석하지 못했습니다: {e}")
    st.info("CSV 주소, UTF-8 인코딩, 열 이름을 확인해 주세요.")
    st.stop()


# 요약 정보
c1, c2, c3 = st.columns(3)
c1.metric("급식 일수", f"{len(baskets):,}일")
c2.metric("메뉴 종류 수", f"{menu_count:,}종")
c3.metric("함께 나온 메뉴 쌍", f"{pair_count:,}쌍")

st.divider()

if rules_df.empty:
    st.warning("서로 다른 메뉴가 함께 나온 기록이 없습니다.")
    st.stop()


# 필터 및 정렬
st.subheader("🔎 연관 규칙 탐색")

all_menus = sorted(
    set(rules_df["조건"]).union(set(rules_df["결과"]))
)

col1, col2 = st.columns([2, 1])

with col1:
    selected_menu = st.selectbox(
        "메뉴 선택",
        options=["전체 메뉴"] + all_menus,
        index=0
    )

with col2:
    sort_by = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0
    )

filtered = rules_df.copy()

if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ].copy()

sort_columns = {
    "향상도 순": ["향상도", "신뢰도", "동시"],
    "신뢰도 순": ["신뢰도", "향상도", "동시"],
    "동시 순": ["동시", "향상도", "신뢰도"]
}

filtered = filtered.sort_values(
    by=sort_columns[sort_by],
    ascending=[False, False, False]
).reset_index(drop=True)

display_df = filtered.copy()
display_df["지지도"] = display_df["지지도"].map(
    lambda x: f"{x:.2%}"
)
display_df["신뢰도"] = display_df["신뢰도"].map(
    lambda x: f"{x:.2%}"
)
display_df["향상도"] = display_df["향상도"].map(
    lambda x: f"{x:.3f}"
)

st.caption(
    f"표시 중인 규칙: {len(filtered):,}개 "
    "(조건과 결과를 바꾼 규칙은 별도로 표시)"
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

# 상위 10개 향상도 가로 막대그래프
st.subheader("📊 향상도 상위 10개 규칙")

chart_df = filtered.sort_values(
    by=["향상도", "신뢰도", "동시"],
    ascending=[False, False, False]
).head(10).copy()

if chart_df.empty:
    st.info("선택한 메뉴에 해당하는 규칙이 없습니다.")
else:
    chart_df["규칙"] = (
        chart_df["조건"] + " → " + chart_df["결과"]
    )

    chart_df = chart_df.sort_values("향상도", ascending=True)

    fig = px.bar(
        chart_df,
        x="향상도",
        y="규칙",
        orientation="h",
        text=chart_df["향상도"].map(lambda x: f"{x:.3f}"),
        labels={
            "향상도": "향상도 (Lift)",
            "규칙": "조건 → 결과"
        },
        title="함께 등장하는 경향이 강한 메뉴 규칙"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis_title="",
        xaxis_title="향상도",
        height=max(350, 42 * len(chart_df)),
        margin=dict(l=20, r=60, t=60, b=30)
    )

    st.plotly_chart(fig, use_container_width=True)

with st.expander("📘 지표 읽는 법"):
    st.markdown(
        """
        - **지지도**: 전체 급식 중 두 메뉴가 함께 나온 비율
        - **신뢰도**: 조건 메뉴가 나온 날에 결과 메뉴도 나온 비율
        - **향상도 1 초과**: 두 메뉴가 독립적일 때보다 자주 함께 등장
        - **향상도 1**: 독립적인 등장 빈도와 같음
        - **향상도 1 미만**: 독립적일 때보다 덜 자주 함께 등장

        향상도가 높더라도 한 해의 급식 데이터에서 발견된
        연관성일 뿐, 두 메뉴 사이의 인과관계를 뜻하지는 않습니다.
        """
    )

with st.expander("원본 데이터 확인"):
    st.dataframe(selected_df, use_container_width=True, hide_index=True)
