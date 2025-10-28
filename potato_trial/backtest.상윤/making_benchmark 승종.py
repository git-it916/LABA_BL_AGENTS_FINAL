import pandas as pd
from datetime import datetime

from aiportfolio.BL_MVO.BL_params.market_params import Market_Params
from aiportfolio.BL_MVO.MVO_opt import MVO_Optimizer
from aiportfolio.BL_MVO.prepare.making_excessreturn import final
from aiportfolio.backtest.open_log import open_log

# python -m aiportfolio.backtest.calculating_performance

class BackTest:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.df_forecast = final()

    def prepare_benchmark(self):

        # benchmark1 비중 및 섹터 데이터프레임
        market_params = Market_Params(self.start_date, self.end_date)


        # benchmark2 비중 및 섹터 데이터프레임
        mu_benchmark2 = market_params.making_mu()
        sigma_benchmark2 = market_params.making_sigma()
        sectors_benchmark2 = list(sigma_benchmark2.columns)

        mvo = MVO_Optimizer(mu=mu_benchmark2, sigma=sigma_benchmark2, sectors=sectors_benchmark2)
        w_benchmark2 = mvo.optimize_tangency_1()

        benchmark2 = pd.DataFrame({'SECTOR': w_benchmark2[1], 'Weight': w_benchmark2[0].flatten()})

        # aiportfoilo 비중 및 섹터 데이터프레임
        aiportfoilo = open_log()

        return benchmark2, aiportfoilo

    def calculating_performance(self, df_sector_weight):
        # 예측할 month의 데이터만 필터링
        forecast_date = self.end_date + pd.DateOffset(months=1) + pd.offsets.MonthEnd(0)
        df_filtered = self.df_forecast[
            (self.df_forecast['date'].dt.year == forecast_date.year) &
            (self.df_forecast['date'].dt.month == forecast_date.month)
        ]

        # 가중수익률 계산
        merged_portfolio = pd.merge(
        df_sector_weight,
        df_filtered,
        left_on='SECTOR',
        right_on='GICS Sector',
        how='inner'
        )

        merged_portfolio['Weighted_Return'] = merged_portfolio['Weight'] * merged_portfolio['ExcessReturn']
        performance_portfolio = merged_portfolio['Weighted_Return'].sum()

        return performance_portfolio

'''
start_date = datetime(2015, 1, 31)
end_date = datetime(2024, 4, 30)

a = prepare_benchmark(start_date=start_date, end_date=end_date)

df_forecast = final()
forecast_date = end_date + pd.DateOffset(months=1) + pd.offsets.MonthEnd(0)

df_filtered = df_forecast[
    (df_forecast['date'].dt.year == forecast_date.year) &
    (df_forecast['date'].dt.month == forecast_date.month)
]

# calculating performance of benchmark1
merged_benchmark1 = pd.merge(
    a[0],
    df_filtered,
    left_on='SECTOR',
    right_on='GICS Sector',
    how='inner'
)

merged_benchmark1['Weighted_Return'] = merged_benchmark1['Weight'] * merged_benchmark1['ExcessReturn']
performance_benchmark1 = merged_benchmark1['Weighted_Return'].sum()

# calculating performance of benchmark2
merged_benchmark2 = pd.merge(
    a[1],
    df_filtered,
    left_on='SECTOR',
    right_on='GICS Sector',
    how='inner'
)

merged_benchmark2['Weighted_Return'] = merged_benchmark2['Weight'] * merged_benchmark2['ExcessReturn']
performance_benchmark2 = merged_benchmark2['Weighted_Return'].sum()

# calculating performance of aiportfolio
merged_aiportfolio = pd.merge(
    a[2],
    df_filtered,
    left_on='SECTOR',
    right_on='GICS Sector',
    how='inner'
)

merged_aiportfolio['Weighted_Return'] = merged_aiportfolio['Weight'] * merged_aiportfolio['ExcessReturn']
performance_aiportfolio = merged_aiportfolio['Weighted_Return'].sum()

print("-------calculating performance of benchmark1-------")
print("benchmark1 가중치")
print(a[0])
print()
print("benchmark1 성과")
print(performance_benchmark1)
print()
print("-------calculating performance of benchmark2-------")
print("benchmark2 가중치")
print(a[1])
print()
print("benchmark2 성과")
print(performance_benchmark2)
print()
print("-------calculating performance of aiportfolio-------")
print("aiportfolio 가중치")
print(a[2])
print()
print("aiportfolio 성과")
print(performance_aiportfolio)
'''