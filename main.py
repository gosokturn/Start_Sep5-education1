import streamlit as st
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(
    page_title="실시간 극장가 대시보드",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 전체 HTML/CSS/JS 및 Plotly 차트 코드
html_code = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Plotly.js 차트 라이브러리 로드 -->
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    /* 글로벌 테마 및 리셋 */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }

    body {
      background-color: #0f172a;
      color: #f8fafc;
      min-height: 100vh;
      padding: 16px;
    }

    .dashboard-container {
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    /* 1. 최상단 헤더 박스 */
    .top-header {
      background: linear-gradient(135deg, #1e293b, #334155);
      border: 1px solid #475569;
      border-radius: 16px;
      padding: 20px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .top-header h1 {
      font-size: 1.4rem;
      font-weight: 700;
      color: #38bdf8;
      letter-spacing: -0.5px;
    }

    .top-header .status-tag {
      background-color: rgba(56, 189, 248, 0.1);
      color: #38bdf8;
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.85rem;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }

    /* 2. 실시간 극장가 하이라이트 (KPI Overview) */
    .kpi-overview-section {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }

    .kpi-card {
      background-color: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 14px 18px;
      transition: transform 0.2s, border-color 0.2s;
    }

    .kpi-card:hover {
      transform: translateY(-2px);
      border-color: #38bdf8;
    }

    .kpi-label {
      font-size: 0.8rem;
      color: #94a3b8;
      margin-bottom: 6px;
      display: block;
    }

    .kpi-value {
      font-size: 1.2rem;
      font-weight: 700;
      color: #f1f5f9;
    }

    .kpi-value .highlight {
      color: #f43f5e;
    }

    /* 3. 영화 검색창 */
    .search-section {
      width: 100%;
    }

    .search-bar-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }

    .search-input {
      width: 100%;
      height: 44px;
      background-color: #1e293b;
      border: 1px solid #334155;
      border-radius: 10px;
      padding: 0 48px 0 16px;
      color: #fff;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
    }

    .search-input:focus {
      border-color: #38bdf8;
    }

    .search-btn {
      position: absolute;
      right: 6px;
      background: #38bdf8;
      color: #0f172a;
      border: none;
      border-radius: 6px;
      padding: 8px 14px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
    }

    /* 4. 그래프 섹션 */
    .charts-section {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
      gap: 16px;
    }

    .chart-card {
      background-color: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 16px;
    }

    .chart-title {
      font-size: 1rem;
      font-weight: 600;
      color: #cbd5e1;
      margin-bottom: 12px;
    }

    /* 5. 영화 목록 섹션 */
    .content-section {
      margin-top: 10px;
    }

    .section-title {
      font-size: 1.1rem;
      margin-bottom: 12px;
      color: #cbd5e1;
    }

    .movie-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 16px;
    }

    .movie-card {
      background-color: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .movie-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.5);
      border-color: #38bdf8;
    }

    .poster-placeholder {
      width: 100%;
      height: 200px;
      background-color: #334155;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #64748b;
      font-size: 0.9rem;
    }

    .movie-info {
      padding: 12px;
    }

    .movie-title {
      font-size: 0.95rem;
      font-weight: 600;
      color: #f8fafc;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .movie-meta {
      font-size: 0.8rem;
      color: #94a3b8;
      margin-top: 4px;
      display: flex;
      justify-content: space-between;
    }

    /* 상세 정보 모달 */
    .modal-overlay {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(4px);
      z-index: 1000;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }

    .modal-content {
      background-color: #1e293b;
      border: 1px solid #475569;
      border-radius: 16px;
      max-width: 480px;
      width: 100%;
      padding: 24px;
      position: relative;
    }

    .close-btn {
      position: absolute;
      top: 16px;
      right: 16px;
      background: none;
      border: none;
      color: #94a3b8;
      font-size: 1.2rem;
      cursor: pointer;
    }

    .modal-title {
      font-size: 1.3rem;
      color: #38bdf8;
      margin-bottom: 4px;
    }

    .modal-genre {
      font-size: 0.85rem;
      color: #94a3b8;
    }

    .modal-body p {
      font-size: 0.9rem;
      line-height: 1.6;
      color: #cbd5e1;
      margin: 12px 0;
    }

    .modal-stats {
      display: flex;
      gap: 16px;
      background-color: #0f172a;
      padding: 12px;
      border-radius: 8px;
      font-size: 0.85rem;
    }

    .modal-stats div span {
      color: #94a3b8;
      display: block;
    }

    .modal-stats div strong {
      color: #f8fafc;
    }
  </style>
