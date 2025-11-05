import pandas as pd
import numpy as np
import os
import json

# [수정] 실제 'indicator' 함수를 import합니다.
from aiportfolio.agents.prepare.calculating_indicator import indicator

# python -m aiportfolio.agents.prompt_maker

def making_INPUT(end_date):
    
    # [수정] 실제 indicator() 함수를 호출합니다.
    data = indicator() 
    
    # [핵심] 날짜 비교를 위해 'end_date'와 'date' 컬럼을 datetime 객체로 통일
    try:
        data['date'] = pd.to_datetime(data['date'])
        end_date = pd.to_datetime(end_date)
    except Exception as e:
        print(f"Warning: Date conversion error in making_INPUT: {e}. Ensure 'end_date' format matches data['date'].")
        pass 

    # [핵심] f-string (f"...")을 제거하여 '숫자(Number)'와 '리스트(List)' 원본 타입으로 전달
    sector_data_list = [
        {
            "sector": "Energy",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Energy'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Materials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Materials'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Industrials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Industrials'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Consumer Discretionary",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Discretionary'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Consumer Staples",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Consumer Staples'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Health Care",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Health Care'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Financials",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Financials'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Information Technology",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Information Technology'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Communication Services",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Communication Services'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Utilities",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Utilities'), 'CAGR'].iloc[0]
        },
        {
            "sector": "Real Estate",
            "Recent 12-month monthly returns (or Trailing 12-month (TTM) monthly returns)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'return_list'].iloc[0],
            "Mean reversion signal (12-month z-score)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'z-score'].iloc[0],
            "12-month volatility (or Trailing 12-month volatility)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'volatility'].iloc[0],
            "12-month trend strength": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'trend_strength'].iloc[0],
            "3-year CAGR (Compound Annual Growth Rate)": data.loc[(data['date'] == end_date) & (data['gsector'] == 'Real Estate'), 'CAGR'].iloc[0]
        }
    ]
    
    # [참고] .iloc[0]은 해당 날짜/섹터에 데이터가 없으면 오류를 발생시킵니다.
    # 실제 운영 시에는 try-except나 .empty 검사를 통해
    # 데이터가 없는 섹터를 제외(filter)하는 로직을 추가하는 것이 더 견고합니다.

    return sector_data_list

def making_user_prompt(end_date):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'user_prompt_1.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"오류: '{file_path}' 경로에 파일이 없습니다.")
        return None 
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None 

    # --- [핵심 수정] 날짜 계산 로직 추가 ---
    try:
        # 1. end_date (문자열 또는 Timestamp)를 Timestamp 객체로 변환
        end_date_ts = pd.to_datetime(end_date)
    except Exception as e:
        print(f"Error converting end_date '{end_date}' to datetime: {e}")
        return None

    # 2. Analysis As-Of Date 문자열 생성 (예: '2024-05-31')
    analysis_date_str = end_date_ts.strftime('%Y-%m-%d')
    
    # 3. Target View Month 문자열 생성 (다음 달, 예: '2024-06')
    target_month_ts = end_date_ts + pd.DateOffset(months=1)
    target_month_str = target_month_ts.strftime('%Y-%m')
    # --- [날짜 계산 끝] ---

    # [핵심] 수정된 making_INPUT 함수 호출 (숫자/리스트 반환)
    try:
        a = making_INPUT(end_date=end_date_ts) 
    except Exception as e:
        print(f"Error running making_INPUT for date {end_date_ts}: {e}")
        print(" -> 'indicator' 함수가 데이터를 반환했는지, 해당 날짜의 데이터가 있는지 확인하세요.")
        return None

    # json.dumps는 파이썬 숫자/리스트를 올바른 JSON 문자열로 변환
    data_string = json.dumps(a, indent=2)
    
    # --- [핵심 수정] 3개의 플레이스홀더를 모두 교체 ---
    final_output = content.replace("<ANALYSIS_DATE>", analysis_date_str)
    final_output = final_output.replace("<TARGET_MONTH>", target_month_str)
    final_output = final_output.replace("<INPUT>", data_string)
    # --- [교체 끝] ---

    return final_output

def making_system_prompt():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'system_prompt.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"오류: '{file_path}' 경로에 파일이 없습니다.")
        return None 
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        return None
    
    return content

# --- 이 스크립트를 직접 실행할 때 (예: python -m aiportfolio.agents.prompt_maker) ---
if __name__ == "__main__":
    
    print("--- 1. System Prompt 생성 테스트 ---")
    system_prompt = making_system_prompt()
    if system_prompt:
        print("System Prompt 로드 성공.")
    else:
        print("System Prompt 로드 실패.")
        
    print("\n--- 2. User Prompt (2024년 5월 ~ 12월) 생성 테스트 ---")
    
    # [핵심] 2024년 5월부터 12월까지의 월말 날짜 리스트 생성
    target_dates = pd.date_range(start='2024-05-31', end='2024-11-30', freq='ME')
    
    all_prompts_generated = True
    generated_prompts = {} # 생성된 프롬프트를 저장할 딕셔너리

    for date in target_dates:
        # 'YYYY-MM-DD' 형식의 문자열로 변환
        date_str = date.strftime('%Y-%m-%d')
        
        print(f"\n[{date_str}] 날짜로 User Prompt 생성 시도...")
        
        user_prompt = making_user_prompt(end_date=date_str)
        
        if user_prompt:
            target_month = (date + pd.DateOffset(months=1)).strftime('%Y-%m')
            print(f"-> [성공] {date_str} 기준 (Target: {target_month}) 프롬프트 생성 완료.")
            generated_prompts[target_month] = user_prompt
        else:
            print(f"-> [실패] {date_str} 기준 프롬프트 생성 실패. 'indicator' 함수가 해당 날짜의 데이터를 반환하는지 확인하세요.")
            all_prompts_generated = False

    if all_prompts_generated:
        print("\n\n--- [최종 결론] ---")
        print("모든 월(2024년 5월~12월)에 대한 User Prompt가 성공적으로 생성되었습니다.")
        print(f"총 {len(generated_prompts)}개의 프롬프트가 생성되었습니다.")
        # print(generated_prompts['2024-06']) # 6월 프롬프트 예시 출력
    else:
        print("\n\n--- [최종 결론] ---")
        print("일부 월의 프롬프트 생성에 실패했습니다. 위쪽의 오류 메시지를 확인하세요.")
        print("'indicator' 함수가 해당 기간의 모든 월말 데이터를 포함하고 있는지 확인해야 합니다.")