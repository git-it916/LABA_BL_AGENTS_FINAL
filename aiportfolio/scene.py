from .BL_MVO.BL_opt import BL_optimization
from .BL_MVO.MVO_opt import MVO_Optimizer
from .util.making_rollingdate import get_rolling_dates

def scene(tau, gamma, forecast_period):
    
    tau = tau
    gamma = gamma
    forecast_period = forecast_period
    forecast_date = get_rolling_dates(forecast_period)

    results = []

    # 기간별 BL -> MVO 수행
    for i, period in enumerate(forecast_date):

        print(f"--- forecast_date: {period['forecast_date']} ---")
        start_date = period['start_date']
        end_date = period['end_date']
        
        # BL 실행
        BL = BL_optimization(tau, start_date=start_date, end_date=end_date)

        # MVO 실행
        mvo = MVO_Optimizer(BL[0], BL[1], BL[2])
        w_delta_norm = mvo.optimize_utility_1(gamma)
        w_tan = mvo.optimize_tangency_1()
        
        # 결과 저장
        scenario_result = {
            "forecast_date": period['forecast_date'],
            "w_delta_norm": w_delta_norm,
            "w_tan": w_tan,
            "SECTOR": BL[2]
        }
        results.append(scenario_result)
    
    return results