import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    # 인코딩 예외 처리 (cp949 / euc-kr / utf-8)
    try:
        df = pd.read_csv(url, encoding="cp949")
    except Exception:
        try:
            df = pd.read_csv(url, encoding="euc-kr")
        except Exception:
            df = pd.read_csv(url, encoding="utf-8")
            
    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()
    
    # 컬럼명 유연성 대응 (단위 표시 포함)
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
    
    # 날짜 변환 및 연도 추출
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    df["연도"] = df["날짜"].dt.year
    
    # 수치형 변환
    for temp_col in ["평균기온", "최저기온", "최고기온"]:
        if temp_col in df.columns:
            df[temp_col] = pd.to_numeric(df[temp_col], errors="coerce")
            
    return df

# 데이터 로딩
try:
    df = load_data()
    data_loaded = True
except Exception as e:
    data_loaded = False
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

if data_loaded:
    # 연도별 평균 집계
    yearly_df = df.groupby("연도").agg({
        "평균기온": "mean",
        "최저기온": "mean",
        "최고기온": "mean"
    }).reset_index()

    # 관측 일수가 부족한 결측 연도(300일 미만) 제외 처리
    valid_years = df.groupby("연도")["평균기온"].count()
    valid_years = valid_years[valid_years >= 300].index
    yearly_df = yearly_df[yearly_df["연도"].isin(valid_years)].copy()
    
    # 10년 이동평균 계산
    yearly_df["10년_이동평균"] = yearly_df["평균기온"].rolling(window=10, min_periods=1).mean()

    # 사이드바 컨트롤
    st.sidebar.header("⚙️ 분석 및 시각화 설정")
    
    min_year = int(yearly_df["연도"].min())
    max_year = int(yearly_df["연도"].max())
    
    year_range = st.sidebar.slider(
        "조회 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    show_moving_avg = st.sidebar.checkbox("10년 이동평균선 표시", value=True)
    show_trendline = st.sidebar.checkbox("장기 추세선(Trendline) 표시", value=True)
    
    # 선택된 범위 데이터 필터링
    filtered_df = yearly_df[(yearly_df["연도"] >= year_range[0]) & (yearly_df["연도"] <= year_range[1])]

    # 헤더 섹션
    st.title("🌡️ 서울 100년 연평균 기온 변화 추이")
    st.markdown(
        f"**{min_year}년부터 {max_year}년까지** 서울 기상 관측 데이터를 바탕으로 지난 100여 년간의 연평균 기온 변화를 시각화한 앱입니다."
    )
    st.markdown("---")

    # 요약 지표 (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    
    avg_temp_all = filtered_df["평균기온"].mean()
    warmest_row = filtered_df.loc[filtered_df["평균기온"].idxmax()]
    coolest_row = filtered_df.loc[filtered_df["평균기온"].idxmin()]
    
    # 기간 내 기온 변화 경향 계산
    if len(filtered_df) > 1:
        start_temp = filtered_df["평균기온"].iloc[:5].mean()
        end_temp = filtered_df["평균기온"].iloc[-5:].mean()
        temp_diff = end_temp - start_temp
    else:
        temp_diff = 0.0

    col1.metric("선택 기간 평균 기온", f"{avg_temp_all:.1f} ℃")
    col2.metric("가장 따뜻했던 해", f"{int(warmest_row['연도'])}년", f"{warmest_row['평균기온']:.1f} ℃")
    col3.metric("가장 추웠던 해", f"{int(coolest_row['연도'])}년", f"{coolest_row['평균기온']:.1f} ℃")
    col4.metric("기간 내 온난화 경향", f"{temp_diff:+.1f} ℃")

    st.markdown("---")

    # Plotly 시각화 그래프
    st.subheader("📈 연평균 기온 변화 시각화")

    fig = go.Figure()

    # 1. 연평균 기온 선 그래프
    fig.add_trace(go.Scatter(
        x=filtered_df["연도"],
        y=filtered_df["평균기온"],
        mode="lines+markers",
        name="연평균 기온",
        line=dict(color="#E63946", width=2),
        marker=dict(size=5),
        hovertemplate="<b>%{x}년</b><br>연평균 기온: %{y:.2f}℃<extra></extra>"
    ))

    # 2. 10년 이동평균선
    if show_moving_avg:
        fig.add_trace(go.Scatter(
            x=filtered_df["연도"],
            y=filtered_df["10년_이동평균"],
            mode="lines",
            name="10년 이동평균",
            line=dict(color="#1D3557", width=3, dash="dash"),
            hovertemplate="<b>%{x}년 (10년 평균)</b><br>이동평균: %{y:.2f}℃<extra></extra>"
        ))

    # 3. 장기 추세선 (선형 회귀)
    if show_trendline and len(filtered_df) > 1:
        x_vals = filtered_df["연도"].values
        y_vals = filtered_df["평균기온"].values
        slope, intercept = np.polyfit(x_vals, y_vals, 1)
        trend_y = slope * x_vals + intercept

        fig.add_trace(go.Scatter(
            x=filtered_df["연도"],
            y=trend_y,
            mode="lines",
            name="장기 추세선",
            line=dict(color="#2A9D8F", width=2, dash="dot"),
            hovertemplate="<b>%{x}년 추세값</b><br>추세 기온: %{y:.2f}℃<extra></extra>"
        ))

    # Layout 설정
    fig.update_layout(
        title="서울 연평균 기온 추이 (Plotly)",
        xaxis_title="연도 (Year)",
        yaxis_title="기온 (℃)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=520
    )

    st.plotly_chart(fig, use_container_width=True)

    # 데이터 상세 정보 제공
    with st.expander("📋 연도별 데이터 데이터프레임 확인"):
        st.dataframe(
            filtered_df[["연도", "평균기온", "최저기온", "최고기온", "10년_이동평균"]].round(2),
            use_container_width=True
        )
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 일별 평균기온 분포 분석",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    # 인코딩 예외 처리 (cp949 / euc-kr / utf-8)
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
    
    # 날짜 변환 및 결측치 제거
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜", "평균기온"])
    
    # 수치형 변환
    for temp_col in ["평균기온", "최저기온", "최고기온"]:
        if temp_col in df.columns:
            df[temp_col] = pd.to_numeric(df[temp_col], errors="coerce")
            
    # 파생 변수 생성 (연도, 월, 계절)
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
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
    # 사이드바 설정
    st.sidebar.header("⚙️ 분석 및 시각화 설정")
    
    min_year = int(df["연도"].min())
    max_year = int(df["연도"].max())
    
    year_range = st.sidebar.slider(
        "조회 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    bin_size = st.sidebar.slider(
        "기온 구간 너비 (℃)",
        min_value=1,
        max_value=5,
        value=2,
        step=1
    )
    
    selected_seasons = st.sidebar.multiselect(
        "계절 선택",
        options=["봄", "여름", "가을", "겨울"],
        default=["봄", "여름", "가을", "겨울"]
    )
    
    # 데이터 필터링
    filtered_df = df[
        (df["연도"] >= year_range[0]) & 
        (df["연도"] <= year_range[1]) &
        (df["계절"].isin(selected_seasons))
    ]

    # Main Title
    st.title("📊 서울 일별 평균기온 분포 (히스토그램)")
    st.markdown(
        f"**{year_range[0]}년부터 {year_range[1]}년까지** 기록된 서울의 **일별 평균기온**이 어느 온도 구간에 몇 일이나 몰려 있는지 보여주는 히스토그램입니다."
    )
    st.markdown("---")

    # 핵심 요약 지표 (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    
    total_days = len(filtered_df)
    mean_temp = filtered_df["평균기온"].mean() if total_days > 0 else 0
    min_temp = filtered_df["평균기온"].min() if total_days > 0 else 0
    max_temp = filtered_df["평균기온"].max() if total_days > 0 else 0

    col1.metric("분석 대상 총 일수", f"{total_days:,} 일")
    col2.metric("기간 평균기온", f"{mean_temp:.1f} ℃")
    col3.metric("최저 일 평균기온", f"{min_temp:.1f} ℃")
    col4.metric("최고 일 평균기온", f"{max_temp:.1f} ℃")

    st.markdown("---")

    # 히스토그램 시각화
    st.subheader("📈 일별 평균기온 도수분포 그래프")

    if total_days > 0:
        fig = px.histogram(
            filtered_df,
            x="평균기온",
            color="계절" if len(selected_seasons) > 1 else None,
            color_discrete_map={
                "봄": "#2A9D8F",
                "여름": "#E63946",
                "가을": "#F4A261",
                "겨울": "#457B9D"
            },
            nbins=int((max_temp - min_temp) / bin_size),
            title="서울 일별 평균기온 히스토그램",
            labels={"평균기온": "일별 평균기온 (℃)", "count": "일수 (일)"},
            opacity=0.75,
            barmode="overlay"
        )

        fig.update_layout(
            xaxis_title="일별 평균기온 (℃)",
            yaxis_title="빈도 수 (일수)",
            template="plotly_white",
            hovermode="x unified",
            height=520,
            legend_title_text="계절"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

    # 상세 데이터 레이아웃
    with st.expander("📋 필터링된 일별 상세 데이터 확인"):
        st.dataframe(
            filtered_df[["날짜", "연도", "계절", "평균기온", "최저기온", "최고기온"]],
            use_container_width=True
        )
        import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 일별 평균기온 분포 분석",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    
    # 인코딩 예외 처리 (cp949 / euc-kr / utf-8)
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
    
    # 날짜 변환 및 결측치 제거
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜", "평균기온"])
    
    # 수치형 변환
    for temp_col in ["평균기온", "최저기온", "최고기온"]:
        if temp_col in df.columns:
            df[temp_col] = pd.to_numeric(df[temp_col], errors="coerce")
            
    # 파생 변수 생성 (연도, 월, 계절)
    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
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
    # 사이드바 설정
    st.sidebar.header("⚙️ 분석 및 시각화 설정")
    
    min_year = int(df["연도"].min())
    max_year = int(df["연도"].max())
    
    year_range = st.sidebar.slider(
        "조회 연도 범위 선택",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
    
    bin_size = st.sidebar.slider(
        "기온 구간 너비 (℃)",
        min_value=1,
        max_value=5,
        value=2,
        step=1
    )
    
    selected_seasons = st.sidebar.multiselect(
        "계절 선택",
        options=["봄", "여름", "가을", "겨울"],
        default=["봄", "여름", "가을", "겨울"]
    )
    
    # 데이터 필터링
    filtered_df = df[
        (df["연도"] >= year_range[0]) & 
        (df["연도"] <= year_range[1]) &
        (df["계절"].isin(selected_seasons))
    ]

    # Main Title
    st.title("📊 서울 일별 평균기온 분포 (히스토그램)")
    st.markdown(
        f"**{year_range[0]}년부터 {year_range[1]}년까지** 기록된 서울의 **일별 평균기온**이 어느 온도 구간에 몇 일이나 몰려 있는지 보여주는 히스토그램입니다."
    )
    st.markdown("---")

    # 핵심 요약 지표 (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    
    total_days = len(filtered_df)
    mean_temp = filtered_df["평균기온"].mean() if total_days > 0 else 0
    min_temp = filtered_df["평균기온"].min() if total_days > 0 else 0
    max_temp = filtered_df["평균기온"].max() if total_days > 0 else 0

    col1.metric("분석 대상 총 일수", f"{total_days:,} 일")
    col2.metric("기간 평균기온", f"{mean_temp:.1f} ℃")
    col3.metric("최저 일 평균기온", f"{min_temp:.1f} ℃")
    col4.metric("최고 일 평균기온", f"{max_temp:.1f} ℃")

    st.markdown("---")

    # 히스토그램 시각화
    st.subheader("📈 일별 평균기온 도수분포 그래프")

    if total_days > 0:
        fig = px.histogram(
            filtered_df,
            x="평균기온",
            color="계절" if len(selected_seasons) > 1 else None,
            color_discrete_map={
                "봄": "#2A9D8F",
                "여름": "#E63946",
                "가을": "#F4A261",
                "겨울": "#457B9D"
            },
            nbins=int((max_temp - min_temp) / bin_size),
            title="서울 일별 평균기온 히스토그램",
            labels={"평균기온": "일별 평균기온 (℃)", "count": "일수 (일)"},
            opacity=0.75,
            barmode="overlay"
        )

        fig.update_layout(
            xaxis_title="일별 평균기온 (℃)",
            yaxis_title="빈도 수 (일수)",
            template="plotly_white",
            hovermode="x unified",
            height=520,
            legend_title_text="계절"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

    # 상세 데이터 레이아웃
    with st.expander("📋 필터링된 일별 상세 데이터 확인"):
        st.dataframe(
            filtered_df[["날짜", "연도", "계절", "평균기온", "최저기온", "최고기온"]],
            use_container_width=True
        )
