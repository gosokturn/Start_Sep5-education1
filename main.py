# ===============================
# 그래프 4
# ===============================
st.header("그래프 4. 영화별 기간 일관객 TOP 10")

movie_summary = (
    df.groupby("영화명")
    .agg(
        기간_일관객=("일관객", "sum"),
        top10_일수=("날짜", "count")
    )
    .reset_index()
)

top10_movies = (
    movie_summary
    .sort_values("기간_일관객", ascending=False)
    .head(10)
    .sort_values("기간_일관객", ascending=True)
)

fig4 = px.bar(
    top10_movies,
    x="기간_일관객",
    y="영화명",
    orientation="h",
    title="이 기간 일관객 합계 TOP 10",
    text="기간_일관객",
    custom_data=["top10_일수"]
)

fig4.update_traces(
    hovertemplate=(
        "영화: %{y}<br>"
        "기간 일관객: %{x:,}명<br>"
        "10위권에 든 날수: %{customdata[0]}일"
        "<extra></extra>"
    )
)

fig4.update_layout(
    xaxis_title="기간 일관객 합계",
    yaxis_title="영화명"
)

fig4.update_xaxes(
    tickformat=","
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

st.info("**이 그래프로 알 수 있는 것:** (여기에 한 문장을 작성하면 됩니다.)")

st.divider()


# ===============================
# 그래프 5 (추가 예정)
# ===============================
st.header("그래프 5. (추가 예정)")
st.write("이 구역에 다음 그래프를 추가합니다.")

st.divider()
