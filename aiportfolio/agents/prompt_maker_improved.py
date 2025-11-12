"""
개선된 프롬프트 생성 시스템

주요 개선사항:
1. 소수점 2자리로 제한 (가독성 향상)
2. Tier별 가변 프롬프트 (일관성 유지하면서 필요한 부분만 변경)
3. 불필요한 메타데이터 제거
4. 더 깔끔한 JSON 출력
"""

import pandas as pd
import numpy as np
import os
import json
from aiportfolio.agents.prepare.Tier1_calculate import indicator
from aiportfolio.agents.prepare.Tier2_calculate import calculate_accounting_indicator
from aiportfolio.agents.prepare.Tier3_calculate import calculate_macro_indicator

def round_numeric_values(data, decimals=2):
    """
    딕셔너리의 모든 숫자 값을 지정된 소수점 자리로 반올림

    Args:
        data: 처리할 데이터 (dict, list, float, etc.)
        decimals: 소수점 자리수 (기본값 2)

    Returns:
        반올림된 데이터
    """
    if isinstance(data, dict):
        return {k: round_numeric_values(v, decimals) for k, v in data.items()}
    elif isinstance(data, list):
        return [round_numeric_values(item, decimals) for item in data]
    elif isinstance(data, (float, np.floating)):
        return round(float(data), decimals)
    elif isinstance(data, (int, np.integer)):
        return int(data)
    elif isinstance(data, str):
        # 문자열 안의 리스트를 파싱하여 반올림
        try:
            # "[0.123, -0.456, ...]" 형식 처리
            if data.startswith('[') and data.endswith(']'):
                parsed = eval(data)  # 안전한 환경에서만 사용
                if isinstance(parsed, list):
                    rounded = [round(float(x), decimals) if isinstance(x, (int, float)) else x for x in parsed]
                    return str(rounded)
        except:
            pass
        return data
    else:
        return data


def making_tier1_INPUT(end_date):
    """
    Tier 1 (기술적 지표) 데이터 생성

    Args:
        end_date: 데이터 기준 날짜

    Returns:
        list: 11개 섹터의 기술적 지표 데이터 (소수점 2자리)
    """
    data = indicator()

    def safe_get_value(sector, column):
        """섹터와 컬럼에 대한 값을 안전하게 가져오고 소수점 4자리로 반올림합니다."""
        filtered = data.loc[(data['date'] == end_date) & (data['gsector'] == sector), column]
        if len(filtered) == 0:
            print(f"[경고] {sector} 섹터의 {column} 데이터가 {end_date}에 없습니다. 'N/A'로 대체합니다.")
            return "N/A"
        value = filtered.iloc[0]

        # 리스트인 경우 (return_list)
        if isinstance(value, list):
            # return_list는 이미 소수점 단위 (0.0659 = 6.59%) → 그대로 반올림만
            return [round(float(x), 4) for x in value]
        # 숫자인 경우
        elif isinstance(value, (int, float, np.number)):
            # 모든 지표를 소수점 4자리로 반올림 (0.0001 = 0.01%)
            return round(float(value), 4)
        else:
            return value

    sectors = [
        "Energy", "Materials", "Industrials", "Consumer Discretionary",
        "Consumer Staples", "Health Care", "Financials", "Information Technology",
        "Communication Services", "Utilities", "Real Estate"
    ]

    sector_data_list = []
    for sector in sectors:
        sector_data_list.append({
            "sector": sector,
            "ttm_returns": safe_get_value(sector, 'return_list'),
            "z_score": safe_get_value(sector, 'z-score'),
            "volatility": safe_get_value(sector, 'volatility'),
            "trend_strength": safe_get_value(sector, 'trend_strength'),
            "cagr_3y": safe_get_value(sector, 'CAGR')
        })

    return sector_data_list


