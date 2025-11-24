import os
import json
import numpy as np
from scipy import stats
import glob

######################################
#            configuration           #
######################################

# 통계검정 진행할 반복실행 simul_name_base
simul_name_base = 'before_changing_prompt_2_'


######################################
#           Helper Functions         #
######################################

def find_json_files(simul_name_base, tier):
    """
    특정 Tier의 result_of_test 디렉토리에서 simul_name_base로 시작하는 JSON 파일 찾기

    Returns:
        list: 파일 경로 리스트 (번호 순으로 정렬됨)
    """
    base_dir = os.path.join("database", "logs")
    save_dir = os.path.join(base_dir, f"Tier{tier}", 'result_of_test')

    if not os.path.exists(save_dir):
        return []

    # simul_name_base로 시작하는 모든 JSON 파일 찾기
    pattern = os.path.join(save_dir, f'{simul_name_base}Tier{tier}_*.json')
    files = glob.glob(pattern)

    # 파일명의 숫자로 정렬
    def extract_number(filepath):
        filename = os.path.basename(filepath)
        # 'simul_name_base'Tier{tier}_{number}.json 형식에서 number 추출
        try:
            num_part = filename.split('_')[-1].replace('.json', '')
            return int(num_part)
        except:
            return 0

    files.sort(key=extract_number)
    return files


def load_tier_data(simul_name_base, tier):
    """
    특정 Tier의 모든 데이터 로드

    Returns:
        tuple: (AI_portfolio_returns, MVO_returns) 두 개의 numpy array
    """
    files = find_json_files(simul_name_base, tier)

    if not files:
        return np.array([]), np.array([])

    AI_portfolio_sample = []
    mvo_sample = []

    print(f"\n{'='*80}")
    print(f"Tier {tier} 데이터 수집 중... (찾은 파일: {len(files)}개)")
    print(f"{'='*80}\n")

    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # data[2]에 평균값 요약이 저장되어 있음
            summary = data[2]

            # AI Portfolio와 MVO의 평균 누적 수익률 추출
            ai_avg = summary['AI_portfolio']['final_avg_cumulative_return']
            mvo_avg = summary['MVO']['final_avg_cumulative_return']

            AI_portfolio_sample.append(ai_avg)
            mvo_sample.append(mvo_avg)

            print(f"[{i}/{len(files)}] {filename} (AI: {ai_avg*100:.2f}%, MVO: {mvo_avg*100:.2f}%)")

        except FileNotFoundError:
            print(f"[오류] 파일을 찾을 수 없습니다: {filepath}")
            continue
        except json.JSONDecodeError as e:
            print(f"[오류] JSON 파일 파싱 실패: {e}")
            continue
        except Exception as e:
            print(f"[오류] 예상치 못한 오류 발생: {e}")
            continue

    return np.array(AI_portfolio_sample), np.array(mvo_sample)


######################################
#          Data Collection           #
######################################

# 결과 저장 디렉토리 생성
base_dir = os.path.join("database", "logs")
os.makedirs(base_dir, exist_ok=True)
log_path = os.path.join(base_dir, "stat_test")
os.makedirs(log_path, exist_ok=True)

# 각 Tier별로 파일 개수 확인
print(f"\n{'='*80}")
print(f"'{simul_name_base}' 시뮬레이션 데이터 탐색 중...")
print(f"{'='*80}\n")

tier_file_counts = {}
for tier in [1, 2, 3]:
    files = find_json_files(simul_name_base, tier)
    tier_file_counts[tier] = len(files)
    print(f"Tier {tier}: {len(files)}개 파일 발견")

# 파일 개수 확인
unique_counts = set(tier_file_counts.values())
unique_counts.discard(0)  # 0개는 제외

if len(unique_counts) == 0:
    print(f"\n[오류] 모든 Tier에서 파일을 찾을 수 없습니다.")
    print(f"경로: database/logs/Tier[1-3]/result_of_test/{simul_name_base}Tier*_*.json")
    exit(1)

if len(unique_counts) > 1:
    print(f"\n[경고] Tier별 파일 개수가 다릅니다:")
    for tier, count in tier_file_counts.items():
        print(f"  Tier {tier}: {count}개")
    print(f"\n통계검정을 위해서는 모든 Tier의 파일 개수가 동일해야 합니다.")
    print(f"프로그램을 종료합니다.")
    exit(1)

repetition_counts = list(unique_counts)[0]
print(f"\n[확인] 모든 Tier에서 {repetition_counts}개의 파일이 발견되었습니다.")
print(f"통계검정을 진행합니다.\n")

