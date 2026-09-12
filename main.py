import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import re

API_KEY = st.secrets["NEIS_API_KEY"]
BASE = "https://open.neis.go.kr/hub"

SCHOOLS = [
    "인천산곡고등학교",
    "세일고등학교",
    "부평고등학교"
]

FROM = "20260101"
TO = "20261231"

def school_code(name):
    url = f"{BASE}/schoolInfo"
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "SCHUL_NM": name
    }
    data = requests.get(url, params=params).json()
    row = data["schoolInfo"][1]["row"][0]
    return row["ATPT_OFCDC_SC_CODE"], row["SD_SCHUL_CODE"]

def meal_data(name):
    edu, code = school_code(name)

    url = f"{BASE}/mealServiceDietInfo"

    params = {
        "KEY": API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": edu,
        "SD_SCHUL_CODE": code,
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": FROM,
        "MLSV_TO_YMD": TO,
        "pSize": "1000",
        "pIndex": "1"
    }

    data = requests.get(url, params=params).json()

    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    rows = data["mealServiceDietInfo"][1]["row"]

    result = []

    for r in rows:
        raw = r["DDISH_NM"]
        clean = re.sub(r"\([0-9\.]+\)", "", raw).replace("<br/>", "\n")

        result.append({
            "학교": name,
            "날짜": pd.to_datetime(r["MLSV_YMD"]),
            "원본메뉴": raw,
            "메뉴": clean
        })

    return pd.DataFrame(result)

df = pd.concat([meal_data(s) for s in SCHOOLS], ignore_index=True)

st.title("🍱 2026년 세 학교 급식 비교 분석")

st.write(f"총 {len(df)}일의 급식 데이터를 분석했습니다.")

def extract_kimchi(menu):
    foods = []

    for item in menu.split("\n"):
        item = item.strip()
        item = item.replace("-자율", "")
        item = item.replace("(자율)", "")

        if "김치" in item or item in ["석박지", "동치미", "겉절이"]:
            foods.append(item)

    return foods

kimchi_data = {}

for school in SCHOOLS:

    kimchis = []

    for meal in df[df["학교"] == school]["메뉴"]:
        kimchis.extend(extract_kimchi(meal))

    kimchi_data[school] = (
        pd.Series(kimchis)
        .value_counts()
        .reset_index()
    )

    kimchi_data[school].columns = ["김치", "횟수"]

st.header("🥬 학교별 김치 종류 비율")

c1, c2, c3 = st.columns(3)

for col, school in zip([c1, c2, c3], SCHOOLS):
    with col:
        fig = px.pie(
            kimchi_data[school],
            names="김치",
            values="횟수",
            hole=0.6
        )

        fig.update_layout(
            title=school,
            showlegend=False,
            margin=dict(l=0, r=0, t=45, b=0)
        )

        fig.update_traces(textinfo="percent+label")

        st.plotly_chart(fig, use_container_width=True)

shellfish_keywords = [
    "새우","칵테일새우","새우살","왕새우","건새우","새우튀김",
    "새우볶음","새우까스","새우볼","새우링","새우완자",
    "게","꽃게","게살","크래미","게맛살","대게","홍게","꽃게탕"
]

st.header("🦐 갑각류 메뉴가 나온 날짜")

shell_rows = []

for school in SCHOOLS:

    meals = df[df["학교"] == school]

    for _, row in meals.iterrows():

        found = False

        for menu in row["원본메뉴"].split("<br/>"):

            menu_clean = re.sub(r"\([0-9\.]+\)", "", menu)

            allergy = re.findall(r"\((.*?)\)", menu)

            allergy_text = "".join(allergy)

            if (
                any(word in menu_clean for word in shellfish_keywords)
                or "8" in allergy_text
                or "9" in allergy_text
            ):
                found = True

        if found:
            shell_rows.append({
                "학교": school,
                "날짜": row["날짜"].strftime("%Y-%m-%d"),
                "메뉴": row["메뉴"].replace("\n"," / ")
            })

shellfish_df = pd.DataFrame(shell_rows)

st.dataframe(shellfish_df, use_container_width=True)

dessert_keywords = [
    "케이크","초코케이크","생크림케이크","치즈케이크","롤케이크","컵케이크",
    "마카롱","쿠키","비스킷","크래커","도넛","츄러스","와플","크로플",
    "머핀","파이","타르트","브라우니","브레드","빵","모닝빵","소보루",
    "식빵","토스트","크루아상","샌드쿠키","초코칩","카스테라","마들렌",
    "푸딩","젤리","요거트","그릭요거트","요구르트","아이스크림","샤베트",
    "빙수","아이스바","초코우유","딸기우유","바나나우유","우유빙수",
    "수박","멜론","바나나","사과","배","포도","딸기","귤","오렌지",
    "참외","복숭아","망고","블루베리","파인애플","키위","토마토","체리",
    "자두","감","샤인머스켓","청포도","한라봉","레몬에이드","망고주스",
    "사과주스","오렌지주스","포도주스","딸기라떼","초코라떼","밀크쉐이크"
]

st.header("🍰 학교별 디저트 메뉴")

dessert_rows = []

for school in SCHOOLS:

    meals = df[df["학교"] == school]

    for _, row in meals.iterrows():

        for menu in row["메뉴"].split("\n"):

            if any(word in menu for word in dessert_keywords):

                dessert_rows.append({
                    "학교": school,
                    "날짜": row["날짜"].strftime("%Y-%m-%d"),
                    "디저트": menu.strip()
                })

dessert_df = (
    pd.DataFrame(dessert_rows)
    .drop_duplicates()
    .sort_values(["학교","날짜"])
)

for school in SCHOOLS:

    st.subheader(school)

    school_df = dessert_df[dessert_df["학교"] == school]

    st.write(f"디저트 제공 횟수 : {len(school_df)}회")

    st.dataframe(
        school_df[["날짜","디저트"]],
        use_container_width=True
    )

st.header("📊 학교별 디저트 제공 횟수")

dessert_count = (
    dessert_df.groupby(["학교","디저트"])
    .size()
    .reset_index(name="횟수")
)

fig = px.bar(
    dessert_count,
    x="디저트",
    y="횟수",
    color="학교",
    barmode="group"
)

st.plotly_chart(fig, use_container_width=True)

st.header("📄 전체 급식 데이터")

st.dataframe(
    df[["학교","날짜","메뉴"]].sort_values(["학교","날짜"]),
    use_container_width=True
)
