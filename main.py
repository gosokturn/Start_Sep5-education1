import datetime
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import pytz

# 1. 페이지 기본 설정 (제목, 레이아웃)
st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)


# 2. API 호출 함수 (결과를 1시간 동안 캐싱)
# Streamlit Cloud 서버 시계와 무관하게 한국 시간(Asia/Seoul) 기준으로 '어제' 날짜를 구합니다.
@st.cache_data(ttl=3600)
def fetch_daily_box_office(api_key: str, target_date_str: str):
    """
    KOBIS API를 호출하여 해당 날짜의 일별 박스오피스 데이터를 가져오는 함수입니다.
    ttl=3600 설정을 통해 같은 날짜에 대한 요청은 1시간(3600초) 동안 API를 재요청하지 않고 캐시 데이터를 사용합니다.
    """
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": api_key,
        "targetDt": target_date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        # HTTP 통신 에러 확인 (200 OK가 아닌 경우)
        if response.status_code != 200:
            return None, f"서버 통신 오류가 발생했습니다. (HTTP 상태 코드: {response.status_code})"
            
        data = response.json()
        
        # KOBIS API 특성: 인증키가 틀려도 200 OK가 오며, 대신 'faultInfo' 객체가 반환됨
        if "faultInfo" in data:
            message = data["faultInfo"].get("message", "알 수 없는 오류가 발생했습니다.")
            return None, f"KOBIS API 오류: {message}"
            
        # 정상적인 박스오피스 결과가 없는 경우
        box_office_result = data.get("boxOfficeResult", {})
        daily_list = box_office_result.get("dailyBoxOfficeList", [])
        
        if not daily_list:
            return None, "조회된 영화 목록이 없습니다. 해당 날짜의 데이터 집계가 아직 완료되지 않았을 수 있습니다."
            
        return daily_list, None

    except requests.exceptions.RequestException as e:
        return None, f"네트워크 요청 중 오류가 발생했습니다: {str(e)}"


# 3. 메인 앱 로직
def main():
    st.title("🎬 어제의 박스오피스 순위")
    
    # -------------------------------------------------------------
    # [설정 1] Secrets에서 API Key 가져오기
    # -------------------------------------------------------------
    if "KOBIS_KEY" not in st.secrets:
        st.error("🔑 API 인증키가 설정되지 않았습니다.")
        st.info("""
        **확인해 주세요:**
        1. Streamlit Cloud의 앱 설정에서 **Secrets** 메뉴를 엽니다.
        2. `KOBIS_KEY = "발급받은_인증키"` 형식으로 키를 등록했는지 확인해 주세요.
        """)
        return

    api_key = st.secrets["KOBIS_KEY"]

    # -------------------------------------------------------------
    # [설정 2] 한국 시간(KST) 기준 '어제' 날짜 계산하기
    # -------------------------------------------------------------
    kst = pytz.timezone("Asia/Seoul")
    today_kst = datetime.datetime.now(kst).date()
    yesterday_kst = today_kst - datetime.timedelta(days=1)
    
    # API 요청 형식 (YYYYMMDD) 및 화면 표시 형식 (YYYY년 MM월 DD일)
    target_dt_str = yesterday_kst.strftime("%Y%m%d")
    display_date_str = yesterday_kst.strftime("%Y년 %m월 %d일")
    
    st.caption(f"📅 기준일: {display_date_str} (한국 시간 기준 어제)")

    # -------------------------------------------------------------
    # [설정 3] API 데이터 불러오기 및 에러 처리
    # -------------------------------------------------------------
    with st.spinner("박스오피스 데이터를 불러오는 중입니다..."):
        raw_data, error_message = fetch_daily_box_office(api_key, target_dt_str)

    # 에러가 발생했거나 데이터가 없는 경우 안내 메시지 출력
    if error_message:
        st.error(f"⚠️ 데이터를 불러올 수 없습니다.")
        st.warning(f"**상세 원인:** {error_message}")
        st.info("""
        **확인 사항:**
        - `secrets.toml` 또는 Streamlit Secrets에 입력한 `KOBIS_KEY` 값이 정확한지 확인해 주세요.
        - KOBIS 개발자 센터에서 키가 정상적으로 활성화되었는지 확인해 주세요.
        - 일시적인 KOBIS 서버 점검 또는 네트워크 문제일 수 있으니 잠시 후 다시 시도해 주세요.
        """)
        return

    # -------------------------------------------------------------
    # [설정 4] 데이터 전처리 (문자열 -> 숫자 변환)
    # -------------------------------------------------------------
    df = pd.DataFrame(raw_data)

    # API 응답 결과가 전부 문자열로 넘어오므로 필요한 컬럼을 숫자형으로 변환합니다.
    numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt", "rankInten"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 순위 기준으로 정렬
    df = df.sort_values(by="rank", ascending=True)

    # -------------------------------------------------------------
    # [시각화 1] 1위 영화 핵심 지표 카드 (Metrics)
    # -------------------------------------------------------------
    top_movie = df.iloc[0]
    
    st.subheader(f"🥇 1위 영화: {top_movie['movieNm']}")
    
    col1, col2, col3 = st.columns(3)
    
    # 전날 대비 순위 증감 레이블 생성
    rank_inten = int(top_movie["rankInten"])
    if rank_inten > 0:
        delta_str = f"▲ {rank_inten}"
    elif rank_inten < 0:
        delta_str = f"▼ {abs(rank_inten)}"
    else:
        delta_str = "변동 없음"

    with col1:
        st.metric(
            label="어제 관객수",
            value=f"{int(top_movie['audiCnt']):,} 명",
            delta=delta_str
        )
        
    with col2:
        st.metric(
            label="누적 관객수",
            value=f"{int(top_movie['audiAcc']):,} 명"
        )
        
    with col3:
        st.metric(
            label="스크린수",
            value=f"{int(top_movie['scrnCnt']):,} 개"
        )

    st.markdown("---")

    # -------------------------------------------------------------
    # [시각화 2] 관객수 상위 5편 막대그래프 (Plotly)
    # -------------------------------------------------------------
    st.subheader("📊 관객수 상위 5개 영화")
    
    # 상위 5개 데이터 추출
    top5_df = df.head(5).copy()
    
    # 막대그래프 생성 (순위 순서대로 보이도록 categoryarray 설정)
    fig = px.bar(
        top5_df,
        x="movieNm",
        y="audiCnt",
        text="audiCnt",
        labels={"movieNm": "영화명", "audiCnt": "어제 관객수(명)"},
        color="audiCnt",
        color_continuous_scale="Blues"
    )
    
    # 그래프 스타일 조정 (수치 표시 포맷 및 레이아웃)
    fig.update_traces(texttemplate='%{text:,}명', textposition='outside')
    fig.update_layout(
        xaxis_title="",
        yaxis_title="관객수",
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------
    # [시각화 3] 전체 박스오피스 표 (Table)
    # -------------------------------------------------------------
    st.subheader("📋 전체 순위표")

    # 표에 보여줄 컬럼선택 및 이름 변경
    display_df = df[[
        "rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"
    ]].copy()

    display_df.columns = ["순위", "영화명", "개봉일", "어제 관객수", "누적 관객수", "스크린수"]

    # Streamlit 데이터프레임으로 출력 (숫자 세세한 포맷팅 적용)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "순위": st.column_config.NumberColumn(format="%d"),
            "어제 관객수": st.column_config.NumberColumn(format="%d 명"),
            "누적 관객수": st.column_config.NumberColumn(format="%d 명"),
            "스크린수": st.column_config.NumberColumn(format="%d 개"),
        }
    )


if __name__ == "__main__":
    main()
