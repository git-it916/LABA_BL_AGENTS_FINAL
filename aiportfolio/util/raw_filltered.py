import os
import sys
import time
import re
import datetime as dt
from datetime import datetime  # daily_sp500.py에서 사용
from pathlib import Path
import pandas as pd
import numpy as np
import traceback

# 사용법 읽어보세요!! databse 폴더에 raw_data.csv 파일을 넣고
# 이 스크립트를 실행하면 전처리된 final_processed_stock_data.parquet 파일이 생성됩니다~
# 로컬에 저장할 필요없습니다.

# python -m aiportfolio.util.raw_filltered

# ##################################################################

def safe_to_csv(df, final_path: str, encoding='utf-8-sig', max_retries=5, wait=0.5):
    """
    OneDrive/Excel 잠금 회피용 안전 저장 함수
    """
    final_path = Path(final_path)
    tmp_path = final_path.with_suffix(final_path.suffix + ".tmp")
    df.to_csv(tmp_path, index=False, encoding=encoding)
    for attempt in range(1, max_retries + 1):
        try:
            os.replace(tmp_path, final_path)
            print(f"✓ CSV 저장 완료: {final_path}")
            return
        except PermissionError:
            if attempt == max_retries:
                raise
            time.sleep(wait)

# ##################################################################
# 파이프라인 1번 함수 (daily_NQ_data.py)
# - 수정: output_file 저장 대신 DataFrame을 반환(return)
# ##################################################################

def filter_by_exchange(input_file, column_name, keep_values, columns_to_delete=None):
    """
    CSV/Excel 파일에서 특정 열 값을 기준으로 필터링하고 불필요한 열을 삭제합니다.
    (daily_NQ_data.py의 메인 함수)
    
    수정:
    - 파일 저장 로직 제거
    - 필터링된 DataFrame (df_filtered) 반환
    """
    
    print("=" * 60)
    print("STEP 1: Exchange 필터링 (N/Q) 시작")
    print("=" * 60)
    
    # 1단계: 파일 읽기
    print(f"\n[1단계] 파일 읽는 중: {input_file}")
    if str(input_file).endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        df = pd.read_excel(input_file)
    initial_count = len(df)
    print(f"✓ 전체 행 개수: {initial_count:,}개")
    
    # 2단계: 열 확인
    print(f"\n[2단계] '{column_name}' 열 확인 중...")
    if column_name not in df.columns:
        print(f"✗ 오류: '{column_name}' 열을 찾을 수 없습니다."); return None
    print(f"✓ '{column_name}' 열 찾음")
    
    # 3단계: 필터링 적용
    print(f"\n[3단계] 필터링 적용 중... (유지할 값: {', '.join(keep_values)})")
    df_filtered = df[df[column_name].isin(keep_values)].copy() # .copy()로 사본 생성
    final_count = len(df_filtered)
    deleted_count = initial_count - final_count
    print(f"✓ 필터링 완료! (삭제된 행: {deleted_count:,}개, 남은 행: {final_count:,}개)")
    
    # 4단계: 불필요한 열 삭제
    if columns_to_delete:
        print(f"\n[4단계] 불필요한 열 삭제 중...")
        existing_cols_to_delete = [col for col in columns_to_delete if col in df_filtered.columns]
        if existing_cols_to_delete:
            df_filtered = df_filtered.drop(columns=existing_cols_to_delete)
            print(f"  삭제된 열: {', '.join(existing_cols_to_delete)}")
    
    # --- 시총 계산 로직 (별도 파일로 저장) ---
    if "DlyCap" in df_filtered.columns and "DlyCalDt" in df_filtered.columns:
        print(f"\n[별도 작업] 날짜별(N/Q) 시총 및 비율 계산 중...")
        df_filtered["DlyCalDt"] = pd.to_datetime(df_filtered["DlyCalDt"])
        pivot = (
            df_filtered
            .groupby(["DlyCalDt", column_name], as_index=False)["DlyCap"]
            .sum()
            .pivot(index="DlyCalDt", columns=column_name, values="DlyCap")
            .fillna(0.0)
        )
        pivot = pivot.rename(columns={"N": "mcap_N", "Q": "mcap_Q"})
        if "mcap_N" not in pivot.columns: pivot["mcap_N"] = 0.0
        if "mcap_Q" not in pivot.columns: pivot["mcap_Q"] = 0.0
        pivot["total_mcap"] = pivot["mcap_N"] + pivot["mcap_Q"]
        pivot["ratio_N"] = np.where(pivot["total_mcap"] > 0, pivot["mcap_N"] / pivot["total_mcap"], 0.0)
        pivot["ratio_Q"] = np.where(pivot["total_mcap"] > 0, pivot["mcap_Q"] / pivot["total_mcap"], 0.0)

        db_dir = Path.cwd() / "database"
        db_dir.mkdir(exist_ok=True)
        out_csv_path = db_dir / "mcap_by_exchange_daily.csv"
        pivot.reset_index().to_csv(out_csv_path, index=False, encoding="utf-8-sig")
        print(f"✓ 날짜별(N/Q) 시총 비율 파일 저장: {out_csv_path}")
    
    print(f"\n✅ STEP 1 완료 (filter_by_exchange)")
    
    # 5단계: 결과 DataFrame 반환
    return df_filtered


