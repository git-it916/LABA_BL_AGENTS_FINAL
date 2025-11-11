import pandas as pd
import numpy as np

from aiportfolio.util.data_load.open_final_stock_months import open_final_stock_months

def final():
    df = open_final_stock_months()
    # ---------- 1) S&P500 == 1 필터 ----------
    # 여기부터 결측치 없음
    df_sp = df[df["sp500"] == 1].copy()

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
    
    return df_final