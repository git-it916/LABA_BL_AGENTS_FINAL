import pandas as pd

from aiportfolio.scene import scene
from aiportfolio.test import test

#######################################
# configuration
#######################################
# 연구 기간
'''
forecast_period = [
    "24-05-31"
]
'''

forecast_period = [
    "24-05-31",
    "24-06-30",
    "24-07-31",
    "24-08-31",
    "24-09-30",
    "24-10-31",
    "24-11-30",
    "24-12-31"
]


# tau: 시장 불확실성(조정계수)
tau = 0.025

#######################################
# run
#######################################

BL_results = scene(tau=tau, forecast_period=forecast_period)
backtest = test(forecast_period=forecast_period)

for name, result in zip(
    ['Benchmark 1', 'Benchmark 2', 'AI Portfolio'],
    backtest
):
    print(f"\n📊 {name} 결과 요약")
    print("-" * 40)
    for key, value in result.items():
        # tail(1) 결과가 DataFrame 형태이므로 float로 변환해주는 게 깔끔함
        val = value.values[0] if hasattr(value, "values") else value
        print(f"{key:10s}: {val:.6f}")