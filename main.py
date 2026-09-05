import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import pytz

# ==========================================
# 1. 페이지 설정 및 커스텀 테마 CSS
# ==========================================
st.set_page_config(
    page_title="KOBIS 박스오피스 인사이트 인텔리전스",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 고급 대시보드 UI를 위한 테마 CSS
st.markdown("""
    <style>
    /* Google Fonts Pretendard 웹폰트 로드 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* 상단 헤더 배너 */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311b92 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 32px 36px;
        border-radius: 16px;
        margin-bottom: 28px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #94a3b8;
        font-weight: 400;
    }

    /* 구분을 위한 섹션 컨테이너 카드 */
    .section-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 32px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 2px solid #1f2937;
        padding-bottom: 14px;
        margin-bottom: 24px;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f3f4f6;
        margin: 0;
    }
    .section-badge {
        background: #3b82f6;
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
    }

    /* KPI 카드 디자인 */
    .kpi-card {
        background: #1e293b;
        border-left: 4px solid #3b82f6;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .kpi-label {
        font-size: 0.875rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    .kpi-sub {
        font-size: 0.85rem;
        color: #38bdf8;
        font-weight: 500;
    }

    /* 영화 카드 인터랙션 UI */
    .movie-detail-card {
        background: #1f2937;
        border: 1px solid #374151;
        border-radius: 14px;
        padding: 24px;
        margin-top: 12px;
    }
    
    /* Plotly 차트 배경 투명화 */
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. API 수집 및 캐싱 (KOBIS API)
# ==========================================
@st.cache_data(ttl=3600)
def fetch_daily_box_office(api_key: str, target_date_str: str):
    """
    KOBIS 일별 박스오피스 API 호출
    """
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_date_str}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None, f"서버 통신 오류 (HTTP {response.status_code})"
            
        data = response.json()
        if "faultInfo" in data:
            return None, f"API 오류: {data['faultInfo'].get('message', '인증 실패')}"
            
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])
        
        if not daily_list:
            return None, "그날은 아직 집계 전입니다."
            
        return daily_list, None
    except requests.exceptions.RequestException as e:
        return None, f"네트워크 통신 에러: {str(e)}"


# ==========================================
# 3. 데이터 정제 및 전처리
# ==========================================
def process_box_office_data(raw_data):
    df = pd.DataFrame(raw_data)

    numeric_cols = [
        "rank", "rankInten", "audiCnt", "audiAcc", 
        "scrnCnt", "showCnt", "salesAmt", "salesShare", "salesAcc"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 순위 변동 포맷
    def format_rank_change(row):
        if row.get("rankOldAndNew") == "NEW":
            return "🆕 NEW"
        inten = int(row["rankInten"])
        if inten > 0:
            return f"🔺 {inten}"
        elif inten < 0:
            return f"🔻 {abs(inten)}"
        else:
            return "➖"

    df["순위변동"] = df.apply(format_rank_change, axis=1)

    # 100만 이상 관객 트로피 표기
    def format_movie_title(row):
        title = row["movieNm"]
        if row["audiAcc"] >= 1_000_000:
            return f"🏆 {title}"
        return title

    df["디스플레이_제목"] = df.apply(format_movie_title, axis=1)
    
    # 1회당 평균 관객수 (좌석 효율성)
    df["회당관객수"] = (df["audiCnt"] / df["showCnt"].replace(0, 1)).round(1)
    
    # 실시간 모멘텀 점수 계산 (관객수 + 매출점유율 + 회당관객 가중치 조합)
    max_audi = df["audiCnt"].max() if df["audiCnt"].max() > 0 else 1
    max_per_show = df["회당관객수"].max() if df["회당관객수"].max() > 0 else 1
    df["모멘텀점수"] = (
        (df["audiCnt"] / max_audi * 50) + 
        (df["salesShare"] * 0.3) + 
        (df["회당관객수"] / max_per_show * 20)
    ).round(1)

    return df.sort_values(by="rank", ascending=True).reset_index(drop=True)


# ==========================================
# 4. 차트 렌더링 헬퍼 함수 (Dark Theme 최적화)
# ==========================================
def apply_dark_chart_style(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Pretendard, sans-serif", color="#cbd5e1", size=12),
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
        yaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
    )
    return fig


# ==========================================
# 5. 메인 애플리케이션
# ==========================================
def main():
    # -------------------------------------------------------------
    # [사이드바 Controls]
    # -------------------------------------------------------------
    st.sidebar.markdown("### ⚙️ 대시보드 필터")
    
    kst = pytz.timezone("Asia/Seoul")
    today_kst = datetime.datetime.now(kst).date()
    yesterday_kst = today_kst - datetime.timedelta(days=1)

    selected_date = st.sidebar.date_input(
        label="📅 조회 일자",
        value=yesterday_kst,
        max_value=yesterday_kst,
        min_value=datetime.date(2004, 1, 1),
        help="오늘 데이터는 미집계 상태이므로 어제 날짜까지 선택할 수 있습니다."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **💡 안내 및 안내 사항**
    - **API Key:** Streamlit Secrets 내 `KOBIS_KEY` 이용
    - **업데이트:** 매일 KST 00시 이후 집계
    """)

    # -------------------------------------------------------------
    # [Hero Banner]
    # -------------------------------------------------------------
    st.markdown(f"""
        <div class="hero-container">
            <div class="hero-title">🎬 KOBIS 박스오피스 인텔리전스</div>
            <div class="hero-subtitle">기준일자: <strong>{selected_date.strftime('%Y년 %m월 %d일')}</strong> | 대한민국 영화 시장 실시간 분석 리포트</div>
        </div>
    """, unsafe_allow_html=True)

    # API Key 검증
    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 API 인증키(KOBIS_KEY)가 설정되지 않았습니다.")
        st.warning("Streamlit Cloud 설정(Settings -> Secrets)에서 `KOBIS_KEY`를 추가하세요.")
        return

    api_key = st.secrets["KOBIS_KEY"]
    target_dt_str = selected_date.strftime("%Y%m%d")

    # 데이터 로딩
    with st.spinner("박스오피스 빅데이터를 다차원으로 분석 중입니다..."):
        raw_data, error_msg = fetch_daily_box_office(api_key, target_dt_str)

    if error_msg:
        if error_msg == "그날은 아직 집계 전입니다.":
            st.info("ℹ️ 그날은 아직 집계 전입니다.")
        else:
            st.error("⚠️ 데이터를 불러올 수 없습니다.")
            st.warning(f"**원인:** {error_msg}")
        return

    df = process_box_office_data(raw_data)

    # -------------------------------------------------------------
    # [SECTION 1] 핵심 성과 지표 (KPI Overview)
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">📌 일별 주요 시장 지표 (KPI Overview)</div>
                <div class="section-badge">SUMMARY</div>
            </div>
    """, unsafe_allow_html=True)

    top_movie = df.iloc[0]
    total_audi = df["audiCnt"].sum()
    total_sales = df["salesAmt"].sum()
    new_movies = (df["rankOldAndNew"] == "NEW").sum()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">🥇 박스오피스 1위</div>
                <div class="kpi-value">{top_movie['movieNm']}</div>
                <div class="kpi-sub">어제 관객 {int(top_movie['audiCnt']):,}명</div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #10b981;">
                <div class="kpi-label">👥 Top 10 총 관객수</div>
                <div class="kpi-value">{int(total_audi):,}명</div>
                <div class="kpi-sub">누적 관객 합계 {int(df['audiAcc'].sum()):,}명</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #f59e0b;">
                <div class="kpi-label">💰 Top 10 총 매출액</div>
                <div class="kpi-value">₩{int(total_sales / 100000000):,}억원</div>
                <div class="kpi-sub">시장 매출 규모</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="kpi-card" style="border-left-color: #8b5cf6;">
                <div class="kpi-label">🆕 신규 차트인 영화</div>
                <div class="kpi-value">{new_movies}편</div>
                <div class="kpi-sub">신규 진입 경쟁작</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [SECTION 2] 실시간 인기영화 흥행 모멘텀 차트
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">🔥 실시간 흥행 모멘텀 & 관객 트렌드 분석</div>
                <div class="section-badge">REAL-TIME TREND</div>
            </div>
    """, unsafe_allow_html=True)

    col_trend1, col_trend2 = st.columns([6, 4])

    with col_trend1:
        st.markdown("##### 🚀 영화별 종합 흥행 모멘텀 지수 (Momentum Score)")
        st.caption("※ 일일 관객수, 매출 점유율, 회당 관객 효율성을 종합 가중 산출한 흥행 파워 지수입니다.")
        
        fig_momentum = px.bar(
            df.sort_values(by="모멘텀점수", ascending=True),
            x="모멘텀점수",
            y="디스플레이_제목",
            orientation="h",
            text="모멘텀점수",
            color="모멘텀점수",
            color_continuous_scale=["#1e3a8a", "#3b82f6", "#60a5fa", "#f59e0b", "#ef4444"]
        )
        fig_momentum.update_traces(texttemplate='%{text}점', textposition='outside')
        fig_momentum = apply_dark_chart_style(fig_momentum)
        fig_momentum.update_layout(height=380, showlegend=False, xaxis_title="흥행 모멘텀 점수", yaxis_title="")
        st.plotly_chart(fig_momentum, use_container_width=True)

    with col_trend2:
        st.markdown("##### 🍕 시장 점유율 Distribution")
        st.caption("상위 Top 10 영화 간 매출액 점유율 비교")
        
        fig_pie = px.pie(
            df,
            names="movieNm",
            values="salesShare",
            hole=0.5,
            color_discrete_sequence=px.colors.sequential.Darkmint_r
        )
        fig_pie.update_traces(textinfo="percent+label", textposition="inside")
        fig_pie = apply_dark_chart_style(fig_pie)
        fig_pie.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [SECTION 3] 영화별 세부 정보 및 심층 비교
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">🔍 개별 영화 심층 인텔리전스 & 상영 효율성</div>
                <div class="section-badge">DETAIL ANALYSIS</div>
            </div>
    """, unsafe_allow_html=True)

    selected_movie_name = st.selectbox(
        "🎬 상세 정보를 확인할 영화를 선택하세요",
        options=df["movieNm"].tolist(),
        index=0
    )

    movie_info = df[df["movieNm"] == selected_movie_name].iloc[0]

    st.markdown(f"""
        <div class="movie-detail-card">
            <h3 style="margin-top:0; color:#38bdf8;">{movie_info['디스플레이_제목']} <span style="font-size:1rem; color:#94a3b8;">(개봉일: {movie_info['openDt']})</span></h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-top: 16px;">
                <div><strong>순위:</strong> {int(movie_info['rank'])}위 ({movie_info['순위변동']})</div>
                <div><strong>어제 관객수:</strong> {int(movie_info['audiCnt']):,} 명</div>
                <div><strong>누적 관객수:</strong> {int(movie_info['audiAcc']):,} 명</div>
                <div><strong>스크린 수:</strong> {int(movie_info['scrnCnt']):,} 개</div>
                <div><strong>상영 횟수:</strong> {int(movie_info['showCnt']):,} 회</div>
                <div><strong>회당 평균 관객:</strong> {movie_info['회당관객수']} 명/회</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("##### 📈 스크린 독점도 대비 관객 동원 효율성 분석")
    st.caption("💡 오른쪽 상단에 위치할수록 스크린 수가 많고 관객 수가 많은 인기작이며, 원의 크기는 누적 관객수를 의미합니다.")

    fig_scatter = px.scatter(
        df,
        x="scrnCnt",
        y="audiCnt",
        size="audiAcc",
        color="movieNm",
        hover_name="movieNm",
        text="movieNm",
        labels={
            "scrnCnt": "스크린 수 (개)",
            "audiCnt": "일일 관객 수 (명)",
            "audiAcc": "누적 관객수"
        }
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter = apply_dark_chart_style(fig_scatter)
    fig_scatter.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [SECTION 4] 전체 순위 데이터 종합 표
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">📋 전체 박스오피스 종합 마스터 테이블</div>
                <div class="section-badge">DATA TABLE</div>
            </div>
    """, unsafe_allow_html=True)

    search_query = st.text_input("🔍 표 내 영화 제목 검색", "", placeholder="검색할 영화명을 입력하세요...")
    
    table_df = df.copy()
    if search_query:
        table_df = table_df[table_df["movieNm"].str.contains(search_query, case=False, na=False)]

    view_cols = [
        "rank", "순위변동", "디스플레이_제목", "openDt", 
        "audiCnt", "audiAcc", "scrnCnt", "showCnt", "salesShare", "모멘텀점수"
    ]
    
    render_df = table_df[view_cols].copy()
    render_df.columns = [
        "순위", "변동", "영화명 (100만+ 🏆)", "개봉일", 
        "어제 관객수", "누적 관객수", "스크린수", "상영횟수", "점유율(%)", "모멘텀 지수"
    ]

    st.dataframe(
        render_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "순위": st.column_config.NumberColumn(format="%d 위"),
            "어제 관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적 관객수": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
            "상영횟수": st.column_config.NumberColumn(format="%d 회"),
            "점유율(%)": st.column_config.NumberColumn(format="%.1f %%"),
            "모멘텀 지수": st.column_config.NumberColumn(format="%.1f 점"),
        }
    )

    csv_bytes = render_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 데이터셋 CSV 익스포트",
        data=csv_bytes,
        file_name=f"kobis_boxoffice_intelligence_{target_dt_str}.csv",
        mime="text/csv"
    )

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
