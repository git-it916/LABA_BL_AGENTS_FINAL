import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (Windows: 'Malgun Gothic', macOS: 'AppleGothic')
# 사용하시는 OS에 맞춰 폰트 이름을 설정하세요.
try:
    plt.rc('font', family='Malgun Gothic')
    plt.rc('axes', unicode_minus=False) # 마이너스 부호 깨짐 방지
except:
    try:
        plt.rc('font', family='AppleGothic')
        plt.rc('axes', unicode_minus=False) # 마이너스 부호 깨짐 방지
    except:
        print("한글 폰트를 찾을 수 없습니다. 그래프의 한글이 깨질 수 있습니다.")


#################################################################
# 1. 가상 데이터 생성 (주어졌다고 가정한 데이터)
#################################################################

FORECAST_PERIODS = [
    "24-05-31", "24-06-30", "24-07-31", "24-08-31",
    "24-09-30", "24-10-31", "24-11-30", "24-12-31"
]
SECTORS = ['IT', '금융', '소비재', '바이오', '에너지']
HOLD_DAYS = 20 # 보유 기간 (영업일 기준)
MARKET_COL = 'Market' # 시장 지수 컬럼명

def create_mock_results(periods, sectors):
    """
    'scene' 함수가 반환하는 것과 유사한 구조의 가상 결과 리스트를 생성합니다.
    (예: BL_results)
    """
    results_list = []
    np.random.seed(42) # 재현성을 위한 시드 고정
    
    for period in periods:
        # 가중치의 합이 1이 되도록 랜덤 생성
        weights = np.random.rand(len(sectors))
        weights /= np.sum(weights)
        
        scenario = {
            "forecast_date": period,
            "w_aiportfolio": [f"{w * 100:.4f}%" for w in weights],
            "SECTOR": sectors
        }
        results_list.append(scenario)
    return results_list

def create_mock_price_data(assets, start='2024-04-01', end='2025-01-31'):
    """
    섹터 및 시장 지수의 일별 가격에 대한 가상 데이터프레임을 생성합니다.
    시뮬레이션 기간(24년 5월 ~ 12월 말 + 20영업일)을 모두 포함해야 합니다.
    """
    # 영업일 기준 날짜 인덱스 생성
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)
    
    # 랜덤 워크(Random Walk)를 사용한 가상 가격 데이터 생성
    data = {}
    for asset in assets + [MARKET_COL]:
        # 자산별로 변동성을 조금씩 다르게 줌
        returns = np.random.normal(loc=0.0005, scale=np.random.uniform(0.01, 0.03), size=n)
        price = 100 * (1 + returns).cumprod()
        data[asset] = price
        
    prices_df = pd.DataFrame(data, index=dates)
    prices_df.index.name = 'Date'
    return prices_df

#################################################################
# 2. 데이터 전처리 함수
#################################################################

def preprocess_weights(results_list):
    """
    'scene' 함수의 결과(w_aiportfolio가 문자열 리스트)를
    날짜별 {종목: 비중} 딕셔너리 형태로 변환합니다.
    """
    weights_dict = {}
    all_sectors = set()
    
    for item in results_list:
        key = item["forecast_date"] # 예: "24-05-31"
        sectors = item["SECTOR"]
        weights_str = item["w_aiportfolio"]
        
        # ["10.5000%"] -> [0.105]
        weights_float = [float(w.strip('%')) / 100.0 for w in weights_str]
        
        weights_dict[key] = dict(zip(sectors, weights_float))
        all_sectors.update(sectors)
        
    return weights_dict, sorted(list(all_sectors))

#################################################################
# 3. 핵심 백테스팅 로직
#################################################################

