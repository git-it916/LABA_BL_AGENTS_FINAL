import pandas as pd

# Parquet 파일 경로 지정
file_path = 'database/sector/2015/01/Communication_Services.parquet'

# Parquet 파일을 데이터프레임으로 불러오기
try:
    df = pd.read_parquet(file_path)
    print("Parquet 파일이 성공적으로 로드되었습니다.")
    print(df.head()) # 데이터프레임의 상위 5개 행 출력
except FileNotFoundError:
    print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
except Exception as e:
    print(f"파일을 읽는 도중 오류가 발생했습니다: {e}")

print(df.columns)