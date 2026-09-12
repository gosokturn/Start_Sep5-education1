import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import re

st.set_page_config(
    page_title="세 학교 급식 비교",
    page_icon="🍱",
    layout="wide"
)

API_KEY = st.secrets["NEIS_API_KEY"]
BASE_URL = "https://open.neis.go.kr/hub"

SCHOOLS = [
    "인천산곡고등학교",
    "세일고등학교",
    "부평고등학교"
]

FROM = "20260101"
TO = "20261231"

st.markdown("""
<style>
.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
}
.metric{
    background:#F8FAFC;
    border:1px solid #E5E7EB;
    border-radius:14px;
    padding:15px;
    text-align:center;
}
.shell-card{
    background:#EFF6FF;
    border-left:6px solid #2563EB;
    border-radius:12px;
    padding:15px;
    margin-bottom:12px;
}
.dessert-card{
    background:#FFF7ED;
    border-left:6px solid #EA580C;
    border-radius:12px;
    padding:12px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def school_code(name):
    params={
        "KEY":API_KEY,
        "Type":"json",
        "SCHUL_NM":name
    }
    data=requests.get(f"{BASE_URL}/schoolInfo",params=params).json()
    row=data["schoolInfo"][1]["row"][0]
    return row["ATPT_OFCDC_SC_CODE"],row["SD_SCHUL_CODE"]

@st.cache_data
def meal_data(name):
    edu,code=school_code(name)

    params={
        "KEY":API_KEY,
        "Type":"json",
        "ATPT_OFCDC_SC_CODE":edu,
        "SD_SCHUL_CODE":code,
        "MMEAL_SC_CODE":"2",
        "MLSV_FROM_YMD":FROM,
        "MLSV_TO_YMD":TO,
        "pSize":1000,
        "pIndex":1
    }

    data=requests.get(
        f"{BASE_URL}/mealServiceDietInfo",
        params=params
    ).json()

    rows=data["mealServiceDietInfo"][1]["row"]

    result=[]

    for r in rows:
        raw=r["DDISH_NM"]
        clean=re.sub(r"\([0-9\.]+\)","",raw)
        clean=clean.replace("<br/>","\n")

        result.append({
            "학교":name,
            "날짜":pd.to_datetime(r["MLSV_YMD"]),
            "원본메뉴":raw,
            "메뉴":clean
        })

    return pd.DataFrame(result)

df=pd.concat([meal_data(s) for s in SCHOOLS],ignore_index=True)

kimchi_list=[]
shell_rows=[]
dessert_rows=[]

dessert_keywords=[
"케이크","치즈케이크","초코케이크","생크림케이크","롤케이크","컵케이크",
"마카롱","쿠키","비스킷","브라우니","머핀","도넛","츄러스","와플",
"크로플","타르트","카스테라","마들렌","파이","푸딩","젤리",
"요거트","그릭요거트","요구르트","아이스크림","샤베트","빙수",
"아이스바","초코우유","딸기우유","바나나우유","우유","주스",
"수박","멜론","사과","배","바나나","귤","포도","청포도","샤인머스켓",
"딸기","망고","복숭아","참외","파인애플","오렌지","키위","체리",
"자두","감","토마토"
]

shell_keywords=[
"새우","칵테일새우","새우살","건새우","왕새우","새우튀김","새우까스",
"새우볶음","새우링","새우볼","꽃게","게","게살","게맛살","대게","홍게"
]

for _,row in df.iterrows():

    menus=row["메뉴"].split("\n")
    rawmenus=row["원본메뉴"].split("<br/>")

    for m in menus:
        item=m.strip()
        item=item.replace("-자율","").replace("(자율)","")

        if "김치" in item or item in ["동치미","석박지","겉절이"]:
            kimchi_list.append([row["학교"],item])

        if any(d in item for d in dessert_keywords):
            dessert_rows.append([
                row["학교"],
                row["날짜"].strftime("%Y-%m-%d"),
                item
            ])

    for raw in rawmenus:

        clean=re.sub(r"\([0-9\.]+\)","",raw)
        allergy="".join(re.findall(r"\((.*?)\)",raw))

        if any(k in clean for k in shell_keywords) or "8" in allergy or "9" in allergy:
            shell_rows.append({
                "학교":row["학교"],
                "날짜":row["날짜"].strftime("%Y-%m-%d"),
                "갑각류메뉴":clean.strip(),
                "전체메뉴":row["메뉴"].replace("\n"," / ")
            })

kimchi_df=pd.DataFrame(kimchi_list,columns=["학교","김치"])
dessert_df=pd.DataFrame(
    dessert_rows,
    columns=["학교","날짜","디저트"]
).drop_duplicates()

shellfish_df=pd.DataFrame(shell_rows).drop_duplicates()

st.title("🍱 2026년 세 학교 급식 메뉴 비교 분석")

c1,c2,c3,c4=st.columns(4)

with c1:
    st.markdown(
        f"<div class='metric'><h3>{len(df)}</h3><p>급식일 수</p></div>",
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f"<div class='metric'><h3>{len(shellfish_df)}</h3><p>갑각류 메뉴</p></div>",
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f"<div class='metric'><h3>{dessert_df['디저트'].nunique()}</h3><p>디저트 종류</p></div>",
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f"<div class='metric'><h3>{len(SCHOOLS)}</h3><p>분석 학교</p></div>",
        unsafe_allow_html=True
    )

st.divider()

st.header("🥬 학교별 김치 종류 비율")

cols=st.columns(3)

for col,school in zip(cols,SCHOOLS):

    data=(
        kimchi_df[kimchi_df["학교"]==school]["김치"]
        .value_counts()
        .reset_index()
    )

    data.columns=["김치","횟수"]

    fig=px.pie(
        data,
        names="김치",
        values="횟수",
        hole=0.6
    )

    fig.update_traces(textinfo="percent+label")
    fig.update_layout(
        title=school,
        showlegend=False,
        margin=dict(l=0,r=0,t=40,b=0)
    )

    col.plotly_chart(fig,use_container_width=True)

st.divider()

st.header("🦐 갑각류 메뉴 날짜별 확인")

school_choice=st.selectbox(
    "학교 선택",
    SCHOOLS
)

school_shell=shellfish_df[shellfish_df["학교"]==school_choice].sort_values("날짜")

st.write(f"총 **{len(school_shell)}회** 갑각류 메뉴가 제공되었습니다.")

for _,r in school_shell.iterrows():

    st.markdown(
        f"""
        <div class="shell-card">
            <h4>🗓 {r['날짜']}</h4>
            <p><b>갑각류 메뉴 :</b> {r['갑각류메뉴']}</p>
            <p>{r['전체메뉴']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()
st.header("🍰 디저트 검색")

search = st.text_input(
    "디저트 이름을 검색하세요.",
    placeholder="예) 마카롱, 아이스크림, 수박, 케이크..."
)

if search:
    result = dessert_df[
        dessert_df["디저트"].str.contains(search, case=False, na=False)
    ]
else:
    result = dessert_df.copy()

st.write(f"검색 결과 **{len(result)}개**")

st.dataframe(
    result.sort_values(["학교", "날짜"]),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.header("📊 학교별 디저트 제공 횟수")

dessert_count = (
    dessert_df.groupby("디저트")
    .size()
    .reset_index(name="횟수")
    .sort_values("횟수", ascending=False)
)

fig = px.bar(
    dessert_count.head(20),
    x="횟수",
    y="디저트",
    orientation="h",
    text="횟수"
)

fig.update_layout(
    yaxis={"categoryorder": "total ascending"},
    showlegend=False,
    margin=dict(l=20, r=20, t=40, b=20)
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.header("🏆 학교별 인기 디저트 TOP 5")

col1, col2, col3 = st.columns(3)

for col, school in zip([col1, col2, col3], SCHOOLS):

    top5 = (
        dessert_df[dessert_df["학교"] == school]
        .groupby("디저트")
        .size()
        .reset_index(name="횟수")
        .sort_values("횟수", ascending=False)
        .head(5)
    )

    with col:

        st.subheader(school)

        medals = ["🥇", "🥈", "🥉", "④", "⑤"]

        for i, (_, row) in enumerate(top5.iterrows()):
            st.markdown(
                f"""
                <div class="dessert-card">
                    <b>{medals[i]} {row['디저트']}</b><br>
                    제공 횟수 : {row['횟수']}회
                </div>
                """,
                unsafe_allow_html=True
            )

st.divider()

st.header("📅 학교별 디저트 제공 일정")

school_dessert = st.selectbox(
    "디저트 일정 확인",
    SCHOOLS,
    key="dessert_school"
)

school_table = dessert_df[dessert_df["학교"] == school_dessert]

st.dataframe(
    school_table.sort_values("날짜"),
    use_container_width=True,
    hide_index=True
)

st.divider()

st.header("📋 전체 급식 데이터")

with st.expander("전체 급식 메뉴 보기"):

    st.dataframe(
        df[["학교", "날짜", "메뉴"]]
        .sort_values(["학교", "날짜"]),
        use_container_width=True,
        hide_index=True
    )

st.divider()

with st.expander("📚 자료 출처 보기"):

    st.markdown("""
    **데이터 출처**

    - 교육부 **나이스(NEIS) 교육정보 개방 포털**
    - `schoolInfo` API (학교 코드 조회)
    - `mealServiceDietInfo` API (급식 식단 정보)

    **조회 기간**

    - 2026년 1월 1일 ~ 2026년 12월 31일
    - 중식(MMEAL_SC_CODE=2)

    **분석 내용**

    - 학교별 김치 종류 비율
    - 갑각류(새우·게) 포함 메뉴 날짜
    - 학교별 디저트 종류와 제공 날짜
    - 디저트 제공 횟수 통계
    """)
