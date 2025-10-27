'''
55까지 각 번호가 뭘 의미하는지는 찾겠는데 60까지 나와있는건 왜 못찾겠지...?
10: 에너지 (Energy)
15: 소재 (Materials)
20: 산업재 (Industrials)
25: 경기소비재 (Consumer Discretionary)
30: 필수소비재 (Consumer Staples)
35: 헬스케어 (Health Care)
40: 금융 (Financials)
45: 정보기술 (Information Technology)
50: 통신 서비스 (Communication Services)
55: 유틸리티 (Utilities)
60: 부동산 (Real Estate)
'''

def map_gics_sector(sector_list):
    gics_mapping = {
        10: "Energy",
        15: "Materials",
        20: "Industrials",
        25: "Consumer Discretionary",
        30: "Consumer Staples",
        35: "Health Care",
        40: "Financials",
        45: "Information Technology",
        50: "Communication Services",
        55: "Utilities",
        60: "Real Estate"
    }

    mapped = []  # 결과를 담을 리스트

    for code in sector_list:
        if code in gics_mapping:
            mapped.append(gics_mapping[code])
        else:
            raise KeyError(f"Invalid GICS code: {code}")
    
    return mapped
