import pandas as pd
import numpy as np
from IPython.display import display

def calculating_performance(results):
    df = pd.DataFrame(results)
    df['forecast_date'] = pd.to_datetime(df['forecast_date'])
    df.set_index('forecast_date', inplace=True)

    final_results = {}
    portfolios = [ 'benchmark2', 'aiportfolio']
    confidence_level = 0.95

    for port in portfolios:
        perf_col = f'performance_{port}'
        cum_col = f'cumulative_{port}'

        # 1. 누적수익률 (Cumulative Return)
        df[cum_col] = (1 + df[perf_col]).cumprod()
        final_cumulative_return = df[cum_col].iloc[-1] # 마지막 누적 수익률

        # 2. sharpe ratio (연율화)
        # (수익률이 0% 미만일 때 std()가 0이면 0으로 처리, 그 외는 nan 방지)
        if df[perf_col].std() == 0:
             sharpe_ratio = 0.0 if df[perf_col].mean() < 0 else np.nan
        else:
            sharpe_ratio = (df[perf_col].mean() / df[perf_col].std()) * np.sqrt(12)

        # 3. MDD (Maximum Drawdown)
        peak = df[cum_col].expanding().max()
        drawdown = (df[cum_col] - peak) / peak
        mdd = drawdown.min()

        # 4. VaR (Value at Risk)
        var = df[perf_col].quantile(1 - confidence_level)

        # 5. CVaR (Conditional VaR)
        cvar = df[perf_col][df[perf_col] <= var].mean()

        # 결과 저장
        final_results[port] = {
            'sharpe ratio': sharpe_ratio,
            'CAGR': final_cumulative_return, # 주석/키 이름은 원본 유지 (의미는 누적수익률)
            'MDD': mdd,
            'VaR': var,
            'CVaR': cvar
        }

    return final_results['benchmark1'], final_results['benchmark2'], final_results['aiportfolio']