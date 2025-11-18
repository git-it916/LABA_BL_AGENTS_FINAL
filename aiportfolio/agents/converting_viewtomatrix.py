import os
import json
import numpy as np
import pandas as pd
from glob import glob

# python -m aiportfolio.agents.converting_viewtomatrix

# database/output_view의 뷰 로그 파일 열기
def open_view_log(simul_name=None, Tier=None, end_date=None):
    """
    'save_view_as_json'이 저장한 뷰 파일을 읽어,
    특정 end_date와 일치하는 뷰 데이터만 필터링하여 반환합니다.

    Args:
        simul_name (str, optional): 시뮬레이션 이름
        Tier (int, optional): 분석 단계 (1, 2, 3)
        end_date (datetime, optional): 종료 날짜 (필터링 기준)
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

        # simul_name으로 파일 찾기
        if simul_name is not None:
            # 파일명: {simul_name}.json
            filename = f'{simul_name}.json'
            target_file = os.path.join(output_dir, filename)

            if os.path.exists(target_file):
                latest_file = target_file
                print(f"[알림] 뷰 파일 로드: {filename}")
            else:
                print(f"경고: '{target_file}' 파일을 찾을 수 없습니다.")
                return None
        else:
            # simul_name이 없으면 오류 발생
            raise ValueError(
                "View를 행렬로 바꾸기 위해 View를 로드하던 중 오류가 발생했습니다.\n"
                "simul_name은 필수 인자입니다.\n"
                f"제공된 값: simul_name={simul_name}\n"
                "사용 예시: open_view_log(simul_name='test1', Tier=2, end_date='2024-05-31')"
            )

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

        # === Step 1: 형식에 따라 파싱 ===
        if isinstance(views_data_raw, list):
            # 신규 형식: 이미 파싱된 리스트
            print(f"[알림] 이미 파싱된 뷰 데이터 감지 (항목 수: {len(views_data_raw)})")
            views_data = views_data_raw
        else:
            # 기존 형식: 문자열로 저장된 경우
            views_data_string = views_data_raw

            # 2-2. 순수 JSON 배열 추출
            # 방법 1: '[{' 패턴으로 시작하는 JSON 배열 찾기 (가장 일반적)
            start_index = views_data_string.find('[{')

            # 방법 2: 만약 '[{' 가 없다면, 독립된 '[' 찾기 (fallback)
            if start_index == -1:
                start_index = views_data_string.find('[')
                if start_index != -1:
                    # '[' 다음에 공백/개행 후 '{' 가 올 수도 있음
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

        # === Step 2: end_date 필터링 (공통 로직) ===
        if end_date is None:
            raise ValueError(
                "View를 행렬로 바꾸기 위해 View를 로드하던 중 오류가 발생했습니다.\n"
                "end_date는 필수 인자입니다.\n"
                f"제공된 값: end_date={end_date}\n"
                "사용 예시: open_view_log(simul_name='test1', Tier=2, end_date='2024-05-31')"
            )

        # end_date를 문자열로 변환 (비교를 위해)
        if isinstance(end_date, str):
            end_date_str = end_date
        else:
            end_date_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        # end_date와 일치하는 뷰만 필터링
        filtered_views = [view for view in views_data if view.get('end_date') == end_date_str]

        if len(filtered_views) == 0:
            print(f"경고: end_date={end_date_str}와 일치하는 뷰를 찾을 수 없습니다.")
            return None

        print(f"[알림] end_date={end_date_str}와 일치하는 뷰 {len(filtered_views)}개 필터링 완료")
        return filtered_views

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