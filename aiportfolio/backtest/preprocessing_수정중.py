import pandas as pd
import numpy as np

from aiportfolio.util.data_load.open_DTB3 import open_rf_rate
from aiportfolio.util.data_load.open_final_stock_daily import open_final_stock_daily
from aiportfolio.util.data_load.open_final_stock_months import open_final_stock_months

# python -m aiportfolio.backtest.preprocessing_수정중

# ---------- 1) 일별 초과수익률 제작 ----------
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

# ---------- 2) 일별 S&P 500의 섹터별 초과수익률 제작 ----------
def sector_daily_returns():
    df = open_final_stock_daily()
    
    df.rename(columns={'DlyCalDt': 'date'}, inplace=True) # 컬럼명 변경
    df["date"] = pd.to_datetime(df["date"]) # 날짜 형식 변환

    # S&P500 == 1 필터링
    df_sp = df[df["sp500"] == 1].copy()
    df_sp['DlyRet'] = df_sp['DlyRet'].ffill() # 결측치 처리

    df_rf = preprocess_rf_rate()

    # 종목 데이터 기준으로 병합
    merged_df = pd.merge(df_sp, df_rf, on='date', how='left')

    # 일별 초과수익률 계산
    merged_df['excess_return'] = merged_df['DlyRet'] - merged_df['rf_daily']

    # 전 일의 시가총액을 매칭
    merged_df = merged_df.sort_values(['Ticker', 'date']).copy()
    merged_df['prev_DlyCap'] = merged_df.groupby('Ticker')['DlyCap'].shift(1)

    # 가중수익률 계산
    merged_df["_ret_x_cap"] = merged_df["excess_return"] * merged_df["prev_DlyCap"] # excess_return

    group_keys = ['date', 'gsector']
    agg = (
        merged_df.groupby(group_keys, dropna=False)
            .agg(sector_prevmktcap=("prev_DlyCap", "sum"),
                ret_x_cap_sum=("_ret_x_cap", "sum"),
                n_stocks=("Ticker", "count"))
            .reset_index())

    mask = agg["sector_prevmktcap"] != 0
    agg["sector_excess_return"] = agg["ret_x_cap_sum"].div(agg["sector_prevmktcap"]).where(mask)

    agg = agg.drop(columns=["ret_x_cap_sum"]) # 중간열 제거
    agg = agg.sort_values(['date', 'gsector']).reset_index(drop=True).copy() # 정렬

    return agg

# ---------- 3) 일별 market의 초과수익률 제작 ----------
def total_daily_returns():
    df = open_final_stock_daily()

    df.rename(columns={'DlyCalDt': 'date'}, inplace=True) # 컬럼명 변경
    df["date"] = pd.to_datetime(df["date"]) # 날짜 형식 변환

    # 우선주 제거(date 값이 중복되어 있는 Ticker 중에서 DlyCap이 가장 큰 행만 남기기)
    dupes = df[df.duplicated(subset=['Ticker', 'date'], keep=False)] # 중복된 그룹 찾기
    # 중복 그룹 중에서 DlyCap이 가장 큰 행만 남기기
    dupes_max = (
        dupes.sort_values(['Ticker', 'date', 'DlyCap'], ascending=[True, True, False])
            .drop_duplicates(subset=['Ticker', 'date'], keep='first')
    )
    # 중복이 아닌 행 찾기
    non_dupes = df[~df.duplicated(subset=['Ticker', 'date'], keep=False)]
    # 두 결과 합치기
    filtered_df = pd.concat([dupes_max, non_dupes]).sort_index().reset_index(drop=True)

    '''
    추가적인 후처리 필요
    '''

    df_rf = preprocess_rf_rate()

    # 종목 데이터 기준으로 병합
    merged_df = pd.merge(df, df_rf, on='date', how='left')

    # 일별 초과수익률 계산
    merged_df['excess_return'] = merged_df['DlyRet'] - merged_df['rf_daily']

    # 전 일의 시가총액을 매칭
    merged_df = merged_df.sort_values(['Ticker', 'date']).copy()
    merged_df['prev_DlyCap'] = merged_df.groupby('Ticker')['DlyCap'].shift(1)

    # 가중수익률 계산
    merged_df["_ret_x_cap"] = merged_df["excess_return"] * merged_df["prev_DlyCap"] # excess_return

    agg = (
        merged_df.groupby('date', dropna=False)
            .agg(total_prevmktcap=("prev_DlyCap", "sum"),
                ret_x_cap_sum=("_ret_x_cap", "sum"),
                n_stocks=("Ticker", "count"))
            .reset_index())

    mask = agg["total_prevmktcap"] != 0
    agg["total_excess_return"] = agg["ret_x_cap_sum"].div(agg["total_prevmktcap"]).where(mask)

    agg = agg.drop(columns=["ret_x_cap_sum"]) # 중간열 제거
    agg = agg.sort_values(['date']).reset_index(drop=True).copy() # 정렬

    return agg

# ---------- 4) abnormal return 제작 ----------
def final_abnormal_returns():
    a = sector_daily_returns()
    b = total_daily_returns()

    merged_df = pd.merge(a, b, on='date', how='inner')

    merged_df['abnormal_return'] = merged_df['sector_excess_return'] - merged_df['total_excess_return']

    pivoted_df = merged_df.pivot(index='date', columns='gsector', values='abnormal_return')
    df_reset = pivoted_df.reset_index()

    return df_reset


