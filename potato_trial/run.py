import os
from datetime import datetime

from aiportfolio.scene import scene

#######################################
# Interactive Configuration
#######################################

print("\n" + "="*80)
print("Black-Litterman Portfolio Optimization with LLM")
print("="*80 + "\n")

# 1. 시뮬레이션 이름 입력
print("[1/4] 시뮬레이션 이름을 입력하세요.")
print("      (결과 파일 식별에 사용됩니다)")
simul_name = input("      입력 (기본값: test1): ").strip()
if not simul_name:
    simul_name = 'test1'
    print(f"      → 기본값 사용: {simul_name}")

# 2. Tier 선택
print("\n[2/4] 분석 단계(Tier)를 선택하세요.")
print("      Tier 1: 기술적 지표 (CAGR, 수익률, 변동성, Z-score, 추세)")
print("      Tier 2: 회계 지표 (P/E, ROE 등) - 미구현")
print("      Tier 3: 거시 지표 (금리, 인플레이션 등) - 미구현")
while True:
    tier_input = input("      입력 (1/2/3, 기본값: 1): ").strip()
    if not tier_input:
        Tier = 1
        print(f"      → 기본값 사용: Tier {Tier}")
        break
    elif tier_input in ['1', '2', '3']:
        Tier = int(tier_input)
        if Tier in [2, 3]:
            print(f"      ⚠️  경고: Tier {Tier}는 아직 구현되지 않았습니다.")
            confirm = input("      계속하시겠습니까? (y/n): ").strip().lower()
            if confirm != 'y':
                print("      → Tier 1로 변경합니다.")
                Tier = 1
        break
    else:
        print("      ❌ 잘못된 입력입니다. 1, 2, 3 중 하나를 입력하세요.")

# 3. 예측 기간 입력
print("\n[3/4] 예측 기간을 입력하세요.")
print("      형식: YY-MM-DD (예: 24-05-31)")
print("      여러 날짜 입력 시 쉼표로 구분 (예: 24-05-31, 24-06-30)")
print("      또는 엔터를 누르면 기본 기간 사용 (2024년 5월~12월)")
forecast_input = input("      입력: ").strip()

if not forecast_input:
    # 기본값: 2024년 5월~12월
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
    print(f"      → 기본값 사용: 2024년 5월~12월 (8개 기간)")
else:
    # 사용자 입력 파싱
    forecast_period = [date.strip() for date in forecast_input.split(',')]
    print(f"      → 입력된 기간: {len(forecast_period)}개")
    for i, date in enumerate(forecast_period, 1):
        print(f"         {i}. {date}")

# 4. tau 값 입력
print("\n[4/4] Black-Litterman 불확실성 계수(tau)를 입력하세요.")
print("      일반적 범위: 0.01 ~ 0.05")
print("      - 작은 값 (0.01): 시장 균형에 더 의존")
print("      - 큰 값 (0.05): LLM 뷰에 더 의존")
while True:
    tau_input = input("      입력 (기본값: 0.025): ").strip()
    if not tau_input:
        tau = 0.025
        print(f"      → 기본값 사용: {tau}")
        break
    else:
        try:
            tau = float(tau_input)
            if 0.001 <= tau <= 0.1:
                break
            else:
                print("      ⚠️  경고: tau는 일반적으로 0.001~0.1 범위입니다.")
                confirm = input(f"      {tau}를 사용하시겠습니까? (y/n): ").strip().lower()
                if confirm == 'y':
                    break
        except ValueError:
            print("      ❌ 잘못된 입력입니다. 숫자를 입력하세요.")

# 설정 확인
print("\n" + "="*80)
print("설정 확인")
print("="*80)
print(f"시뮬레이션 이름: {simul_name}")
print(f"분석 단계(Tier): {Tier}")
print(f"예측 기간: {len(forecast_period)}개 기간")
for i, date in enumerate(forecast_period, 1):
    print(f"  {i}. {date}")
print(f"불확실성 계수(tau): {tau}")
print("="*80)

# 최종 확인
confirm = input("\n위 설정으로 실행하시겠습니까? (y/n): ").strip().lower()
if confirm != 'y':
    print("\n프로그램을 종료합니다.")
    exit(0)

#######################################
# run
#######################################

print("\n" + "="*80)
print("프로그램 실행 시작")
print("="*80 + "\n")

try:
    BL_results = scene(simul_name=simul_name, Tier=Tier, tau=tau, forecast_period=forecast_period)

    print("\n" + "="*80)
    print("프로그램 실행 완료")
    print("="*80)
    print(f"\n결과 저장 위치: database/logs/Tier{Tier}/result_of_BL-MVO/{simul_name}.json")
    print("="*80 + "\n")

except Exception as e:
    print("\n" + "="*80)
    print("프로그램 실행 중 오류 발생")
    print("="*80)
    print(f"오류 내용: {e}")
    print("="*80 + "\n")
    raise