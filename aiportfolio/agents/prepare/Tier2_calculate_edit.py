import pandas as pd
import os

# ==========================================================
# 1) S&P500 플래그 추가 (Ticker + 날짜 범위)
# ==========================================================
def add_sp500_flag(compustat_df: pd.DataFrame, base_path: str) -> pd.DataFrame:
    """
    compustat_df : 최소 ['Ticker', 'public_date'] 포함
    sp500_ticker_start_end.csv : ['Ticker', 'start_date', 'end_date']

    return : compustat_df + sp500 (1 or 0)
    """

    sp500_path = os.path.join(base_path, "sp500_ticker_start_end.csv")
    sp500_df = pd.read_csv(sp500_path)

    # 날짜 변환
    sp500_df["start_date"] = pd.to_datetime(sp500_df["start_date"])
    sp500_df["end_date"]   = pd.to_datetime(sp500_df["end_date"])

    # 문자열 통일 (대문자)
    compustat_df["Ticker"] = compustat_df["Ticker"].astype(str).str.upper()
    sp500_df["Ticker"]     = sp500_df["Ticker"].astype(str).str.upper()

    # merge : Ticker 기준
    merged = compustat_df.merge(
        sp500_df,
        on="Ticker",
        how="left"
    )

    # 공시일 기준으로 S&P500 편입 여부 플래그
    merged["public_date"] = pd.to_datetime(merged["public_date"])

    merged["sp500"] = (
        (merged["public_date"] >= merged["start_date"]) &
        (merged["public_date"] <= merged["end_date"])
    ).astype(int)

    # 불필요한 컬럼 제거
    merged = merged.drop(columns=["start_date", "end_date"])

    # 로깅
    print(f"[INFO] S&P500 플래그 추가 완료. 전체 관측치 수: {len(merged):,}")
    print(f"[INFO] S&P500 편입 관측치 수: {merged['sp500'].sum():,}")
    print(f"[INFO] S&P500 편입 고유 ticker 수: {merged.loc[merged['sp500'] == 1, 'Ticker'].nunique():,}")

    return merged


# ==========================================================
# 2) GICS 섹터 매핑 (Ticker 기준 최신 datadate 1개)
# ==========================================================
def add_gics_sector_for_sp500(df: pd.DataFrame, base_path: str):
    """
    df : 최소 ['Ticker', 'public_date', 'sp500'] 포함
    ticker_GICS.csv : ['Ticker', 'datadate', 'gsector']

    반환:
      df_with_gics : 전체 DF + gsector
      unmatched_df : sp500 == 1인데 gsector가 없는 관측치 (디버깅용, 저장은 안 함)
    """

    print(f"[INFO] 전체 관측치 수: {len(df):,}")
    print(f"[INFO] 전체 고유 ticker 수: {df['Ticker'].nunique():,}")

    # --- GICS 파일 로드 ---
    gics_path = os.path.join(base_path, "ticker_GICS.csv")
    gics = pd.read_csv(gics_path)

    gics["Ticker"]   = gics["Ticker"].astype(str).str.upper()
    gics["datadate"] = pd.to_datetime(gics["datadate"])

    # GICS 파일 자체에 몇 개 섹터가 있는지 먼저 확인
    print(f"[DEBUG] GICS 파일 내 고유 섹터 수 (전체): {gics['gsector'].nunique()}")
    print(f"[DEBUG] GICS 파일 섹터 분포:\n{gics['gsector'].value_counts().sort_index()}")

    # 각 Ticker별로 가장 최근 datadate 1개만 남기기
    gics_sorted = gics.sort_values(["Ticker", "datadate"])
    gics_latest = gics_sorted.groupby("Ticker").tail(1).copy()

    print(f"[INFO] GICS 매핑용 Ticker 수: {gics_latest['Ticker'].nunique():,}")
    print(f"[INFO] GICS 매핑용 고유 섹터 수: {gics_latest['gsector'].nunique()}")
    print(f"[DEBUG] GICS 최신 기준 섹터 분포:\n{gics_latest['gsector'].value_counts().sort_index()}")

    # --- Compustat 쪽도 Ticker 정규화 ---
    df = df.copy()
    df["Ticker"]      = df["Ticker"].astype(str).str.upper()
    df["public_date"] = pd.to_datetime(df["public_date"])

    # --- 단순 merge: Ticker 기준으로 gsector 붙이기 ---
    df_merged = df.merge(
        gics_latest[["Ticker", "gsector"]],
        on="Ticker",
        how="left"
    )

    print(f"[INFO] GICS 매핑 후 전체 고유 섹터 수 (NaN 포함): {df_merged['gsector'].nunique(dropna=True)}")

    # --- S&P500 구간에서 매핑 성공/실패 집계 ---
    sp500_mask = df_merged["sp500"] == 1
    sp500_df   = df_merged[sp500_mask].copy()

    total_sp500_rows   = len(sp500_df)
    matched_sp500_rows = sp500_df["gsector"].notna().sum()
    unmatched_sp500    = sp500_df[sp500_df["gsector"].isna()].copy()

    print(f"[INFO] S&P500 관측치 수: {total_sp500_rows:,}")
    if total_sp500_rows > 0:
        print(f"[INFO] S&P500 + gsector 매핑 성공: {matched_sp500_rows:,} "
              f"({matched_sp500_rows / total_sp500_rows:.2%})")
    else:
        print(f"[INFO] S&P500 데이터가 없습니다.")

    print(f"[INFO] S&P500 + gsector 매핑 실패: {len(unmatched_sp500):,}")
    print(f"[INFO] S&P500 내 고유 섹터 수 (매핑된 것 기준): {sp500_df['gsector'].nunique(dropna=True)}")
    print(f"[DEBUG] S&P500 내 섹터 분포:\n{sp500_df['gsector'].value_counts(dropna=True).sort_index()}")

    return df_merged, unmatched_sp500


