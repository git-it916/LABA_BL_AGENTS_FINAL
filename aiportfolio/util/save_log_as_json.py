import os
import json
from datetime import datetime

def save_BL_as_json(results, simul_name, Tier):
    """
    'database/logs' 디렉토리에서 Tier에 해당하는 디렉토리를 찾고,
    그 하위의 'result_of_BL-MVO' 디렉토리에 JSON 결과를 simul_name으로 저장합니다.
    """
    
    # 1. 기본 로그 디렉토리 설정
    base_log_dir = os.path.join("database", "logs")

    try:
        # 2. 'database.logs' 내의 모든 항목(파일/디렉토리) 목록을 가져옴
        all_entries = os.listdir(base_log_dir)
        
        # 3. 이 중에서 '디렉토리'만 필터링 (전체 경로로 변환)
        tier_dirs = [
            os.path.join(base_log_dir, d) 
            for d in all_entries 
            if os.path.isdir(os.path.join(base_log_dir, d))
        ]

        if not tier_dirs:
            print("result_of_BL-MVO를 저장하던 도중 오류가 발생했습니다.")
            print(f"[오류] '{base_log_dir}' 디렉토리 안에 하위 디렉토리가 없습니다.")
            return

    except FileNotFoundError:
        print("result_of_BL-MVO를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 기본 로그 디렉토리를 찾을 수 없습니다: {base_log_dir}")
        return
    
    # 4. Tier에 해당하는 디렉토리 찾기
    if 1 <= Tier <= len(tier_dirs):
        target_dir = tier_dirs[Tier - 1]
    else:
        print("result_of_BL-MVO를 저장하던 도중 오류가 발생했습니다.")
        print("Tier 변수에 유효하지 않은 입력값입니다.")

    # 5. 최종 저장 경로 설정
    save_dir = os.path.join(target_dir, 'result_of_BL-MVO')
    
    # 6. 파일명 설정
    filename = f'{simul_name}.json'
    filepath = os.path.join(save_dir, filename)

    try:
        # 7. 최종 저장 디렉토리가 존재하지 않으면 생성(안정성)
        os.makedirs(save_dir, exist_ok=True)

        # 8. JSON 파일로 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4, default=str)
        
        print(f"{filepath}에 결과가 저장되었습니다.")

    except OSError as e:
        print("result_of_BL-MVO를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 디렉토리를 생성하거나 파일에 쓰는 데 실패했습니다: {e}")
    except Exception as e:
        print("result_of_BL-MVO를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 파일 저장 중 알 수 없는 오류 발생: {e}")

    return

