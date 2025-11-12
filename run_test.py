"""
테스트용 실행 스크립트 (대화형 입력 없이 자동 실행)
"""
import os
from datetime import datetime

from aiportfolio.scene import scene

#######################################
# Test Configuration
#######################################

print("\n" + "="*80)
print("Black-Litterman Portfolio Optimization with LLM - TEST MODE")
print("="*80 + "\n")

# 테스트 설정
simul_name = 'test_validation'
Tier = 1
forecast_period = ["24-05-31"]  # 단일 기간으로 빠른 테스트
tau = 0.025

# 설정 출력
print("테스트 설정:")
print(f"  시뮬레이션 이름: {simul_name}")
print(f"  분석 단계(Tier): {Tier}")
print(f"  예측 기간: {forecast_period}")
print(f"  불확실성 계수(tau): {tau}")
print("="*80 + "\n")

#######################################
# run
#######################################

print("프로그램 실행 시작...\n")

try:
    BL_results = scene(simul_name=simul_name, Tier=Tier, tau=tau, forecast_period=forecast_period)

    print("\n" + "="*80)
    print("[성공] 프로그램 실행 완료")
    print("="*80)
    print(f"\n결과 저장 위치: database/logs/Tier{Tier}/result_of_BL-MVO/{simul_name}.json")
    print("="*80 + "\n")

    print("결과 요약:")
    for i, result in enumerate(BL_results, 1):
        print(f"\n[기간 {i}] {result['forecast_date']}")
        print(f"섹터별 비중:")
        for sector, weight in zip(result['SECTOR'], result['w_aiportfolio']):
            print(f"  {sector}: {weight}")

except Exception as e:
    print("\n" + "="*80)
    print("[오류] 프로그램 실행 중 오류 발생")
    print("="*80)
    print(f"오류 내용: {e}")
    print("="*80 + "\n")

    import traceback
    print("상세 오류 정보:")
    traceback.print_exc()

    raise
