import pandas as pd
import numpy as np
from scipy.optimize import minimize

class MVO_Optimizer:
    def __init__(self, mu_BL, tausigma, SECTOR):
        self.mu_BL = mu_BL.values.reshape(-1, 1)
        self.tausigma = tausigma
        self.SECTOR = SECTOR
        self.n_assets = len(SECTOR)

    # 아래는 롱온리랑 레버리지X 제약조건이 없어서 사용하지 않음

    # 탄젠트 최적화 포트폴리오(지금은 rf=0 가정, 원래는 rf 들어가야 함) 
    def optimize_tangency(self):
        mu_BL = self.mu_BL
        tausigma = self.tausigma
        SECTOR = self.SECTOR

        tausigma_inv = np.linalg.inv(tausigma)
        w_dir = tausigma_inv @ mu_BL
        w_tan = w_dir / np.sum(w_dir)

        print("w_tan:\n", pd.Series(w_tan.flatten(), index=SECTOR))

        return w_tan

    # 탄젠트 최적화 포트폴리오(지금은 rf=0 가정, 원래는 rf 들어가야 함) 
    def optimize_tangency_1(self):
        SECTOR = self.SECTOR
        # Objective function to minimize (negative of the Sharpe Ratio)
        def objective_function(weights, mu, sigma):
            portfolio_return = np.dot(weights.T, mu)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(sigma, weights)))
            # 분모가 0이 되는 경우를 방지
            if portfolio_volatility == 0:
                return 0
            sharpe_ratio = portfolio_return / portfolio_volatility
            return -sharpe_ratio # Minimize the negative Sharpe Ratio

        # Define constraints
        constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
        
        # Define bounds for long-only constraint
        bounds = tuple((0.0, None) for asset in range(self.n_assets))

        # Initial guess for weights
        initial_weights = np.ones(self.n_assets) / self.n_assets

        # Perform the optimization
        result = minimize(
            objective_function, 
            initial_weights, 
            args=(self.mu_BL, self.tausigma),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        w_tan = result.x.reshape(-1, 1)
                # 1. 소수점 셋째 자리에서 반올림
        w_tan_rounded = np.round(w_tan, 3)
        
        # 2. 반올림된 가중치의 합이 1이 되도록 다시 정규화
        w_tan_normalized = w_tan_rounded / np.sum(w_tan_rounded)
        
        # 3. 결과를 백분율(%) 형태로 출력 (소수점 둘째 자리까지)
        print("w_tan:\n", pd.Series(w_tan_normalized.flatten(), index=SECTOR).to_string(float_format='{:.2%}'.format))

        return w_tan_normalized