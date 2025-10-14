import pandas as pd
from aiportfolio.BL_MVO.BL_opt import get_bl_outputs
from aiportfolio.BL_MVO.MVO_opt import MVO_Optimizer

# 1. Run the Black-Litterman model to get outputs
print("✅ STEP 1: Running Black-Litterman model...")
Pi_new, sigma, sectors, tau = get_bl_outputs()
print("Black-Litterman calculation complete.\n")

# 2. Prepare inputs for the MVO Optimizer
print("✅ STEP 2: Preparing inputs for MVO...")
mu_BL = pd.DataFrame(Pi_new, index=sectors, columns=['ExcessReturn'])
tausigma = tau * sigma
print("Inputs are ready.\n")

# 3. Instantiate and run the MVO optimizer
print("✅ STEP 3: Running Mean-Variance Optimization...")
optimizer = MVO_Optimizer(mu_BL, tausigma, sectors)

# Run the two different optimization methods
print("\n--- Method 1: optimize_tangency() ---")
w_tan_direct = optimizer.optimize_tangency()

print("\n--- Method 2: optimize_tangency_1() (with long-only constraint) ---")
w_tan_scipy = optimizer.optimize_tangency_1()
print("\nOptimization complete.\n")

# 4. Display the final comparison
print("✅ FINAL RESULTS: Portfolio Weights Comparison")
print("-" * 50)
weights_df = pd.DataFrame({
    'Weights (Direct)': w_tan_direct.flatten(),
    'Weights (SciPy Long-Only)': w_tan_scipy.flatten()
}, index=sectors)

print(weights_df.to_string(float_format="%.4f"))
print("-" * 50)