def making_tier2_INPUT(end_date):
    """
    Tier 2 (회계 지표) 데이터 생성

    Args:
        end_date: 데이터 기준 날짜

    Returns:
        list: 11개 섹터의 회계 지표 데이터 (소수점 2자리)
    """
    data = calculate_accounting_indicator()

    def safe_get_value(sector, column):
        """섹터와 컬럼에 대한 값을 안전하게 가져옵니다."""
        filtered = data.loc[(data['date'] == end_date) & (data['gsector'] == sector), column]
        if len(filtered) == 0:
            print(f"[경고] {sector} 섹터의 {column} 데이터가 {end_date}에 없습니다. 'N/A'로 대체합니다.")
            return "N/A"
        value = filtered.iloc[0]

        # 숫자인 경우 반올림
        if isinstance(value, (int, float, np.number)):
            return round(float(value), 2)
        else:
            return value

    sectors = [
        "Energy", "Materials", "Industrials", "Consumer Discretionary",
        "Consumer Staples", "Health Care", "Financials", "Information Technology",
        "Communication Services", "Utilities", "Real Estate"
    ]

    sector_data_list = []
    for sector in sectors:
        sector_data_list.append({
            "sector": sector,
            "pe_ratio": safe_get_value(sector, 'pe_ratio'),
            "roe": safe_get_value(sector, 'roe_Mean'),
            "pb_ratio": safe_get_value(sector, 'bm_Mean'),  # Book-to-Market의 역수
            "debt_to_equity": safe_get_value(sector, 'totdebt_invcap_Mean'),
            "operating_margin": safe_get_value(sector, 'npm_Mean')
        })

    return sector_data_list

def making_tier3_INPUT(end_date):
    """
    Tier 3 (거시 지표) 데이터 생성

    Args:
        end_date: 데이터 기준 날짜
    
    Returns:
        dict: 거시경제 지표 데이터
    """
    data = calculate_macro_indicator()

    def safe_get_value(column):
        """컬럼에 대한 값을 안전하게 가져옵니다."""
        filtered = data.loc[(data['date'] == end_date), column]
        if len(filtered) == 0:
            print(f"[경고] {column} 데이터가 {end_date}에 없습니다. 'N/A'로 대체합니다.")
            return "N/A"
        value = filtered.iloc[0]

        # 숫자인 경우 반올림
        if isinstance(value, (int, float, np.number)):
            return round(float(value), 2)
        else:
            return value

    macro_data = {
        "date": end_date,
        "FEDFUNDS": safe_get_value('FEDFUNDS'),
        "CPI": safe_get_value('CPI'),
        "CA0_CLI": safe_get_value('CA0_CLI(Amplitude adjusted, Long-term average = 100)'),
        "T10Y2Y": safe_get_value('T10Y2Y'),
        "GPDIC1_PCA": safe_get_value('GPDIC1_PCA')
    }

    return macro_data


