import pandas as pd
import numpy as np
import os
import json

from aiportfolio.agents.prepare.Tier1_calculate import indicator

# python -m aiportfolio.agents.prompt_maker

def making_INPUT(end_date):
    """
    지정된 날짜의 섹터별 지표 데이터를 가져옵니다.

    Args:
        end_date: 데이터를 가져올 기준 날짜

    Returns:
        list: 11개 섹터의 지표 데이터 리스트
    """
    data = indicator()

    # 헬퍼 함수: 안전하게 데이터 가져오기 + 소수점 4자리 반올림
    def safe_get_value(sector, column):
        """섹터와 컬럼에 대한 값을 안전하게 가져오고 소수점 4자리로 반올림합니다."""
        filtered = data.loc[(data['date'] == end_date) & (data['gsector'] == sector), column]
        if len(filtered) == 0:
            print(f"[경고] {sector} 섹터의 {column} 데이터가 {end_date}에 없습니다. 'N/A'로 대체합니다.")
            return "N/A"

        value = filtered.iloc[0]

        # 리스트인 경우 (return_list)
        if isinstance(value, list):
            # return_list는 이미 소수점 단위 (0.0659 = 6.59%) → 그대로 반올림만
            return [round(float(x), 4) for x in value]
        # 숫자인 경우
        elif isinstance(value, (int, float, np.number)):
            # 모든 지표를 소수점 4자리로 반올림 (0.0001 = 0.01%)
            return round(float(value), 4)
        else:
            return value

    sector_data_list = [
        {
            "sector": "Energy",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Energy', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Energy', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Energy', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Energy', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Energy', 'CAGR')}"
        },
        {
            "sector": "Materials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Materials', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Materials', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Materials', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Materials', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Materials', 'CAGR')}"
        },
        {
            "sector": "Industrials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Industrials', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Industrials', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Industrials', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Industrials', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Industrials', 'CAGR')}"
        },
        {
            "sector": "Consumer Discretionary",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Consumer Discretionary', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Consumer Discretionary', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Consumer Discretionary', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Consumer Discretionary', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Consumer Discretionary', 'CAGR')}"
        },
        {
            "sector": "Consumer Staples",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Consumer Staples', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Consumer Staples', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Consumer Staples', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Consumer Staples', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Consumer Staples', 'CAGR')}"
        },
        {
            "sector": "Health Care",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Health Care', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Health Care', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Health Care', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Health Care', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Health Care', 'CAGR')}"
        },
        {
            "sector": "Financials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Financials', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Financials', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Financials', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Financials', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Financials', 'CAGR')}"
        },
        {
            "sector": "Information Technology",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Information Technology', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Information Technology', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Information Technology', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Information Technology', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Information Technology', 'CAGR')}"
        },
        {
            "sector": "Communication Services",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Communication Services', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Communication Services', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Communication Services', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Communication Services', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Communication Services', 'CAGR')}"
        },
        {
            "sector": "Utilities",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Utilities', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Utilities', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Utilities', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Utilities', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Utilities', 'CAGR')}"
        },
        {
            "sector": "Real Estate",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value('Real Estate', 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value('Real Estate', 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value('Real Estate', 'volatility')}",
            "12-month trend strength": f"{safe_get_value('Real Estate', 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value('Real Estate', 'CAGR')}"
        }
        ]
    return sector_data_list

def making_user_prompt(end_date):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'user_prompt_final.txt')

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
    file_path = os.path.join(base_path, 'prompt_template', 'system_prompt_1.txt')

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