"""
다중 Tier 자동 반복 실행 스크립트

Tier 1, 2, 3을 각각 지정된 횟수만큼 자동으로 반복 실행합니다.
각 Tier별로 0번 이상 실행 가능하며, 모든 결과는 자동으로 저장됩니다.
"""

import pandas as pd
from datetime import datetime, timedelta
from aiportfolio.scene import scene
from aiportfolio.backtest.data_prepare import calculate_monthly_mvo_weights, open_BL_MVO_log
from aiportfolio.backtest.final_Ret import load_daily_returns, calculate_performance
import numpy as np
import json
from pathlib import Path
from tqdm import tqdm


def get_user_input():
    """사용자로부터 실행 횟수와 공통 설정을 입력받습니다."""
    print("\n" + "="*70)
    print("📊 다중 Tier 자동 반복 실행 설정")
    print("="*70)

    # Tier별 실행 횟수 입력
    print("\n각 Tier를 몇 번씩 실행할지 입력하세요 (0 입력 시 해당 Tier 건너뜀):")

    while True:
        try:
            n_tier1 = int(input("  Tier 1 실행 횟수 (n): ").strip())
            if n_tier1 < 0:
                print("    오류: 0 이상의 정수를 입력하세요.")
                continue
            break
        except ValueError:
            print("    오류: 정수를 입력하세요.")

    while True:
        try:
            k_tier2 = int(input("  Tier 2 실행 횟수 (k): ").strip())
            if k_tier2 < 0:
                print("    오류: 0 이상의 정수를 입력하세요.")
                continue
            break
        except ValueError:
            print("    오류: 정수를 입력하세요.")

    while True:
        try:
            p_tier3 = int(input("  Tier 3 실행 횟수 (p): ").strip())
            if p_tier3 < 0:
                print("    오류: 0 이상의 정수를 입력하세요.")
                continue
            break
        except ValueError:
            print("    오류: 정수를 입력하세요.")

    # 총 실행 횟수 확인
    total_runs = n_tier1 + k_tier2 + p_tier3
    if total_runs == 0:
        print("\n⚠ 경고: 모든 Tier의 실행 횟수가 0입니다. 프로그램을 종료합니다.")
        import sys
        sys.exit(0)

    print(f"\n총 실행 횟수: {total_runs}회")
    print(f"  - Tier 1: {n_tier1}회")
    print(f"  - Tier 2: {k_tier2}회")
    print(f"  - Tier 3: {p_tier3}회")

    # 공통 설정 입력
    print("\n" + "="*70)
    print("공통 설정")
    print("="*70)

    base_simul_name = input("\n시뮬레이션 기본 이름 (예: auto_test): ").strip()
    if not base_simul_name:
        base_simul_name = "auto_test"
        print(f"  → 기본값 사용: {base_simul_name}")

    while True:
        tau_input = input("tau 값 (예: 0.025, 기본값 0.025): ").strip()
        if not tau_input:
            tau = 0.025
            break
        try:
            tau = float(tau_input)
            if tau <= 0:
                print("    오류: tau는 양수여야 합니다.")
                continue
            break
        except ValueError:
            print("    오류: 숫자를 입력하세요.")

    print(f"  → tau = {tau}")

    # 예측 기간 입력
    print("\n예측 기간 설정:")
    print("  형식: YY-MM-DD (예: 24-05-31)")
    print("  여러 기간은 쉼표로 구분 (예: 24-05-31, 24-06-30, 24-07-31)")

    while True:
        forecast_input = input("\n예측 기간: ").strip()
        if not forecast_input:
            # 기본값: 2024년 5월~12월
            forecast_period = [
                "24-05-31", "24-06-30", "24-07-31", "24-08-31",
                "24-09-30", "24-10-31", "24-11-30", "24-12-31"
            ]
            print(f"  → 기본값 사용: {', '.join(forecast_period)}")
            break

        # 쉼표로 분리
        forecast_period = [p.strip() for p in forecast_input.split(',')]

        # 날짜 형식 검증
        valid = True
        for period in forecast_period:
            try:
                pd.to_datetime(period, format='%y-%m-%d')
            except:
                print(f"    오류: '{period}'는 올바른 형식이 아닙니다. (YY-MM-DD 형식)")
                valid = False
                break

        if valid:
            break

    print(f"  → 예측 기간: {len(forecast_period)}개")

    # 백테스트 설정
    print("\n백테스트 설정:")
    while True:
        backtest_input = input("  백테스트 거래일 수 (5-250, 기본 20): ").strip()
        if not backtest_input:
            backtest_days = 20
            break
        try:
            backtest_days = int(backtest_input)
            if 5 <= backtest_days <= 250:
                break
            print("    오류: 5에서 250 사이의 값을 입력하세요.")
        except ValueError:
            print("    오류: 정수를 입력하세요.")

    print(f"  → 백테스트 거래일: {backtest_days}일")

    return {
        'n_tier1': n_tier1,
        'k_tier2': k_tier2,
        'p_tier3': p_tier3,
        'base_simul_name': base_simul_name,
        'tau': tau,
        'forecast_period': forecast_period,
        'backtest_days': backtest_days
    }


