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

# 시트 로드 및 전처리
def load_sheet(sheet_name):
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    except Exception:
        st.error(f"'{sheet_name}' 시트를 불러올 수 없습니다.")
        return None, None, None, None, pd.DataFrame()
    mcol = get_best_match_column(df, ["모델명","모델","Model"])
    qcol = get_best_match_column(df, ["토출량","유량"])
    hcol = get_best_match_column(df, ["토출양정","전양정"])
    kcol = get_best_match_column(df, ["축동력"])
    if not mcol or not qcol or not hcol:
        st.error(f"{sheet_name}: 필수 컬럼(Model/토출량/토출양정) 누락")
        return None, None, None, None, pd.DataFrame()
    df['Series'] = df[mcol].astype(str).str.extract(r"(XRF\d+)")
    df['Series'] = pd.Categorical(df['Series'], categories=SERIES_ORDER, ordered=True)
    df = df.sort_values('Series')
    return mcol, qcol, hcol, kcol, df

# 필터 UI: 기본값 빈 상태
def render_filters(df, mcol, key_prefix):
    mode = st.radio("분류 기준", ["시리즈별","모델별"], key=key_prefix+"_mode")
    if mode == "시리즈별":
        opts = df['Series'].dropna().unique().tolist()
        sel = st.multiselect("시리즈 선택", opts, default=[], key=key_prefix+"_series")
        df_f = df[df['Series'].isin(sel)] if sel else pd.DataFrame()
    else:
        opts = df[mcol].dropna().unique().tolist()
        sel = st.multiselect("모델 선택", opts, default=[], key=key_prefix+"_models")
        df_f = df[df[mcol].isin(sel)] if sel else pd.DataFrame()
    models = df_f[mcol].dropna().unique().tolist()
    return df_f, models

# 곡선/점 추가
def add_traces(fig, df, mcol, xcol, ycol, models, mode, line_style=None, marker_style=None):
    for m in models:
        sub = df[df[mcol]==m].sort_values(xcol)
        fig.add_trace(go.Scatter(
            x=sub[xcol], y=sub[ycol],
            mode=mode,
            name=m,
            line=line_style or {},
            marker=marker_style or {}
        ))

# 보조선 추가
def add_guides(fig, hline, vline):
    if hline is not None:
        fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=hline, y1=hline,
                      line=dict(color="red", dash="dash"))
    if vline is not None:
        fig.add_shape(type="line", xref="x", x0=vline, x1=vline, yref="paper", y0=0, y1=1,
                      line=dict(color="blue", dash="dash"))

if uploaded_file:
    tabs = st.tabs(["Total","Reference","Catalog","Deviation"])

    # Total 탭
    with tabs[0]:
        st.subheader("📊 Total - Q-H & Q-kW 통합 분석")
        show_ref = st.checkbox("Reference", value=True)
        show_cat = st.checkbox("Catalog", value=True)
        show_dev = st.checkbox("Deviation", value=True)
        # 로드
        m_r,q_r,h_r,k_r,df_r = load_sheet("reference data")
        m_c,q_c,h_c,k_c,df_c = load_sheet("catalog data")
        m_d,q_d,h_d,k_d,df_d = load_sheet("deviation data")
        # 필터
        df_f, models = render_filters(df_r, m_r, "total")
        # 보조선
        col1,col2 = st.columns(2)
        with col1:
            hh = st.number_input("Q-H 수평선", key="total_hh")
            vh = st.number_input("Q-H 수직선", key="total_vh")
        with col2:
            hk = st.number_input("Q-kW 수평선", key="total_hk")
            vk = st.number_input("Q-kW 수직선", key="total_vk")
        # Q-H
        st.markdown("#### Q-H (토출량-토출양정)")
        fig_h = go.Figure()
        if show_ref: add_traces(fig_h, df_r, m_r, q_r, h_r, models, mode='lines+markers')
        if show_cat: add_traces(fig_h, df_c, m_c, q_c, h_c, models, mode='lines+markers', line_style=dict(dash='dot'))
        if show_dev: add_traces(fig_h, df_d, m_d, q_d, h_d, models, mode='markers')
        add_guides(fig_h, hh, vh)
        st.plotly_chart(fig_h, use_container_width=True)
        # Q-kW
        st.markdown("#### Q-kW (토출량-축동력)")
        fig_k = go.Figure()
        if show_ref and k_r: add_traces(fig_k, df_r, m_r, q_r, k_r, models, mode='lines+markers')
        if show_cat and k_c: add_traces(fig_k, df_c, m_c, q_c, k_c, models, mode='lines+markers', line_style=dict(dash='dot'))
        if show_dev and k_d: add_traces(fig_k, df_d, m_d, q_d, k_d, models, mode='markers')
        add_guides(fig_k, hk, vk)
        st.plotly_chart(fig_k, use_container_width=True)

    # 개별 탭
    for idx,sheet in enumerate(["reference data","catalog data","deviation data"]):
        with tabs[idx+1]:
            st.subheader(sheet.title())
            mcol,qcol,hcol,kcol,df = load_sheet(sheet)
            df_f, models = render_filters(df, mcol, sheet)
            if not models:
                st.info("모델을 선택해주세요.")
                continue
            # Q-H
            st.markdown("#### Q-H (토출량-토출양정)")
            fig1=go.Figure()
            mode1 = 'markers' if sheet=='deviation data' else 'lines+markers'
            style_line = dict(dash='dot') if sheet=='catalog data' else None
            add_traces(fig1, df_f, mcol, qcol, hcol, models, mode=mode1, line_style=style_line)
            st.plotly_chart(fig1, use_container_width=True)
            # Q-kW
            if kcol:
                st.markdown("#### Q-kW (토출량-축동력)")
                fig2=go.Figure()
                add_traces(fig2, df_f, mcol, qcol, kcol, models, mode=mode1, line_style=style_line)
                st.plotly_chart(fig2, use_container_width=True)
            # 테이블
            st.markdown("#### 데이터 확인")
            st.dataframe(df_f, use_container_width=True, height=300)
