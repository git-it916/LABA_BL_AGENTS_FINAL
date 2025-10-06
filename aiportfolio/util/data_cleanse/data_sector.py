import pandas as pd
from pathlib import Path
import sys
import re
import shutil

def split_data_by_sector():
    """
    월별 Parquet 파일을 읽어, 연도/월별 하위 폴더 구조로 나누고 
    그 안에 'GICS Sector'별 파일을 저장합니다.
    실행 전에 기존 sector 폴더는 삭제됩니다.
    """
    # 1. 입력 폴더와 최상위 출력 폴더 경로 설정
    input_dir = Path("database/monthly/")
    output_dir = Path("database/sector/")

    # 스크립트 실행 시 기존 sector 폴더를 모두 삭제
    if output_dir.exists():
        print(f"기존 '{output_dir}' 폴더의 모든 파일을 삭제합니다...")
        shutil.rmtree(output_dir)
    # 최상위 출력 폴더(sector)를 새로 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    monthly_files = list(input_dir.glob('*.parquet'))
    if not monthly_files:
        print(f"오류: '{input_dir}' 폴더에 처리할 Parquet 파일이 없습니다.")
        sys.exit(1)

    print(f"총 {len(monthly_files)}개의 월별 파일을 처리합니다...")

    # 2. 각 월별 파일을 순회하며 작업
    for file_path in monthly_files:
        print(f"\n처리 중인 파일: {file_path.name}")
        try:
            df = pd.read_parquet(file_path)
        except Exception as e:
            print(f"오류: {file_path.name} 파일을 읽는 중 문제가 발생했습니다: {e}")
            continue

        if 'GICS Sector' not in df.columns:
            print(f"경고: '{file_path.name}' 파일에 'GICS Sector' 컬럼이 없어 건너뜁니다.")
            continue
            
        # --- 핵심 로직 1: 파일명에서 연도와 월 추출 ---
        base_name = file_path.stem.replace('merged_final_', '') # 'YYYY-MM' 형식
        try:
            year, month = base_name.split('-')
        except ValueError:
            print(f"경고: '{file_path.name}' 파일명 형식이 'YYYY-MM'이 아니므로 건너뜁니다.")
            continue

        # 'GICS Sector'를 기준으로 데이터 그룹화
        grouped_by_sector = df.groupby('GICS Sector')

        # 3. 각 섹터별 그룹을 구조에 맞게 저장
        for sector_name, data_for_sector in grouped_by_sector:
            if data_for_sector.empty:
                continue

            # --- 핵심 로직 2: 연도/월별 하위 폴더 생성 및 파일 경로 설정 ---
            # 예: 'database/sector/2015/01/' 경로를 만듭니다.
            monthly_output_dir = output_dir / year / month
            monthly_output_dir.mkdir(parents=True, exist_ok=True)
            
            clean_sector_name = re.sub(r'[\\/*?:"<>|]', "", sector_name).replace(' ', '_')
            
            # 파일명은 이제 섹터 이름만 포함합니다 (예: Industrials.parquet)
            output_filename = f"{clean_sector_name}.parquet"
            output_path = monthly_output_dir / output_filename

            print(f"  -> 저장 중: {output_path}")
            data_for_sector.to_parquet(output_path, index=False)

    print("\n작업 완료! 모든 월별 데이터를 연/월/섹터별로 분할하여 다음 폴더에 저장했습니다:")
    print(f"'{output_dir.resolve()}'")


if __name__ == "__main__":
    split_data_by_sector()