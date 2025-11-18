import pandas as pd
from aiportfolio.util.making_rollingdate import get_rolling_dates

print("="*80)
print("현재 시스템의 동작")
print("="*80)

forecast_period = ['24-05-31', '24-06-30', '24-11-30', '24-12-31']
result = get_rolling_dates(forecast_period)

for r in result:
    print(f"입력: {r['forecast_date'].date()}")
    print(f"  학습 종료일: {r['end_date'].date()} (1개월 전)")
    print(f"  학습 시작일: {r['start_date'].date()} (10년 전)")
    print()

print("="*80)
print("문제점")
print("="*80)
print("입력 24-05-31 -> 학습은 4월 30일까지 (OK)")
print("하지만 forecast_date = 2024-05-31로 저장됨")
print()
print("백테스트에서:")
print("- BL 가중치가 forecast_date = 2024-05-31 시점에 저장")
print("- 투자 시작 = backtest_date + 1일 = 2024-06-01")
print("- 결과: 5월이 아니라 6월에 투자!")
print()

print("="*80)
print("당신이 원하는 방식")
print("="*80)
print("4월 데이터 -> 5월 예측 -> 5월 1일부터 투자")
print("5월 데이터 -> 6월 예측 -> 6월 1일부터 투자")
print("11월 데이터 -> 12월 예측 -> 12월 1일부터 투자")
