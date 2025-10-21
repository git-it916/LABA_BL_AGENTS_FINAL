import pandas as pd
from datetime import datetime

from aiportfolio.backtest.making_benchmark import prepare_benchmark
from aiportfolio.BL_MVO.prepare.making_excessreturn import final

# python -m aiportfolio.backtest.calculating_performance

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