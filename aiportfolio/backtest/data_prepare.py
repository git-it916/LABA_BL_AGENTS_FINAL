import json
import pandas as pd
import os
import glob

def open_log():
    """
    'database/logs/BL_MVO' 디렉토리에서 가장 최신의 
    'result of BL_MVO*.json' 파일을 찾아,
    모든 날짜의 데이터를 포함하는 long-format DataFrame으로 반환합니다.
    """
    log_dir = 'database/logs/BL_MVO'
    list_of_files = glob.glob(os.path.join(log_dir, 'result of BL_MVO*.json'))
    
    if not list_of_files:
        print(f"오류: '{log_dir}' 디렉토리에서 로그 파일을 찾을 수 없습니다.")
        return None
        
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"가장 최신 로그 파일 사용: {latest_file}")

    try:
        # 1. 파일을 열고 JSON 데이터를 불러옵니다.
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 2. 모든 날짜-섹터-가중치 정보를 담을 리스트 생성
        processed_data = []
        
        # 3. JSON 데이터의 각 항목(날짜별 데이터)을 순회
        for entry in data:
            forecast_date = entry['forecast_date']
            sectors = entry['SECTOR']
            # '%' 제거 및 소수점(e.g., 0.3946)으로 변환
            weights = [float(w.strip('%')) / 100.0 for w in entry['w_aiportfolio']] 
            
            # 4. 날짜-섹터-가중치를 짝지어 리스트에 추가
            for sector, weight in zip(sectors, weights):
                processed_data.append({
                    'forecast_date': forecast_date,
                    'SECTOR': sector,
                    'Weight': weight # 컬럼명을 'Weight'로 변경
                })

        # 5. 전체 데이터를 하나의 DataFrame으로 생성
        if not processed_data:
            print("오류: JSON 파일에서 데이터를 처리하지 못했습니다.")
            return None
            
        df = pd.DataFrame(processed_data)
        
        # 6. 'forecast_date'를 datetime 객체로 변환
        df['forecast_date'] = pd.to_datetime(df['forecast_date'])
        
        return df

    except FileNotFoundError:
        print(f"오류: '{latest_file}' 파일을 찾을 수 없습니다.")
        return None
    except json.JSONDecodeError:
        print(f"오류: '{latest_file}' 파일이 올바른 JSON 형식이 아닙니다.")
        return None
    except Exception as e:
        print(f"데이터 처리 중 알 수 없는 오류 발생: {e}")
        return None

# --- 메인 코드 ---

# 1. 수정한 open_log() 함수를 호출하여 long-format DataFrame을 가져옵니다.
bl_long_df = open_log()

if bl_long_df is not None:
    # 2. 데이터를 피벗(pivot)하여 백테스트용 wide-format DataFrame 생성
    bl_weights_df = bl_long_df.pivot(
        index='forecast_date',
        columns='SECTOR',
        values='Weight'
    )

    # 3. 인덱스(날짜)를 '2024-05-31' -> '2024-05-01'로 변경
    # (월별 투자의 기준일로 삼기 위함)
    bl_weights_df.index = bl_weights_df.index.to_period('M').to_timestamp()

    # 4. 인덱스 및 컬럼 이름 정리
    bl_weights_df.index.name = 'InvestmentMonth'
    bl_weights_df.columns.name = 'Sector'

    # 5. 최종 결과 확인
    print("\nBlack-Litterman 포트폴리오 월별 가중치 (백테스트 준비 완료):")
    print(bl_weights_df)
else:
    print("데이터를 불러오지 못해 처리를 중단합니다.")