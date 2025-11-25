# LABA_BL_AGENTS_FINAL

> **LLM-Agent 기반 Black-Litterman 포트폴리오 최적화 시스템**
>
> LABA (Lab for Accounting Big Data & Artificial Intelligence) 4th Project-Based Semester

---

## 📌 프로젝트 개요

이 프로젝트는 **Llama 3 LLM을 활용하여 Black-Litterman 포트폴리오 최적화 모델에 자동으로 투자 견해(views)를 생성하고 통합하는 시스템**입니다.

### 핵심 아이디어

- 기존 Black-Litterman 모델은 투자자의 주관적 견해를 수작업으로 입력
- 이 프로젝트는 **LLM이 자동으로 섹터 간 상대적 수익률 전망을 생성**
- **3단계 데이터 분석**(기술적/회계/거시)을 점진적으로 제공하여 정교한 견해 도출

### 주요 특징

✅ **다층 데이터 분석 파이프라인** (Tier 1-3)
- Tier 1: 기술적 지표 (CAGR, 수익률, 변동성, 추세)
- Tier 2: 회계 지표 (P/E, ROE, ROA 등 재무지표)
- Tier 3: 거시경제 지표 (현재 미구현)

✅ **LLM 기반 구조화된 뷰 생성**
- Llama 3 8B 모델 사용 (4-bit 양자화)
- JSON 형식 출력으로 자동 파싱

✅ **베이지안 포트폴리오 최적화**
- Black-Litterman 모델 (이론적 정확성 100%)
- Mean-Variance Optimization (MVO)

✅ **백테스팅 및 성과 검증**
- 복리 누적 수익률 (CAR) 계산
- NONE_view (뷰 없는 BL 베이스라인) 대비 초과 성과 측정
  - AI_portfolio: LLM 뷰 + BL + MVO
  - NONE_view: 뷰 없는 BL (P=0, 시장 균형 수익률 사용)

---

## 🚀 빠른 시작

### 1. 환경 설정

#### 가상 환경 생성 및 활성화

