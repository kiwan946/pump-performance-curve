import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pymc as pm
import arviz as az

# 파일 경로 설정
MASTER_FILE = "대외비 - 성능 검토용mk2_REV0.1_closebeta0.1.xlsx.xlsm"
SAMPLE_FILE = "3FS-XRF64-4_주_22120885_월드펌프시스템_구미확장3블럭중흥_(20230227).xlsx"

@st.cache_data
def load_master_data():
    deviation = pd.read_excel(MASTER_FILE, sheet_name="deviation data")
    reference = pd.read_excel(MASTER_FILE, sheet_name="reference data")
    catalog = pd.read_excel(MASTER_FILE, sheet_name="catalog data")
    return deviation, reference, catalog

@st.cache_data
def extract_sample_data(file_path):
    df = pd.read_excel(file_path, sheet_name="DATA SHEET", header=None)
    cols = list(range(8, 23, 2))  # I, K, M, ..., W열
    flow = pd.to_numeric(df.iloc[19, cols], errors='coerce')       # 20행
    head = pd.to_numeric(df.iloc[21, cols], errors='coerce')       # 22행
    total_head = pd.to_numeric(df.iloc[23, cols], errors='coerce') # 24행
    power = pd.to_numeric(df.iloc[33, cols], errors='coerce')      # 34행
    product = df.iloc[7, 6]  # 제품명
    test_id = df.iloc[5, 18] # 시험번호
    sample = pd.DataFrame({
        "Flow Rate": flow,
        "Head": head,
        "Total Head": total_head,
        "Shaft Power": power
    })
    sample["Product"] = product
    sample["Test ID"] = test_id
    return sample.dropna()

# 데이터베이스 로드
deviation_df, reference_df, catalog_df = load_master_data()
sample_df = extract_sample_data(SAMPLE_FILE)

@st.cache_data
def get_models():
    dev = deviation_df.get('모델명', pd.Series()).dropna().unique()
    ref = reference_df.get('모델', pd.Series()).dropna().unique()
    cat = catalog_df.get('모델명', pd.Series()).dropna().unique()
    return sorted(set(list(dev) + list(ref) + list(cat)))

# 앱 타이틀 및 네비게이션
st.title("펌프 성능 분석 및 시각화")
page = st.sidebar.radio("메뉴 선택", [
    "실측 vs 기준 비교",
    "성능 이탈 감지",
    "베이지안 추정 학습",
    "시각화 분석",
    "앱 소스 다운로드"
])

# 1. 실측 vs 기준 비교
if page == "실측 vs 기준 비교":
    model = st.selectbox("모델 선택", get_models())
    dev = deviation_df[deviation_df['모델명'] == model]
    ref = reference_df[reference_df['모델'] == model]
    cat = catalog_df[catalog_df['모델명'] == model]
    fig, ax = plt.subplots()
    if not dev.empty:
        ax.scatter(dev['유량'], dev['토출양정'], label='실측', marker='x')
    if not ref.empty:
        ax.plot(ref['토출량'], ref['토출양정'], label='기준')
    if not cat.empty:
        ax.plot(cat['유량'], cat['양정'], label='카탈로그', linestyle='--')
    ax.set_xlabel("유량 (Q)")
    ax.set_ylabel("양정 (H)")
    ax.legend()
    st.pyplot(fig)

# 2. 성능 이탈 감지
elif page == "성능 이탈 감지":
    st.write("신규 성적서 업로드 또는 기본 샘플 데이터 사용")
    uploaded = st.file_uploader("엑셀 파일 업로드", type=['xlsx','xlsm'])
    if uploaded:
        new_df = extract_sample_data(uploaded)
    else:
        new_df = sample_df
        st.info("샘플 성적서 데이터 사용 중")
    model = new_df['Product'].iloc[0]
    ref = reference_df[reference_df['모델'] == model]
    fig, ax = plt.subplots()
    ax.plot(new_df['Flow Rate'], new_df['Head'], label='신규 데이터')
    if not ref.empty:
        ax.plot(ref['토출량'], ref['토출양정'], label='기준 데이터')
    ax.set_xlabel("유량 (Q)")
    ax.set_ylabel("양정 (H)")
    ax.set_title(f"{model} 성능 이탈 검토")
    ax.legend()
    st.pyplot(fig)

# 3. 베이지안 추정 학습
elif page == "베이지안 추정 학습":
    model = st.selectbox("모델 선택 (Bayesian)", deviation_df['모델명'].dropna().unique())
    dev = deviation_df[deviation_df['모델명'] == model].dropna(subset=['유량','토출양정','축동력'])
    st.subheader("Q-H 곡선 베이지안 추정")
    with pm.Model() as mod_qh:
        alpha = pm.Normal('alpha', mu=0, sigma=100)
        beta = pm.Normal('beta', mu=0, sigma=10)
        sigma = pm.HalfNormal('sigma', sigma=10)
        mu = alpha + beta * dev['유량'].values
        pm.Normal('y_obs', mu=mu, sigma=sigma, observed=dev['토출양정'].values)
        trace_qh = pm.sample(1000, tune=1000, chains=2, target_accept=0.9)
    fig1, ax1 = plt.subplots()
    az.plot_posterior(trace_qh, var_names=['alpha','beta'], ax=ax1)
    st.pyplot(fig1)

    st.subheader("Q-P 곡선 베이지안 추정")
    with pm.Model() as mod_qp:
        a = pm.Normal('a', mu=0, sigma=100)
        b = pm.Normal('b', mu=0, sigma=10)
        s2 = pm.HalfNormal('s2', sigma=10)
        mu2 = a + b * dev['유량'].values
        pm.Normal('y2', mu=mu2, sigma=s2, observed=dev['축동력'].values)
        trace_qp = pm.sample(1000, tune=1000, chains=2, target_accept=0.9)
    fig2, ax2 = plt.subplots()
    az.plot_posterior(trace_qp, var_names=['a','b'], ax=ax2)
    st.pyplot(fig2)

# 4. 시각화 분석
elif page == "시각화 분석":
    option = st.selectbox("보기 종류", ["Reference Q-H", "Reference Q-P", "Catalog Q-H", "Catalog Q-P"])
    model = st.selectbox("모델 선택", get_models())
    fig, ax = plt.subplots()
    if "Reference" in option:
        df = reference_df[reference_df['모델'] == model]
        x = df['토출량']
        y = df['토출양정'] if 'Q-H' in option else df['축동력']
    else:
        df = catalog_df[catalog_df['모델명'] == model]
        x = df['유량']
        y = df['양정'] if 'Q-H' in option else df['축동력']
    ax.plot(x, y, marker='o')
    ax.set_xlabel("유량 (Q)")
    ax.set_ylabel("양정 (H)" if 'Q-H' in option else "축동력 (kW)")
    ax.set_title(f"{model} {option}")
    st.pyplot(fig)

# 5. 앱 소스 다운로드
else:
    with open(__file__, 'r') as f:
        code = f.read()
    st.download_button("앱 소스 코드 다운로드", code, file_name="pump_streamlit_app.py", mime="text/plain")
