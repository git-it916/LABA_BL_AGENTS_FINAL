import pandas as pd

from aiportfolio.BL_MVO.prepare.making_excessreturn import final
from aiportfolio.BL_MVO.BL_params.market_params import Market_Params
from aiportfolio.BL_MVO.MVO_opt import MVO_Optimizer
from aiportfolio.util.making_rollingdate import get_rolling_dates

# 일단 24년 5월만 예측하기 위해 기간 설정
forecast_period = [
    "24-05-31"
]
forecast_date = get_rolling_dates(forecast_period)
start_date = forecast_date[0]['start_date']
end_date = forecast_date[0]['end_date']

# 공분산
market_params = Market_Params(start_date=start_date, end_date=end_date)
sigma = market_params.making_sigma()

# 섹터구분
SECTOR = sigma.columns

# 수익률
df = final()
filtered_df = df[df["date"] == forecast_date[0]['forecast_date']]
benchmark_return = pd.Series(filtered_df, index=SECTOR)
print(df)

mvo = MVO_Optimizer(benchmark_return, sigma, SECTOR)
w_tan = mvo.optimize_tangency_1()