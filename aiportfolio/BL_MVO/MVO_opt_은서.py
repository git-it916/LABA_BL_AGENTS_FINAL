import numpy as np
import pandas as pd
from typing import Iterable, Optional, Tuple
from scipy.optimize import minimize


class MVO_Optimizer:
    """
    실전형 MVO Optimizer
    - BL 출력(초과수익 or 절대수익)과 공분산을 받아 롱온리/상한/합계=1 제약 하에
      (1) 효용 최대화, (2) 샤프비율(탄젠시) 최대화 포트폴리오를 구한다.
    - rf(무위험수익률) 입력을 지원하고, 공분산 정칙화(ridge)로 수치안정성을 높였다.
    """

    def __init__(
        self,
        mu_BL,                     # pd.Series or np.ndarray (N,) or (N,1)
        tausigma,                  # np.ndarray (N,N) : 공분산(동일 주기)
        SECTOR: Iterable[str],     # 섹터/자산 이름 리스트 길이 N
        *,
        mu_is_excess: bool = True,  # True면 mu_BL이 '초과수익' (BL posterior 보통 여기에 해당)
        ridge: float = 1e-8,         # 공분산 대각 정칙화(수치안정)
        verbose: bool = False
    ):

        # ---- 입력 정리 (shape/정렬) ----
        # mu: (N,) 1D
        mu_arr = np.asarray(mu_BL.values if isinstance(mu_BL, pd.Series) else mu_BL, dtype=float)
        mu_arr = mu_arr.reshape(-1)
        self.mu = mu_arr

        # sigma: (N,N) + ridge
        sigma = np.asarray(tausigma, dtype=float)
        if ridge and ridge > 0:
            sigma = sigma + ridge * np.eye(sigma.shape[0])
        self.sigma = sigma

        # 이름/차원 저장 + 안전 검사 
        self.SECTOR = list(SECTOR)
        self.n_assets = len(self.SECTOR)
        assert self.sigma.shape == (self.n_assets, self.n_assets), "sigma 크기가 (N,N)이어야 합니다."
        assert self.mu.shape[0] == self.n_assets, "mu 길이와 SECTOR 길이가 달라요."

        self.mu_is_excess = mu_is_excess
        self.verbose = verbose

    # ---------- 진단용 계산 ----------
    def _stats(self, w: np.ndarray, rf: float = 0.0) -> dict:
        """
        포트폴리오 통계(기대수익, 변동성, 샤프)를 dict로 반환.
        - mu가 '초과수익'이면 rf=0에서 기대수익=초과수익.
        - mu가 '절대수익'이면 기대초과수익 = 기대수익 - rf.
        """
        w = w.reshape(-1)
        mu = self.mu
        ret = float(w @ mu)                 # 기대수익(입력 mu 기준)
        var = float(w @ (self.sigma @ w))
        vol = float(np.sqrt(max(var, 0.0)))
        # 초과수익 처리
        if self.mu_is_excess:
            ex_ret = ret                    # 이미 초과수익
        else:
            ex_ret = ret - rf               # 절대수익이면 rf를 빼 초과수익으로
        sharpe = ex_ret / (vol + 1e-12)
        return {"return": ret, "excess_return": ex_ret, "vol": vol, "sharpe": sharpe}

    # ---------- 공통 제약/바운드 ----------
    def _build_constraints_bounds(
        self,
        long_only: bool,
        fully_invested: bool,
        max_weight: Optional[float],
        custom_bounds: Optional[Iterable[Tuple[Optional[float], Optional[float]]]] = None,
    ):
        # 합계=1 제약
        constraints = ()
        if fully_invested:
            constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},)

        # 바운드
        if custom_bounds is not None:
            bounds = tuple(custom_bounds)
            assert len(bounds) == self.n_assets, "custom_bounds 길이가 자산 수와 달라요."
        else:
            if long_only:
                hi = 1.0 if max_weight is None else float(max_weight)
                bounds = tuple((0.0, hi) for _ in range(self.n_assets))
            else:
                # 공매도 허용: 상·하한 미지정 (필요시 max_weight로 상한만 둘 수 있음)
                hi = None if max_weight is None else float(max_weight)
                bounds = tuple((None, hi) for _ in range(self.n_assets))
        return constraints, bounds

    # ---------- 1) 효용 최대화 (제약 포함) ----------
    def optimize_utility_1(
        self,
        gamma: float,          # 리스크를 얼마나 싫어하는지(크면 위험 벌점↑)
        *,
        long_only: bool = True,   # 공매도 금지(비중 음수 금지)
        fully_invested: bool = True,      # 비중 합계 = 1 (현금 잔여 0)
        max_weight: Optional[float] = 1.0,
        custom_bounds: Optional[Iterable[Tuple[Optional[float], Optional[float]]]] = None,
        maxiter: int = 1000,
        ftol: float = 1e-12,
        rf: float = 0.0,  # 참고: fully_invested=True이면 rf 상수항은 해에 영향 거의 없음
        return_stats: bool = False,
    ):
        """
        maximize  μᵀw - (γ/2) wᵀΣw   (SLSQP)
        - 디폴트: 롱온리, 합계=1, 개별 상한 max_weight(=1.0)
        - mu가 절대수익이면 그대로 사용, 초과수익이면 그대로 사용(합계=1이면 rf는 상수항)
        """
        mu = self.mu
        Sigma = self.sigma

        def neg_utility(w):
            # 효용 = 기대수익 - 0.5*gamma*분산
            # (합계=1이면 rf는 상수항이라 해에 영향 없음)
            ret = float(w @ mu)
            var = float(w @ (Sigma @ w))
            return -(ret - 0.5 * gamma * var)

        constraints, bounds = self._build_constraints_bounds(
            long_only=long_only, fully_invested=fully_invested,
            max_weight=max_weight, custom_bounds=custom_bounds
        )
        w0 = np.ones(self.n_assets) / self.n_assets

        res = minimize(
            neg_utility, w0, method='SLSQP',
            bounds=bounds, constraints=constraints,
            options={'maxiter': maxiter, 'ftol': ftol, 'disp': False}
        )
        if not res.success:
            raise RuntimeError(f"[optimize_utility_1] 최적화 실패: {res.message}")

        w = res.x.reshape(-1, 1)

        if self.verbose or return_stats:
            stats = self._stats(w, rf=rf)
            if self.verbose:
                print("utility_constrained weights:\n",
                      pd.Series(w.flatten(), index=self.SECTOR).to_string(float_format=lambda x: f"{x:,.4f}"))
                print("utility_constrained stats:", stats)
            if return_stats:
                return w, stats
        return w

    # ---------- 2) 탄젠시(샤프) 최대화 (제약 포함, rf 반영) ----------
    def optimize_tangency_1(
        self,
        *,
        rf: float = 0.0,             # 무위험수익률(μ와 같은 '주기' 단위로!)
        long_only: bool = True,     # 공매도 금지(비중 음수 불가)
        fully_invested: bool = True,
        max_weight: Optional[float] = 1.0,    # 개별 비중 상한
        custom_bounds: Optional[Iterable[Tuple[Optional[float], Optional[float]]]] = None,
        maxiter: int = 1000,
        ftol: float = 1e-12,
        return_stats: bool = False,
    ):
        """
        maximize  Sharpe = ( (μ - rf)ᵀw ) / sqrt( wᵀΣw )
        - mu_is_excess=True(기본)면 (μ-rf) 대신 μ만 쓰면 동일
        - 롱온리/합계=1/개별 상한 기본 활성화
        """
        Sigma = self.sigma
        # 초과수익 벡터 준비
        if self.mu_is_excess:
            mu_ex = self.mu
        else:
            mu_ex = self.mu - rf  # 절대수익이면 rf를 빼서 초과수익으로

        def neg_sharpe(w):
            ret = float(w @ mu_ex)
            vol = float(np.sqrt(max(w @ (Sigma @ w), 0.0) + 1e-12))
            return -(ret / vol)

        constraints, bounds = self._build_constraints_bounds(
            long_only=long_only, fully_invested=fully_invested,
            max_weight=max_weight, custom_bounds=custom_bounds
        )
        w0 = np.ones(self.n_assets) / self.n_assets

        res = minimize(
            neg_sharpe, w0, method='SLSQP',
            bounds=bounds, constraints=constraints,
            options={'maxiter': maxiter, 'ftol': ftol, 'disp': False}
        )
        if not res.success:
            raise RuntimeError(f"[optimize_tangency_1] 최적화 실패: {res.message}")

        w = res.x.reshape(-1, 1)

        if self.verbose or return_stats:
            stats = self._stats(w, rf=rf)  # 초과·샤프 진단
            if self.verbose:
                print("tangency_constrained weights:\n",
                      pd.Series(w.flatten(), index=self.SECTOR).to_string(float_format=lambda x: f"{x:,.4f}"))
                print("tangency_constrained stats:", stats)
            if return_stats:
                return w, stats
        return w