</head>
<body>

  <div class="dashboard-container">
    <!-- 1. 최상단 헤더 -->
    <header class="top-header">
      <div>
        <h1>CINE-INSIGHT</h1>
        <p style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">실시간 극장가 통합 분석 모니터</p>
      </div>
      <span class="status-tag">Live System</span>
    </header>

    <!-- 2. 실시간 극장가 하이라이트 (KPI Overview) -->
    <section class="kpi-overview-section">
      <div class="kpi-card">
        <span class="kpi-label">실시간 예매율 1위</span>
        <div class="kpi-value"><span class="highlight">파묘</span> (38.4%)</div>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">오늘의 일일 총 관객</span>
        <div class="kpi-value">248,102 명</div>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">전국 평균 좌석 점유율</span>
        <div class="kpi-value">31.2%</div>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">누적 매출액 (금일)</span>
        <div class="kpi-value">24.5 억원</div>
      </div>
    </section>

    <!-- 3. 영화 검색창 -->
    <section class="search-section">
      <div class="search-bar-wrapper">
        <input type="text" placeholder="영화 제목, 감독, 배우를 검색하세요..." class="search-input" />
        <button class="search-btn">검색</button>
      </div>
    </section>

    <!-- 4. 분석 그래프 영역 (추가된 부분) -->
    <section class="charts-section">
      <!-- 그래프 1: 예매율 & 점유율 비교 -->
      <div class="chart-card">
        <div class="chart-title">주요 상영작 예매율 및 좌석 점유율 (%)</div>
        <div id="chart-reservation" style="height: 280px;"></div>
      </div>

      <!-- 그래프 2: 시간대별 점유 추이 -->
      <div class="chart-card">
        <div class="chart-title">시간대별 관객 점유 추이</div>
        <div id="chart-hourly" style="height: 280px;"></div>
      </div>
    </section>

    <!-- 5. 영화 목록 섹션 -->
    <section class="content-section">
      <h2 class="section-title">현재 상영작 (클릭 시 상세정보)</h2>
      <div class="movie-grid">
        <div class="movie-card" onclick="openModal('파묘', '미스터리 / 공포', '9.2', '812만명', '기이한 병이 대대로 물려려오는 집안의 부탁을 받은 무당 화림과 봉길은 조상의 묫자리가 화근임을 알아채고 이장을 권한다.')">
          <div class="poster-placeholder">POSTER</div>
          <div class="movie-info">
            <div class="movie-title">파묘</div>
            <div class="movie-meta"><span>★ 9.2</span><span>예매율 38.4%</span></div>
          </div>
        </div>

        <div class="movie-card" onclick="openModal('듄: 파트2', 'SF / 액션', '9.0', '195만명', '황제의 음모로 멸문한 가문의 유일한 후계자 폴은 어머니와 함께 사막으로 도망쳐 아라키스의 프레멘들과 함께 복수를 준비한다.')">
          <div class="poster-placeholder">POSTER</div>
          <div class="movie-info">
            <div class="movie-title">듄: 파트2</div>
            <div class="movie-meta"><span>★ 9.0</span><span>예매율 24.1%</span></div>
          </div>
        </div>

        <div class="movie-card" onclick="openModal('윙카', '판타지 / 뮤지컬', '8.6', '340만명', '세계 최고의 Chocolatier가 되기 위해 모험을 떠나는 젊은 시절 위리 웡카의 판타지한 여정.')">
          <div class="poster-placeholder">POSTER</div>
          <div class="movie-info">
            <div class="movie-title">윙카</div>
            <div class="movie-meta"><span>★ 8.6</span><span>예매율 12.5%</span></div>
          </div>
        </div>

        <div class="movie-card" onclick="openModal('시민덕희', '드라마 / 범죄', '8.4', '170만명', '보이스피싱을 당한 평범한 시민 덕희에게 사기 친 조직원이 직접 제보를 해오며 벌어지는 통쾌한 추적극.')">
          <div class="poster-placeholder">POSTER</div>
          <div class="movie-info">
            <div class="movie-title">시민덕희</div>
            <div class="movie-meta"><span>★ 8.4</span><span>예매율 5.2%</span></div>
          </div>
        </div>
      </div>
    </section>
  </div>

  <!-- 영화 정보 팝업 모달 -->
  <div class="modal-overlay" id="movieModal" onclick="closeModalOutside(event)">
    <div class="modal-content">
      <button class="close-btn" onclick="closeModal()">&times;</button>
      <div class="modal-header">
        <h3 class="modal-title" id="modalTitle">영화 제목</h3>
        <span class="modal-genre" id="modalGenre">장르</span>
      </div>
      <div class="modal-body">
        <p id="modalDesc">영화 줄거리 설명이 이곳에 표시됩니다.</p>
        <div class="modal-stats">
          <div><span>관람객 평점</span><strong id="modalRating">0.0</strong></div>
          <div><span>누적 관객수</span><strong id="modalAudience">0명</strong></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // 모달 제어 함수
    function openModal(title, genre, rating, audience, desc) {
      document.getElementById('modalTitle').innerText = title;
      document.getElementById('modalGenre').innerText = genre;
      document.getElementById('modalRating').innerText = `★ ${rating}`;
      document.getElementById('modalAudience').innerText = audience;
      document.getElementById('modalDesc').innerText = desc;
      document.getElementById('movieModal').style.display = 'flex';
    }

    function closeModal() {
      document.getElementById('movieModal').style.display = 'none';
    }

    function closeModalOutside(event) {
      if (event.target.id === 'movieModal') {
        closeModal();
      }
    }

    // 그래프 1: 예매율 바 차트
    const reservationData = [{
      x: ['파묘', '듄: 파트2', '윙카', '시민덕희'],
      y: [38.4, 24.1, 12.5, 5.2],
      type: 'bar',
      marker: {
        color: ['#f43f5e', '#38bdf8', '#38bdf8', '#38bdf8']
      }
    }];

    const layout1 = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 30, r: 20, t: 10, b: 40 },
      font: { color: '#94a3b8' },
      xaxis: { gridcolor: '#334155' },
      yaxis: { gridcolor: '#334155' }
    };

    Plotly.newPlot('chart-reservation', reservationData, layout1, {responsive: true, displayModeBar: false});

    // 그래프 2: 시간대별 라인 차트
    const hourlyData = [
      {
        x: ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
        y: [12, 28, 45, 52, 78, 85, 60],
        type: 'scatter',
        mode: 'lines+markers',
        name: '파묘',
        line: { color: '#f43f5e', width: 3 }
      },
      {
        x: ['10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
        y: [8, 18, 30, 38, 55, 62, 40],
        type: 'scatter',
        mode: 'lines+markers',
        name: '듄: 파트2',
        line: { color: '#38bdf8', width: 2 }
      }
    ];

    const layout2 = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 30, r: 20, t: 10, b: 40 },
      font: { color: '#94a3b8' },
      xaxis: { gridcolor: '#334155' },
      yaxis: { gridcolor: '#334155' },
      legend: { orientation: 'h', y: 1.15 }
    };

    Plotly.newPlot('chart-hourly', hourlyData, layout2, {responsive: true, displayModeBar: false});
  </script>
</body>
</html>
"""

# Streamlit 화면 출력
components.html(html_code, height=1250, scrolling=True)
