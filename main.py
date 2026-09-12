import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import re

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
        "Type":"json",
        "SCHUL_NM":name
    }
    data = requests.get(url, params=params).json()
    row = data["schoolInfo"][1]["row"][0]
    return row["ATPT_OFCDC_SC_CODE"], row["SD_SCHUL_CODE"]

def meal_data(name):
    edu, code = school_code(name)

    url = f"{BASE}/mealServiceDietInfo"

    params = {
        "Type":"json",
        "ATPT_OFCDC_SC_CODE":edu,
        "SD_SCHUL_CODE":code,
        "MMEAL_SC_CODE":"2",
        "MLSV_FROM_YMD":FROM,
        "MLSV_TO_YMD":TO,
        "pSize":"1000"
    }

    data = requests.get(url, params=params).json()

    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    rows = data["mealServiceDietInfo"][1]["row"]

    meals = []

    for r in rows:
        menu = re.sub(r"\([0-9\.]+\)", "", r["DDISH_NM"])
        meals.append(menu.replace("<br/>","\n"))

    return pd.DataFrame({
        "학교":name,
        "날짜":[r["MLSV_YMD"] for r in rows],
        "메뉴":meals
    })

df = pd.concat([meal_data(s) for s in SCHOOLS], ignore_index=True)

st.title("🍱 세 학교 1년 급식 분석")

kimchi_types = [
    "배추김치","깍두기","총각김치","열무김치",
    "백김치","갓김치","파김치","오이김치",
    "나박김치","보쌈김치"
]

st.header("🥬 학교별 김치 종류 비율")

for school in SCHOOLS:

    text = "\n".join(df[df["학교"]==school]["메뉴"])

    result = []

    for k in kimchi_types:
        count = text.count(k)
        if count > 0:
            result.append({
                "김치":k,
                "횟수":count
            })

    kimchi_df = pd.DataFrame(result)

    st.subheader(school)

    fig = px.pie(
        kimchi_df,
        names="김치",
        values="횟수",
        hole=0.6
    )

    fig.update_traces(textinfo="percent+label")

    st.plotly_chart(fig, use_container_width=True)

shellfish_words = [
    "새우","게","꽃게","새우살","칵테일새우",
    "감바스","새우튀김","새우볶음","게살"
]

st.header("🦐 갑각류 메뉴가 나온 날짜")

for school in SCHOOLS:

    result = []

    meals = df[df["학교"]==school]

    for _, row in meals.iterrows():

        if any(word in row["메뉴"] for word in shellfish_words):
            result.append({
                "날짜":row["날짜"],
                "메뉴":row["메뉴"].replace("\n"," / ")
            })

    st.subheader(school)

    if result:
        st.dataframe(pd.DataFrame(result), use_container_width=True)
    else:
        st.write("갑각류 메뉴 없음")

dessert_words = [
    "케이크","쿠키","마카롱","푸딩","요거트",
    "젤리","아이스크림","샤베트","도넛","와플",
    "크로플","타르트","머핀","초코","과일",
    "수박","딸기","바나나","귤","포도","망고",
    "복숭아","배","사과","파인애플","토스트"
]

st.header("🍰 학교별 디저트 메뉴")

for school in SCHOOLS:

    desserts = []

    meals = df[df["학교"]==school]

    for _, row in meals.iterrows():

        menu_list = row["메뉴"].split("\n")

        for menu in menu_list:
            if any(word in menu for word in dessert_words):
                desserts.append({
                    "날짜":row["날짜"],
                    "디저트":menu
                })

    dessert_df = pd.DataFrame(desserts)

    st.subheader(school)

    st.dataframe(dessert_df, use_container_width=True)

st.header("📄 전체 급식 데이터")

st.dataframe(df, use_container_width=True)
