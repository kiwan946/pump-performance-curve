
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 Interactive Pump Performance Curve Viewer")

uploaded_file = st.file_uploader("Upload Excel file with 'reference data' sheet", type=["xlsx", "xlsm"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name='reference data')
        df.columns = df.columns.str.strip()  # 공백 제거

        # 열 이름 자동 매핑
        column_map = {
            '토출량': 'Capacity',
            '토출양정': 'Total Head',
            '전양정': 'Total Head',
            '모델': 'Model'
        }
        df.rename(columns=column_map, inplace=True)

        # 필수 열 존재 확인
        if not {'Capacity', 'Total Head', 'Model'}.issubset(df.columns):
            st.error("필수 열(Capacity, Total Head, Model)이 누락되었습니다.")
        else:
            fig = go.Figure()
            for model in df['Model'].unique():
                subset = df[df['Model'] == model]
                fig.add_trace(go.Scatter(
                    x=subset['Capacity'],
                    y=subset['Total Head'],
                    mode='lines+markers+text',
                    name=model,
                    text=[model] + [""]*(len(subset)-1),
                    textposition='top left',
                    hovertemplate='Model: %{text}<br>Capacity: %{x} L/min<br>Head: %{y} m'
                ))

            fig.update_layout(
                xaxis_title='Capacity (L/min)',
                yaxis_title='Total Head (m)',
                title='Pump Performance Curves',
                height=800,
                showlegend=True
            )
            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
