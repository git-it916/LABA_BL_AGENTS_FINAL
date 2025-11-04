import pandas as pd

from aiportfolio.util.data_cleanse.open_DTB3 import open_rf_rate
from aiportfolio.util.data_cleanse.open_final_stock_daily import open_final_stock_daily
from aiportfolio.util.data_cleanse.open_final_stock_months import open_final_stock_months

# python -m aiportfolio.backtest.preprocessing_2차수정

# ---------- 1) 일별 무위험수익률 제작 ----------
# https://fred.stlouisfed.org/series/DTB3
# 3-Month Treasury Bill Secondary Market Rate, Discount Basis (DTB3) 사용
def preprocess_rf_rate():
    df_rf = open_rf_rate()

    # 컬럼명 변경
    df_rf.rename(columns={'observation_date': 'date', 'DTB3': 'rf_daily'}, inplace=True)

    # 날짜 형식 변환
    df_rf['date'] = pd.to_datetime(df_rf['date'])

    # 무위험 수익률 전처리
    df_rf['rf_daily'] = df_rf['rf_daily'].ffill() # 휴일 때문에 발생하는 결측치 바로 전날의 값으로 채움.
    df_rf['rf_daily'] = df_rf['rf_daily'] / 100  # % -> 소수점 변환
    df_rf['rf_daily'] = (1 + df_rf['rf_daily']) ** (1/252) - 1  # 연율 -> 일율 변환
    
    return df_rf

# ---------- 2) 일별 데이터 전처리 및 초과수익률 제작 ----------
def preprocess_daily_returns():
    df = open_final_stock_daily()
    
    df.rename(columns={'DlyCalDt': 'date'}, inplace=True) # 컬럼명 변경
    df["date"] = pd.to_datetime(df["date"]) # 날짜 형식 변환

    # 날짜 중복되는 종목 처리(시가총액이 가장 큰 것 선택)
    filtered_df = (
        df.sort_values(['Ticker', 'date', 'DlyCap'], ascending=[True, True, False])
        .drop_duplicates(subset=['Ticker', 'date'], keep='first')
        .sort_index()
        .reset_index(drop=True)
    )

    # 초과수익률 계산
    df_rf = preprocess_rf_rate()
    merged_df = pd.merge(filtered_df, df_rf, on='date', how='left') # 종목 데이터 기준으로 병합
    merged_df['excess_return'] = merged_df['DlyRet'] - merged_df['rf_daily'] # 일별 초과수익률 계산

    return merged_df

# --- 3) 포트폴리오 가중치 산출에 이용된 종목들만 필터링하기 위한 더미 데이터프레임 ---
def filtering_dummy():
    
    df_month = open_final_stock_months()
    df_month['date'] = pd.to_datetime(df_month['cyear'].astype(str) + '-' + df_month['cmonth'].astype(str)) + pd.offsets.MonthEnd(0)

    df_month = df_month.sort_values(['Ticker', 'date'])
    df_month['sp500_lag1'] = df_month.groupby('Ticker')['sp500'].shift(1) # 전 월 sp500 값

    df_sp = df_month[df_month['sp500_lag1']==1].copy()

    df_filtered = df_sp[(df_sp['date'] >= "2024-05-01") &(df_sp['date'] <= "2024-12-31")].copy()
    df_filtered['month'] = df_filtered['date'].dt.to_period('M')
    flag_tickers = df_filtered[['month', 'Ticker']].drop_duplicates()

    return flag_tickers

# ---------- 4) 일별 sp500의 초과수익률 제작 ----------
def sp500_daily():
    merged_df = preprocess_daily_returns()

    # 가중치 계산에 사용된 종목만 필터링(여기부터 결측치X)
    merged_df['month'] = merged_df['date'].dt.to_period('M')
    a = filtering_dummy()
    daily_filtered = merged_df.merge(a, on=['month','Ticker'])

    # 전 거래일의 sp500에 해당하는 불리언 컬럼 추가 및 필터링
    daily_filtered = daily_filtered.sort_values(['Ticker', 'date']).copy()
    daily_filtered['sp500_lag1'] = daily_filtered.groupby('Ticker')['sp500'].shift(1)
    sp_filtered = daily_filtered[daily_filtered['sp500_lag1']==1].copy()

    # 전 월의 시가총액을 매칭
    sp_filtered = sp_filtered.sort_values(['Ticker', 'date']).copy()
    sp_filtered['prev_DlyCap'] = sp_filtered.groupby('Ticker')['DlyCap'].shift(1)

    # 가중수익률 계산
    sp_filtered["_ret_x_cap"] = sp_filtered["excess_return"] * sp_filtered["prev_DlyCap"] # excess_return

    group_keys = ['date', 'gsector']
    agg = (
    sp_filtered.groupby(group_keys, dropna=False)
            .agg(sector_prevmktcap=("prev_DlyCap", "sum"),
                ret_x_cap_sum=("_ret_x_cap", "sum"),
                n_stocks=("Ticker", "count"))
            .reset_index())

    mask = agg["sector_prevmktcap"] != 0
    agg["sector_excess_return"] = agg["ret_x_cap_sum"].div(agg["sector_prevmktcap"]).where(mask)

    # 중간열 제거 및 정리
    agg = agg.drop(columns=["ret_x_cap_sum"])
    agg = agg.sort_values(['date', 'gsector']).reset_index(drop=True).copy()

    return agg

# python -m aiportfolio.backtest.preprocessing_2차수정

# ---------- 5) 일별 시장의 초과수익률 제작 ----------
# def market_daily():
df = preprocess_daily_returns()
a = sp500_daily()
print(a.info())
print(a.head(20))

# ---------- 6) abnormal return 제작 ----------
# def final_abnormal_returns():