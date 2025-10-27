import pandas as pd
import numpy as np
from datetime import datetime
from aiportfolio.BL_MVO.prepare.preprocessing import final

# N: 자산 개수
# K: 견해 개수
# sigma: 초과수익률 공분산 행렬 (N*N)
# pi: 내재 시장 균형 초과수익률 벡터 (N*1)

class Market_Params:
    def __init__(self, start_date, end_date):
        self.df = final()
        self.start_date = start_date
        self.end_date = end_date
    
    # mu: 초과수익률의 기대수익률
    def making_mu(self):
            filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
            mu = filtered_df.groupby('gsector')['sector_return'].mean()
            return mu
    
    # Sigma: 초과수익률 공분산 행렬 (N*N)
    def making_sigma(self):
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        pivot_filtered_df = filtered_df.pivot_table(index='date', columns='gsector', values='cap_weighted_return')
        sigma = filtered_df['sector_return'].cov()
        return sigma

    # Pi: 내재 시장 균형 초과수익률 벡터 (N*1)
    def making_w_mkt(self):
        end_month_str = self.end_date.strftime('%Y-%m')
        filtered_df = self.df[self.df['date'].dt.strftime('%Y-%m') == end_month_str].copy()
        
        # 총 시가총액 계산
        total_mkt_cap = filtered_df['mktcap'].sum()
        
        # 시장 가중치 계산
        w_mkt = filtered_df['mktcap'] / total_mkt_cap

        # 섹터 반환
        sector = filtered_df['gsector'].tolist()

        return w_mkt, sector
    
    def making_delta(self):
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        ret_mean = filtered_df['sector_return'].mean()
        ret_variance = filtered_df['sector_return'].var()
        delta = ret_mean / ret_variance
        return delta
    
    def making_pi(self):
        w_mkt = self.making_w_mkt()[0]
        delta = self.making_delta()
        sigma = self.making_sigma()
        pi = delta * sigma.values @ w_mkt
        return pi