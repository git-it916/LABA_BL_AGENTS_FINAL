import os

from .BL_MVO.BL_opt import get_bl_outputs
from .BL_MVO.MVO_opt import MVO_Optimizer
from .util.making_rollingdate import get_rolling_dates
from .util.sector_mapping import map_gics_sector
from .util.save_log_as_json import save_BL_as_json

def scene(simul_name, Tier, tau, forecast_period):
    tau = tau
    forecast_period = forecast_period
    forecast_date = get_rolling_dates(forecast_period)

    # 결과를 저장한 디렉토리 생성
    base_dir = os.path.join("database", "logs")
    current_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    log_path = os.path.join(base_dir, f'result of {current_time_str}')
    bl_result_path = os.path.join(log_path, "BL_result")
    llm_view_path = os.path.join(log_path, "LLM_view")

    os.makedirs(bl_result_path, exist_ok=True)
    os.makedirs(llm_view_path, exist_ok=True)

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
            "SECTOR": map_gics_sector(BL[2])
        }
        results.append(scenario_result)
    
    save_BL_as_json(results)

    return results