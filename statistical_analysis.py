import os
import json
import numpy as np
from scipy import stats

######################################
#            configuration           #
######################################

# 통계검정 진행할 반복실행 simul_name_base
simul_name_base = 'before_changing_prompt_'

# 통계검정 진행할 Tier
Tier = 1

# 표본 수(=반복횟수)
repetition_counts = 8


######################################
#                test                #
######################################

# 결과 저장 디렉토리 생성
base_dir = os.path.join("database", "logs")
os.makedirs(base_dir, exist_ok=True)
log_path = os.path.join(base_dir, "stat_test")
os.makedirs(log_path, exist_ok=True)

AI_portfolio_sample = []
mvo_sample = []

# logs에서 통계검정 진행할 Tier 데이터 불러오기
print(f"\n{'='*80}")
print(f"데이터 수집 시작: {simul_name_base}Tier{Tier}")
print(f"{'='*80}\n")

for i in range(1, repetition_counts + 1):
    save_dir = os.path.join(base_dir, f"Tier{Tier}", 'result_of_test')
    filename = f'{simul_name_base}Tier{Tier}_{i}.json'
    filepath = os.path.join(save_dir, filename)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # data[2]에 평균값 요약이 저장되어 있음
        summary = data[2]

        # AI Portfolio와 MVO의 평균 수익률 추출
        ai_avg = summary['AI_portfolio']['final_avg_return']
        mvo_avg = summary['MVO']['final_avg_return']

        AI_portfolio_sample.append(ai_avg)
        mvo_sample.append(mvo_avg)

        print(f"[{i}/{repetition_counts}] JSON 파일 로드 완료: {filename} (AI 평균: {ai_avg*100:.2f}%, MVO 평균: {mvo_avg*100:.2f}%)")

    except FileNotFoundError:
        print(f"[오류] 파일을 찾을 수 없습니다: {filepath}")
        continue
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 파일 파싱 실패: {e}")
        continue
    except Exception as e:
        print(f"[오류] 예상치 못한 오류 발생: {e}")
        continue

print(f"\n{'='*80}")
print(f"AI Portfolio 표본 수: {len(AI_portfolio_sample)}")
print(f"MVO 표본 수: {len(mvo_sample)}")
print(f"{'='*80}\n")

# 표본 수 확인
if len(AI_portfolio_sample) == 0 or len(mvo_sample) == 0:
    print("[오류] 데이터가 없습니다. 프로그램을 종료합니다.")
    exit(1)

if len(AI_portfolio_sample) != len(mvo_sample):
    print("[경고] AI Portfolio와 MVO의 표본 수가 다릅니다.")

# ============================================================
# 통계 검정 1: AI Portfolio 평균 > 0
# ============================================================
print(f"\n{'='*80}")
print("통계 검정 1: AI Portfolio의 평균 수익률이 0보다 큰가?")
print(f"{'='*80}\n")

AI_array = np.array(AI_portfolio_sample)
t_stat_1, p_val_1 = stats.ttest_1samp(AI_array, popmean=0, alternative='greater')

print(f"[기술 통계]")
print(f"평균 수익률: {AI_array.mean()*100:.2f}%")
print(f"표준편차: {AI_array.std(ddof=1)*100:.2f}%")
print(f"표본 크기: {len(AI_array)}")

print(f"\n[t검정 결과]")
print(f"귀무가설 (H0): μ = 0")
print(f"대립가설 (H1): μ > 0")
print(f"t-통계량: {t_stat_1:.4f}")
print(f"p-value: {p_val_1:.4f}")

alpha = 0.05
print(f"\n[판정] (유의수준 α = {alpha})")
if p_val_1 < alpha:
    print(f"[O] p-value ({p_val_1:.4f}) < {alpha}")
    print("-> 귀무가설 기각")
    print(f"-> AI Portfolio의 평균 수익률({AI_array.mean()*100:.2f}%)은 0보다 통계적으로 유의하게 큽니다.")
