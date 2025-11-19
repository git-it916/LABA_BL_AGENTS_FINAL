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

def map_code_to_gics_sector(sector_list):
    """
    GICS 섹터 코드(숫자)를 영어 이름으로 변환합니다.
    """
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

    mapped = []

    for code in sector_list:
        if code in gics_mapping:
            mapped.append(gics_mapping[code])
        else:
            raise KeyError(f"Invalid GICS code: {code}")

    return mapped

def map_gics_sector_to_code(sector_list):
    """
    GICS 영어 섹터 이름을 숫자 코드로 변환합니다.
    """
    # GICS 이름 -> 코드 매핑 딕셔너리
    code_mapping = {
        "Energy": 10,
        "Materials": 15,
        "Industrials": 20,
        "Consumer Discretionary": 25,
        "Consumer Staples": 30,
        "Health Care": 35,
        "Financials": 40,
        "Information Technology": 45,
        "Communication Services": 50,
        "Utilities": 55,
        "Real Estate": 60
    }

    mapped = []

    for name in sector_list:
        if name in code_mapping:
            mapped.append(code_mapping[name])
        else:
            raise KeyError(f"유효하지 않은 GICS 섹터 이름입니다 (Invalid GICS name): {name}")

    return mapped
