import pandas as pd
import numpy as np
from scipy.stats import linregress
from pandas.tseries.offsets import MonthEnd
import warnings

# python -m aiportfolio.agents.prepare.Tier1_calculate

# 불필요한 경고 메시지를 무시합니다.
warnings.filterwarnings("ignore")

try:
    from aiportfolio.BL_MVO.prepare.sector_excess_return import final
    print("[성공] preprocessing_수정중 모듈을 정상적으로 임포트했습니다.")
except ImportError as e:
    print(f"[오류] aiportfolio.BL_MVO.prepare.preprocessing_수정중 임포트 실패: {e}")
    print("[오류] 파일명을 확인하거나 'preprocessing.py'로 변경하세요.")
    print("[오류] 프로덕션 환경에서는 실제 데이터 모듈이 필요합니다.")

    # 임시로 final() 함수를 정의하여 테스트가 가능하도록 합니다.
    # ⚠️ 경고: 실제 실행 시 이 부분은 동작하지 않아야 합니다!
    def final():
        warnings.warn(
            "임시 final() 함수를 사용 중입니다. 가상 데이터로 모델이 실행됩니다!",
            category=UserWarning,
            stacklevel=2
        )
        print("[경고] 가상 데이터 생성 중 - 실제 결과와 다를 수 있습니다!")
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
        # 'YYYY-MM' 형식을 해당 월의 마지막 날로 변환
        view_date_start = pd.to_datetime(view_month_str)
        as_of_date = view_date_start + MonthEnd(0)  # 해당 월의 마지막 날
        
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
            # returns_df는 이미 소수점 단위 (예: 0.0659 = 6.59%, -0.0403 = -4.03%)
            # 추가 변환 없이 바로 표준편차 계산

            # 월별 수익률의 표준편차를 계산하고 연율화
            indicator_results['volatility'] = simple_returns_12m.std() * np.sqrt(12)
        else:
            indicator_results['volatility'] = np.nan

        # 4. 평균 회귀 신호 (z_score)
        #    - 데이터 소스: returns_df (월별 수익률)
        recent_24m_returns = returns_slice.tail(24)
        if len(recent_24m_returns) == 24:
            # returns_df는 이미 소수점 단위
            # Z-score는 표준화된 값이므로 단위에 영향받지 않음
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
    # print("--- final() 함수로부터 불러온 원본 데이터 (Head) ---")
    # print(raw_data_from_final.head())

    raw_data_from_final['date'] = pd.to_datetime(raw_data_from_final['date'])
    
    # --- [수정] '수익률 DF'와 '가격지수 DF'를 모두 생성 ---

    # 1. [신규] '월별 수익률' DataFrame (단위: 소수점, 예: 0.0659 = 6.59%, -0.0403 = -4.03%)
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

    # (1 + 수익률)의 누적곱(cumprod)을 계산하여 '가격 지수'로 변환합니다.
    # (첫 달의 NaN을 0으로 채워서 1+0=1이 되도록 함)
    # 주의: returns_df는 이미 소수점 단위이므로 100으로 나누지 않음
    price_index_df = (1 + returns_df.fillna(0)).cumprod()
    
    # 3. [신규] 컬럼명 정리 (두 DataFrame의 컬럼명이 일치해야 함)
    gsector_columns = [f'gsector_{col}' for col in returns_df.columns]
    returns_df.columns = gsector_columns
    price_index_df.columns = gsector_columns
    
    returns_df.index.name = 'Date'
    price_index_df.index.name = 'Date'
    
    # print("\n--- 1. 지표 계산을 위한 '월별 수익률' (Head) ---")
    # print(returns_df.head())
    # print("\n--- 2. 지표 계산을 위한 '가격 지수' (Head) ---")
    # print(price_index_df.head())

    # 3. 롤링 지표 계산 함수를 호출합니다.
    # 동적으로 사용 가능한 모든 월말 날짜를 생성합니다.
    # CAGR 계산을 위해 최소 37개월(3년+1개월)이 필요하므로, 충분한 데이터가 있는 날짜만 포함
    all_dates = returns_df.index.sort_values()

    # 최소 37개월 이전 날짜부터 시작 (CAGR 계산 가능)
    min_required_months = 37
    if len(all_dates) >= min_required_months:
        valid_start_idx = min_required_months - 1
        target_dates = all_dates[valid_start_idx:]

        # 'YYYY-MM' 형식으로 변환
        target_view_months = [date.strftime('%Y-%m') for date in target_dates]
    else:
        print(f"[경고] 데이터가 {min_required_months}개월 미만입니다. CAGR 계산이 불가능할 수 있습니다.")
        target_view_months = [date.strftime('%Y-%m') for date in all_dates]

    # [수정] 2개의 DataFrame을 인자로 전달
    rolling_indicator_data_multi_index = calculate_rolling_indicators(
        price_index_df=price_index_df,
        returns_df=returns_df,
        view_months_list=target_view_months
    )

    # print("\n--- 최종 롤링 지표 데이터 (Head - 원본 MultiIndex) ---")
    # print(rolling_indicator_data_multi_index.head())

    # 4. [신규] MultiIndex를 풀고 'as_of_date'와 'sector'를 일반 열로 변환
    # print("\n[알림] MultiIndex를 Long Format 테이블로 변환합니다...")
    final_long_format_df = rolling_indicator_data_multi_index.reset_index()
    
    # 5. [신규] 컬럼명을 사용자의 이미지(a.head())와 유사하게 변경
    final_long_format_df['sector'] = final_long_format_df['sector'].str.replace('gsector_', '')
    final_long_format_df = final_long_format_df.rename(columns={
        'as_of_date': 'date',
        'sector': 'gsector'
    })

    # print("\n--- 최종 롤링 지표 데이터 (Head - 변환된 Long Format) ---")
    # print(final_long_format_df.head())
    
    # 6. [수정] 변환된 Long Format DataFrame을 반환합니다.

    final_long_format_df.rename(columns={
    '12m_returns': 'return_list',
    'cagr_3y': 'CAGR',
    'volatility': 'volatility',
    'z_score': 'z-score',
    'trend_strength_r2': 'trend_strength'
    }, inplace=True)

    gics_mapping = {
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

    final_long_format_df['gsector'] = (
    final_long_format_df['gsector']
        .astype(str)
        .str.strip()       # 공백 제거
        .astype(float)
        .astype(int)
        .map(gics_mapping)
    )

    return final_long_format_df

# 메인 실행 코드 (모듈로 임포트될 때는 실행되지 않음)
if __name__ == "__main__":
    a = indicator()
    print(a.head())
    print(a.info())