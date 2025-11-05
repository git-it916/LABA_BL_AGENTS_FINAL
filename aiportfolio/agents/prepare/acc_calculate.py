import pandas as pd
import numpy as np
import os
import warnings

# 불필요한 경고 메시지를 무시합니다.
warnings.filterwarnings("ignore")

def calculate_accounting_indicator(): 
    """
    gics_accounting_info.csv 파일을 읽어,
    5가지 재무 지표 각각에 대해 '지난달 대비 변화율(%)'을 계산합니다.
    """
# --- 1. 데이터 파일 불러오기 ---
# --- 1. 데이터 파일 불러오기 ---
    try:
        # 이 스크립트 파일이 있는 위치를 기준으로 경로 설정
        # base_path = c:\...\LABA_BL_AGENTS_FINAL\aiportfolio\agents\prepare
        base_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # Jupyter Notebook 등 __file__이 없는 환경
        print("[경고] __file__ 변수를 찾을 수 없습니다. 현재 작업 디렉토리를 기준으로 경로를 설정합니다.")
        base_path = os.getcwd() 
        
    # [수정] '..'을 사용하여 세 단계 상위 폴더로 이동한 후 'database' 폴더로 진입
    # '..'은 '부모 폴더'를 의미합니다.
    # .../prepare -> .../agents -> .../aiportfolio -> .../LABA_BL_AGENTS_FINAL
    file_path = os.path.join(base_path, '..', '..', '..', 'database', 'gics_accounting_info.csv')
    try:
        raw_df = pd.read_csv(file_path, encoding='utf-8')
    except FileNotFoundError:
        print(f"오류: {file_path} 에서 파일을 찾을 수 없습니다.")
        return pd.DataFrame()
        
    raw_df['public_date'] = pd.to_datetime(raw_df['public_date'])

    # --- 2. 계산할 5가지 재무 지표(레벨) 목록 ---
    TARGET_METRICS = [
        'gpm_Median', 
        'npm_Median', 
        'roa_Median', 
        'roe_Median', 
        'debt_assets_Median'
    ]
    
    all_mom_results = []

    # --- 3. 각 재무 지표별로 반복 ---
    for metric_name in TARGET_METRICS:
        
        print(f"[알림] '{metric_name}' 지표의 월별 변화율 계산 중...")
        
        # 3-1. '레벨' 데이터 피벗 (Wide format)
        # (Index: 날짜, Columns: 섹터명, Values: 해당 재무 지표 값)
        levels_df = raw_df.pivot_table(
            index='public_date',
            columns='gicdesc',
            values=metric_name
        )
        
        # 3-2. [핵심] 지난달 대비 변화율(%) 계산
        # .pct_change()는 바로 전 행(지난달) 대비 변화율(예: 0.05)을 계산
        # 여기에 100을 곱해 퍼센트(%) 단위(예: 5.0)로 만듭니다.
        mom_change_df = levels_df.pct_change() 
        
        # 3-3. Long Format으로 변환
        # (결측치(NaN)가 아닌 값들만 stack하여 긴 형태로 변환)
        mom_long_df = mom_change_df.stack().reset_index()
        
        # 3-4. 컬럼명 변경
        mom_long_df.columns = ['date', 'gsector', 'mom_percent_change']
        
        # 3-5. 어떤 재무 지표인지 기록
        mom_long_df['metric'] = metric_name
        
        all_mom_results.append(mom_long_df)

    print("[알림] 모든 계산 완료. 데이터 취합 중...")
    
    # --- 4. 모든 결과를 하나의 DataFrame으로 합치기 ---
    if not all_mom_results:
        print("[경고] 최종 결과가 없습니다.")
        return pd.DataFrame()
        
    final_df = pd.concat(all_mom_results, ignore_index=True)
    
    # (첫 달은 비교 대상이 없어 NaN이 되므로, dropna=True인 stack()에서 이미 제거됨)
    
    # 가독성을 위해 정렬
    final_df = final_df.sort_values(by=['metric', 'gsector', 'date']).reset_index(drop=True)
    
    return final_df

# --- 스크립트 실행 ---
if __name__ == "__main__":
    print("[알림] 월별(MoM) 단순 변화율 계산 스크립트 실행 시작...")
    
    final_monthly_changes = calculate_accounting_indicator()
    
    print("\n[알림] 스크립트 실행 완료.")
    
    print("\n--- 최종 변화율 데이터 (Long Format)의 형태: ---")
    print(final_monthly_changes.info())
    
    print("\n--- 최종 변화율 데이터 (Head) ---")
    # (첫 달(2021-05)은 계산이 안되므로 2021-06부터 나옵니다)
    print(final_monthly_changes.head())
    
    print("\n--- 최종 변화율 데이터 (Tail) ---")
    print(final_monthly_changes.tail())