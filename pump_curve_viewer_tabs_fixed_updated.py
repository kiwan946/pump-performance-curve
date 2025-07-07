import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Dooch XRL(F) 성능 곡선 뷰어", layout="wide")
st.title("📊 Dooch XRL(F) 성능 곡선 뷰어")

uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])

SERIES_ORDER = [
    "XRF3", "XRF5", "XRF10", "XRF15", "XRF20", "XRF32",
    "XRF45", "XRF64", "XRF95", "XRF125", "XRF155", "XRF185",
    "XRF215", "XRF255"
]

def get_best_match_column(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name in col:
                return col
    return None

def plot_lines(df, model_col, x_col, y_col, selected_models, source=None, hline=None, vline=None):
    fig = go.Figure()
    for model in selected_models:
        model_df = df[df[model_col] == model].sort_values(by=x_col)
        if source == 'Catalog':
            line_style = dict(dash='dot')
        elif source == 'Deviation':
            fig.add_trace(go.Scatter(
                x=model_df[x_col], y=model_df[y_col], mode='markers',
                name=f"{model} ({source})",
                text=[f"Model: {model}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])],
                hoverinfo='text'))
            continue
        else:
            line_style = dict()

        fig.add_trace(go.Scatter(
            x=model_df[x_col], y=model_df[y_col], mode='lines+markers',
            name=f"{model} ({source})" if source else model, line=line_style,
            text=[f"Model: {model}<br>Q: {q}<br>H: {h}" for q, h in zip(model_df[x_col], model_df[y_col])],
            hoverinfo='text'))

    if hline is not None:
        fig.add_shape(type="line", x0=df[x_col].min(), x1=df[x_col].max(), y0=hline, y1=hline,
                      line=dict(color="Red", dash="dash"))
    if vline is not None:
        fig.add_shape(type="line", x0=vline, x1=vline, y0=df[y_col].min(), y1=df[y_col].max(),
                      line=dict(color="Blue", dash="dash"))

    fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                      hovermode='closest', height=600)
    st.plotly_chart(fig, use_container_width=True)

def process_and_plot(sheet_name, show=True):
    if not show:
        return None, None, None, None, pd.DataFrame()

    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

    model_col = get_best_match_column(df, ["모델", "모델명", "Model"])
    x_col = get_best_match_column(df, ["토출량", "유량"])
    y_col = get_best_match_column(df, ["토출양정", "전양정"])
    y2_col = get_best_match_column(df, ["축동력"])

    if not model_col or not x_col or not y_col:
        st.error(f"{sheet_name} 시트에서 필수 컬럼(Model, 토출량, 토출양정)을 찾을 수 없습니다.")
        return None, None, None, None, pd.DataFrame()

    df['Series'] = df[model_col].astype(str).str.extract(r"(XRF\d+)")
    df['Series'] = pd.Categorical(df['Series'], categories=SERIES_ORDER, ordered=True)
    df = df.sort_values("Series")

    return df, model_col, x_col, y_col, y2_col

def render_filter_controls(df, model_col, sheet_name):
    mode = st.selectbox(f"{sheet_name}_분류 기준 선택", ["시리즈별", "모델별"], key=sheet_name+"_mode")
    if mode == "시리즈별":
        options = df['Series'].dropna().unique().tolist()
        selected = st.multiselect(f"{sheet_name}_시리즈 선택", options, key=sheet_name+'_series')
        filtered_df = df[df['Series'].isin(selected)]
    else:
        options = df[model_col].dropna().unique().tolist()
        selected = st.multiselect(f"{sheet_name}_모델 선택", options, key=sheet_name+'_models')
        filtered_df = df[df[model_col].isin(selected)]
    return filtered_df, filtered_df[model_col].dropna().unique().tolist()

if uploaded_file:
    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation"])

    with tabs[0]:
        st.subheader("📊 Total - 통합 곡선 분석")

        show_ref = st.checkbox("📘 Reference Data 표시", value=True)
        show_cat = st.checkbox("📙 Catalog Data 표시", value=False)
        show_dev = st.checkbox("📕 Deviation Data 표시", value=False)

        df_ref, model_col, x_col, y_col, y2_col = process_and_plot("reference data", show_ref)
        df_cat, *_ = process_and_plot("catalog data", show_cat)
        df_dev, *_ = process_and_plot("deviation data", show_dev)

        filtered_df, selected_models = render_filter_controls(df_ref, model_col, "total")

        hline = st.number_input("수평 보조선 (H)", value=None, placeholder="선택 안함")
        vline = st.number_input("수직 보조선 (Q)", value=None, placeholder="선택 안함")

        if selected_models:
            if show_ref:
                plot_lines(df_ref, model_col, x_col, y_col, selected_models, source='Reference', hline=hline, vline=vline)
            if show_cat:
                plot_lines(df_cat, model_col, x_col, y_col, selected_models, source='Catalog', hline=hline, vline=vline)
            if show_dev:
                plot_lines(df_dev, model_col, x_col, y_col, selected_models, source='Deviation', hline=hline, vline=vline)

    for i, sheet in enumerate(["reference data", "catalog data", "deviation data"]):
        with tabs[i+1]:
            st.subheader(f"📘 {sheet.title() if i == 0 else ('📙 Catalog Data' if i == 1 else '📕 Deviation Data')}")
            df, model_col, x_col, y_col, y2_col = process_and_plot(sheet)
            if df is not None:
                filtered_df, selected_models = render_filter_controls(df, model_col, sheet)

                hline = st.number_input(f"{sheet}_수평 보조선 (H)", value=None, placeholder="선택 안함", key=sheet+"_h")
                vline = st.number_input(f"{sheet}_수직 보조선 (Q)", value=None, placeholder="선택 안함", key=sheet+"_v")

                if selected_models:
                    plot_lines(filtered_df, model_col, x_col, y_col, selected_models, source=sheet.title(), hline=hline, vline=vline)
                    if y2_col:
                        plot_lines(filtered_df, model_col, x_col, y2_col, selected_models, source=sheet.title(), hline=hline, vline=vline)
                st.dataframe(filtered_df, use_container_width=True, height=300)
