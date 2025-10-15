import pandas as pd
import numpy as np
from scipy.optimize import minimize

class MVO_Optimizer:
    def __init__(self, pi_new, tau, sigma, sectors):
        self.pi_new = pi_new.reshape(-1, 1)
        self.tau = tau
        self.sigma = sigma
        self.SECTOR = sectors
        self.n_assets = len(sectors)

    # 탄젠트 최적화 포트폴리오(지금은 rf=0 가정, 원래는 rf 들어가야 함) 
    def optimize_tangency(self):
        mu_BL = self.pi_new
        tausigma = self.tau * self.sigma
        SECTOR = self.SECTOR

        tausigma_inv = np.linalg.inv(tausigma)
        w_dir = tausigma_inv @ mu_BL
        w_tan = w_dir / np.sum(w_dir)

        print("w_tan:\n", pd.Series(w_tan.flatten(), index=SECTOR))

        return w_tan

    # 탄젠트 최적화 포트폴리오(지금은 rf=0 가정, 원래는 rf 들어가야 함) 
    def optimize_tangency_1(self):
        tausigma = self.tau * self.sigma
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
            args=(self.pi_new, tausigma),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        w_tan = result.x.reshape(-1, 1)
        
        # <<< 가중치 합이 1이 되도록 정규화하는 코드 추가 >>>
        w_tan = w_tan / np.sum(w_tan)
        
        print("w_tan:\n", pd.Series(w_tan.flatten(), index=SECTOR).to_string(float_format='{:,.4f}'.format))

        return w_tan