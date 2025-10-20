import numpy as np
import pandas as pd

# Analyst confidence and view parameters
from aiportfolio.agents.generator_people import generated_view

def get_view_params(sigma, tau):
    """
    This function calculates and returns the view-related parameters P, Q, and Omega.

    Args:
        sigma (pd.DataFrame): The covariance matrix of asset returns.
        tau (float): A scalar indicating the uncertainty in the prior estimate.

    Returns:
        tuple: A tuple containing P, Q, and Omega.
    """
    current_forecasts, analyst_mses = generated_view()

    # --- Analyst weights calculation (w) ---
    inverse_mses = 1 / analyst_mses
    analyst_weights = inverse_mses / np.sum(inverse_mses)

    # --- Picking matrix (P) ---
    # Sectors order: Communication Services, Consumer Discretionary, Consumer Staples,
    # Energy, Financials, Health Care, Industrials, Information Technology,
    # Materials, Real Estate, Utilities
    P = np.array([
        [0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0],   # 뷰 1: IT > Financials
        [0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0],   # 뷰 2: Discretionary > Staples
        [0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0],   # 뷰 3: Healthcare > Industrials
        [0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0],   # 뷰 4: Energy > Industrials
        [0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1]    # 뷰 5: Utilities > Financials
    ])

    # --- View vector (Q) ---
    Q = np.dot(current_forecasts, analyst_weights)

    # --- Omega matrix (Ω) ---
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

    return P, Q, Omega