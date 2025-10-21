import os
import json
from datetime import datetime

def save_log_as_json(results):
    # 1. 저장할 디렉토리 경로 설정
    log_dir = 'database/logs'

    # 2. 파일 이름을 현재 시간으로 동적으로 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'result of BL_MVO {timestamp}.json'
    filepath = os.path.join(log_dir, filename)

    # 3. JSON 파일로 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4, default=str)
    
    print(f"{filepath}에 결과가 저장되었습니다.")

    return