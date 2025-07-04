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

    def plot_lines(df, model_col, x_col, y_col, selected_models, source=None):
        fig = go.Figure()
        for model in selected_models:
            model_df = df[df[model_col] == model].sort_values(by=x_col)
            line_style = dict(dash='dot') if source == 'Catalog' else dict()
            fig.add_trace(go.Scatter(
                x=model_df[x_col], y=model_df[y_col], mode='lines+markers',
                name=f"{model}", line=line_style,
                text=[f"Model: {model}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])],
                hoverinfo='text'))
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                          hovermode='closest', height=600)
        st.plotly_chart(fig, use_container_width=True)

    def plot_points(df, model_col, x_col, y_col, selected_models):
        fig = go.Figure()
        for model in selected_models:
            model_df = df[df[model_col] == model]
            fig.add_trace(go.Scatter(
                x=model_df[x_col], y=model_df[y_col], mode='markers',
                name=f"{model}",
                text=[f"Model: {model}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])],
                hoverinfo='text'))
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                          hovermode='closest', height=600)
        st.plotly_chart(fig, use_container_width=True)

    def process_and_plot(sheet_name, point_only=False):
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

        model_col = get_best_match_column(df, ["모델", "모델명", "Model"])
        x_col = get_best_match_column(df, ["토출량", "유량"])
        y_col = get_best_match_column(df, ["토출양정", "전양정"])
        y2_col = get_best_match_column(df, ["축동력"])

        if not model_col or not x_col or not y_col:
            st.error("필수 컬럼(Model, 토출량, 토출양정)을 찾을 수 없습니다.")
            return

        df['Series'] = df[model_col].astype(str).str.extract(r"(XRF\d+)")

        mode = st.selectbox(f"{sheet_name}_분류 기준 선택", ["시리즈별", "모델별"], key=sheet_name+"_mode")

        if mode == "시리즈별":
            options = df['Series'].dropna().unique().tolist()
            selected = st.multiselect(f"{sheet_name}_시리즈 선택", options, default=options, key=sheet_name+'_series')
            filtered_df = df[df['Series'].isin(selected)]
        else:
            options = df[model_col].dropna().unique().tolist()
            selected = st.multiselect(f"{sheet_name}_모델 선택", options, default=options[:5], key=sheet_name+'_models')
            filtered_df = df[df[model_col].isin(selected)]

        selected_models = filtered_df[model_col].dropna().unique().tolist()

        if selected_models:
            if point_only:
                plot_points(filtered_df, model_col, x_col, y_col, selected_models)
                if y2_col:
                    plot_points(filtered_df, model_col, x_col, y2_col, selected_models)
            else:
                plot_lines(filtered_df, model_col, x_col, y_col, selected_models, source=sheet_name.title())
                if y2_col:
                    plot_lines(filtered_df, model_col, x_col, y2_col, selected_models, source=sheet_name.title())

        st.dataframe(filtered_df, use_container_width=True, height=300)

    # Reference 탭
    with tabs[1]:
        st.subheader("📘 Reference Data")
        process_and_plot("reference data")

    # Catalog 탭
    with tabs[2]:
        st.subheader("📙 Catalog Data")
        process_and_plot("catalog data")

    # Deviation 탭
    with tabs[3]:
        st.subheader("📕 Deviation Data")
        process_and_plot("deviation data", point_only=True)

    # Total 탭은 이후 확장 가능
