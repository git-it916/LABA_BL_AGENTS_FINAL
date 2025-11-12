import pandas as pd
import numpy as np
from scipy.stats import linregress
from pandas.tseries.offsets import MonthEnd
import warnings

# python -m aiportfolio.agents.prepare.Tier1_calculate

# 불필요한 경고 메시지를 무시합니다.
warnings.filterwarnings("ignore")

from aiportfolio.BL_MVO.prepare.preprocessing_수정중 import final

# --- 헬퍼 함수: R-squared 계산기(추세 강도) ---
def calculate_r_squared(series: pd.Series) -> float:
    """
    주어진 시계열(가격) 데이터에 대해 선형 회귀를 수행하고 R-squared를 반환합니다.
    y = a*x + b (y=가격, x=시간)
    """
    y = series.dropna()
    if len(y) < 2:
        return np.nan
    #시간 공백 압축
    x = np.arange(len(y))
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        return r_value ** 2
    except ValueError:
        return np.nan

# --- 메인 함수: 롤링 퀀트 지표 계산 ---
def calculate_rolling_indicators(price_df: pd.DataFrame, view_months_list: list) -> pd.DataFrame:
    """
    주어진 월별 가격 데이터(price_df)를 기반으로,
    지정된 뷰 생성 월(view_months_list)에 맞춰
    5가지 퀀트 지표를 롤링 방식으로 계산합니다.
    
    Args:
        price_df (pd.DataFrame): Index=DatetimeIndex(월말), Columns=섹터명
        view_months_list (list): 뷰를 생성할 연-월 리스트 (예: ['2024-05', '2024-06'])
        
    Returns:
        pd.DataFrame: (as_of_date, sector)를 인덱스로 하는 MultiIndex DataFrame
    """
    
    all_results = []
    
    # 전체 기간의 월별 수익률을 slicing

    returns_df = price_df.pct_change()

    for view_month_str in view_months_list:
        view_date_start = pd.to_datetime(view_month_str)
        as_of_date = view_date_start - MonthEnd(1)
        
        prices_slice = price_df.loc[:as_of_date]
        returns_slice = returns_df.loc[:as_of_date]

        sectors = price_df.columns
        indicator_results = pd.DataFrame(index=sectors)
        indicator_results['as_of_date'] = as_of_date
        
        # --- 5가지 지표 계산 ---
        
        # 1. 최근 12개월 월별 수익률 (12m_returns)
        recent_12m_returns_data = returns_slice.tail(12) # 이름 변경: raw data임을 명시
        indicator_results['12m_returns'] = [
            list(recent_12m_returns_data[col].dropna()) for col in sectors
        ]

        # 2. 3년 평균 복리 수익률 (cagr_3y)
        prices_3y = prices_slice.tail(37)
        if len(prices_3y) == 37:
            start_price = prices_3y.iloc[0]
            end_price = prices_3y.iloc[-1]
            cagr = (end_price / start_price) ** (1/3) - 1
            indicator_results['cagr_3y'] = cagr
        else:
            indicator_results['cagr_3y'] = np.nan

        # 3. 변동성 (volatility) - 12개월 로그 수익률 표준편차 연율화 (수정됨)
        # 월별 로그 수익률 계산
        simple_returns_12m = returns_slice.tail(12)
        
        if len(simple_returns_12m) == 12:
            
            # --- ▼▼▼ 단위(Unit) 수정 코드 추가 ▼▼▼ ---
            # simple_returns_12m이 백분율(72.64)이므로,
            # 계산을 위해 소수점(0.7264)으로 변경합니다.
            simple_returns_12m_decimal = simple_returns_12m / 100.0
            # --- ▲▲▲ 코드 추가 완료 ▲▲▲ ---

            # 월별 '소수점' 수익률의 표준편차를 계산하고 연율화
            indicator_results['volatility'] = simple_returns_12m_decimal.std() * np.sqrt(12)
        else:
            indicator_results['volatility'] = np.nan
        # 4. 평균 회귀 신호 (z_score) - 24개월 수익률 기준
        recent_24m_returns = returns_slice.tail(24)
        if len(recent_24m_returns) == 24:
            mean_24m = recent_24m_returns.mean()
            std_24m = recent_24m_returns.std()
            current_return = recent_24m_returns.iloc[-1]
            z_score = (current_return - mean_24m) / std_24m
            indicator_results['z_score'] = z_score
        else:
            indicator_results['z_score'] = np.nan

        # 5. 추세 강도 (trend_strength_r2) - 12개월 가격 기준 R^2
        recent_12m_prices = prices_slice.tail(12)
        indicator_results['trend_strength_r2'] = recent_12m_prices.apply(calculate_r_squared)
        
        all_results.append(indicator_results)

    if not all_results:
        print("[경고] 생성된 지표가 없습니다. view_months_list 또는 price_df를 확인하세요.")
        return pd.DataFrame()
        
    final_df = pd.concat(all_results)
    final_df = final_df.reset_index().rename(columns={'index': 'sector'})
    final_df = final_df.set_index(['as_of_date', 'sector']).sort_index()
    
    return final_df

