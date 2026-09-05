import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import pytz

# ==========================================
# 1. 페이지 기본 설정 및 디자인 CSS 정의
# ==========================================
st.set_page_config(
    page_title="KOBIS 일별 박스오피스 대시보드",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 공공기관 대시보드 느낌의 깔끔한 사용자 정의 CSS 스타일 적용
st.markdown("""
    <style>
    /* 메인 배경 및 타이틀 스타일 */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #f8fafc !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin-bottom: 8px !important;
    }
    .main-header p {
        color: #94a3b8 !important;
        margin: 0 !important;
        font-size: 0.95rem;
    }
    
    /* 카드 / 메트릭 스타일링 */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #0f172a;
    }
    
    /* 탭 디자인 강화 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #f1f5f9;
        border-radius: 8px 8px 0px 0px;
        padding: 8px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. KOBIS API 호출 함수 (캐싱 처리)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_daily_box_office(api_key: str, target_date_str: str):
    """
    KOBIS API를 호출하여 날짜별 박스오피스 데이터를 가져옵니다.
    ttl=3600으로 설정하여 같은 날짜 조회 시 1시간 동안 API 재요청 없이 캐시를 사용합니다.
    """
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": target_date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        # HTTP 응답 코드 점검
        if response.status_code != 200:
            return None, f"서버 통신 오류가 발생했습니다. (HTTP 상태 코드: {response.status_code})"
            
        data = response.json()
        
        # KOBIS API 오류 예외 처리 (인증키 오류 등)
        if "faultInfo" in data:
            message = data["faultInfo"].get("message", "알 수 없는 API 오류가 발생했습니다.")
            return None, f"KOBIS API 오류: {message}"
            
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])
        
        # 영화 목록이 비어 있는 경우
        if not daily_list:
            return None, "그날은 아직 집계 전입니다."
            
        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 오류가 발생했습니다: {str(e)}"


# ==========================================
# 3. 데이터 가공 및 변환 함수
# ==========================================
def process_box_office_data(raw_data):
    """
    API에서 문자열로 전달된 수치 데이터를 정수/실수형으로 변환하고,
    요구조건(순위증감 화살표, 100만 관객 트로피 이모지 등)을 반영합니다.
    """
    df = pd.DataFrame(raw_data)

    # 1. 수치형 컬럼 변환
    numeric_cols = [
        "rank", "rankInten", "audiCnt", "audiAcc", 
        "scrnCnt", "showCnt", "salesAmt", "salesShare", "salesAcc"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 2. 순위 증감(rankInten) 표시 가공
    # 양수 -> 빨간 위 화살표(🔺), 음수 -> 파란 아래 화살표(🔻), 신규진입 -> 🆕 NEW
    def format_rank_change(row):
        if row.get("rankOldAndNew") == "NEW":
            return "🆕 NEW"
        inten = int(row["rankInten"])
        if inten > 0:
            return f"🔺 {inten}"
        elif inten < 0:
            return f"🔻 {abs(inten)}"
        else:
            return "-"

    df["순위변동"] = df.apply(format_rank_change, axis=1)

    # 3. 누적관객 100만 명 이상 영화명 옆 트로피(🏆) 이모지 추가
    def format_movie_name(row):
        name = row["movieNm"]
        if row["audiAcc"] >= 1_000_000:
            return f"🏆 {name}"
        return name

    df["표시_영화명"] = df.apply(format_movie_name, axis=1)

    # 4. 순위 기준 오름차순 정렬
    df = df.sort_values(by="rank", ascending=True).reset_index(drop=True)
    return df


# ==========================================
# 4. 메인 애플리케이션
# ==========================================
def main():
    # -------------------------------------------------------------
    # [사이드바] 날짜 선택 및 API 키 확인
    # -------------------------------------------------------------
    st.sidebar.image("https://img.icons8.com/color/96/movie-ticket.png", width=64)
    st.sidebar.title("📌 조회 설정")
    
    # KST (한국 표준시) 기준 어제 날짜 계산
    kst = pytz.timezone("Asia/Seoul")
    today_kst = datetime.datetime.now(kst).date()
    yesterday_kst = today_kst - datetime.timedelta(days=1)

    # 달력에서 조회 날짜 선택 (최대 날짜는 '어제'로 제한)
    selected_date = st.sidebar.date_input(
        label="조회 날짜 선택",
        value=yesterday_kst,
        max_value=yesterday_kst,
        min_value=datetime.date(2004, 1, 1), # KOBIS 데이터 제공 시작 시점
        help="오늘 데이터는 집계 전이므로, 어제 날짜까지만 고를 수 있습니다."
    )

    st.sidebar.info(f"💡 **선택된 날짜:**\n{selected_date.strftime('%Y년 %m월 %d일')}")
    st.sidebar.markdown("---")
    st.sidebar.caption("데이터 출처: 영화진흥위원회(KOBIS) Open API")

    # 헤더 영역
    st.markdown(f"""
        <div class="main-header">
            <h1>🎬 영화진흥위원회 일별 박스오피스 대시보드</h1>
            <p>선택 날짜: <strong>{selected_date.strftime('%Y-%m-%d')}</strong> 기준 영화 시장 현황 보고서</p>
        </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Secrets 관리자 설정 확인
    # -------------------------------------------------------------
    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 API 인증키(KOBIS_KEY)가 설정되지 않았습니다.")
        st.warning("""
        **Streamlit Cloud 비밀금고(Secrets) 설정 방법:**
        1. Streamlit 대시보드의 앱 설정(Settings) -> **Secrets** 클릭
        2. `KOBIS_KEY = "발급받은_키"` 등록
        """)
        return

    api_key = st.secrets["KOBIS_KEY"]
    target_dt_str = selected_date.strftime("%Y%m%d")

    # -------------------------------------------------------------
    # API 데이터 수집 및 처리
    # -------------------------------------------------------------
    with st.spinner("박스오피스 데이터를 분석 중입니다..."):
        raw_data, error_message = fetch_daily_box_office(api_key, target_dt_str)

    # 데이터 호출 실패 및 오류 발생 시 처리
    if error_message:
        if error_message == "그날은 아직 집계 전입니다.":
            st.info("ℹ️ 그날은 아직 집계 전입니다. 다른 날짜를 선택해 주세요.")
        else:
            st.error("⚠️ 데이터를 불러올 수 없습니다.")
            st.warning(f"**원인:** {error_message}")
            st.info("""
            **확인 사항:**
            - API 키가 정확하게 등록되어 있는지 확인해 주세요.
            - KOBIS 서버 상태 및 네트워크 연결을 점검해 주세요.
            """)
        return

    # 데이터 가공
    df = process_box_office_data(raw_data)

    # -------------------------------------------------------------
    # [요약 지표] 상단 주요 요약 카드 (KPI Cards)
    # -------------------------------------------------------------
    top_1_movie = df.iloc[0]
    total_audience = df["audiCnt"].sum()
    total_screens = df["scrnCnt"].sum()
    new_entry_count = (df["rankOldAndNew"] == "NEW").sum()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(
            label="🥇 1위 영화",
            value=top_1_movie["movieNm"],
            delta=f"관객 {int(top_1_movie['audiCnt']):,}명"
        )
    with kpi2:
        st.metric(
            label="👥 일일 총 관객수 (Top10)",
            value=f"{int(total_audience):,} 명"
        )
    with kpi3:
        st.metric(
            label="🖥️ 총 상영 스크린수",
            value=f"{int(total_screens):,} 개"
        )
    with kpi4:
        st.metric(
            label="🆕 신규 진입 영화",
            value=f"{new_entry_count} 편"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [탭 구성] 공공/기업 사이트 스타일 분석 탭
    # -------------------------------------------------------------
    tab1, tab2, tab3 = st.tabs([
        "📊 차트 보고서 (관객/점유율)", 
        "📋 전체 박스오피스 상세 표", 
        "🔍 영화 시장 심층 분석"
    ])

    # ==========================================
    # TAB 1: 차트 보고서
    # ==========================================
    with tab1:
        col_chart1, col_chart2 = st.columns([6, 4])

        with col_chart1:
            st.subheader("🏆 관객수 상위 5개 영화")
            top5_df = df.head(5).sort_values(by="audiCnt", ascending=True)

            fig_bar = px.bar(
                top5_df,
                x="audiCnt",
                y="표시_영화명",
                orientation="h",
                text="audiCnt",
                labels={"audiCnt": "어제 관객수", "표시_영화명": "영화명"},
                color="audiCnt",
                color_continuous_scale="Blues"
            )
            fig_bar.update_traces(texttemplate='%{text:,}명', textposition='outside')
            fig_bar.update_layout(
                height=380,
                showlegend=False,
                xaxis_title="관객수 (명)",
                yaxis_title="",
                margin=dict(l=10, r=40, t=10, b=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            st.subheader("🍕 매출액 점유율 (Top 10)")
            fig_donut = px.pie(
                df,
                names="movieNm",
                values="salesShare",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_donut.update_traces(textinfo="percent+label")
            fig_donut.update_layout(
                height=380,
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    # ==========================================
    # TAB 2: 상세 데이터표
    # ==========================================
    with tab2:
        st.subheader("📋 순위별 상세 현황")

        # 검색 필터 기능 추가
        search_kw = st.text_input("🔍 영화명 검색", "", placeholder="영화 제목을 입력하세요...")
        
        display_df = df.copy()
        if search_kw:
            display_df = display_df[display_df["movieNm"].str.contains(search_kw, case=False, na=False)]

        # 필요한 컬럼 정제
        view_cols = [
            "rank", "순위변동", "표시_영화명", "openDt", 
            "audiCnt", "audiAcc", "scrnCnt", "showCnt", "salesShare"
        ]
        
        table_df = display_df[view_cols].copy()
        table_df.columns = [
            "순위", "변동", "영화명 (100만+ 🏆)", "개봉일", 
            "어제 관객수", "누적 관객수", "스크린수", "상영횟수", "점유율(%)"
        ]

        # 데이터 프레임 출력 (포맷 지정)
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "순위": st.column_config.NumberColumn(format="%d 위"),
                "어제 관객수": st.column_config.NumberColumn(format="%d 명"),
                "누적 관객수": st.column_config.NumberColumn(format="%d 명"),
                "스크린수": st.column_config.NumberColumn(format="%d 개"),
                "상영횟수": st.column_config.NumberColumn(format="%d 회"),
                "점유율(%)": st.column_config.NumberColumn(format="%.1f %%")
            }
        )

        # CSV 다운로드 버튼
        csv_data = table_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 박스오피스 데이터 CSV 다운로드",
            data=csv_data,
            file_name=f"kobis_boxoffice_{target_dt_str}.csv",
            mime="text/csv"
        )

    # ==========================================
    # TAB 3: 심층 데이터 분석
    # ==========================================
    with tab3:
        st.subheader("📈 스크린 수 대비 관객 동원 효율성")
        st.caption("스크린 수가 많을수록 상단에, 관객수가 많을수록 우측에 위치합니다.")

        # 스크린수 vs 관객수 산점도 분석
        fig_scatter = px.scatter(
            df,
            x="scrnCnt",
            y="audiCnt",
            size="audiAcc",
            color="salesShare",
            hover_name="movieNm",
            labels={
                "scrnCnt": "스크린 수 (개)",
                "audiCnt": "일일 관객 수 (명)",
                "salesShare": "점유율(%)",
                "audiAcc": "누적관객"
            },
            color_continuous_scale="Viridis"
        )
        fig_scatter.update_layout(height=420)
        st.plotly_chart(fig_scatter, use_container_width=True)

        # 회당 평균 관객수 분석 (효율 지표)
        df["audi_per_show"] = (df["audiCnt"] / df["showCnt"].replace(0, 1)).round(1)
        
        st.subheader("🎯 상영 1회당 평균 관객수 (좌석 점유 효율)")
        fig_efficiency = px.bar(
            df.sort_values(by="audi_per_show", ascending=False),
            x="movieNm",
            y="audi_per_show",
            text="audi_per_show",
            labels={"movieNm": "영화명", "audi_per_show": "회당 평균 관객(명)"},
            color="audi_per_show",
            color_continuous_scale="Tealgrn"
        )
        fig_efficiency.update_traces(texttemplate='%{text}명', textposition='outside')
        fig_efficiency.update_layout(height=380, showlegend=False, xaxis_title="", yaxis_title="명/회")
        st.plotly_chart(fig_efficiency, use_container_width=True)


if __name__ == "__main__":
    main()
