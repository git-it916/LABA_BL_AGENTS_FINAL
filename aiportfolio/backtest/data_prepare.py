import json
import pandas as pd
import os
import glob
from datetime import datetime

# python -m aiportfolio.backtest.data_prepare

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


# --- `open_BL_MVO_log` 함수 (BL 가중치 로드용) ---
def open_BL_MVO_log(simul_name, Tier):
    """
    로그 디렉토리에서 BL_MVO.json 파일을 찾아,
    모든 월의 데이터를 포함하는 long-format DataFrame으로 반환합니다.
    [수정] 영어 섹터 이름을 숫자 코드로 변환합니다.

    Args:
        simul_name (str): 시뮬레이션 이름
        Tier (int): 분석 단계 (1, 2, 3)
    """
    log_dir = f'database/logs/Tier{Tier}/result_of_BL-MVO'
    list_of_files = glob.glob(os.path.join(log_dir, f'{simul_name}.json'))
    
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
            # forecast_date를 그대로 사용 (날짜 변환 제거)
            forecast_date = pd.to_datetime(record['forecast_date'])
            weights = [float(w.strip('%')) / 100.0 for w in record['w_aiportfolio']]

            # BL 로그는 영어 섹터 이름을 포함
            sectors_english = record['SECTOR']

            # --- [수정된 부분] ---
            # 영어 섹터 이름을 GICS 숫자 코드로 변환
            try:
                numeric_sectors = map_gics_sector_to_code(sectors_english)
            except KeyError as e:
                # 맵핑 실패 시 오류 출력 후 해당 레코드를 건너뜀
                print(f"  !오류! {forecast_date.date()} BL 로그 GICS 맵핑 실패: {e}")
                continue # 이 record 처리를 건너뛰고 다음 record로 이동
            # --------------------

            # 숫자 코드(numeric_sectors)를 사용
            # ForecastDate 컬럼으로 변경 (InvestmentMonth 대신)
            for sector, weight in zip(numeric_sectors, weights):
                all_data.append({
                    'ForecastDate': forecast_date,  # 변경: forecast_date 그대로 사용
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
    [수정] forecast_date 기준으로 저장하도록 변경.
    """
    hist_start_date = pd.to_datetime(hist_start_date)

    # 월말(Month End) 기준으로 forecast_date 생성
    forecast_dates = pd.date_range(
        start=investment_start_date,
        end=investment_end_date,
        freq='M'  # 월말(Month End) 기준
    )

    print("월별 MVO 가중치 계산 시작...")
    print(f"예측 기간: {forecast_dates[0].date()} ~ {forecast_dates[-1].date()}")
    print(f"MVO 학습 시작일: {hist_start_date.date()}")

    mvo_weights_list = []

    # forecast_date별로 반복 (Expanding Window)
    for forecast_date in forecast_dates:
        # MVO 학습은 forecast_date까지의 데이터 사용
        training_end_date = forecast_date

        print(f"  - {forecast_date.date()} 예측 가중치 계산 (학습 기간: {hist_start_date.date()} ~ {training_end_date.date()})")

        try:
            # 1. Market_Params 객체 생성
            market_params = Market_Params(hist_start_date, training_end_date)

            # 2. MVO 계산
            mu_benchmark2 = market_params.making_mu()

            # making_sigma()는 (DataFrame, list[숫자코드]) 튜플 반환
            sigma_benchmark2, sectors_benchmark2_numeric = market_params.making_sigma()

            # [수정] MVO_Optimizer에 숫자 코드(sectors_benchmark2_numeric)를 직접 전달
            mvo = MVO_Optimizer(mu=mu_benchmark2, sigma=sigma_benchmark2, sectors=sectors_benchmark2_numeric)
            w_benchmark2 = mvo.optimize_tangency_1() # (weights, numeric_sectors) 튜플 반환

            # 3. 결과를 DataFrame으로 변환
            # ForecastDate 컬럼으로 변경
            df2 = pd.DataFrame({'SECTOR': w_benchmark2[1], 'Weight': w_benchmark2[0].flatten()})
            df2['ForecastDate'] = forecast_date  # 변경: forecast_date 저장
            mvo_weights_list.append(df2)

        except Exception as e:
            # MVO 계산 등 다른 오류 처리
            print(f"  !오류! {forecast_date.date()} MVO 계산 실패: {e}")
            continue
            
    if not mvo_weights_list:
        print("MVO 가중치 계산에 모두 실패했습니다.")
        return None
        
    mvo_portfolio_df = pd.concat(mvo_weights_list, ignore_index=True)
    
    print("월별 MVO 가중치 계산 완료.")
    return mvo_portfolio_df


# --- Market Portfolio 월별 가중치 계산 함수 (신규 추가) ---
def calculate_monthly_market_weights(investment_start_date, investment_end_date):
    """
    주어진 기간 동안 매월 시가총액 가중 포트폴리오(Market Portfolio) 가중치를 계산합니다.

    Market Portfolio는 각 섹터의 시가총액 비율로 가중치를 결정합니다.
    이는 수동적(passive) 투자 전략의 대표적인 벤치마크입니다.

    Args:
        investment_start_date (str or datetime): 투자 시작일
        investment_end_date (str or datetime): 투자 종료일

    Returns:
        pd.DataFrame: 월별 Market Portfolio 가중치
            - ForecastDate: 예측 기준일 (월말)
            - SECTOR: GICS 섹터 코드
            - Weight: 시가총액 가중치
    """
    # 월말(Month End) 기준으로 forecast_date 생성
    forecast_dates = pd.date_range(
        start=investment_start_date,
        end=investment_end_date,
        freq='M'  # 월말(Month End) 기준
    )

    print("월별 Market Portfolio 가중치 계산 시작...")
    print(f"예측 기간: {forecast_dates[0].date()} ~ {forecast_dates[-1].date()}")

    market_weights_list = []

    # forecast_date별로 반복
    for forecast_date in forecast_dates:
        print(f"  - {forecast_date.date()} 시가총액 가중치 계산")

        try:
            # Market_Params 객체 생성 (hist_start는 불필요하지만 인터페이스 맞추기 위해 사용)
            # w_mkt는 forecast_date 시점의 시가총액 가중치만 사용
            market_params = Market_Params(start_date=forecast_date, end_date=forecast_date)

            # making_sigma()를 호출하여 sectors 정보 획득
            sigma, sectors_numeric = market_params.making_sigma()

            # making_w_mkt()를 호출하여 시가총액 가중치 계산
            w_mkt, _ = market_params.making_w_mkt(sectors_numeric)

            # 결과를 DataFrame으로 변환
            df_market = pd.DataFrame({
                'SECTOR': sectors_numeric,  # GICS 숫자 코드
                'Weight': w_mkt.values  # 시가총액 가중치
            })
            df_market['ForecastDate'] = forecast_date
            market_weights_list.append(df_market)

        except Exception as e:
            print(f"  !오류! {forecast_date.date()} Market Portfolio 계산 실패: {e}")
            continue

    if not market_weights_list:
        print("Market Portfolio 가중치 계산에 모두 실패했습니다.")
        return None

    market_portfolio_df = pd.concat(market_weights_list, ignore_index=True)

    print("월별 Market Portfolio 가중치 계산 완료.")
    return market_portfolio_df


# --- 메인 실행 코드 (변경 없음) ---
if __name__ == "__main__":
    
    # MVO 학습 데이터 시작일 (예: 2020년부터)
    HIST_START = '2020-01-01' 
    
    # 백테스트(투자) 기간 (2024년 5월 ~ 12월)
    INVEST_START = '2024-05-01'
    INVEST_END = '2024-12-31'

    # 1. Market Portfolio 월별 가중치 계산 (신규)
    market_weights_df = calculate_monthly_market_weights(
        investment_start_date=INVEST_START,
        investment_end_date=INVEST_END
    )

    # 2. MVO 월별 가중치 계산
    mvo_weights_df = calculate_monthly_mvo_weights(
        hist_start_date=HIST_START,
        investment_start_date=INVEST_START,
        investment_end_date=INVEST_END
    )

    # 3. BL(AI) 월별 가중치 불러오기
    # 시뮬레이션 이름과 Tier를 지정하세요
    SIMUL_NAME = 'test1'  # 실제 시뮬레이션 이름
    TIER = 1              # 실제 Tier (1, 2, 3)
    bl_weights_df = open_BL_MVO_log(simul_name=SIMUL_NAME, Tier=TIER)

    # 4. Market Portfolio 가중치 결과 확인 (신규)
    if market_weights_df is not None:
        market_weights_df = market_weights_df.sort_values(
            by=['ForecastDate', 'SECTOR']
        ).reset_index(drop=True)

        print("\n\n" + "="*50)
        print("--- 최종 Market Portfolio 월별 가중치 DataFrame (정렬됨, GICS 숫자) ---")
        print("="*50)
        print(market_weights_df.to_string())
    else:
        print("\n\n--- Market Portfolio 가중치 생성 실패 ---")

    # 5. MVO 가중치 결과 확인 (전체 출력, 정렬)
    if mvo_weights_df is not None:
        # ForecastDate와 SECTOR로 정렬하여 BL 데이터와 구조를 통일
        mvo_weights_df = mvo_weights_df.sort_values(
            by=['ForecastDate', 'SECTOR']
        ).reset_index(drop=True)

        print("\n\n" + "="*50)
        print("--- 최종 MVO 월별 가중치 DataFrame (정렬됨, GICS 숫자) ---")
        print("="*50)
        print(mvo_weights_df.to_string())
    else:
        print("\n\n--- MVO 가중치 생성 실패 ---")

    # 6. BL(AI) 가중치 결과 확인 (전체 출력, 정렬)
    if bl_weights_df is not None:
        # ForecastDate와 SECTOR로 정렬하여 MVO 데이터와 구조를 통일
        bl_weights_df = bl_weights_df.sort_values(
            by=['ForecastDate', 'SECTOR']
        ).reset_index(drop=True)

        print("\n\n" + "="*50)
        print("--- 최종 BL(AI) 월별 가중치 DataFrame (정렬됨, GICS 숫자) ---")
        print("="*50)
        print(bl_weights_df.to_string())
    else:
        print("\n\n--- BL(AI) 가중치 생성 실패 ---")