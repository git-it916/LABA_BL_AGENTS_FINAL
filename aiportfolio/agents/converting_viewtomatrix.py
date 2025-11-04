import os
import json
import numpy as np
import pandas as pd
from glob import glob

# python -m aiportfolio.agents.converting_viewtomatrix

# database/output_view의 가장 최근 파일 열기
def open_file():
    base_path = os.path.dirname(os.path.abspath(__file__)) # 현재 파일 기준으로 output_view 디렉토리 경로 설정
    output_dir = os.path.join(base_path, '../..', 'database', 'output_view')
    json_files = glob(os.path.join(output_dir, '*.json')) # output_view 폴더 내의 모든 JSON 파일 리스트 가져오기

    if not json_files: # JSON 파일이 하나라도 있는지 확인
        raise FileNotFoundError(f"JSON 파일이 존재하지 않습니다: {output_dir}")

    latest_file = max(json_files, key=os.path.getmtime) # 가장 최근 수정된 JSON 파일 찾기
    with open(latest_file, 'r', encoding='utf-8') as f:
        views_data = json.load(f)
    print(latest_file)
    
    return views_data

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