def load_tier_guidelines(tier):
    """
    Tier별 분석 가이드라인 로드

    Args:
        tier (int): 1, 2, 또는 3

    Returns:
        str: 해당 Tier의 가이드라인 텍스트
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'tier_guidelines.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Tier별 섹션 추출
        sections = content.split('### TIER ')
        tier_section = None

        for section in sections:
            if section.startswith(f'{tier} GUIDELINES'):
                tier_section = section
                break

        if tier_section:
            # 다음 Tier 섹션 전까지만 추출
            end_marker = '\n### TIER '
            if end_marker in tier_section:
                tier_section = tier_section[:tier_section.index(end_marker)]

            # COMMON RULES 추가
            if '### COMMON RULES' in content:
                common_start = content.index('### COMMON RULES')
                common_section = content[common_start:]
                tier_section += '\n\n' + common_section

            return f'### TIER {tier_section.strip()}'
        else:
            print(f"[경고] Tier {tier} 가이드라인을 찾을 수 없습니다.")
            return f"[Tier {tier} analysis guidelines not found]"

    except FileNotFoundError:
        print(f"[오류] 가이드라인 파일을 찾을 수 없습니다: {file_path}")
        return f"[Tier {tier} guidelines file not found]"
    except Exception as e:
        print(f"[오류] 가이드라인 로드 중 오류 발생: {e}")
        return f"[Error loading Tier {tier} guidelines]"


def making_system_prompt(tier):
    """
    Tier별 시스템 프롬프트 생성

    Args:
        tier (int): 1, 2, 또는 3

    Returns:
        str: 완성된 시스템 프롬프트
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_path, 'prompt_template', 'system_prompt_improved.txt')

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Tier별 가이드라인 로드
        tier_guidelines = load_tier_guidelines(tier)

        # 템플릿 변수 치환
        prompt = template.replace('{{TIER}}', str(tier))
        prompt = prompt.replace('{{TIER_SPECIFIC_GUIDELINES}}', tier_guidelines)

        return prompt

    except FileNotFoundError:
        print(f"[오류] 시스템 프롬프트 템플릿을 찾을 수 없습니다: {template_path}")
        return None
    except Exception as e:
        print(f"[오류] 시스템 프롬프트 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


def making_user_prompt(end_date, tier):
    """
    Tier별 사용자 프롬프트 생성

    Args:
        end_date: 데이터 기준 날짜
        tier (int): 1, 2, 또는 3

    Returns:
        str: 완성된 사용자 프롬프트
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_path, 'prompt_template', 'user_prompt_improved.txt')

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Tier별 데이터 블록 생성
        data_blocks = []

        # Tier 1: 기술적 지표 (항상 포함)
        tier1_data = making_tier1_INPUT(end_date)
        tier1_json = json.dumps(tier1_data, indent=2, ensure_ascii=False)
        data_blocks.append(f"=== Technical Indicators (Tier 1) ===\n{tier1_json}")

        # Tier 2: 회계 지표 추가
        if tier >= 2:
            tier2_data = making_tier2_INPUT(end_date)
            tier2_json = json.dumps(tier2_data, indent=2, ensure_ascii=False)
            data_blocks.append(f"\n=== Accounting Indicators (Tier 2) ===\n{tier2_json}")

        # Tier 3: 거시 지표 추가
        if tier >= 3:
            tier3_data = making_tier3_INPUT(end_date)
            tier3_json = json.dumps(tier3_data, indent=2, ensure_ascii=False)
            data_blocks.append(f"\n=== Macro Indicators (Tier 3) ===\n{tier3_json}")

        # 데이터 블록 결합
        combined_data = '\n'.join(data_blocks)

        # 템플릿 변수 치환
        prompt = template.replace('{{TIER}}', str(tier))
        prompt = prompt.replace('{{DATA_BLOCKS}}', combined_data)

        return prompt

    except FileNotFoundError:
        print(f"[오류] 사용자 프롬프트 템플릿을 찾을 수 없습니다: {template_path}")
        return None
    except Exception as e:
        print(f"[오류] 사용자 프롬프트 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


# 테스트 코드
if __name__ == "__main__":
    test_date = pd.Timestamp('2024-05-31')

    print("="*80)
    print("Tier 1 시스템 프롬프트 테스트")
    print("="*80)
    sys_prompt = making_system_prompt(tier=1)
    if sys_prompt:
        print(sys_prompt[:500] + "...\n")

    print("="*80)
    print("Tier 1 사용자 프롬프트 테스트")
    print("="*80)
    user_prompt = making_user_prompt(end_date=test_date, tier=1)
    if user_prompt:
        print(user_prompt[:500] + "...\n")

    print("="*80)
    print("Tier 2 사용자 프롬프트 테스트")
    print("="*80)
    user_prompt_2 = making_user_prompt(end_date=test_date, tier=2)
    if user_prompt_2:
        print(user_prompt_2[:500] + "...\n")

    print("="*80)
    print("Tier 3 사용자 프롬프트 테스트")
    print("="*80)
    user_prompt_3 = making_user_prompt(end_date=test_date, tier=3)
    if user_prompt_3:
        print(user_prompt_3[:500] + "...\n")
