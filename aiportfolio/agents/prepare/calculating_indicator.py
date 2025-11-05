import pandas as pd
import numpy as np
from scipy.stats import linregress
from pandas.tseries.offsets import MonthEnd
import warnings

# python -m aiportfolio.agents.prepare.calculating_indicator

# 불필요한 경고 메시지를 무시합니다.
warnings.filterwarnings("ignore")

try:
    from aiportfolio.BL_MVO.prepare.preprocessing_수정중 import final
except ImportError:
    print("[경고] aiportfolio.BL_MVO.prepare.preprocessing_수정중 임포트 실패.")
    # 임시로 final() 함수를 정의하여 테스트가 가능하도록 합니다.
    # (실제 실행 시 이 부분은 동작하지 않아야 함)
    def final():
        print("[알림] 임시 final() 함수 사용 중. 2015년부터 2024년까지의 가상 수익률 데이터 생성")
        sectors = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        dates = pd.date_range(start='2015-01-31', end='2024-12-31', freq='M')
        data = []
        for date in dates:
            for gsector in sectors:
                # 백분율(%) 단위의 수익률을 생성합니다. (예: -10 ~ +10)
                sector_return = np.random.uniform(-10, 10)
                data.append({'date': date, 'gsector': gsector, 'sector_return': sector_return})
        return pd.DataFrame(data)

# --- 헬퍼 함수: R-squared 계산기(추세 강도) ---
def calculate_r_squared(series: pd.Series) -> float:
    """
    주어진 시계열(가격) 데이터에 대해 선형 회귀를 수행하고 R-squared를 반환합니다.
    y = a*x + b (y=가격, x=시간)
    """
    y = series.dropna()
    if len(y) < 2:
        return np.nan
    x = np.arange(len(y))
    
    try:
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        return r_value ** 2
    except ValueError:
        return np.nan

