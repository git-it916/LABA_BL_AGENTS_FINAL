import pandas as pd
import numpy as np
from datetime import datetime
from aiportfolio.BL_MVO.prepare.sector_excess_return import final

# N: 자산 개수 (11 GICS sectors)
# K: 견해 개수
# sigma: 초과수익률 공분산 행렬 (N×N)
# pi: 내재 시장 균형 초과수익률 벡터 (N×1)

class Market_Params:
    """
    Calculate market parameters for Black-Litterman model

    This class computes the equilibrium market parameters required for
    the Black-Litterman model:

    - Pi (π): Equilibrium excess returns vector (N×1)
    - Sigma (Σ): Covariance matrix of returns (N×N)
    - Lambda (λ): Market risk aversion coefficient (scalar)
    - w_mkt: Market capitalization weights (N×1)

    Theoretical Foundation:
        Black & Litterman (1992) "Global Portfolio Optimization"
        He & Litterman (1999) "The Intuition Behind Black-Litterman Model Portfolios"
        Idzorek (2005) "A step-by-step guide to the Black-Litterman model"

    Attributes:
        df (pd.DataFrame): Preprocessed sector return data
        start_date (datetime): Start date for parameter estimation period
        end_date (datetime): End date (as of date for market weights)

    Methods:
        making_mu(): Calculate mean excess returns (for reference, not used in BL)
        making_sigma(): Calculate covariance matrix of excess returns
        making_w_mkt(): Calculate market capitalization weights
        making_lambda(): Calculate market risk aversion coefficient
        making_pi(): Calculate equilibrium excess returns (CAPM reverse-engineering)
    """
    def __init__(self, start_date, end_date):
        """
        Initialize Market_Params with date range

        Args:
            start_date (datetime): Start date for parameter estimation
            end_date (datetime): End date (as of date for market weights)
        """
        self.df = final()
        self.start_date = start_date
        self.end_date = end_date

    def making_mu(self):
        """
        Calculate mean excess returns (μ)

        Note: This is for reference only. Black-Litterman model uses
        equilibrium returns (π) derived from CAPM, not historical mean.

        Returns:
            pd.Series: Mean excess returns by sector (N×1)
        """
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        mu = filtered_df.groupby('gsector')['sector_excess_return'].mean()
        return mu

    def making_sigma(self):
        """
        Calculate covariance matrix of excess returns (Σ)

        Formula:
            Σ_ij = Cov(R_i - R_f, R_j - R_f)
                 = 1/(T-1) × Σ_t[(R_i,t - μ_i)(R_j,t - μ_j)]

        Uses sample covariance (Pandas .cov() with ddof=1)

        Returns:
            tuple: (sigma, sectors)
                - sigma (pd.DataFrame): Covariance matrix (N×N)
                - sectors (list): Sector codes in order
        """
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        pivot_filtered_df = filtered_df.pivot_table(index='date', columns='gsector', values='sector_excess_return')
        sigma = pivot_filtered_df.cov()
        sectors = sigma.columns.tolist()

        # 공분산 행렬의 인덱스가 정해진 순서와 일치하지 않는다면 에러 발생
        expected_index = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        if not isinstance(sigma, pd.DataFrame):
            raise TypeError("sigma[0] must be a pandas DataFrame (covariance matrix)")

        if list(sigma.index) != expected_index or list(sigma.columns) != expected_index:
            raise ValueError(
                f"Covariance matrix index/columns mismatch.\n"
                f"Expected: {expected_index}\n"
                f"Got index: {list(sigma.index)}\n"
                f"Got columns: {list(sigma.columns)}"
            )

        return sigma, sectors
    
    def making_sigma_for_optimize(self):
        '''
        샤프 최적화 시의 샤프비율 분모용 공분산
        '''
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()
        pivot_filtered_df = filtered_df.pivot_table(index='date', columns='gsector', values='sector_return')
        sigma_for_optimize = pivot_filtered_df.cov()
        sectors = sigma_for_optimize.columns.tolist()

        # 공분산 행렬의 인덱스가 정해진 순서와 일치하지 않는다면 에러 발생
        expected_index = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        if not isinstance(sigma_for_optimize, pd.DataFrame):
            raise TypeError("sigma[0] must be a pandas DataFrame (covariance matrix)")

        if list(sigma_for_optimize.index) != expected_index or list(sigma_for_optimize.columns) != expected_index:
            raise ValueError(
                f"Covariance matrix index/columns mismatch.\n"
                f"Expected: {expected_index}\n"
                f"Got index: {list(sigma_for_optimize.index)}\n"
                f"Got columns: {list(sigma_for_optimize.columns)}"
            )

        return sigma_for_optimize, sectors

    def making_w_mkt(self, sigma_sectors):
        """
        Calculate market capitalization weights (w_mkt)

        Formula:
            w_i = Market_Cap_i / Σ(Market_Cap)

        Uses end_date (as of date) market capitalization.

        Args:
            sigma_sectors (list): Sector codes from sigma matrix (for validation)

        Returns:
            tuple: (w_mkt, sectors)
                - w_mkt (pd.Series): Market cap weights (N×1)
                - sectors (list): Sector codes in order
        """
        end_month_str = self.end_date.strftime('%Y-%m')
        filtered_df = self.df[self.df['date'].dt.strftime('%Y-%m') == end_month_str].copy()

        # 계산의 정확성을 위해 gsector가 11개인지 확인하고 인덱스로 설정
        if len(filtered_df['gsector'].unique()) == 11:
            filtered_df = filtered_df.set_index('gsector')
        else:
            raise ValueError(f"gsector의 고유값 개수가 11이 아닙니다. (현재 {len(filtered_df['gsector'].unique())}개)")

        total_mkt_cap = filtered_df['sector_mktcap'].sum()
        
        # 시장 가중치 계산
        w_mkt = filtered_df['sector_mktcap'] / total_mkt_cap
        
        # 계산의 정확성을 위해 w_mkt.index와 sigma_sectors 리스트 비교
        if (w_mkt.index == sigma_sectors).all():
            pass
        else:
            raise ValueError(
                f"w_mkt.index와 sectors가 일치하지 않습니다.\n"
                f"w_mkt.index: {w_mkt.index}\n"
                f"sectors: {sigma_sectors}"
            )
        
        # 섹터 반환
        sectors = w_mkt.index.tolist()

        return w_mkt, sectors
    
    def making_lambda(self):
        """
        Calculate market risk aversion coefficient (λ)

        Theoretical Foundation:
            λ = E[R_m - R_f] / Var(R_m)

        This is derived from CAPM:
            E[R_m] - R_f = λ × σ_m^2

        Where:
            - E[R_m - R_f] = Expected market excess return
            - Var(R_m) = Market return variance
            - λ = Market risk aversion coefficient

        Returns:
            float: Market risk aversion coefficient (lambda)
        """
        filtered_df = self.df[(self.df['date'] >= self.start_date) & (self.df['date'] <= self.end_date)].copy()

        # 시총가중 수익률 생성
        filtered_df["_ret_x_cap_1"] = filtered_df["sector_excess_return"] * filtered_df["sector_prevmktcap"] # excess_return
        filtered_df["_ret_x_cap_2"] = filtered_df["sector_return"] * filtered_df["sector_prevmktcap"] # 그냥 수익률
        agg = (
            filtered_df.groupby("date", dropna=False)
                .agg(total_mktcap=("sector_prevmktcap", "sum"),
                    ret_x_cap_1_sum=("_ret_x_cap_1", "sum"),
                    ret_x_cap_2_sum=("_ret_x_cap_2", "sum"))
                .reset_index()
        )
        mask = agg["total_mktcap"] != 0
        agg["total_excess_return"] = agg["ret_x_cap_1_sum"].div(agg["total_mktcap"]).where(mask)
        agg["total_return"]        = agg["ret_x_cap_2_sum"].div(agg["total_mktcap"]).where(mask)
        agg = agg.drop(columns=["ret_x_cap_1_sum", "ret_x_cap_2_sum"])  # 중간열 제거

        # λ (lambda) 계산
        ret_mean = agg['total_excess_return'].mean()  # E[R_m - R_f]
        ret_variance = agg['total_return'].var()      # Var(R_m)
        lambda_mkt = ret_mean / ret_variance
        return lambda_mkt

    def making_pi(self):
        """
        Calculate equilibrium excess returns (π)

        Theoretical Foundation:
            π = λ × Σ × w_mkt
    
        This reverse-engineers the CAPM equilibrium:
            E[R_i] - R_f = β_i × (E[R_m] - R_f)
                         = β_i × λ × σ_m^2
                         = λ × Cov(R_i, R_m)
                         = λ × [Σ × w_mkt]_i

        Where:
            - λ = Market risk aversion coefficient
            - Σ = Covariance matrix of returns (N×N)
            - w_mkt = Market capitalization weights (N×1)
            - π = Equilibrium excess returns (N×1)

        Returns:
            np.ndarray: Equilibrium excess returns vector (N×1)
        """
        sigma = self.making_sigma()
        w_mkt = self.making_w_mkt(sigma[1])
        lambda_mkt = self.making_lambda()  # 변수명 변경: delta → lambda_mkt
        pi = lambda_mkt * sigma[0].values @ w_mkt[0]

        return pi