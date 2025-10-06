import pandas as pd
from pathlib import Path
import sys

def combine_and_save_data():
    """
    database/monthly/ 폴더의 모든 월별 Parquet 파일을 읽어
    하나의 데이터프레임으로 합친 후, database/combine/ 폴더에 저장합니다.
    """
    # 1. 입력 폴더와 출력 경로 설정
    input_dir = Path("database/monthly/")
    output_dir = Path("database/combine/")
    output_file = output_dir / "all_data.parquet"

    # 출력 폴더가 없으면 자동으로 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    # 입력 폴더가 있는지 확인
    if not input_dir.is_dir():
        print(f"오류: 입력 폴더를 찾을 수 없습니다: {input_dir}")
        print("먼저 split_data_monthly.py 스크립트를 실행했는지 확인하세요.")
        sys.exit(1)

    # 2. 월별 Parquet 파일 목록을 시간순으로 정렬
    monthly_files = sorted(input_dir.glob('*.parquet'))
    
    if not monthly_files:
        print(f"오류: '{input_dir}' 폴더에 처리할 Parquet 파일이 없습니다.")
        sys.exit(1)

    print(f"총 {len(monthly_files)}개의 월별 파일을 하나로 합칩니다...")

    try:
        # 3. 모든 파일을 읽어 리스트에 담기
        df_list = [pd.read_parquet(file) for file in monthly_files]

        # 4. 리스트의 모든 데이터프레임을 하나로 합치기
        combined_df = pd.concat(df_list, ignore_index=True)

        print("\n데이터 통합 완료!")
        print("통합된 데이터프레임 정보:")
        combined_df.info()
        
        # 5. 합쳐진 데이터프레임을 Parquet 파일로 저장
        print(f"\n통합된 데이터프레임을 다음 경로에 저장합니다: {output_file}")
        combined_df.to_parquet(output_file, index=False)
        
        print("\n--- 작업 완료! ---")
        print(f"모든 데이터가 '{output_file.resolve()}' 파일에 성공적으로 저장되었습니다.")

    except Exception as e:
        print(f"데이터 처리 중 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    combine_and_save_data()