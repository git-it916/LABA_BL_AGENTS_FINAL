"""
대화형 단일 시점 Black-Litterman 포트폴리오 최적화 및 백테스트 실행 스크립트

이 스크립트는 다음을 수행합니다:
1. 사용자로부터 날짜, Tier, 시뮬레이션 이름 입력 받기
2. LLM으로 섹터 뷰 생성
3. Black-Litterman 모델로 포트폴리오 최적화
4. 백테스트 수행
5. 결과 출력 및 저장

실행: python run_single.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

# 프로젝트 모듈 임포트
from aiportfolio.scene import scene
from aiportfolio.backtest.data_prepare import (
    calculate_monthly_mvo_weights,
    calculate_monthly_market_weights,  # 신규 추가
    open_log
)
from aiportfolio.backtest.final_Ret import load_daily_returns, calculate_performance


def validate_date(date_str):
    """날짜 형식 검증 (YYYY-MM-DD)"""
    try:
        return pd.to_datetime(date_str)
    except:
        return None


def get_user_input():
    """사용자로부터 입력 받기"""
    print("\n" + "="*80)
    print("Black-Litterman 포트폴리오 최적화 및 백테스트 시스템")
    print("="*80)

    # 시뮬레이션 이름
    simul_name = input("\n시뮬레이션 이름을 입력하세요 (예: my_simulation): ").strip()
    if not simul_name:
        simul_name = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[알림] 기본 이름으로 설정됨: {simul_name}")

    # Tier 선택
    while True:
        tier_input = input("\nTier를 선택하세요 (1: 기술적 지표만, 2: 기술적+회계, 3: 모든 지표): ").strip()
        if tier_input in ['1', '2', '3']:
            tier = int(tier_input)
            break
        else:
            print("[오류] 1, 2, 3 중 하나를 입력하세요.")

    # 예측 날짜
    while True:
        forecast_date = input("\n예측 날짜를 입력하세요 (YYYY-MM-DD 형식, 예: 2024-05-31): ").strip()
        validated_date = validate_date(forecast_date)
        if validated_date:
            # 월말로 변환
            forecast_date = validated_date + pd.offsets.MonthEnd(0)
            break
        else:
            print("[오류] 올바른 날짜 형식을 입력하세요 (YYYY-MM-DD).")

    # tau 값
    while True:
        tau_input = input("\ntau 값을 입력하세요 (기본값 0.025, 범위 0.01~0.1): ").strip()
        if not tau_input:
            tau = 0.025
            print(f"[알림] 기본값 사용: {tau}")
            break
        try:
            tau = float(tau_input)
            if 0.01 <= tau <= 0.1:
                break
            else:
                print("[오류] tau 값은 0.01에서 0.1 사이여야 합니다.")
        except:
            print("[오류] 숫자를 입력하세요.")

    # 백테스트 기간 (일수)
    while True:
        days_input = input("\n백테스트 기간을 입력하세요 (영업일 기준, 기본값 20일, 범위 5~250일): ").strip()
        if not days_input:
            backtest_days = 20
            print(f"[알림] 기본값 사용: {backtest_days}일")
            break
        try:
            backtest_days = int(days_input)
            if 5 <= backtest_days <= 250:
                break
            else:
                print("[오류] 백테스트 기간은 5일에서 250일 사이여야 합니다.")
        except:
            print("[오류] 정수를 입력하세요.")

    return {
        'simul_name': simul_name,
        'tier': tier,
        'forecast_date': forecast_date,
        'tau': tau,
        'backtest_days': backtest_days
    }


def run_single_backtest(simul_name, tier, forecast_date, tau, backtest_days=20):
    """단일 시점에 대한 전체 워크플로우 실행"""

    print("\n" + "="*80)
    print("1단계: LLM 뷰 생성 및 Black-Litterman 최적화")
    print("="*80)

    # 날짜 형식 변환
    forecast_date_str = forecast_date.strftime('%y-%m-%d')

    try:
        # scene 함수 실행 (LLM 뷰 생성 + BL 최적화)
        print(f"\n[실행] 시뮬레이션: {simul_name}, Tier: {tier}, 날짜: {forecast_date.date()}")
        results = scene(
            simul_name=simul_name,
            Tier=tier,
            tau=tau,
            forecast_period=[forecast_date_str]
        )

        if not results or len(results) == 0:
            print("\n[오류] BL 최적화 결과가 없습니다.")
            return None

        print(f"\n[성공] BL 최적화 완료")
        print(f"포트폴리오 가중치:")
        for sector, weight in zip(results[0]['SECTOR'], results[0]['w_aiportfolio']):
            print(f"  {sector}: {weight}")

    except Exception as e:
        print(f"\n[오류] BL 최적화 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 백테스트 실행
    print("\n" + "="*80)
    print("2단계: 백테스트 수행")
    print("="*80)

    try:
        # 백테스트 기간 설정
        # 거래일 기준 backtest_days를 확보하기 위해 충분한 캘린더 일수 계산
        # 거래일은 약 주 5일 (주말 제외) = 연간 약 252일
        # 안전하게 거래일 * 2.0 + 30일 여유분
        calendar_days = int(backtest_days * 2.0) + 30

        # 투자 시작일 (forecast_date 다음 날부터)
        invest_start = forecast_date + timedelta(days=1)
        invest_end = invest_start + timedelta(days=calendar_days)

        # MVO 학습 기간
        hist_start = forecast_date - pd.DateOffset(years=10)  # 10년 전부터 학습

        print(f"\n[설정] 학습 기간: {hist_start.date()} ~ {forecast_date.date()}")
        print(f"[설정] 데이터 수집 기간: {invest_start.date()} ~ {invest_end.date()}")
        print(f"[설정] 목표 거래일: {backtest_days}일")

        # ✅ 벤치마크 일관성 검증: 모든 가중치는 forecast_date 시점 기준
        print("\n" + "="*50)
        print("[검증] 벤치마크 일관성 체크")
        print("="*50)
        print(f"  - 모든 포트폴리오 가중치 기준일: {forecast_date.date()}")
        print(f"  - 백테스트 시작일: {invest_start.date()} (forecast_date 다음날)")
        print(f"  - 백테스트 종료일: {invest_end.date()}")
        print("="*50)

        # Market Portfolio 가중치 계산
        print("\n[실행] Market Portfolio 가중치 계산 중...")
        market_weights_df = calculate_monthly_market_weights(
            investment_start_date=forecast_date.strftime('%Y-%m-%d'),  # ✅ forecast_date만 계산
            investment_end_date=forecast_date.strftime('%Y-%m-%d')
        )

        # MVO 가중치 계산
        # ✅ 중요: MVO도 forecast_date 시점의 가중치를 계산해야 BL과 비교 가능
        print("[실행] MVO 벤치마크 가중치 계산 중...")
        mvo_weights_df = calculate_monthly_mvo_weights(
            hist_start_date=hist_start.strftime('%Y-%m-%d'),
            investment_start_date=forecast_date.strftime('%Y-%m-%d'),  # ✅ forecast_date로 시작
            investment_end_date=forecast_date.strftime('%Y-%m-%d')     # ✅ forecast_date만 계산
        )

        # BL 가중치 로드
        print("[실행] BL 포트폴리오 가중치 로드 중...")
        bl_weights_df = open_log(simul_name=simul_name, Tier=tier)

        if bl_weights_df is None or bl_weights_df.empty:
            print("[오류] BL 가중치를 로드할 수 없습니다.")
            return None

        # ✅ 가중치 날짜 일관성 검증
        print("\n[검증] 가중치 날짜 확인:")
        if market_weights_df is not None:
            market_dates = market_weights_df['ForecastDate'].unique()
            print(f"  - Market Portfolio: {[d.date() for d in market_dates]}")
        if mvo_weights_df is not None:
            mvo_dates = mvo_weights_df['ForecastDate'].unique()
            print(f"  - MVO: {[d.date() for d in mvo_dates]}")
        if bl_weights_df is not None:
            bl_dates = bl_weights_df['ForecastDate'].unique()
            print(f"  - BL: {[d.date() for d in bl_dates]}")

        # 일별 수익률 데이터 로드
        print(f"\n[실행] 일별 수익률 데이터 로드 중...")
        daily_returns = load_daily_returns(
            invest_start.strftime('%Y-%m-%d'),
            invest_end.strftime('%Y-%m-%d')
        )

        if daily_returns is None or daily_returns.empty:
            print("[오류] 일별 수익률 데이터를 로드할 수 없습니다.")
            return None

        # 백테스트 수행 (forecast_date 기준)
        print(f"\n[실행] 백테스트 계산 중...")
        market_performance = None
        if market_weights_df is not None:
            market_performance = calculate_performance(
                market_weights_df, daily_returns, forecast_date, backtest_days=backtest_days
            )

        mvo_performance = calculate_performance(
            mvo_weights_df, daily_returns, forecast_date, backtest_days=backtest_days
        )
        bl_performance = calculate_performance(
            bl_weights_df, daily_returns, forecast_date, backtest_days=backtest_days
        )

        if mvo_performance is None or bl_performance is None:
            print("[오류] 백테스트 계산 실패")
            return None

        # 결과 출력
        print("\n" + "="*80)
        print("3단계: 결과 분석")
        print("="*80)

        # 비교 테이블 생성
        performance_dict = {}
        if market_performance is not None:
            performance_dict['Market'] = market_performance
        performance_dict['MVO'] = mvo_performance
        performance_dict['BL_AI'] = bl_performance

        comparison_df = pd.DataFrame(performance_dict)

        print(f"\n[결과] {backtest_days} 영업일 누적 수익률:")
        print(comparison_df.to_string())

        # 성과 지표 계산
        market_final = market_performance.iloc[-1] if market_performance is not None else None
        mvo_final = mvo_performance.iloc[-1]
        bl_final = bl_performance.iloc[-1]

        outperformance_vs_mvo = bl_final - mvo_final
        outperformance_vs_market = bl_final - market_final if market_final is not None else None

        print(f"\n[요약]")
        if market_final is not None:
            print(f"  Market Portfolio 최종 수익률: {market_final*100:.2f}%")
        print(f"  MVO 벤치마크 최종 수익률: {mvo_final*100:.2f}%")
        print(f"  BL-AI 포트폴리오 최종 수익률: {bl_final*100:.2f}%")
        print(f"\n[초과 수익률]")
        print(f"  vs MVO: {outperformance_vs_mvo*100:+.2f}%p")
        if outperformance_vs_market is not None:
            print(f"  vs Market: {outperformance_vs_market*100:+.2f}%p")

        if outperformance_vs_mvo > 0:
            print(f"\n  [성공] BL-AI 포트폴리오가 MVO를 {outperformance_vs_mvo*100:.2f}%p 초과달성했습니다!")
        else:
            print(f"\n  [주의] BL-AI 포트폴리오가 MVO 대비 {abs(outperformance_vs_mvo)*100:.2f}%p 저조했습니다.")

        # 결과 저장
        output_dir = Path(f'database/logs/Tier{tier}/result_of_test')
        output_dir.mkdir(parents=True, exist_ok=True)

        result_data = {
            "simulation_name": simul_name,
            "tier": tier,
            "forecast_date": forecast_date.strftime('%Y-%m-%d'),
            "tau": tau,
            "backtest_period": {
                "start": invest_start.strftime('%Y-%m-%d'),
                "end": invest_end.strftime('%Y-%m-%d'),
                "trading_days": backtest_days
            },
            "summary": {
                "market_final_return": float(market_final) if market_final is not None else None,
                "mvo_final_return": float(mvo_final),
                "bl_final_return": float(bl_final),
                "outperformance_vs_mvo": float(outperformance_vs_mvo),
                "outperformance_vs_market": float(outperformance_vs_market) if outperformance_vs_market is not None else None
            },
            "market_performance": {
                "daily_returns": market_performance.to_dict() if market_performance is not None else None
            },
            "mvo_performance": {
                "daily_returns": mvo_performance.to_dict()
            },
            "bl_performance": {
                "daily_returns": bl_performance.to_dict()
            }
        }

        output_file = output_dir / f'{simul_name}_single_backtest.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)

        print(f"\n[저장] 결과가 저장되었습니다: {output_file}")

        return result_data

    except Exception as e:
        print(f"\n[오류] 백테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """메인 함수"""
    try:
        # 사용자 입력 받기
        params = get_user_input()

        # 확인
        print("\n" + "="*80)
        print("입력 확인")
        print("="*80)
        print(f"시뮬레이션 이름: {params['simul_name']}")
        print(f"Tier: {params['tier']}")
        print(f"예측 날짜: {params['forecast_date'].date()}")
        print(f"tau: {params['tau']}")
        print(f"백테스트 기간: {params['backtest_days']}일")

        confirm = input("\n계속 진행하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            print("\n[취소] 실행이 취소되었습니다.")
            return

        # 실행
        result = run_single_backtest(
            simul_name=params['simul_name'],
            tier=params['tier'],
            forecast_date=params['forecast_date'],
            tau=params['tau'],
            backtest_days=params['backtest_days']
        )

        if result:
            print("\n" + "="*80)
            print("실행 완료!")
            print("="*80)
        else:
            print("\n[오류] 실행 중 문제가 발생했습니다.")

    except KeyboardInterrupt:
        print("\n\n[중단] 사용자가 실행을 중단했습니다.")
    except Exception as e:
        print(f"\n[오류] 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
