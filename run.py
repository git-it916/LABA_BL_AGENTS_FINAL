import os
from datetime import datetime

from aiportfolio.scene import scene

#######################################
# configuration
#######################################
# 연구 기간
'''
forecast_period = [
    "24-05-31"
]
'''

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


# tau: 시장 불확실성(조정계수)
tau = 0.025

#######################################
# run
#######################################

# 결과를 저장한 디렉토리 생성
base_dir = os.path.join("database", "logs")
current_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

log_path = os.path.join(base_dir, f'result of {current_time_str}')
bl_result_path = os.path.join(log_path, "BL_result")
llm_view_path = os.path.join(log_path, "LLM_view")

os.makedirs(bl_result_path, exist_ok=True)
os.makedirs(llm_view_path, exist_ok=True)

BL_results = scene(tau=tau, forecast_period=forecast_period)