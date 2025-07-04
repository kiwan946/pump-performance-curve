
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 펌프 성능 곡선 뷰어 (인터랙티브 완성형)")

uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])

if uploaded_file:
    try:
        sheets = pd.read_excel(uploaded_file, sheet_name=None)
        ref_df = sheets.get("reference data")
        cat_df = sheets.get("catalog data")
        dev_df = sheets.get("deviation data")

        def clean_df(df):
            df.columns = df.columns.str.strip()
            df = df.rename(columns={
                "토출양정": "Total Head",
                "토출량": "Capacity",
                "모델": "Model"
            })
            df["Series"] = df["Model"].str.extract(r"(XRF\d+)", expand=False)
            return df

        ref_df = clean_df(ref_df) if ref_df is not None else pd.DataFrame()
        cat_df = clean_df(cat_df) if cat_df is not None else pd.DataFrame()
        dev_df = clean_df(dev_df) if dev_df is not None else pd.DataFrame()

        tab1, tab2, tab3, tab4 = st.tabs(["📊 Total", "📋 Reference", "📘 Catalog", "📐 Deviation"])

        # ===== Reference Tab =====
        with tab2:
            st.subheader("📈 성능 곡선 시각화 (시리즈별)")
            selected_series = st.multiselect(
                "표시할 시리즈 선택",
                options=sorted(ref_df["Series"].dropna().unique()),
                default=sorted(ref_df["Series"].dropna().unique())
            )

            x_line = st.number_input("수직 보조선 (Capacity)", value=0.0, step=10.0)
            y_line = st.number_input("수평 보조선 (Head)", value=0.0, step=5.0)

            fig_ref = go.Figure()
            for model in ref_df["Model"].unique():
                subset = ref_df[ref_df["Model"] == model]
                if subset.empty or subset["Series"].iloc[0] not in selected_series:
                    continue
                fig_ref.add_trace(go.Scatter(
                    x=subset["Capacity"],
                    y=subset["Total Head"],
                    mode="lines+markers+text",
                    name=model,
                    text=[model] + [""] * (len(subset) - 1),
                    textposition="top left"
                ))
            if x_line > 0:
                fig_ref.add_vline(x=x_line, line_width=2, line_dash="dash", line_color="red")
            if y_line > 0:
                fig_ref.add_hline(y=y_line, line_width=2, line_dash="dash", line_color="blue")
            fig_ref.update_layout(
                xaxis_title="Capacity (L/min)", yaxis_title="Total Head (m)",
                height=900, width=1500, hovermode="closest", showlegend=True
            )
            fig_ref.update_xaxes(showgrid=True)
            fig_ref.update_yaxes(showgrid=True)
            st.plotly_chart(fig_ref, use_container_width=True)

            st.subheader("📝 백데이터 편집")
            st.data_editor(ref_df, num_rows="dynamic")

        # ===== Total Tab =====
        with tab1:
            st.subheader("📊 성능 곡선 시각화 (모델별 + 데이터 선택)")
            show_ref = st.checkbox("📘 Reference", value=True)
            show_cat = st.checkbox("📘 Catalog")
            show_dev = st.checkbox("📘 Deviation")

            all_models = pd.concat([ref_df, cat_df, dev_df], ignore_index=True)["Model"].unique()
            selected_models = st.multiselect("표시할 모델 선택", options=sorted(all_models), default=sorted(all_models))

            fig_total = go.Figure()
            sources = [("Reference", ref_df, show_ref), ("Catalog", cat_df, show_cat), ("Deviation", dev_df, show_dev)]

            for label, df_src, show in sources:
                if not show or df_src.empty:
                    continue
                for model in df_src["Model"].unique():
                    if model not in selected_models:
                        continue
                    subset = df_src[df_src["Model"] == model]
                    if subset.empty:
                        continue
                    fig_total.add_trace(go.Scatter(
                        x=subset["Capacity"],
                        y=subset["Total Head"],
                        mode="lines+markers",
                        name=f"{model} ({label})"
                    ))

            fig_total.update_layout(
                xaxis_title="Capacity (L/min)", yaxis_title="Total Head (m)",
                height=900, width=1500, hovermode="closest", showlegend=True
            )
            fig_total.update_xaxes(showgrid=True)
            fig_total.update_yaxes(showgrid=True)
            st.plotly_chart(fig_total, use_container_width=True)

        # ===== Catalog Tab =====
        with tab3:
            st.subheader("📘 Catalog Data (시리즈별)")
            st.dataframe(cat_df)

        # ===== Deviation Tab =====
        with tab4:
            st.subheader("📐 Deviation Data (시리즈별)")
            st.dataframe(dev_df)

    except Exception as e:
        st.error(f"오류 발생: {e}")
