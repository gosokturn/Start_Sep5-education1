import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import pytz

# ==========================================
# 1. 페이지 설정 및 시네마틱 레드 테마 CSS
# ==========================================
st.set_page_config(
    page_title="KOBIS 시네마틱 박스오피스 인텔리전스",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 영화관 분위기의 고급 스칼렛/버건디 레드 커스텀 CSS
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
        background-color: #0a0506;
        color: #f3f4f6;
    }
    
    /* 시네마틱 시그니처 레드 히어로 헤더 */
    .hero-container {
        background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 50%, #991b1b 100%);
        border: 1px solid #dc2626;
        padding: 32px 36px;
        border-radius: 16px;
        margin-bottom: 28px;
        box-shadow: 0 12px 30px rgba(220, 38, 38, 0.25);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.6);
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #fca5a5;
        font-weight: 400;
    }

    /* 시네마 섹션 카드 */
    .section-card {
        background: #14080a;
        border: 1px solid #2d1216;
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 32px;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
    }
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        border-bottom: 2px solid #3f1719;
        padding-bottom: 14px;
        margin-bottom: 24px;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #fef2f2;
        margin: 0;
    }
    .section-badge {
        background: #e11d48;
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
    }

    /* KPI 카드 (레드 포인트) */
    .kpi-card {
        background: #1f0d11;
        border-left: 4px solid #ef4444;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    .kpi-label {
        font-size: 0.875rem;
        color: #fca5a5;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .kpi-sub {
        font-size: 0.85rem;
        color: #f87171;
        font-weight: 500;
    }

    /* 첨부 이미지 참고: 포스터 + 영화 상세정보 오버레이 포스터 카드 */
    .movie-info-card {
        background: linear-gradient(180deg, #2b0e14 0%, #17070a 100%);
        border: 1px solid #7f1d1d;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
    }
    .movie-card-header {
        color: #f87171;
        font-size: 1.5rem;
        font-weight: 800;
        border-bottom: 1px solid #450a0a;
        padding-bottom: 12px;
        margin-bottom: 16px;
    }
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
    }
    .info-item {
        background: #110507;
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 3px solid #dc2626;
    }
    .info-item label {
        color: #9ca3af;
        font-size: 0.8rem;
        display: block;
        margin-bottom: 2px;
    }
    .info-item value {
        color: #ffffff;
        font-weight: 700;
        font-size: 1.05rem;
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
    df["회당관객수"] = (df["audiCnt"] / df["showCnt"].replace(0, 1)).round(1)
    
    # 실시간 모멘텀 점수 계산 (레드 시네마 차트용)
    max_audi = df["audiCnt"].max() if df["audiCnt"].max() > 0 else 1
    max_per_show = df["회당관객수"].max() if df["회당관객수"].max() > 0 else 1
    df["모멘텀점수"] = (
        (df["audiCnt"] / max_audi * 50) + 
        (df["salesShare"] * 0.3) + 
        (df["회당관객수"] / max_per_show * 20)
    ).round(1)

    return df.sort_values(by="rank", ascending=True).reset_index(drop=True)


# ==========================================
# 4. 차트 렌더링 헬퍼 함수 (Red Cinema Theme)
# ==========================================
def apply_red_chart_style(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Pretendard, sans-serif", color="#f3f4f6", size=12),
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(gridcolor="#3f1719", zerolinecolor="#3f1719"),
        yaxis=dict(gridcolor="#3f1719", zerolinecolor="#3f1719"),
    )
    return fig


# ==========================================
# 5. 메인 애플리케이션
# ==========================================
def main():
    # -------------------------------------------------------------
    # [사이드바 Controls]
    # -------------------------------------------------------------
    st.sidebar.markdown("### 🍿 시네마 렌즈 필터")
    
    kst = pytz.timezone("Asia/Seoul")
    today_kst = datetime.datetime.now(kst).date()
    yesterday_kst = today_kst - datetime.timedelta(days=1)

    selected_date = st.sidebar.date_input(
        label="📅 조회 일자",
        value=yesterday_kst,
        max_value=yesterday_kst,
        min_value=datetime.date(2004, 1, 1),
        help="오늘 데이터는 미집계 상태이므로 어제 날짜까지 선택 가능합니다."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **🎬 KOBIS 시네마 센터**
    - **디자인 컨셉:** 스칼렛 레드 영화관 룩앤필
    - **데이터 출처:** 영화진흥위원회 KOBIS API
    """)

    # -------------------------------------------------------------
    # [Hero Banner - 시네마 레드]
    # -------------------------------------------------------------
    st.markdown(f"""
        <div class="hero-container">
            <div class="hero-title">🍿 KOBIS 시네마틱 박스오피스 인텔리전스</div>
            <div class="hero-subtitle">기준일자: <strong>{selected_date.strftime('%Y년 %m월 %d일')}</strong> | 극장가 실시간 흥행 스펙트럼</div>
        </div>
    """, unsafe_allow_html=True)

    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 API 인증키(KOBIS_KEY)가 설정되지 않았습니다.")
        st.warning("Streamlit Cloud 설정(Settings -> Secrets)에서 `KOBIS_KEY`를 추가하세요.")
        return

    api_key = st.secrets["KOBIS_KEY"]
    target_dt_str = selected_date.strftime("%Y%m%d")

    with st.spinner("극장가 흥행 빅데이터를 불러오는 중입니다..."):
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
    # [SECTION 1] 핵심 영화관 시장 지표 (KPI Overview)
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">🍿 실시간 극장가 하이라이트 (KPI Overview)</div>
                <div class="section-badge">CINEMA TODAY</div>
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
            <div class="kpi-card">
                <div class="kpi-label">👥 Top 10 총 관객수</div>
                <div class="kpi-value">{int(total_audi):,}명</div>
                <div class="kpi-sub">누적 관객 {int(df['audiAcc'].sum()):,}명</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">💰 Top 10 총 매출액</div>
                <div class="kpi-value">₩{int(total_sales / 100000000):,}억원</div>
                <div class="kpi-sub">일일 총 티켓 매출</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">🆕 신규 개봉 진입작</div>
                <div class="kpi-value">{new_movies}편</div>
                <div class="kpi-sub">차트인 신작 수</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [SECTION 2] 실시간 인기영화 흥행 분석 차트
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">🔥 실시간 흥행 모멘텀 & 매출 점유율 차트</div>
                <div class="section-badge">REAL-TIME CHART</div>
            </div>
    """, unsafe_allow_html=True)

    col_trend1, col_trend2 = st.columns([6, 4])

    with col_trend1:
        st.markdown("##### 🚀 영화별 실시간 흥행 모멘텀 지수")
        st.caption("※ 관객 수, 매출 점유율, 회당 관객 효율성을 결합한 시네마 파워 지수입니다.")
        
        # 레드 그라데이션 차트
        fig_momentum = px.bar(
            df.sort_values(by="모멘텀점수", ascending=True),
            x="모멘텀점수",
            y="디스플레이_제목",
            orientation="h",
            text="모멘텀점수",
            color="모멘텀점수",
            color_continuous_scale=["#450a0a", "#7f1d1d", "#dc2626", "#ef4444", "#fca5a5"]
        )
        fig_momentum.update_traces(texttemplate='%{text}점', textposition='outside')
        fig_momentum = apply_red_chart_style(fig_momentum)
        fig_momentum.update_layout(height=380, showlegend=False, xaxis_title="흥행 모멘텀 점수", yaxis_title="")
        st.plotly_chart(fig_momentum, use_container_width=True)

    with col_trend2:
        st.markdown("##### 🍕 극장가 매출 점유율 (Sales Share)")
        st.caption("상위 10개 영화의 매출 파이")
        
        fig_pie = px.pie(
            df,
            names="movieNm",
            values="salesShare",
            hole=0.45,
            color_discrete_sequence=["#7f1d1d", "#991b1b", "#b91c1c", "#dc2626", "#ef4444", "#f87171", "#fca5a5", "#fef2f2", "#450a0a", "#270708"]
        )
        fig_pie.update_traces(textinfo="percent+label", textposition="inside")
        fig_pie = apply_red_chart_style(fig_pie)
        fig_pie.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [SECTION 3] 영화별 정보 상세보기 (이미지 레이아웃 오버레이 양식 구현)
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">🎬 개별 영화 상세 스펙 카드</div>
                <div class="section-badge">MOVIE INFO CARD</div>
            </div>
    """, unsafe_allow_html=True)

    selected_movie_name = st.selectbox(
        "🔍 상세 정보를 조회할 영화를 선택하세요",
        options=df["movieNm"].tolist(),
        index=0
    )

    movie_info = df[df["movieNm"] == selected_movie_name].iloc[0]

    # 이미지 오버레이 스타일을 반영한 카드 인터페이스
    st.markdown(f"""
        <div class="movie-info-card">
            <div class="movie-card-header">
                {movie_info['디스플레이_제목']} <span style="font-size:1rem; color:#fca5a5; font-weight:normal;">({movie_info['openDt']} 개봉)</span>
            </div>
            <div class="info-grid">
                <div class="info-item">
                    <label>박스오피스 순위</label>
                    <value>{int(movie_info['rank'])}위 ({movie_info['순위변동']})</value>
                </div>
                <div class="info-item">
                    <label>일일 관객수</label>
                    <value>{int(movie_info['audiCnt']):,} 명</value>
                </div>
                <div class="info-item">
                    <label>누적 관객수</label>
                    <value>{int(movie_info['audiAcc']):,} 명</value>
                </div>
                <div class="info-item">
                    <label>스크린 점유수</label>
                    <value>{int(movie_info['scrnCnt']):,} 개</value>
                </div>
                <div class="info-item">
                    <label>일일 상영 횟수</label>
                    <value>{int(movie_info['showCnt']):,} 회</value>
                </div>
                <div class="info-item">
                    <label>회당 평균 관객수</label>
                    <value>{movie_info['회당관객수']} 명/회</value>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 📈 스크린 규모 대비 관객 수 효율성 비교 (Scatter Matrix)")
    st.caption("💡 상단에 위치할수록 스크린 대비 일일 관객 동원력이 뛰어난 영화입니다.")

    fig_scatter = px.scatter(
        df,
        x="scrnCnt",
        y="audiCnt",
        size="audiAcc",
        color="movieNm",
        hover_name="movieNm",
        text="movieNm",
        color_discrete_sequence=px.colors.sequential.Reds_r,
        labels={
            "scrnCnt": "스크린 수 (개)",
            "audiCnt": "일일 관객 수 (명)",
            "audiAcc": "누적 관객수"
        }
    )
    fig_scatter.update_traces(textposition='top center')
    fig_scatter = apply_red_chart_style(fig_scatter)
    fig_scatter.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [SECTION 4] 전체 순위 마스터 테이블
    # -------------------------------------------------------------
    st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <div class="section-title">📋 박스오피스 전체 순위 마스터 데이터</div>
                <div class="section-badge">FULL DATA</div>
            </div>
    """, unsafe_allow_html=True)

    search_query = st.text_input("🔍 표 내 영화 검색", "", placeholder="검색할 영화명을 입력하세요...")
    
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
        label="📥 데이터셋 CSV 다운로드",
        data=csv_bytes,
        file_name=f"kobis_red_cinema_boxoffice_{target_dt_str}.csv",
        mime="text/csv"
    )

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