# ==========================================================
# 3) 섹터 × 연 × 월별 평균 계산
# ==========================================================
def calculate_sector_monthly_average(df: pd.DataFrame, metric_cols=None) -> pd.DataFrame:
    """
    df : ['Ticker', 'public_date', 'sp500', 'gsector', ...지표들...]
    metric_cols : 평균 낼 지표 컬럼 리스트 (None이면 숫자형에서 자동 선택)

    반환:
      gsector × year × month 별 평균 지표 DF
    """

    df = df.copy()

    # S&P500 + gsector 있는 데이터만 사용
    filtered = df[(df["sp500"] == 1) & (df["gsector"].notna())].copy()
    print(f"[INFO] 섹터 평균 계산 대상 관측치 수: {len(filtered):,}")
    print(f"[INFO] 섹터 평균 계산 대상 고유 ticker 수: {filtered['Ticker'].nunique():,}")
    print(f"[INFO] 섹터 평균 계산 대상 고유 섹터 수: {filtered['gsector'].nunique()}")

    if filtered.empty:
        print("[WARN] 조건에 맞는 데이터가 없습니다. 빈 DF 반환.")
        return pd.DataFrame()

    filtered["public_date"] = pd.to_datetime(filtered["public_date"])
    filtered["year"]  = filtered["public_date"].dt.year
    filtered["month"] = filtered["public_date"].dt.month

    # metric_cols가 지정되지 않으면 숫자형 컬럼에서 자동 선택
    if metric_cols is None:
        metric_cols = filtered.select_dtypes(include=["float32", "float64", "int32", "int64"]).columns.tolist()
        metric_cols = [c for c in metric_cols if c not in ["sp500", "year", "month"]]

    print(f"[INFO] 평균 계산 대상 지표 컬럼: {metric_cols}")

    grouped = (
        filtered
        .groupby(["gsector", "year", "month"])[metric_cols]
        .mean()
        .reset_index()
        .sort_values(["gsector", "year", "month"])
    )

    print(f"[INFO] 섹터×연×월 조합 개수: {len(grouped):,}")
    print(f"[INFO] 최종 결과 내 고유 섹터 수: {grouped['gsector'].nunique()}")

    return grouped


# ==========================================================
# MAIN 실행부
# ==========================================================
if __name__ == "__main__":

    # Compustat 파일 경로 (OneDrive)
    base_path_compustat = r"C:\Users\shins\OneDrive\문서"

    # 레포지토리 내 database 경로
    base_path_repo = r"C:\Users\shins\OneDrive\LABA_BL_AGENTS_F\LABA_BL_AGENTS_FINAL\database"

    # ----------------------------------------------
    # 1) Compustat 로드
    # ----------------------------------------------
    comp_path = os.path.join(base_path_compustat, "compustat_2021.01_2024.12_company.csv")
    compustat_df = pd.read_csv(comp_path)
    compustat_df["public_date"] = pd.to_datetime(compustat_df["public_date"])

    if "Ticker" not in compustat_df.columns:
        raise ValueError("Compustat 파일에 'Ticker' 컬럼이 없습니다. 모든 파일에서 컬럼명을 'Ticker'로 통일하세요.")

    print(f"[INFO] Compustat 로드 완료. 관측치 수: {len(compustat_df):,}, "
          f"고유 ticker 수: {compustat_df['Ticker'].nunique():,}")

    # ----------------------------------------------
    # 2) S&P500 플래그 추가
    # ----------------------------------------------
    compustat_df = add_sp500_flag(compustat_df, base_path_repo)

    # ----------------------------------------------
    # 3) GICS 섹터 매핑
    # ----------------------------------------------
    df_with_gics, unmatched = add_gics_sector_for_sp500(compustat_df, base_path_repo)

    # ❌ 네 요구대로: 매칭 안 되는 데이터는 따로 파일로 저장하지 않음
    # (필요하면 나중에 unmatched를 수동으로 확인)

    # ----------------------------------------------
    # 4) 섹터 × 연 × 월 평균 계산
    # ----------------------------------------------
    metric_cols = ["bm", "npm", "roe", "roa", "CAPEI", "GProf", "totdebt_invcap"]  # 실제 컬럼명에 맞게 조정
    sector_month_avg = calculate_sector_monthly_average(df_with_gics, metric_cols)

    print("\n[RESULT] 섹터 × 연 × 월 평균 (상위 10행):")
    print(sector_month_avg.head(10))

    # ----------------------------------------------
    # 5) 최종 결과 CSV로 저장 (database 폴더)
    # ----------------------------------------------
    output_path = os.path.join(base_path_repo, "sector_monthly_average.csv")
    sector_month_avg.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"\n[SAVED] 섹터 × 연 × 월 평균 결과 저장 완료 → {output_path}")
