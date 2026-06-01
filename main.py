import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from statsmodels.api import OLS, add_constant

# 한글 폰트 설정 (스트림릿 클라우드 리눅스 환경 고려)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="기온 상승 추세 분석기", layout="wide")

st.title("🌡️ 1980년대 전후 기온 상승 추세 비교 분석")
st.markdown("""
본 웹앱은 1980년대를 기점으로 기온 상승 속도가 달라졌다는 가설을 검증하기 위해 제작되었습니다.
기상청 장기 관측 데이터를 바탕으로 **1980년 이전**과 **1980년 이후**의 연평균 기온 변화율(회귀계수)을 비교합니다.
""")

# 데이터 로드 함수
@st.cache_data
def load_data():
    # 파일 읽기
    df = pd.read_csv('ta_20260601093156.csv', encoding='utf-8')
    
    # 컬럼명 공백 제거 및 정제
    df.columns = df.columns.str.strip()
    
    # 날짜 데이터의 '\t' 문자 제거 후 datetime 변환
    df['날짜'] = df['날짜'].astype(str).str.replace('\t', '').str.strip()
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 연도 컬럼 생성
    df['연도'] = df['날짜'].dt.year
    
    # 연평균 기온 계산 (결측치가 있을 수 있으므로 연도별 평균)
    # 기상청 컬럼명 맞춤: '평균기온(℃)'
    target_col = '평균기온(℃)'
    if target_col not in df.columns:
        # 혹시 모를 컬럼명 매칭 예외 처리
        target_col = [c for c in df.columns if '평균' in c][0]
        
    annual_df = df.groupby('연to')[target_col].mean().reset_index()
    annual_df.columns = ['연도', '연평균기온']
    return annual_df

try:
    data = load_data()
    
    # 데이터 분할 (1980년 기준)
    before_1980 = data[data['연도'] < 1980]
    after_1980 = data[data['연to'] >= 1980]
    
    # 사이드바 레이아웃
    st.sidebar.header("📊 데이터 요약")
    st.sidebar.write(f"전체 관측 기간: {data['연도'].min()}년 ~ {data['연도'].max()}년")
    st.sidebar.write(f"1980년 이전 데이터 수: {len(before_1980)}개 연도")
    st.sidebar.write(f"1980년 이후 데이터 수: {len(after_1980)}개 연도")

    # 통계 분석 (선형 회귀) 계산 함수
    def get_trend(df):
        X = add_constant(df['연도'])
        y = df['연평균기온']
        model = OLS(y, X).fit()
        slope = model.params['연도']  # 1년당 기온 상승량
        r_squared = model.rsquared
        return slope, r_squared

    slope_before, r2_before = get_trend(before_1980)
    slope_after, r2_after = get_trend(after_1980)

    # 지표 시각화 (KPI 마크다운)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="📉 1980년 이전 10년당 기온 변화", 
            value=f"+{slope_before * 10:.3f} °C",
            delta="상승 느림"
        )
        st.caption(f"결정계수 (R²): {r2_before:.3f}")
        
    with col2:
        st.metric(
            label="📈 1980년 이후 10년당 기온 변화", 
            value=f"+{slope_after * 10:.3f} °C",
            delta=f"이전 대비 {((slope_after/slope_before) if slope_before != 0 else 0):.1f}배 속도",
            delta_color="inverse"
        )
        st.caption(f"결정계수 (R²): {r2_after:.3f}")

    st.markdown("---")
    
    # 시각화 (그래프)
    st.subheader("📈 기간별 기온 상승 추세선 비교 그래프")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 전체 데이터 산점도
    sns.scatterplot(data=data, x='연도', y='연평균기온', color='gray', alpha=0.5, ax=ax, label='연평균 기온 관측치')
    
    # 1980년 이전 회귀선
    sns.regplot(data=before_1980, x='연도', y='연평균기온', scatter=False, ax=ax, 
                color='blue', label=f'1980년 이전 추세 (10년당 +{slope_before*10:.2f}°C)')
    
    # 1980년 이후 회귀선
    sns.regplot(data=after_1980, x='연도', y='연평균기온', scatter=False, ax=ax, 
                color='red', label=f'1980년 이후 추세 (10년당 +{slope_after*10:.2f}°C)')
    
    # 1980년 구분선
    ax.axvline(x=1980, color='purple', linestyle='--', alpha=0.7, label='1980년 기준선')
    
    ax.set_title('연도별 평균 기온 및 기간별 추세선 비교', fontsize=14, pad=15)
    ax.set_xlabel('연도', fontsize=12)
    ax.set_ylabel('평균 기온 (°C)', fontsize=12)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=11)
    
    st.pyplot(fig)

    # 결론 및 데이터 표
    st.markdown("---")
    st.subheader("💡 가설 검증 결과 요약")
    if slope_after > slope_before:
        st.success(f"**가설이 지지됩니다!** 1980년 이후 기온 상승 속도(10년당 {slope_after*10:.2f}°C)가 1980년 이전(10년당 {slope_before*10:.2f}°C)보다 더 가파르게 나타납니다.")
    else:
        st.warning("1980년 전후의 기온 상승 속도 차이가 가설과 다르거나 유의미하지 않습니다. 데이터를 다시 확인해보세요.")

    with st.expander("정제된 연도별 데이터 보기"):
        st.dataframe(data.sort_values(by='연도', ascending=False), use_container_width=True)

except FileNotFoundError:
    st.error("❌ `ta_20260601093156.csv` 파일을 찾을 수 없습니다. 깃허브 저장소 내 app.py와 같은 위치에 파일을 올려주세요.")
except Exception as e:
    st.error(f"❌ 오류가 발생했습니다: {e}")
