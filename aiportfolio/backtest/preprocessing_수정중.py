import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from aiportfolio.util.data_cleanse.open_DTB3 import open_rf_rate
from aiportfolio.util.data_cleanse.open_final_stock_daily import open_final_stock_daily

# python -m aiportfolio.backtest.preprocessing_수정중

# ---------- 1) 월별 초과수익률 제작 ----------
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

# ---------- 3) 일별 S&P 500의 섹터별 초과수익률 제작 ----------
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

    tickers_with_na = filtered_df.loc[filtered_df['DlyRet'].isnull(), 'Ticker'].unique()
    print(tickers_with_na)

    na_counts = (
        filtered_df[filtered_df['Ticker'].isin(tickers_with_na) & filtered_df['DlyRet'].isnull()]
        .groupby('Ticker')['DlyRet']
        .size()
        .sort_values(ascending=False)
    )

    print(na_counts.sort_values(ascending=False).head(20))
    '''
    추가적인 후처리 필요
    '''
# python -m aiportfolio.backtest.preprocessing_수정중

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


a = total_daily_returns()
# print(a.head(20))
# print(a.tail(20))
# print(a.info())