# --- return.py의 메인 실행 함수 (수정됨) ---
def indicator(): 
    raw_data_from_final = final()
    print("--- final() 함수로부터 불러온 원본 데이터 (Head) ---")
    print(raw_data_from_final.head())

    # --- (중간 생략) ... price_df_for_indicators 생성 ... ---

    price_df_for_indicators = raw_data_from_final.pivot_table(
        index='date',
        columns='gsector',
        values='sector_return' 
    )
    
    price_df_for_indicators.columns = [f'gsector_{col}' for col in price_df_for_indicators.columns]
    price_df_for_indicators.index.name = 'Date'
    
    print("\n--- 지표 계산을 위한 price_df (Head) ---")
    print(price_df_for_indicators.head())
    
    # 3. 롤링 지표 계산 함수를 호출합니다.
    target_view_months = [
        '2024-05', '2024-06', '2024-07', '2024-08',
        '2024-09', '2024-10', '2024-11', '2024-12'
    ]
    
    # [수정 1] 원본 MultiIndex 결과를 별도 변수에 저장합니다.
    rolling_indicator_data_multi_index = calculate_rolling_indicators(
        price_df=price_df_for_indicators,
        view_months_list=target_view_months
    )

    print("\n--- 최종 롤링 지표 데이터 (Head - 원본 MultiIndex) ---")
    print(rolling_indicator_data_multi_index.head())

    

    # 4. [신규] MultiIndex를 풀고 'as_of_date'와 'sector'를 일반 열로 변환
    print("\n[알림] MultiIndex를 Long Format 테이블로 변환합니다...")
    final_long_format_df = rolling_indicator_data_multi_index.reset_index()
    
    # 5. [신규] 컬럼명을 사용자의 이미지(a.head())와 유사하게 변경
    
    # 'sector' 컬럼의 'gsector_' 접두사 제거 (예: 'gsector_10' -> '10')
    final_long_format_df['sector'] = final_long_format_df['sector'].str.replace('gsector_', '')
    
    
    # 컬럼명 변경 (as_of_date -> date, sector -> gsector)
    final_long_format_df = final_long_format_df.rename(columns={
        'as_of_date': 'date', 
        'sector': 'gsector',
        '12m_returns': 'return_list'
    })

    print("\n--- 최종 롤링 지표 데이터 (Head - 변환된 Long Format) ---")
    print(final_long_format_df.head())
    
    # --- ▲▲▲ 코드 추가 완료 ▲▲▲ ---

    # [수정 2] 변환된 Long Format DataFrame을 반환합니다.
    return final_long_format_df

# 이 파일이 직접 실행될 때 indicator 함수를 호출합니다.
if __name__ == "__main__":
    print("[알림] return.py 스크립트 실행 시작...")
    final_indicators = indicator()
    print("\n[알림] return.py 스크립트 실행 완료.")
    print("\n최종 지표 데이터 (Long Format)의 형태:") # 'Long Format'임을 명시
    print(final_indicators.info())