# ##################################################################
# 파이프라인 2번 함수 (daily_sp500.py)
# - 수정: filtered_file (경로) 대신 input_df (DataFrame)을 입력받음
# - 수정: output_file 저장 대신 DataFrame을 반환(return)
# ##################################################################

def match_sp500_by_date(input_df, sp500_file, 
                        ticker_column='Ticker', date_column='DlyCalDt'):
    """
    필터링된 DataFrame의 ticker와 날짜를 SP500 기간별 리스트와 매칭합니다.
    (daily_sp500.py의 메인 함수)
    
    수정:
    - input_df (DataFrame)을 입력 받음
    - 파일 저장 로직 제거
    - 'sp500' 열이 추가된 DataFrame 반환
    """
    
    print("=" * 70)
    print("STEP 2: SP500 기간별 매칭 시작")
    print("=" * 70)
    
    # 1단계: 입력 DataFrame 사용
    df_filtered = input_df.copy() # 원본 보존을 위해 사본 사용
    total_records = len(df_filtered)
    print(f"\n[1단계] 입력 DataFrame 사용 (전체 레코드 수: {total_records:,}개)")
    
    # 열 확인
    if ticker_column not in df_filtered.columns:
        print(f"\n✗ 오류: '{ticker_column}' 열을 찾을 수 없습니다."); return None
    if date_column not in df_filtered.columns:
        print(f"\n✗ 오류: '{date_column}' 열을 찾을 수 없습니다."); return None
    
    # 2단계: SP500 기간 파일 읽기
    print(f"\n[2단계] SP500 기간 파일 읽는 중: {sp500_file}")
    df_sp500 = pd.read_csv(sp500_file)
    print(f"✓ SP500 기간 레코드 수: {len(df_sp500):,}개")
    
    # 3단계: 날짜 변환
    print(f"\n[3단계] 날짜 형식 변환 중...")
    df_filtered[date_column] = pd.to_datetime(df_filtered[date_column])
    df_sp500['start_date'] = pd.to_datetime(df_sp500['start_date'])
    df_sp500['end_date'] = df_sp500['end_date'].fillna('2099-12-31')
    df_sp500['end_date'] = pd.to_datetime(df_sp500['end_date'])
    print(f"✓ 날짜 변환 완료")
    
    # Ticker 대문자 통일
    df_filtered['ticker_upper'] = df_filtered[ticker_column].astype(str).str.strip().str.upper()
    df_sp500['ticker_upper'] = df_sp500['Ticker'].astype(str).str.strip().str.upper()
    
    # 4단계: 매칭 수행
    print(f"\n[4단계] 기간별 매칭 진행 중... (시간이 걸릴 수 있습니다)")
    sp500_flags = []
    batch_size = 10000
    total_batches = (total_records + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, total_records)
        
        batch_flags = []
        for idx in range(start_idx, end_idx):
            row = df_filtered.iloc[idx]
            ticker = row['ticker_upper']
            date = row[date_column]
            sp500_periods = df_sp500[df_sp500['ticker_upper'] == ticker]
            is_in_sp500 = False
            for _, period in sp500_periods.iterrows():
                if period['start_date'] <= date <= period['end_date']:
                    is_in_sp500 = True
                    break
            batch_flags.append(1 if is_in_sp500 else 0)
        
        sp500_flags.extend(batch_flags)
        
        if (batch_num + 1) % 10 == 0 or batch_num == total_batches - 1:
            progress = ((batch_num + 1) / total_batches) * 100
            processed = min((batch_num + 1) * batch_size, total_records)
            print(f"  진행: {processed:,}/{total_records:,} ({progress:.1f}%)")
    
    df_filtered['sp500'] = sp500_flags
    df_filtered = df_filtered.drop(columns=['ticker_upper'])
    
    sp500_matched = df_filtered['sp500'].sum()
    match_rate = (sp500_matched / total_records * 100) if total_records > 0 else 0
    print(f"\n✓ 매칭 완료! (SP500 포함: {sp500_matched:,}개, {match_rate:.1f}%)")
    
    # 5단계: (저장 대신) DataFrame 반환
    print(f"\n✅ STEP 2 완료 (match_sp500_by_date)! 'sp500' 열이 추가되었습니다.")
    return df_filtered


