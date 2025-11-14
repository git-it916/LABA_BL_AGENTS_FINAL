import pandas as pd
import os
from pathlib import Path
import numpy as np

def filter_excel_with_progress(input_file, output_file, column_name, keep_values, columns_to_delete=None):
    """
    엑셀 파일에서 특정 열의 값을 기준으로 행을 필터링하고, 불필요한 열을 삭제합니다.
    
    Parameters:
    - input_file: 입력 엑셀 파일 경로
    - output_file: 출력 엑셀 파일 경로
    - column_name: 필터링할 열 이름 (예: 'PrimaryExchange')
    - keep_values: 남길 값들의 리스트 (예: ['N', 'Q'])
    - columns_to_delete: 삭제할 열 이름 리스트 (예: ['PERMNO', 'HdrCUSIP'])
    """
    
    print("=" * 60)
    print("엑셀 파일 필터링 시작")
    print("=" * 60)
    
    # 1단계: 파일 읽기
    print(f"\n[1단계] 파일 읽는 중: {input_file}")
    
    # 파일 확장자에 따라 읽기 방식 선택
    if input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        df = pd.read_excel(input_file)
    
    initial_count = len(df)
    print(f"✓ 전체 행 개수: {initial_count:,}개")
    
    # 2단계: 열 확인
    print(f"\n[2단계] '{column_name}' 열 확인 중...")
    if column_name not in df.columns:
        print(f"✗ 오류: '{column_name}' 열을 찾을 수 없습니다.")
        print(f"사용 가능한 열: {', '.join(df.columns)}")
        return
    print(f"✓ '{column_name}' 열 찾음")
    
    # 3단계: 현재 값 분포 확인
    print(f"\n[3단계] 현재 '{column_name}' 열의 값 분포:")
    value_counts = df[column_name].value_counts()
    for value, count in value_counts.items():
        keep_marker = "← 유지" if value in keep_values else "← 삭제"
        print(f"  {value}: {count:,}개 {keep_marker}")
    
    # 4단계: 필터링 적용
    print(f"\n[4단계] 필터링 적용 중...")
    print(f"  유지할 값: {', '.join(keep_values)}")
    
    # 필터링 전 각 값의 개수 확인
    delete_count = 0
    for value in df[column_name].unique():
        if value not in keep_values:
            count = len(df[df[column_name] == value])
            delete_count += count
            print(f"  - '{value}' 값을 가진 {count:,}개 행 삭제 예정...")
    
    # 실제 필터링
    df_filtered = df[df[column_name].isin(keep_values)]
    final_count = len(df_filtered)
    
    print(f"\n✓ 필터링 완료!")
    print(f"  삭제된 행: {delete_count:,}개")
    print(f"  남은 행: {final_count:,}개")
    print(f"  삭제율: {(delete_count/initial_count*100):.1f}%")
    
    # 4-1단계: 불필요한 열 삭제 (있는 경우)
    if columns_to_delete:
        print(f"\n[4-1단계] 불필요한 열 삭제 중...")
        existing_cols_to_delete = [col for col in columns_to_delete if col in df_filtered.columns]
        missing_cols = [col for col in columns_to_delete if col not in df_filtered.columns]
        
        if existing_cols_to_delete:
            original_col_count = len(df_filtered.columns)
            df_filtered = df_filtered.drop(columns=existing_cols_to_delete)
            final_col_count = len(df_filtered.columns)
            
            print(f"  삭제된 열: {', '.join(existing_cols_to_delete)}")
            print(f"  원본 열 개수: {original_col_count}개 → 최종 열 개수: {final_col_count}개")
        
        if missing_cols:
            print(f"  ⚠ 찾을 수 없는 열: {', '.join(missing_cols)}")
    
    if "DlyCap" in df_filtered.columns:
        n_sum = df_filtered.loc[df_filtered[column_name] == "N", "DlyCap"].sum()
        q_sum = df_filtered.loc[df_filtered[column_name] == "Q", "DlyCap"].sum()
        print(f"\n[요약] 시가총액 합계:")
        print(f"  N: {n_sum:,.0f}")
        print(f"  Q: {q_sum:,.0f}")
        print(f"  총합: {n_sum + q_sum:,.0f}")
    else:
        print("\n⚠ 'DlyCap' 열이 없어 시가총액 합계를 계산할 수 없습니다.")

    # 날짜 파싱 (이미 datetime이면 영향 없음)
    df_filtered = df_filtered.copy()
    df_filtered["DlyCalDt"] = pd.to_datetime(df_filtered["DlyCalDt"])

    # 날짜×거래소(N/Q)별 시총 합계 피벗
    pivot = (
        df_filtered
        .groupby(["DlyCalDt", column_name], as_index=False)["DlyCap"]
        .sum()
        .pivot(index="DlyCalDt", columns=column_name, values="DlyCap")
        .fillna(0.0)
    )

    # 컬럼명 정리 (없으면 0으로 자동 대체됨)
    pivot = pivot.rename(columns={"N": "mcap_N", "Q": "mcap_Q"})
    if "mcap_N" not in pivot.columns: pivot["mcap_N"] = 0.0
    if "mcap_Q" not in pivot.columns: pivot["mcap_Q"] = 0.0

    # 합/비율
    pivot["total_mcap"] = pivot["mcap_N"] + pivot["mcap_Q"]
    # 0 나누기 방지
    pivot["ratio_N"] = np.where(pivot["total_mcap"] > 0, pivot["mcap_N"] / pivot["total_mcap"], 0.0)
    pivot["ratio_Q"] = np.where(pivot["total_mcap"] > 0, pivot["mcap_Q"] / pivot["total_mcap"], 0.0)

    # 저장 경로: VS Code 현재 작업 디렉토리의 database 폴더
    db_dir = Path.cwd() / "database"
    db_dir.mkdir(exist_ok=True)
    out_csv_path = db_dir / "mcap_by_exchange_daily.csv"

    pivot.reset_index().to_csv(out_csv_path, index=False, encoding="utf-8-sig")
    print(f"\n✓ 날짜별(N/Q) 시총 및 비율 파일 저장: {out_csv_path}")

    # head(5) 미리보기
    print("\n[미리보기] mcap_by_exchange_daily.csv (상위 5행)")
    print(pivot.reset_index().head(5))


    # 5단계: 파일 저장
    print(f"\n[5단계] 결과 저장 중: {output_file}")
    
    # 파일 확장자에 따라 저장 방식 선택
    if output_file.endswith('.csv'):
        df_filtered.to_csv(output_file, index=False, encoding='utf-8-sig')
    else:
        df_filtered.to_excel(output_file, index=False)
    
    file_size = os.path.getsize(output_file) / 1024  # KB
    print(f"✓ 저장 완료! (파일 크기: {file_size:.1f} KB)")
    
    print("\n" + "=" * 60)
    print("작업 완료!")
    print("=" * 60)
    print(f"\n최종 결과:")
    print(f"  원본 행 개수: {initial_count:,}개")
    print(f"  최종 행 개수: {final_count:,}개")
    print(f"  '{keep_values[0]}'로 끝나는 행: {len(df_filtered[df_filtered[column_name] == keep_values[0]]):,}개")
    if len(keep_values) > 1:
        print(f"  '{keep_values[1]}'로 끝나는 행: {len(df_filtered[df_filtered[column_name] == keep_values[1]]):,}개")


# 사용 예시
if __name__ == "__main__":
    # 설정
    input_file = r"C:\Users\shins\OneDrive\문서\crsp_20240501_daily_11.14.csv"  # 전체 경로
    output_file = r"C:\Users\shins\OneDrive\문서\필터링결과_11.14.csv"          # 출력 파일 전체 경로
    column_name = "PrimaryExch"   # 필터링할 열 이름
    keep_values = ['N', 'Q']          # 남길 값들
    columns_to_delete = ['PERMNO', 'HdrCUSIP', 'PERMCO', 'vwretd']  # 삭제할 열들
    
    # 실행
    try:
        filter_excel_with_progress(input_file, output_file, column_name, keep_values, columns_to_delete)
    except FileNotFoundError:
        print(f"\n✗ 오류: '{input_file}' 파일을 찾을 수 없습니다.")
        print("파일명과 경로를 확인해주세요.")
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")