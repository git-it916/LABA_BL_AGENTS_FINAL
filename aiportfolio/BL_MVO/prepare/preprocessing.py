import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 확인할 Parquet 파일 경로
file_path = Path("database/combine/all_data.parquet")

# 파일이 존재하는지 확인
if not file_path.exists():
    print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
    print("먼저 combine_and_save.py 스크립트를 실행했는지 확인하세요.")
    sys.exit(1)

try:
    # 1. Parquet 파일을 pandas 데이터프레임으로 읽기
    print(f"'{file_path}' 파일을 읽는 중입니다...")
    df = pd.read_parquet(file_path)

    # 2. 데이터프레임의 상위 5개 행을 화면에 출력
    print("\n파일 내용 미리보기 (상위 5개 행):")
    print(df.head().to_string())

    # 3. 데이터프레임의 기본 정보 출력
    print("\n데이터프레임 정보:")
    df.info()

except Exception as e:
    print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    sys.exit(1)


def preprocessing(df):
    # 1. MKT(시가총액) 컬럼 추가
    df['MKT'] = df['PRC'] * df['SHROUT'] * 1_000_000

    # 2. 종가, 상장주식수, vwretd, sprtrn 컬럼 제거(데이터 바뀌면 제거해야됨)
    processed_df = df.drop(columns=['PRC', 'SHROUT', 'vwretd', 'sprtrn'], errors='ignore')

    # 3. 섹터별 시가총액 계산
    sector_market_cap = processed_df.groupby(['date', 'GICS Sector'])['MKT'].sum().reset_index()
    sector_market_cap.rename(columns={'MKT': 'MKT_SEC'}, inplace=True)
    processed_df = processed_df.merge(sector_market_cap, on=['date', 'GICS Sector'], how='left')

    # 4. 각 종목의 섹터 내 시가총액 비중 계산
    processed_df['w_MKT'] = processed_df['MKT'] / processed_df['MKT_SEC']
    processed_df['RET'] = pd.to_numeric(processed_df['RET'], errors='coerce')
    # 5. 시총가중 수익률 계산 (종목별 수익률 × 시총비중)
    processed_df['w_RET'] = processed_df['RET'] * processed_df['w_MKT']

    # 6. 섹터별로 가중 수익률 합계 계산 (= 섹터별 시총가중 수익률)
    df_sector = processed_df.groupby(['date', 'GICS Sector']).agg({
        'w_RET': 'sum',      # 섹터별 시총가중 수익률
        'MKT_SEC': 'first'   # 섹터 시가총액 (모든 행이 동일하므로 first 사용)
    }).reset_index()
    df_sector.rename(columns={'w_RET': 'RET_SEC'}, inplace=True)

    # ✅ CSV 저장 (최소 변경)
    output_dir = Path("database/processed_view/")
    output_file_csv = output_dir / "df_sector_full_view.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    df_sector.to_csv(output_file_csv, index=False, encoding="utf-8-sig")
    print(f"\nCSV 저장 완료: {output_file_csv}")

    return df_sector


# ✅ 함수 실제 실행 (최소 변경)
_ = preprocessing(df)
