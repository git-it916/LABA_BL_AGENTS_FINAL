import pandas as pd
import numpy as np

from .BL_params.view_params import BlackLittermanMatrixGenerator
from .BL_params.market_params import Market_Params

def BL_optimization(tau, start_date=None, end_date=None):
    start_date = start_date
    end_date = end_date

    # view_params
    view_params = BlackLittermanMatrixGenerator(n_assets=9)
    my_matrices = view_params.generate_all_matrices(k_views=5)
    P = my_matrices['P']
    Q = my_matrices['Q']
    omega = my_matrices['Omega']

    # market_params
    market_params = Market_Params(start_date=start_date, end_date=end_date)
    pi = market_params.making_pi()
    sigma = market_params.making_sigma()
    tau=tau

    # Black-Litterman 공식 적용
    tausigma = tau * sigma
    tausigma_inv = np.linalg.inv(tausigma)
    omega_inv = np.linalg.inv(omega)

    BL_returns = np.linalg.inv(tausigma_inv + P.T @ omega_inv @ P) @ (tausigma_inv @ pi + P.T @ omega_inv @ Q)

    SECTOR = sigma.columns
    BL_returns_series = pd.Series(BL_returns.values.flatten(), index=SECTOR)

    # print("BL returns:\n", BL_returns_series)

    return [BL_returns_series, tausigma, SECTOR]