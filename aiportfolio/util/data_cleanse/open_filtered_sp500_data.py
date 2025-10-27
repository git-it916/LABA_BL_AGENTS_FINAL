import pandas as pd
from pathlib import Path
import sys

# python -m aiportfolio.util.data_cleanse.open_parquet

def open_filtered_sp500_data():
    # 확인할 Parquet 파일 경로
    file_path = Path("database/filtered_sp500_data.parquet")

    # 파일이 존재하는지 확인
    if not file_path.exists():
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
        print("먼저 combine_and_save.py 스크립트를 실행했는지 확인하세요.")
        sys.exit(1)

    try:
        # 1. Parquet 파일을 pandas 데이터프레임으로 읽기
        print(f"'{file_path}' 파일을 읽는 중입니다...")
        df = pd.read_parquet(file_path)

        '''
        # 2. 데이터프레임의 상위 5개 행을 화면에 출력
        print("\n파일 내용 미리보기 (상위 5개 행):")
        print(df.head().to_string())

        # 3. 데이터프레임의 기본 정보 출력
        print("\n데이터프레임 정보:")
        df.info()

        # 4. describe() 메서드를 사용하여 통계 요약 정보 출력
        print("\n데이터프레임 통계 요약 정보:")
        print(df.describe(include='all').to_string())
        
        df_2024 = df[df['cyear'] == 2024]
        print("\n2024년 데이터프레임 정보:")
        df_2024
        df_2024.info()
        '''

    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        sys.exit(1)

    return df