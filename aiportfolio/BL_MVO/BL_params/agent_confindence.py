#코드 필요 / 지금은 랜덤 값
import numpy as np
analyst_mses = np.array([0.00020, 0.00020, 0.00020, 0.00020])


# import numpy as np

# # 소수점 출력을 보기 좋게 설정
# np.set_printoptions(precision=8, suppress=True)


# # 과거 24개월을 바탕으로 최근예측에 더 큰 가중치를 주어서 MSE 계산 / 이 MSE 역수가 예측도가 될것 / 롤링방식 


# num_analysts = 4
# num_months = 24

# # 1. 과거 24개월간의 '실제 시장 결과' 및 '애널리스트 예측치' 데이터 생성(대체 필요)

# np.random.seed(123) # 결과를 일정하게 보기 위해 시드 고정
# historical_actual_outcomes = np.random.randn(num_months) * 0.02

# # 애널리스트별로 다른 수준의 노이즈를 추가하여 실력을 시뮬레이션
# historical_analyst_forecasts = np.zeros((num_months, num_analysts))
# for i in range(num_analysts):
#     # Analyst 1이 가장 정확하고, 4로 갈수록 부정확해짐
#     noise_level = 0.005 * (i + 1)
#     noise = np.random.randn(num_months) * noise_level
#     historical_analyst_forecasts[:, i] = historical_actual_outcomes + noise

# # 2. '시간 가중치' 생성(가장 최근이 24개월 전에 비해 24배 만큼의 가중치)
# time_weights = np.arange(1, num_months + 1)
# normalized_time_weights = time_weights / np.sum(time_weights) # 가중치의 합이 1이 되도록 정규화


# # 3. '시간 가중 MSE' 계산
# # 이 계산은 매월 새로운 데이터가 들어올 때마다 과거 24개월치를 대상으로 반복 수행 (롤링 방식)
# weighted_mses = np.zeros(num_analysts)
# for i in range(num_analysts):
#     # (예측치 - 실제값)^2 으로 제곱 오차 계산
#     squared_errors = (historical_analyst_forecasts[:, i] - historical_actual_outcomes)**2
#     # 시간 가중치를 적용하여 MSE 계산 (단순 평균 대신 가중합 사용)
#     weighted_mses[i] = np.sum(normalized_time_weights * squared_errors)

# print(f"시간 가중 방식을 통해 계산된 애널리스트별 MSE:\n{weighted_mses}\n")
