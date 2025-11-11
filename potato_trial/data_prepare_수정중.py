import json
import pandas as pd
import os
from glob import glob
from datetime import datetime

# python -m aiportfolio.backtest.data_prepare_수정중

# MVO 계산에 필요한 모듈 임포트
from aiportfolio.BL_MVO.BL_params.market_params import Market_Params
from aiportfolio.BL_MVO.MVO_opt import MVO_Optimizer
# (final은 수익률 계산용이므로 여기서는 필요 없음)


# --- [수정된 GICS 맵핑] ---

# 기준이 되는 맵핑 (코드 -> 이름)
gics_mapping_code_to_name = {
    10: "Energy",
    15: "Materials",
    20: "Industrials",
    25: "Consumer Discretionary",
    30: "Consumer Staples",
    35: "Health Care",
    40: "Financials",
    45: "Information Technology",
    50: "Communication Services",
    55: "Utilities",
    60: "Real Estate"
}

# [신규] 역맵핑 (이름 -> 코드), open_log 함수에서 사용
gics_mapping_name_to_code = {v: k for k, v in gics_mapping_code_to_name.items()}

def map_gics_sector_to_code(sector_list):
    """ [신규] GICS 영어 섹터 이름을 숫자 코드로 변환합니다. """
    mapped = []  # 결과를 담을 리스트

    for name in sector_list:
        if name in gics_mapping_name_to_code:
            mapped.append(gics_mapping_name_to_code[name])
        else:
            # 맵핑에 실패하면 오류를 발생시켜 상위에서 처리하도록 함
            raise KeyError(f"유효하지 않은 GICS 섹터 이름입니다 (Invalid GICS name): {name}")
    
    return mapped
# ---------------------------------


