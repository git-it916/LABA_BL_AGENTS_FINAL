import os
import json
import numpy as np
import pandas as pd
from glob import glob

# python -m aiportfolio.agents.converting_viewtomatrix

# database/output_view의 가장 최근 파일 열기
def open_file(simul_name=None, Tier=None, end_date=None):
    """
    'save_view_as_json'이 저장한 "JSON 인코딩된 문자열" 파일을 읽어,
    파싱하고 "청소"하여 Python 리스트로 반환합니다.

    Args:
        simul_name (str, optional): 시뮬레이션 이름
        Tier (int, optional): 분석 단계 (1, 2, 3)
        end_date (datetime, optional): 종료 날짜
    """
    try:
        # === 1. Tier에 해당하는 로그 폴더 찾기 ===
        current_script_path = os.path.dirname(os.path.abspath(__file__))
        mvo_logs_dir = os.path.join(current_script_path, '../..', 'database', 'logs')

        if Tier is not None:
            # Tier가 지정된 경우 해당 폴더 직접 접근
            tier_folder = os.path.join(mvo_logs_dir, f'Tier{Tier}')
            if not os.path.isdir(tier_folder):
                print(f"경고: '{tier_folder}' 폴더를 찾지 못했습니다.")
                return None
            latest_folder = tier_folder
        else:
            # Tier가 없으면 기존 로직 사용 (가장 최근 폴더)
            search_pattern = os.path.join(mvo_logs_dir, 'Tier*')
            all_log_folders = glob(search_pattern)

            if not all_log_folders:
                print(f"경고: '{mvo_logs_dir}'에서 'Tier*' 폴더를 찾지 못했습니다.")
                return None

            all_log_folders.sort()
            latest_folder = all_log_folders[-1]

        if not os.path.isdir(latest_folder):
            print(f"오류: '{latest_folder}'는 디렉토리가 아닙니다.")
            return None

        output_dir = os.path.join(latest_folder, 'LLM-view')
        
        if not os.path.isdir(output_dir):
            print(f"오류: 최신 로그 폴더 안에 'LLM-view'를 찾을 수 없습니다. (경로: {output_dir})")
            return None

        # simul_name과 end_date가 주어진 경우 특정 파일 찾기
        if simul_name is not None and end_date is not None:
            # datetime 객체를 Windows 파일명에 안전한 형식으로 변환
            if isinstance(end_date, str):
                end_date_str = end_date
            else:
                end_date_str = end_date.strftime('%Y-%m-%d')

            filename = f'{simul_name}_{end_date_str}.json'
            target_file = os.path.join(output_dir, filename)

            if os.path.exists(target_file):
                latest_file = target_file
            else:
                print(f"경고: '{target_file}' 파일을 찾을 수 없습니다.")
                # 대안: 같은 simul_name의 가장 최근 파일 찾기
                pattern = os.path.join(output_dir, f'{simul_name}_*.json')
                matching_files = glob(pattern)
                if matching_files:
                    latest_file = max(matching_files, key=os.path.getmtime)
                    print(f"대신 최신 파일을 사용합니다: {latest_file}")
                else:
                    print(f"경고: '{simul_name}'에 해당하는 파일이 없습니다.")
                    return None
        else:
            # simul_name이나 end_date가 없으면 가장 최근 파일 사용
            json_files = glob(os.path.join(output_dir, '*.json'))

            if not json_files:
                print(f"경고: '{output_dir}'에 JSON 파일이 존재하지 않습니다.")
                return None

            latest_file = max(json_files, key=os.path.getmtime)

        # ---
        # 💡 [핵심] 2단계 파싱 (Load -> Loads)
        # ---

        # 2-1. [json.load] 파일 로드
        with open(latest_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        # save_view_as_json이 리스트로 감싸서 저장하므로 확인 후 추출
        if isinstance(loaded_data, list):
            if len(loaded_data) == 0:
                print(f"오류: {latest_file} 파일이 비어 있습니다.")
                return None
            # 가장 최근 항목 사용 (마지막 항목)
            views_data_raw = loaded_data[-1]
        else:
            views_data_raw = loaded_data

        # === 새로운 형식 체크: 이미 파싱된 객체인지 확인 ===
        # Llama_view_generator가 수정되어 파싱된 리스트를 직접 저장하는 경우
        if isinstance(views_data_raw, list):
            # 이미 파싱된 리스트 -> 바로 반환
            print(f"[알림] 이미 파싱된 뷰 데이터 감지 (항목 수: {len(views_data_raw)})")
            return views_data_raw

        # === 기존 형식: 문자열로 저장된 경우 ===
        views_data_string = views_data_raw

        # 이제 'views_data_string'은 "Here is the output... [...]" 또는
        # "[JSON Output][{...}]" 형태의 "더러운" Python 문자열입니다.

        # 2-2. 순수 JSON 배열 추출
        # 전략: 모든 문자를 순회하며 첫 번째 유효한 JSON 배열을 찾기

        # 방법 1: '[{' 패턴으로 시작하는 JSON 배열 찾기 (가장 일반적)
        start_index = views_data_string.find('[{')

        # 방법 2: 만약 '[{' 가 없다면, 독립된 '[' 찾기 (fallback)
        if start_index == -1:
            start_index = views_data_string.find('[')
            if start_index != -1:
                # '[' 다음에 공백/개행 후 '{' 가 올 수도 있음
                # 확인: '[' 이후 첫 번째 non-whitespace 문자가 '{'인지
                temp_str = views_data_string[start_index:].lstrip('[').lstrip()
                if not temp_str.startswith('{'):
                    start_index = -1  # 유효한 JSON 배열 시작이 아님

        if start_index == -1:
            print(f"오류: JSON 배열 시작('[{{' 또는 '[ {{')을 찾을 수 없습니다.")
            print(f"--- 문자열 앞부분 (300자) ---")
            print(views_data_string[:300])
            print("---------------------------")
            return None

        # '}]'로 끝나는 위치 찾기
        # rfind로 가장 마지막 '}]' 찾기
        end_index = views_data_string.rfind('}]')

        if end_index == -1:
            # '}]'가 없으면 독립된 ']' 찾기 (fallback)
            end_index = views_data_string.rfind(']')
            if end_index == -1:
                print(f"오류: JSON 배열 끝(']')을 찾을 수 없습니다.")
                print(f"--- 문자열 뒷부분 (300자) ---")
                print(views_data_string[-300:])
                print("---------------------------")
                return None
        else:
            # '}]'를 포함하려면 끝 인덱스를 ']' 위치로 조정
            end_index = end_index + 1  # '}]'의 ']' 위치

        # JSON 문자열 추출
        json_string = views_data_string[start_index : end_index + 1]

        # 2-3. "압축(Minify)" : 모든 비표준 공백 및 줄 바꿈 제거
        lines = json_string.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        json_string_minified = ''.join(cleaned_lines)

        # 디버그: 추출된 JSON 문자열 일부 출력
        print(f"[디버그] 추출된 JSON 문자열 (앞 200자): {json_string_minified[:200]}")

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