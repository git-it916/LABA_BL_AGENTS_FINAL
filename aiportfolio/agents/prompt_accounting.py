import pandas as pd
import numpy as np
import os
import json

from aiportfolio.agents.prepare.Tier2_calculate import calculate_accounting_indicator

# python -m aiportfolio.agents.prompt_accounting

def making_acc_INPUT(end_date):
    data = calculate_accounting_indicator()

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

    sectors = [
        "Energy", "Materials", "Industrials", "Consumer Discretionary",
        "Consumer Staples", "Health Care", "Financials", "Information Technology",
        "Communication Services", "Utilities", "Real Estate"
    ]

    sector_acc_data_list = []
    for sector in sectors:
        sector_acc_data_list.append({
            "sector": sector,
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": f"{safe_get_value(sector, 'return_list')}",
            "Mean reversion signal (12-month z-score)": f"{safe_get_value(sector, 'z-score')}",
            "12-month volatility (or Trailing 12-month volatility)": f"{safe_get_value(sector, 'volatility')}",
            "12-month trend strength": f"{safe_get_value(sector, 'trend_strength')}",
            "3-year CAGR (Compound Annual Growth Rate)": f"{safe_get_value(sector, 'CAGR')}"
        })

    return sector_acc_data_list

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

    a = making_acc_INPUT(end_date=end_date)
    data_string = json.dumps(a, indent=2)
    final_output = content.replace("<acc_INPUT>", data_string)

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
