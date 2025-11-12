import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from pathlib import Path

# python -m aiportfolio.backtest.final_Ret

# 1. data_prepare 모듈에서 가중치 계산 함수들을 임포트
try:
    from aiportfolio.backtest.data_prepare import (
        calculate_monthly_mvo_weights,
        calculate_monthly_market_weights,  # 신규 추가
        open_log
    )
except ImportError:
    print("오류: data_prepare 모듈을 임포트할 수 없습니다. 경로를 확인하세요.")
    # 실제 실행 시엔 exit()을 사용하거나 경로 문제를 해결해야 합니다.
    # 데모용으로 임시 함수를 만듭니다. (실제 실행 시 이 부분은 없어야 함)
    def calculate_monthly_mvo_weights(hist_start_date, investment_start_date, investment_end_date):
        print("경고: MVO 가중치 계산 함수 임포트 실패. 데모 데이터를 반환합니다.")
        return pd.DataFrame()
    def calculate_monthly_market_weights(investment_start_date, investment_end_date):
        print("경고: Market Portfolio 가중치 계산 함수 임포트 실패. 데모 데이터를 반환합니다.")
        return pd.DataFrame()
    def open_log(simul_name='test1', Tier=1):
        print("경고: BL 가중치 계산 함수 임포트 실패. 데모 데이터를 반환합니다.")
        return pd.DataFrame()

# 2. preprocessing 모듈에서 일별 섹터 수익률 함수 임포트
try:
    from aiportfolio.backtest.preprocessing import sector_daily_returns
except ImportError:
    print("오류: preprocessing 모듈을 임포트할 수 없습니다.")
    def sector_daily_returns():
        return pd.DataFrame()

# GICS 코드와 섹터 이름 매핑
gics_mapping_code_to_name = {
    10: "Energy",
    15: "Materials",
    20: "Industrials",
    25: "Consumer Discretionary",
    30: "Consumer Staples",
    35: "Health Care",
    40: "Financials",
    45: "Information Technology",
    50: "Communication Services",
    55: "Utilities",
    60: "Real Estate"
}


# 3. 일별 수익률 데이터 준비 (실제 데이터 사용)
def load_daily_returns(start_date, end_date):
    """
    preprocessing.sector_daily_returns()를 호출하여 실제 일별 섹터 수익률을 로드하고,
    wide format으로 변환합니다.
    """
    print(f"\n{start_date} ~ {end_date} 기간의 일별 섹터 수익률 데이터를 로드합니다...")

    # Long format으로 데이터 로드
    df = sector_daily_returns()

    if df is None or df.empty:
        print("오류: 일별 수익률 데이터를 로드할 수 없습니다.")
        return None

    # 날짜를 datetime으로 변환
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # 날짜 필터링
    df = df[(df['DlyCalDt'] >= start_dt) & (df['DlyCalDt'] <= end_dt)].copy()

    # GICS 코드를 정수로 변환 (float -> int)
    df['gsector'] = df['gsector'].astype(int)

    # Wide format으로 피벗
    daily_returns_wide = df.pivot(
        index='DlyCalDt',
        columns='gsector',  # 숫자 코드를 컬럼으로 사용
        values='sector_return'
    )

    print(f"로드된 일별 수익률 데이터: {len(daily_returns_wide)}일, {len(daily_returns_wide.columns)}개 섹터")
    print("데이터 앞 5줄:")
    print(daily_returns_wide.head())

    return daily_returns_wide