# 각 Tier 데이터 로드
tier1_ai, tier1_mvo = load_tier_data(simul_name_base, 1)
tier2_ai, tier2_mvo = load_tier_data(simul_name_base, 2)
tier3_ai, tier3_mvo = load_tier_data(simul_name_base, 3)

# 데이터 검증
print(f"\n{'='*80}")
print(f"데이터 로드 완료")
print(f"{'='*80}")
print(f"Tier 1: AI={len(tier1_ai)}개, MVO={len(tier1_mvo)}개")
print(f"Tier 2: AI={len(tier2_ai)}개, MVO={len(tier2_mvo)}개")
print(f"Tier 3: AI={len(tier3_ai)}개, MVO={len(tier3_mvo)}개")
print(f"{'='*80}\n")

# 최소 표본 수 확인
if len(tier1_ai) == 0:
    print("[오류] Tier 1 데이터가 없습니다. 프로그램을 종료합니다.")
    exit(1)

# 유의수준
alpha = 0.05

######################################
#          Statistical Tests         #
######################################

# ============================================================
# 통계 검정 1: Tier 1 평균 > 0
# ============================================================
print(f"\n{'='*80}")
print("통계 검정 1: Tier 1 AI Portfolio의 평균 수익률이 0보다 큰가?")
print(f"{'='*80}\n")

t_stat_1, p_val_1 = stats.ttest_1samp(tier1_ai, popmean=0, alternative='greater')

print(f"[기술 통계]")
print(f"평균 수익률: {tier1_ai.mean()*100:.2f}%")
print(f"표준편차: {tier1_ai.std(ddof=1)*100:.2f}%")
print(f"표본 크기: {len(tier1_ai)}")

print(f"\n[t검정 결과]")
print(f"귀무가설 (H0): μ_Tier1 = 0")
print(f"대립가설 (H1): μ_Tier1 > 0")
print(f"t-통계량: {t_stat_1:.4f}")
print(f"p-value: {p_val_1:.4f}")

print(f"\n[판정] (유의수준 α = {alpha})")
if p_val_1 < alpha:
    print(f"[O] p-value ({p_val_1:.4f}) < {alpha}")
    print("-> 귀무가설 기각")
    print(f"-> Tier 1의 평균 수익률({tier1_ai.mean()*100:.2f}%)은 0보다 통계적으로 유의하게 큽니다.")
else:
    print(f"[X] p-value ({p_val_1:.4f}) >= {alpha}")
    print("-> 귀무가설 기각 실패")
    print("-> Tier 1의 평균 수익률이 0보다 크다고 할 수 없습니다.")

# ============================================================
# 통계 검정 2: Tier 1 평균 > MVO 평균
# ============================================================
print(f"\n{'='*80}")
print("통계 검정 2: Tier 1 AI Portfolio의 평균 수익률이 MVO보다 큰가?")
print(f"{'='*80}\n")

excess_tier1_vs_mvo = tier1_ai - tier1_mvo
t_stat_2, p_val_2 = stats.ttest_1samp(excess_tier1_vs_mvo, popmean=0, alternative='greater')

print(f"[기술 통계]")
print(f"Tier 1 AI 평균: {tier1_ai.mean()*100:.2f}%")
print(f"MVO 평균: {tier1_mvo.mean()*100:.2f}%")
print(f"평균 초과 수익률: {excess_tier1_vs_mvo.mean()*100:.2f}%")
print(f"초과 수익률 표준편차: {excess_tier1_vs_mvo.std(ddof=1)*100:.2f}%")
print(f"표본 크기: {len(excess_tier1_vs_mvo)}")

print(f"\n[대응표본 t검정 결과]")
print(f"귀무가설 (H0): μ_Tier1 - μ_MVO = 0")
print(f"대립가설 (H1): μ_Tier1 - μ_MVO > 0")
print(f"t-통계량: {t_stat_2:.4f}")
print(f"p-value: {p_val_2:.4f}")

print(f"\n[판정] (유의수준 α = {alpha})")
if p_val_2 < alpha:
    print(f"[O] p-value ({p_val_2:.4f}) < {alpha}")
    print("-> 귀무가설 기각")
    print(f"-> Tier 1이 MVO보다 평균 {excess_tier1_vs_mvo.mean()*100:.2f}% 높은 수익률을 보이며,")
    print("   이는 통계적으로 유의합니다.")
else:
    print(f"[X] p-value ({p_val_2:.4f}) >= {alpha}")
    print("-> 귀무가설 기각 실패")
    print("-> Tier 1이 MVO보다 유의하게 높다고 할 수 없습니다.")

