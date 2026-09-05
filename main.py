import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. 페이지 기본 설정 (단 한 번만 실행)
st.set_page_config(
    page_title="서울 기온 데이터 종합 분석 Dashboard",
    page_icon="🌡️",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    # 인코딩 예외 처리
    try:
        df = pd.read_csv(url, encoding="cp949")
    except Exception:
        try:
            df = pd.read_csv(url, encoding="euc-kr")
        except Exception:
            df = pd.read_csv(url, encoding="utf-8")
            
    # 컬럼명 공백 제거 및 대표 매핑
    df.columns = df.columns.str.strip()
    
    col_map = {}
    for col in df.columns:
        if "날짜" in col:
            col_map[col] = "날짜"
        elif "지점" in col:
            col_map[col] = "지점"
        elif "평균" in col:
            col_map[col] = "평균기온"
        elif "최저" in col:
            col_map[col] = "최저기온"
        elif "최고" in col:
            col_map[col] = "최고기온"
            
    df = df.rename(columns=col_map)
    
    # 날짜 및 수치형 데이터 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    
    for temp_col in ["평균기온", "최저기온", "최고기온"]:
        if temp_col in df.columns:
            df[temp_col] = pd.to_numeric(df[temp_col], errors="coerce")
            
    # 파생 변수 생성
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일교차"] = df["최고기온"] - df["최저기온"]
    df["계절"] = df["월"].map({
        12: "겨울", 1: "겨울", 2: "겨울",
        3: "봄", 4: "봄", 5: "봄",
        6: "여름", 7: "여름", 8: "여름",
        9: "가을", 10: "가을", 11: "가을"
    })
    
    return df

# 데이터 로딩
try:
    df = load_data()
    data_loaded = True
except Exception as e:
    data_loaded = False
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

if data_loaded:
    # 3. 사이드바 - 공통 분석 조건 설정
    st.sidebar.header("⚙️ 분석 조건 설정")
    
    min_year = int(df["연도"].min())
    max_year = int(df["연도"].max())
    
    # 고유 key 값을 부여하여 Element ID 충돌 방지
    year_range = st.sidebar.slider(
        "조회 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        key="main_year_range_slider"
    )
    
    selected_seasons = st.sidebar.multiselect(
        "계절 선택 (분포 및 상관관계 분석용)",
        options=["봄", "여름", "가을", "겨울"],
        default=["봄", "여름", "가을", "겨울"],
        key="main_season_multiselect"
    )

    # 기본 필터링 데이터
    filtered_df = df[
        (df["연도"] >= year_range[0]) & 
        (df["연도"] <= year_range[1]) &
        (df["계절"].isin(selected_seasons))
    ]

    st.title("🌡️ 서울 100년 기온 데이터 종합 분석")
    st.markdown("---")

    # 4. 탭 구성 (기능별 분리)
    tab1, tab2, tab3 = st.tabs([
        "📈 연평균 기온 변화 추이", 
        "📊 일별 평균기온 분포 (히스토그램)", 
        "📉 최저 vs 최고기온 상관관계"
    ])

    # ==========================================
    # TAB 1: 연평균 기온 변화 추이
    # ==========================================
    with tab1:
        st.header("📈 연평균 기온 변화 추이")
        
        # 연도별 집계
        yearly_df = df[(df["연도"] >= year_range[0]) & (df["연도"] <= year_range[1])].groupby("연도").agg({
            "평균기온": "mean",
            "최저기온": "mean",
            "최고기온": "mean"
        }).reset_index()

        valid_years = df.groupby("연도")["평균기온"].count()
        valid_years = valid_years[valid_years >= 300].index
        yearly_df = yearly_df[yearly_df["연도"].isin(valid_years)].copy()
        
        yearly_df["10년_이동평균"] = yearly_df["평균기온"].rolling(window=10, min_periods=1).mean()

        col1_1, col1_2 = st.columns(2)
        with col1_1:
            show_moving_avg = st.checkbox("10년 이동평균선 표시", value=True, key="tab1_moving_avg")
        with col1_2:
            show_trendline = st.checkbox("장기 추세선(Trendline) 표시", value=True, key="tab1_trendline")

        if len(yearly_df) > 0:
            c1, c2, c3, c4 = st.columns(4)
            avg_temp_all = yearly_df["평균기온"].mean()
            warmest_row = yearly_df.loc[yearly_df["평균기온"].idxmax()]
            coolest_row = yearly_df.loc[yearly_df["평균기온"].idxmin()]
            
            temp_diff = (yearly_df["평균기온"].iloc[-5:].mean() - yearly_df["평균기온"].iloc[:5].mean()) if len(yearly_df) >= 5 else 0.0

            c1.metric("선택 기간 평균 기온", f"{avg_temp_all:.1f} ℃")
            c2.metric("가장 따뜻했던 해", f"{int(warmest_row['연도'])}년", f"{warmest_row['평균기온']:.1f} ℃")
            c3.metric("가장 추웠던 해", f"{int(coolest_row['연도'])}년", f"{coolest_row['평균기온']:.1f} ℃")
            c4.metric("기간 내 온난화 경향", f"{temp_diff:+.1f} ℃")

            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=yearly_df["연도"], y=yearly_df["평균기온"],
                mode="lines+markers", name="연평균 기온",
                line=dict(color="#E63946", width=2), marker=dict(size=5)
            ))

            if show_moving_avg:
                fig1.add_trace(go.Scatter(
                    x=yearly_df["연도"], y=yearly_df["10년_이동평균"],
                    mode="lines", name="10년 이동평균",
                    line=dict(color="#1D3557", width=3, dash="dash")
                ))

            if show_trendline and len(yearly_df) > 1:
                x_vals = yearly_df["연도"].values
                y_vals = yearly_df["평균기온"].values
                slope, intercept = np.polyfit(x_vals, y_vals, 1)
                trend_y = slope * x_vals + intercept
                fig1.add_trace(go.Scatter(
                    x=yearly_df["연도"], y=trend_y,
                    mode="lines", name="장기 추세선",
                    line=dict(color="#2A9D8F", width=2, dash="dot")
                ))

            fig1.update_layout(
                xaxis_title="연도", yaxis_title="기온 (℃)",
                template="plotly_white", hovermode="x unified", height=500
            )
            st.plotly_chart(fig1, use_container_width=True)

    # ==========================================
    # TAB 2: 일별 평균기온 분포 (히스토그램)
    # ==========================================
    with tab2:
        st.header("📊 일별 평균기온 분포 (히스토그램)")
        
        bin_size = st.slider("기온 구간 너비 (℃)", min_value=1, max_value=5, value=2, step=1, key="tab2_bin_size")

        total_days = len(filtered_df)
        if total_days > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("분석 대상 총 일수", f"{total_days:,} 일")
            c2.metric("기간 평균기온", f"{filtered_df['평균기온'].mean():.1f} ℃")
            c3.metric("최저 일 평균기온", f"{filtered_df['평균기온'].min():.1f} ℃")
            c4.metric("최고 일 평균기온", f"{filtered_df['평균기온'].max():.1f} ℃")

            fig2 = px.histogram(
                filtered_df, x="평균기온",
                color="계절" if len(selected_seasons) > 1 else None,
                color_discrete_map={"봄": "#2A9D8F", "여름": "#E63946", "가을": "#F4A261", "겨울": "#457B9D"},
                nbins=int((filtered_df["평균기온"].max() - filtered_df["평균기온"].min()) / bin_size),
                labels={"평균기온": "일별 평균기온 (℃)", "count": "일수 (일)"},
                opacity=0.75, barmode="overlay"
            )
            fig2.update_layout(template="plotly_white", height=500)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

    # ==========================================
    # TAB 3: 최저 vs 최고기온 상관관계
    # ==========================================
    with tab3:
        st.header("📉 최저기온 vs 최고기온 상관관계 분석")

        c_col1, c_col2 = st.columns(2)
        with c_col1:
            show_ols = st.checkbox("회귀 추세선(Trendline) 표시", value=True, key="tab3_ols")
        with c_col2:
            sample_size = st.slider("표시할 데이터 샘플 개수 (0 = 전체)", 0, 10000, 3000, step=1000, key="tab3_sample")

        scatter_df = filtered_df.dropna(subset=["최저기온", "최고기온"])
        
        if sample_size > 0 and len(scatter_df) > sample_size:
            plot_df = scatter_df.sample(n=sample_size, random_state=42)
        else:
            plot_df = scatter_df.copy()

        if len(scatter_df) > 0:
            c1, c2, c3, c4 = st.columns(4)
            corr = scatter_df["최저기온"].corr(scatter_df["최고기온"])
            max_range_row = scatter_df.loc[scatter_df["일교차"].idxmax()]

            c1.metric("분석 대상 일수", f"{len(scatter_df):,} 일")
            c2.metric("상관계수", f"{corr:.3f}")
            c3.metric("평균 일교차", f"{scatter_df['일교차'].mean():.1f} ℃")
            c4.metric("최대 일교차 기록", f"{max_range_row['일교차']:.1f} ℃", f"{max_range_row['날짜'].strftime('%Y-%m-%d')}")

            fig3 = px.scatter(
                plot_df, x="최저기온", y="최고기온", color="계절",
                color_discrete_map={"봄": "#2A9D8F", "여름": "#E63946", "가을": "#F4A261", "겨울": "#457B9D"},
                hover_data=["날짜", "일교차"],
                trendline="ols" if show_ols else None,
                opacity=0.6
            )
            fig3.update_layout(template="plotly_white", height=500)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

    # 상세 데이터 확인 (공통)
    with st.expander("📋 상세 데이터 확인"):
        st.dataframe(filtered_df[["날짜", "연도", "계절", "평균기온", "최저기온", "최고기온", "일교차"]], use_container_width=True)