# ##################################################################
# 파이프라인 3번 함수 (daily_GICS.py)
# - 수정: input_file (경로) 대신 input_df (DataFrame)을 입력받음
# - 수정: output_file 저장 대신 DataFrame을 반환(return)
# ##################################################################

def match_gics_sector(input_df, gics_file, ticker_column='Ticker'):
    """
    입력 DataFrame의 ticker와 GICS 파일의 gsector를 매칭합니다.
    (daily_GICS.py의 메인 함수)
    
    수정:
    - input_df (DataFrame)을 입력 받음
    - 중간/최종 파일 저장 로직 제거
    - 'gsector'가 추가/정리된 최종 DataFrame 반환
    """
    print("=" * 70)
    print("STEP 3: GICS Sector 매칭 시작")
    print("=" * 70)

    # 1단계: 입력 DataFrame 사용
    df_input = input_df.copy() # 원본 보존을 위해 사본 사용
    total_records = len(df_input)
    print(f"\n[1단계] 입력 DataFrame 사용 (전체 레코드 수: {total_records:,}개)")

    # Ticker 열 확인
    if ticker_column not in df_input.columns:
        print(f"\n✗ 오류: '{ticker_column}' 열을 찾을 수 없습니다."); return None
    
    # 2단계: GICS 파일 읽기
    print(f"\n[2단계] GICS 파일 읽는 중: {gics_file}")
    df_gics = pd.read_csv(gics_file)
    print(f"✓ GICS 레코드 수: {len(df_gics):,}개")

    # GICS 파일의 열 확인
    gics_ticker_col = None
    gics_sector_col = None
    for col in df_gics.columns:
        if col.lower() in ['ticker', 'symbol']: gics_ticker_col = col; break
    for col in df_gics.columns:
        if 'sector' in col.lower() or col.lower() == 'gsector': gics_sector_col = col; break
    if gics_ticker_col is None: print(f"\n✗ 오류: GICS 파일에서 ticker 열을 찾을 수 없습니다."); return None
    if gics_sector_col is None: print(f"\n✗ 오류: GICS 파일에서 sector 열을 찾을 수 없습니다."); return None
    print(f"\n✓ GICS Ticker 열: '{gics_ticker_col}', Sector 열: '{gics_sector_col}'")

    # 3단계: GICS 데이터 준비
    print(f"\n[3단계] GICS 매핑 딕셔너리 생성 중...")
    df_gics['ticker_upper'] = df_gics[gics_ticker_col].astype(str).str.strip().str.upper()
    gics_dict = df_gics.set_index('ticker_upper')[gics_sector_col].to_dict()
    print(f"✓ GICS 매핑 딕셔너리 생성 완료: {len(gics_dict):,}개")
    
    # 4단계: 매칭 수행
    print(f"\n[4단계] Sector 매칭 중...")
    df_input['ticker_upper'] = df_input[ticker_column].astype(str).str.strip().str.upper()
    df_input['gsector'] = df_input['ticker_upper'].map(gics_dict)
    df_input = df_input.drop(columns=['ticker_upper'])

    matched_count = df_input['gsector'].notna().sum()
    match_rate = (matched_count / total_records * 100) if total_records > 0 else 0
    print(f"✓ 매칭 완료! (매칭 성공: {matched_count:,}개, {match_rate:.1f}%)")

    # 5단계: SP500 체크(선택)
    if 'sp500' in df_input.columns:
        sp500_no_gics_count = len(df_input[(df_input['sp500'] == 1) & (df_input['gsector'].isna())])
        if sp500_no_gics_count > 0:
            print(f"  ⚠ SP500 종목 중 GICS가 없는 레코드: {sp500_no_gics_count}개")
        else:
            print(f"  ✓ SP500 종목은 모두 GICS가 매칭되었습니다!")
    
    # 6단계: 수동 보정 및 GICS 없는 행 삭제
    print(f"\n[6단계] 데이터 정리 (GOOG 보정, GICS 없는 행 삭제)")
    goog_mask = df_input[ticker_column].astype(str).str.upper() == 'GOOG'
    if goog_mask.sum() > 0:
        df_input.loc[goog_mask, 'gsector'] = 50.0
        print(f"  ✓ GOOG의 gsector를 50.0으로 설정")

    before_delete = len(df_input)
    df_input = df_input[df_input['gsector'].notna()]
    after_delete = len(df_input)
    deleted_count = before_delete - after_delete
    print(f"  ✓ GICS 없는 행 삭제 완료 (삭제된 행: {deleted_count:,}개)")

    # 7단계: (저장 대신) DataFrame 반환
    print(f"\n✅ STEP 3 완료 (match_gics_sector)!")
    print(f"  최종 레코드 수: {after_delete:,}개")
    
    return df_input

