from aiportfolio.BL_MVO.BL_params.market_params_상윤수정 import Market_Params
from aiportfolio.BL_MVO.MVO_opt import MVO_Optimizer
from aiportfolio.backtest.making_dataframe import open_log

# benchmark1: 시총가중 포트폴리오
# benchmark2: tangency 포트폴리오
# aiportfoilo: 우리가 만든 포트폴리오

def prepare_benchmark(start_date, end_date):

    # benchmark1 비중
    market_params = Market_Params(start_date, end_date)
    w_benchmark1 = market_params.making_w_mkt()

    # benchmark2 비중
    mu_benchmark2 = market_params.making_mu()
    sigma_benchmark2 = market_params.making_sigma()
    sectors_benchmark2 = list(sigma_benchmark2.columns)

    mvo = MVO_Optimizer(mu=mu_benchmark2, sigma=sigma_benchmark2, sectors=sectors_benchmark2)
    w_benchmark2 = mvo.optimize_tangency_1()

    # aiportfoilo 비중
    df_aiportfoilo = open_log()

    return w_benchmark1, w_benchmark2, df_aiportfoilo