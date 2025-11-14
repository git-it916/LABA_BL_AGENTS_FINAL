import os
import time
import pandas as pd
import numpy as np
from pathlib import Path
import re
import datetime as dt

# --- OneDrive/Excel 잠금 회피용 안전 저장 ---
def safe_to_csv(df, final_path: str, encoding='utf-8-sig', max_retries=5, wait=0.5):
    final_path = Path(final_path)
    tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
    # 임시 파일로 저장
    df.to_csv(tmp_path, index=False, encoding=encoding)
    # 원자적 교체 재시도
    for attempt in range(1, max_retries + 1):
        try:
            os.replace(tmp_path, final_path)
            print(f"✓ CSV 저장 완료: {final_path}")
            return
        except PermissionError:
            if attempt == max_retries:
                raise
            time.sleep(wait)

def match_gics_sector(input_file, gics_file, output_file, ticker_column='Ticker'):
    """
    입력 파일의 ticker와 GICS 파일의 gsector를 매칭합니다.
    """
    print("=" * 70)
    print("GICS Sector 매칭 시작")
    print("=" * 70)

    # 1단계: 입력 파일 읽기
    print(f"\n[1단계] 입력 파일 읽는 중: {input_file}")
    df_input = pd.read_csv(input_file)
    total_records = len(df_input)
    print(f"✓ 전체 레코드 수: {total_records:,}개")

    # Ticker 열 확인
    if ticker_column not in df_input.columns:
        print(f"\n✗ 오류: '{ticker_column}' 열을 찾을 수 없습니다.")
        print(f"사용 가능한 열: {', '.join(df_input.columns)}")
        return

    unique_tickers = df_input[ticker_column].nunique()
    print(f"✓ 고유 ticker 수: {unique_tickers:,}개")

    # 2단계: GICS 파일 읽기
    print(f"\n[2단계] GICS 파일 읽는 중: {gics_file}")
    df_gics = pd.read_csv(gics_file)
    gics_records = len(df_gics)
    print(f"✓ GICS 레코드 수: {gics_records:,}개")

    # GICS 파일의 열 확인
    print(f"\nGICS 파일의 열:")
    for col in df_gics.columns:
        print(f"  - {col}")

    # ticker와 gsector 열 찾기
    gics_ticker_col = None
    gics_sector_col = None

    for col in df_gics.columns:
        if col.lower() in ['ticker', 'symbol']:
            gics_ticker_col = col
            break

    for col in df_gics.columns:
        if 'sector' in col.lower() or col.lower() == 'gsector':
            gics_sector_col = col
            break

    if gics_ticker_col is None:
        print(f"\n✗ 오류: GICS 파일에서 ticker 열을 찾을 수 없습니다.")
        return

    if gics_sector_col is None:
        print(f"\n✗ 오류: GICS 파일에서 sector 열을 찾을 수 없습니다.")
        return

    print(f"\n✓ GICS Ticker 열: '{gics_ticker_col}'")
    print(f"✓ GICS Sector 열: '{gics_sector_col}'")

    # 3단계: GICS 데이터 준비
    print(f"\n[3단계] GICS 데이터 준비 중...")
    df_gics['ticker_upper'] = df_gics[gics_ticker_col].astype(str).str.strip().str.upper()
    gics_dict = df_gics.set_index('ticker_upper')[gics_sector_col].to_dict()
    print(f"✓ GICS 매핑 딕셔너리 생성 완료: {len(gics_dict):,}개")

    unique_sectors = df_gics[gics_sector_col].dropna().unique()
    print(f"✓ 고유 Sector 수: {len(unique_sectors)}개")
    print(f"\nSector 종류:")
    for sector in sorted(unique_sectors):
        sector_count = (df_gics[gics_sector_col] == sector).sum()
        print(f"  - {sector}: {sector_count}개")

    # 4단계: 매칭 수행
    print(f"\n[4단계] Sector 매칭 중...")
    df_input['ticker_upper'] = df_input[ticker_column].astype(str).str.strip().str.upper()
    df_input['gsector'] = df_input['ticker_upper'].map(gics_dict)
    df_input = df_input.drop(columns=['ticker_upper'])

    matched_count = df_input['gsector'].notna().sum()
    unmatched_count = df_input['gsector'].isna().sum()
    match_rate = (matched_count / total_records * 100) if total_records > 0 else 0

    print(f"\n✓ 매칭 완료!")
    print(f"  매칭 성공: {matched_count:,}개 ({match_rate:.1f}%)")
    print(f"  매칭 실패: {unmatched_count:,}개 ({100-match_rate:.1f}%)")

    if unmatched_count > 0:
        unmatched_tickers = df_input[df_input['gsector'].isna()][ticker_column].astype(str).unique()[:10]
        print(f"\n⚠ 매칭되지 않은 ticker 예시 (최대 10개):")
        for ticker in unmatched_tickers:
            print(f"  - {ticker}")

    # 5단계: 중간 결과 저장(안전 저장)
    print(f"\n[5단계] 결과 저장 중: {output_file}")
    safe_to_csv(df_input, output_file, encoding='utf-8-sig')
    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"✓ 저장 완료! (파일 크기: {file_size:.2f} MB)")

    # 6단계: 샘플
    print(f"\n[6단계] 결과 미리보기:")
    print("-" * 70)
    if matched_count > 0:
        print("\n✓ Sector별 샘플:")
        for sector in df_input['gsector'].dropna().unique()[:5]:
            sample = df_input[df_input['gsector'] == sector].iloc[0]
            print(f"  {str(sample[ticker_column]):6s} | gsector = {sector}")

    # 7단계: 통계
    print("\n" + "=" * 70)
    print("Sector별 통계")
    print("=" * 70)
    sector_stats = df_input['gsector'].value_counts()
    print(f"\nSector별 레코드 수:")
    for sector, count in sector_stats.items():
        percentage = (count / total_records * 100)
        sector_str = str(sector) if pd.notna(sector) else "N/A"
        print(f"  {sector_str:30s}: {count:7,}개 ({percentage:5.1f}%)")
    if unmatched_count > 0:
        percentage = (unmatched_count / total_records * 100)
        print(f"  {'(매칭 안됨)':30s}: {unmatched_count:7,}개 ({percentage:5.1f}%)")

    # 8단계: SP500 체크(선택)
    if 'sp500' in df_input.columns:
        print("\n" + "=" * 70)
        print("SP500 포함 여부 체크")
        print("=" * 70)
        sp500_no_gics = df_input[(df_input['sp500'] == 1) & (df_input['gsector'].isna())]
        sp500_no_gics_count = len(sp500_no_gics)
        if sp500_no_gics_count > 0:
            sp500_no_gics_tickers = sp500_no_gics[ticker_column].astype(str).unique()
            print(f"\n⚠ SP500에 포함되지만 GICS가 없는 종목: {len(sp500_no_gics_tickers)}개")
            print(f"   (총 {sp500_no_gics_count:,}개 레코드)")
            print(f"\nTicker 리스트:")
            for i, ticker in enumerate(sorted(sp500_no_gics_tickers), 1):
                ticker_records = len(sp500_no_gics[sp500_no_gics[ticker_column] == ticker])
                print(f"  {i:3d}. {ticker:6s} ({ticker_records:,}개 레코드)")
                if i >= 50:
                    remaining = len(sp500_no_gics_tickers) - 50
                    if remaining > 0:
                        print(f"  ... 외 {remaining}개 더")
                    break
        else:
            print(f"\n✓ SP500 종목은 모두 GICS가 매칭되었습니다!")
        sp500_total = (df_input['sp500'] == 1).sum()
        sp500_with_gics = ((df_input['sp500'] == 1) & (df_input['gsector'].notna())).sum()
        sp500_gics_rate = (sp500_with_gics / sp500_total * 100) if sp500_total > 0 else 0
        print(f"\nSP500 GICS 매칭률:")
        print(f"  SP500 총 레코드: {sp500_total:,}개")
        print(f"  GICS 매칭 완료: {sp500_with_gics:,}개 ({sp500_gics_rate:.1f}%)")
        print(f"  GICS 매칭 안됨: {sp500_no_gics_count:,}개 ({100-sp500_gics_rate:.1f}%)")

    # 9단계: 수동 보정 및 GICS 없는 행 삭제
    print("\n" + "=" * 70)
    print("데이터 정리")
    print("=" * 70)
    goog_mask = df_input[ticker_column].astype(str).str.upper() == 'GOOG'
    goog_count = goog_mask.sum()
    if goog_count > 0:
        df_input.loc[goog_mask, 'gsector'] = 50.0
        print(f"\n✓ GOOG의 gsector를 50.0으로 설정: {goog_count:,}개 레코드")

    before_delete = len(df_input)
    no_gics_count = df_input['gsector'].isna().sum()
    df_input = df_input[df_input['gsector'].notna()]
    after_delete = len(df_input)
    deleted_count = before_delete - after_delete

    print(f"\n✓ GICS 없는 행 삭제:")
    print(f"  삭제 전: {before_delete:,}개")
    print(f"  삭제 후: {after_delete:,}개")
    print(f"  삭제됨: {deleted_count:,}개 ({deleted_count/before_delete*100:.1f}%)")

    # 10단계: 최종 결과 저장(안전 저장)
    print(f"\n[10단계] 최종 결과 저장 중: {output_file}")
    safe_to_csv(df_input, output_file, encoding='utf-8-sig')
    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"✓ 최종 저장 완료! (파일 크기: {file_size:.2f} MB)")

    # 최종 통계
    print("\n" + "=" * 70)
    print("최종 통계")
    print("=" * 70)
    final_sector_stats = df_input['gsector'].value_counts()
    print(f"\n최종 Sector별 레코드 수:")
    for sector, count in final_sector_stats.items():
        percentage = (count / after_delete * 100)
        sector_str = str(sector) if pd.notna(sector) else "N/A"
        print(f"  {sector_str:30s}: {count:7,}개 ({percentage:5.1f}%)")

    print(f"\n✅ 작업 완료!")
    print(f"  최종 레코드 수: {after_delete:,}개")
    print(f"  모든 레코드에 gsector가 할당되었습니다.")

    return df_input  # ← 반환하여 메인에서 활용

