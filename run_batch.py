"""
다중 시점 Black-Litterman 포트폴리오 최적화 및 백테스트 배치 실행 스크립트

이 스크립트는 다음을 수행합니다:
1. 여러 날짜에 대해 LLM 뷰 생성
2. Black-Litterman 모델로 포트폴리오 최적화
3. 각 시점별 백테스트 수행
4. 모든 시점의 평균 성과 계산 및 출력

실행: python run_batch.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from tqdm import tqdm

# 프로젝트 모듈 임포트
from aiportfolio.scene import scene
from aiportfolio.backtest.data_prepare import calculate_monthly_mvo_weights, open_log
from aiportfolio.backtest.final_Ret import load_daily_returns, calculate_performance


def validate_date(date_str):
    """날짜 형식 검증 (YYYY-MM-DD)"""
    try:
        return pd.to_datetime(date_str)
    except:
        return None


def generate_monthly_dates(start_date, end_date):
    """시작일부터 종료일까지 월말 날짜 생성"""
    dates = pd.date_range(start=start_date, end=end_date, freq='M')
    return dates.tolist()


def get_batch_input():
    """배치 실행을 위한 사용자 입력 받기"""
    print("\n" + "="*80)
    print("Black-Litterman 배치 백테스트 시스템")
    print("="*80)

    # 시뮬레이션 이름
    simul_name = input("\n시뮬레이션 이름을 입력하세요 (예: batch_2024): ").strip()
    if not simul_name:
        simul_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[알림] 기본 이름으로 설정됨: {simul_name}")

    # Tier 선택
    while True:
        tier_input = input("\nTier를 선택하세요 (1: 기술적 지표만, 2: 기술적+회계, 3: 모든 지표): ").strip()
        if tier_input in ['1', '2', '3']:
            tier = int(tier_input)
            break
        else:
            print("[오류] 1, 2, 3 중 하나를 입력하세요.")

    # 시작 날짜 (백테스트하려는 달)
    while True:
        start_date = input("\n백테스트 시작 달을 입력하세요 (월말 날짜, 예: 2024-05-31 = 5월 백테스트): ").strip()
        validated_start = validate_date(start_date)
        if validated_start:
            start_date = validated_start + pd.offsets.MonthEnd(0)
            break
        else:
            print("[오류] 올바른 날짜 형식을 입력하세요 (YYYY-MM-DD).")

    # 종료 날짜 (백테스트하려는 마지막 달)
    while True:
        end_date = input("\n백테스트 종료 달을 입력하세요 (월말 날짜, 예: 2024-11-30 = 11월까지 백테스트): ").strip()
        validated_end = validate_date(end_date)
        if validated_end:
            end_date = validated_end + pd.offsets.MonthEnd(0)
            if end_date >= start_date:
                break
            else:
                print("[오류] 종료 날짜는 시작 날짜와 같거나 나중이어야 합니다.")
        else:
            print("[오류] 올바른 날짜 형식을 입력하세요 (YYYY-MM-DD).")

    # 월말 날짜 생성 (백테스트하려는 달들)
    forecast_dates_for_backtest = generate_monthly_dates(start_date, end_date)

    # 학습에 사용할 날짜
    # 주의: get_rolling_dates()가 내부적으로 1개월을 빼므로
    # 백테스트 날짜를 그대로 전달하면 최종적으로 1개월 전 데이터로 학습됨
    # 예: 6월 백테스트 입력 → 6월 30일 전달 → get_rolling_dates()에서 5월 31일로 변환
    forecast_dates_for_learning = forecast_dates_for_backtest

    print(f"\n[알림] 총 {len(forecast_dates_for_backtest)}개 시점에 대해 백테스트를 수행합니다.")
    print(f"[알림] 백테스트 기간: {[d.strftime('%Y년 %m월') for d in forecast_dates_for_backtest]}")
    print(f"[알림] scene()에 전달할 날짜: {[d.date() for d in forecast_dates_for_learning]}")
    print(f"[알림] 실제 학습 종료일: get_rolling_dates()가 각 날짜에서 1개월 뺀 값 사용")

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
        'forecast_dates_for_backtest': forecast_dates_for_backtest,
        'forecast_dates_for_learning': forecast_dates_for_learning,
        'tau': tau,
        'backtest_days': backtest_days
    }


def run_batch_backtest(simul_name, tier, forecast_dates_for_backtest, forecast_dates_for_learning, tau, backtest_days=20):
    """다중 시점에 대한 배치 백테스트 실행"""

    print("\n" + "="*80)
    print("1단계: 모든 시점에 대한 LLM 뷰 생성 및 BL 최적화")
    print("="*80)

    # 날짜 형식 변환 (학습용 날짜 사용)
    forecast_period_str = [d.strftime('%y-%m-%d') for d in forecast_dates_for_learning]

    try:
        # scene 함수 실행 (모든 날짜에 대해 한 번에)
        print(f"\n[실행] 시뮬레이션: {simul_name}, Tier: {tier}")
        print(f"[실행] 백테스트 기간: {forecast_dates_for_backtest[0].strftime('%Y년 %m월')} ~ {forecast_dates_for_backtest[-1].strftime('%Y년 %m월')}")
        print(f"[실행] 학습 기준일: {forecast_dates_for_learning[0].date()} ~ {forecast_dates_for_learning[-1].date()}")
        print(f"[실행] 총 {len(forecast_dates_for_backtest)}개 시점 처리 중...")

        results = scene(
            simul_name=simul_name,
            Tier=tier,
            tau=tau,
            forecast_period=forecast_period_str
        )

        if not results or len(results) == 0:
            print("\n[오류] BL 최적화 결과가 없습니다.")
            return None

        print(f"\n[성공] BL 최적화 완료 ({len(results)}개 시점)")

    except Exception as e:
        print(f"\n[오류] BL 최적화 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 각 시점별 백테스트 실행
    print("\n" + "="*80)
    print("2단계: 각 시점별 백테스트 수행")
    print("="*80)

    all_results = []
    mvo_returns_list = []
    bl_returns_list = []
    hist_start = forecast_dates_for_learning[0] - pd.DateOffset(years=10)  # 10년 전부터 학습 (BL과 동일)

    for i, backtest_date in enumerate(tqdm(forecast_dates_for_backtest, desc="백테스트 진행")):
        try:
            # 해당 백테스트 시점의 학습 기준일
            learning_date = forecast_dates_for_learning[i]

            # 거래일 기준 backtest_days를 확보하기 위해 충분한 캘린더 일수 계산
            calendar_days = int(backtest_days * 2.0) + 30

            # ✅ 투자 시작일: learning_date 다음 달 1일
            # 예: learning_date = 2024-04-30 → invest_start = 2024-05-01
            invest_start = (learning_date + pd.DateOffset(months=1)).replace(day=1)
            invest_end = invest_start + timedelta(days=calendar_days)

            # MVO 가중치 계산 (learning_date 시점에서)
            # ✅ 중요: MVO도 learning_date 시점의 가중치를 계산해야 BL과 비교 가능
            mvo_weights_df = calculate_monthly_mvo_weights(
                hist_start_date=hist_start.strftime('%Y-%m-%d'),
                investment_start_date=learning_date.strftime('%Y-%m-%d'),  # ✅ learning_date로 계산
                investment_end_date=learning_date.strftime('%Y-%m-%d')     # ✅ learning_date만 계산
            )

            # BL 가중치 로드 (learning_date 기준으로 생성된 가중치)
            bl_weights_df = open_log(simul_name=simul_name, Tier=tier)

            # 일별 수익률 데이터 로드
            daily_returns = load_daily_returns(
                invest_start.strftime('%Y-%m-%d'),
                invest_end.strftime('%Y-%m-%d')
            )

            if daily_returns is None or daily_returns.empty:
                print(f"\n[경고] {backtest_date.strftime('%Y년 %m월')}: 일별 수익률 데이터 없음")
                continue

            # 백테스트 수행 (learning_date 기준 가중치로 backtest_date 이후 성과 측정)
            mvo_performance = calculate_performance(
                mvo_weights_df, daily_returns, learning_date, backtest_days=backtest_days
            )
            bl_performance = calculate_performance(
                bl_weights_df, daily_returns, learning_date, backtest_days=backtest_days
            )

            if mvo_performance is None or bl_performance is None:
                print(f"\n[경고] {backtest_date.strftime('%Y년 %m월')}: 백테스트 계산 실패")
                continue

            # 최종 수익률 저장
            mvo_final = mvo_performance.iloc[-1]
            bl_final = bl_performance.iloc[-1]
            outperformance = bl_final - mvo_final

            mvo_returns_list.append(mvo_final)
            bl_returns_list.append(bl_final)

            result = {
                'backtest_month': backtest_date.strftime('%Y년 %m월'),
                'learning_date': learning_date.strftime('%Y-%m-%d'),
                'backtest_period': {
                    'start': invest_start.strftime('%Y-%m-%d'),
                    'end': invest_end.strftime('%Y-%m-%d')
                },
                'mvo_final_return': float(mvo_final),
                'bl_final_return': float(bl_final),
                'outperformance': float(outperformance)
            }

            all_results.append(result)

        except Exception as e:
            print(f"\n[경고] {backtest_date.strftime('%Y년 %m월')}: 오류 발생 - {e}")
            continue

    if len(all_results) == 0:
        print("\n[오류] 성공한 백테스트가 없습니다.")
        return None

    # 평균 성과 계산
    print("\n" + "="*80)
    print("3단계: 평균 성과 분석")
    print("="*80)

    mvo_mean = np.mean(mvo_returns_list)
    mvo_std = np.std(mvo_returns_list)
    bl_mean = np.mean(bl_returns_list)
    bl_std = np.std(bl_returns_list)
    outperformance_mean = bl_mean - mvo_mean

    # Win rate 계산
    win_count = sum(1 for r in all_results if r['outperformance'] > 0)
    win_rate = win_count / len(all_results) * 100

    print(f"\n[결과] 총 {len(all_results)}개 시점 백테스트 완료")
    print(f"\n{'='*60}")
    print(f"{'지표':<30} {'MVO 벤치마크':<15} {'BL-AI 포트폴리오':<15}")
    print(f"{'='*60}")
    print(f"{'평균 20일 누적 수익률':<30} {mvo_mean*100:>14.2f}% {bl_mean*100:>14.2f}%")
    print(f"{'표준편차':<30} {mvo_std*100:>14.2f}% {bl_std*100:>14.2f}%")
    print(f"{'='*60}")
    print(f"{'평균 초과 수익률':<30} {outperformance_mean*100:>14.2f}%")
    print(f"{'승률 (BL-AI > MVO)':<30} {win_rate:>14.1f}%")
    print(f"{'='*60}")

    if outperformance_mean > 0:
        print(f"\n[성공] BL-AI 포트폴리오가 평균적으로 벤치마크를 {outperformance_mean*100:.2f}%p 초과달성했습니다!")
    else:
        print(f"\n[주의] BL-AI 포트폴리오가 평균적으로 벤치마크 대비 {abs(outperformance_mean)*100:.2f}%p 저조했습니다.")

    # 시점별 상세 결과 출력
    print(f"\n{'='*80}")
    print(f"시점별 상세 결과")
    print(f"{'='*80}")
    print(f"{'백테스트 월':<15} {'학습 날짜':<15} {'MVO 수익률':<12} {'BL 수익률':<12} {'초과 수익률':<12}")
    print(f"{'-'*80}")
    for r in all_results:
        print(f"{r['backtest_month']:<15} {r['learning_date']:<15} {r['mvo_final_return']*100:>11.2f}% "
              f"{r['bl_final_return']*100:>11.2f}% {r['outperformance']*100:>11.2f}%")

    # 결과 저장
    output_dir = Path(f'database/logs/Tier{tier}/result_of_test')
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_data = {
        "simulation_name": simul_name,
        "tier": tier,
        "tau": tau,
        "num_periods": len(all_results),
        "backtest_period_range": {
            "start": forecast_dates_for_backtest[0].strftime('%Y년 %m월'),
            "end": forecast_dates_for_backtest[-1].strftime('%Y년 %m월')
        },
        "learning_period_range": {
            "start": forecast_dates_for_learning[0].strftime('%Y-%m-%d'),
            "end": forecast_dates_for_learning[-1].strftime('%Y-%m-%d')
        },
        "average_performance": {
            "mvo_mean_return": float(mvo_mean),
            "mvo_std_return": float(mvo_std),
            "bl_mean_return": float(bl_mean),
            "bl_std_return": float(bl_std),
            "mean_outperformance": float(outperformance_mean),
            "win_rate": float(win_rate)
        },
        "detailed_results": all_results
    }

    output_file = output_dir / f'{simul_name}_batch_backtest.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)

    print(f"\n[저장] 결과가 저장되었습니다: {output_file}")

    return summary_data


def main():
    """메인 함수"""
    try:
        # 사용자 입력 받기
        params = get_batch_input()

        # 확인
        print("\n" + "="*80)
        print("입력 확인")
        print("="*80)
        print(f"시뮬레이션 이름: {params['simul_name']}")
        print(f"Tier: {params['tier']}")
        print(f"백테스트 기간: {params['forecast_dates_for_backtest'][0].strftime('%Y년 %m월')} ~ {params['forecast_dates_for_backtest'][-1].strftime('%Y년 %m월')}")
        print(f"학습 기준일: {params['forecast_dates_for_learning'][0].date()} ~ {params['forecast_dates_for_learning'][-1].date()}")
        print(f"시점 개수: {len(params['forecast_dates_for_backtest'])}개")
        print(f"tau: {params['tau']}")
        print(f"백테스트 기간: {params['backtest_days']}일")

        # 예상 소요 시간 안내
        estimated_time = len(params['forecast_dates_for_backtest']) * 2  # 시점당 약 2분 가정
        print(f"\n[알림] 예상 소요 시간: 약 {estimated_time}분")
        print(f"[알림] GPU가 필요합니다. CUDA가 사용 가능한지 확인하세요.")

        confirm = input("\n계속 진행하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            print("\n[취소] 실행이 취소되었습니다.")
            return

        # 실행
        result = run_batch_backtest(
            simul_name=params['simul_name'],
            tier=params['tier'],
            forecast_dates_for_backtest=params['forecast_dates_for_backtest'],
            forecast_dates_for_learning=params['forecast_dates_for_learning'],
            tau=params['tau'],
            backtest_days=params['backtest_days']
        )

        if result:
            print("\n" + "="*80)
            print("배치 실행 완료!")
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
