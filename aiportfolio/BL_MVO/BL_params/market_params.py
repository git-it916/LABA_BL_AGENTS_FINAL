import pandas as pd
import numpy as np
from datetime import datetime
from aiportfolio.BL_MVO.prepare.preprocessing_수정중 import final

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
            mu = filtered_df.groupby('gsector')['sector_excess_return'].mean()
            return mu
    
    # Sigma: 초과수익률 공분산 행렬 (N*N)
    def making_sigma(self):
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        pivot_filtered_df = filtered_df.pivot_table(index='date', columns='gsector', values='sector_excess_return')
        sigma = pivot_filtered_df.cov()
        sectors = sigma.columns.tolist()

        # 공분산 행렬의 인덱스가 정해진 순서와 일치하지 않는다면 에러 발생
        expected_index = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        if not isinstance(sigma, pd.DataFrame):
            raise TypeError("sigma[0] must be a pandas DataFrame (covariance matrix)")

        if list(sigma.index) != expected_index or list(sigma.columns) != expected_index:
            raise ValueError(
                f"Covariance matrix index/columns mismatch.\n"
                f"Expected: {expected_index}\n"
                f"Got index: {list(sigma.index)}\n"
                f"Got columns: {list(sigma.columns)}"
            )

        return sigma, sectors

    # Pi: 내재 시장 균형 초과수익률 벡터 (N*1)
    def making_w_mkt(self, sigma_sectors):
        end_month_str = self.end_date.strftime('%Y-%m')
        filtered_df = self.df[self.df['date'].dt.strftime('%Y-%m') == end_month_str].copy()

        # 계산의 정확성을 위해 gsector가 11개인지 확인하고 인덱스로 설정
        if len(filtered_df['gsector'].unique()) == 11:
            filtered_df = filtered_df.set_index('gsector')
        else:
            raise ValueError(f"gsector의 고유값 개수가 11이 아닙니다. (현재 {len(filtered_df['gsector'].unique())}개)")

        total_mkt_cap = filtered_df['sector_mktcap'].sum()
        
        # 시장 가중치 계산
        w_mkt = filtered_df['sector_mktcap'] / total_mkt_cap
        
        # 계산의 정확성을 위해 w_mkt.index와 sigma_sectors 리스트 비교
        if (w_mkt.index == sigma_sectors).all():
            pass
        else:
            raise ValueError(
                f"w_mkt.index와 sectors가 일치하지 않습니다.\n"
                f"w_mkt.index: {w_mkt.index}\n"
                f"sectors: {sigma_sectors}"
            )
        
        # 섹터 반환
        sectors = w_mkt.index.tolist()

        return w_mkt, sectors
    
    def making_delta(self):
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        
        # 시총가중 수익률 생성
        filtered_df["_ret_x_cap_1"] = filtered_df["sector_excess_return"] * filtered_df["sector_prevmktcap"] # excess_return
        filtered_df["_ret_x_cap_2"] = filtered_df["sector_return"] * filtered_df["sector_prevmktcap"] # 그냥 수익률
        agg = (
            filtered_df.groupby("date", dropna=False)
                .agg(total_mktcap=("sector_prevmktcap", "sum"),
                    ret_x_cap_1_sum=("_ret_x_cap_1", "sum"),
                    ret_x_cap_2_sum=("_ret_x_cap_2", "sum"))
                .reset_index()
        )
        mask = agg["total_mktcap"] != 0
        agg["total_excess_return"] = agg["ret_x_cap_1_sum"].div(agg["total_mktcap"]).where(mask)
        agg["total_return"]        = agg["ret_x_cap_2_sum"].div(agg["total_mktcap"]).where(mask)
        agg = agg.drop(columns=["ret_x_cap_1_sum", "ret_x_cap_2_sum"])  # 중간열 제거
        
        # delta 계산
        ret_mean = agg['total_excess_return'].mean()
        ret_variance = agg['total_return'].var()
        delta = ret_mean / ret_variance
        return delta
    
    def making_pi(self):
        sigma = self.making_sigma()
        w_mkt = self.making_w_mkt(sigma[1])
        delta = self.making_delta()
        pi = delta * sigma[0].values @ w_mkt[0]

        return pi