# ============================================================
# 통계 검정 3: Tier 2 평균 > Tier 1 평균
# ============================================================
print(f"\n{'='*80}")
print("통계 검정 3: Tier 2 AI Portfolio의 평균 수익률이 Tier 1보다 큰가?")
print(f"{'='*80}\n")

if len(tier2_ai) > 0:
    excess_tier2_vs_tier1 = tier2_ai - tier1_ai
    t_stat_3, p_val_3 = stats.ttest_1samp(excess_tier2_vs_tier1, popmean=0, alternative='greater')

    print(f"[기술 통계]")
    print(f"Tier 2 AI 평균: {tier2_ai.mean()*100:.2f}%")
    print(f"Tier 1 AI 평균: {tier1_ai.mean()*100:.2f}%")
    print(f"평균 초과 수익률: {excess_tier2_vs_tier1.mean()*100:.2f}%")
    print(f"초과 수익률 표준편차: {excess_tier2_vs_tier1.std(ddof=1)*100:.2f}%")
    print(f"표본 크기: {len(excess_tier2_vs_tier1)}")

    print(f"\n[대응표본 t검정 결과]")
    print(f"귀무가설 (H0): μ_Tier2 - μ_Tier1 = 0")
    print(f"대립가설 (H1): μ_Tier2 - μ_Tier1 > 0")
    print(f"t-통계량: {t_stat_3:.4f}")
    print(f"p-value: {p_val_3:.4f}")

    print(f"\n[판정] (유의수준 α = {alpha})")
    if p_val_3 < alpha:
        print(f"[O] p-value ({p_val_3:.4f}) < {alpha}")
        print("-> 귀무가설 기각")
        print(f"-> Tier 2가 Tier 1보다 평균 {excess_tier2_vs_tier1.mean()*100:.2f}% 높은 수익률을 보이며,")
        print("   이는 통계적으로 유의합니다.")
    else:
        print(f"[X] p-value ({p_val_3:.4f}) >= {alpha}")
        print("-> 귀무가설 기각 실패")
        print("-> Tier 2가 Tier 1보다 유의하게 높다고 할 수 없습니다.")
else:
    print("[경고] Tier 2 데이터가 없어 검정을 수행할 수 없습니다.")
    t_stat_3, p_val_3 = None, None
    excess_tier2_vs_tier1 = np.array([])

# ============================================================
# 통계 검정 4: Tier 3 평균 > Tier 2 평균
# ============================================================
print(f"\n{'='*80}")
print("통계 검정 4: Tier 3 AI Portfolio의 평균 수익률이 Tier 2보다 큰가?")
print(f"{'='*80}\n")

if len(tier3_ai) > 0 and len(tier2_ai) > 0:
    excess_tier3_vs_tier2 = tier3_ai - tier2_ai
    t_stat_4, p_val_4 = stats.ttest_1samp(excess_tier3_vs_tier2, popmean=0, alternative='greater')

    print(f"[기술 통계]")
    print(f"Tier 3 AI 평균: {tier3_ai.mean()*100:.2f}%")
    print(f"Tier 2 AI 평균: {tier2_ai.mean()*100:.2f}%")
    print(f"평균 초과 수익률: {excess_tier3_vs_tier2.mean()*100:.2f}%")
    print(f"초과 수익률 표준편차: {excess_tier3_vs_tier2.std(ddof=1)*100:.2f}%")
    print(f"표본 크기: {len(excess_tier3_vs_tier2)}")

    print(f"\n[대응표본 t검정 결과]")
    print(f"귀무가설 (H0): μ_Tier3 - μ_Tier2 = 0")
    print(f"대립가설 (H1): μ_Tier3 - μ_Tier2 > 0")
    print(f"t-통계량: {t_stat_4:.4f}")
    print(f"p-value: {p_val_4:.4f}")

    print(f"\n[판정] (유의수준 α = {alpha})")
    if p_val_4 < alpha:
        print(f"[O] p-value ({p_val_4:.4f}) < {alpha}")
        print("-> 귀무가설 기각")
        print(f"-> Tier 3이 Tier 2보다 평균 {excess_tier3_vs_tier2.mean()*100:.2f}% 높은 수익률을 보이며,")
        print("   이는 통계적으로 유의합니다.")
    else:
        print(f"[X] p-value ({p_val_4:.4f}) >= {alpha}")
        print("-> 귀무가설 기각 실패")
        print("-> Tier 3이 Tier 2보다 유의하게 높다고 할 수 없습니다.")
else:
    if len(tier3_ai) == 0:
        print("[경고] Tier 3 데이터가 없어 검정을 수행할 수 없습니다.")
    else:
        print("[경고] Tier 2 데이터가 없어 검정을 수행할 수 없습니다.")
    t_stat_4, p_val_4 = None, None
    excess_tier3_vs_tier2 = np.array([])

