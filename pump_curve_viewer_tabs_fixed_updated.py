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

def get_best_match_column(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name in col:
                return col
    return None

# 곡선 또는 점 그리기 함수
def plot_lines(df, model_col, x_col, y_col, models, source=None, hline=None, vline=None):
    fig = go.Figure()
    # 모델별 데이터 추가
    for m in models:
        sub = df[df[model_col] == m].sort_values(by=x_col)
        if source == 'Catalog':
            style = dict(dash='dot')
            mode = 'lines+markers'
        elif source == 'Deviation':
            style = {}
            mode = 'markers'
        else:
            style = {}
            mode = 'lines+markers'
        fig.add_trace(go.Scatter(
            x=sub[x_col], y=sub[y_col], mode=mode,
            name=f"{m} ({source})" if source else m,
            line=style,
            marker={}
        ))
    # 보조선 추가 (paper 좌표 사용)
    if hline is not None:
        fig.add_shape(type="line",
                      xref="paper", x0=0, x1=1,
                      yref="y", y0=hline, y1=hline,
                      line=dict(color="red", dash="dash"))
    if vline is not None:
        fig.add_shape(type="line",
                      xref="x", x0=vline, x1=vline,
                      yref="paper", y0=0, y1=1,
                      line=dict(color="blue", dash="dash"))
    fig.update_layout(
        xaxis_title=x_col, yaxis_title=y_col,
        hovermode='closest', height=600
    )
    st.plotly_chart(fig, use_container_width=True)

# 시트별 데이터 로드 및 컬럼 파싱
def load_sheet(sheet_name, show=True):
    if not show:
        return None, None, None, None, pd.DataFrame()
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    model_col = get_best_match_column(df, ["모델", "모델명", "Model"] )
    x_col = get_best_match_column(df, ["토출량", "유량"] )
    y_col = get_best_match_column(df, ["토출양정", "전양정"] )
    y2_col = get_best_match_column(df, ["축동력"] )
    if not model_col or not x_col or not y_col:
        st.error(f"{sheet_name} 시트에서 필수 컬럼을 찾을 수 없습니다.")
        return None, None, None, None, pd.DataFrame()
    df['Series'] = df[model_col].astype(str).str.extract(r"(XRF\d+)")
    df['Series'] = pd.Categorical(df['Series'], categories=SERIES_ORDER, ordered=True)
    df = df.sort_values('Series')
    return model_col, x_col, y_col, y2_col, df

# 필터 UI 및 데이터 반환
def render_filters(df, model_col, key_prefix):
    mode = st.selectbox("분류 기준", ["시리즈별", "모델별"], key=key_prefix+"_mode")
    if mode == "시리즈별":
        opts = df['Series'].dropna().unique().tolist()
        sel = st.multiselect("시리즈 선택", opts, key=key_prefix+"_series")
        return df[df['Series'].isin(sel)], sel
    else:
        opts = df[model_col].dropna().unique().tolist()
        sel = st.multiselect("모델 선택", opts, key=key_prefix+"_models")
        return df[df[model_col].isin(sel)], sel

if uploaded_file:
    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation"])

    # Total 탭
    with tabs[0]:
        st.subheader("📊 Total - 통합 곡선 분석")
        r = st.checkbox("Reference 표시", value=True)
        c = st.checkbox("Catalog 표시", value=False)
        d = st.checkbox("Deviation 표시", value=False)

        mc_r, xc_r, yc_r, y2_r, df_r = load_sheet("reference data", r)
        mc_c, xc_c, yc_c, y2_c, df_c = load_sheet("catalog data", c)
        mc_d, xd_d, yd_d, y2_d, df_d = load_sheet("deviation data", d)

        df_f, sel = render_filters(df_r, mc_r, "total")
        h = st.number_input("수평선(H)", value=None, placeholder="생략")
        v = st.number_input("수직선(Q)", value=None, placeholder="생략")
        if sel:
            if r: plot_lines(df_r, mc_r, xc_r, yc_r, sel, source='Reference', hline=h, vline=v)
            if c: plot_lines(df_c, mc_c, xc_c, yc_c, sel, source='Catalog', hline=h, vline=v)
            if d: plot_lines(df_d, mc_d, xc_c, yc_c, sel, source='Deviation', hline=h, vline=v)

    # Reference, Catalog, Deviation 개별 탭
    for idx, name in enumerate(["reference data","catalog data","deviation data"]):
        with tabs[idx+1]:
            st.subheader(name.title())
            mc, xc, yc, y2, df = load_sheet(name)
            if df is not None:
                df_f, sel = render_filters(df, mc, name)
                h = st.number_input(f"{name}_H 보조선", value=None, placeholder="생략", key=name+"_h")
                v = st.number_input(f"{name}_Q 보조선", value=None, placeholder="생략", key=name+"_v")
                if sel:
                    plot_lines(df_f, mc, xc, yc, sel, source=name.title(), hline=h, vline=v)
                    if y2:
                        plot_lines(df_f, mc, xc, y2, sel, source=name.title(), hline=h, vline=v)
                st.dataframe(df_f, use_container_width=True, height=300)
