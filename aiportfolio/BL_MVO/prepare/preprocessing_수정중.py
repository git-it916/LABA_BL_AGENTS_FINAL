import pandas as pd
import numpy as np

from aiportfolio.util.data_cleanse.open_DTB3 import open_rf_rate
from aiportfolio.util.data_cleanse.open_final_stock_months import open_final_stock_months

# python -m aiportfolio.BL_MVO.prepare.preprocessing_수정중

# ---------- 1) 월별 초과수익률 제작 ----------
# https://fred.stlouisfed.org/series/DTB3
# 3-Month Treasury Bill Secondary Market Rate, Discount Basis (DTB3) 사용
def preprocess_rf_rate():
    df_rf = open_rf_rate()

    # 컬럼명 변경
    df_rf.rename(columns={'observation_date': 'date', 'DTB3': 'rf_daily'}, inplace=True)

    # 날짜 형식 변환 및 날짜로 정렬
    df_rf['date'] = pd.to_datetime(df_rf['date'])
    df_rf = df_rf.sort_values('date').reset_index(drop=True)

    # 무위험 수익률 전처리
    df_rf['rf_daily'] = df_rf['rf_daily'].ffill() # 휴일 때문에 발생하는 결측치 바로 전날의 값으로 채움.
    df_rf['rf_daily'] = df_rf['rf_daily'] / 100  # % -> 소수점 변환
    df_rf['rf_daily'] = (1 + df_rf['rf_daily']) ** (1/252) - 1  # 연율 -> 일율 변환

    # 월별 무위험 수익률로 변환
    rf_monthly = (
    df_rf.assign(year_month=df_rf['date'].dt.to_period('M'))
    .groupby('year_month')['rf_daily']
    .apply(lambda x: (1 + x).prod() - 1)
    .reset_index(name='rf_monthly')
    )

    # date 컬럼을 각 연월의 말일로 변환
    rf_monthly['date'] = rf_monthly['year_month'].dt.to_timestamp('M')
    rf_monthly = rf_monthly[['date', 'rf_monthly']]
    
    return rf_monthly

# ---------- 2) 최종 데이터프레임 ----------
def final():
    df = open_final_stock_months()

    # date 컬럼 생성 (각 연월의 말일)
    df['date'] = pd.to_datetime(df['cyear'].astype(str) + '-' + df['cmonth'].astype(str)) + pd.offsets.MonthEnd(0)

    # 전 월의 sp500에 해당하는 불리언 컬럼 추가
    df = df.sort_values(['Ticker', 'date']).copy()
    df['sp500_lag1'] = df.groupby('Ticker')['sp500'].shift(1)

    df_sp = df[df['sp500_lag1']==1].copy()

    df_rf = preprocess_rf_rate()

    # 종목 데이터 기준으로 병합
    merged_df = pd.merge(df_sp, df_rf, on='date', how='left')

    # 월별 초과수익률 계산
    merged_df['excess_return'] = merged_df['MthRet'] - merged_df['rf_monthly']

    # 전 월의 시가총액을 매칭
    merged_df = merged_df.sort_values(['Ticker', 'date']).copy()
    merged_df['prev_MthCap'] = merged_df.groupby('Ticker')['MthCap'].shift(1)

    # 가중수익률 계산
    merged_df["_ret_x_cap_1"] = merged_df["excess_return"] * merged_df["prev_MthCap"] # excess_return
    merged_df["_ret_x_cap_2"] = merged_df["MthRet"] * merged_df["prev_MthCap"] # 그냥 수익률(BL 람다 계산용)

    group_keys = [merged_df['date'].dt.to_period('M'), 'gsector']
    agg = (
        merged_df.groupby(group_keys, dropna=False)
            .agg(sector_prevmktcap=("prev_MthCap", "sum"), # 시총가중치 계산용
                    sector_mktcap=("MthCap", "sum"),          # pi 계산용 
                ret_x_cap_1_sum=("_ret_x_cap_1", "sum"),   # excess_return
                ret_x_cap_2_sum=("_ret_x_cap_2", "sum"),   # 그냥 수익률
                n_stocks=("Ticker", "count"))
            .reset_index())

    mask = agg["sector_prevmktcap"] != 0
    agg["sector_excess_return"] = agg["ret_x_cap_1_sum"].div(agg["sector_prevmktcap"]).where(mask)
    agg["sector_return"]        = agg["ret_x_cap_2_sum"].div(agg["sector_prevmktcap"]).where(mask)

    # 중간열 제거
    agg = agg.drop(columns=["ret_x_cap_1_sum", "ret_x_cap_2_sum"])

    # date 컬럼 수정 (각 월의 말일 추가)
    agg['date'] = agg['date'].dt.to_timestamp('M')

    agg = agg.sort_values(['date', 'gsector']).reset_index(drop=True).copy()

    return agg

a = final()
print(a.head(20))
print(a.info())