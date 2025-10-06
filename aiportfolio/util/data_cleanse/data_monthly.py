import pandas as pd
from pathlib import Path
import sys

def split_data_by_month():
    """
    Reads the merged_final.csv file, and splits it into monthly Parquet files.
    """
    # 1. 입력 파일과 출력 폴더 경로 설정
    # 이전 단계에서 생성된 CSV 파일을 입력으로 사용합니다.
    input_file = Path("database/raw/merged_final.csv")
    output_dir = Path("database/monthly/")

    # 출력 폴더가 없으면 자동으로 생성
    # exist_ok=True 옵션은 폴더가 이미 있어도 오류를 발생시키지 않습니다.
    output_dir.mkdir(parents=True, exist_ok=True)

    # 입력 파일이 있는지 확인
    if not input_file.exists():
        print(f"오류: 입력 파일을 찾을 수 없습니다: {input_file}")
        print("먼저 data_filtering.py 스크립트를 실행하여 파일을 생성했는지 확인하세요.")
        sys.exit(1) # 오류와 함께 프로그램 종료

    print(f"{input_file} 파일을 읽는 중입니다...")
    # CSV 파일을 읽어옵니다.
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        print(f"오류: 파일을 읽는 중 문제가 발생했습니다: {e}")
        sys.exit(1)


    # 2. 'date' 컬럼이 있는지 확인하고 날짜 형식으로 변환
    if 'date' not in df.columns:
        print("오류: 'date' 컬럼을 찾을 수 없습니다.")
        sys.exit(1)
        
    # 날짜 형식을 자동으로 감지하여 날짜 타입으로 변환
    print("'date' 컬럼을 날짜 형식으로 변환하는 중입니다...")
    df['date'] = pd.to_datetime(df['date'])

    # 3. '연도-월'을 기준으로 데이터 그룹화
    print("데이터를 월별로 그룹화하는 중입니다...")
    # 'freq='M'' 옵션은 월말을 기준으로 그룹화합니다.
    grouped = df.groupby(pd.Grouper(key='date', freq='M'))
    
    total_files = len(grouped)
    print(f"총 {total_files}개의 월별 파일로 데이터를 분할합니다...")

    # 4. 각 월별 그룹을 별도의 Parquet 파일로 저장
    for i, (month_end_date, data_for_month) in enumerate(grouped, 1):
        # 파일 이름 형식을 'YYYY-MM'으로 지정
        year_month = month_end_date.strftime('%Y-%m')
        output_filename = f"merged_final_{year_month}.parquet"
        output_path = output_dir / output_filename

        # 해당 월에 데이터가 있는 경우에만 저장
        if not data_for_month.empty:
            print(f"({i}/{total_files}) 저장 중: {output_path}")
            data_for_month.to_parquet(output_path, index=False)
        else:
            print(f"({i}/{total_files}) 데이터가 없는 월은 건너뜁니다: {year_month}")

    print("\n작업 완료! 모든 데이터를 성공적으로 분할하여 다음 폴더에 저장했습니다:")
    # os.path.abspath 대신 Path.resolve()를 사용
    print(f"'{output_dir.resolve()}'")

# 이 스크립트가 직접 실행될 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    split_data_by_month()