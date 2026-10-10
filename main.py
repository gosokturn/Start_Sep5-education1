
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
        return pd.DataFrame(), {}, 0

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

        expected_ab = (
            menu_counts[a] / total_days
        ) * (
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

    return rules_df, menu_counts, len(pair_counts)


with st.sidebar:
    st.header("데이터 설정")

    data_url = st.text_input(
        "CSV 데이터 주소",
        value=DEFAULT_URL,
        help="UTF-8 인코딩이며 날짜, 식사, 메뉴 열이 있어야 합니다."
    )

    st.divider()
    st.header("규칙 필터")

    min_days = st.slider(
        "최소 동시 일수",
        min_value=1,
        max_value=10,
        value=1,
        step=1,
        help="선택한 횟수 이상 함께 나온 메뉴 규칙만 표시합니다."
    )


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
    rules_df, menu_counts, pair_count = find_rules(baskets)

except Exception as e:
    st.error(f"데이터를 불러오거나 분석하지 못했습니다: {e}")
    st.info("CSV 주소, UTF-8 인코딩, 열 이름을 확인해 주세요.")
    st.stop()


total_days = len(baskets)
menu_count = len(menu_counts)
all_menus = sorted(menu_counts.keys())

if total_days == 0:
    st.warning("분석할 급식 데이터가 없습니다.")
    st.stop()


# 요약 정보
c1, c2, c3 = st.columns(3)
c1.metric("급식 일수", f"{total_days:,}일")
c2.metric("메뉴 종류 수", f"{menu_count:,}종")
c3.metric("함께 나온 메뉴 쌍", f"{pair_count:,}쌍")

st.divider()


# 연관 규칙 탐색
st.subheader("🔎 연관 규칙 탐색")

col1, col2 = st.columns([2, 1])

with col1:
    selected_menu = st.selectbox(
        "규칙을 좁혀 볼 메뉴",
        options=["전체 메뉴"] + all_menus,
        index=0,
        key="rule_menu_filter"
    )

with col2:
    sort_by = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0
    )


# 최소 동시 일수 필터를 먼저 적용
filtered = rules_df[
    rules_df["동시"] >= min_days
].copy()

# 선택한 메뉴가 조건 또는 결과인 규칙만 표시
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


# 필터링 후 남은 규칙 수
st.write(
    f"**현재 조건에 남은 규칙: {len(filtered):,}개** "
    f"(최소 동시 일수 {min_days}일 이상)"
)

if filtered.empty:
    st.info(
        "조건에 맞는 규칙이 없습니다. "
        "최소 동시 일수를 낮추거나 다른 메뉴를 선택해 보세요."
    )
else:
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

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# 향상도 상위 10개 그래프
st.subheader("📊 향상도 상위 10개 규칙")

chart_df = filtered.sort_values(
    by=["향상도", "신뢰도", "동시"],
    ascending=[False, False, False]
).head(10).copy()

if chart_df.empty:
    st.info("그래프로 표시할 규칙이 없습니다.")
else:
    chart_df["규칙"] = (
        chart_df["조건"] + " → " + chart_df["결과"]
    )

    chart_df = chart_df.sort_values(
        "향상도",
        ascending=True
    )

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


st.divider()


# 함께 나온 적 없는 짝
st.subheader("🚫 함께 나온 적 없는 짝")
st.caption(
    "선택한 메뉴와 같은 날 한 번도 함께 나오지 않았지만, "
    "단독으로는 10일 이상 등장한 메뉴를 찾습니다."
)

if not all_menus:
    st.info("선택할 메뉴가 없습니다.")
else:
    absent_menu = st.selectbox(
        "함께 나온 적 없는 짝을 찾을 기준 메뉴",
        options=all_menus,
        index=0,
        key="absent_pair_menu"
    )

    selected_days = menu_counts[absent_menu]

    # 선택 메뉴가 등장한 날의 다른 메뉴와 함께 나온 횟수 계산
    cooccurring_menus = set()

    for basket in baskets:
        if absent_menu in basket:
            cooccurring_menus.update(basket)

    cooccurring_menus.discard(absent_menu)

    # 10일 이상 등장했지만 선택 메뉴와 동시 등장한 적이 없는 메뉴
    absent_candidates = [
        (menu, count)
        for menu, count in menu_counts.items()
        if menu != absent_menu
        and count >= 10
        and menu not in cooccurring_menus
    ]

    absent_candidates.sort(
        key=lambda item: (-item[1], item[0])
    )

    st.write(
        f"**선택한 메뉴 「{absent_menu}」는 "
        f"{selected_days:,}일 등장했습니다.**"
    )

    st.write(
        f"함께 나온 적 없는 메뉴: "
        f"**{len(absent_candidates):,}종**"
    )

    if absent_candidates:
        absent_df = pd.DataFrame(
            absent_candidates,
            columns=["메뉴", "등장 일수"]
        )

        st.dataframe(
            absent_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "이 메뉴와 한 번도 함께 나오지 않았으면서 "
            "10일 이상 등장한 메뉴가 없습니다."
        )


with st.expander("📘 지표 읽는 법"):
    st.markdown(
        """
        - **지지도**: 전체 급식 중 두 메뉴가 함께 나온 비율
        - **신뢰도**: 조건 메뉴가 나온 날에 결과 메뉴도 나온 비율
        - **향상도 1 초과**: 두 메뉴가 독립적일 때보다 자주 함께 등장
        - **향상도 1**: 독립적인 등장 빈도와 같음
        - **향상도 1 미만**: 독립적일 때보다 덜 자주 함께 등장
        - **최소 동시 일수**: 선택한 횟수 미만으로 함께 나온 규칙은 제외

        향상도가 높더라도 인과관계를 뜻하지는 않습니다.
        '함께 나온 적 없는 짝'도 분석한 데이터 기간 안에서의 결과입니다.
        """
    )


with st.expander("원본 데이터 확인"):
    st.dataframe(
        selected_df,
        use_container_width=True,
        hide_index=True
    )
