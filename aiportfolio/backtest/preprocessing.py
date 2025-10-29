import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

from aiportfolio.util.data_cleanse.open_final_stock_daily import open_final_stock_daily

# python -m aiportfolio.backtest.preprocessing

# 일별 섹터별 수익률
def sector_daily_returns():
    df = open_final_stock_daily()

    df["DlyCalDt"] = pd.to_datetime(df["DlyCalDt"])
    df["_ret_x_cap"] = df["DlyRet"] * df["DlyCap"]
    group_keys = ["DlyCalDt", "gsector"]
    agg = (
        df.groupby(group_keys, dropna=False)
            .agg(sector_mktcap=("DlyCap", "sum"),
                ret_x_cap_sum=("_ret_x_cap", "sum"))
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

    return agg

# 일별 전체 수익률
def total_daily_returns():
    df = open_final_stock_daily()
    df["DlyCalDt"] = pd.to_datetime(df["DlyCalDt"])

    df["_ret_x_cap"] = df["DlyRet"] * df["DlyCap"]
    agg = df.groupby("DlyCalDt").agg(
        total_mktcap=("DlyCap", "sum"),
        total_ret_x_cap=("_ret_x_cap", "sum")
    ).reset_index()

    # 분모 0 방지
    agg["total_return"] = np.where(
        agg["total_mktcap"] != 0,
        agg["total_ret_x_cap"] / agg["total_mktcap"],
        np.nan
    )

    # 중간열 제거
    agg = agg.drop(columns=["total_ret_x_cap"])

    return agg

# 두개 뺀 값
def final_abnormal_returns():
    a = sector_daily_returns()
    b = total_daily_returns()
    merged_df = pd.merge(a, b, on='DlyCalDt', how='inner')

    merged_df['abnormal_return'] = merged_df['sector_return'] - merged_df['total_return']

    pivoted_df = merged_df.pivot(index='DlyCalDt', columns='gsector', values='abnormal_return')
    df_reset = pivoted_df.reset_index()

    return df_reset

# 테스트 1. (나스닥 NYSE 수익률 분포가 실제랑 비슷한지)
'''
# ---------- 1) N, Q 수익률 계산 ----------
df = open_final_stock_daily()
df["_ret_x_cap"] = df["DlyRet"] * df["DlyCap"]
group_keys = ["DlyCalDt", "PrimaryExch"]
agg_1 = (
    df.groupby(group_keys, dropna=False)
        .agg(exch_mktcap=("DlyCap", "sum"),
            ret_x_cap_sum=("_ret_x_cap", "sum"))
        .reset_index()
)

# 분모 0 방지
agg_1["exch_return"] = np.where(
    agg_1["exch_mktcap"] != 0,
    agg_1["ret_x_cap_sum"] / agg_1["exch_mktcap"],
    np.nan
)

# 중간열 제거
agg_1 = agg_1.drop(columns=["ret_x_cap_sum"])

# ---------- 중간 테스트용 시각화 ----------
# 1. 거래소 'N'과 'Q' 데이터 필터링
#    .copy()를 사용하여 SettingWithCopyWarning 방지
df_n = agg_1[agg_1['PrimaryExch'] == 'N'].sort_values(by='DlyCalDt').copy()
df_q = agg_1[agg_1['PrimaryExch'] == 'Q'].sort_values(by='DlyCalDt').copy()

# 2. 각 거래소별 누적 수익률 계산
#    (1 + 일별수익률)을 누적 곱한 후, 1을 빼준다.
df_n['cumulative_return'] = (1 + df_n['exch_return']).cumprod() - 1
df_q['cumulative_return'] = (1 + df_q['exch_return']).cumprod() - 1

# 3. 시각화 설정
plt.style.use('seaborn-v0_8-whitegrid')
plt.figure(figsize=(14, 7))

# 4. 누적 수익률을 라인 플롯으로 그리기
plt.plot(df_n['DlyCalDt'], df_n['cumulative_return'], label='Exchange N', color='royalblue')
plt.plot(df_q['DlyCalDt'], df_q['cumulative_return'], label='Exchange Q', color='orangered')

# 5. 그래프 제목 및 레이블, 범례 추가
plt.title('Cumulative Exchange Returns (N vs. Q)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Cumulative Return', fontsize=12)
plt.legend()

# Y축 서식을 퍼센트(%)로 변경
plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

# 기준선 (0%) 추가
plt.axhline(0, color='grey', linestyle='--', linewidth=0.8)

# 6. 그래프 출력
plt.show()
'''

# 테스트 2. (영업일 개수 확인)
'''
monthly_summary = b.groupby(pd.Grouper(key='DlyCalDt', freq='MS')).agg(
    business_day_count=('total_return', 'count')
).reset_index()

print(monthly_summary)
'''