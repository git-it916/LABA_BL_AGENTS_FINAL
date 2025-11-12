import pandas as pd
import numpy as np
import os
import warnings

# 불필요한 경고 메시지를 무시합니다.
warnings.filterwarnings("ignore")

def calculate_accounting_indicator(): 
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        print("[경고] __file__ 변수를 찾을 수 없습니다. 현재 작업 디렉토리를 기준으로 경로를 설정합니다.")
        base_path = os.getcwd() 
        
    file_path = os.path.join(base_path, '..', '..', '..', 'database', 'compustat_2021.01_2024.12.csv')
    try:
        raw_df = pd.read_csv(file_path, encoding='utf-8')
    except FileNotFoundError:
        print(f"오류: {file_path} 에서 파일을 찾을 수 없습니다.")
        return pd.DataFrame()
        
    raw_df['public_date'] = pd.to_datetime(raw_df['public_date'])

    # --- 계산할 회계 지표(레벨) 목록 ---
    TARGET_METRICS = [
        'bm_Mean',
        'CAPEI_Mean',
        'GProf_Mean',
        'npm_Mean',
        'roa_Mean',
        'roe_Mean',
        'totdebt_invcap_Mean'
    ]
    
    # 최종 결과 담을 리스트
    all_results = []

    # --- 각 지표별로: "공시 시차 반영 3개월 평균( t-3, t-4, t-5 )"을 현재 월 t에서 사용 ---
    for metric_name in TARGET_METRICS:
        print(f"[알림] '{metric_name}' 지표의 공시 시차( t-3, t-4, t-5 ) 평균 계산 중...")

        # (1) 레벨 피벗 (Index: 날짜, Columns: 섹터, Values: 지표값)
        levels_df = raw_df.pivot_table(
            index='public_date',
            columns='gicdesc',
            values=metric_name
        ).sort_index()

        # (2) 시차 3·4·5개월 이전 값 준비
        # 예) t가 5월이면 shift(3)=2월, shift(4)=1월, shift(5)=이전해 12월
        L3 = levels_df.shift(3)
        L4 = levels_df.shift(4)
        L5 = levels_df.shift(5)

        # (3) 세 값의 단순 평균을 현재 월 t의 "사용 가능 회계정보"로 정의
        #     세 달 모두 있어야 평균이 나오도록(=하나라도 없으면 NaN)
        available_acct = (L3 + L4 + L5) / 3.0

        # (4) Long 포맷으로 변환
        long_df = available_acct.stack(dropna=True).reset_index()
        long_df.columns = ['date', 'gsector', 'acct_level_lagged_avg']
        long_df['metric'] = metric_name

        all_results.append(long_df)

    print("[알림] 모든 지표 계산 완료. 데이터 취합 중...")

    if not all_results:
        print("[경고] 최종 결과가 없습니다.")
        return pd.DataFrame()

    # (5) 하나로 합치고 정렬
    final_df = pd.concat(all_results, ignore_index=True)
    final_df = final_df.sort_values(by=['metric', 'gsector', 'date']).reset_index(drop=True)

    # 최종 출력: date 시점에서 사용 가능한 회계 레벨 (t-3,4,5 평균)
    return final_df

if __name__ == "__main__":
    print("[알림] 공시 시차 반영 회계 레벨(3개월 평균) 계산 스크립트 실행 시작...")
    accounting_levels = calculate_accounting_indicator()
    print("\n[알림] 스크립트 실행 완료.")
    print("\n--- 최종 데이터 정보 ---")
    print(accounting_levels.info())
    print("\n--- Head ---")
    print(accounting_levels.head())
    print("\n--- Tail ---")
    print(accounting_levels.tail())
