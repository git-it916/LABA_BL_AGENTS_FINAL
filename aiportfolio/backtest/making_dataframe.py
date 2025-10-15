import json
import pandas as pd

def open_log():
    
    file_path = 'database/logs/result of BL_MVO 20251015_113143.json' 

    try:
        # 파일을 열고 JSON 데이터를 파이썬 딕셔너리/리스트로 불러옵니다.
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # --- 데이터 가공 시작 ---
        
        # 1. DataFrame으로 변환할 데이터를 담을 빈 리스트를 생성합니다.
        processed_data = []

        # 2. JSON 데이터의 각 항목(날짜별 데이터)을 순회합니다.
        for record in data:
            # 3. 각 섹터 이름과 가중치를 짝지어 딕셔너리로 만듭니다.
            weights = [float(w.strip('%')) / 100 for w in record['w_tan']]
            portfolio_dict = dict(zip(record['SECTOR'], weights))
            
            # 4. 'forecast_date'를 딕셔너리에 추가합니다.
            portfolio_dict['forecast_date'] = record['forecast_date']
            
            processed_data.append(portfolio_dict)

        # --- 데이터 가공 끝 ---

        df_result = pd.DataFrame(processed_data)
        
        # 'forecast_date' 컬럼을 맨 앞으로 오도록 순서를 조정합니다.
        if not df_result.empty:
            cols = ['forecast_date'] + [col for col in df_result.columns if col != 'forecast_date']
            df_result = df_result[cols]

        print("DataFrame 변환 성공!")
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        print(df_result)

    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다.")
    except json.JSONDecodeError:
        print(f"오류: '{file_path}' 파일이 올바른 JSON 형식이 아닙니다.")
    
    return df_result