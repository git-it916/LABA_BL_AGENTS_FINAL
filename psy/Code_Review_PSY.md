# Code Review — AI-View Black-Litterman Tier Comparison Model

> **작성일**: 2026-03-25
> **목적**: (1) 모델 필수/비필수 구성 요소 분류, (2) 중복·혼란 코드 정리

---

## 목차

1. [필수 구성 요소](#1-필수-구성-요소)
2. [비필수 구성 요소](#2-비필수-구성-요소)
3. [중복·혼란 코드 목록](#3-중복혼란-코드-목록)
4. [변수 수준 코멘트 정리](#4-변수-수준-코멘트-정리)

---

## 1. 필수 구성 요소

> 티어별 BL 수익률 비교 파이프라인이 정상 작동하기 위해 **반드시** 존재해야 하는 파일과 함수

### 1-A. 오케스트레이션

| 파일 | 핵심 함수 | 역할 |
|------|-----------|------|
| `run_single.py` | — | 실험 파라미터 설정 및 `scene()` 호출 진입점 |
| `aiportfolio/scene.py` | `scene()` | 전체 파이프라인 조율 (BL→MVO→백테스트→시각화) |

### 1-B. Black-Litterman 최적화

| 파일 | 핵심 함수 / 클래스 | 역할 |
|------|-------------------|------|
| `aiportfolio/BL_MVO/BL_opt.py` | `get_bl_outputs()` | BL 공식 적용, μ_BL 산출 |
| `aiportfolio/BL_MVO/BL_params/market_params.py` | `Market_Params` | π, Σ, λ, w_mkt 계산 |
| `aiportfolio/BL_MVO/BL_params/view_params.py` | `get_view_params()` | LLM 뷰 → P, Q, Ω 변환 |
| `aiportfolio/BL_MVO/MVO_opt.py` | `optimize_tangency_1()` | Sharpe 최대화 MVO (SLSQP) |
| `aiportfolio/BL_MVO/prepare/sector_excess_return.py` | `final()` | 섹터 초과수익률 데이터 로드 |

### 1-C. LLM 뷰 생성

| 파일 | 핵심 함수 | 역할 |
|------|-----------|------|
| `aiportfolio/agents/Llama_view_generator.py` | `generate_sector_views()` | LLM 호출 → JSON 뷰 생성 → 저장 |
| `aiportfolio/agents/Llama_config_수정중.py` | `prepare_pipeline_obj()`, `chat_with_llama3()`, `call_gemini_api()` | LLM 파이프라인 초기화 및 추론 |
| `aiportfolio/agents/converting_viewtomatrix.py` | `open_view_log()`, `create_P_matrix()`, `create_Q_vector()` | 뷰 JSON → BL 행렬(P, Q) 변환 |
| `aiportfolio/agents/prompt_maker_improved.py` | `making_system_prompt()`, `making_user_prompt()` | 티어별 프롬프트 생성 |
| `aiportfolio/agents/prompt_template/system_prompt_1.txt` | — | LLM 역할·출력 형식 지정 |
| `aiportfolio/agents/prompt_template/user_prompt_final.txt` | — | 데이터 + 분석 지시 |

### 1-D. 티어별 지표 계산

| 파일 | 핵심 함수 | 역할 |
|------|-----------|------|
| `aiportfolio/agents/prepare/Tier1_calculate.py` | `calculate_rolling_indicators()` | 기술적 지표 (모멘텀, 추세, z-score 등) |
| `aiportfolio/agents/prepare/Tier2_calculate.py` | `calculate_accounting_indicator()` | 회계 지표 (BM, Gprof, CAPEI 등) |

### 1-E. 백테스트 및 결과 저장

| 파일 | 핵심 함수 / 클래스 | 역할 |
|------|-------------------|------|
| `aiportfolio/backtest/calculating_performance.py` | `backtest`, `performance_of_portfolio()`, `get_NONE_view_BL_weight()` | AI_portfolio vs NONE_view 성과 계산 |
| `aiportfolio/backtest/preprocessing_2차수정.py` | `final_abnormal_returns()` | 일별 섹터 초과수익률 로드 |
| `aiportfolio/backtest/visalization.py` | `calculate_average_cumulative_returns()` | 기간별 평균 CAR 집계 |
| `aiportfolio/util/save_log_as_json.py` | `save_BL_as_json()`, `save_view_as_json()`, `save_performance_as_json()` | 결과 JSON 저장 |
| `aiportfolio/util/making_rollingdate.py` | `get_rolling_dates()` | 예측 기간 파싱 |
| `aiportfolio/util/sector_mapping.py` | `map_code_to_gics_sector()` | GICS 코드 ↔ 섹터명 매핑 |

### 1-F. 데이터 로딩

| 파일 | 역할 |
|------|------|
| `aiportfolio/util/data_load/open_DTB3.py` | 무위험 수익률(3M T-Bill) |
| `aiportfolio/util/data_load/open_final_stock_months.py` | 월별 주식 수익률 |
| `aiportfolio/util/data_load/open_final_stock_daily.py` | 일별 주식 수익률 |
| `aiportfolio/util/data_load/cap_month_check.py` | 시가총액 검증 |

---

## 2. 비필수 구성 요소

> 현재 파이프라인에서 **사용되지 않거나**, **더 나은 버전으로 대체됐거나**, **미구현**인 파일들

### 2-A. 완전 미구현

| 파일 | 이유 |
|------|------|
| `aiportfolio/agents/prepare/Tier3_calculate.py` | 빈 파일. Tier 3 실험을 실행하면 빈 데이터가 그대로 LLM에 전달됨. 구현하거나 Tier 3 옵션을 비활성화해야 함. |

### 2-B. 더 나은 버전으로 대체된 파일

| 구버전 파일 | 대체 파일 | 비고 |
|------------|-----------|------|
| `aiportfolio/agents/Llama_config.py` | `Llama_config_수정중.py` | 구버전은 deprecated `torch_dtype` 사용, `max_new_tokens=512`로 JSON 잘림 발생 가능 |
| `aiportfolio/agents/prompt_maker.py` | `prompt_maker_improved.py` | 구버전은 소수점 15자리 그대로 전달, 개선판은 2자리 반올림 + 단위 통일 |
| `aiportfolio/backtest/final_Ret.py` | `calculating_performance.py` | CAR을 cumsum(산술합)으로 계산하는 치명적 오류 포함. 완전 deprecated |
| `aiportfolio/backtest/preprocessing.py` | `preprocessing_2차수정.py` | 구버전 |
| `aiportfolio/backtest/preprocessing_수정중.py` | `preprocessing_2차수정.py` | 실험적 버전 |

### 2-C. 사용 여부가 불명확한 파일

| 파일 | 이유 |
|------|------|
| `aiportfolio/agents/Llama_view.py` | `Llama_view_generator.py`에 흡수된 것으로 보이며 독립적으로 import되는 곳 없음 |
| `aiportfolio/agents/Llama_Login.py` | Hugging Face 로그인 로직이 config 파일 내에서 처리될 경우 불필요 |
| `aiportfolio/agents/prompt_accounting.py` | `prompt_maker_improved.py`에서 통합 처리되는 것으로 보임 |
| `aiportfolio/util/preprocess_raw_to_parquet.py` | 일회성 데이터 변환 스크립트. 재실행 필요 없으면 보관만 하면 됨 |
| `aiportfolio/util/raw_filltered.py` | 동일하게 일회성 필터링 스크립트로 추정 |
| `aiportfolio/util/data_load/종류.py` | 한글 파일명. 내용 및 사용처 불명확 |
| `aiportfolio/BL_MVO/MVO_opt.py` — `optimize_tangency()` 메서드 | 해석적 풀이 구버전. `optimize_tangency_1()`(SLSQP)로 대체됨 |
| `aiportfolio/BL_MVO/BL_params/market_params.py` — `making_mu()` | 코드 내 주석에도 "for reference only, not used in BL"로 명시됨 |

### 2-D. 실험·임시 코드 (potato_trial/)

전체 `potato_trial/` 디렉토리가 해당. 프로덕션 코드와 독립적으로 존재하는 시험 구현체들이며, 현재 메인 파이프라인에서 import되지 않음. 아카이빙 또는 삭제 권장.

---

## 3. 중복·혼란 코드 목록

### 3-1. 동일 역할의 파일이 두 개 이상 공존

| 역할 | 파일 A (구버전 / 미사용) | 파일 B (현재 사용) | 문제 |
|------|--------------------------|-------------------|------|
| LLM 설정 | `Llama_config.py` | `Llama_config_수정중.py` | 이름만 봐서는 어느 것이 현행인지 알 수 없음 |
| 프롬프트 생성 | `prompt_maker.py` | `prompt_maker_improved.py` | 두 파일 모두 `making_system_prompt`, `making_user_prompt` 함수 보유 |
| 백테스트 전처리 | `preprocessing.py`, `preprocessing_수정중.py` | `preprocessing_2차수정.py` | 3개 버전이 같은 디렉토리에 공존 |
| 백테스트 성과 계산 | `final_Ret.py` | `calculating_performance.py` | `final_Ret.py`는 오류 포함 deprecated이나 파일이 남아있음 |

**권고**: 구버전 파일을 삭제하거나 `_deprecated` suffix를 붙여 명확히 구분.

---

### 3-2. 동일 파일 내 중복 메서드

**`aiportfolio/BL_MVO/MVO_opt.py`**

```python
# 구버전 (사용 안 함)
def optimize_tangency(self): ...        # 해석적 풀이, 제약조건 없음

# 현재 버전 (사용 중)
def optimize_tangency_1(self, return_original=False): ...  # SLSQP, Long-only 제약
```

두 메서드가 같은 클래스에 공존. `optimize_tangency()`는 호출되는 곳이 없으면 제거 권장.

---

**`aiportfolio/BL_MVO/BL_params/market_params.py`**

```python
def making_sigma(self):               # 초과수익률 기반 공분산 → BL 내부 사용
def making_sigma_for_optimize(self):  # 절대수익률 기반 공분산 → MVO Sharpe 분모 사용
```

이름이 비슷해서 혼란스러움. 두 메서드가 사용하는 수익률 기준이 다르다는 점(초과 vs 절대)을 주석이나 함수명으로 명시할 것. 예: `making_sigma_excess()` / `making_sigma_absolute()`.

---

### 3-3. 섹터 목록 하드코딩 중복

아래 3곳 이상에서 동일한 11개 섹터 리스트가 각각 독립적으로 하드코딩되어 있음:

- `aiportfolio/agents/converting_viewtomatrix.py` (P 행렬 생성 시)
- `aiportfolio/BL_MVO/BL_params/market_params.py` (GICS 코드 순서 검증)
- `aiportfolio/util/sector_mapping.py` (코드-이름 매핑)

한 곳에서 변경이 발생할 경우 나머지를 업데이트하지 않으면 불일치 발생. `sector_mapping.py`를 단일 진실 공급원(single source of truth)으로 사용하도록 통일 권장.

---

### 3-4. 날짜 파싱 방식이 파일마다 다름

| 파일 | 사용 방식 |
|------|-----------|
| `making_rollingdate.py` | `pd.to_datetime(s, format='%y-%m-%d')` |
| `calculating_performance.py` | `datetime.strptime(s, '%y-%m-%d')` |
| `converting_viewtomatrix.py` | `pd.to_datetime(record['date'])` (형식 불지정) |
| `scene.py` | 문자열 그대로 전달 후 내부에서 변환 |

날짜 파싱 로직을 `making_rollingdate.py` 또는 별도 util 함수로 단일화 권장.

---

### 3-5. 포트폴리오 명칭 혼용

`MVO`와 `NONE_view`가 코드베이스 전체에서 혼용됨:

- `scene.py`: `portfolio_name='NONE_view'` ← 현재 표준
- `final_visualization.py`: `if portfolio_name == 'MVO': portfolio_name = 'NONE_view'` ← 하위호환 처리
- `visalization.py`: 동일한 하위호환 처리
- 기존 JSON 로그: `"portfolio_name": "MVO"` ← 구버전 데이터

실험 재실행 없이는 로그 파일을 일괄 마이그레이션하기 어려우므로, 하위호환 처리는 유지하되 신규 로그가 모두 `NONE_view`를 사용하는지 확인 필요.

---

### 3-6. 실행 진입점(Entry Point)이 여러 개

루트 디렉토리에만 아래 실행 스크립트들이 공존:

```
run_single.py          ← 현재 사용 중
run_auto_repetition.py ← 반복 자동화용
final_visualization.py ← 결과 시각화용
statistical_analysis.py← 통계 분석용
test_branch.py         ← 테스트용
test_branch2.py        ← 테스트용
potato_trial/run.py    ← 실험용
potato_trial/run_single.py  ← 실험용
potato_trial/run_batch.py   ← 실험용
```

어느 파일이 "현재 기준 실행 파일"인지 README에 명시하거나, 실험용 스크립트는 `potato_trial/`로 격리 권장.

---

### 3-7. `Omega = Omega / 1` (무의미한 코드)

**`aiportfolio/BL_MVO/BL_params/view_params.py`** 내 아래 라인 존재:

```python
Omega = Omega / 1  # 아무 효과 없음
```

제거 권장.

---

### 3-8. GPU 체크 위치가 늦음

GPU 필수 확인 로직이 `view_params.py` 내부에 있어, BL 시장 파라미터 계산을 모두 마친 후에야 GPU 없음 오류가 발생함. `scene.py` 또는 `run_single.py` 최상단에서 먼저 확인하도록 이동 권장.

---

## 4. 변수 수준 코멘트 정리

> `psy/Comment_20251225.md`의 내용을 바탕으로 현행 코드 맥락에서 재정리

### 4-A. Market Variables (Tier 1)

| 변수 | 현재 구현 파일 | 필수? | 이유 |
|------|---------------|-------|------|
| `12_1_momentum` | `Tier1_calculate.py` 미구현 | **필수** | Jegadeesh & Titman(1993) 근거. 추가 필요 |
| `52_week_high_prox` | `Tier1_calculate.py` 미구현 | **필수** | George & Hwang(2004) 근거. 추가 필요 |
| `cagr_3y` | 구현됨 | 재검토 | 3년은 섹터 로테이션에 과도하게 긴 기간. 학술 근거 보강 필요 |
| `12m_returns` | 구현됨 (raw list) | **제거 권장** | 의미 없는 raw 리스트를 LLM에 전달. Momentum proxy로 대체 |
| `volatility` | 구현됨 | **제거 권장** | 견해 형성에 대한 역할 불명확. Confidence 지표라면 뷰 Q가 아니라 Ω에 반영해야 함 |
| `z_score` | 구현됨 | **제거 권장** | 학술 근거 불명확 |
| `trend_strength_r2` | 구현됨 | **제거 권장** | 학술 근거 불명확. R² 자체는 추세 강도와 직접적 연관 없음 |

**결론**: Market 변수는 `12_1_momentum`과 `52_week_high_prox` 2개로 단순화 권장. 현재 5개 변수 중 3개는 근거가 취약함.

---

### 4-B. Accounting Variables (Tier 2)

| 변수 | 현재 구현 파일 | 필수? | 이유 |
|------|---------------|-------|------|
| `BM` (bm_Mean) | `Tier2_calculate.py` | **필수** | FF HML 팩터의 기초 변수. 가장 robust한 가치 지표 |
| `Gprof` (GProf_Mean) | `Tier2_calculate.py` | **필수** | FF RMW와 연결. Novy-Marx(2013) 수익성 지표 |
| `CAPEI` (CAPEI_Mean) | `Tier2_calculate.py` | **필수** | FF CMA와 연결. 자본배분 효율성 지표 |
| `npm_Mean` | `Tier2_calculate.py` | **제거 권장** | Gprof와 수익성 중복 |
| `roe_Mean` | `Tier2_calculate.py` | **제거 권장** | Gprof, NPM과 수익성 중복 |
| `roa_Mean` | `Tier2_calculate.py` | **제거 권장** | Gprof, NPM, ROE와 수익성 중복 |
| `totdebt_invcap_Mean` | `Tier2_calculate.py` | 재검토 | 레버리지-수익률 관계가 모호함. 제거 또는 부채 변화율(MoM)로 대체 검토 |

**결론**: Accounting 변수는 BM, Gprof, CAPEI 3개로 단순화. FF 3-factor 확장(HML, RMW, CMA)과 직접 연결되는 구조가 논문 기여도에도 유리함.

---

### 4-C. Macro Variables (Tier 3 — 미구현)

| 변수 | 권장 처리 방식 |
|------|---------------|
| `Fedfunds` | 레벨값 + MoM 변화 모두 사용 |
| `CPI` | YoY% 변화율 사용 |
| `G20_CLI` | 100 대비 위치 또는 MoM 변화 |
| `T10Y2Y` | 부호(양/음) 반전 여부 명시적 확인 필요 |
| `GPDIC1_PCA` | YoY% 변화율 사용 |

**핵심 주의사항**: Macro 데이터는 발표 시점이 제각각이므로 **해당 날짜 기준 가장 최근에 available한 데이터**를 사용하는 룩어헤드 방지 로직이 필수. 단순히 날짜 기준으로 join하면 안 됨.

---

## 요약

| 분류 | 파일 수 | 핵심 조치 |
|------|---------|-----------|
| 필수 구성 요소 | ~20개 | 현재 파이프라인 유지 |
| 비필수 (미구현) | 1개 | `Tier3_calculate.py` 구현 또는 Tier 3 비활성화 |
| 비필수 (deprecated) | ~6개 | 삭제 또는 아카이빙 |
| 비필수 (사용처 불명) | ~7개 | import 경로 추적 후 정리 |
| 중복/혼란 | 8건 | 파일 통합, 명칭 통일, 하드코딩 제거 |
| 변수 제거 권장 | Market 3개, Accounting 3개 | Tier1/2 코드 단순화 |
