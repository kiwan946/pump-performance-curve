import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Dooch XRL(F) 성능 곡선 뷰어", layout="wide")
st.title("📊 Dooch XRL(F) 성능 곡선 뷰어")

uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])

# 고정된 시리즈 순서
SERIES_ORDER = [
    "XRF3", "XRF5", "XRF10", "XRF15", "XRF20", "XRF32",
    "XRF45", "XRF64", "XRF95", "XRF125", "XRF155", "XRF185",
    "XRF215", "XRF255"
]

def get_best_match_column(df, names):
    for n in names:
        for col in df.columns:
            if n in col:
                return col
    return None

# 시트 데이터 로드 및 전처리
def load_sheet(name):
    df = pd.read_excel(uploaded_file, sheet_name=name)
    mcol = get_best_match_column(df, ["모델명", "모델", "Model"])
    qcol = get_best_match_column(df, ["토출량", "유량"])
    hcol = get_best_match_column(df, ["토출양정", "전양정"])
    kcol = get_best_match_column(df, ["축동력"])
    if not mcol or not qcol or not hcol:
        st.error(f"{name} 시트: Model/토출량/토출양정 컬럼 누락")
        return None, None, None, None, None, pd.DataFrame()
    df['Series'] = df[mcol].astype(str).str.extract(r"(XRF\d+)")
    df['Series'] = pd.Categorical(df['Series'], categories=SERIES_ORDER, ordered=True)
    df = df.sort_values('Series')
    return mcol, qcol, hcol, kcol, df

# 필터 UI: 시리즈별/모델별
def render_filters(df, mcol, key):
    mode = st.radio("분류 기준", ["시리즈별", "모델별"], key=key+"_mode")
    if mode == "시리즈별":
        opts = df['Series'].dropna().unique().tolist()
        sel = st.multiselect("시리즈 선택", opts, default=opts, key=key+"_series")
        df_f = df[df['Series'].isin(sel)]
    else:
        opts = df[mcol].dropna().unique().tolist()
        keyword = st.text_input("모델 검색", value="", key=key+"_search")
        filt = [m for m in opts if keyword.lower() in m.lower()] if keyword else opts
        sel = st.multiselect("모델 선택", filt, default=filt, key=key+"_models")
        df_f = df[df[mcol].isin(sel)]
    models = df_f[mcol].dropna().unique().tolist()
    return df_f, models

# 곡선/점 그리기 함수
def plot_curve(df, mcol, xcol, ycol, models, style, hline=None, vline=None):
    fig = go.Figure()
    for m in models:
        sub = df[df[mcol] == m].sort_values(xcol)
        fig.add_trace(go.Scatter(
            x=sub[xcol], y=sub[ycol], mode=style['mode'],
            name=m, line=style.get('line', {}), marker=style.get('marker', {})
        ))
    if hline is not None:
        fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=hline, y1=hline,
                      line=dict(color="red", dash="dash"))
    if vline is not None:
        fig.add_shape(type="line", xref="x", x0=vline, x1=vline, yref="paper", y0=0, y1=1,
                      line=dict(color="blue", dash="dash"))
    fig.update_layout(xaxis_title=xcol, yaxis_title=ycol, height=600, hovermode='closest')
    return fig

if uploaded_file:
    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation"])

    # Total 탭
    with tabs[0]:
        st.subheader("📊 Total - Q-H / Q-kW 통합 분석")
        show_ref = st.checkbox("Reference 데이터", value=True)
        show_cat = st.checkbox("Catalog 데이터", value=False)
        show_dev = st.checkbox("Deviation 데이터", value=False)

        mcol_ref, qcol, hcol, kcol_ref, df_ref = load_sheet("reference data")
        mcol_cat, _, _, kcol_cat, df_cat = load_sheet("catalog data")
        mcol_dev, _, _, kcol_dev, df_dev = load_sheet("deviation data")

        df_f, models = render_filters(df_ref, mcol_ref, "total")

        col1, col2 = st.columns(2)
        with col1:
            h_h = st.number_input("Q-H 수평선", value=None)
            v_h = st.number_input("Q-H 수직선", value=None)
        with col2:
            h_k = st.number_input("Q-kW 수평선", value=None)
            v_k = st.number_input("Q-kW 수직선", value=None)

        # Q-H 그래프
        st.markdown("#### Q-H (토출량-토출양정)")
        fig_h = go.Figure()
        if show_ref:
            fig_h = plot_curve(df_ref[df_ref[mcol_ref].isin(models)], mcol_ref, qcol, hcol,
                               models, style={'mode':'lines+markers'},
                               hline=h_h, vline=v_h)
        if show_cat:
            fig_h = plot_curve(df_cat[df_cat[mcol_cat].isin(models)], mcol_cat, qcol, hcol,
                               models, style={'mode':'lines+markers','line':{'dash':'dot'}},
                               hline=h_h, vline=v_h)
        if show_dev:
            fig_h = plot_curve(df_dev[df_dev[mcol_dev].isin(models)], mcol_dev, qcol, hcol,
                               models, style={'mode':'markers'},
                               hline=h_h, vline=v_h)
        st.plotly_chart(fig_h, use_container_width=True)

        # Q-kW 그래프
        st.markdown("#### Q-kW (토출량-축동력)")
        fig_k = go.Figure()
        if show_ref and kcol_ref:
            fig_k = plot_curve(df_ref[df_ref[mcol_ref].isin(models)], mcol_ref, qcol, kcol_ref,
                               models, style={'mode':'lines+markers'})
        if show_cat and kcol_cat:
            fig_k = plot_curve(df_cat[df_cat[mcol_cat].isin(models)], mcol_cat, qcol, kcol_cat,
                               models, style={'mode':'lines+markers','line':{'dash':'dot'}})
        if show_dev and kcol_dev:
            fig_k = plot_curve(df_dev[df_dev[mcol_dev].isin(models)], mcol_dev, qcol, kcol_dev,
                               models, style={'mode':'markers'})
        # 보조선
        fig_k = fig_k or go.Figure()
        if h_k is not None or v_k is not None:
            for trace in fig_k.layout['shapes'] if 'shapes' in fig_k.layout else []:
                fig_k.add_shape(trace)
        st.plotly_chart(fig_k, use_container_width=True)

    # 개별 탭: Q-H & Q-kW + DB
    for i, name in enumerate(["reference data","catalog data","deviation data"]):
        with tabs[i+1]:
            st.subheader(name.title())
            mcol, qcol, hcol, kcol, df = load_sheet(name)
            if df.empty:
                st.info("데이터가 없습니다.")
                continue
            df_f, models = render_filters(df, mcol, name)

            # Q-H
            st.markdown("#### Q-H (토출량-토출양정)")
            style = {'mode':'markers'} if name=='deviation data' else {'mode':'lines+markers'}
            if name=='catalog data': style['line']={'dash':'dot'}
            fig1 = plot_curve(df_f, mcol, qcol, hcol, models, style)
            st.plotly_chart(fig1, use_container_width=True)

            # Q-kW
            if kcol:
                st.markdown("#### Q-kW (토출량-축동력)")
                fig2 = plot_curve(df_f, mcol, qcol, kcol, models, style)
                st.plotly_chart(fig2, use_container_width=True)

            # 데이터 테이블
            st.markdown("#### 데이터 확인")
            st.dataframe(df_f, use_container_width=True, height=300)