# 포트폴리오 제작 시에 사용된 티커만 추출하기 위한 작업
df = open_final_stock_months()

# date 컬럼 생성 (각 연월의 말일)
df['date'] = pd.to_datetime(df['cyear'].astype(str) + '-' + df['cmonth'].astype(str)) + pd.offsets.MonthEnd(0)

# 포트폴리오 비중 산출에 이용된 티커만 식별할 더미 데이터프레임 제작
df = df.sort_values(['Ticker', 'date']).copy()
df['sp500_lag1'] = df.groupby('Ticker')['sp500'].shift(1)

df_sp = df[df['sp500_lag1']==1].copy()

df_filtered = df_sp[(df_sp['date'] >= "2024-04-01") &(df_sp['date'] < "2024-12-01")].copy()

df_filtered['month'] = df_filtered['date'].dt.to_period('M')
df_filtered['flag'] = df_filtered['month'] + 1
flag_tickers = df_filtered[['flag', 'Ticker']].drop_duplicates()
flag_tickers.rename(columns={'flag': 'month'}, inplace=True)

# 포트폴리오 비중 산출에 이용된 티커만 남도록 필터링
df_daily = open_final_stock_daily()
df_daily.rename(columns={'DlyCalDt': 'date'}, inplace=True)
df_daily["date"] = pd.to_datetime(df_daily["date"])
df_daily['month'] = df_daily['date'].dt.to_period('M')
f_daily_filtered = df_daily.merge(flag_tickers.rename(columns={'flag':'month'}), on=['month','Ticker'])

# 우선주 제거(date 값이 중복되어 있는 Ticker 중에서 DlyCap이 가장 큰 행만 남기기)
dupes = f_daily_filtered[f_daily_filtered.duplicated(subset=['Ticker', 'date'], keep=False)] # 중복된 그룹 찾기
dupes_max = (
    dupes.sort_values(['Ticker', 'date', 'DlyCap'], ascending=[True, True, False])
        .drop_duplicates(subset=['Ticker', 'date'], keep='first')
)
non_dupes = f_daily_filtered[~f_daily_filtered.duplicated(subset=['Ticker', 'date'], keep=False)]
filtered_df = pd.concat([dupes_max, non_dupes]).sort_index().reset_index(drop=True)

# 무위험 수익률 불러와서 초과수익률 제작
df_rf = preprocess_rf_rate()
merged_df = pd.merge(filtered_df, df_rf, on='date', how='left')
merged_df['excess_return'] = merged_df['DlyRet'] - merged_df['rf_daily']

# 전 일의 시가총액을 매칭
merged_df = merged_df.sort_values(['Ticker', 'date']).copy()
merged_df['prev_DlyCap'] = merged_df.groupby('Ticker')['DlyCap'].shift(1)

# 월 내에서 사라지는 애 고려하기 위한 sp500_lag1 생성 및 필터링
merged_df = merged_df.sort_values(['Ticker', 'date']).copy()
merged_df['sp500_lag1'] = merged_df.groupby('Ticker')['sp500'].shift(1)
df_sp_daily = merged_df[merged_df['sp500_lag1']==1].copy()

# 가중수익률 계산
df_sp_daily["_ret_x_cap"] = df_sp_daily["excess_return"] * df_sp_daily["prev_DlyCap"] # excess_return

group_keys = ['date', 'gsector']
agg = (
    df_sp_daily.groupby(group_keys, dropna=False)
        .agg(sector_prevmktcap=("prev_DlyCap", "sum"),
            ret_x_cap_sum=("_ret_x_cap", "sum"),
            n_stocks=("Ticker", "count"))
        .reset_index())

mask = agg["sector_prevmktcap"] != 0
agg["sector_excess_return"] = agg["ret_x_cap_sum"].div(agg["sector_prevmktcap"]).where(mask)

agg = agg.drop(columns=["ret_x_cap_sum"]) # 중간열 제거
agg = agg.sort_values(['date', 'gsector']).reset_index(drop=True).copy() # 정렬

print(agg.head(50))

'''
flag_tickers_count = flag_tickers.groupby('month')['Ticker'].nunique().reset_index()
flag_tickers_count.columns = ['month', 'ticker_count']

f_daily_filtered_count = f_daily_filtered.groupby('date')['Ticker'].nunique().reset_index()
f_daily_filtered_count.columns = ['date', 'ticker_count']

# date에서 month 컬럼 생성
f_daily_filtered_count['month'] = f_daily_filtered_count['date'].dt.to_period('M')

# 월별로 ticker_count의 유니크 값 개수 확인
unique_counts_per_month = f_daily_filtered_count.groupby('month')['ticker_count'].apply(lambda x: x.nunique()).reset_index()
unique_counts_per_month.columns = ['month', 'unique_ticker_count_values']

# 12월 데이터만 추출
dec_data = f_daily_filtered[f_daily_filtered['date'].dt.month == 12]

# 일별로 Ticker 확인
dec_data_counts = dec_data.groupby(['date', 'Ticker']).size().reset_index(name='count')

# 특정 날짜에 누락된 티커 확인
dec_missing = dec_data_counts.groupby('Ticker')['date'].nunique().reset_index()
dec_missing.columns = ['Ticker', 'days_present']
dec_missing = dec_missing[dec_missing['days_present'] < dec_data['date'].nunique()]

missing_dates = dec_data[dec_data['Ticker']=='CTLT']
'''

# python -m aiportfolio.backtest.preprocessing_수정중