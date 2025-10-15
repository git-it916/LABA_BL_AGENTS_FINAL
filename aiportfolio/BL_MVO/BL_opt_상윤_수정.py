import numpy as np
import pandas as pd
from datetime import datetime

# Import parameters from the BL_params directory
from aiportfolio.BL_MVO.BL_params.market_params import Market_Params
from aiportfolio.BL_MVO.BL_params.view_params_상윤수정 import get_view_params

def get_bl_outputs(tau, start_date, end_date):
    """
    This function runs the full Black-Litterman model by fetching market and view
    parameters and then returns the new combined expected returns.
    """
    # BL 변수 생성
    market_params = Market_Params(start_date, end_date)
    Pi = market_params.making_pi()      # Equilibrium excess returns (pi)
    sigma = market_params.making_sigma()  # Covariance matrix (Sigma)

    P, Q, Omega = get_view_params(sigma, tau)

    # --- Execute the Black-Litterman formula ---
    pi_np = Pi.values.flatten() if isinstance(Pi, pd.DataFrame) else Pi.flatten()
    sigma_np = sigma.values if isinstance(sigma, pd.DataFrame) else sigma

    # Calculate intermediate terms
    tau_sigma_inv = np.linalg.inv(tau * sigma_np)
    omega_inv = np.linalg.inv(Omega)
    PT_omega_inv = P.T @ omega_inv

    # Term A: [ (tau*Sigma)^-1 + P.T * Omega^-1 * P ]
    term_A = tau_sigma_inv + PT_omega_inv @ P

    # Term B: [ (tau*Sigma)^-1 * Pi + P.T * Omega^-1 * Q ]
    term_B_part1 = tau_sigma_inv @ pi_np
    term_B_part2 = PT_omega_inv @ Q
    term_B = term_B_part1 + term_B_part2

    # Calculate new posterior expected returns (Pi_new)
    Pi_new = np.linalg.inv(term_A) @ term_B

    # --- Return the outputs for the MVO script ---
    sectors = list(sigma.columns)
    tausigma = tau * sigma

    return Pi_new.reshape(-1, 1), tausigma, sectors

# This part allows the script to be run on its own for testing purposes
if __name__ == '__main__':
    # Set print options for better readability
    np.set_printoptions(precision=8, suppress=True)

    Pi_new, sigma, sectors, tau = get_bl_outputs(start_date=datetime(2021, 5, 1), end_date=datetime(2024, 4, 30), tau = 0.025)

    print("--- Black-Litterman Model Executed Successfully ---")
    print("\nSectors:")
    print(sectors)
    print(f"\nNew Expected Returns (Pi_new):\n{Pi_new}\n")
    print(f"Covariance Matrix (Sigma):\n{sigma}\n")