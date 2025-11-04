import pandas as pd
import numpy as np
from scipy.stats import linregress
from pandas.tseries.offsets import MonthEnd
import warnings

# 불필요한 경고 메시지를 무시합니다.
warnings.filterwarnings("ignore")

# --- 1. (테스트용) 가상 가격 데이터 생성 함수 ---
# (실제 적용 시: 이 함수 대신 실제 price_df를 로드하십시오.)
def create_dummy_price_data():
    """
    롤링 계산을 테스트하기에 충분한 기간(2020년~2024년)의
    11개 섹터 월말 가격 가상 데이터를 생성합니다.
    """
    sectors = ['정보기술(IT)', '금융', '헬스케어', '유틸리티', '산업재', '소재',
               '에너지', '커뮤니케이션', '필수소비재', '경기소비재', '부동산']
    
    # 3년 CAGR + 1년 롤링을 위해 최소 4년치 데이터 생성
    dates = pd.date_range(start='2020-01-31', end='2024-12-31', freq='M')
    
    # 로그 정규분포를 따르는 주가 시뮬레이션
    data = {}
    for sector in sectors:
        # 섹터별로 약간 다른 드리프트와 변동성 부여
        drift = np.random.uniform(0.001, 0.01)
        vol = np.random.uniform(0.03, 0.08)
        
        prices = [100]
        for _ in range(1, len(dates)):
            change = np.exp(np.random.normal(drift, vol))
            prices.append(prices[-1] * change)
        data[sector] = prices

    df = pd.DataFrame(data, index=dates, columns=sectors)
    df.index.name = 'Date'
    return df

# --- 2. 헬퍼 함수: R-squared 계산기 ---
def calculate_r_squared(series: pd.Series) -> float:
    """
    주어진 시계열(가격) 데이터에 대해 선형 회귀를 수행하고 R-squared를 반환합니다.
    y = a*x + b (y=가격, x=시간)
    """
    # 결측치 제거
    y = series.dropna()
    if len(y) < 2:
        return np.nan
    
    # x축 (시간) 생성 (0, 1, 2, 3, ...)
    x = np.arange(len(y))
    
    # 선형 회귀
    try:
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        # R-squared 반환
        return r_value ** 2
    except ValueError:
        return np.nan

