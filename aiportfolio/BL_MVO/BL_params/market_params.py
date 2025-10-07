import pandas as pd
import numpy as np
import os

from ..prepare.making_excessreturn import final

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
        end_month = self.end_date.strftime('%Y-%m')
        filtered_df = self.df[self.df['date'].dt.strftime('%Y-%m') == end_month].copy()
        
        # 필터링된 데이터가 비어 있는지 확인하고, 비어있으면 오류 발생
        if filtered_df.empty:
            raise ValueError(f"오류: {end_month}에 해당하는 데이터가 없습니다.")

        # 가장 최근 날짜의 MKT_SEC 값만 선택
        # 날짜를 기준으로 내림차순 정렬 후 첫 번째 행을 선택 (가장 마지막 영업일)
        last_day_data = filtered_df.sort_values(by='date', ascending=False).drop_duplicates(subset='GICS Sector')
        
        # MKT_SEC 값을 reshape하여 행렬 곱셈이 가능하도록 함
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
        pi = delta * sigma @ w_mkt
        return pi