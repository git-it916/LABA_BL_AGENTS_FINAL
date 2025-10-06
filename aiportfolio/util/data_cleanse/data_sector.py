import pandas as pd
from pathlib import Path
import sys
import re

def split_data_by_sector():
    """
    Reads monthly Parquet files and splits them further by 'GICS Sector'.
    """
    # 1. 입력 폴더와 출력 폴더 경로 설정
    input_dir = Path("database/monthly/")
    output_dir = Path("database/sector/")

    # 출력 폴더가 없으면 자동으로 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    # 입력 폴더에 파일이 있는지 확인
    # .glob('*.parquet')를 사용해 모든 파케이 파일을 리스트로 만듭니다.
    monthly_files = list(input_dir.glob('*.parquet'))
    if not monthly_files:
        print(f"오류: '{input_dir}' 폴더에 처리할 Parquet 파일이 없습니다.")
        print("먼저 split_data_monthly.py 스크립트를 실행했는지 확인하세요.")
        sys.exit(1)

    print(f"총 {len(monthly_files)}개의 월별 파일을 처리합니다...")

    # 2. 각 월별 파일을 순회하며 작업
    for file_path in monthly_files:
        print(f"\n처리 중인 파일: {file_path.name}")
        try:
            df = pd.read_parquet(file_path)
        except Exception as e:
            print(f"오류: {file_path.name} 파일을 읽는 중 문제가 발생했습니다: {e}")
            continue # 다음 파일로 넘어감

        # 'GICS Sector' 컬럼 확인
        if 'GICS Sector' not in df.columns:
            print(f"경고: '{file_path.name}' 파일에 'GICS Sector' 컬럼이 없어 건너뜁니다.")
            continue

        # 3. 'GICS Sector'를 기준으로 데이터 그룹화
        grouped_by_sector = df.groupby('GICS Sector')

        # 4. 각 섹터별 그룹을 별도의 Parquet 파일로 저장
        for sector_name, data_for_sector in grouped_by_sector:
            if data_for_sector.empty:
                continue

            # 파일명으로 사용하기 어려운 특수문자 제거 및 공백을 '_'로 변경
            # re.sub(r'[\\/*?:"<>|]', "", sector_name) -> Windows 파일명 금지 문자 제거
            clean_sector_name = re.sub(r'[\\/*?:"<>|]', "", sector_name).replace(' ', '_')
            
            # 원본 파일명에서 'merged_final_YYYY-MM' 부분 추출
            base_name = file_path.stem.replace('merged_final_', '')
            
            output_filename = f"{base_name}_{clean_sector_name}.parquet"
            output_path = output_dir / output_filename

            print(f"  -> 저장 중: {output_path}")
            data_for_sector.to_parquet(output_path, index=False)

    print("\n작업 완료! 모든 월별 데이터를 섹터별로 분할하여 다음 폴더에 저장했습니다:")
    print(f"'{output_dir.resolve()}'")


if __name__ == "__main__":
    split_data_by_sector()