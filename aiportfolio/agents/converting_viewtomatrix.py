import os
import json
import numpy as np
import pandas as pd
from glob import glob

# python -m aiportfolio.agents.converting_viewtomatrix

# database/output_view의 가장 최근 파일 열기
def open_file():
    """
    'save_view_as_json'이 저장한 "JSON 인코딩된 문자열" 파일을 읽어,
    파싱하고 "청소"하여 Python 리스트로 반환합니다.
    """
    try:
        # === 1. 최신 로그 파일 찾기 (기존 로직 동일) ===
        current_script_path = os.path.dirname(os.path.abspath(__file__))
        mvo_logs_dir = os.path.join(current_script_path, '../..', 'database', 'logs')
        search_pattern = os.path.join(mvo_logs_dir, 'result of *')
        all_log_folders = glob(search_pattern)
        
        if not all_log_folders:
            print(f"경고: '{mvo_logs_dir}'에서 'result of *' 폴더를 찾지 못했습니다.")
            return None
            
        all_log_folders.sort()
        latest_folder = all_log_folders[-1]
        
        if not os.path.isdir(latest_folder):
            print(f"오류: '{latest_folder}'는 디렉토리가 아닙니다.")
            return None

        output_dir = os.path.join(latest_folder, 'LLM_view')
        
        if not os.path.isdir(output_dir):
            print(f"오류: 최신 로그 폴더 안에 'LLM_view'를 찾을 수 없습니다. (경로: {output_dir})")
            return None

        json_files = glob(os.path.join(output_dir, '*.json'))

        if not json_files: 
            print(f"경고: '{output_dir}'에 JSON 파일이 존재하지 않습니다.")
            return None

        latest_file = max(json_files, key=os.path.getmtime)
        print(f"파일 로드 중: {latest_file}")

        # ---
        # 💡 [핵심] 2단계 파싱 (Load -> Loads)
        # ---

        # 2-1. [json.load] 파일에 저장된 "JSON 문자열"을 "Python 문자열"로 로드
        with open(latest_file, 'r', encoding='utf-8') as f:
            views_data_string = json.load(f)
            
        # 이제 'views_data_string'은 "Here is the output... [...]" 형태의
        # "더러운" Python 문자열입니다.

        # 2-2. [ 와 ] 사이의 순수 JSON 문자열 추출
        start_index = views_data_string.find('[')
        end_index = views_data_string.rfind(']')
        
        if start_index == -1 or end_index == -1:
            print(f"오류: {latest_file} 파일 내용에서 JSON 리스트( [...] )를 찾을 수 없습니다.")
            print(f"--- 파일에서 로드한 문자열 (일부) ---")
            print(views_data_string[:200])
            print("---------------------------")
            return None

        json_string = views_data_string[start_index : end_index + 1]

        # 2-3. "압축(Minify)" : 모든 비표준 공백 및 줄 바꿈 제거
        lines = json_string.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        json_string_minified = ''.join(cleaned_lines)
        
        # 2-4. [json.loads] "압축된 문자열"을 "Python 리스트"로 변환
        views_data = json.loads(json_string_minified) 

        # 2-5. 파싱이 완료된 'Python 리스트'를 반환
        return views_data

    except json.JSONDecodeError as e:
        # 2-1 (json.load) 또는 2-4 (json.loads)에서 실패 시
        print(f"오류: JSON 파싱에 실패했습니다. {e}")
        if 'json_string_minified' in locals():
            print(f"--- (실패한) 압축된 문자열 ---")
            print(json_string_minified)
            print("-----------------------")
        return None
    except Exception as e:
        print(f"파일 처리 중 알 수 없는 오류 발생: {e}")
        return None

# python -m aiportfolio.agents.converting_viewtomatrix
# ==================== 1. Q 행렬 생성 ====================
def create_Q_vector(views_data):
    k = len(views_data)
    current_forecasts = np.zeros((k, 1))

    for i, view in enumerate(views_data):
        current_forecasts[i, 0] = view['relative_return_view']
    
    return current_forecasts

# ==================== 2. P 행렬 생성 ====================
def create_P_matrix(views_data):
    sector_order = [
        "Energy",
        "Materials",
        "Industrials",
        "Consumer Discretionary",
        "Consumer Staples",
        "Health Care",
        "Financials",
        "Information Technology",
        "Communication Services",
        "Utilities",
        "Real Estate"
        ]

    k = len(views_data)  # 뷰 개수
    n = len(sector_order)  # 섹터 개수
    
    P = np.zeros((k, n))
    
    for i, view in enumerate(views_data):
        # 섹터명 추출 (Long/Short 표시 제거)
        sector_1 = view['sector_1'].replace(' (Long)', '').strip()
        sector_2 = view['sector_2'].replace(' (Short)', '').strip()
        
        # 섹터 인덱스 찾기
        try:
            idx_1 = sector_order.index(sector_1)
            idx_2 = sector_order.index(sector_2)
            
            # Long 섹터: +1, Short 섹터: -1
            P[i, idx_1] = 1
            P[i, idx_2] = -1
        except ValueError as e:
            print(f"Warning: 섹터를 찾을 수 없습니다 - {e}")
    
    return P