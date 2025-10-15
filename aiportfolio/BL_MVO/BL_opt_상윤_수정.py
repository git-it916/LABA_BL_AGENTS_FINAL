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