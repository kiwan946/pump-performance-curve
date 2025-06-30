
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 펌프 성능 곡선 뷰어 (인터랙티브 완성형)")

uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="reference data")
        df.columns = df.columns.str.strip()

        if "토출양정" not in df.columns or "토출량" not in df.columns or "모델" not in df.columns:
            st.error("필수 열이 누락되었습니다. (토출양정, 토출량, 모델)")
            st.stop()

        df.rename(columns={
            "토출양정": "Total Head",
            "토출량": "Capacity",
            "모델": "Model"
        }, inplace=True)

        df["Series"] = df["Model"].str.extract(r"(XRF\d+)", expand=False)

        st.subheader("📋 백데이터 편집")
        edited_df = st.data_editor(df, num_rows="dynamic")

        st.sidebar.header("📐 보조선 추가")
        x_line = st.sidebar.number_input("수직 보조선 (Capacity)", value=0.0, step=10.0)
        y_line = st.sidebar.number_input("수평 보조선 (Head)", value=0.0, step=5.0)

        selected_series = st.sidebar.multiselect(
            "표시할 시리즈 선택",
            options=sorted(edited_df["Series"].dropna().unique()),
            default=sorted(edited_df["Series"].dropna().unique())
        )

        fig = go.Figure()

        for model in edited_df["Model"].unique():
            subset = edited_df[edited_df["Model"] == model]
            if subset.empty:
                continue  # 빈 데이터는 건너뜀
            if subset["Series"].iloc[0] not in selected_series:
                continue
            fig.add_trace(go.Scatter(
                x=subset["Capacity"],
                y=subset["Total Head"],
                mode="lines+markers+text",
                name=model,
                text=[model] + [""] * (len(subset) - 1),
                textposition="top left",
                hovertemplate="Model: %{text}<br>Capacity: %{x} L/min<br>Head: %{y} m"
            ))

        if x_line > 0:
            fig.add_vline(x=x_line, line_width=2, line_dash="dash", line_color="red")
        if y_line > 0:
            fig.add_hline(y=y_line, line_width=2, line_dash="dash", line_color="blue")

        fig.update_layout(
            xaxis_title="Capacity (L/min)",
            yaxis_title="Total Head (m)",
            height=900,
            width=1500,
            hovermode="closest",
            showlegend=True
        )
        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

        st.subheader("📈 성능 곡선 시각화")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"오류 발생: {e}")
