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

# 컬럼 명 자동 매칭
def get_best_match_column(df, names):
    for n in names:
        for col in df.columns:
            if n in col:
                return col
    return None

# 시트 로드 및 전처리
def load_sheet(name):
    try:
        df = pd.read_excel(uploaded_file, sheet_name=name)
    except Exception:
        return None, None, None, None, pd.DataFrame()
    mcol = get_best_match_column(df, ["모델명","모델","Model"])
    qcol = get_best_match_column(df, ["토출량","유량"])
    hcol = get_best_match_column(df, ["토출양정","전양정"])
    kcol = get_best_match_column(df, ["축동력"])
    if not mcol or not qcol or not hcol:
        return None, None, None, None, pd.DataFrame()
    df['Series'] = df[mcol].astype(str).str.extract(r"(XRF\d+)")
    df['Series'] = pd.Categorical(df['Series'], categories=SERIES_ORDER, ordered=True)
    df = df.sort_values('Series')
    return mcol, qcol, hcol, kcol, df

# 필터 UI
def render_filters(df, mcol, prefix):
    mode = st.radio("분류 기준", ["시리즈별","모델별"], key=prefix+"_mode")
    if mode == "시리즈별":
        opts = df['Series'].dropna().unique().tolist()
        sel = st.multiselect("시리즈 선택", opts, default=[], key=prefix+"_series")
        df_f = df[df['Series'].isin(sel)] if sel else pd.DataFrame()
    else:
        opts = df[mcol].dropna().unique().tolist()
        sel = st.multiselect("모델 선택", opts, default=[], key=prefix+"_models")
        df_f = df[df[mcol].isin(sel)] if sel else pd.DataFrame()
    return df_f

# 트레이스 추가
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

    with tabs[0]:  # Total 탭
        st.subheader("📊 Total - 통합 곡선 분석")
        # 데이터 로드
        m_r,q_r,h_r,k_r,df_r = load_sheet("reference data")
        m_c,q_c,h_c,k_c,df_c = load_sheet("catalog data")
        m_d,q_d,h_d,k_d,df_d = load_sheet("deviation data")
        # 필터
        df_f = render_filters(df_r, m_r, "total")
        models = df_f[m_r].unique().tolist() if not df_f.empty else []
        # 체크박스
        ref_show = st.checkbox("Reference 표시", key="total_ref")
        cat_show = st.checkbox("Catalog 표시", key="total_cat")
        dev_show = st.checkbox("Deviation 표시", key="total_dev")
        # 보조선 입력
        col1, col2 = st.columns(2)
        with col1:
            hh = st.number_input("Q-H 수평선", key="total_hh")
            vh = st.number_input("Q-H 수직선", key="total_vh")
        with col2:
            hk = st.number_input("Q-kW 수평선", key="total_hk")
            vk = st.number_input("Q-kW 수직선", key="total_vk")
        # Q-H 그래프
        st.markdown("#### Q-H (토출량-토출양정)")
        fig_h = go.Figure()
        if ref_show:
            add_traces(fig_h, df_r, m_r, q_r, h_r, models, 'lines+markers')
        if cat_show:
            add_traces(fig_h, df_c, m_c, q_c, h_c, models, 'lines+markers', line_style=dict(dash='dot'))
        if dev_show:
            add_traces(fig_h, df_d, m_d, q_d, h_d, models, 'markers')
        add_guides(fig_h, hh, vh)
        st.plotly_chart(fig_h, use_container_width=True, key="total_qh")
        # Q-kW 그래프
        st.markdown("#### Q-kW (토출량-축동력)")
        fig_k = go.Figure()
        if ref_show:
            add_traces(fig_k, df_r, m_r, q_r, k_r, models, 'lines+markers')
        if cat_show:
            add_traces(fig_k, df_c, m_c, q_c, k_c, models, 'lines+markers', line_style=dict(dash='dot'))
        if dev_show:
            add_traces(fig_k, df_d, m_d, q_d, k_d, models, 'markers')
        add_guides(fig_k, hk, vk)
        st.plotly_chart(fig_k, use_container_width=True, key="total_qk")

    # 개별 탭들
    for idx, sheet in enumerate(["reference data","catalog data","deviation data"]):
        with tabs[idx+1]:
            st.subheader(sheet.title())
            mcol,qcol,hcol,kcol,df = load_sheet(sheet)
            df_f = render_filters(df, mcol, sheet)
            models = df_f[mcol].unique().tolist() if not df_f.empty else []
            if not models:
                st.info("모델을 선택해주세요.")
                continue
            # Q-H
            st.markdown("#### Q-H (토출량-토출양정)")
            fig1 = go.Figure()
            mode1 = 'markers' if sheet=='deviation data' else 'lines+markers'
            style1 = dict(dash='dot') if sheet=='catalog data' else None
            add_traces(fig1, df_f, mcol, qcol, hcol, models, mode1, line_style=style1)
            st.plotly_chart(fig1, use_container_width=True, key=f"{sheet}_qh")
            # Q-kW
            if kcol:
                st.markdown("#### Q-kW (토출량-축동력)")
                fig2 = go.Figure()
                add_traces(fig2, df_f, mcol, qcol, kcol, models, mode1, line_style=style1)
                st.plotly_chart(fig2, use_container_width=True, key=f"{sheet}_qk")
            # 데이터 테이블
            st.markdown("#### 데이터 확인")
            st.dataframe(df_f, use_container_width=True, height=300, key=f"df_{sheet}")

