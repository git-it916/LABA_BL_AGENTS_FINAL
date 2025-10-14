import numpy as np
import pandas as pd
from datetime import datetime

# Make sure these imports are correct for your project structure
import aiportfolio.BL_MVO.BL_params.agent_confindence as ac
import aiportfolio.BL_MVO.BL_params.view_params as vp
from aiportfolio.BL_MVO.BL_params.market_params import Market_Params

def get_bl_outputs():
    """
    This function runs the Black-Litterman model and returns its key outputs.
    """
    start_date = datetime(2021, 5, 1)
    end_date = datetime(2024, 4, 30)

    market_params = Market_Params(start_date, end_date)
    analyst_mses = ac.analyst_mses
    current_forecasts = vp.current_forecasts

    np.set_printoptions(precision=8, suppress=True)

    sectors = [
        'Communication Services', 'Consumer Discretionary', 'Consumer Staples',
        'Energy', 'Financials', 'Health Care', 'Industrials',
        'Information Technology', 'Materials', 'Real Estate', 'Utilities'
    ]

    sigma = market_params.making_sigma()
    tau = 0.025

    # Analyst weights calculation
    inverse_mses = 1 / analyst_mses
    analyst_weights = inverse_mses / np.sum(inverse_mses)

    # Picking matrix P
    P = np.array([
        [0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0],
        [0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0],
        [0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1]
    ])

    # View vector Q
    Q = np.dot(current_forecasts, analyst_weights)

    # Omega matrix
    num_views = P.shape[0]
    Omega = np.zeros((num_views, num_views))
    sigma_np = sigma.values if isinstance(sigma, pd.DataFrame) else sigma

    for i in range(num_views):
        forecasts_for_view = current_forecasts[i, :]
        sigma_q_i_sq = np.var(forecasts_for_view)
        P_row = P[i, :]
        p_sigma_pT = P_row @ sigma_np @ P_row.T
        omega_i = tau * sigma_q_i_sq * p_sigma_pT
        Omega[i, i] = omega_i

    # Black-Litterman formula
    Pi = market_params.making_pi()
    pi_np = Pi.values.flatten() if isinstance(Pi, pd.DataFrame) else Pi.flatten()

    tau_sigma_inv = np.linalg.inv(tau * sigma_np)
    omega_inv = np.linalg.inv(Omega)
    PT_omega_inv = P.T @ omega_inv
    term_A = tau_sigma_inv + PT_omega_inv @ P
    term_B_part1 = tau_sigma_inv @ pi_np
    term_B_part2 = PT_omega_inv @ Q
    term_B = term_B_part1 + term_B_part2
    
    Pi_new = np.linalg.inv(term_A) @ term_B

    # Return all the necessary outputs for the MVO script
    return Pi_new.reshape(-1, 1), sigma, sectors, tau

# This part allows the script to still be run on its own for testing purposes
if __name__ == '__main__':
    Pi_new, sigma, sectors, tau = get_bl_outputs()
    print("--- Black-Litterman Model Executed Directly ---")
    print(f"New Expected Returns (Pi_new):\n{Pi_new}\n")
    print(f"Covariance Matrix (Sigma):\n{sigma}\n")