import numpy as np
import pandas as pd
from typing import Tuple, Optional

# P: 자산 식별 견해 행렬 (K*N)
# omega: 견해 불확실성 공분산 행렬 (K*K)
# Q: 투자자 견해 초과수익률 벡텨 (K*1)

class BlackLittermanMatrixGenerator:
    """
    블랙 리터만 모델에 필요한 행렬들을 자동 생성하는 클래스
    """
    
    def __init__(self, n_assets: int = 11):
        """
        Parameters:
        n_assets (int): 자산의 개수 (기본값: 11)
        """
        self.n_assets = n_assets
           
    def generate_view_returns(self, k_views: int, 
                            return_range: Tuple[float, float] = (-0.05, 0.05)) -> np.ndarray:
        """
        견해 수익률 행렬 Q (K x 1) 생성
        
        Parameters:
        k_views (int): 견해의 개수
        return_range (tuple): 수익률 범위 (최소, 최대)
        
        Returns:
        np.ndarray: 견해 수익률 행렬 (K x 1)
        """
        min_return, max_return = return_range
        Q = np.random.uniform(min_return, max_return, size=(k_views, 1))
        return Q
    
    def generate_picking_matrix(self, k_views: int, 
                              view_type: str = 'mixed') -> np.ndarray:
        """
        피킹 행렬 P (K x N) 생성
        
        Parameters:
        k_views (int): 견해의 개수
        view_type (str): 견해 유형
            - 'absolute': 절대 견해 (각 행에 하나의 자산만 1)
            - 'relative': 상대 견해 (각 행에 두 자산이 1, -1)
            - 'mixed': 혼합 견해 (절대 + 상대 견해)
            - 'portfolio': 포트폴리오 견해 (여러 자산에 대한 가중치)
        
        Returns:
        np.ndarray: 피킹 행렬 (K x N)
        """
        P = np.zeros((k_views, self.n_assets))
        
        if view_type == 'absolute':
            # 절대 견해: 각 견해마다 하나의 자산 선택
            for i in range(k_views):
                asset_idx = np.random.randint(0, self.n_assets)
                P[i, asset_idx] = 1.0
                
        elif view_type == 'relative':
            # 상대 견해: 두 자산 간의 상대적 성과
            for i in range(k_views):
                asset_indices = np.random.choice(self.n_assets, size=2, replace=False)
                P[i, asset_indices[0]] = 1.0
                P[i, asset_indices[1]] = -1.0
                
        elif view_type == 'mixed':
            # 혼합 견해: 절대 견해와 상대 견해를 섞음
            for i in range(k_views):
                if np.random.random() < 0.5:  # 50% 확률로 절대 견해
                    asset_idx = np.random.randint(0, self.n_assets)
                    P[i, asset_idx] = 1.0
                else:  # 50% 확률로 상대 견해
                    asset_indices = np.random.choice(self.n_assets, size=2, replace=False)
                    P[i, asset_indices[0]] = 1.0
                    P[i, asset_indices[1]] = -1.0
                    
        elif view_type == 'portfolio':
            # 포트폴리오 견해: 여러 자산에 대한 가중치
            for i in range(k_views):
                # 2-4개의 자산 선택
                n_assets_in_view = np.random.randint(2, min(5, self.n_assets + 1))
                asset_indices = np.random.choice(self.n_assets, size=n_assets_in_view, replace=False)
                
                # 가중치 생성 (합이 0이 되도록)
                weights = np.random.uniform(-1, 1, size=n_assets_in_view)
                weights = weights - np.mean(weights)  # 평균을 0으로 만듦
                
                P[i, asset_indices] = weights
        
        return P
    
    def generate_view_covariance(self, k_views: int, 
                               uncertainty_level: str = 'medium',
                               correlation_strength: str = 'low') -> np.ndarray:
        """
        견해 공분산 행렬 Ω (K x K) 생성
        
        Parameters:
        k_views (int): 견해의 개수
        uncertainty_level (str): 불확실성 수준 ('low', 'medium', 'high')
        correlation_strength (str): 견해 간 상관관계 강도 ('low', 'medium', 'high')
        
        Returns:
        np.ndarray: 견해 공분산 행렬 (K x K)
        """
        # 불확실성 수준에 따른 분산 설정
        if uncertainty_level == 'low':
            base_variance = 0.0001  # 0.01^2
        elif uncertainty_level == 'medium':
            base_variance = 0.0004  # 0.02^2
        else:  # high
            base_variance = 0.0009  # 0.03^2
        
        # 대각선 원소 (분산) 생성
        variances = np.random.uniform(base_variance * 0.5, base_variance * 1.5, k_views)
        
        # 상관계수 강도 설정
        if correlation_strength == 'low':
            corr_range = (0, 0.3)
        elif correlation_strength == 'medium':
            corr_range = (0, 0.5)
        else:  # high
            corr_range = (0, 0.7)
        
        # 상관계수 행렬 생성
        omega = np.diag(variances)
        
        if k_views > 1:
            for i in range(k_views):
                for j in range(i + 1, k_views):
                    # 랜덤 상관계수 생성
                    corr = np.random.uniform(corr_range[0], corr_range[1])
                    if np.random.random() < 0.3:  # 30% 확률로 음의 상관관계
                        corr = -corr
                    
                    # 공분산 계산
                    cov = corr * np.sqrt(variances[i] * variances[j])
                    omega[i, j] = cov
                    omega[j, i] = cov
        
        return omega
    
    def generate_all_matrices(self, k_views: int,
                            view_type: str = 'mixed',
                            uncertainty_level: str = 'medium',
                            correlation_strength: str = 'low',
                            return_range: Tuple[float, float] = (-0.05, 0.05)) -> dict:
        """
        모든 블랙 리터만 행렬들을 한번에 생성
        
        Parameters:
        k_views (int): 견해의 개수
        view_type (str): 견해 유형
        uncertainty_level (str): 불확실성 수준
        correlation_strength (str): 견해 간 상관관계 강도
        return_range (tuple): 수익률 범위
        
        Returns:
        dict: 생성된 행렬들과 메타데이터
        """
        Q = self.generate_view_returns(k_views, return_range)
        P = self.generate_picking_matrix(k_views, view_type)
        Omega = self.generate_view_covariance(k_views, uncertainty_level, correlation_strength)
        
        return {
            'Q': Q,
            'P': P,
            'Omega': Omega,
            'dimensions': {
                'K': k_views,
                'N': self.n_assets,
                'Q_shape': Q.shape,
                'P_shape': P.shape,
                'Omega_shape': Omega.shape
            }
        }
    
    def display_matrices(self, matrices: dict, precision: int = 4):
        """
        생성된 행렬들을 보기 좋게 출력
        
        Parameters:
        matrices (dict): generate_all_matrices()의 결과
        precision (int): 소수점 자릿수
        """
        print("=" * 60)
        print(f"블랙 리터만 모델 행렬 생성 결과")
        print("=" * 60)
        print(f"견해 개수 (K): {matrices['dimensions']['K']}")
        print(f"자산 개수 (N): {matrices['dimensions']['N']}")
        print()
        
        print("1. 견해 수익률 행렬 Q (K × 1):")
        print("-" * 30)
        Q_df = pd.DataFrame(matrices['Q'], 
                           index=[f'View_{i+1}' for i in range(matrices['dimensions']['K'])],
                           columns=['Expected_Return'])
        print(Q_df.round(precision))
        print()
        
        print("2. 피킹 행렬 P (K × N):")
        print("-" * 30)
        P_df = pd.DataFrame(matrices['P'],
                           index=[f'View_{i+1}' for i in range(matrices['dimensions']['K'])],
                           columns=[f'Asset_{i+1}' for i in range(matrices['dimensions']['N'])])
        print(P_df.round(precision))
        print()
        
        print("3. 견해 공분산 행렬 Ω (K × K):")
        print("-" * 30)
        Omega_df = pd.DataFrame(matrices['Omega'],
                               index=[f'View_{i+1}' for i in range(matrices['dimensions']['K'])],
                               columns=[f'View_{i+1}' for i in range(matrices['dimensions']['K'])])
        print(Omega_df.round(precision))
        print()