def save_view_as_json(results, simul_name, Tier, end_date):
    """
    'database/logs' 디렉토리에서 Tier에 해당하는 디렉토리를 찾고,
    그 하위의 'LLM_view' 디렉토리에 JSON 결과를 저장하는데,
    'LLM_view' 디렉토리에 simul_name이 존재하지 않는 경우 simul_name으로 저장.
    'LLM_view' 디렉토리에 simul_name이 존재하는 경우 simul_name 파일을 리스트로 불러와서 내용 추가.
    """
    # 1. 기본 로그 디렉토리 설정
    base_log_dir = os.path.join("database", "logs")

    try:
        # 2. 'database.logs' 내의 모든 항목(파일/디렉토리) 목록을 가져옴
        all_entries = os.listdir(base_log_dir)
        
        # 3. 이 중에서 '디렉토리'만 필터링 (전체 경로로 변환)
        tier_dirs = [
            os.path.join(base_log_dir, d) 
            for d in all_entries 
            if os.path.isdir(os.path.join(base_log_dir, d))
        ]

        if not tier_dirs:
            print("LLM_view를 저장하던 도중 오류가 발생했습니다.")
            print(f"[오류] '{base_log_dir}' 디렉토리 안에 하위 디렉토리가 없습니다.")
            return

    except FileNotFoundError:
        print("LLM_view를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 기본 로그 디렉토리를 찾을 수 없습니다: {base_log_dir}")
        return
    
    # 4. Tier에 해당하는 디렉토리 찾기
    if 1 <= Tier <= len(tier_dirs):
        target_dir = tier_dirs[Tier - 1]
    else:
        print("LLM_view를 저장하던 도중 오류가 발생했습니다.")
        print("Tier 변수에 유효하지 않은 입력값입니다.")
        return

    # 5. 최종 저장 경로 설정
    save_dir = os.path.join(target_dir, 'LLM_view')

    # 6. 파일명 설정
    filename = f'{simul_name}_{end_date}.json'
    filepath = os.path.join(save_dir, filename)

    try:
        # 7. 최종 저장 디렉토리가 존재하지 않으면 생성(안정성)
        os.makedirs(save_dir, exist_ok=True)

        # 8. 기존 파일이 있는지 확인하고 처리
        if os.path.exists(filepath):
            # 기존 파일을 리스트로 읽어옴
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # 기존 데이터가 리스트가 아니면 리스트로 변환
            if not isinstance(existing_data, list):
                existing_data = [existing_data]
            
            # 새로운 결과를 추가
            existing_data.append(results)
            
            # 업데이트된 데이터 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4, default=str)
            
            print(f"{filepath}에 결과가 추가되었습니다.")
        else:
            # 파일이 없으면 새로 생성 (리스트로 저장)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([results], f, ensure_ascii=False, indent=4, default=str)
            
            print(f"{filepath}에 결과가 저장되었습니다.")

    except OSError as e:
        print("LLM_view를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 디렉토리를 생성하거나 파일에 쓰는 데 실패했습니다: {e}")
    except json.JSONDecodeError as e:
        print("LLM_view를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 기존 JSON 파일을 읽는 데 실패했습니다: {e}")
    except Exception as e:
        print("LLM_view를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 파일 저장 중 알 수 없는 오류 발생: {e}")

    return

def save_performance_as_json(results, simul_name, Tier):
    # 1. 기본 로그 디렉토리 설정
    base_log_dir = os.path.join("database", "logs")

    try:
        # 2. 'database.logs' 내의 모든 항목(파일/디렉토리) 목록을 가져옴
        all_entries = os.listdir(base_log_dir)
        
        # 3. 이 중에서 '디렉토리'만 필터링 (전체 경로로 변환)
        tier_dirs = [
            os.path.join(base_log_dir, d) 
            for d in all_entries 
            if os.path.isdir(os.path.join(base_log_dir, d))
        ]

        if not tier_dirs:
            print("result_of_test를 저장하던 도중 오류가 발생했습니다.")
            print(f"[오류] '{base_log_dir}' 디렉토리 안에 하위 디렉토리가 없습니다.")
            return

    except FileNotFoundError:
        print("result_of_test를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 기본 로그 디렉토리를 찾을 수 없습니다: {base_log_dir}")
        return
    # 4. Tier에 해당하는 디렉토리 찾기
    if 1 <= Tier <= len(tier_dirs):
        target_dir = tier_dirs[Tier - 1]
        
    else:
        print("result_of_test를 저장하던 도중 오류가 발생했습니다.")
        print("Tier 변수에 유효하지 않은 입력값입니다.")

    # 5. 최종 저장 경로 설정
    save_dir = os.path.join(target_dir, 'result_of_test')

    # 6. 파일명 설정
    filename = f'{simul_name}.json'
    filepath = os.path.join(save_dir, filename)

    try:
        # 7. 최종 저장 디렉토리가 존재하지 않으면 생성(안정성)
        os.makedirs(save_dir, exist_ok=True)

        # 8. JSON 파일로 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4, default=str)
        
        print(f"{filepath}에 결과가 저장되었습니다.")

    except OSError as e:
        print("result_of_test를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 디렉토리를 생성하거나 파일에 쓰는 데 실패했습니다: {e}")
    except Exception as e:
        print("result_of_test를 저장하던 도중 오류가 발생했습니다.")
        print(f"[오류] 파일 저장 중 알 수 없는 오류 발생: {e}")

    return