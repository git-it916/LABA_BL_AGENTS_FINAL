import pandas as pd

'''
# Parquet 파일 경로 지정
file_path = 'database/combine/all_data.parquet'

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
print(df.info())
'''

import logging
import os

# 로그를 저장할 디렉터리 경로
log_dir = 'logs'

# 현재 스크립트의 절대 경로를 기준으로 로그 디렉터리 경로 생성
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir_path = os.path.join(script_dir, log_dir)

# 만약 로그 디렉터리가 없으면 생성
if not os.path.exists(log_dir_path):
    os.makedirs(log_dir_path)

# 로그 파일 경로
log_file_path = os.path.join(log_dir_path, 'script_log.log')

# logging 기본 설정
logging.basicConfig(
    filename=log_file_path,  # 로그를 기록할 파일명
    level=logging.INFO,      # 기록할 로그 레벨 (INFO 이상)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_process():
    logging.info("프로세스 실행을 시작합니다.")
    try:
        # 여기에 실제 스크립트의 로직을 작성합니다.
        # 예시로 파일을 읽는 작업을 추가
        file_path = "example.txt"
        logging.info(f"'{file_path}' 파일을 읽으려고 시도합니다.")
        
        with open(file_path, 'r') as f:
            content = f.read()
            logging.info(f"파일 내용: {content[:50]}...") # 처음 50자만 출력
        
        logging.info("프로세스 실행이 성공적으로 완료되었습니다.")
        
    except FileNotFoundError:
        logging.error(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
    except Exception as e:
        logging.error(f"예기치 않은 오류가 발생했습니다: {e}")

# 함수 실행
if __name__ == "__main__":
    run_process()