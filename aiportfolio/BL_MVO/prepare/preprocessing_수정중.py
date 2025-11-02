import pandas as pd
import numpy as np

from aiportfolio.util.data_cleanse.open_final_stock_months import open_final_stock_months
from aiportfolio.util.data_cleanse.open_DTB3 import open_rf_rate

# python -m aiportfolio.BL_MVO.prepare.preprocessing_수정중

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
    df_rf['rf_daily'] = df_rf['rf_daily'] / 252  # 연율 -> 일율 변환

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

# def final():
df = open_final_stock_months()
# S&P500 == 1 필터링
# 여기부터 결측치 없음
df_sp = df[df["sp500"] == 1].copy()

# date 컬럼 생성 (각 연월의 말일)
df_sp['date'] = pd.to_datetime(df_sp['cyear'].astype(str) + '-' + df_sp['cmonth'].astype(str)) + pd.offsets.MonthEnd(0)

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
        .agg(sector_prevmktcap=("prev_MthCap", "sum"),
            ret_x_cap_1_sum=("_ret_x_cap_1", "sum"),
            ret_x_cap_2_sum=("_ret_x_cap_2", "sum"),
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

print(agg.head(20))
print(agg.info())

'''
# ---------- 2) 가중수익률 계산 ----------
df_sp["_ret_x_cap"] = df_sp["MthRet"] * df_sp["MthCap"]

group_keys = ["cyear", "cmonth", "gsector"]
agg = (
    df_sp.groupby(group_keys, dropna=False)
        .agg(sector_mktcap=("MthCap", "sum"),
            ret_x_cap_sum=("_ret_x_cap", "sum"),
            n_stocks=("Ticker", "count"))
        .reset_index()
)

# 분모 0 방지
agg["sector_return"] = np.where(
    agg["sector_mktcap"] != 0,
    agg["ret_x_cap_sum"] / agg["sector_mktcap"],
    np.nan
)

# 중간열 제거
agg = agg.drop(columns=["ret_x_cap_sum"])

# 보기 좋게 정렬
df_agg = agg.sort_values(group_keys).reset_index(drop=True)

# ---------- 3) 컬럼 정리 ----------
# 필요한 컬럼만 선택
df_filtered = df_agg[['cyear', 'cmonth', 'gsector', 'sector_mktcap', 'sector_return']].copy()

# date 컬럼 생성 (각 연월의 말일)
df_filtered['date'] = pd.to_datetime(df_filtered['cyear'].astype(str) + '-' + df_filtered['cmonth'].astype(str)) + pd.offsets.MonthEnd(0)

# cyear, cmonth 컬럼을 제거하고 date 컬럼을 앞으로 이동
df_filtered = df_filtered[['gsector', 'sector_mktcap', 'sector_return', 'date']].copy()
cols = ['date'] + [col for col in df_filtered.columns if col != 'date']
df_final = df_filtered[cols]
'''
    # return df_final