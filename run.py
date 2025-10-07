import pandas as pd

from aiportfolio.scene import scene

#######################################
# configuration
#######################################
# 연구 기간
forecast_period = [
    "24-05-31",
    "24-06-30",
    "24-07-31",
    "24-08-31",
    "24-09-30",
    "24-10-31",
    "24-11-30",
    "24-12-31"
]

# tau: 시장 불확실성(pi 계산용)
tau = 0.025
# gamma: 위험회피계수(MVO 최적화용)
gamma = 0.1

#######################################
# run
#######################################

results = scene(tau=tau, gamma=gamma, forecast_period=forecast_period)

# 결과 출력
for i, scenario in enumerate(results):
    forecast_date = scenario['forecast_date'].strftime('%Y-%m-%d')
    
    print(f"\n✅ 시나리오 {i+1} : {forecast_date}")
    print("-" * 30)

    # w_delta_norm 출력
    w_delta_norm_df = pd.DataFrame({
        'SECTOR': scenario['SECTOR'],
        'w_delta_norm': scenario['w_delta_norm'].flatten()
    }).set_index('SECTOR')
    print("👉 효용함수 포트폴리오 비중 (w_delta_norm):")
    print(w_delta_norm_df.to_string(float_format="%.4f"))

    print() # 빈 줄 추가

    # w_tan 출력
    w_tan_df = pd.DataFrame({
        'SECTOR': scenario['SECTOR'],
        'w_tan': scenario['w_tan'].flatten()
    }).set_index('SECTOR')
    print("👉 텐전시 포트폴리오 비중 (w_tan):")
    print(w_tan_df.to_string(float_format="%.4f"))
    print("\n" + "-" * 60)