from aiportfolio.scene import scene

######################################
#            configuration           #
######################################

simul_name = 'single_test1'
Tier = 3
tau = 0.025
forecast_period = [
        "24-05-31",
        "24-06-30"
]
backtest_days_count = 19

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
    '''

######################################
#                 run                #
######################################

scene(simul_name, Tier, tau, forecast_period, backtest_days_count)