# 3. 백테스트 성과 계산 함수 (수정됨)
def calculate_performance(monthly_weights_df, daily_returns_df, forecast_date, backtest_days=20):
    """
    주어진 월별 가중치와 일별 수익률로 지정된 거래일 동안의 누적 성과를 계산합니다.

    Args:
        monthly_weights_df: 월별 가중치 DataFrame (ForecastDate, SECTOR, Weight 컬럼)
        daily_returns_df: 일별 수익률 DataFrame (날짜 인덱스, 섹터 코드 컬럼)
        forecast_date: 예측 기준 날짜 (이 날짜의 가중치를 사용)
        backtest_days: 백테스트 기간 (거래일 수, 기본값 20일)
    """

    if monthly_weights_df is None or monthly_weights_df.empty:
        print("오류: 가중치 데이터가 비어있습니다.")
        return None

    # forecast_date를 datetime으로 변환
    if isinstance(forecast_date, str):
        forecast_date = pd.to_datetime(forecast_date)

    try:
        # 변경: InvestmentMonth → ForecastDate
        weights_wide = monthly_weights_df.pivot(
            index='ForecastDate',
            columns='SECTOR',
            values='Weight'
        ).fillna(0)
    except Exception as e:
        print(f"오류: 가중치 DF를 피벗하는 중 실패: {e}")
        print(f"데이터 컬럼: {monthly_weights_df.columns.tolist()}")
        return None

    # forecast_date와 가장 가까운 가중치 찾기
    available_dates = weights_wide.index
    if len(available_dates) == 0:
        print("오류: 가중치 데이터에 날짜가 없습니다.")
        return None

    print(f"[디버그] forecast_date: {forecast_date}")
    print(f"[디버그] 사용 가능한 가중치 날짜: {[d.date() for d in available_dates]}")

    # forecast_date와 정확히 일치하는 가중치 찾기 (월말 normalize 불필요)
    # BL 최적화는 forecast_date로 실행되므로, 가중치도 정확히 그 날짜로 저장됨
    if forecast_date in available_dates:
        weight_date = forecast_date
        print(f"[알림] {forecast_date.date()} 예측에 정확히 일치하는 가중치 사용")
    else:
        # 정확히 일치하지 않으면 가장 가까운 과거 날짜 찾기
        matching_dates = available_dates[available_dates <= forecast_date]
        if len(matching_dates) == 0:
            print(f"경고: {forecast_date.date()} 이전의 가중치 데이터가 없습니다.")
            print(f"가장 이른 가중치 날짜: {available_dates[0].date()}")
            return None

        weight_date = matching_dates[-1]  # 가장 최근 날짜
        print(f"[알림] {forecast_date.date()} 예측에 가장 가까운 {weight_date.date()} 가중치 사용")

    weights = weights_wide.loc[weight_date]

    # forecast_date 이후 첫 번째 거래일부터 시작
    try:
        future_dates = daily_returns_df.index[daily_returns_df.index > forecast_date]
        if len(future_dates) == 0:
            print(f"경고: {forecast_date.date()} 이후의 수익률 데이터가 없습니다.")
            return None

        first_bday = future_dates[0]
    except IndexError:
        print(f"경고: {forecast_date.date()} 이후의 수익률 데이터가 없습니다.")
        return None

    # 첫 거래일부터 backtest_days 거래일만큼 가져오기
    start_idx = daily_returns_df.index.get_loc(first_bday)
    daily_returns_period = daily_returns_df.iloc[start_idx : start_idx + backtest_days]

    actual_days = len(daily_returns_period)
    if actual_days < backtest_days:
        print(f"경고: {backtest_days}일치 거래일 데이터가 부족합니다 (실제: {actual_days}일).")

    if actual_days == 0:
        print("오류: 거래일 데이터가 없습니다.")
        return None

    print(f"[알림] 백테스트 기간: {daily_returns_period.index[0].date()} ~ {daily_returns_period.index[-1].date()} (실제 {actual_days} 거래일)")

    # 가중치와 수익률 컬럼 정렬 (GICS 코드로 매칭)
    aligned_returns, aligned_weights = daily_returns_period.align(weights, axis=1, fill_value=0)

    # 일별 포트폴리오 수익률 계산 (가중 평균)
    # portfolio_return = Σ(weight_i × return_i)
    port_daily_return = aligned_returns.dot(aligned_weights)

    # 누적 수익률 계산 (복리 효과 적용)
    # CAR_t = (1 + r1) × (1 + r2) × ... × (1 + rt) - 1
    port_cum_return = (1 + port_daily_return).cumprod() - 1

    port_cum_return.index = range(1, len(port_cum_return) + 1)
    port_cum_return.name = "CumulativeReturn"
    port_cum_return.index.name = "TradingDay"

    # backtest_days까지 마지막 값으로 채우기 (데이터 부족 시)
    return port_cum_return.reindex(
        range(1, backtest_days + 1),
        fill_value=port_cum_return.iloc[-1] if len(port_cum_return) > 0 else 0
    )


