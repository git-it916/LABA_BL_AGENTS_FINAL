import pandas as pd
import numpy as np
from IPython.display import display

def calculating_performance(results):
    df = pd.DataFrame(results)
    df['forecast_date'] = pd.to_datetime(df['forecast_date'])
    df.set_index('forecast_date', inplace=True)

    # 1. sharpe ratio(연율화)
    df['sharpe_ratio of benchmark1'] = (df['performance_benchmark1'].mean() / df['performance_benchmark1'].std()) * np.sqrt(12)
    df['sharpe_ratio of benchmark2'] = (df['performance_benchmark2'].mean() / df['performance_benchmark2'].std()) * np.sqrt(12)
    df['sharpe_ratio of aiportfolio'] = (df['performance_aiportfolio'].mean() / df['performance_aiportfolio'].std()) * np.sqrt(12)

    # 2. 누적수익률(CAGR)
    df['cumulative_benchmark1'] = (1 + df['performance_benchmark1']).cumprod()
    df['cumulative_benchmark2'] = (1 + df['performance_benchmark2']).cumprod()
    df['cumulative_aiportfolio'] = (1 + df['performance_aiportfolio']).cumprod()

    # 3. MDD
    rolling_max_1 = df['cumulative_benchmark1'].max()
    df['drawdown_benchmark1'] = (df['cumulative_benchmark1'] - rolling_max_1) / rolling_max_1
    df['MDD_benchmark1'] = df['drawdown_benchmark1'].min()
    df.drop('drawdown_benchmark1', axis=1, inplace=True)
    rolling_max_2 = df['cumulative_benchmark2'].max()
    df['drawdown_benchmark2'] = (df['cumulative_benchmark2'] - rolling_max_2) / rolling_max_2
    df['MDD_benchmark2'] = df['drawdown_benchmark2'].min()
    df.drop('drawdown_benchmark2', axis=1, inplace=True)
    rolling_max_a = df['cumulative_aiportfolio'].max()
    df['drawdown_aiportfolio'] = (df['cumulative_aiportfolio'] - rolling_max_a) / rolling_max_a
    df['MDD_aiportfolio'] = df['drawdown_aiportfolio'].min()
    df.drop('drawdown_aiportfolio', axis=1, inplace=True)

    # 4. VaR/CVaR
    confidence_level = 0.95

    var_benchmark1 = df['performance_benchmark1'].quantile(1 - confidence_level)
    df['var_benchmark1'] = var_benchmark1
    var_benchmark2 = df['performance_benchmark2'].quantile(1 - confidence_level)
    df['var_benchmark2'] = var_benchmark2
    var_aiportfolio = df['performance_aiportfolio'].quantile(1 - confidence_level)
    df['var_aiportfolio'] = var_aiportfolio

    cvar_benchmark1 = df['performance_benchmark1'][df['MDD_benchmark1'] <= var_benchmark1].mean()
    df['cvar_benchmark1'] = cvar_benchmark1
    cvar_benchmark2 = df['performance_benchmark2'][df['MDD_benchmark2'] <= var_benchmark2].mean()
    df['cvar_benchmark2'] = cvar_benchmark2
    cvar_aiportfolio = df['performance_aiportfolio'][df['MDD_aiportfolio'] <= var_aiportfolio].mean()
    df['cvar_aiportfolio'] = cvar_aiportfolio

    final_benchmark1 = {'sharpe ratio': df['sharpe_ratio of benchmark1'].tail(1),
                        'CAGR': df['cumulative_benchmark1'].tail(1),
                        'MDD': df['MDD_benchmark1'].tail(1),
                        'VaR': df['var_benchmark1'].tail(1),
                        'CVaR': df['cvar_benchmark1'].tail(1)
                        }
    final_benchmark2 = {'sharpe ratio': df['sharpe_ratio of benchmark2'].tail(1),
                        'CAGR': df['cumulative_benchmark2'].tail(1),
                        'MDD': df['MDD_benchmark2'].tail(1),
                        'VaR': df['var_benchmark2'].tail(1),
                        'CVaR': df['cvar_benchmark2'].tail(1)
                        }
    final_aiportfolio = {'sharpe ratio': df['sharpe_ratio of aiportfolio'].tail(1),
                        'CAGR': df['cumulative_aiportfolio'].tail(1),
                        'MDD': df['MDD_aiportfolio'].tail(1),
                        'VaR': df['var_aiportfolio'].tail(1),
                        'CVaR': df['cvar_aiportfolio'].tail(1)
                        }

    return final_benchmark1, final_benchmark2, final_aiportfolio