def calculate_aggregated_ecr(weights_dict, prices_df, all_sectors, forecast_periods, market_col='Market', hold_days=20):
    """
    주어진 가중치 딕셔너리를 기반으로 월별 초과 누적 수익률(ECR)을 계산하고,
    보유 기간(1~20일)별로 합산하여 반환합니다.
    """
    
    # 일별 수익률 계산
    daily_returns = prices_df.pct_change().dropna()
    
    # 각 월의 1일~20일차 초과 누적 수익률(ECR)을 저장할 DataFrame
    # 행: 보유일(1~20), 열: 투자월(24-05-31, 24-06-30, ...)
    all_period_ecr = pd.DataFrame(index=range(1, hold_days + 1), columns=forecast_periods)

    for period_key in forecast_periods:
        # 1. 투자 시작일(해당 월의 첫 번째 영업일) 찾기
        # period_key (예: "24-05-31") -> "2024-05"
        year_month = "20" + period_key[:2] + "-" + period_key[3:5]
        
        try:
            # 해당 월의 수익률 데이터에서 첫 번째 날짜(첫 영업일)를 찾음
            start_date = daily_returns.loc[year_month].index[0]
        except IndexError:
            print(f"경고: {year_month}의 데이터가 없어 {period_key} 기간을 건너뜁니다.")
            continue

        # 2. 투자 기간(20영업일)의 수익률 데이터 추출
        try:
            returns_slice = daily_returns.loc[start_date:].iloc[:hold_days]
            if len(returns_slice) < hold_days:
                print(f"경고: {period_key}의 투자 기간이 {hold_days}일보다 짧아 건너뜁니다.")
                continue
        except Exception as e:
            print(f"데이터 슬라이싱 오류 ({period_key}): {e}")
            continue
            
        # 3. 해당 월의 포트폴리오 가중치 벡터 생성
        current_weights = weights_dict.get(period_key, {})
        # all_sectors 기준_으로 가중치 벡터 생성 (없는 종목은 0)
        w = pd.Series([current_weights.get(s, 0) for s in all_sectors], index=all_sectors)

        # 4. 일별 포트폴리오 수익률 및 시장 수익률 계산
        port_returns = returns_slice[all_sectors].dot(w)
        market_returns = returns_slice[market_col]

        # 5. 누적 수익률(CR) 계산 (투자 시작일[0] ~ 19일차)
        # (1 + r).cumprod() - 1
        port_cr = (1 + port_returns).cumprod() - 1
        market_cr = (1 + market_returns).cumprod() - 1
        
        # 6. 초과 누적 수익률(ECR) 계산 (ECR = Portfolio CR - Market CR)
        ecr = port_cr - market_cr
        
        # 7. 결과 저장 (DataFrame의 인덱스가 1부터 시작하므로 .values 사용)
        all_period_ecr[period_key] = ecr.values

    # 8. 보유 기간(행)별로 모든 월(열)의 ECR을 합산
    # axis=1 : 가로(월별)로 더하기
    aggregated_ecr = all_period_ecr.sum(axis=1)
    
    return aggregated_ecr

#################################################################
# 4. 메인 실행 및 그래프 비교
#################################################################

if __name__ == "__main__":
    
    # --- 1. 가상 데이터 생성 (실제 데이터로 대체) ---
    print("가상 데이터 생성 중...")
    # BL 전략의 가중치 결과 (가상)
    mock_bl_results = create_mock_results(FORECAST_PERIODS, SECTORS)
    
    # MVO 전략의 가중치 결과 (가상)
    # 다른 시드(seed)를 사용하여 MVO 가중치는 BL과 다르게 생성
    np.random.seed(101) 
    mock_mvo_results = create_mock_results(FORECAST_PERIODS, SECTORS)
    
    # 모든 종목 리스트 (BL, MVO 포함)
    all_used_sectors = sorted(list(set(SECTORS)))
    
    # 종목 및 시장 가격 데이터 (가상)
    prices_df = create_mock_price_data(all_used_sectors)
    print("가상 데이터 생성 완료.")

    # --- 2. 데이터 전처리 ---
    print("가중치 데이터 전처리 중...")
    bl_weights_dict, _ = preprocess_weights(mock_bl_results)
    mvo_weights_dict, _ = preprocess_weights(mock_mvo_results)

    # --- 3. 백테스팅 실행 ---
    print("백테스팅 시뮬레이션 실행 중...")
    
    # BL 전략 시뮬레이션
    ecr_bl = calculate_aggregated_ecr(
        bl_weights_dict, prices_df, all_used_sectors, 
        FORECAST_PERIODS, market_col=MARKET_COL, hold_days=HOLD_DAYS
    )
    
    # MVO 전략 시뮬레이션
    ecr_mvo = calculate_aggregated_ecr(
        mvo_weights_dict, prices_df, all_used_sectors, 
        FORECAST_PERIODS, market_col=MARKET_COL, hold_days=HOLD_DAYS
    )
    print("시뮬레이션 완료.")

    # --- 4. 결과 출력 ---
    print("\n--- Black-Litterman (BL) 보유 기간별 총 초과 누적 수익률 ---")
    print(ecr_bl.to_string())
    
    print("\n--- Markowitz (MVO) 보유 기간별 총 초과 누적 수익률 ---")
    print(ecr_mvo.to_string())

    # --- 5. 그래프 시각화 ---
    plt.figure(figsize=(12, 7))
    
    plt.plot(ecr_bl.index, ecr_bl.values, marker='o', linestyle='-', label='Black-Litterman (BL)')
    plt.plot(ecr_mvo.index, ecr_mvo.values, marker='s', linestyle='--', label='Markowitz (MVO)')
    
    plt.title(f'보유 기간(1~{HOLD_DAYS}일)별 총 초과 누적 수익률 비교\n(2024년 5월~12월 합산)')
    plt.xlabel('보유 기간 (영업일)')
    plt.ylabel('총 초과 누적 수익률 (ECR 합산)')
    plt.xticks(range(1, HOLD_DAYS + 1)) # x축을 1, 2, 3... 20으로 표시
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.7)
    
    # 수익률(%)로 y축 포맷팅
    formatter = plt.FuncFormatter(lambda y, _: f'{y:.2%}')
    plt.gca().yaxis.set_major_formatter(formatter)
    
    plt.tight_layout()
    plt.show()