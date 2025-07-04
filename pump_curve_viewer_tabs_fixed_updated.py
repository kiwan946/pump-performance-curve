import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Dooch XRL(F) 성능 곡선 뷰어", layout="wide")
st.title("📊 Dooch XRL(F) 성능 곡선 뷰어")

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
        label = model.replace("-토출양정", "").replace("-축동력", "")
        fig.add_trace(go.Scatter(
            x=model_df[x_col], y=model_df[y_col], mode='lines+markers+text',
            name=label, line=line_style,
            text=[label for _ in range(len(model_df))], textposition='top center',
            hoverinfo='text',
            hovertext=[f"Model: {label}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])]))
    fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                      hovermode='closest', height=600, showlegend=True)
    return fig

def plot_points(df, model_col, x_col, y_col, selected_models):
    fig = go.Figure()
    for model in selected_models:
        model_df = df[df[model_col] == model]
        label = model.replace("-토출양정", "").replace("-축동력", "")
        fig.add_trace(go.Scatter(
            x=model_df[x_col], y=model_df[y_col], mode='markers+text',
            name=label,
            text=[label for _ in range(len(model_df))], textposition='top center',
            hoverinfo='text',
            hovertext=[f"Model: {label}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])]))
    fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                      hovermode='closest', height=600)
    return fig

def process_and_plot(sheet_name, point_only=False, catalog_style=False):
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

    model_col = get_best_match_column(df, ["모델", "모델명", "Model"])
    x_col = get_best_match_column(df, ["토출량", "유량"])
    y_col = get_best_match_column(df, ["토출양정", "전양정"])
    y2_col = get_best_match_column(df, ["축동력"])

    if not model_col or not x_col or not y_col:
        st.error("필수 컬럼(Model, 토출량, 토출양정)을 찾을 수 없습니다.")
        return

    df['Series'] = df[model_col].astype(str).str.extract(r"(XRF\d+)")

    col_filter1, col_filter2 = st.columns([1, 3])
    with col_filter1:
        mode = st.selectbox(f"{sheet_name} - 분류 기준", ["시리즈별", "모델별"], key=f"{sheet_name}_mode")

    if mode == "시리즈별":
        options = df['Series'].dropna().unique().tolist()
        with col_filter2:
            selected = st.multiselect(f"{sheet_name} - 시리즈 선택", options, default=options, key=f"{sheet_name}_series")
        filtered_df = df[df['Series'].isin(selected)]
    else:
        options = df[model_col].dropna().unique().tolist()
        with col_filter2:
            selected = st.multiselect(f"{sheet_name} - 모델 선택", options, default=options[:5], key=f"{sheet_name}_models")
        filtered_df = df[df[model_col].isin(selected)]

    selected_models = filtered_df[model_col].dropna().unique().tolist()

    if selected_models:
        st.markdown("#### Q-H (토출양정) 성능곡선")
        fig1 = plot_points(filtered_df, model_col, x_col, y_col, selected_models) if point_only else \
               plot_lines(filtered_df, model_col, x_col, y_col, selected_models, source=sheet_name.title(), linestyle='dot' if catalog_style else None)

        if sheet_name == "AI 분석":
            reference_df = pd.read_excel(uploaded_file, sheet_name="reference data")
            reference_df = reference_df[[model_col, x_col, y_col]].dropna()
            for model in selected_models:
                ref_model_df = reference_df[reference_df[model_col] == model].sort_values(by=x_col)
                fig1.add_trace(go.Scatter(
                    x=ref_model_df[x_col], y=ref_model_df[y_col],
                    mode='lines+markers', name=f"{model} (Reference)",
                    line=dict(dash='dot')))

        st.plotly_chart(fig1, use_container_width=True)

        if y2_col:
            st.markdown("#### Q-축동력 성능곡선")
            fig2 = plot_points(filtered_df, model_col, x_col, y2_col, selected_models) if point_only else \
                   plot_lines(filtered_df, model_col, x_col, y2_col, selected_models, source=sheet_name.title(), linestyle='dot' if catalog_style else None)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 데이터 테이블")
    st.dataframe(filtered_df, use_container_width=True, height=300)

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation", "AI 분석"])

    with tabs[0]:
        st.subheader("📊 Total - 통합 곡선 분석")

    with tabs[1]:
        st.subheader("📘 Reference Data")
        process_and_plot("reference data")

    with tabs[2]:
        st.subheader("📙 Catalog Data")
        process_and_plot("catalog data", catalog_style=True)

    with tabs[3]:
        st.subheader("📕 Deviation Data")
        process_and_plot("deviation data", point_only=True)

    with tabs[4]:
        st.subheader("🤖 AI 성능 예측")
        df = pd.read_excel(uploaded_file, sheet_name="reference data")
        model_col = get_best_match_column(df, ["모델", "모델명", "Model"])
        x_col = get_best_match_column(df, ["토출량", "유량"])
        y_col = get_best_match_column(df, ["토출양정", "전양정"])

        if model_col and x_col and y_col:
            df = df[[model_col, x_col, y_col]].dropna()
            model = st.selectbox("모델 선택", df[model_col].unique())
            model_df = df[df[model_col] == model]
            X = model_df[[x_col]].values
            y = model_df[y_col].values

            degree = st.slider("다항 회귀 차수 선택", 2, 5, 2)
            poly = PolynomialFeatures(degree)
            X_poly = poly.fit_transform(X)

            reg = LinearRegression().fit(X_poly, y)

            user_input = st.slider("토출량 입력", float(X.min()), float(X.max()), float(X.mean()))
            prediction = reg.predict(poly.transform([[user_input]]))[0]
            st.success(f"예측된 양정(H): {prediction:.2f} @ Q={user_input}")

            x_range = np.linspace(X.min(), X.max(), 300).reshape(-1, 1)
            y_pred = reg.predict(poly.transform(x_range))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=model_df[x_col], y=model_df[y_col], mode='markers', name='실측값'))
            fig.add_trace(go.Scatter(x=x_range.flatten(), y=y_pred, mode='lines', name='회귀곡선'))
            fig.add_trace(go.Scatter(x=[user_input], y=[prediction], mode='markers+text', name='예측값',
                                     text=[f"Q={user_input}, H={prediction:.2f}"], textposition='top center'))

            ref_df = df[df[model_col] == model].sort_values(by=x_col)
            fig.add_trace(go.Scatter(x=ref_df[x_col], y=ref_df[y_col], mode='lines+markers',
                                     name='Reference', line=dict(dash='dot')))

            fig.update_layout(title="AI 기반 예측 곡선", xaxis_title=x_col, yaxis_title=y_col)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("AI 분석을 위한 필수 컬럼이 부족합니다.")