# 사용 예시
if __name__ == "__main__":
    input_file  = r"C:\Users\shins\OneDrive\문서\SP500매칭결과_11.14.csv"
    gics_file   = r"C:\Users\shins\OneDrive\문서\ticker_GICS.csv"
    output_file = r"C:\Users\shins\OneDrive\문서\최종결과_11.14.csv"
    ticker_column = "Ticker"

    try:
        # 함수 실행 → 최종 DataFrame 반환
        df_final = match_gics_sector(input_file, gics_file, output_file, ticker_column)

        # Parquet 저장
        parquet_dir = Path(output_file).parent / "database"
        parquet_dir.mkdir(exist_ok=True)
        parquet_path = parquet_dir / f"final_stock_daily_11.14.parquet"
        # pyarrow 또는 fastparquet 필요 (권장: pyarrow)
        df_final.to_parquet(parquet_path, index=False)
        print(f"✓ Parquet 파일 저장 완료: {parquet_path}")

    except FileNotFoundError as e:
        print(f"\n✗ 파일을 찾을 수 없습니다.\n  {e}")
    except PermissionError as e:
        print(f"\n✗ 권한(잠금) 오류입니다. 파일이 열려있는지/동기화 중인지 확인하세요.\n  {e}")
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback; traceback.print_exc()
''''''