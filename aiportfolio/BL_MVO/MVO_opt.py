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
    '''
    # 효용함수 최적화 포트폴리오
    def optimize_utility(self, gamma):
        gamma = gamma
        mu_BL = self.mu_BL
        tausigma = self.tausigma
        SECTOR = self.SECTOR

        tausigma_inv = np.linalg.inv(tausigma)
        w_dir = tausigma_inv @ mu_BL
    
        w_delta = (1.0 / gamma) * w_dir
        w_delta_norm = w_delta / np.sum(w_delta)

        print("w_delta_norm:\n", pd.Series(w_delta_norm.flatten(), index=SECTOR))
        
        return w_delta_norm

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
    '''
    
    # 효용함수 최적화 포트폴리오
    def optimize_utility_1(self, gamma):
        # Objective function to minimize (negative of the utility function)
        SECTOR = self.SECTOR
        def objective_function(weights, mu, sigma, gamma):
            portfolio_return = np.dot(weights.T, mu)
            portfolio_variance = np.dot(weights.T, np.dot(sigma, weights))
            utility = portfolio_return - 0.5 * gamma * portfolio_variance
            return -utility # Minimize the negative utility

        # Define constraints
        constraints = ({'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1})
        
        # Define bounds for long-only constraint (weights >= 0)
        bounds = tuple((0.0, None) for asset in range(self.n_assets))
        
        # Initial guess for weights
        initial_weights = np.ones(self.n_assets) / self.n_assets

        # Perform the optimization
        result = minimize(
            objective_function, 
            initial_weights, 
            args=(self.mu_BL, self.tausigma, gamma),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        w_delta_norm = result.x.reshape(-1, 1)
        # print("w_delta_norm:\n", pd.Series(w_delta_norm.flatten(), index=SECTOR).to_string(float_format='{:,.4f}'.format))
        
        return w_delta_norm

    # 탄젠트 최적화 포트폴리오(지금은 rf=0 가정, 원래는 rf 들어가야 함) 
    def optimize_tangency_1(self):
        SECTOR = self.SECTOR
        # Objective function to minimize (negative of the Sharpe Ratio)
        def objective_function(weights, mu, sigma):
            portfolio_return = np.dot(weights.T, mu)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(sigma, weights)))
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
        # print("w_tan:\n", pd.Series(w_tan.flatten(), index=SECTOR).to_string(float_format='{:,.4f}'.format))

        return w_tan