# ##################################################################
# 독립 함수 (open_DTB3.py)
# - (이 파이프라인과 별도로 RF 금리 로드 시 사용)
# ##################################################################

def open_rf_rate(file_path="database/DTB3.csv"):
    """
    무위험 이자율(DTB3.csv) 파일을 읽어 DataFrame으로 반환합니다.
    (open_DTB3.py의 메인 함수)
    """
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
        return None
    try:
        df = pd.read_csv(file_path)
        print(f"✓ 무위험 이자율 파일 로드 완료: {file_path}")
        return df
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

# ##################################################################
# 🚀 메인 파이프라인 실행
# ##################################################################

def main_pipeline():
    """
    데이터 전처리 전체 파이프라인을 순차적으로 실행합니다.
    Input: database/raw_data.csv
    Output: database/final_processed_stock_data.parquet
    """
    print("======= 🚀 RAW DATA FILTERING PIPELINE START 🚀 =======")
    
    # --- 1. 경로 설정 ---
    # (스크립트가 실행되는 위치를 기준으로 'database' 폴더 참조)
    try:
        DB_PATH = Path.cwd() / "database"
        DB_PATH.mkdir(exist_ok=True) # database 폴더가 없으면 생성
    except Exception as e:
        print(f"✗ 'database' 폴더 경로 설정 오류: {e}")
        return

    # --- 입력 파일 (사용자 요청) ---
    raw_data_file = DB_PATH / "raw_data.csv"
    
    # --- 참조(Lookup) 파일 ---
    # (이 파일들은 'database' 폴더에 미리 준비되어 있어야 합니다)
    sp500_list_file = DB_PATH / "sp500_ticker_start_end.csv"
    gics_list_file = DB_PATH / "ticker_GICS.csv"
    
    # --- 최종 출력 파일 (사용자 요청) ---
    final_output_parquet = DB_PATH / "final_processed_stock_data.parquet"

    # --- 파이프라인 1 매개변수 ---
    filter_column = "PrimaryExch"
    filter_keep_values = ['N', 'Q']
    filter_delete_columns = ['PERMNO', 'HdrCUSIP', 'PERMCO', 'vwretd']

    # --- 파이프라인 2/3 매개변수 ---
    ticker_column = "Ticker"
    date_column = "DlyCalDt"
    
    
    # --- 파일 존재 여부 확인 ---
    if not raw_data_file.exists():
        print(f"✗✗✗ 파이프라인 중단: 입력 파일 '{raw_data_file.name}'을 'database' 폴더에서 찾을 수 없습니다.")
        return
    if not sp500_list_file.exists():
        print(f"✗✗✗ 파이프라인 중단: 참조 파일 '{sp500_list_file.name}'을 'database' 폴더에서 찾을 수 없습니다.")
        return
    if not gics_list_file.exists():
        print(f"✗✗✗ 파이프라인 중단: 참조 파일 '{gics_list_file.name}'을 'database' 폴더에서 찾을 수 없습니다.")
        return

    try:
        # --- 🚀 [STEP 1: NQ 필터링] ---
        # Input: raw_data.csv
        # Output: df_step1 (DataFrame)
        df_step1 = filter_by_exchange(
            input_file=str(raw_data_file),
            column_name=filter_column,
            keep_values=filter_keep_values,
            columns_to_delete=filter_delete_columns
        )
        if df_step1 is None: raise Exception("STEP 1 (NQ 필터링) 실패")

        # --- 🚀 [STEP 2: SP500 기간 매칭] ---
        # Input: df_step1 (DataFrame)
        # Output: df_step2 (DataFrame)
        df_step2 = match_sp500_by_date(
            input_df=df_step1,
            sp500_file=str(sp500_list_file),
            ticker_column=ticker_column,
            date_column=date_column
        )
        if df_step2 is None: raise Exception("STEP 2 (SP500 매칭) 실패")

        # --- 🚀 [STEP 3: GICS Sector 매칭] ---
        # Input: df_step2 (DataFrame)
        # Output: df_step3 (DataFrame)
        df_step3 = match_gics_sector(
            input_df=df_step2,
            gics_file=str(gics_list_file),
            ticker_column=ticker_column
        )
        if df_step3 is None: raise Exception("STEP 3 (GICS 매칭) 실패")
        
        # --- 🚀 [STEP 4: 최종 Parquet 파일 저장] ---
        print("\n" + "="*70)
        print("🚀 STEP 4: 최종 Parquet 파일 저장")
        print("="*70)
        df_step3.to_parquet(final_output_parquet, index=False, engine='pyarrow')
        print(f"✓ 최종 Parquet 파일 저장 완료: {final_output_parquet}")
        
        print("\n" + "="*70)
        print("======= ✅ PIPELINE ALL COMPLETE ✅ =======")
        print(f"  최종 레코드 수: {len(df_step3):,}개")
        print(f"  최종 파일: {final_output_parquet.name}")
        print("="*70)

    except FileNotFoundError as e:
        print(f"\n✗✗✗ 파이프라인 중단: 파일을 찾을 수 없습니다.")
        print(f"  {e}")
    except PermissionError as e:
        print(f"\n✗✗✗ 파이프라인 중단: 권한(잠금) 오류입니다. 파일이 열려있는지/동기화 중인지 확인하세요.")
        print(f"  {e}")
    except Exception as e:
        print(f"\n✗✗✗ 파이프라인 중단: 오류 발생")
        print(f"  {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # 이 스크립트를 직접 실행하면 메인 파이프라인 가동
    main_pipeline()