**Windows (PowerShell)**:
```powershell
python -m venv .venv
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 의존성 설치

```bash
pip install -r requirements.txt
```

**주요 패키지**:
- `torch==2.5.1+cu121` (CUDA 12.1 필요)
- `transformers==4.57.1`
- `numpy==2.3.4`
- `pandas==2.3.3`
- `scipy==1.16.3`

#### GPU 확인

```python
import torch
print(f"CUDA 사용 가능: {torch.cuda.is_available()}")
print(f"GPU 이름: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

**⚠️ 중요**: 이 프로젝트는 Llama 3 8B 모델 실행을 위해 **NVIDIA GPU가 필수**입니다.

---

### 2. 데이터 준비

필수 데이터 파일을 `database/` 디렉토리에 배치하세요:

- `final_stock_months.parquet` - 월별 주식 수익률 데이터
- `final_stock_daily.parquet` - 일일 주식 수익률 데이터
- `DTB3.csv` - 3개월 US Treasury Bill 수익률 (무위험 수익률)
- `compustat_2021.01_2024.12.csv` - 회계 데이터 (2021-2024)
- `filtered_sp500_data.parquet` - S&P500 필터링 데이터

---

### 3. 실행

#### 단일 시점 백테스트

```bash
python run_single.py
```

**대화형 입력 예시**:
```
시뮬레이션 이름: test_validation
Tier (1, 2, 3): 2
예측 기준일 (YYYY-MM-DD): 2024-05-31
tau 값 (예: 0.025): 0.025
백테스트 거래일 수 (5-250, 기본 20): 20
```

#### 일괄 백테스트

```bash
python run_batch.py
```

**대화형 입력 예시**:
```
시뮬레이션 이름: batch_test
Tier (1, 2, 3): 2
시작 날짜 (YYYY-MM-DD): 2024-05-01
종료 날짜 (YYYY-MM-DD): 2024-12-31
tau 값 (예: 0.025): 0.025
백테스트 거래일 수 (5-250, 기본 20): 20
```

**출력 예시**:
```
평균 NONE_view (베이스라인) 성과: 5.23%
평균 AI_portfolio 성과: 7.89%
평균 초과 성과: 2.66%
승률: 75.0%

※ NONE_view: 뷰 없는 Black-Litterman (P=0, 시장 균형 수익률 기반)
```

#### 커스텀 실행 (run.py 수정)

```python
if __name__ == "__main__":
    simul_name = 'my_simulation'  # 시뮬레이션 이름
    Tier = 2                       # 분석 단계 (1, 2, 3)
    tau = 0.025                    # BL 불확실성 계수

    forecast_period = [
        "24-05-31",
        "24-06-30",
        "24-07-31",
        # ... 추가 기간
    ]

    from aiportfolio.scene import scene
    results = scene(simul_name, Tier, tau, forecast_period)
    print(f"완료: {len(results)}개 기간")
```

---

## 📂 프로젝트 구조

```
LABA_BL_AGENTS_FINAL/
│
├── aiportfolio/                    # 핵심 패키지
│   │
│   ├── agents/                     # LLM 에이전트
│   │   ├── prepare/                # 단계별 지표 계산
│   │   │   ├── Tier1_calculate.py  # 기술적 지표
│   │   │   ├── Tier2_calculate.py  # 회계 지표
│   │   │   └── Tier3_calculate.py  # 거시 지표 (미구현)
│   │   │
│   │   ├── Llama_view_generator.py # 뷰 생성 오케스트레이션
│   │   ├── converting_viewtomatrix.py # 뷰 → BL 매개변수 변환
│   │   ├── prompt_maker.py         # 프롬프트 동적 생성
│   │   └── prompt_template/        # 프롬프트 템플릿
│   │
│   ├── BL_MVO/                     # Black-Litterman & MVO
│   │   ├── BL_params/
│   │   │   ├── market_params.py    # 시장 매개변수 (Pi, Sigma, Lambda)
│   │   │   └── view_params.py      # 뷰 매개변수 (P, Q, Omega)
│   │   │
│   │   ├── BL_opt.py               # Black-Litterman 모델 실행
│   │   └── MVO_opt.py              # Mean-Variance Optimization
│   │
│   ├── backtest/                   # 백테스팅
│   │   ├── data_prepare.py         # 데이터 준비
│   │   └── final_Ret.py            # 성과 계산 (CAR)
│   │
│   ├── util/                       # 유틸리티
│   │   ├── data_load/              # 데이터 로딩
│   │   ├── making_rollingdate.py   # 롤링 기간 생성
│   │   └── save_log_as_json.py     # 결과 저장
│   │
│   └── scene.py                    # 메인 오케스트레이션
│
├── database/                       # 데이터 저장소
│   ├── logs/                       # 시뮬레이션 결과
│   │   └── Tier[1-3]/
│   │       ├── result_of_BL-MVO/   # BL-MVO 가중치
│   │       ├── LLM-view/           # LLM 생성 뷰
│   │       └── result_of_test/     # 백테스트 결과
│   │
│   ├── final_stock_months.parquet
│   ├── final_stock_daily.parquet
│   ├── DTB3.csv
│   └── compustat_2021.01_2024.12.csv
│
├── run.py                          # 메인 실행 스크립트
├── run_single.py                   # 단일 시점 백테스트
├── run_batch.py                    # 일괄 백테스트
├── requirements.txt
└── README.md
```

---

## 🔬 이론적 배경

### Black-Litterman 모델

**베이지안 공식**:
```
μ_BL = [(τΣ)^(-1) + P^T·Ω^(-1)·P]^(-1) × [(τΣ)^(-1)·π + P^T·Ω^(-1)·Q]
Σ_BL = [(τΣ)^(-1) + P^T·Ω^(-1)·P]^(-1)
```

**변수 설명**:
- **μ_BL**: BL 조정 기대수익률 (사후 분포)
- **π**: 시장 균형 초과수익률 (사전 분포)
- **Σ**: 수익률 공분산 행렬
- **τ**: 불확실성 계수 (기본값 0.025)
- **P**: 뷰 선택 행렬 (K×N)
- **Q**: 뷰 벡터 (K×1)
- **Ω**: 뷰 불확실성 행렬 (K×K)

### Mean-Variance Optimization (MVO)

**목적함수**: Sharpe Ratio 최대화
```
max  SR = (w^T μ - R_f) / √(w^T Σ w)
 w
```

**제약조건**:
- ∑w_i = 1 (가중치 합)
- w_i ≥ 0 (Long-only)

---

## 📊 워크플로우

```
1. 데이터 로드 → 2. 지표 계산 (Tier 1-3) → 3. LLM 뷰 생성
    ↓
4. P, Q, Ω 생성 → 5. BL 최적화 (μ_BL, Σ_BL) → 6. MVO 최적화 (w*)
    ↓
7. 백테스트 → 8. 성과 측정 (CAR, Sharpe Ratio)
```

### 상세 단계

1. **데이터 전처리**: 초과수익률 계산 (R - R_f)
2. **시장 매개변수**: λ (위험 회피도), π (균형 수익률)
3. **LLM 뷰 생성**: Llama 3가 5개 상대 뷰 생성
4. **BL 모델**: 시장 균형과 LLM 뷰 결합
5. **MVO**: Sharpe Ratio 최대화 포트폴리오
6. **백테스팅**: 실제 수익률과 비교

---

## 📈 결과 확인

### 1. JSON 파일

**BL-MVO 가중치**:
```bash
cat database/logs/Tier2/result_of_BL-MVO/test1.json
```

**LLM 뷰**:
```bash
cat database/logs/Tier2/LLM-view/test1.json
```

**백테스트 결과**:
```bash
cat database/logs/Tier2/result_of_test/test1.json
```

### 2. Python 로드

```python
import json

# BL-MVO 결과 로드
with open('database/logs/Tier2/result_of_BL-MVO/test1.json', 'r') as f:
    results = json.load(f)

# 첫 번째 기간 가중치 확인
print(results[0]['w_aiportfolio'])
print(results[0]['SECTOR'])
```

---

## ⚙️ 주요 매개변수

### tau (τ)

**의미**: Black-Litterman 모델의 불확실성 계수

**값 범위**: 0.01 ~ 0.05 (일반적으로)

**효과**:
- **낮은 tau (예: 0.01)**: 시장 균형에 더 의존
- **높은 tau (예: 0.05)**: LLM 뷰에 더 의존

**권장값**: 0.025

### Tier

**의미**: LLM에 제공할 데이터 분석 단계

**선택**:
- **Tier 1**: 기술적 지표만 (빠름)
- **Tier 2**: 기술적 + 회계 지표 (권장)
- **Tier 3**: 기술적 + 회계 + 거시 지표 (미구현)

---

## 🛠️ 트러블슈팅

### GPU 관련 오류

**문제**: `RuntimeError: GPU를 사용할 수 없어 프로그램을 중단합니다`

**해결**:
1. NVIDIA GPU가 설치되어 있는지 확인
2. CUDA 12.1 설치:
   ```bash
   # CUDA 버전 확인
   nvidia-smi
   ```
3. PyTorch CUDA 버전 재설치:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

### JSON 파싱 오류

**문제**: LLM 출력을 JSON으로 파싱하지 못함

**해결**: `system_prompt_1.txt`가 올바르게 설정되었는지 확인
- JSON-only 출력 강제
- Markdown 코드 블록 금지

### 날짜 형식 오류

**문제**: `"24-05-31"` 형식을 잘못 파싱

**해결**: `YY-MM-DD` 형식 사용 (자동 처리됨)
```python
forecast_period = ["24-05-31", "24-06-30", ...]  # ✅ 올바름
```

---

## 📚 참고 문헌

1. **Black, F., & Litterman, R. (1992)**. "Global Portfolio Optimization". *Financial Analysts Journal*, 48(5), 28-43.

2. **He, G., & Litterman, R. (1999)**. "The Intuition Behind Black-Litterman Model Portfolios". *Goldman Sachs Quantitative Resources Group*.

3. **Idzorek, T. (2005)**. "A step-by-step guide to the Black-Litterman model". *Zephyr Associates*.

4. **Markowitz, H. (1952)**. "Portfolio Selection". *The Journal of Finance*, 7(1), 77-91.

---

## 📄 상세 문서

### 핵심 문서
- **[CLAUDE.md](CLAUDE.md)** - 전체 시스템 상세 설명 (프로젝트 분석 보고서, 2000+ 라인)
- **[THEORETICAL_VALIDATION_REPORT.md](THEORETICAL_VALIDATION_REPORT.md)** - 이론적 정확성 검증 (19개 항목, 100% 달성)
- **[BACKTEST_README.md](BACKTEST_README.md)** - 백테스트 시스템 설명
- **[PROMPT_IMPROVEMENTS.md](PROMPT_IMPROVEMENTS.md)** - 프롬프트 개선 사항

### 주요 업데이트 이력
- **2025-11-25**: 명명 체계 개선
  - `MVO` → `NONE_view` (개념적 정확성 향상)
  - 함수명: `get_MVO_weight()` → `get_NONE_view_BL_weight()`
  - 하위 호환성 보장 (기존 JSON 파일 자동 변환)
- **2025-11-12**: 백테스트 시스템 전면 수정
  - 날짜 컬럼 통일 (`ForecastDate`)
  - CAR 계산 수정 (복리 사용)
  - 이론적 정확성 100% 달성

---

## 🔧 실행 스크립트

### 메인 실행 파일
| 파일 | 설명 | 용도 |
|------|------|------|
| [run_single.py](run_single.py) | 단일 시뮬레이션 | 하나의 설정으로 전체 기간 백테스트 |
| [run_auto_repetition.py](run_auto_repetition.py) | 반복 실험 자동화 | Tier별 여러 번 반복 실행 (통계적 검증) |

### 분석 도구
| 파일 | 설명 | 출력 |
|------|------|------|
| [final_visualization.py](final_visualization.py) | 결과 시각화 | 그래프 및 차트 |
| [statistical_analysis.py](statistical_analysis.py) | 통계 분석 | 평균, 표준편차, t-test 등 |

### 실험 디렉토리
- **[potato_trial/](potato_trial/)**: 개발 중/테스트용 스크립트
  - 실험적 기능 및 백업 코드 포함
  - 프로덕션 실행 시 무시 가능
  - 여러 버전의 백테스트 구현 포함

---

## 📝 라이선스

이 프로젝트의 라이선스는 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 👥 연구기관

**LABA (Lab for Accounting Big Data & Artificial Intelligence)**
- 4th Project-Based Semester
- Topic: Integrating an LLM-Agent into Investor Views for the traditional Black-Litterman Model

---

## 🔄 최근 업데이트

### 2025-11-12
- ✅ 이론적 정확성 100% 달성 (5개 이슈 수정)
- ✅ BL 사후 공분산 행렬 수정 (Critical)
- ✅ Lambda 변수명 일관성 확보
- ✅ MVO 가중치 반올림 영향 추적 기능 추가
- ✅ 포괄적인 문서화 (docstring, 주석)
- ✅ 무위험 수익률 전체 시스템 추적
- ✅ 백테스트 시스템 날짜 컬럼 통일 (ForecastDate)
- ✅ CAR 계산 복리 공식 적용
- ✅ LLM JSON 파싱 안정성 개선

---

*Last Updated: 2025-11-12*
