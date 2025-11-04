import os
import json
from datetime import datetime

# python -m aiportfolio.agents.making_example_view

# 뷰 1
views_data1 = [
    {
        "sector_1": "Information Technology (Long)",
        "sector_2": "Energy (Short)",
        "relative_return_view": 0.02
    },
    {
        "sector_1": "Health Care (Long)",
        "sector_2": "Utilities (Short)",
        "relative_return_view": 0.015
    },
    {
        "sector_1": "Financials (Long)",
        "sector_2": "Consumer Staples (Short)",
        "relative_return_view": 0.01
    },
    {
        "sector_1": "Industrials (Long)",
        "sector_2": "Real Estate (Short)",
        "relative_return_view": 0.018
    },
    {
        "sector_1": "Consumer Discretionary (Long)",
        "sector_2": "Communication Services (Short)",
        "relative_return_view": 0.012
    }
]

views_data2 = [
    {
        "sector_1": "Materials (Long)",
        "sector_2": "Utilities (Short)",
        "relative_return_view": 0.017
    },
    {
        "sector_1": "Communication Services (Long)",
        "sector_2": "Financials (Short)",
        "relative_return_view": 0.013
    },
    {
        "sector_1": "Consumer Staples (Long)",
        "sector_2": "Energy (Short)",
        "relative_return_view": 0.011
    },
    {
        "sector_1": "Real Estate (Long)",
        "sector_2": "Industrials (Short)",
        "relative_return_view": 0.016
    },
    {
        "sector_1": "Information Technology (Long)",
        "sector_2": "Health Care (Short)",
        "relative_return_view": 0.019
    }
]

# 1. 저장할 디렉토리 경로 설정
log_dir = 'database/output_view'

# 2. 파일 이름을 현재 시간으로 동적으로 생성
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f'example_{timestamp}.json'
filepath = os.path.join(log_dir, filename)

# 3. JSON 파일로 저장
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(views_data2, f, ensure_ascii=False, indent=4, default=str)

print(f"{filepath}에 결과가 저장되었습니다.")