import pandas as pd
import numpy as np
from scipy.optimize import minimize

class MVO_Optimizer:
    def __init__(self, mu, sigma, sectors):
        self.mu = mu
        self.sigma = sigma
        self.SECTOR = sectors
        self.n_assets = len(sectors)

    # 탄젠트 최적화 포트폴리오 
    def optimize_tangency(self):
        mu_BL = self.mu
        sigma = self.sigma
        SECTOR = self.SECTOR

        sigma_inv = np.linalg.inv(sigma)
        w_dir = sigma_inv @ mu_BL
        w_tan = w_dir / np.sum(w_dir)

        print("w_tan:\n", pd.Series(w_tan.flatten(), index=SECTOR))

        return w_tan

    # 탄젠트 최적화 포트폴리오
    def optimize_tangency_1(self, return_original=False):
        """
        Optimize tangency portfolio using numerical optimization (SLSQP)

        Objective:
            Maximize Sharpe Ratio = (w^T·μ) / sqrt(w^T·Σ·w)

        Constraints:
            1. Σw_i = 1 (weights sum to 1)
            2. w_i ≥ 0 (long-only, no short selling)

        Theoretical Foundation:
            Markowitz (1952) "Portfolio Selection"

        Args:
            return_original (bool): If True, return both original and rounded weights

        Returns:
            If return_original=False:
                tuple: (w_tan_normalized, SECTOR)
            If return_original=True:
                dict: {
                    'weights_optimal': Original optimal weights (N×1),
                    'weights_rounded': Rounded and normalized weights (N×1),
                    'sectors': Sector list,
                    'sharpe_ratio_optimal': Sharpe ratio of original weights,
                    'sharpe_ratio_rounded': Sharpe ratio of rounded weights
                }
        """
        sigma = self.sigma
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

        def calculate_sharpe(weights, mu, sigma):
            """Calculate Sharpe Ratio for given weights"""
            portfolio_return = np.dot(weights.T, mu)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(sigma, weights)))
            if portfolio_volatility == 0:
                return 0
            return portfolio_return / portfolio_volatility

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
            args=(self.mu, sigma),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        w_tan_original = result.x.reshape(-1, 1)

        # 1. 소수점 셋째 자리에서 반올림
        w_tan_rounded = np.round(w_tan_original, 3)

        # 2. 반올림된 가중치의 합이 1이 되도록 다시 정규화
        w_tan_normalized = w_tan_rounded / np.sum(w_tan_rounded)

        if return_original:
            # Sharpe Ratio 계산
            sr_optimal = calculate_sharpe(w_tan_original.flatten(), self.mu.flatten(), sigma)
            sr_rounded = calculate_sharpe(w_tan_normalized.flatten(), self.mu.flatten(), sigma)

            return {
                'weights_optimal': w_tan_original,
                'weights_rounded': w_tan_normalized,
                'sectors': SECTOR,
                'sharpe_ratio_optimal': float(sr_optimal),
                'sharpe_ratio_rounded': float(sr_rounded),
                'sharpe_ratio_loss': float(sr_optimal - sr_rounded)
            }
        else:
            return w_tan_normalized, SECTOR