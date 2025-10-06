import pandas as pd
from pathlib import Path
import argparse # 명령줄 인자를 처리하기 위한 표준 라이브러리

def inspect_parquet_file(file_path_str: str, num_rows: int):
    """
    지정된 Parquet 파일의 상위 N개 행을 읽어 화면에 출력합니다.

    Args:
        file_path_str (str): 확인할 Parquet 파일의 경로.
        num_rows (int): 출력할 행의 개수.
    """
    file_path = Path(file_path_str)

    # 1. 파일이 존재하는지 확인
    if not file_path.exists():
        print(f"오류: 파일을 찾을 수 없습니다: {file_path}")
        return

    try:
        # 2. Parquet 파일 읽기 및 상위 N개 행 출력
        print(f"파일 미리보기: {file_path}")
        df = pd.read_parquet(file_path)

        print(f"상위 {num_rows}개 행을 표시합니다:")
        
        # to_string()을 사용하면 모든 열이 잘리지 않고 깔끔하게 출력됩니다.
        print(df.head(num_rows).to_string())

    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")

# 이 스크립트가 직접 실행될 때만 아래 코드가 동작합니다.
if __name__ == "__main__":
    # 3. 사용자가 터미널에서 옵션을 지정할 수 있도록 설정
    parser = argparse.ArgumentParser(description="Parquet 파일의 상위 몇 개 행을 보여줍니다.")
    
    # --path 옵션: 확인할 파일 경로를 지정 (기본값 설정)
    parser.add_argument(
        "--path",
        default="database/sector/2016/02/Consumer_Discretionary.parquet",
        help="확인할 Parquet 파일의 경로입니다."
    )
    
    # --rows 옵션: 확인할 행의 개수를 지정 (기본값 5)
    parser.add_argument(
        "--rows",
        type=int,
        default=5,
        help="표시할 행의 개수입니다."
    )

    args = parser.parse_args()
    
    # 사용자가 입력한 옵션을 바탕으로 함수 실행
    inspect_parquet_file(args.path, args.rows)