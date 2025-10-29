import pandas as pd
import numpy as np
from datetime import datetime

from aiportfolio.backtest.data_prepare import calculate_monthly_mvo_weights, open_log

# 1. [수정] data_prepare 및 preprocessing 모듈에서 실제 함수 임포트
try:
# data_prepare.py에서 가중치 계산 함수 임포트

except ImportError:
    print("오류: data_prepare 모듈(calculate_monthly_mvo_weights, open_log)을 임포트할 수 없습니다.")
    print("aiportfolio/backtest/data_prepare.py 파일이 올바른 위치에 있는지 확인하세요.")
    exit()

# [수정] preprocessing 모듈에서 수익률 로딩 함수 임포트
try:
    # data_load.py 대신 preprocessing.py에서 sector_daily_returns 임포트
    from aiportfolio.backtest.preprocessing import sector_daily_returns
except ImportError:
    print("오류: preprocessing 모듈(sector_daily_returns)을 임포트할 수 없습니다.")
    print("aiportfolio/backtest/preprocessing.py 파일이 올바른 위치에 있는지 확인하세요.")
    exit()


# 2. [삭제] load_demo_daily_returns 함수 정의
# (데모 함수는 삭제하고 main 블록에서 직접 sector_daily_returns()를 호출)


# 3. 백테스트 성과 계산 함수 (수정 없음)
def calculate_performance(monthly_weights_df, daily_returns_df, investment_months):
    """
    주어진 월별 가중치와 일별 수익률로 20일간의 누적 성과를 계산합니다.
    (monthly_weights_df는 long-format, daily_returns_df는 wide-format)
    """
    
    try:
        # 가중치 DF (long) -> wide-format으로 피벗
        weights_wide = monthly_weights_df.pivot(
            index='InvestmentMonth', 
            columns='SECTOR', 
            values='Weight'
        ).fillna(0)
    except Exception as e:
        print(f"오류: 가중치 DF를 피벗하는 중 실패: {e}")
        print("로드된 가중치 DF의 컬럼:", monthly_weights_df.columns)
        return None

    all_monthly_cum_returns = []

    for investment_month in investment_months:
        if investment_month not in weights_wide.index:
            print(f"경고: {investment_month.date()}의 가중치 데이터가 없습니다. 건너뜁니다.")
            continue

        weights = weights_wide.loc[investment_month] # 해당 월의 가중치 (Series)
        
        try:
            # 일별 수익률(daily_returns_df)에서 투자 시작일(investment_month) 이후 첫 영업일 찾기
            first_bday = daily_returns_df.index[
                daily_returns_df.index >= investment_month
            ][0]
        except IndexError:
            print(f"경고: {investment_month.date()} 이후의 수익률 데이터가 없습니다. 건너뜁니다.")
            continue
            
        # 첫 영업일로부터 20일치 데이터 슬라이싱
        start_idx = daily_returns_df.index.get_loc(first_bday)
        daily_returns_20d = daily_returns_df.iloc[start_idx : start_idx + 20]
        
        if len(daily_returns_20d) < 20:
            print(f"경고: {investment_month.date()}의 20일치 영업일 데이터가 부족합니다 (보유: {len(daily_returns_20d)}일).")
        
        # 수익률(DataFrame)과 가중치(Series)의 컬럼(섹터)을 정렬
        aligned_returns, aligned_weights = daily_returns_20d.align(weights, axis=1, fill_value=0)

        # (20, N) . (N,) -> (20,) : 20일간의 일별 포트폴리오 수익률
        port_daily_return = aligned_returns.dot(aligned_weights)
        
        port_cum_return = port_daily_return.cumsum() # 누적 수익률 계산
        port_cum_return.index = range(1, len(port_cum_return) + 1) # 인덱스를 1~20일로 변경
        all_monthly_cum_returns.append(port_cum_return)

    if not all_monthly_cum_returns:
        print("오류: 계산된 월별 수익률이 없습니다.")
        return None
        
    # 월별 20일치 누적수익률 Series들을 하나의 DataFrame으로 합침
    combined_cum_returns = pd.concat(all_monthly_cum_returns, axis=1, sort=True)
    
    # 모든 월의 누적수익률을 일(Day)별로 합산 (1일차 합, 2일차 합, ...)
    total_aggregated_returns = combined_cum_returns.sum(axis=1)
    
    total_aggregated_returns.name = "AggregatedCumulativeReturn"
    total_aggregated_returns.index.name = "BusinessDay"
    return total_aggregated_returns.reindex(range(1, 21), fill_value=0)


