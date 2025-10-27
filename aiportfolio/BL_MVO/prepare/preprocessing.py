import pandas as pd
import numpy as np

from aiportfolio.util.data_cleanse.open_filtered_sp500_data import open_filtered_sp500_data

# python -m aiportfolio.BL_MVO.prepare.preprocessing

# cap_weighted_return을 각 종목의 시가총액 가중 수익률이라고 가정
# total_mktcap: 각 섹터의 시가총액 합계라고 가정

# 컬럼명 변경(market_params에서 GICS Sector->gsector, ExcessReturn->cap_weighted_return)
# cyear, cmonth -> date
# gsector -> 각 숫자 섹터명으로 변환

df = open_filtered_sp500_data()

# 필요한 컬럼만 선택
df_filtered = df[['cyear', 'cmonth', 'gsector', 'total_mktcap', 'cap_weighted_return']].copy()

# 컬럼명 변환
df_filtered.rename(columns={'total_mktcap': 'mktcap', 'cap_weighted_return': 'sector_return'}, inplace=True)

# date 컬럼 생성 (각 연월의 말일)
df_filtered['date'] = pd.to_datetime(df_filtered['cyear'].astype(str) + '-' + df_filtered['cmonth'].astype(str)) + pd.offsets.MonthEnd(0)

# cyear, cmonth 컬럼을 제거하고 date 컬럼을 앞으로 이동
df_filtered = df_filtered[['gsector', 'mktcap', 'sector_return', 'date']].copy()
cols = ['date'] + [col for col in df_filtered.columns if col != 'date']
df_final = df_filtered[cols]

# print(df_final.head())
# print(df_final.info())

start_date = pd.to_datetime("2015-05-31")
end_date = pd.to_datetime("2024-04-30")

filtered_df = df_final[(df_final['date'] >= start_date) & (df_final['date'] <= end_date)].copy()
print(filtered_df.info())
# pivot_filtered_df = filtered_df.pivot_table(index='date', columns='gsector', values='cap_weighted_return')
sigma = filtered_df['sector_return'].to_frame().T.cov()
sector = sigma.columns.tolist()

print(sigma)
print(sector)