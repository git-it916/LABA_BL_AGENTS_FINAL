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


# 결과를 표시할 새로운 데이터프레임 생성
display_df = pd.DataFrame(index=weights_df.index)

# 각 열(포트폴리오)에 대해 반올림, 정규화, 포맷팅을 순차적으로 적용
for column in weights_df.columns:
    # 1. 소수점 셋째 자리에서 반올림
    rounded_weights = weights_df[column].round(3)
    
    # 2. 반올림된 가중치의 합이 1이 되도록 다시 정규화
    normalized_weights = rounded_weights / rounded_weights.sum()
    
    # 3. 백분율(%) 형태로 변환하여 display_df에 저장
    display_df[column] = normalized_weights.apply('{:.2%}'.format)

# 최종 결과 출력
print(display_df)
print("-" * 50)