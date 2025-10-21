from datetime import datetime
import pandas as pd

from aiportfolio.backtest.making_benchmark import prepare_benchmark

# 3개의 포트폴리오에 대해 준비된 비중, 수익률을 다음달의 수익률로 가중평균

start_date = datetime(2015, 1, 31)
end_date = datetime(2024, 4, 30)

a = prepare_benchmark(start_date=start_date, end_date=end_date)
print("benchmark1")
print(a[0])
# print(a[0][1])
print()
print("benchmark2")
print(a[1])
# print(a[1][1])
print()
print("aiportfolio")
print(a[2].T)