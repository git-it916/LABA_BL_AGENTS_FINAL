import json
import pandas as pd
import os
import glob
from datetime import datetime

# MVO 계산에 필요한 모듈 임포트
from aiportfolio.BL_MVO.BL_params.market_params import Market_Params
from aiportfolio.BL_MVO.MVO_opt import MVO_Optimizer
# (final은 수익률 계산용이므로 여기서는 필요 없음)


# --- [추가된 GICS 맵핑 함수] ---
def map_gics_sector(sector_list):
    """ GICS 숫자 코드를 영어 섹터 이름으로 변환합니다. """
    gics_mapping = {
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

    mapped = []  # 결과를 담을 리스트

    for code in sector_list:
        # GICS 코드는 정수형(int)일 수 있으므로, .get()을 사용하기보다
        # in 연산자
        int_code = int(code) # 혹시 모를 문자열 입력을 위해 형변환
        if int_code in gics_mapping:
            mapped.append(gics_mapping[int_code])
        else:
            # 맵핑에 실패하면 오류를 발생시켜 상위에서 처리하도록 함
            raise KeyError(f"유효하지 않은 GICS 코드입니다 (Invalid GICS code): {code}")
    
    return mapped
# ---------------------------------


# --- `open_log` 함수 (BL 가중치 로드용) ---
def open_log():
    """
    로그 디렉토리에서 가장 최신 BL_MVO.json 파일을 찾아,
    모든 월의 데이터를 포함하는 long-format DataFrame으로 반환합니다.
    """
    log_dir = 'database/logs/BL_MVO'
    list_of_files = glob.glob(os.path.join(log_dir, 'result of BL_MVO*.json'))
    
    if not list_of_files:
        print(f"오류: '{log_dir}' 디렉토리에서 로그 파일을 찾을 수 없습니다.")
        return None
        
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"BL 로그 파일 사용: {latest_file}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        all_data = []
        for record in data:
            forecast_date = pd.to_datetime(record['forecast_date'])
            # 'M'은 월말 기준이므로, 월초 기준으로 통일합니다.
            investment_month = forecast_date.to_period('M').to_timestamp()
            weights = [float(w.strip('%')) / 100.0 for w in record['w_aiportfolio']]
            sectors = record['SECTOR'] # BL 로그는 이미 영어 섹터 이름을 포함
            
            for sector, weight in zip(sectors, weights):
                all_data.append({
                    'InvestmentMonth': investment_month,
                    'SECTOR': sector,
                    'Weight': weight
                })
                
        if not all_data: 
            print("오류: JSON 파일 내용은 있으나 처리된 데이터가 없습니다.")
            return None
            
        return pd.DataFrame(all_data)
        
    except Exception as e:
        print(f"open_log 처리 중 오류 발생: {e}")
        return None

# --- MVO 월별 가중치 계산 함수 (맵핑 로직 반영) ---
def calculate_monthly_mvo_weights(hist_start_date, investment_start_date, investment_end_date):
    """
    주어진 기간 동안 매월 MVO 가중치를 계산합니다.
    [수정] GICS 맵핑 함수를 사용하여 숫자 코드를 영어 섹터 이름으로 변환합니다.
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
            # 제공된 GICS 맵핑 함수를 사용해 숫자 코드를 영어 섹터 이름으로 변환
            try:
                english_sectors = map_gics_sector(sectors_benchmark2_numeric)
            except KeyError as e:
                # 맵핑 실패 시(map_gics_sector에서 raise된 KeyError 처리)
                # 오류 출력 후 해당 월을 건너뜀
                print(f"  !오류! {investment_month.date()} GICS 코드 맵핑 실패: {e}")
                continue # 다음 월로 넘어감
            # --------------------

            # MVO_Optimizer에 영어 이름(english_sectors)을 전달
            mvo = MVO_Optimizer(mu=mu_benchmark2, sigma=sigma_benchmark2, sectors=english_sectors)
            w_benchmark2 = mvo.optimize_tangency_1() # (weights, english_sectors) 튜플 반환

            # 3. 결과를 DataFrame으로 변환
            # w_benchmark2[1]는 이제 맵핑된 영어 섹터 이름 리스트입니다.
            df2 = pd.DataFrame({'SECTOR': w_benchmark2[1], 'Weight': w_benchmark2[0].flatten()})
            df2['InvestmentMonth'] = investment_month # 투자월 정보 추가
            mvo_weights_list.append(df2)

        except Exception as e:
            # GICS 맵핑 외의 MVO 계산 등 다른 오류 처리
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
        print("--- 최종 MVO 월별 가중치 DataFrame (정렬됨) ---")
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
        print("--- 최종 BL(AI) 월별 가중치 DataFrame (정렬됨) ---")
        print("="*50)
        print(bl_weights_df.to_string())
    else:
        print("\n\n--- BL(AI) 가중치 생성 실패 ---")