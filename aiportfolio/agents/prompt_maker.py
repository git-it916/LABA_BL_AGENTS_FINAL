import pandas as pd
import numpy as np
import os
import json

from aiportfolio.agents.prepare.calculating_indicator import indicator

# python -m aiportfolio.agents.prompt_maker

def making_INPUT(end_date):
    data = indicator()
    
    sector_data_list = [
        {
            "sector": "Energy",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Materials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Industrials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Consumer Discretionary",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Consumer Staples",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Health Care",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Financials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Information Technology",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Communication Services",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Utilities",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'CAGR'].iloc[0]}"
        },
        {
            "sector": "Real Estate",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'return_list'].iloc[0]}",
            "Mean reversion signal (12-month z-score)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'z-score'].iloc[0]}",
            "12-month volatility (or Trailing 12-month volatility)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'volatility'].iloc[0]}",
            "12-month trend strength": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'trend_strength'].iloc[0]}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'CAGR'].iloc[0]}"
        }
        ]
    return sector_data_list

def making_user_prompt(end_date):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'user_prompt.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    except FileNotFoundError:
        print("오류: 해당 경로에 파일이 없습니다.")
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    a = making_INPUT(end_date=end_date)
    data_string = json.dumps(a, indent=2)

    final_output = content.replace("<INPUT>", data_string)

    return final_output

def making_system_prompt():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'system_prompt.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    except FileNotFoundError:
        print("오류: 해당 경로에 파일이 없습니다.")
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
    
    return content

'''
# 예시 데이터프레임
def example():
    dates = pd.date_range(start='2024-04-30', end='2024-11-30', freq='ME')
    sectors = [
        "Energy", "Materials", "Industrials", "Consumer Discretionary", 
        "Consumer Staples", "Health Care", "Financials", "Information Technology", 
        "Communication Services", "Utilities", "Real Estate"
    ]
    data = []
    np.random.seed(42)  # 재현성을 위한 시드 설정
    for date in dates:
        for sector in sectors:
            row = {
                'date': date,
                'gsector': sector,
                'return_list': np.random.randn(12).tolist(),  # 12개의 랜덤 값을 가진 리스트
                'z-score': np.random.randn(),  # 표준정규분포
                'volatility': np.random.uniform(0.1, 0.5),  # 0.1~0.5 사이의 변동성
                'trend_strength': np.random.uniform(0, 1),  # 0~1 사이의 추세 강도
                'CAGR': np.random.uniform(-0.2, 0.3)  # -20%~30% 사이의 CAGR
            }
            data.append(row)
    calculate_return = pd.DataFrame(data)
    return calculate_return
'''