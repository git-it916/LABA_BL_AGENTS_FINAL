import os
import json
from datetime import datetime

def save_BL_as_json(results):
    """
    'database.logs' 폴더에서 가장 최근에 생성된 시간 폴더를 찾아,
    그 하위의 'BL_result' 디렉토리에 JSON 결과를 저장합니다.
    """
    
    # 1. 기본 로그 디렉토리 설정
    base_log_dir = os.path.join("database", "logs")

    try:
        # 2. 'database.logs' 내의 모든 항목(파일/디렉토리) 목록을 가져옴
        all_entries = os.listdir(base_log_dir)
        
        # 3. 이 중에서 '디렉토리'만 필터링 (전체 경로로 변환)
        # (참고: os.path.isdir는 전체 경로를 필요로 합니다)
        sub_dirs = [
            os.path.join(base_log_dir, d) 
            for d in all_entries 
            if os.path.isdir(os.path.join(base_log_dir, d))
        ]

        if not sub_dirs:
            print(f"[오류] '{base_log_dir}' 디렉토리 안에 하위 디렉토리가 없습니다.")
            return

        # 4. (핵심) 생성 시간(ctime)을 기준으로 가장 최신 디렉토리를 찾음
        latest_dir = max(sub_dirs, key=os.path.getctime)
        
        # (latest_dir는 'database.logs/2025-11-05_07-15-00'와 같은 경로가 됨)

    except FileNotFoundError:
        print(f"[오류] 기본 로그 디렉토리를 찾을 수 없습니다: {base_log_dir}")
        return
    except Exception as e:
        print(f"[오류] 최신 로그 디렉토리를 찾는 중 오류 발생: {e}")
        return

    # 5. 최종 저장 경로 설정 (최신 디렉토리 하위의 'BL_result')
    save_dir = os.path.join(latest_dir, 'BL_result')
    
    # 6. 파일명 설정 (원본 코드와 동일)
    filename = 'result of BL_MVO.json'
    filepath = os.path.join(save_dir, filename)

    try:
        # 7. (안정성) 최종 저장 디렉토리가 존재하지 않으면 생성
        # (이전 단계의 'create_log_directories' 함수가 이미 만들었겠지만,
        #  혹시 모르니 확인하는 것이 안전합니다.)
        os.makedirs(save_dir, exist_ok=True)

        # 8. JSON 파일로 저장 (원본 코드와 동일)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4, default=str)
        
        print(f"{filepath}에 결과가 저장되었습니다.")

    except OSError as e:
        print(f"[오류] 디렉토리를 생성하거나 파일에 쓰는 데 실패했습니다: {e}")
    except Exception as e:
        print(f"[오류] 파일 저장 중 알 수 없는 오류 발생: {e}")

    return

def save_view_as_json(results, end_date):
    """
    'database.logs' 폴더에서 가장 최근에 생성된 시간 폴더를 찾아,
    그 하위의 'BL_result' 디렉토리에 JSON 결과를 저장합니다.
    """
    
    # 1. 기본 로그 디렉토리 설정
    base_log_dir = os.path.join("database", "logs")

    try:
        # 2. 'database.logs' 내의 모든 항목(파일/디렉토리) 목록을 가져옴
        all_entries = os.listdir(base_log_dir)
        
        # 3. 이 중에서 '디렉토리'만 필터링 (전체 경로로 변환)
        # (참고: os.path.isdir는 전체 경로를 필요로 합니다)
        sub_dirs = [
            os.path.join(base_log_dir, d) 
            for d in all_entries 
            if os.path.isdir(os.path.join(base_log_dir, d))
        ]

        if not sub_dirs:
            print(f"[오류] '{base_log_dir}' 디렉토리 안에 하위 디렉토리가 없습니다.")
            return

        # 4. (핵심) 생성 시간(ctime)을 기준으로 가장 최신 디렉토리를 찾음
        latest_dir = max(sub_dirs, key=os.path.getctime)
        
        # (latest_dir는 'database.logs/2025-11-05_07-15-00'와 같은 경로가 됨)

    except FileNotFoundError:
        print(f"[오류] 기본 로그 디렉토리를 찾을 수 없습니다: {base_log_dir}")
        return
    except Exception as e:
        print(f"[오류] 최신 로그 디렉토리를 찾는 중 오류 발생: {e}")
        return

    # 5. 최종 저장 경로 설정 (최신 디렉토리 하위의 'BL_result')
    save_dir = os.path.join(latest_dir, 'LLM_view')
    
    # 6. 파일명 설정 (원본 코드와 동일)
    safe_date = str(end_date).replace(":", "-").replace(" ", "_")
    filename = f'result of {safe_date}.json'
    filepath = os.path.join(save_dir, filename)

    try:
        # 7. (안정성) 최종 저장 디렉토리가 존재하지 않으면 생성
        # (이전 단계의 'create_log_directories' 함수가 이미 만들었겠지만,
        #  혹시 모르니 확인하는 것이 안전합니다.)
        os.makedirs(save_dir, exist_ok=True)

        # 8. JSON 파일로 저장 (원본 코드와 동일)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4, default=str)
        
        print(f"{filepath}에 결과가 저장되었습니다.")

    except OSError as e:
        print(f"[오류] 디렉토리를 생성하거나 파일에 쓰는 데 실패했습니다: {e}")
    except Exception as e:
        print(f"[오류] 파일 저장 중 알 수 없는 오류 발생: {e}")

    return

def save_performance_as_json(results):
    # 1. 저장할 디렉토리 경로 설정
    log_dir = 'database/logs/test_result'

    # 2. 파일 이름을 현재 시간으로 동적으로 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'result of test {timestamp}.json'
    filepath = os.path.join(log_dir, filename)

    # 3. JSON 파일로 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4, default=str)
    
    print(f"{filepath}에 결과가 저장되었습니다.")

    return