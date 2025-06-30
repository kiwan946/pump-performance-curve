
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np

st.set_page_config(layout="wide")
st.title("🚀 Interactive Pump Performance Curve Viewer")

# 파일 업로드
uploaded_file = st.file_uploader("Upload Excel file with 'reference data' sheet", type=["xls", "xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="reference data")

    # 전처리
    df = df.rename(columns=lambda x: x.strip())
    df = df[df["모델"].notna()]
    df["Series"] = df["모델"].str.extract(r"(XRF\d+)")
    df["Impeller"] = df["모델"].str.extract(r"XRF\d+-(.*)")
    df["토출량(L/min)"] = df["Capacity"]
    df["토출양정"] = df["Total Head"]

    # 시리즈 선택
    series_options = df["Series"].dropna().unique()
    selected_series = st.selectbox("Select Series", sorted(series_options))

    df_series = df[df["Series"] == selected_series].copy()

    # 모델별로 시각화
    fig = go.Figure()

    for model, group in df_series.groupby("모델"):
        group_sorted = group.sort_values("토출량(L/min)")
        fig.add_trace(go.Scatter(
            x=group_sorted["토출량(L/min)"],
            y=group_sorted["토출양정"],
            mode="lines+markers",
            name=model,
            text=[f"{model}<br>Capacity: {x} L/min<br>Head: {y:.1f} m"
                  for x, y in zip(group_sorted["토출량(L/min)"], group_sorted["토출양정"])],
            hoverinfo="text"
        ))

    # 사용자 입력으로 보조선 추가
    st.sidebar.markdown("### ➕ Add Custom Guide Lines")
    xline = st.sidebar.number_input("Vertical Line (Capacity, L/min)", value=None, step=10.0, format="%.1f")
    yline = st.sidebar.number_input("Horizontal Line (Head, m)", value=None, step=5.0, format="%.1f")

    shapes = []
    if xline:
        shapes.append(dict(type="line", x0=xline, x1=xline, y0=0, y1=1, yref='paper',
                           line=dict(color="red", width=1, dash="dot")))
    if yline:
        shapes.append(dict(type="line", y0=yline, y1=yline, x0=0, x1=1, xref='paper',
                           line=dict(color="blue", width=1, dash="dot")))

    fig.update_layout(
        title=f"{selected_series} Performance Curves",
        xaxis_title="Capacity (L/min)",
        yaxis_title="Total Head (m)",
        hovermode="closest",
        height=800,
        width=1400,
        dragmode="pan",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=True),
        shapes=shapes
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📋 Edit Backdata for This Series")
    edited_df = st.data_editor(df_series[["모델", "Impeller", "토출량(L/min)", "토출양정"]], num_rows="dynamic")

    # 실시간 반영 그래프
    if st.checkbox("🔄 Update Graph with Edited Data"):
        fig2 = go.Figure()
        for model, group in edited_df.groupby("모델"):
            group_sorted = group.sort_values("토출량(L/min)")
            fig2.add_trace(go.Scatter(
                x=group_sorted["토출량(L/min)"],
                y=group_sorted["토출양정"],
                mode="lines+markers",
                name=model,
                text=[f"{model}<br>Capacity: {x} L/min<br>Head: {y:.1f} m"
                      for x, y in zip(group_sorted["토출량(L/min)"], group_sorted["토출양정"])],
                hoverinfo="text"
            ))
        fig2.update_layout(
            title=f"{selected_series} (Updated)",
            xaxis_title="Capacity (L/min)",
            yaxis_title="Total Head (m)",
            hovermode="closest",
            height=800,
            width=1400,
            dragmode="pan",
            xaxis=dict(showgrid=True),
            yaxis=dict(showgrid=True),
        )
        st.plotly_chart(fig2, use_container_width=True)