# ============================================================
# 결과 저장
# ============================================================
results = {
    "simulation_info": {
        "simul_name_base": simul_name_base,
        "repetition_counts": repetition_counts,
        "tier1_samples": len(tier1_ai),
        "tier2_samples": len(tier2_ai),
        "tier3_samples": len(tier3_ai)
    },
    "test_1_Tier1_vs_zero": {
        "hypothesis": {
            "H0": "μ_Tier1 = 0",
            "H1": "μ_Tier1 > 0"
        },
        "statistics": {
            "mean": float(tier1_ai.mean()),
            "std": float(tier1_ai.std(ddof=1)),
            "sample_size": len(tier1_ai),
            "t_statistic": float(t_stat_1),
            "p_value": float(p_val_1)
        },
        "result": {
            "reject_H0": bool(p_val_1 < alpha),
            "conclusion": "Tier 1 평균 > 0 (유의)" if p_val_1 < alpha else "통계적으로 유의하지 않음"
        }
    },
    "test_2_Tier1_vs_MVO": {
        "hypothesis": {
            "H0": "μ_Tier1 - μ_MVO = 0",
            "H1": "μ_Tier1 - μ_MVO > 0"
        },
        "statistics": {
            "Tier1_mean": float(tier1_ai.mean()),
            "MVO_mean": float(tier1_mvo.mean()),
            "excess_return_mean": float(excess_tier1_vs_mvo.mean()),
            "excess_return_std": float(excess_tier1_vs_mvo.std(ddof=1)),
            "sample_size": len(excess_tier1_vs_mvo),
            "t_statistic": float(t_stat_2),
            "p_value": float(p_val_2)
        },
        "result": {
            "reject_H0": bool(p_val_2 < alpha),
            "conclusion": "Tier 1 > MVO (유의)" if p_val_2 < alpha else "통계적으로 유의하지 않음"
        }
    }
}

# 통계 검정 3 결과 추가
if t_stat_3 is not None and p_val_3 is not None:
    results["test_3_Tier2_vs_Tier1"] = {
        "hypothesis": {
            "H0": "μ_Tier2 - μ_Tier1 = 0",
            "H1": "μ_Tier2 - μ_Tier1 > 0"
        },
        "statistics": {
            "Tier2_mean": float(tier2_ai.mean()),
            "Tier1_mean": float(tier1_ai.mean()),
            "excess_return_mean": float(excess_tier2_vs_tier1.mean()),
            "excess_return_std": float(excess_tier2_vs_tier1.std(ddof=1)),
            "sample_size": len(excess_tier2_vs_tier1),
            "t_statistic": float(t_stat_3),
            "p_value": float(p_val_3)
        },
        "result": {
            "reject_H0": bool(p_val_3 < alpha),
            "conclusion": "Tier 2 > Tier 1 (유의)" if p_val_3 < alpha else "통계적으로 유의하지 않음"
        }
    }
else:
    results["test_3_Tier2_vs_Tier1"] = {
        "result": {
            "conclusion": "Tier 2 데이터 없음 - 검정 불가"
        }
    }

# 통계 검정 4 결과 추가
if t_stat_4 is not None and p_val_4 is not None:
    results["test_4_Tier3_vs_Tier2"] = {
        "hypothesis": {
            "H0": "μ_Tier3 - μ_Tier2 = 0",
            "H1": "μ_Tier3 - μ_Tier2 > 0"
        },
        "statistics": {
            "Tier3_mean": float(tier3_ai.mean()),
            "Tier2_mean": float(tier2_ai.mean()),
            "excess_return_mean": float(excess_tier3_vs_tier2.mean()),
            "excess_return_std": float(excess_tier3_vs_tier2.std(ddof=1)),
            "sample_size": len(excess_tier3_vs_tier2),
            "t_statistic": float(t_stat_4),
            "p_value": float(p_val_4)
        },
        "result": {
            "reject_H0": bool(p_val_4 < alpha),
            "conclusion": "Tier 3 > Tier 2 (유의)" if p_val_4 < alpha else "통계적으로 유의하지 않음"
        }
    }
else:
    results["test_4_Tier3_vs_Tier2"] = {
        "result": {
            "conclusion": "Tier 2 또는 Tier 3 데이터 없음 - 검정 불가"
        }
    }

# JSON 저장
output_filename = f'{simul_name_base}all_tiers_stat_test.json'
output_filepath = os.path.join(log_path, output_filename)

with open(output_filepath, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"\n{'='*80}")
print(f"통계 검정 결과 저장 완료: {output_filepath}")
print(f"{'='*80}\n")