def run_single_tier_iteration(tier, simul_name, tau, forecast_period, backtest_days):
    """단일 Tier를 한 번 실행하고 백테스트까지 수행합니다."""

    print("\n" + "="*70)
    print(f"🚀 {simul_name} 실행 시작 (Tier {tier})")
    print("="*70)

    # 예측 기간을 날짜 객체로 변환
    forecast_dates = [pd.to_datetime(p, format='%y-%m-%d') for p in forecast_period]

    # Scene 실행 (LLM 뷰 생성 + BL-MVO 최적화)
    print(f"\n[1/3] LLM 뷰 생성 및 BL-MVO 최적화 실행 중...")
    try:
        results = scene(simul_name, tier, tau, forecast_period)
        print(f"✓ {len(results)}개 예측 기간 완료")
    except Exception as e:
        print(f"✗ Scene 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 백테스트 데이터 준비
    print(f"\n[2/3] 백테스트 데이터 준비 중...")
    try:
        # BL 가중치 로드
        bl_weights_df = open_BL_MVO_log(simul_name=simul_name, Tier=tier)
        print(f"✓ BL 가중치 로드 완료: {len(bl_weights_df)}개 레코드")

    except Exception as e:
        print(f"✗ BL 가중치 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 백테스트 실행
    print(f"\n[3/3] 백테스트 실행 중...")
    all_results = []
    hist_start = forecast_dates[0] - pd.DateOffset(years=10)  # 10년 전부터 학습

    for idx, forecast_date in enumerate(forecast_dates, 1):
        print(f"\n  [{idx}/{len(forecast_dates)}] {forecast_date.date()} 백테스트 중...")

        try:
            # get_rolling_dates()를 통해 계산된 learning_date (1개월 전)
            learning_date = (forecast_date - pd.DateOffset(months=1)).to_period('M').to_timestamp('M')

            # 거래일 기준 backtest_days를 확보하기 위해 충분한 캘린더 일수 계산
            calendar_days = int(backtest_days * 2.0) + 30

            # 투자 시작일: learning_date 다음 달 1일
            invest_start = (learning_date + pd.DateOffset(months=1)).replace(day=1)
            invest_end = invest_start + timedelta(days=calendar_days)

            # MVO 가중치 계산 (learning_date 시점에서)
            mvo_weights_df = calculate_monthly_mvo_weights(
                hist_start_date=hist_start.strftime('%Y-%m-%d'),
                investment_start_date=learning_date.strftime('%Y-%m-%d'),
                investment_end_date=learning_date.strftime('%Y-%m-%d')
            )

            # 일별 수익률 데이터 로드
            daily_returns = load_daily_returns(
                invest_start.strftime('%Y-%m-%d'),
                invest_end.strftime('%Y-%m-%d')
            )

            if daily_returns is None or daily_returns.empty:
                print(f"    ✗ 일별 수익률 데이터 없음")
                raise ValueError("일별 수익률 데이터를 로드할 수 없습니다")

            # 백테스트 수행
            mvo_perf = calculate_performance(
                mvo_weights_df, daily_returns, learning_date, backtest_days
            )
            bl_perf = calculate_performance(
                bl_weights_df, daily_returns, learning_date, backtest_days
            )

            if mvo_perf is None or bl_perf is None:
                print(f"    ✗ 백테스트 계산 실패")
                raise ValueError("백테스트 성과 계산 실패")

            # 최종 수익률 추출
            mvo_final_return = mvo_perf.iloc[-1] if len(mvo_perf) > 0 else 0.0
            bl_final_return = bl_perf.iloc[-1] if len(bl_perf) > 0 else 0.0
            outperformance = bl_final_return - mvo_final_return

            all_results.append({
                'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                'learning_date': learning_date.strftime('%Y-%m-%d'),
                'invest_start': invest_start.strftime('%Y-%m-%d'),
                'mvo_final_return': float(mvo_final_return),
                'bl_final_return': float(bl_final_return),
                'outperformance': float(outperformance)
            })

            print(f"    학습: {learning_date.date()} | 투자: {invest_start.date()}")
            print(f"    MVO: {mvo_final_return*100:+.2f}% | BL: {bl_final_return*100:+.2f}% | 초과: {outperformance*100:+.2f}%")

        except Exception as e:
            print(f"    ✗ 백테스트 실패: {e}")
            all_results.append({
                'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                'mvo_final_return': None,
                'bl_final_return': None,
                'outperformance': None,
                'error': str(e)
            })

    # 백테스트 결과 저장
    output_dir = Path(f"database/logs/Tier{tier}/result_of_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{simul_name}_batch_backtest.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 백테스트 결과 저장: {output_path}")

    # 성공한 결과만 필터링하여 평균 계산
    valid_results = [r for r in all_results if r['mvo_final_return'] is not None]

    if len(valid_results) > 0:
        avg_mvo = np.mean([r['mvo_final_return'] for r in valid_results])
        avg_bl = np.mean([r['bl_final_return'] for r in valid_results])
        avg_outperf = np.mean([r['outperformance'] for r in valid_results])
        win_rate = sum(1 for r in valid_results if r['outperformance'] > 0) / len(valid_results) * 100

        print(f"\n📊 백테스트 요약 ({len(valid_results)}개 성공):")
        print(f"  평균 MVO 성과: {avg_mvo*100:+.2f}%")
        print(f"  평균 BL(AI) 성과: {avg_bl*100:+.2f}%")
        print(f"  평균 초과 성과: {avg_outperf*100:+.2f}%")
        print(f"  승률: {win_rate:.1f}%")

        return {
            'simul_name': simul_name,
            'tier': tier,
            'avg_mvo': avg_mvo,
            'avg_bl': avg_bl,
            'avg_outperformance': avg_outperf,
            'win_rate': win_rate,
            'total_periods': len(all_results),
            'successful_periods': len(valid_results)
        }
    else:
        print(f"\n⚠ 모든 백테스트가 실패했습니다.")
        return None


def main():
    """메인 실행 함수"""

    # 시작 시간 기록
    start_time = datetime.now()

    # 사용자 입력 받기
    config = get_user_input()

    n_tier1 = config['n_tier1']
    k_tier2 = config['k_tier2']
    p_tier3 = config['p_tier3']
    base_simul_name = config['base_simul_name']
    tau = config['tau']
    forecast_period = config['forecast_period']
    backtest_days = config['backtest_days']

    # 전체 실행 계획 표시
    print("\n" + "="*70)
    print("📋 실행 계획")
    print("="*70)

    total_runs = n_tier1 + k_tier2 + p_tier3
    run_sequence = []

    for i in range(1, n_tier1 + 1):
        tier = 1
        simul_name = f"{base_simul_name}_tier{tier}_{i:03d}"
        run_sequence.append((tier, simul_name))
        print(f"  {len(run_sequence):3d}. Tier {tier}: {simul_name}")

    for i in range(1, k_tier2 + 1):
        tier = 2
        simul_name = f"{base_simul_name}_tier{tier}_{i:03d}"
        run_sequence.append((tier, simul_name))
        print(f"  {len(run_sequence):3d}. Tier {tier}: {simul_name}")

    for i in range(1, p_tier3 + 1):
        tier = 3
        simul_name = f"{base_simul_name}_tier{tier}_{i:03d}"
        run_sequence.append((tier, simul_name))
        print(f"  {len(run_sequence):3d}. Tier {tier}: {simul_name}")

    # 사용자 확인
    print("\n" + "="*70)
    confirm = input(f"총 {total_runs}회 실행을 시작하시겠습니까? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("실행을 취소했습니다.")
        return

    # 실행 시작
    print("\n" + "="*70)
    print("🚀 실행 시작")
    print("="*70)
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    all_summaries = []
    failed_runs = []

    for idx, (tier, simul_name) in enumerate(run_sequence, 1):
        print("\n" + "█"*70)
        print(f"진행: {idx}/{total_runs} ({idx/total_runs*100:.1f}%)")
        print("█"*70)

        try:
            summary = run_single_tier_iteration(
                tier=tier,
                simul_name=simul_name,
                tau=tau,
                forecast_period=forecast_period,
                backtest_days=backtest_days
            )

            if summary is not None:
                all_summaries.append(summary)
            else:
                failed_runs.append((tier, simul_name))

        except KeyboardInterrupt:
            print("\n\n⚠ 사용자가 실행을 중단했습니다.")
            print(f"완료된 실행: {len(all_summaries)}/{total_runs}")
            break
        except Exception as e:
            print(f"\n✗ 예상치 못한 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            failed_runs.append((tier, simul_name))

    # 종료 시간 기록
    end_time = datetime.now()
    duration = end_time - start_time

    # 최종 요약
    print("\n\n" + "="*70)
    print("📊 전체 실행 요약")
    print("="*70)
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"총 소요 시간: {duration}")
    print(f"\n전체 실행 횟수: {total_runs}회")
    print(f"  성공: {len(all_summaries)}회")
    print(f"  실패: {len(failed_runs)}회")

    if failed_runs:
        print(f"\n⚠ 실패한 실행:")
        for tier, simul_name in failed_runs:
            print(f"  - Tier {tier}: {simul_name}")

    # Tier별 평균 성과
    if all_summaries:
        print("\n" + "="*70)
        print("Tier별 평균 성과")
        print("="*70)

        for tier_num in [1, 2, 3]:
            tier_results = [s for s in all_summaries if s['tier'] == tier_num]

            if tier_results:
                avg_mvo = np.mean([r['avg_mvo'] for r in tier_results])
                avg_bl = np.mean([r['avg_bl'] for r in tier_results])
                avg_outperf = np.mean([r['avg_outperformance'] for r in tier_results])
                avg_win_rate = np.mean([r['win_rate'] for r in tier_results])

                print(f"\nTier {tier_num} ({len(tier_results)}회 평균):")
                print(f"  평균 MVO 성과: {avg_mvo*100:+.2f}%")
                print(f"  평균 BL(AI) 성과: {avg_bl*100:+.2f}%")
                print(f"  평균 초과 성과: {avg_outperf*100:+.2f}%")
                print(f"  평균 승률: {avg_win_rate:.1f}%")

    # 최종 요약을 JSON으로 저장
    summary_dir = Path("database/logs/summary")
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / f"{base_simul_name}_multi_tier_summary_{start_time.strftime('%Y%m%d_%H%M%S')}.json"

    summary_data = {
        'config': config,
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': duration.total_seconds(),
        'total_runs': total_runs,
        'successful_runs': len(all_summaries),
        'failed_runs': len(failed_runs),
        'failed_list': [{'tier': t, 'simul_name': s} for t, s in failed_runs],
        'results': all_summaries
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 전체 요약 저장: {summary_path}")
    print("\n✅ 모든 작업 완료!")


if __name__ == "__main__":
    main()