# --- `open_log` 함수 (BL 가중치 로드용) ---
def open_log():
    """
    로그 디렉토리에서 가장 최신 BL_MVO.json 파일을 찾아,
    모든 월의 데이터를 포함하는 long-format DataFrame으로 반환합니다.
    [수정] 영어 섹터 이름을 숫자 코드로 변환합니다.
    """
    # === 1. 최신 로그 파일 찾기 (기존 로직 동일) ===
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    mvo_logs_dir = os.path.join(current_script_path, '../..', 'database', 'logs')
    search_pattern = os.path.join(mvo_logs_dir, 'result of *')
    all_log_folders = glob(search_pattern)
    
    if not all_log_folders:
        print(f"경고: '{mvo_logs_dir}'에서 'result of *' 폴더를 찾지 못했습니다.")
        return None
        
    all_log_folders.sort()
    latest_folder = all_log_folders[-1]
    
    if not os.path.isdir(latest_folder):
        print(f"오류: '{latest_folder}'는 디렉토리가 아닙니다.")
        return None

    output_dir = os.path.join(latest_folder, 'BL_result')
    
    if not os.path.isdir(output_dir):
        print(f"오류: 최신 로그 폴더 안에 'LLM_view'를 찾을 수 없습니다. (경로: {output_dir})")
        return None

    json_files = glob(os.path.join(output_dir, '*.json'))

    if not json_files: 
        print(f"경고: '{output_dir}'에 JSON 파일이 존재하지 않습니다.")
        return None

    latest_file = max(json_files, key=os.path.getmtime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        all_data = []
        for record in data:
            forecast_date = pd.to_datetime(record['forecast_date'])
            # 'M'은 월말 기준이므로, 월초 기준으로 통일합니다.
            investment_month = forecast_date.to_period('M').to_timestamp()
            weights = [float(w.strip('%')) / 100.0 for w in record['w_aiportfolio']]
            
            # BL 로그는 영어 섹터 이름을 포함
            sectors_english = record['SECTOR'] 
            
            # --- [수정된 부분] ---
            # 영어 섹터 이름을 GICS 숫자 코드로 변환
            try:
                numeric_sectors = map_gics_sector_to_code(sectors_english)
            except KeyError as e:
                # 맵핑 실패 시 오류 출력 후 해당 레코드를 건너뜀
                print(f"  !오류! {investment_month.date()} BL 로그 GICS 맵핑 실패: {e}")
                continue # 이 record 처리를 건너뛰고 다음 record로 이동
            # --------------------

            # 숫자 코드(numeric_sectors)를 사용
            for sector, weight in zip(numeric_sectors, weights):
                all_data.append({
                    'InvestmentMonth': investment_month,
                    'SECTOR': sector, # 숫자 코드가 저장됨
                    'Weight': weight
                })
                
        if not all_data: 
            print("오류: JSON 파일 내용은 있으나 처리된 데이터가 없습니다.")
            return None
            
        return pd.DataFrame(all_data)
        
    except Exception as e:
        print(f"open_log 처리 중 오류 발생: {e}")
        return None

# --- MVO 월별 가중치 계산 함수 (맵핑 로직 제거) ---
def calculate_monthly_mvo_weights(hist_start_date, investment_start_date, investment_end_date):
    """
    주어진 기간 동안 매월 MVO 가중치를 계산합니다.
    [수정] GICS 맵핑을 제거하고 숫자 코드를 직접 사용합니다.
    """
    hist_start_date = pd.to_datetime(hist_start_date)
    investment_months = pd.date_range(
        start=investment_start_date, 
        end=investment_end_date, 
        freq='MS' # 월초(Month Start) 기준
    )
    
    print("월별 MVO 가중치 계산 시작...")
    print(f"투자 기간: {investment_months[0].date()} ~ {investment_months[-1].date()}")
    print(f"MVO 학습 시작일: {hist_start_date.date()}")
    
    mvo_weights_list = []

    # 투자월별로 반복 (Expanding Window)
    for investment_month in investment_months:
        # MVO 학습 종료일 = 투자월 1일의 하루 전
        training_end_date = investment_month - pd.DateOffset(days=1)
        
        print(f"  - {investment_month.date()} 투자 가중치 계산 (학습 기간: {hist_start_date.date()} ~ {training_end_date.date()})")
        
        try:
            # 1. Market_Params 객체 생성
            market_params = Market_Params(hist_start_date, training_end_date)
            
            # 2. MVO 계산
            mu_benchmark2 = market_params.making_mu()
            
            # making_sigma()는 (DataFrame, list[숫자코드]) 튜플 반환
            sigma_benchmark2, sectors_benchmark2_numeric = market_params.making_sigma()
            
            # --- [수정된 부분] ---
            # GICS 맵핑(숫자->영어) 로직을 제거함
            # --------------------

            # [수정] MVO_Optimizer에 숫자 코드(sectors_benchmark2_numeric)를 직접 전달
            mvo = MVO_Optimizer(mu=mu_benchmark2, sigma=sigma_benchmark2, sectors=sectors_benchmark2_numeric)
            w_benchmark2 = mvo.optimize_tangency_1() # (weights, numeric_sectors) 튜플 반환

            # 3. 결과를 DataFrame으로 변환
            # w_benchmark2[1]는 이제 숫자 섹터 코드 리스트입니다.
            df2 = pd.DataFrame({'SECTOR': w_benchmark2[1], 'Weight': w_benchmark2[0].flatten()})
            df2['InvestmentMonth'] = investment_month # 투자월 정보 추가
            mvo_weights_list.append(df2)

        except Exception as e:
            # MVO 계산 등 다른 오류 처리
            print(f"  !오류! {investment_month.date()} MVO 계산 실패: {e}")
            continue
            
    if not mvo_weights_list:
        print("MVO 가중치 계산에 모두 실패했습니다.")
        return None
        
    mvo_portfolio_df = pd.concat(mvo_weights_list, ignore_index=True)
    
    print("월별 MVO 가중치 계산 완료.")
    return mvo_portfolio_df


# --- 메인 실행 코드 (변경 없음) ---
if __name__ == "__main__":
    
    # MVO 학습 데이터 시작일 (예: 2020년부터)
    HIST_START = '2020-01-01' 
    
    # 백테스트(투자) 기간 (2024년 5월 ~ 12월)
    INVEST_START = '2024-05-01'
    INVEST_END = '2024-12-31'

    # 1. MVO 월별 가중치 계산
    mvo_weights_df = calculate_monthly_mvo_weights(
        hist_start_date=HIST_START, 
        investment_start_date=INVEST_START,
        investment_end_date=INVEST_END
    )

    # 2. BL(AI) 월별 가중치 불러오기
    bl_weights_df = open_log()

    # 3. MVO 가중치 결과 확인 (전체 출력, 정렬)
    if mvo_weights_df is not None:
        # InvestmentMonth와 SECTOR로 정렬하여 BL 데이터와 구조를 통일
        mvo_weights_df = mvo_weights_df.sort_values(
            by=['InvestmentMonth', 'SECTOR']
        ).reset_index(drop=True)

        print("\n\n" + "="*50)
        print("--- 최종 MVO 월별 가중치 DataFrame (정렬됨, GICS 숫자) ---")
        print("="*50)
        print(mvo_weights_df.to_string())
    else:
        print("\n\n--- MVO 가중치 생성 실패 ---")

    # 4. BL(AI) 가중치 결과 확인 (전체 출력, 정렬)
    if bl_weights_df is not None:
        # InvestmentMonth와 SECTOR로 정렬하여 MVO 데이터와 구조를 통일
        bl_weights_df = bl_weights_df.sort_values(
            by=['InvestmentMonth', 'SECTOR']
        ).reset_index(drop=True)

        print("\n\n" + "="*50)
        print("--- 최종 BL(AI) 월별 가중치 DataFrame (정렬됨, GICS 숫자) ---")
        print("="*50)
        print(bl_weights_df.to_string())
    else:
        print("\n\n--- BL(AI) 가중치 생성 실패 ---")