# 4. 메인 실행 블록
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

    # --- 3. [수정] 일별 수익률 데이터 준비 (preprocessing.py 호출 및 피벗) ---
    print(f"\n실제 데이터: {HIST_START} ~ {INVEST_END} 기간의 일별 수익률 데이터를 로드합니다.")
    
    try:
        # [수정] preprocessing.sector_daily_returns() 호출
        # (이 함수는 preprocessing.py에 따라 별도 인자가 필요 없어 보입니다)
        long_returns_df = sector_daily_returns()
        
        if long_returns_df is None or long_returns_df.empty:
            raise ValueError("preprocessing.sector_daily_returns()가 비어있는 DataFrame을 반환했습니다.")

        # [수정] preprocessing.py의 반환값에 맞게 컬럼명 검증
        if not all(col in long_returns_df.columns for col in ['DlyCalDt', 'gsector', 'sector_return']):
             raise ValueError("로드된 데이터에 'DlyCalDt', 'gsector', 'sector_return' 컬럼이 없습니다.")

        # [수정] 날짜 컬럼명 변경
        long_returns_df['DlyCalDt'] = pd.to_datetime(long_returns_df['DlyCalDt'])

        # wide format으로 피벗 (백테스트 함수가 요구하는 형식)
        daily_returns = long_returns_df.pivot(
            index='DlyCalDt',         # 'date' -> 'DlyCalDt'
            columns='gsector',        # 'SECTOR' -> 'gsector'
            values='sector_return'  # 'RET' -> 'sector_return'
        ).fillna(0)
        
        # calculate_performance 함수와의 일관성을 위해 인덱스 이름 변경
        daily_returns.index.name = 'date' 
        
        # 백테스트 기간(INVEST_START) 및 20영업일을 포함하도록 데이터 필터링
        # (날짜 오프셋을 줘서 20영업일을 포함하도록 함)
        filter_start = pd.to_datetime(INVEST_START) - pd.DateOffset(days=5)
        daily_returns = daily_returns[daily_returns.index >= filter_start]
        
        print("로드 및 피벗 완료. 실제 일별 수익률 데이터 (wide format, 앞 5줄):")
        print(daily_returns.head())

    except Exception as e:
        print(f"오류: sector_daily_returns() 호출 또는 수익률 데이터 피벗 중 실패: {e}")
        daily_returns = None
        exit() # 데이터 로드 실패 시 실행 중지
    

    # --- 4. 백테스트 수행 ---
    print("\n" + "="*50)
    print("백테스트 성과 계산 시작...")
    print("="*50)
    
    mvo_performance = None
    bl_performance = None

    # daily_returns가 성공적으로 로드되었는지 확인
    if daily_returns is None or daily_returns.empty:
        print("오류: 일별 수익률 데이터가 없어 백테스트를 수행할 수 없습니다.")
        exit()

    if mvo_weights_df is not None and not mvo_weights_df.empty:
        print("\n--- MVO 포트폴리오 백테스트 실행 ---")
        mvo_performance = calculate_performance(mvo_weights_df, daily_returns, investment_months_list)
    else:
        print("\n--- MVO 가중치가 없거나 비어있어 백테스트를 건너뜁니다 ---")

    if bl_weights_df is not None and not bl_weights_df.empty:
        print("\n--- BL(AI) 포트폴리오 백테스트 실행 ---")
        bl_performance = calculate_performance(bl_weights_df, daily_returns, investment_months_list)
    else:
        print("\n--- BL(AI) 가중치가 없거나 비어있어 백테스트를 건너뜁니다 ---")

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
        if mvo_performance is not None:
            print("\nMVO 성과:")
            print(mvo_performance.to_string())
        if bl_performance is not None:
            print("\nBL 성과:")
            print(bl_performance.to_string())