else:
    print(f"[X] p-value ({p_val_1:.4f}) >= {alpha}")
    print("-> 귀무가설 기각 실패")
    print("-> AI Portfolio의 평균 수익률이 0보다 크다고 할 수 없습니다.")

# ============================================================
# 통계 검정 2: AI Portfolio 평균 > MVO 평균
# ============================================================
print(f"\n{'='*80}")
print("통계 검정 2: AI Portfolio의 평균 수익률이 MVO보다 큰가?")
print(f"{'='*80}\n")

mvo_array = np.array(mvo_sample)
excess_returns = AI_array - mvo_array

t_stat_2, p_val_2 = stats.ttest_1samp(excess_returns, popmean=0, alternative='greater')

print(f"[기술 통계]")
print(f"AI Portfolio 평균: {AI_array.mean()*100:.2f}%")
print(f"MVO 평균: {mvo_array.mean()*100:.2f}%")
print(f"평균 초과 수익률: {excess_returns.mean()*100:.2f}%")
print(f"초과 수익률 표준편차: {excess_returns.std(ddof=1)*100:.2f}%")
print(f"표본 크기: {len(excess_returns)}")

print(f"\n[대응표본 t검정 결과]")
print(f"귀무가설 (H0): μ_AI - μ_MVO = 0")
print(f"대립가설 (H1): μ_AI - μ_MVO > 0")
print(f"t-통계량: {t_stat_2:.4f}")
print(f"p-value: {p_val_2:.4f}")

print(f"\n[판정] (유의수준 α = {alpha})")
if p_val_2 < alpha:
    print(f"[O] p-value ({p_val_2:.4f}) < {alpha}")
    print("-> 귀무가설 기각")
    print(f"-> AI Portfolio가 MVO보다 평균 {excess_returns.mean()*100:.2f}% 높은 수익률을 보이며,")
    print("   이는 통계적으로 유의합니다.")
else:
    print(f"[X] p-value ({p_val_2:.4f}) >= {alpha}")
    print("-> 귀무가설 기각 실패")
    print("-> AI Portfolio가 MVO보다 유의하게 높다고 할 수 없습니다.")

# ============================================================
# 결과 저장
# ============================================================
results = {
    "simulation_info": {
        "simul_name_base": simul_name_base,
        "Tier": Tier,
        "repetition_counts": repetition_counts,
        "total_samples": len(AI_array)
    },
    "test_1_AI_vs_zero": {
        "hypothesis": {
            "H0": "μ = 0",
            "H1": "μ > 0"
        },
        "statistics": {
            "mean": float(AI_array.mean()),
            "std": float(AI_array.std(ddof=1)),
            "sample_size": len(AI_array),
            "t_statistic": float(t_stat_1),
            "p_value": float(p_val_1)
        },
        "result": {
            "reject_H0": bool(p_val_1 < alpha),
            "conclusion": "AI Portfolio 평균 > 0 (유의)" if p_val_1 < alpha else "통계적으로 유의하지 않음"
        }
    },
    "test_2_AI_vs_MVO": {
        "hypothesis": {
            "H0": "μ_AI - μ_MVO = 0",
            "H1": "μ_AI - μ_MVO > 0"
        },
        "statistics": {
            "AI_mean": float(AI_array.mean()),
            "MVO_mean": float(mvo_array.mean()),
            "excess_return_mean": float(excess_returns.mean()),
            "excess_return_std": float(excess_returns.std(ddof=1)),
            "sample_size": len(excess_returns),
            "t_statistic": float(t_stat_2),
            "p_value": float(p_val_2)
        },
        "result": {
            "reject_H0": bool(p_val_2 < alpha),
            "conclusion": "AI Portfolio > MVO (유의)" if p_val_2 < alpha else "통계적으로 유의하지 않음"
        }
    }
}

# JSON 저장
output_filename = f'{simul_name_base}Tier{Tier}_stat_test.json'
output_filepath = os.path.join(log_path, output_filename)

with open(output_filepath, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"\n{'='*80}")
print(f"통계 검정 결과 저장 완료: {output_filepath}")
print(f"{'='*80}\n")
