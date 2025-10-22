import json
import pandas as pd
import os
import glob

def open_log():

    log_dir = 'database/logs/BL_MVO'
    list_of_files = glob.glob(os.path.join(log_dir, 'result of BL_MVO*.json'))
    if not list_of_files:
        print("오류: 로그 파일을 찾을 수 없습니다.")
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    file_path = latest_file 

    try:
        # 파일을 열고 JSON 데이터를 파이썬 딕셔너리/리스트로 불러옵니다.
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. 각 날짜별 포트폴리오 DataFrame을 담을 리스트를 생성합니다.
        all_portfolios = []

        # 2. JSON 데이터의 각 항목(날짜별 데이터)을 순회합니다.
        for record in data:
            weights = [float(w.strip('%')) / 100 for w in record['w_aiportfolio']]
            sectors = record['SECTOR']
            
            # 4. 'SECTOR'와 'Weight'를 컬럼으로 하는 DataFrame을 직접 생성합니다.
            portfolio_df = pd.DataFrame({
                'SECTOR': sectors,
                'Weight': weights
            })

    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
        return [] # 오류 발생 시 빈 리스트 반환
    except json.JSONDecodeError:
        print(f"오류: '{file_path}' 파일이 올바른 JSON 형식이 아닙니다.")
        return [] # 오류 발생 시 빈 리스트 반환
    
    # 최종적으로 DataFrame들이 담긴 리스트를 반환합니다.
    return portfolio_df