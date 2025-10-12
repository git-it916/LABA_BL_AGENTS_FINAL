#2024년 5월 예측
import numpy as np

import aiportfolio.BL_MVO.BL_params.agent_confindence as ac
import aiportfolio.BL_MVO.BL_params.view_params as vp
from aiportfolio.BL_MVO.BL_params.market_params import Market_Params
from datetime import datetime

start_date = datetime(2021, 5, 1)
end_date = datetime(2024, 4, 30)

market_params = Market_Params(start_date, end_date)
Pi = market_params.making_pi()
analyst_mses = ac.analyst_mses
current_forecasts = vp.current_forecasts


# 소수점 출력을 보기 좋게 설정
np.set_printoptions(precision=8, suppress=True)


# 전체 자산(섹터) 목록 및 공분산 행렬 (Sigma)
# 앞에서 구해줘야 함
sectors = [
    'Communication Services',
    'Consumer Discretionary',
    'Consumer Staples',
    'Energy',
    'Financials',
    'Health Care',
    'Industrials',
    'Information Technology',
    'Materials',
    'Real Estate',
    'Utilities'
]

# 실제 데이터 기반의 Sigma 행렬 가져오기
sigma = market_params.making_sigma()
print(f"자산 공분산 행렬 Sigma (11x11 행렬):\n{sigma}\n")

# ⚖️ 모델의 신뢰도 파라미터 (Tau)
tau = 0.025


# 애널리스트 신뢰도 가중치 (w) 계산
print("STEP 1: 애널리스트 신뢰도 가중치(w) 계산")

# MSE의 역수를 취해 초기 가중치 설정 (오차가 작을수록 가중치 높음)
inverse_mses = 1 / analyst_mses
# 총합이 1이 되도록 정규화
analyst_weights = inverse_mses / np.sum(inverse_mses)




# 피킹 행렬 (P) 및 뷰 벡터 (Q) 생성


# 피킹 행렬 P 정의 (5개 뷰 x 11개 섹터)
# 섹터 순서: Communication Services, Consumer Discretionary, Consumer Staples, Energy, Financials, Health Care, Industrials, Information Technology, Materials, Real Estate, Utilities
P = np.array([
    # IT vs Financials
    [0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0],   # 뷰 1: IT > Financials
    # Discretionary vs Staples
    [0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0],   # 뷰 2: Discretionary > Staples
    # Healthcare vs Industrials
    [0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0],   # 뷰 3: Healthcare > Industrials
    # Energy vs Industrials
    [0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0],   # 뷰 4: Energy > Industrials
    # Utilities vs Financials
    [0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1]    # 뷰 5: Utilities > Financials
])
print(f"피킹 행렬 P (5x11 행렬):\n{P}\n")

# 뷰 벡터 Q 계산 (전망치 행렬과 가중치 벡터의 내적)
Q = np.dot(current_forecasts, analyst_weights)
print(f"계산된 뷰 벡터 Q (5x1 벡터):\n{Q.reshape(-1, 1)}\n")


# 뷰 불확실성 행렬 (Omega) 생성

print("STEP 3: 뷰 불확실성 행렬(Omega) 생성")

# 오메가 행렬을 0으로 초기화
num_views = P.shape[0]
Omega = np.zeros((num_views, num_views))

# 각 뷰에 대해 대각 원소(omega_i)를 계산
for i in range(num_views):
    # 1. 애널리스트 뷰의 분산 (sigma_q_i^2) 계산
    forecasts_for_view = current_forecasts[i, :]
    sigma_q_i_sq = np.var(forecasts_for_view)

    # 2. 뷰 포트폴리오의 분산 (P_i * Sigma * P_i^T) 계산
    P_row = P[i, :]
    p_sigma_pT = P_row @ sigma.values @ P_row.T

    # 3. 최종 omega_i 계산 및 행렬에 삽입
    omega_i = tau * sigma_q_i_sq * p_sigma_pT
    Omega[i, i] = omega_i

print(f"최종 계산된 오메가 행렬 Omega (5x5 대각 행렬):\n{Omega}\n")


# ----------------------------------------------------------------------
# STEP 4: 최종 Black-Litterman 포트폴리오(Equilibrium Excess Returns) 계산
# ----------------------------------------------------------------------
print("STEP 4: 최종 Black-Litterman 포트폴리오 계산")

# 시장 균형 초과 수익률 (Pi)
Pi = market_params.making_pi()
print(f"시장 균형 초과 수익률 Pi (11X1 벡터):\n{Pi.reshape(-1, 1)}\n")

# Black-Litterman 공식: Pi_new = [ (tau*Sigma)^-1 + P.T * Omega^-1 * P ]^-1 * [ (tau*Sigma)^-1 * Pi + P.T * Omega^-1 * Q ]

# 1. (tau*Sigma)^-1
# sigma는 Pandas DataFrame이므로 .values를 사용합니다.
tau_sigma_inv = np.linalg.inv(tau * sigma.values)

# 2. P.T * Omega^-1
omega_inv = np.linalg.inv(Omega)
PT_omega_inv = P.T @ omega_inv

# 3. [ (tau*Sigma)^-1 + P.T * Omega^-1 * P ]
# P는 이미 NumPy 배열이므로 .values가 필요 없습니다.
term_A = tau_sigma_inv + PT_omega_inv @ P

# 4. [ (tau*Sigma)^-1 * Pi + P.T * Omega^-1 * Q ]
# ✨✨✨ 여기가 가장 중요한 수정 지점입니다! ✨✨✨
# Pi는 Pandas 객체이므로 반드시 .values를 붙여 NumPy 배열로 만들어야 합니다.
term_B = (tau_sigma_inv @ Pi) + (PT_omega_inv @ Q)

# 5. 최종 Pi_new 계산
Pi_new = np.linalg.inv(term_A) @ term_B

# 출력 메시지의 벡터 크기를 (11x1 벡터)로 수정했습니다.
print(f"새로운 기대 초과 수익률 Pi_new (11x1 벡터):\n{Pi_new.reshape(-1, 1)}\n")