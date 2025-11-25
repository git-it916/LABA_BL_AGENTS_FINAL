import os
import json
import numpy as np
import matplotlib.pyplot as plt

######################################
#            configuration           #
######################################

# 시각화할 시뮬레이션 이름
simul_name = 'test_5_Tier3_3'  # 예: 'before_changing_prompt_2_Tier1_1'


######################################
#           Helper Functions         #
######################################

def load_result_file(simul_name, tier):
    """
    특정 Tier의 result_of_test 디렉토리에서 시뮬레이션 결과 파일 로드

    Args:
        simul_name (str): 시뮬레이션 파일 이름 (확장자 제외)
                         예: 'before_changing_prompt_2_Tier1_1'
        tier (int): Tier 번호 (1, 2, 3)

    Returns:
        dict or None: 로드된 JSON 데이터, 실패 시 None
    """
    import re

    # simul_name에서 Tier 번호를 해당 tier로 교체
    # 예: 'before_changing_prompt_2_Tier1_1' -> 'before_changing_prompt_2_Tier2_1'
    tier_adjusted_name = re.sub(r'Tier\d+', f'Tier{tier}', simul_name)

    base_dir = os.path.join("database", "logs")
    save_dir = os.path.join(base_dir, f"Tier{tier}", 'result_of_test')
    filepath = os.path.join(save_dir, f'{tier_adjusted_name}.json')

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"[성공] Tier {tier} 파일 로드: {tier_adjusted_name}.json")
        return data
    except FileNotFoundError:
        print(f"[오류] Tier {tier} 파일을 찾을 수 없습니다: {tier_adjusted_name}.json")
        print(f"       경로: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"[오류] Tier {tier} JSON 파일 파싱 실패: {e}")
        return None
    except Exception as e:
        print(f"[오류] Tier {tier} 파일 로드 중 예상치 못한 오류: {e}")
        return None


def extract_avg_cumulative_returns(data, portfolio_name):
    """
    JSON 데이터에서 특정 포트폴리오의 평균 누적 수익률 추출

    Args:
        data (list): JSON 데이터 (3개 요소: [AI_portfolio by date, MVO by date, summary])
        portfolio_name (str): 'AI_portfolio' 또는 'MVO'

    Returns:
        list or None: 평균 누적 수익률 리스트, 실패 시 None
    """
    try:
        # data[2]는 summary에 avg_cumulative_returns가 포함되어 있음
        summary = data[2]

        if portfolio_name not in summary:
            print(f"[오류] '{portfolio_name}'이(가) summary에 없습니다. 사용 가능한 키: {list(summary.keys())}")
            return None

        portfolio_data = summary[portfolio_name]
        return portfolio_data.get('avg_cumulative_returns', None)
    except (IndexError, KeyError, TypeError) as e:
        print(f"[오류] {portfolio_name} 데이터 추출 실패: {e}")
        return None


def check_mvo_consistency(tier1_data, tier2_data, tier3_data):
    """
    세 Tier의 MVO 누적 수익률이 동일한지 확인

    Returns:
        bool: 동일하면 True, 다르면 False
    """
    mvo1 = extract_avg_cumulative_returns(tier1_data, 'MVO')
    mvo2 = extract_avg_cumulative_returns(tier2_data, 'MVO')
    mvo3 = extract_avg_cumulative_returns(tier3_data, 'MVO')

    if mvo1 is None or mvo2 is None or mvo3 is None:
        print("[오류] MVO 데이터 추출 실패")
        return False

    # numpy array로 변환하여 비교
    mvo1_arr = np.array(mvo1)
    mvo2_arr = np.array(mvo2)
    mvo3_arr = np.array(mvo3)

    # 길이 확인
    if len(mvo1_arr) != len(mvo2_arr) or len(mvo2_arr) != len(mvo3_arr):
        print(f"[오류] MVO 데이터 길이 불일치: Tier1={len(mvo1_arr)}, Tier2={len(mvo2_arr)}, Tier3={len(mvo3_arr)}")
        return False

    # 값 비교 (부동소수점 오차 허용)
    if not np.allclose(mvo1_arr, mvo2_arr, rtol=1e-9, atol=1e-9):
        print("[오류] Tier1과 Tier2의 MVO 데이터가 다릅니다.")
        return False

    if not np.allclose(mvo2_arr, mvo3_arr, rtol=1e-9, atol=1e-9):
        print("[오류] Tier2와 Tier3의 MVO 데이터가 다릅니다.")
        return False

    print("[확인] 세 Tier의 MVO 데이터가 동일합니다.")
    return True


######################################
#          Main Execution            #
######################################

print(f"\n{'='*80}")
print(f"시뮬레이션 결과 시각화")
print(f"{'='*80}\n")
print(f"시뮬레이션 이름: {simul_name}\n")

# 1. 세 Tier 데이터 로드
print("[1/4] 데이터 로딩 중...")
tier1_data = load_result_file(simul_name, 1)
tier2_data = load_result_file(simul_name, 2)
tier3_data = load_result_file(simul_name, 3)

if tier1_data is None or tier2_data is None or tier3_data is None:
    print("\n[오류] 일부 Tier 데이터를 로드할 수 없습니다. 프로그램을 종료합니다.")
    exit(1)

# 2. MVO 일관성 확인
print(f"\n[2/4] MVO 데이터 일관성 확인 중...")
if not check_mvo_consistency(tier1_data, tier2_data, tier3_data):
    print("\n[오류] MVO 데이터가 일치하지 않습니다. 프로그램을 종료합니다.")
    exit(1)

# 3. 누적 수익률 데이터 추출
print(f"\n[3/4] 누적 수익률 데이터 추출 중...")
tier1_ai = extract_avg_cumulative_returns(tier1_data, 'AI_portfolio')
tier2_ai = extract_avg_cumulative_returns(tier2_data, 'AI_portfolio')
tier3_ai = extract_avg_cumulative_returns(tier3_data, 'AI_portfolio')
mvo = extract_avg_cumulative_returns(tier1_data, 'MVO')  # 어느 Tier든 동일

if tier1_ai is None or tier2_ai is None or tier3_ai is None or mvo is None:
    print("[오류] 누적 수익률 데이터 추출 실패. 프로그램을 종료합니다.")
    exit(1)

# numpy array로 변환
tier1_ai = np.array(tier1_ai)
tier2_ai = np.array(tier2_ai)
tier3_ai = np.array(tier3_ai)
mvo = np.array(mvo)

# 백테스트 거래일 수
backtest_days = len(tier1_ai)

print(f"- Tier 1 AI Portfolio: {backtest_days} days")
print(f"- Tier 2 AI Portfolio: {backtest_days} days")
print(f"- Tier 3 AI Portfolio: {backtest_days} days")
print(f"- MVO: {backtest_days} days")

# 4. 시각화
print(f"\n[4/4] 시각화 생성 중...")

# Figure 생성
fig, ax = plt.subplots(figsize=(14, 8))

# x축: 영업일 (1부터 시작)
days = np.arange(1, backtest_days + 1)

# 누적 수익률 플롯 (백분율 변환)
ax.plot(days, tier1_ai * 100, label='Tier 1 (Technical)', marker='o', linewidth=2, markersize=4)
ax.plot(days, tier2_ai * 100, label='Tier 2 (Technical + Accounting)', marker='s', linewidth=2, markersize=4)
ax.plot(days, tier3_ai * 100, label='Tier 3 (Technical + Accounting + Macro)', marker='^', linewidth=2, markersize=4)
ax.plot(days, mvo * 100, label='MVO (Baseline)', marker='x', linewidth=2, markersize=4, linestyle='--', color='gray')

# 0% 기준선
ax.axhline(0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)

# 축 레이블 및 제목
ax.set_xlabel('Business Days', fontsize=12)
ax.set_ylabel('Average Cumulative Return (%)', fontsize=12)
ax.set_title(f'Portfolio Performance Comparison: {simul_name}', fontsize=14, fontweight='bold')

# 범례
ax.legend(loc='best', fontsize=10, frameon=True, shadow=True)

# 그리드
ax.grid(True, alpha=0.3, linestyle='--')

# x축 정수로만 표시
ax.set_xticks(days)

# 레이아웃 조정
plt.tight_layout()

# 저장
output_dir = os.path.join("database", "logs")
os.makedirs(output_dir, exist_ok=True)
output_filename = f'{simul_name}_visualization.png'
output_filepath = os.path.join(output_dir, output_filename)

plt.savefig(output_filepath, dpi=300, bbox_inches='tight')
print(f"\n[성공] 시각화 저장 완료: {output_filepath}")

# 화면에 표시 (선택 사항)
# plt.show()

# 5. 최종 수익률 비교표 출력
print(f"\n{'='*80}")
print(f"최종 평균 누적 수익률 비교")
print(f"{'='*80}\n")
print(f"{'포트폴리오':<30} | {'최종 수익률':>12} | {'MVO 대비 초과수익률':>20}")
print(f"{'-'*80}")
print(f"{'Tier 1 AI Portfolio':<30} | {tier1_ai[-1]*100:>11.2f}% | {(tier1_ai[-1] - mvo[-1])*100:>+19.2f}%")
print(f"{'Tier 2 AI Portfolio':<30} | {tier2_ai[-1]*100:>11.2f}% | {(tier2_ai[-1] - mvo[-1])*100:>+19.2f}%")
print(f"{'Tier 3 AI Portfolio':<30} | {tier3_ai[-1]*100:>11.2f}% | {(tier3_ai[-1] - mvo[-1])*100:>+19.2f}%")
print(f"{'MVO (Baseline)':<30} | {mvo[-1]*100:>11.2f}% | {0.0:>+19.2f}%")
print(f"\n{'='*80}")
print(f"완료")
print(f"{'='*80}\n")
