import requests
import pandas as pd
import plotly.express as px
import streamlit as st
import re

st.title("🍱 세 학교 급식 메뉴 비교 분석기")

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

    data = requests.get(url,params=params).json()

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

    data = requests.get(url,params=params).json()

    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    rows = data["mealServiceDietInfo"][1]["row"]

    meals = []

    for r in rows:
        menu = re.sub(r"\([0-9\.]+\)","",r["DDISH_NM"])
        meals.append(menu.replace("<br/>","\n"))

    return pd.DataFrame({
        "학교":name,
        "날짜":[r["MLSV_YMD"] for r in rows],
        "메뉴":meals
    })


df = pd.concat([meal_data(s) for s in SCHOOLS], ignore_index=True)

st.success(f"{len(df)}일의 급식 데이터를 불러왔습니다.")

# -----------------------------
# 김치 분석
# -----------------------------

kimchi_list = [
    "배추김치","깍두기","총각김치","열무김치","백김치",
    "갓김치","오이김치","파김치","나박김치","보쌈김치"
]

kimchi_result = []

for school in SCHOOLS:
    menus = "\n".join(df[df["학교"]==school]["메뉴"])

    for k in kimchi_list:
        kimchi_result.append({
            "학교":school,
            "김치":k,
            "횟수":menus.count(k)
        })

kimchi_df = pd.DataFrame(kimchi_result)

fig1 = px.bar(
    kimchi_df,
    x="김치",
    y="횟수",
    color="학교",
    barmode="group",
    title="학교별 김치 종류 출현 횟수"
)

st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# 갑각류 알레르기 분석
# -----------------------------

shellfish = ["새우","게","꽃게","새우살","칵테일새우"]

shell_result = []

for school in SCHOOLS:

    menus = df[df["학교"]==school]["메뉴"]

    count = 0

    for meal in menus:
        if any(word in meal for word in shellfish):
            count += 1

    shell_result.append({
        "학교":school,
        "갑각류 메뉴 수":count,
        "안 나온 메뉴 수":len(menus)-count
    })

shell_df = pd.DataFrame(shell_result)

shell_long = shell_df.melt(
    id_vars="학교",
    var_name="구분",
    value_name="횟수"
)

fig2 = px.bar(
    shell_long,
    x="학교",
    y="횟수",
    color="구분",
    title="학교별 갑각류 알레르기 메뉴 포함 여부"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# 디저트 분석
# -----------------------------

desserts = [
    "케이크","쿠키","마카롱","푸딩","요거트","젤리",
    "아이스크림","샤베트","도넛","와플","빵","크로플",
    "타르트","머핀","초코","과일","수박","딸기","바나나",
    "귤","포도","망고","복숭아","배","사과","토스트"
]

dessert_result = []

for school in SCHOOLS:

    text = "\n".join(df[df["학교"]==school]["메뉴"])

    for d in desserts:
        c = text.count(d)

        if c > 0:
            dessert_result.append({
                "학교":school,
                "디저트":d,
                "횟수":c
            })

dessert_df = pd.DataFrame(dessert_result)

selected = st.selectbox("디저트 비율 보기", SCHOOLS)

fig3 = px.pie(
    dessert_df[dessert_df["학교"]==selected],
    names="디저트",
    values="횟수",
    hole=0.55,
    title=f"{selected} 디저트 종류 비율"
)

st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# 분석 결과 표
# -----------------------------

st.subheader("급식 원본 데이터")

st.dataframe(df)
