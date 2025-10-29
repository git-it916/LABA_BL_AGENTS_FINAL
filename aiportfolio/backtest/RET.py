import pandas as pd
import numpy as np
from datetime import datetime

# 1. data_prepare 및 preprocessing 모듈에서 실제 함수 임포트
try:
    from aiportfolio.backtest.data_prepare import calculate_monthly_mvo_weights, open_log
except ImportError:
    print("오류: data_prepare 모듈(calculate_monthly_mvo_weights, open_log)을 임포트할 수 없습니다.")
    print("aiportfolio/backtest/data_prepare.py 파일이 올바른 위치에 있는지 확인하세요.")
    exit()

try:
    from aiportfolio.backtest.preprocessing import sector_daily_returns
except ImportError:
    print("오류: preprocessing 모듈(sector_daily_returns)을 임포트할 수 없습니다.")
    print("aiportfolio/backtest/preprocessing.py 파일이 올바른 위치에 있는지 확인하세요.")
    exit()


# 2. 백테스트 성과 계산 함수 (디버깅 추가)
def calculate_performance(monthly_weights_df, daily_returns_df, investment_months, portfolio_name="Portfolio"):
    """
    주어진 월별 가중치와 일별 수익률로 20일간의 누적 성과를 계산합니다.
    (monthly_weights_df는 long-format, daily_returns_df는 wide-format)
    """
    
    print(f"\n[{portfolio_name}] 디버깅 정보:")
    print(f"가중치 데이터 shape: {monthly_weights_df.shape}")
    print(f"가중치 데이터 컬럼: {monthly_weights_df.columns.tolist()}")
    print(f"가중치 데이터 샘플 (앞 3줄):")
    print(monthly_weights_df.head(3))
    
    try:
        # 가중치 DF (long) -> wide-format으로 피벗
        weights_wide = monthly_weights_df.pivot(
            index='InvestmentMonth', 
            columns='SECTOR', 
            values='Weight'
        ).fillna(0)
        
        print(f"\n피벗 후 가중치 shape: {weights_wide.shape}")
        print(f"피벗 후 섹터(컬럼): {weights_wide.columns.tolist()}")
        print(f"투자 월(인덱스): {weights_wide.index.tolist()}")
        print(f"가중치 샘플 (첫 번째 월):")
        print(weights_wide.iloc[0])
        
    except Exception as e:
        print(f"오류: 가중치 DF를 피벗하는 중 실패: {e}")
        print("로드된 가중치 DF의 컬럼:", monthly_weights_df.columns)
        return None

    print(f"\n일별 수익률 데이터 shape: {daily_returns_df.shape}")
    print(f"일별 수익률 섹터(컬럼): {daily_returns_df.columns.tolist()}")
    
    # 섹터명 불일치 확인
    weight_sectors = set(weights_wide.columns)
    return_sectors = set(daily_returns_df.columns)
    
    if weight_sectors != return_sectors:
        print(f"\n⚠️ 경고: 섹터명 불일치 발견!")
        print(f"가중치에만 있는 섹터: {weight_sectors - return_sectors}")
        print(f"수익률에만 있는 섹터: {return_sectors - weight_sectors}")

    all_monthly_cum_returns = []
    processed_months = 0

    for investment_month in investment_months:
        if investment_month not in weights_wide.index:
            print(f"⚠️ 경고: {investment_month.date()}의 가중치 데이터가 없습니다. 건너뜁니다.")
            continue

        weights = weights_wide.loc[investment_month]
        print(f"\n처리 중: {investment_month.date()}")
        print(f"가중치 합계: {weights.sum():.6f}")
        print(f"0이 아닌 가중치 개수: {(weights != 0).sum()}")
        
        try:
            first_bday = daily_returns_df.index[
                daily_returns_df.index >= investment_month
            ][0]
            print(f"첫 영업일: {first_bday.date()}")
        except IndexError:
            print(f"⚠️ 경고: {investment_month.date()} 이후의 수익률 데이터가 없습니다. 건너뜁니다.")
            continue
            
        start_idx = daily_returns_df.index.get_loc(first_bday)
        daily_returns_20d = daily_returns_df.iloc[start_idx : start_idx + 20]
        
        if len(daily_returns_20d) < 20:
            print(f"⚠️ 경고: {investment_month.date()}의 20일치 영업일 데이터가 부족합니다 (보유: {len(daily_returns_20d)}일).")
        
        # 수익률(DataFrame)과 가중치(Series)의 컬럼(섹터)을 정렬/
        aligned_returns, aligned_weights = daily_returns_20d.align(weights, axis=1, fill_value=0)
        
        print(f"정렬 후 shape - 수익률: {aligned_returns.shape}, 가중치: {aligned_weights.shape}")
        print(f"정렬 후 가중치 합계: {aligned_weights.sum():.6f}")

        # (20, N) . (N,) -> (20,) : 20일간의 일별 포트폴리오 수익률
        port_daily_return = aligned_returns.dot(aligned_weights)
        
        print(f"첫 3일 일별 수익률: {port_daily_return.iloc[:3].values}")
        
        port_cum_return = port_daily_return.cumsum()
        port_cum_return.index = range(1, len(port_cum_return) + 1)
        all_monthly_cum_returns.append(port_cum_return)
        processed_months += 1
        
        if processed_months >= 2:  # 처음 2개월만 상세 출력
            print("(이후 월은 간략히 처리됩니다...)")
            break

    if not all_monthly_cum_returns:
        print("❌ 오류: 계산된 월별 수익률이 없습니다.")
        return None
        
    combined_cum_returns = pd.concat(all_monthly_cum_returns, axis=1, sort=True)
    print(f"\n결합된 누적 수익률 shape: {combined_cum_returns.shape}")
    print(f"결합된 누적 수익률 샘플:")
    print(combined_cum_returns.iloc[:5, :min(3, combined_cum_returns.shape[1])])
    
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
    print(f"투자 월 목록: {[d.date() for d in investment_months_list]}")

    # --- 2. 월별 가중치 준비 (data_prepare 함수 호출) ---
    print("\n가중치 데이터 로딩 중...")
    mvo_weights_df = calculate_monthly_mvo_weights(
        hist_start_date=HIST_START, 
        investment_start_date=INVEST_START,
        investment_end_date=INVEST_END
    )
    bl_weights_df = open_log()

    # --- 3. 일별 수익률 데이터 준비 ---
    print(f"\n실제 데이터: {HIST_START} ~ {INVEST_END} 기간의 일별 수익률 데이터를 로드합니다.")
    
    try:
        long_returns_df = sector_daily_returns()
        
        if long_returns_df is None or long_returns_df.empty:
            raise ValueError("preprocessing.sector_daily_returns()가 비어있는 DataFrame을 반환했습니다.")

        if not all(col in long_returns_df.columns for col in ['DlyCalDt', 'gsector', 'sector_return']):
            raise ValueError("로드된 데이터에 'DlyCalDt', 'gsector', 'sector_return' 컬럼이 없습니다.")

        long_returns_df['DlyCalDt'] = pd.to_datetime(long_returns_df['DlyCalDt'])

        daily_returns = long_returns_df.pivot(
            index='DlyCalDt',
            columns='gsector',
            values='sector_return'
        ).fillna(0)
        
        daily_returns.index.name = 'date' 
        
        filter_start = pd.to_datetime(INVEST_START) - pd.DateOffset(days=5)
        daily_returns = daily_returns[daily_returns.index >= filter_start]
        
        print("로드 및 피벗 완료. 실제 일별 수익률 데이터 (wide format, 앞 5줄):")
        print(daily_returns.head())

    except Exception as e:
        print(f"오류: sector_daily_returns() 호출 또는 수익률 데이터 피벗 중 실패: {e}")
        exit()
    

    # --- 4. 백테스트 수행 ---
    print("\n" + "="*50)
    print("백테스트 성과 계산 시작...")
    print("="*50)

    if daily_returns is None or daily_returns.empty:
        print("오류: 일별 수익률 데이터가 없어 백테스트를 수행할 수 없습니다.")
        exit()

    mvo_performance = None
    bl_performance = None

    if mvo_weights_df is not None and not mvo_weights_df.empty:
        print("\n--- MVO 포트폴리오 백테스트 실행 ---")
        mvo_performance = calculate_performance(mvo_weights_df, daily_returns, investment_months_list, "MVO")
    else:
        print("\n--- MVO 가중치가 없거나 비어있어 백테스트를 건너뜁니다 ---")

    if bl_weights_df is not None and not bl_weights_df.empty:
        print("\n--- BL(AI) 포트폴리오 백테스트 실행 ---")
        bl_performance = calculate_performance(bl_weights_df, daily_returns, investment_months_list, "BL")
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