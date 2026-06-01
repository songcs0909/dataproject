import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="기온 상승 트렌드 분석 앱", layout="wide")
st.title("🌡️ 1980년대 전후 기온 상승 트렌드 비교 분석")
st.markdown("""
GitHub 저장소에 저장된 기상청 기온 데이터(`ta_20260601093156.csv`)를 기반으로  
1980년 이전과 이후의 기온 상승 속도를 자동으로 분석하고 가설을 검증합니다.
""")

# 데이터 파일 이름 정의
DATA_FILENAME = "ta_20260601093156.csv"

# 2. 파일 존재 여부 확인 후 데이터 로드
if os.path.exists(DATA_FILENAME):
    try:
        # 데이터 로드 및 전처리
        # 기상청 데이터의 한글 인코딩(cp949) 및 공백 제거 처리
        df = pd.read_csv(DATA_FILENAME, encoding='cp949')
        
        df.columns = df.columns.str.strip()
        df['날짜'] = df['날짜'].astype(str).str.replace('\t', '').str.strip()
        df['날짜'] = pd.to_datetime(df['날짜'])
        df['연도'] = df['날짜'].dt.year
        
        # 연도별 평균 기온 계산
        annual_df = df.groupby('연도')['평균기온(℃)'].mean().reset_index()
        
        # 결측치나 비정상 데이터 제외 (예: 데이터가 없는 해가 있을 경우 대비)
        annual_df = annual_df.dropna()

        # 3. 사이드바 - 분석 기준점 설정
        st.sidebar.header("📊 분석 설정")
        split_year = st.sidebar.slider("트렌드를 나눌 기준 연도를 선택하세요", 
                                       min_value=int(annual_df['연도'].min()), 
                                       max_value=int(annual_df['연도'].max()), 
                                       value=1980)
        
        # 데이터 분할
        df_before = annual_df[annual_df['연도'] <= split_year]
        df_after = annual_df[annual_df['연도'] > split_year]
        
        # 4. 주요 지표(Metrics) 시각화
        mean_before = df_before['평균기온(℃)'].mean()
        mean_after = df_after['평균기온(℃)'].mean()
        diff = mean_after - mean_before
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label=f"{split_year}년 이전 평균 기온", value=f"{mean_before:.2f} ℃")
        col2.metric(label=f"{split_year}년 이후 평균 기온", value=f"{mean_after:.2f} ℃")
        col3.metric(label="평균 기온 상승 폭", value=f"+{diff:.2f} ℃", delta=f"{diff:.2f} ℃")
        
        st.markdown("---")
        
        # 5. 회귀선(Trendline) 계산 함수
        def get_trendline(df_sub):
            if len(df_sub) > 1:
                slope, intercept = np.polyfit(df_sub['연도'], df_sub['평균기온(℃)'], 1)
                return slope, intercept, slope * 10  # slope * 10 = 10년당 상승 기온
            return 0, 0, 0

        slope_b, intercept_b, decade_b = get_trendline(df_before)
        slope_a, intercept_a, decade_a = get_trendline(df_after)
        
        # 6. 메인 시각화 (Plotly 차트)
        st.subheader("📈 연도별 평균 기온 추이 및 추세선 비교")
        
        fig = go.Figure()
        
        # 전체 데이터 산점도
        fig.add_trace(go.Scatter(x=annual_df['연도'], y=annual_df['평균기온(℃)'],
                                 mode='markers', name='연평균 기온',
                                 marker=dict(color='gray', opacity=0.6)))
        
        # 기준년 이전 추세선
        if len(df_before) > 1:
            fig.add_trace(go.Scatter(x=df_before['연도'], y=slope_b * df_before['연도'] + intercept_b,
                                     mode='lines', name=f'{split_year}년 이전 추세선',
                                     line=dict(color='blue', width=3)))
            
        # 기준년 이후 추세선
        if len(df_after) > 1:
            fig.add_trace(go.Scatter(x=df_after['연도'], y=slope_a * df_after['연도'] + intercept_a,
                                     mode='lines', name=f'{split_year}년 이후 추세선',
                                     line=dict(color='red', width=3)))
            
        # 수직 기준선
        fig.add_vline(x=split_year, line_dash="dash", line_color="green", 
                      annotation_text=f"{split_year}년 기준", annotation_position="top left")
        
        fig.update_layout(
            xaxis_title="연도",
            yaxis_title="평균 기온 (℃)",
            hovermode="x unified",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 7. 가설 검증 결과 요약문
        st.subheader("💡 가설 검증 결과 요약")
        st.markdown(f"""
        - **{split_year}년 이전**에는 매 10년마다 평균 기온이 약 **{decade_b:.3f}℃** 상승(또는 변화)했습니다.
        - **{split_year}년 이후**에는 매 10년마다 평균 기온이 약 **{decade_a:.3f}℃** 상승하고 있습니다.
        """)
        
        if decade_a > decade_b:
            st.success(f"🎉 **가설 지지:** {split_year}년 이후의 기온 상승 속도가 이전보다 **{decade_a - decade_b:.3f}℃/10년** 더 빠릅니다! 1980년대 이후 기온 상승이 가속화되었다는 가설을 뒷받침하는 강력한 증거입니다.")
        else:
            st.warning(f"⚠️ **가설과 다름:** {split_year}년 이후의 기온 상승 속도가 이전보다 가속화되었다고 보기 어렵거나 완만합니다.")
            
        # 8. 데이터 테이블 확인
        with st.expander("🔍 처리된 연도별 요약 데이터 보기"):
            st.dataframe(annual_df.style.format({'평균기온(℃)': '{:.2f}'}), use_container_width=True)

    except Exception as e:
        st.error(f"데이터를 처리하는 중 오류가 발생했습니다. 오류 메시지: {e}")
else:
    st.error(f"❌ 저장소 내에서 `{DATA_FILENAME}` 파일을 찾을 수 없습니다. 파일명이 정확히 일치하는지 GitHub 저장소를 확인해 주세요.")
