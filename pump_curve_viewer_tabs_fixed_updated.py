import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Dooch XRL(F) 성능 곡선 뷰어", layout="wide")
st.title("📊 Dooch XRL(F) 성능 곡선 뷰어")

# 파일 업로드
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

    def plot_curves(df, model_col, x_col, y_col, selected_models, y2_col=None):
        fig = go.Figure()
        for model in selected_models:
            model_df = df[df[model_col] == model].sort_values(by=x_col)
            fig.add_trace(go.Scatter(x=model_df[x_col], y=model_df[y_col],
                                     mode='lines+markers', name=f"{model} - {y_col}"))
            if y2_col and y2_col in model_df.columns:
                fig.add_trace(go.Scatter(x=model_df[x_col], y=model_df[y2_col],
                                         mode='lines+markers', name=f"{model} - {y2_col}"))
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col,
                          hovermode='closest', height=600)
        st.plotly_chart(fig, use_container_width=True)

    def process_and_plot(sheet_name):
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)

        model_col = get_best_match_column(df, ["모델", "모델명", "Model"])
        x_col = get_best_match_column(df, ["토출량", "유량"])
        y_col = get_best_match_column(df, ["토출양정", "전양정"])
        y2_col = get_best_match_column(df, ["축동력"])

        if not model_col or not x_col or not y_col:
            st.error("필수 컬럼(Model, 토출량, 토출양정)을 찾을 수 없습니다.")
            return

        df['Series'] = df[model_col].astype(str).str.extract(r"(XRF\d+)")
        series_list = df['Series'].dropna().unique().tolist()
        selected_series = st.multiselect("시리즈 선택", series_list, default=series_list)
        filtered_df = df[df['Series'].isin(selected_series)]
        models = filtered_df[model_col].dropna().unique().tolist()
        selected_models = st.multiselect("모델 선택", models, default=models[:5])

        st.dataframe(filtered_df, use_container_width=True, height=300)
        if selected_models:
            plot_curves(filtered_df, model_col, x_col, y_col, selected_models, y2_col)

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
        process_and_plot("deviation data")

    # Total 탭
    with tabs[0]:
        st.subheader("📗 Total Comparison View")
        ref_df = pd.read_excel(uploaded_file, sheet_name="reference data")
        cat_df = pd.read_excel(uploaded_file, sheet_name="catalog data")
        dev_df = pd.read_excel(uploaded_file, sheet_name="deviation data")

        ref_df = ref_df.rename(columns={get_best_match_column(ref_df, ["모델"]): "Model"})
        cat_df = cat_df.rename(columns={get_best_match_column(cat_df, ["모델명"]): "Model",
                                        get_best_match_column(cat_df, ["유량"]): "토출량",
                                        get_best_match_column(cat_df, ["토출양정", "전양정"]): "토출양정"})
        dev_df = dev_df.rename(columns={get_best_match_column(dev_df, ["모델명"]): "Model",
                                        get_best_match_column(dev_df, ["유량"]): "토출량",
                                        get_best_match_column(dev_df, ["토출양정"]): "토출양정"})

        ref_df['source'] = 'Reference'
        cat_df['source'] = 'Catalog'
        dev_df['source'] = 'Deviation'

        ref_df['Series'] = ref_df['Model'].astype(str).str.extract(r"(XRF\d+)")
        cat_df['Series'] = cat_df['Model'].astype(str).str.extract(r"(XRF\d+)")
        dev_df['Series'] = dev_df['Model'].astype(str).str.extract(r"(XRF\d+)")

        combined = pd.concat([
            ref_df[['Model', 'Series', '토출량', '토출양정', '축동력', 'source']],
            cat_df[['Model', 'Series', '토출량', '토출양정', '축동력', 'source']],
            dev_df[['Model', 'Series', '토출량', '토출양정', '축동력', 'source']]
        ], ignore_index=True)

        series_list = combined['Series'].dropna().unique().tolist()
        selected_series = st.multiselect("시리즈 선택", series_list, default=series_list)
        combined = combined[combined['Series'].isin(selected_series)]

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
                                             mode='lines+markers', name=f"{model} ({src}) - Total Head"))
                    if '축동력' in temp.columns:
                        fig.add_trace(go.Scatter(x=temp['토출량'], y=temp['축동력'],
                                                 mode='lines+markers', name=f"{model} ({src}) - 축동력"))
            fig.update_layout(xaxis_title="Capacity", yaxis_title="Total Head / 축동력",
                              hovermode='closest', height=600)
            st.plotly_chart(fig, use_container_width=True)