# --- 3. 메인 함수: 롤링 퀀트 지표 계산 ---
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
    
    # 전체 기간의 월별 수익률을 한 번만 계산
    returns_df = price_df.pct_change()

    # 1. 지정된 8개월(또는 N개월)에 대해 루프 실행
    for view_month_str in view_months_list:
        # '2024-05' -> '2024-05-01'
        view_date_start = pd.to_datetime(view_month_str)
        
        # [핵심] 뷰 생성일(5/1) 기준 데이터 마감일(4/30) 계산
        # '2024-05-01' - 1달 offset = '2024-04-30' (MonthEnd)
        as_of_date = view_date_start - MonthEnd(1)
        
        # 이 시점(as_of_date)까지 사용 가능한 데이터 슬라이싱
        prices_slice = price_df.loc[:as_of_date]
        returns_slice = returns_df.loc[:as_of_date]

        # 11개 섹터 이름을 기반으로 결과 DataFrame 초기화
        sectors = price_df.columns
        indicator_results = pd.DataFrame(index=sectors)
        indicator_results['as_of_date'] = as_of_date
        
        # --- 5가지 지표 계산 ---
        
        # 1. 최근 12개월 월별 수익률 (12m_returns)
        # (as_of_date 포함, 12개월간의 수익률)
        recent_12m_returns = returns_slice.tail(12)
        # DataFrame의 각 셀에 list 객체로 저장
        indicator_results['12m_returns'] = [
            list(recent_12m_returns[col].dropna()) for col in sectors
        ]

        # 2. 3년 평균 복리 수익률 (cagr_3y)
        # (37개월간의 가격 데이터 필요: 36개 구간)
        prices_3y = prices_slice.tail(37)
        if len(prices_3y) == 37:
            start_price = prices_3y.iloc[0] # 36개월 전 가격
            end_price = prices_3y.iloc[-1]  # 현재(as_of_date) 가격
            cagr = (end_price / start_price) ** (1/3) - 1
            indicator_results['cagr_3y'] = cagr
        else:
            indicator_results['cagr_3y'] = np.nan # 데이터 부족

        # 3. 변동성 (volatility) - 12개월 수익률 표준편차
        indicator_results['volatility'] = recent_12m_returns.std()

        # 4. 평균 회귀 신호 (z_score) - 24개월 수익률 기준
        # (안정적인 신호를 위해 24개월 사용)
        recent_24m_returns = returns_slice.tail(24)
        if len(recent_24m_returns) == 24:
            mean_24m = recent_24m_returns.mean()
            std_24m = recent_24m_returns.std()
            # 가장 최근 월(as_of_date) 수익률
            current_return = recent_24m_returns.iloc[-1]
            z_score = (current_return - mean_24m) / std_24m
            indicator_results['z_score'] = z_score
        else:
            indicator_results['z_score'] = np.nan # 데이터 부족

        # 5. 추세 강도 (trend_strength_r2) - 12개월 가격 기준 R^2
        recent_12m_prices = prices_slice.tail(12)
        # apply를 사용하여 각 섹터(컬럼)별로 R^2 헬퍼 함수 적용
        indicator_results['trend_strength_r2'] = recent_12m_prices.apply(calculate_r_squared)
        
        all_results.append(indicator_results)

    # 2. 모든 롤링 결과를 하나의 DataFrame으로 결합
    if not all_results:
        print("[경고] 생성된 지표가 없습니다. view_months_list 또는 price_df를 확인하세요.")
        return pd.DataFrame()
        
    final_df = pd.concat(all_results)
    
    # 3. (as_of_date, sector)로 MultiIndex 재구성
    final_df = final_df.reset_index().rename(columns={'index': 'sector'})
    final_df = final_df.set_index(['as_of_date', 'sector']).sort_index()
    
    return final_df

# --- 4. [메인] 스크립트 실행부 ---
# (이 부분이 지표 계산 코드를 '부르는' 부분입니다)
if __name__ == "__main__":
    
    print("[알림] 1. 테스트용 가상 월별 가격 데이터를 생성합니다...")
    # (실제 적용 시: 이 라인 대신 실제 데이터를 로드하세요)
    # 예: price_data = pd.read_csv("my_sector_prices.csv", index_col=0, parse_dates=True)
    price_data = create_dummy_price_data()

    print("샘플 가격 데이터 (마지막 5행):")
    print(price_data.tail())

    # 뷰(View)를 생성할 8개월 정의
    target_view_months = [
        '2024-05', '2024-06', '2024-07', '2024-08',
        '2024-09', '2024-10', '2024-11', '2024-12'
    ]
    
    print(f"\n[알림] 2. {len(target_view_months)}개월간의 롤링 지표 계산을 시작합니다...")
    
    # (핵심) 롤링 지표 계산 함수 호출
    rolling_indicator_data = calculate_rolling_indicators(
        price_df=price_data,
        view_months_list=target_view_months
    )

    print("\n[성공] 롤링 지표 계산 완료! (총 88개 행 = 8개월 * 11개 섹터)")
    
    print("\n--- 전체 롤링 지표 데이터 (Head) ---")
    print("MultiIndex(as_of_date, sector)로 구성된 상위 5개 행입니다.")
    print(rolling_indicator_data.head())
    
    print("\n--- 결과 (첫 번째 시점: 2024-04-30 기준) ---")
    # .loc['2024-04-30']을 사용하면 해당 날짜의 11개 섹터가 모두 나옵니다.
    print(rolling_indicator_data.loc['2024-04-30'].head()) 

    print("\n--- '정보기술(IT)' 섹터의 롤링 Z-score 변화 ---")
    # .xs()를 사용하면 특정 섹터(level='sector')의 데이터만 추출할 수 있습니다.
    print(rolling_indicator_data.xs('정보기술(IT)', level='sector')['z_score'])
  