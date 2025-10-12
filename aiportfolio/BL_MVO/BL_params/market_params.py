import pandas as pd
import numpy as np
import os
from datetime import datetime
from aiportfolio.BL_MVO.prepare.making_excessreturn import final
'''
# 가정: from ..prepare.making_excessreturn import final 코드는
# 아래와 같은 형식의 DataFrame을 반환한다고 가정합니다.
# 실제 실행을 위해 예시 데이터를 생성합니다.
def create_dummy_data():
    dates = pd.to_datetime(pd.date_range(start='2024-04-01', end='2024-04-30', freq='B'))
    sectors = ['Technology', 'Financials', 'Healthcare', 'Industrials']
    data = []
    for date in dates:
        for sector in sectors:
            data.append({
                'date': date,
                'GICS Sector': sector,
                'ExcessReturn': np.random.randn() * 0.01,
                'MKT_SEC': np.random.randint(1000, 5000) * 1e9
            })
    return pd.DataFrame(data)

# from ..prepare.making_excessreturn import final
# 위 라인 대신 예시 함수를 사용합니다.
final = create_dummy_data
'''
# N: 자산 개수
# K: 견해 개수
# sigma: 초과수익률 공분산 행렬 (N*N)
# pi: 내재 시장 균형 초과수익률 벡터 (N*1)

class Market_Params:
    def __init__(self, start_date, end_date):
        self.df = final()
        self.start_date = start_date
        self.end_date = end_date

    # Sigma: 초과수익률 공분산 행렬 (N*N)
    def making_sigma(self):
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        pivot_filtered_df = filtered_df.pivot_table(index='date', columns='GICS Sector', values='ExcessReturn')
        sigma = pivot_filtered_df.cov()
        return sigma

    # Pi: 내재 시장 균형 초과수익률 벡터 (N*1)
    def making_w_mkt(self):
        # 훈련 기간의 종료일이 속한 월을 기준으로 데이터를 필터링
        # 'YYYY-MM' 형식으로 변환하여 해당 월의 모든 데이터를 가져옴
        end_month_str = self.end_date.strftime('%Y-%m')
        
        # self.df['date']가 datetime 객체라고 가정
        filtered_df = self.df[self.df['date'].dt.strftime('%Y-%m') == end_month_str].copy()
        
        # 필터링된 데이터가 비어 있는지 확인하고, 비어있으면 오류 발생
        if filtered_df.empty:
            raise ValueError(f"오류: {end_month_str}에 해당하는 데이터가 없습니다.")

        # 가장 최근 날짜의 MKT_SEC 값만 선택
        # 날짜를 기준으로 내림차순 정렬 후 첫 번째 행을 선택 (가장 마지막 영업일)
        last_day_data = filtered_df.sort_values(by='date', ascending=False).drop_duplicates(subset='GICS Sector')
        
        # MKT_SEC 값을 reshape하여 행렬 곱셈이 가능하도록 함
        # GICS Sector 순서가 sigma와 일치하도록 정렬
        last_day_data = last_day_data.set_index('GICS Sector').loc[self.making_sigma().columns]
        mkt_cap = last_day_data['MKT_SEC'].values.reshape(-1, 1)

        # 총 시가총액 계산
        total_mkt_cap = np.sum(mkt_cap)
        
        # 시장 가중치 계산
        w_mkt = mkt_cap / total_mkt_cap
        
        return w_mkt

    def making_delta(self):
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        ret_mean = filtered_df['ExcessReturn'].mean()
        ret_variance = filtered_df['ExcessReturn'].var()
        delta = ret_mean / ret_variance
        return delta
    
    def making_pi(self):
        w_mkt = self.making_w_mkt()
        delta = self.making_delta()
        sigma = self.making_sigma()
        pi = delta * sigma.values @ w_mkt
        return pi


# 분석할 기간 설정 / 이거 우리  date time 형식이 어떻게 되지..?
start_date = datetime(2021, 5, 1)
end_date = datetime(2024, 4, 30)

# Market_Params 클래스의 인스턴스 생성
market_params_calculator = Market_Params(start_date, end_date)

# 공분산 행렬(sigma) 계산
sigma_matrix = market_params_calculator.making_sigma()

# 내재 시장 균형 초과수익률(pi) 계산
pi_vector = market_params_calculator.making_pi()

# 결과 출력
print("="*60)
print(f"분석 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
print("="*60)
print("계산된 초과수익률 공분산 행렬 (Sigma Matrix):")
print(sigma_matrix)
print("\n" + "="*60)
print("계산된 내재 시장 균형 초과수익률 (Pi Vector):")
print(pi_vector)
print("="*60)