# 메인 실행 블록
if __name__ == "__main__":

    # --- 1. 설정 ---
    HIST_START = '2020-01-01'
    INVEST_START = '2024-05-01'
    INVEST_END = '2024-12-31'

    # 시뮬레이션 설정
    SIMUL_NAME = 'test_validation'  # 실제 시뮬레이션 이름으로 변경
    TIER = 1                        # 실제 Tier (1, 2, 3)로 변경

    investment_months_list = pd.date_range(start=INVEST_START, end=INVEST_END, freq='MS')

    # --- 2. 월별 가중치 준비 (data_prepare 함수 호출) ---
    market_weights_df = calculate_monthly_market_weights(
        investment_start_date=INVEST_START,
        investment_end_date=INVEST_END
    )
    mvo_weights_df = calculate_monthly_mvo_weights(
        hist_start_date=HIST_START,
        investment_start_date=INVEST_START,
        investment_end_date=INVEST_END
    )
    bl_weights_df = open_log(simul_name=SIMUL_NAME, Tier=TIER)

    # --- 3. 일별 수익률 데이터 준비 (실제 데이터) ---
    daily_returns = load_daily_returns(INVEST_START, INVEST_END)

    # --- 4. 백테스트 수행 ---
    print("\n" + "="*50)
    print("백테스트 성과 계산 시작...")
    print("="*50)

    market_performance = None
    mvo_performance = None
    bl_performance = None

    if market_weights_df is not None:
        print("\n--- Market Portfolio 백테스트 실행 ---")
        market_performance = calculate_performance(market_weights_df, daily_returns, investment_months_list)
    else:
        print("\n--- Market Portfolio 가중치가 없어 백테스트를 건너뜁니다 ---")

    if mvo_weights_df is not None:
        print("\n--- MVO 포트폴리오 백테스트 실행 ---")
        mvo_performance = calculate_performance(mvo_weights_df, daily_returns, investment_months_list)
    else:
        print("\n--- MVO 가중치가 없어 백테스트를 건너뜁니다 ---")

    if bl_weights_df is not None:
        print("\n--- BL(AI) 포트폴리오 백테스트 실행 ---")
        bl_performance = calculate_performance(bl_weights_df, daily_returns, investment_months_list)
    else:
        print("\n--- BL(AI) 가중치가 없어 백테스트를 건너뜁니다 ---")

    # --- 5. 최종 결과 비교 ---
    performance_dict = {}
    if market_performance is not None:
        performance_dict['Market_Performance'] = market_performance
    if mvo_performance is not None:
        performance_dict['MVO_Performance'] = mvo_performance
    if bl_performance is not None:
        performance_dict['BL_Performance'] = bl_performance

    if len(performance_dict) >= 2:
        comparison_df = pd.DataFrame(performance_dict)
        print("\n" + "="*50)
        print("--- 포트폴리오 성과 비교 테이블 (영업일 1~20일 누적 성과) ---")
        print("="*50)
        print(comparison_df.to_string())

        # --- 6. 결과 저장 ---
        output_dir = Path(f'database/logs/Tier{TIER}/result_of_test')
        output_dir.mkdir(parents=True, exist_ok=True)

        result_data = {
            "simulation_name": SIMUL_NAME,
            "tier": TIER,
            "backtest_period": {
                "start": INVEST_START,
                "end": INVEST_END
            },
            "mvo_performance": {
                "final_cumulative_return": float(mvo_performance.iloc[-1]),
                "daily_returns": mvo_performance.to_dict()
            },
            "bl_performance": {
                "final_cumulative_return": float(bl_performance.iloc[-1]),
                "daily_returns": bl_performance.to_dict()
            }
        }

        output_file = output_dir / f'{SIMUL_NAME}_backtest_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)

        print(f"\n백테스트 결과가 저장되었습니다: {output_file}")

    else:
        print("\n--- 두 포트폴리오의 성과를 비교할 수 없습니다 ---")