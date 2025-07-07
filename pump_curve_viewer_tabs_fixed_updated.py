import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Dooch XRL(F) 성능 곡선 뷰어", layout="wide")
st.title("📊 Dooch XRL(F) 성능 곡선 뷰어")

uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])

def get_best_match_column(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name in col:
                return col
    return None

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation"])

    def plot_lines(fig, df, model_col, x_col, y_col, selected_models, style):
        for model in selected_models:
            model_df = df[df[model_col] == model].sort_values(by=x_col)
            fig.add_trace(go.Scatter(
                x=model_df[x_col], y=model_df[y_col], mode='lines+markers',
                name=f"{model}", line=style,
                text=[f"Model: {model}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])],
                hoverinfo='text'))

    def plot_points(fig, df, model_col, x_col, y_col, selected_models):
        for model in selected_models:
            model_df = df[df[model_col] == model]
            fig.add_trace(go.Scatter(
                x=model_df[x_col], y=model_df[y_col], mode='markers',
                name=f"{model}",
                text=[f"Model: {model}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])],
                hoverinfo='text'))

    def process_and_plot(sheet_name, point_only=False, show_plot=True):
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

        model_col = get_best_match_column(df, ["모델", "모델명", "Model"])
        x_col = get_best_match_column(df, ["토출량", "유량"])
        y_col = get_best_match_column(df, ["토출양정", "전양정"])
        y2_col = get_best_match_column(df, ["축동력"])

        if not model_col or not x_col or not y_col:
            st.error("필수 컬럼(Model, 토출량, 토출양정)을 찾을 수 없습니다.")
            return pd.DataFrame(), model_col, x_col, y_col, y2_col

        df['Series'] = df[model_col].astype(str).str.extract(r"(XRF\d+)")

        sorted_series = [f"XRF{i}" for i in [3, 5, 10, 15, 20, 32, 45, 64, 95, 125, 155, 185, 215, 255]]

        mode = st.selectbox(f"{sheet_name}_분류 기준 선택", ["시리즈별", "모델별"], key=sheet_name+"_mode")

        if mode == "시리즈별":
            options = sorted([s for s in df['Series'].dropna().unique().tolist() if s in sorted_series],
                             key=lambda x: sorted_series.index(x))
            selected_series = st.multiselect(f"{sheet_name}_시리즈 선택", options, key=sheet_name+'_series')
            filtered_df = df[df['Series'].isin(selected_series)]
        else:
            options = df[model_col].dropna().unique().tolist()
            selected_models = st.multiselect(f"{sheet_name}_모델 선택", options, key=sheet_name+'_models')
            filtered_df = df[df[model_col].isin(selected_models)]

        selected_models = filtered_df[model_col].dropna().unique().tolist()
        return filtered_df, model_col, x_col, y_col, y2_col

    # Total 탭
    with tabs[0]:
        st.subheader("📊 Total - 통합 곡선 분석")
        show_reference = st.checkbox("Reference Data 표시", value=True)
        show_catalog = st.checkbox("Catalog Data 표시", value=False)
        show_deviation = st.checkbox("Deviation Data 표시", value=False)

        fig_qh = go.Figure()
        fig_kw = go.Figure()

        if show_reference:
            df, model_col, x_col, y_col, y2_col = process_and_plot("reference data", show_plot=False)
            selected_models = df[model_col].dropna().unique().tolist()
            plot_lines(fig_qh, df, model_col, x_col, y_col, selected_models, style=dict(dash='solid'))
            if y2_col:
                plot_lines(fig_kw, df, model_col, x_col, y2_col, selected_models, style=dict(dash='solid'))

        if show_catalog:
            df, model_col, x_col, y_col, y2_col = process_and_plot("catalog data", show_plot=False)
            selected_models = df[model_col].dropna().unique().tolist()
            plot_lines(fig_qh, df, model_col, x_col, y_col, selected_models, style=dict(dash='dash'))
            if y2_col:
                plot_lines(fig_kw, df, model_col, x_col, y2_col, selected_models, style=dict(dash='dash'))

        if show_deviation:
            df, model_col, x_col, y_col, y2_col = process_and_plot("deviation data", point_only=True, show_plot=False)
            selected_models = df[model_col].dropna().unique().tolist()
            plot_points(fig_qh, df, model_col, x_col, y_col, selected_models)
            if y2_col:
                plot_points(fig_kw, df, model_col, x_col, y2_col, selected_models)

        fig_qh.update_layout(title="Q-H (토출양정) 성능곡선")
        fig_kw.update_layout(title="Q-축동력 성능곡선")
        st.plotly_chart(fig_qh, use_container_width=True)
        st.plotly_chart(fig_kw, use_container_width=True)

    # Reference 탭
    with tabs[1]:
        st.subheader("📘 Reference Data")
        df, model_col, x_col, y_col, y2_col = process_and_plot("reference data")

    # Catalog 탭
    with tabs[2]:
        st.subheader("📙 Catalog Data")
        df, model_col, x_col, y_col, y2_col = process_and_plot("catalog data")

    # Deviation 탭
    with tabs[3]:
        st.subheader("📕 Deviation Data")
        df, model_col, x_col, y_col, y2_col = process_and_plot("deviation data", point_only=True)
