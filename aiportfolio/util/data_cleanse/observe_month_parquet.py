import pandas as pd
from pathlib import Path
import argparse

def inspect_parquet_folder(folder_path_str: str, num_rows: int):
    """
    지정된 폴더 안의 모든 Parquet 파일들을 하나로 합쳐서
    상위 N개 행을 화면에 출력합니다.

    Args:
        folder_path_str (str): 확인할 폴더의 경로.
        num_rows (int): 출력할 행의 개수.
    """
    folder_path = Path(folder_path_str)

    # 1. 폴더가 존재하는지 확인
    if not folder_path.is_dir():
        print(f"오류: 폴더를 찾을 수 없습니다: {folder_path}")
        return

    # 2. 폴더 내의 모든 .parquet 파일 목록을 가져옴
    parquet_files = list(folder_path.glob('*.parquet'))
    
    if not parquet_files:
        print(f"오류: '{folder_path}' 폴더에 Parquet 파일이 없습니다.")
        return

    try:
        print(f"폴더 미리보기: {folder_path}")
        print(f"{len(parquet_files)}개의 Parquet 파일을 하나로 합칩니다...")

        # 3. 모든 Parquet 파일을 읽어 하나의 데이터프레임으로 합치기
        df_list = [pd.read_parquet(file) for file in parquet_files]
        combined_df = pd.concat(df_list, ignore_index=True)

        print(f"\n상위 {num_rows}개 행을 표시합니다:")
        # to_string()을 사용하면 모든 열이 잘리지 않고 깔끔하게 출력됩니다.
        print(combined_df.head(num_rows).to_string())

    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="폴더 내의 모든 Parquet 파일을 합쳐 상위 몇 개 행을 보여줍니다.")
    
    # --dir 옵션: 확인할 폴더 경로를 지정 (기본값 변경)
    parser.add_argument(
        "--dir",
        default="database/sector/2024/02/",
        help="확인할 Parquet 파일들이 있는 폴더의 경로입니다."
    )
    
    parser.add_argument(
        "--rows",
        type=int,
        default=510,
        help="표시할 행의 개수입니다."
    )

    args = parser.parse_args()
    
    inspect_parquet_folder(args.dir, args.rows)