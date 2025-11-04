import pandas as pd
import os
from pathlib import Path
import numpy as np    

def summarize_mcap_by_exchange(df_filtered, column_name):
    if "MthCap" in df_filtered.columns:
        n_sum = df_filtered.loc[df_filtered[column_name] == "N", "MthCap"].sum()
        q_sum = df_filtered.loc[df_filtered[column_name] == "Q", "MthCap"].sum()
        print(f"\n[요약] 시가총액 합계:")
        print(f"  N: {n_sum:,.0f}")
        print(f"  Q: {q_sum:,.0f}")
        print(f"  총합: {n_sum + q_sum:,.0f}")
    else:
        print("\n⚠ 'MthCap' 열이 없어 시가총액 합계를 계산할 수 없습니다.")

    # 날짜 파싱 (이미 datetime이면 영향 없음)
    df_filtered = df_filtered.copy()
    df_filtered["cyear"] = pd.to_datetime(df_filtered["cyear"])

    # 날짜×거래소(N/Q)별 시총 합계 피벗
    pivot = (
        df_filtered
        .groupby(["cyear", column_name], as_index=False)["MthCap"]
        .sum()
        .pivot(index="cyear", columns=column_name, values="MthCap")
        .fillna(0.0)
    )

    # 컬럼명 정리 (없으면 0으로 자동 대체됨)
    pivot = pivot.rename(columns={"N": "mcap_N", "Q": "mcap_Q"})
    if "mcap_N" not in pivot.columns: pivot["mcap_N"] = 0.0
    if "mcap_Q" not in pivot.columns: pivot["mcap_Q"] = 0.0

    # 합/비율
    pivot["total_mcap"] = pivot["mcap_N"] + pivot["mcap_Q"]
    pivot["ratio_N"] = np.where(pivot["total_mcap"] > 0, pivot["mcap_N"] / pivot["total_mcap"], 0.0)
    pivot["ratio_Q"] = np.where(pivot["total_mcap"] > 0, pivot["mcap_Q"] / pivot["total_mcap"], 0.0)

    # 저장 경로: VS Code 현재 작업 디렉토리의 database 폴더
    db_dir = Path.cwd() / "database"
    db_dir.mkdir(exist_ok=True)
    out_csv_path = db_dir / "mcap_by_exchange_month.csv"

    pivot.reset_index().to_csv(out_csv_path, index=False, encoding="utf-8-sig")
    print(f"\n✓ 날짜별(N/Q) 시총 및 비율 파일 저장: {out_csv_path}")

    # head(5) 미리보기
    print("\n[미리보기] mcap_by_exchange_month.csv (상위 5행)")
    print(pivot.reset_index().head(5))


# -------------------------------
# ✅ 실행 구간: CSV 파일 불러오기
# -------------------------------
if __name__ == "__main__":
    # 파일 경로 설정
    input_file = Path(r"C:\Users\shins\OneDrive\문서\final_stock_months.csv")

    # 파일 존재 여부 확인
    if not input_file.exists():
        print(f"✗ 오류: {input_file} 파일을 찾을 수 없습니다.")
    else:
        print(f"✓ 파일 로드 중: {input_file}")
        df = pd.read_csv(input_file)
        print(f"✓ 데이터 로드 완료! (행 {len(df):,}개, 열 {len(df.columns)}개)")

        # 함수 실행
        summarize_mcap_by_exchange(df, column_name="PrimaryExch")
