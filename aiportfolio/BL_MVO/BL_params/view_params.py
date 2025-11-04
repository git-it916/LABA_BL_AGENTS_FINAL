import numpy as np
import pandas as pd

from aiportfolio.agents.Llama_config import prepare_pipeline_obj
from aiportfolio.agents.Llama_view_수정중 import generate_sector_views
from aiportfolio.agents.converting_viewtomatrix import open_file, create_Q_vector, create_P_matrix

def get_view_params(sigma, tau, end_date):
    """
    This function calculates and returns the view-related parameters P, Q, and Omega.

    Args:
        sigma (pd.DataFrame): The covariance matrix of asset returns.
        tau (float): A scalar indicating the uncertainty in the prior estimate.

    Returns:
        tuple: A tuple containing P, Q, and Omega.
    """
    pipeline_to_use = prepare_pipeline_obj()
    generate_sector_views(pipeline_to_use, end_date)
    views_data = open_file()

    # --- Picking matrix (P) ---
    P = create_P_matrix(views_data)

    # --- View vector (Q) ---
    Q = create_Q_vector(views_data)

    # --- Omega matrix (Ω) ---
    num_views = P.shape[0]
    Omega = np.zeros((num_views, num_views))
    sigma_np = sigma.values if isinstance(sigma, pd.DataFrame) else sigma

    '''
    for i in range(num_views):
        forecasts_for_view = Q[i, :]
        sigma_q_i_sq = np.var(forecasts_for_view)
        P_row = P[i, :]
        p_sigma_pT = P_row @ sigma_np @ P_row.T
        omega_i = tau * sigma_q_i_sq * p_sigma_pT
        Omega[i, i] = omega_i
    '''
        
    for i in range(num_views):
        P_row = P[i, :]
        p_sigma_pT = P_row @ sigma_np @ P_row.T
        omega_i = tau * p_sigma_pT
        Omega[i, i] = omega_i

    return P, Q, Omega