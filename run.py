import os
from datetime import datetime

from aiportfolio.scene import scene

#######################################
# configuration
#######################################
# 연구 기간
simul_name = 'test1'

Tier = 1

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

BL_results = scene(simul_name=simul_name, Tier=Tier, tau=tau, forecast_period=forecast_period)