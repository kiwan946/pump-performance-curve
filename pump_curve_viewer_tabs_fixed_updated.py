import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Dooch XRL(F) 성능 곡선 뷰어", layout="wide")
st.title("📊 Dooch XRL(F) 성능 곡선 뷰어")

uploaded_file = st.file_uploader("Excel 파일 업로드 (.xlsx 또는 .xlsm)", type=["xlsx", "xlsm"])

# 고정된 시리즈 순서 정의
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

# 데이터 불러오기 및 전처리
def load_sheet(name, active):
    if not active:
        return None, None, None, None, pd.DataFrame()
    df = pd.read_excel(uploaded_file, sheet_name=name)
    mcol = get_best_match_column(df, ["모델명", "모델", "Model"])
    xcol = get_best_match_column(df, ["토출량", "유량"])
    ycol = get_best_match_column(df, ["토출양정", "전양정"])
    y2col = get_best_match_column(df, ["축동력"])
    if not mcol or not xcol or not ycol:
        st.error(f"{name} 시트: Model/토출량/토출양정 컬럼 누락")
        return None, None, None, None, pd.DataFrame()
    df['Series'] = df[mcol].astype(str).str.extract(r"(XRF\d+)")
    df['Series'] = pd.Categorical(df['Series'], categories=SERIES_ORDER, ordered=True)
    df = df.sort_values('Series')
    return mcol, xcol, ycol, y2col, df

# 필터 UI
def render_filters(df, mcol, key):
    mode = st.selectbox("분류 기준", ["시리즈별", "모델별"], key=key+"_mode")
    if mode == "시리즈별":
        opts = list(df['Series'].dropna().unique())
        sel = st.multiselect("시리즈 선택", options=opts, default=opts, key=key+"_series")
        return df[df['Series'].isin(sel)], sel
    else:
        allm = list(df[mcol].dropna().unique())
        keyword = st.text_input("모델 검색", value="", key=key+"_search")
        filt = [m for m in allm if keyword.lower() in m.lower()] if keyword else allm
        sel = st.multiselect("모델 선택", options=filt, default=filt, key=key+"_models")
        return df[df[mcol].isin(sel)], sel

# 플로팅 함수
def plot_curve(df, mcol, xcol, ycol, sel, style, hlin=None, vlin=None):
    fig = go.Figure()
    for m in sel:
        d = df[df[mcol]==m].sort_values(xcol)
        fig.add_trace(go.Scatter(
            x=d[xcol], y=d[ycol], mode=style['mode'],
            name=m, line=style.get('line', {}), marker=style.get('marker', {})
        ))
    if hlin is not None:
        fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y", y0=hlin, y1=hlin,
                      line=dict(color="red", dash="dash"))
    if vlin is not None:
        fig.add_shape(type="line", xref="x", x0=vlin, x1=vlin, yref="paper", y0=0, y1=1,
                      line=dict(color="blue", dash="dash"))
    fig.update_layout(xaxis_title=xcol, yaxis_title=ycol, height=600, hovermode='closest')
    st.plotly_chart(fig, use_container_width=True)

if uploaded_file:
    tabs = st.tabs(["Total", "Reference", "Catalog", "Deviation"])

    # Total 탭
    with tabs[0]:
        st.subheader("📊 Total - 통합 곡선 분석")
        show_r = st.checkbox("Reference 표시", value=True)
        show_c = st.checkbox("Catalog 표시", value=False)
        show_d = st.checkbox("Deviation 표시", value=False)

        mc_r, xc_r, yc_r, y2_r, df_r = load_sheet("reference data", show_r)
        mc_c, xc_c, yc_c, y2_c, df_c = load_sheet("catalog data", show_c)
        mc_d, xc_d, yc_d, y2_d, df_d = load_sheet("deviation data", show_d)

        df_f, sel = render_filters(df_r, mc_r, "total")
        h = st.number_input("수평 보조선(H)", value=None)
        v = st.number_input("수직 보조선(Q)", value=None)
        if sel:
            if show_r:
                plot_curve(df_r, mc_r, xc_r, yc_r, sel,
                           style={'mode':'lines+markers', 'line':{}}, hlin=h, vlin=v)
            if show_c:
                plot_curve(df_c, mc_c, xc_c, yc_c, sel,
                           style={'mode':'lines+markers','line':{'dash':'dot'}}, hlin=h, vlin=v)
            if show_d:
                plot_curve(df_d, mc_d, xc_d, yc_d, sel,
                           style={'mode':'markers'}, hlin=h, vlin=v)

    # 개별 탭
    for i, name in enumerate(["reference data","catalog data","deviation data"]):
        with tabs[i+1]:
            st.subheader(name.title())
            mc, xc, yc, y2, df = load_sheet(name, True)
            df_f, sel = render_filters(df, mc, name)
            h = st.number_input(f"{name} 수평 보조선(H)", value=None, key=name+"_h")
            v = st.number_input(f"{name} 수직 보조선(Q)", value=None, key=name+"_v")
            if sel:
                style = {'mode':'markers'} if name=="deviation data" else {'mode':'lines+markers'}
                if name=="catalog data": style['line'] = {'dash':'dot'}
                plot_curve(df_f, mc, xc, yc, sel, style, hlin=h, vlin=v)
                if y2:
                    plot_curve(df_f, mc, xc, y2, sel, style, hlin=h, vlin=v)
            st.dataframe(df_f, use_container_width=True, height=300)
