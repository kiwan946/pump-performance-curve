import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Dooch XRL(F) 성능 고선 뷰어", layout="wide")
st.title(":bar_chart: Dooch XRL(F) 성능 고선 뷰어")

uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])

def get_best_match_column(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name in col:
                return col
    return None

def plot_lines(df, model_col, x_col, y_col, selected_models, source=None, linestyle=None):
    fig = go.Figure()
    for model in selected_models:
        model_df = df[df[model_col] == model].sort_values(by=x_col)
        line_style = dict(dash=linestyle) if linestyle else dict()
        label = model.replace("-\ud1b5\ucd9c양정", "").replace("-\ucc28도력", "")
        fig.add_trace(go.Scatter(
            x=model_df[x_col], y=model_df[y_col], mode='lines+markers+text',
            name=label, line=line_style,
            text=[label for _ in range(len(model_df))], textposition='top center',
            hoverinfo='text',
            hovertext=[f"Model: {label}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])]))
    fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                      hovermode='closest', height=600, showlegend=True)
    return fig

def add_polynomial_fit(fig, model_df, x_col, y_col, model, degree=3):
    X = model_df[[x_col]].values
    y = model_df[y_col].values
    poly = PolynomialFeatures(degree)
    X_poly = poly.fit_transform(X)
    model_fit = LinearRegression().fit(X_poly, y)
    x_range = np.linspace(X.min(), X.max(), 200).reshape(-1, 1)
    y_pred = model_fit.predict(poly.transform(x_range))
    fig.add_trace(go.Scatter(
        x=x_range.flatten(), y=y_pred, mode='lines',
        name=f"{model} 예측고선", line=dict(dash='solid', color='gray')))

def process_and_plot(sheet_name, point_only=False, catalog_style=False, ai_mode=False, total_mode=False, tab_id="default"):
    df = None
    try:
        df = pd.read_excel(uploaded_file, sheet_name="reference data")
    except:
        if ai_mode or total_mode:
            st.warning("Reference 데이터를 불러오지 않았습니다.")
        return

    if df is not None:
        model_col = get_best_match_column(df, ["\ubaa8\ub378", "\ubaa8\ub378\uba85", "Model"])
        x_col = get_best_match_column(df, ["\ud1b5\ucd9c량", "\uc720량"])
        y_col = get_best_match_column(df, ["\ud1b5\ucd9c양정", "\uc804양정"])
        y2_col = get_best_match_column(df, ["\ucc28도력"])

        if not model_col or not x_col or not y_col:
            st.error("필수 컬럼(Model, \ud1b5\ucd9c량, \ud1b5\ucd9c양정)을 \ucc3e을 수 없습니다.")
            return

        df['Series'] = df[model_col].astype(str).str.extract(r"(XR[\w\-]+)")

        unique_key = tab_id.replace(" ", "_").lower()
        col1, col2 = st.columns([1, 3])
        with col1:
            series_options = df['Series'].dropna().unique().tolist()
            selected_series = st.multiselect("\uc2dc\ub9ac즈 \uc120\ud0dd (\ub2e4중 \uc120\ud0dd \uac00\ub2a5)", options=series_options, key=f"series_{unique_key}")

        if selected_series:
            model_options = df[df['Series'].isin(selected_series)][model_col].dropna().unique().tolist()
        else:
            model_options = []

        with col2:
            selected_models = st.multiselect("\ubaa8\ub378 \uc120\ud0dd (\ub2e4중 \uc120\ud0dd \uac00\ub2a5)", options=model_options, key=f"models_{unique_key}")

        filtered_df = df[df[model_col].isin(selected_models)] if selected_models else pd.DataFrame()
    else:
        selected_models = []
        model_col = x_col = y_col = y2_col = None
        filtered_df = pd.DataFrame()

    if not filtered_df.empty:
        st.markdown("#### Q-H (\ud1b5\ucd9c양정) \uc131능고선")
        fig1 = plot_lines(filtered_df, model_col, x_col, y_col, selected_models, source=sheet_name.title())

        if total_mode:
            for sheet, label, dash_style in zip([
                "catalog data", "deviation data"
            ], ["Catalog", "Deviation"], ["dash", "dot"]):
                show = st.checkbox(f"{label} \ub370이터 \ud45c시", value=False, key=f"{sheet}_show_{unique_key}")
                if show:
                    try:
                        extra_df = pd.read_excel(uploaded_file, sheet_name=sheet)
                        extra_df = extra_df[[model_col, x_col, y_col]].dropna()
                        model_df = extra_df[extra_df[model_col].isin(selected_models)].sort_values(by=x_col)
                        fig1.add_trace(go.Scatter(
                            x=model_df[x_col], y=model_df[y_col],
                            mode='lines+markers', name=f"{label}",
                            line=dict(dash=dash_style)))
                    except:
                        st.warning(f"{label} \ub370이터를 \ubd88러오지 \ubabb했습니다.")

        if ai_mode or total_mode:
            for model in selected_models:
                model_df = filtered_df[filtered_df[model_col] == model]
                add_polynomial_fit(fig1, model_df, x_col, y_col, model)

        st.plotly_chart(fig1, use_container_width=True)

        if y2_col:
            st.markdown("#### Q-\ucc28도력 \uc131능고선")
            fig2 = plot_lines(filtered_df, model_col, x_col, y2_col, selected_models, source=sheet_name.title())
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### \ub370이터 \ud14c이블")
        st.dataframe(filtered_df, use_container_width=True, height=300)

if uploaded_file:
    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation", "AI \ubc30\uce58"])

    with tabs[0]:
        st.subheader(":bar_chart: Total - \ud1b5합 \uace0선 \ubd84석")
        st.info("Reference \ub370이터를 \uae30반으로 \ubd84석합니다.")
        process_and_plot("reference data", total_mode=True, tab_id="total")

    with tabs[1]:
        st.subheader(":blue_book: Reference Data")
        process_and_plot("reference data", tab_id="reference")

    with tabs[2]:
        st.subheader(":orange_book: Catalog Data")
        process_and_plot("catalog data", catalog_style=True, tab_id="catalog")

    with tabs[3]:
        st.subheader(":red_book: Deviation Data")
        process_and_plot("deviation data", point_only=True, tab_id="deviation")

    with tabs[4]:
        st.subheader(":robot_face: AI \uc131능 \uc608측")
        process_and_plot("reference data", ai_mode=True, tab_id="ai")
