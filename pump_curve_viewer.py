import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Dooch XRL(F) 성능 곡선 뷰어", layout="wide")
st.title("📊 Dooch XRL(F) 성능 곡선 뷰어")

# 파일 업로드
uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation"])

    def plot_curves(df, model_col, x_col, y_col, selected_models):
        fig = go.Figure()
        for model in selected_models:
            model_df = df[df[model_col] == model].sort_values(by=x_col)
            fig.add_trace(go.Scatter(x=model_df[x_col], y=model_df[y_col],
                                     mode='lines+markers', name=str(model)))
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                          hovermode='closest', height=600)
        st.plotly_chart(fig, use_container_width=True)

    def process_and_plot(sheet_name, model_col, x_col, y_col, x_label, y_label, convert_columns=None):
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        if convert_columns:
            df = df.rename(columns=convert_columns)
        models = df[model_col].dropna().unique().tolist()
        selected_models = st.multiselect("모델 선택", models, default=models[:5])
        st.dataframe(df, use_container_width=True, height=300)
        if selected_models:
            plot_curves(df, model_col, x_col, y_col, selected_models)

    # Reference 탭
    with tabs[1]:
        st.subheader("📘 Reference Data")
        process_and_plot(
            sheet_name="reference data",
            model_col="모델",
            x_col="토출량",
            y_col="토출양정",
            x_label="Capacity",
            y_label="Total Head"
        )

    # Catalog 탭
    with tabs[2]:
        st.subheader("📙 Catalog Data")
        process_and_plot(
            sheet_name="catalog data",
            model_col="모델명",
            x_col="유량",
            y_col="토출양정&전양정",
            x_label="Capacity",
            y_label="Total Head",
            convert_columns={"유량": "토출량", "토출양정&전양정": "토출양정"}
        )

    # Deviation 탭
    with tabs[3]:
        st.subheader("📕 Deviation Data")
        process_and_plot(
            sheet_name="deviation data",
            model_col="모델명",
            x_col="유량",
            y_col="토출양정",
            x_label="Capacity",
            y_label="Total Head",
            convert_columns={"유량": "토출량"}
        )

    # Total 탭 (Series 무관하게 전체 비교)
    with tabs[0]:
        st.subheader("📗 Total Comparison View")
        ref_df = pd.read_excel(uploaded_file, sheet_name="reference data")
        cat_df = pd.read_excel(uploaded_file, sheet_name="catalog data")
        dev_df = pd.read_excel(uploaded_file, sheet_name="deviation data")

        cat_df = cat_df.rename(columns={"유량": "토출량", "토출양정&전양정": "토출양정"})
        dev_df = dev_df.rename(columns={"유량": "토출량"})

        ref_df['source'] = 'Reference'
        cat_df['source'] = 'Catalog'
        dev_df['source'] = 'Deviation'

        ref_df = ref_df.rename(columns={"모델": "Model"})
        cat_df = cat_df.rename(columns={"모델명": "Model"})
        dev_df = dev_df.rename(columns={"모델명": "Model"})

        combined = pd.concat([ref_df[['Model', '토출량', '토출양정', 'source']],
                              cat_df[['Model', '토출량', '토출양정', 'source']],
                              dev_df[['Model', '토출량', '토출양정', 'source']]],
                             ignore_index=True)

        models = combined['Model'].dropna().unique().tolist()
        selected_models = st.multiselect("모델 선택", models, default=models[:5])
        sources = st.multiselect("데이터 종류 선택", ['Reference', 'Catalog', 'Deviation'], default=['Reference'])

        df_filtered = combined[(combined['Model'].isin(selected_models)) &
                               (combined['source'].isin(sources))]

        st.dataframe(df_filtered, use_container_width=True, height=300)
        if not df_filtered.empty:
            fig = go.Figure()
            for model in selected_models:
                for src in sources:
                    temp = df_filtered[(df_filtered['Model'] == model) & (df_filtered['source'] == src)]
                    fig.add_trace(go.Scatter(x=temp['토출량'], y=temp['토출양정'],
                                             mode='lines+markers', name=f"{model} ({src})"))
            fig.update_layout(xaxis_title="Capacity", yaxis_title="Total Head",
                              hovermode='closest', height=600)
            st.plotly_chart(fig, use_container_width=True)

