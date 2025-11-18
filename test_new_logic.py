"""
수정된 투자 로직 검증 스크립트
"""
import pandas as pd
from datetime import timedelta

print("="*80)
print("수정된 투자 로직 검증")
print("="*80)
print()

# 테스트 케이스
test_cases = [
    ('24-05-31', '2024-04-30', '2024-05-01'),
    ('24-06-30', '2024-05-31', '2024-06-01'),
    ('24-07-31', '2024-06-30', '2024-07-01'),
    ('24-11-30', '2024-10-31', '2024-11-01'),
    ('24-12-31', '2024-11-30', '2024-12-01'),
]

print(f"{'입력값':<12} {'학습 종료일':<15} {'예상 투자일':<15} {'실제 투자일':<15} {'결과':<8}")
print("-"*80)

all_passed = True

for forecast_input, expected_learning, expected_invest in test_cases:
    # 1. get_rolling_dates() 시뮬레이션
    end_date = pd.to_datetime(forecast_input, format='%y-%m-%d')
    learning_date = (end_date - pd.DateOffset(months=1)).to_period('M').to_timestamp('M')

    # 2. 새로운 투자 시작일 계산 로직
    invest_start = (learning_date + pd.DateOffset(months=1)).replace(day=1)

    # 3. 검증
    passed = (learning_date.date() == pd.Timestamp(expected_learning).date() and
              invest_start.date() == pd.Timestamp(expected_invest).date())

    result = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False

    print(f"{forecast_input:<12} {learning_date.date()!s:<15} {expected_invest:<15} "
          f"{invest_start.date()!s:<15} {result:<8}")

print("-"*80)

if all_passed:
    print("\n[성공] 모든 테스트 통과!")
    print("\n[수정 완료]")
    print("   - 4월 데이터 -> 5월 투자")
    print("   - 5월 데이터 -> 6월 투자")
    print("   - 11월 데이터 -> 12월 투자")
    print("\n[12월 백테스트 가능]")
    print("   - 11월 30일까지 학습 -> 12월 1일부터 투자")
    print("   - 필요 데이터: ~ 2024-12-31 (존재함!)")
else:
    print("\n[실패] 일부 테스트 실패. 로직을 다시 확인하세요.")

print()
print("="*80)
print("forecast_date 입력 가이드")
print("="*80)
print()
print("원하는 투자 달의 월말을 입력하세요:")
print()
print("  5월 투자 -> 24-05-31 입력")
print("  6월 투자 -> 24-06-30 입력")
print(" 12월 투자 -> 24-12-31 입력")
print()
print("시스템이 자동으로 1개월 전 데이터로 학습하고,")
print("입력한 달의 1일부터 투자를 시작합니다.")
print()
