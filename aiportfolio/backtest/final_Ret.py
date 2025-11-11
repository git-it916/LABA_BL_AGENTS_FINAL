import pandas as pd
import numpy as np
from datetime import datetime

# python -m aiportfolio.backtest.RET

# 1. data_prepare 모듈에서 가중치 계산 함수들을 임포트
try:
    from potato_trial.data_prepare_수정중 import calculate_monthly_mvo_weights, open_log
except ImportError:
    print("오류: data_prepare 모듈을 임포트할 수 없습니다. 경로를 확인하세요.")
    # 실제 실행 시엔 exit()을 사용하거나 경로 문제를 해결해야 합니다.
    # 데모용으로 임시 함수를 만듭니다. (실제 실행 시 이 부분은 없어야 함)
    def calculate_monthly_mvo_weights(hist_start_date, investment_start_date, investment_end_date):
        print("경고: MVO 가중치 계산 함수 임포트 실패. 데모 데이터를 반환합니다.")
        return pd.DataFrame() 
    def open_log():
        print("경고: BL 가중치 계산 함수 임포트 실패. 데모 데이터를 반환합니다.")
        return pd.DataFrame()


# 2. 일별 수익률 데이터 준비 (데모 함수)
def load_demo_daily_returns(start_date, end_date):
    """
    임의의 일별 수익률 DataFrame을 생성합니다. (wide format)
    (실제 코드에서는 이 함수 대신 final()을 호출하고 피벗(pivot)해야 합니다.)
    """
    print(f"\n데모용: {start_date} ~ {end_date} 기간의 임의의 일별 수익률 데이터를 생성합니다.")
    sectors = [
        "Communication Services", "Consumer Discretionary", "Consumer Staples", 
        "Energy", "Financials", "Health Care", "Industrials", 
        "Information Technology", "Materials", "Real Estate", "Utilities"
    ]
    # 12월 20영업일까지 포함하기 위해 1달 여유
    dates = pd.bdate_range(start=start_date, end=pd.to_datetime(end_date) + pd.DateOffset(months=1))
    
    n_days = len(dates)
    n_sectors = len(sectors)
    returns_data = np.random.normal(0.0001, 0.005, size=(n_days, n_sectors))
    
    daily_returns_df = pd.DataFrame(returns_data, index=dates, columns=sectors)
    daily_returns_df.index.name = 'date'
    
    print("생성된 임의의 일별 수익률 데이터 (wide format, 앞 5줄):")
    print(daily_returns_df.head())
    return daily_returns_df

# 3. 백테스트 성과 계산 함수 (수정됨)
def calculate_performance(monthly_weights_df, daily_returns_df, investment_months):
    """
    주어진 월별 가중치와 일별 수익률로 20일간의 누적 성과를 계산합니다.
    """
    
    try:
        weights_wide = monthly_weights_df.pivot(
            index='InvestmentMonth', 
            columns='SECTOR', 
            values='Weight'
        ).fillna(0)
    except Exception as e:
        print(f"오류: 가중치 DF를 피벗하는 중 실패: {e}")
        return None

    all_monthly_cum_returns = []

    for investment_month in investment_months:
        if investment_month not in weights_wide.index:
            print(f"경고: {investment_month.date()}의 가중치 데이터가 없습니다. 건너뜁니다.")
            continue

        weights = weights_wide.loc[investment_month]
        
        try:
            first_bday = daily_returns_df.index[
                daily_returns_df.index >= investment_month
            ][0]
        except IndexError:
            print(f"경고: {investment_month.date()} 이후의 수익률 데이터가 없습니다. 건너뜁니다.")
            continue
            
        start_idx = daily_returns_df.index.get_loc(first_bday)
        daily_returns_20d = daily_returns_df.iloc[start_idx : start_idx + 20]
        
        if len(daily_returns_20d) < 20:
            print(f"경고: {investment_month.date()}의 20일치 영업일 데이터가 부족합니다 (보유: {len(daily_returns_20d)}일).")
        
        # --- [수정된 라인] ---
        # DataFrame.align(Series, axis=1)을 호출하도록 변경
        aligned_returns, aligned_weights = daily_returns_20d.align(weights, axis=1, fill_value=0)
        # --------------------

        port_daily_return = aligned_returns.dot(aligned_weights)
        
        port_cum_return = port_daily_return.cumsum()
        port_cum_return.index = range(1, len(port_cum_return) + 1)
        all_monthly_cum_returns.append(port_cum_return)

    if not all_monthly_cum_returns:
        print("오류: 계산된 월별 수익률이 없습니다.")
        return None
        
    combined_cum_returns = pd.concat(all_monthly_cum_returns, axis=1, sort=True)
    
    total_aggregated_returns = combined_cum_returns.sum(axis=1)
    
    total_aggregated_returns.name = "AggregatedCumulativeReturn"
    total_aggregated_returns.index.name = "BusinessDay"
    return total_aggregated_returns.reindex(range(1, 21), fill_value=0)


# 3. 메인 실행 블록
if __name__ == "__main__":
    
    # --- 1. 설정 ---
    HIST_START = '2020-01-01' 
    INVEST_START = '2024-05-01'
    INVEST_END = '2024-12-31'
    
    investment_months_list = pd.date_range(start=INVEST_START, end=INVEST_END, freq='MS')

    # --- 2. 월별 가중치 준비 (data_prepare 함수 호출) ---
    mvo_weights_df = calculate_monthly_mvo_weights(
        hist_start_date=HIST_START, 
        investment_start_date=INVEST_START,
        investment_end_date=INVEST_END
    )
    bl_weights_df = open_log()

    # --- 3. 일별 수익률 데이터 준비 (데모) ---
    daily_returns = load_demo_daily_returns(INVEST_START, INVEST_END)

    # --- 4. 백테스트 수행 ---
    print("\n" + "="*50)
    print("백테스트 성과 계산 시작...")
    print("="*50)
    
    mvo_performance = None
    bl_performance = None

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
    if mvo_performance is not None and bl_performance is not None:
        comparison_df = pd.DataFrame({
            'MVO_Performance': mvo_performance,
            'BL_Performance': bl_performance
        })
        print("\n" + "="*50)
        print("--- MVO vs BL 최종 비교 테이블 (영업일 1~20일 누적 성과) ---")
        print("="*50)
        print(comparison_df.to_string())
    else:
        print("\n--- 두 포트폴리오의 성과를 비교할 수 없습니다 ---")