# --- 메인 함수: 롤링 퀀트 지표 계산 (수정됨) ---
def calculate_rolling_indicators(
    price_index_df: pd.DataFrame, 
    returns_df: pd.DataFrame, 
    view_months_list: list
) -> pd.DataFrame:
    """
    주어진 '가격 지수'와 '월별 수익률' 데이터를 기반으로,
    지정된 뷰 생성 월(view_months_list)에 맞춰
    5가지 퀀트 지표를 롤링 방식으로 계산합니다.
    
    Args:
        price_index_df (pd.DataFrame): 가격 지수 (cagr_3y, trend_strength_r2 용)
        returns_df (pd.DataFrame): 월별 수익률 (12m_returns, volatility, z_score 용)
        view_months_list (list): 뷰를 생성할 연-월 리스트
        
    Returns:
        pd.DataFrame: (as_of_date, sector)를 인덱스로 하는 MultiIndex DataFrame
    """
    
    all_results = []
    
    # [수정] returns_df는 이미 수익률이므로 pct_change()가 필요 없습니다.
    # returns_df = price_df.pct_change() # <- [삭제]

    for view_month_str in view_months_list:
        view_date_start = pd.to_datetime(view_month_str)
        as_of_date = view_date_start - MonthEnd(1)
        
        # [수정] 2종류의 데이터를 각각 슬라이싱합니다.
        price_index_slice = price_index_df.loc[:as_of_date]
        returns_slice = returns_df.loc[:as_of_date]

        sectors = price_index_df.columns # 컬럼명은 동일
        indicator_results = pd.DataFrame(index=sectors)
        indicator_results['as_of_date'] = as_of_date
        
        # --- 5가지 지표 계산 (각각 올바른 데이터 소스 사용) ---
        
        # 1. 최근 12개월 월별 수익률 (12m_returns)
        #    - 데이터 소스: returns_df (월별 수익률)
        recent_12m_returns_data = returns_slice.tail(12)
        indicator_results['12m_returns'] = [
            list(recent_12m_returns_data[col].dropna()) for col in sectors
        ]

        # 2. 3년 평균 복리 수익률 (cagr_3y)
        #    - 데이터 소스: price_index_df (가격 지수)
        price_index_3y = price_index_slice.tail(37)
        if len(price_index_3y) == 37:
            start_price = price_index_3y.iloc[0]
            end_price = price_index_3y.iloc[-1]
            
            # 0 또는 음수 가격 지수를 방지하기 위한 안전장치
            if (start_price > 0).all() and (end_price > 0).all():
                cagr = (end_price / start_price) ** (1/3) - 1
                indicator_results['cagr_3y'] = cagr
            else:
                # (이론상 발생 안해야 함)
                indicator_results['cagr_3y'] = np.nan 
        else:
            indicator_results['cagr_3y'] = np.nan # 데이터 기간 부족 시 NaN

        # 3. 변동성 (volatility)
        #    - 데이터 소스: returns_df (월별 수익률)
        simple_returns_12m = returns_slice.tail(12)
        
        if len(simple_returns_12m) == 12:
            # 12m_returns 열에서 본 것처럼, 수익률이 백분율(%) 단위 (예: -4.03, 72.64)
            # 계산을 위해 소수점 단위 (예: -0.0403, 0.7264)로 변경
            simple_returns_12m_decimal = simple_returns_12m / 100.0
            
            # 월별 '소수점' 수익률의 표준편차를 계산하고 연율화
            indicator_results['volatility'] = simple_returns_12m_decimal.std() * np.sqrt(12)
        else:
            indicator_results['volatility'] = np.nan

        # 4. 평균 회귀 신호 (z_score)
        #    - 데이터 소스: returns_df (월별 수익률)
        recent_24m_returns = returns_slice.tail(24)
        if len(recent_24m_returns) == 24:
            # Z-score는 원래 데이터의 단위(%)에 영향을 받지 않으므로 100으로 나눌 필요 없음
            mean_24m = recent_24m_returns.mean()
            std_24m = recent_24m_returns.std()
            current_return = recent_24m_returns.iloc[-1]
            
            # 0으로 나누기 방지
            if (std_24m > 0).all():
                 z_score = (current_return - mean_24m) / std_24m
                 indicator_results['z_score'] = z_score
            else:
                 indicator_results['z_score'] = np.nan
        else:
            indicator_results['z_score'] = np.nan

        # 5. 추세 강도 (trend_strength_r2)
        #    - 데이터 소스: price_index_df (가격 지수)
        recent_12m_price_index = price_index_slice.tail(12)
        indicator_results['trend_strength_r2'] = recent_12m_price_index.apply(calculate_r_squared)
        
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

    raw_data_from_final['date'] = pd.to_datetime(raw_data_from_final['date'])
    
    # --- [수정] '수익률 DF'와 '가격지수 DF'를 모두 생성 ---
    
    # 1. [신규] '월별 수익률' DataFrame (단위: %, 예: 72.64, -4.03)
    #    (데이터 소스: sector_return)
    #    (사용 지표: 12m_returns, volatility, z_score)
    returns_df = raw_data_from_final.pivot_table(
        index='date',
        columns='gsector',
        values='sector_return' 
    )
    
    # 2. [신규] '가격 지수' DataFrame (단위: Index, 예: 100, 98.11)
    #    (데이터 소스: 월별 수익률을 변환)
    #    (사용 지표: cagr_3y, trend_strength_r2)
    
    # (1 + 수익률/100)의 누적곱(cumprod)을 계산하여 '가격 지수'로 변환합니다.
    # (첫 달의 NaN을 0으로 채워서 1+0=1이 되도록 함)
    price_index_df = (1 + returns_df.fillna(0) / 100.0).cumprod()
    
    # 3. [신규] 컬럼명 정리 (두 DataFrame의 컬럼명이 일치해야 함)
    gsector_columns = [f'gsector_{col}' for col in returns_df.columns]
    returns_df.columns = gsector_columns
    price_index_df.columns = gsector_columns
    
    returns_df.index.name = 'Date'
    price_index_df.index.name = 'Date'
    
    print("\n--- 1. 지표 계산을 위한 '월별 수익률' (Head) ---")
    print(returns_df.head())
    print("\n--- 2. 지표 계산을 위한 '가격 지수' (Head) ---")
    print(price_index_df.head())
    
    # 3. 롤링 지표 계산 함수를 호출합니다.
    target_view_months = [
        '2024-05', '2024-06', '2024-07', '2024-08',
        '2024-09', '2024-10', '2024-11', '2024-12'
    ]
    
    # [수정] 2개의 DataFrame을 인자로 전달
    rolling_indicator_data_multi_index = calculate_rolling_indicators(
        price_index_df=price_index_df,
        returns_df=returns_df,
        view_months_list=target_view_months
    )

    print("\n--- 최종 롤링 지표 데이터 (Head - 원본 MultiIndex) ---")
    print(rolling_indicator_data_multi_index.head())

    # 4. [신규] MultiIndex를 풀고 'as_of_date'와 'sector'를 일반 열로 변환
    print("\n[알림] MultiIndex를 Long Format 테이블로 변환합니다...")
    final_long_format_df = rolling_indicator_data_multi_index.reset_index()
    
    # 5. [신규] 컬럼명을 사용자의 이미지(a.head())와 유사하게 변경
    final_long_format_df['sector'] = final_long_format_df['sector'].str.replace('gsector_', '')
    final_long_format_df = final_long_format_df.rename(columns={
        'as_of_date': 'date',
        'sector': 'gsector'
    })

    print("\n--- 최종 롤링 지표 데이터 (Head - 변환된 Long Format) ---")
    print(final_long_format_df.head())
    
    # 6. [수정] 변환된 Long Format DataFrame을 반환합니다.

    final_long_format_df.rename(columns={
    '12m_returns': 'return_list',
    'cagr_3y': 'CAGR',
    'volatility': 'volatility',
    'z_score': 'z-score',
    'trend_strength_r2': 'trend_strength'
    }, inplace=True)

    return final_long_format_df

# 이 파일이 직접 실행될 때 indicator 함수를 호출합니다.
if __name__ == "__main__":
    print("[알림] return.py 스크립트 실행 시작...")
    final_indicators = indicator()
    print("\n[알림] return.py 스크립트 실행 완료.")
    print("\n최종 지표 데이터 (Long Format)의 형태:")
    print(final_indicators.info())

