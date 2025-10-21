from .BL_MVO.BL_opt_상윤_수정 import get_bl_outputs
from .BL_MVO.MVO_opt import MVO_Optimizer
from .util.making_rollingdate import get_rolling_dates
from .util.save_log_as_json import save_log_as_json

def scene(tau, forecast_period):
    tau = tau
    forecast_period = forecast_period
    forecast_date = get_rolling_dates(forecast_period)

    results = []

    # 기간별 BL -> MVO 수행
    for i, period in enumerate(forecast_date):

        print(f"--- forecast_date: {period['forecast_date']} ---")
        start_date = period['start_date']
        end_date = period['end_date']
        
        # BL 실행
        BL = get_bl_outputs(tau, start_date=start_date, end_date=end_date)

        # MVO 실행
        mvo = MVO_Optimizer(mu=BL[0], sigma=BL[1], sectors=BL[2])
        w_tan = mvo.optimize_tangency_1()[0]
        
        # 결과 저장
        scenario_result = {
            "forecast_date": period['forecast_date'],
            "w_aiportfolio": [f"{weight[0] * 100:.4f}%" for weight in w_tan],
            "SECTOR": BL[2]
        }
        results.append(scenario_result)
    
    save_log_as_json(results)

    return results