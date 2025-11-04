import json
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import warnings
import os

# 경고 메시지 무시
warnings.filterwarnings("ignore")

# (참고) Llama 3 모델 경로 설정 (예시: Hugging Face ID)
# 실제 사용 시에는 Meta의 Llama 3 8B Instruct 모델 ID를 사용하세요.
# 예: "meta-llama/Meta-Llama-3-8B-Instruct"
# (Hugging Face Hub 로그인 필요: huggingface-cli login 또는 아래 hf_token 사용)

# (주의) 실제 모델 로드 대신, 테스트를 위한 'Mock(모의) 모델' 클래스 사용
# 만약 실제 모델(위 MODEL_PATH)이 없다면, 아래 Mock 클래스의 주석을 해제하고
# Llama3QuantModel의 주석을 처리하여 테스트하세요.

# class MockLlama3QuantModel:
#     """
#     실제 Llama 3 모델 없이 프롬프트 구조만 테스트하기 위한 모의 클래스
#     """
#     def chat(self, system_prompt, user_prompt, max_new_tokens, temperature, top_p):
#         print("="*50)
#         print("[SYSTEM PROMPT - 전달됨]")
#         print(system_prompt)
#         print("="*50)
#         print("[USER PROMPT - 전달됨]")
#         print(user_prompt)
#         print("="*50)
        
#         # 모의 JSON 응답 반환 (실제 모델이 생성할 것으로 기대되는 형식)
#         mock_response = """
# [
#   {
#     "sector_1": "정보기술 (IT)",
#     "sector_2": "유틸리티 (Utilities)",
#     "relative_return_view": 0.035,
#     "confidence": "High"
#   },
#   {
#     "sector_1": "정보기술 (IT)",
#     "sector_2": "헬스케어 (Healthcare)",
#     "relative_return_view": 0.025,
#     "confidence": "Medium"
#   },
#   {
#     "sector_1": "금융 (Financials)",
#     "sector_2": "유틸리티 (Utilities)",
#     "relative_return_view": 0.015,
#     "confidence": "Medium"
#   }
# ]
# """
#         return mock_response.strip()


class Llama3QuantModel:
    """
    Hugging Face Transformers를 사용한 Llama 3 모델 래퍼(Wrapper)
    (실제 모델 로드 시 이 클래스를 사용하세요)
    """
    def __init__(self, model_id="meta-llama/Meta-Llama-3-8B-Instruct", hf_token=None):
        """
        모델과 토크나이저를 로드하고 파이프라인을 설정합니다.
        (GPU가 없으면 매우 느릴 수 있습니다.)
        hf_token: Hugging Face 인증 토큰 (API Key)
        """
        print(f"'{model_id}' 모델 로딩 중... (시간이 걸릴 수 있습니다)")
        if hf_token is None:
            print("경고: Hugging Face 토큰(hf_token)이 제공되지 않았습니다. 'gated' 모델인 경우 로드에 실패할 수 있습니다.")
            
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id, 
                token=hf_token  # ★ 수정: 토큰 전달
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.bfloat16, # 메모리 절약을 위해 bfloat16 사용
                device_map="auto", # GPU 자동 할당
                token=hf_token  # ★ 수정: 토큰 전달
            )
            
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
            )
            print("모델 로딩 및 파이프라인 설정 완료.")
        except Exception as e:
            print(f"모델 로드 중 오류 발생: {e}")
            print("Hugging Face 토큰이 유효한지, Llama 3 모델 사용 동의(Hugging Face Hub)를 했는지 확인하세요.")
            print("테스트를 위해 'MockLlama3QuantModel'을 대신 사용합니다.")
            # 실제 모델 로드 실패 시, Mock 모델로 대체 (테스트용)
            self.pipe = None 
            self._mock_model = self.MockLlama3ChatModel() # 내부 Mock 모델 사용

    class MockLlama3ChatModel:
        """내부 모의 클래스"""
        def chat(self, system_prompt, user_prompt, max_new_tokens, temperature, top_p):
            print("="*50)
            print("[SYSTEM PROMPT - 전달됨]")
            print(system_prompt)
            print("="*50)
            print("[USER PROMPT - 전달됨]")
            print(user_prompt)
            print("="*50)
            mock_response = """
    [
      {
        "sector_1": "정보기술 (IT)",
        "sector_2": "유틸리티 (Utilities)",
        "relative_return_view": 0.035,
        "confidence": "High"
      },
      {
        "sector_1": "금융 (Financials)",
        "sector_2": "헬스케어 (Healthcare)",
        "relative_return_view": 0.015,
        "confidence": "Medium"
      }
    ]
    """
            return mock_response.strip()

    def chat(self, system_prompt, user_prompt, max_new_tokens=1024, temperature=0.3, top_p=0.9):
        """
        사용자님이 제공한 Llama 3 chat 함수
        (실제 모델 로드 실패 시 Mock 모델을 호출하도록 수정됨)
        """
        if not self.pipe:
            # Mock 모델 호출
            return self._mock_model.chat(system_prompt, user_prompt, max_new_tokens, temperature, top_p)

        # 1. messages (대화 내용 준비)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 2. apply_chat_template (Llama 3 전용 포맷으로 변환)
        prompt = self.pipe.tokenizer.apply_chat_template(
            messages,
            tokenize=False, 
            add_generation_prompt=True 
        )

        # 3. self.pipe() (모델 실행)
        outputs = self.pipe(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=True, 
            temperature=temperature, # 금융 분석이므로 창의성보다 일관성을 위해 낮게 설정 (0.3)
            top_p=top_p, 
            return_full_text=False, # (중요) 프롬프트를 제외하고 순수 답변만 받음
            
            # Llama 3가 JSON 형식을 잘 따르도록 EOS 토큰 설정
            # (JSON의 끝 ']' 또는 '}'를 만나면 생성을 중단하도록 유도)
            eos_token_id=[self.tokenizer.eos_token_id, self.tokenizer.convert_tokens_to_ids("```"), self.tokenizer.convert_tokens_to_ids("]"), self.tokenizer.convert_tokens_to_ids("}")],
        )

        # 4. return (결과 반환)
        return outputs[0]["generated_text"].strip()

def generate_sector_views():
    """
    시스템 프롬프트와 사용자 프롬프트를 정의하고 모델을 호출하여 
    섹터 상대 뷰를 생성하는 메인 함수
    """

    # --- 1. 시스템 프롬프트 정의 (LLM의 역할, 규칙, 최종 출력 형식) ---
    # 이 프롬프트는 한 번 정의되면 거의 바뀌지 않습니다.
    # (★ 중요 ★) LLM이 JSON 외에 다른 말을 하지 않도록 엄격하게 지시
    
    system_prompt = """
당신은 베테랑 '섹터 로테이션 전략가(Sector Rotation Strategist)'입니다.
당신의 임무는 11개 섹터의 퀀트 팩터와 시장 내러티브를 '상대 비교'하여, 향후 1개월간 가장 유망한(Overweight) 섹터와 가장 부진할(Underweight) 섹터를 식별하는 것입니다.

[추론 3단계 지침]
당신은 내부적으로 반드시 다음 3단계를 거쳐 추론해야 합니다.
1. [섹터 랭킹]: 11개 섹터 데이터(정량+정성)를 종합하여 1위(선호)부터 11위(비선호)까지 내부적으로 순위를 매깁니다.
2. [핵심 뷰 식별]: 1위, 2위 등 'Long' 아이디어와 10위, 11위 등 'Short' 아이디어를 선정합니다.
3. [상대 뷰 포맷팅]: 'Long' 아이디어(sector_1)와 'Short' 아이디어(sector_2)를 조합하여 상대 뷰 페어(pair)를 생성합니다.

[최종 출력 규칙]
* '반드시', '오직' 아래와 같은 JSON 리스트 형식으로만 답변하십시오.
* 어떠한 서론, 결론, 설명, 사과("죄송합니다...", "알겠습니다...")도 포함하지 마십시오.
* 당신의 출력은 즉시 Python의 'json.loads()' 함수로 파싱 가능해야 합니다.
* 'relative_return_view'는 예상 초과 수익률(예: 2.5% -> 0.025)입니다.
* 'confidence'는 해당 뷰에 대한 신뢰도(High, Medium, Low)입니다.

[JSON 출력 형식]
[
  {
    "sector_1": "섹터명 (Long)",
    "sector_2": "섹터명 (Short)",
    "relative_return_view": 0.0,
    "confidence": "High/Medium/Low"
  }
]
"""

    # --- 2. 사용자 프롬프트 정의 (실제 데이터 + 실행 명령) ---
    # 이 부분은 매 분석 시점마다 동적으로 생성됩니다.
    
    # (가상) 11개 섹터의 팩터 및 분석 데이터 (실제로는 이 부분을 동적으로 채워야 함)
    sector_data_list = [
      {
        "sector": "정보기술 (IT)",
        "quantitative_factors": { "12m_momentum": 0.45, "mean_reversion_z": -1.9, "volatility_60d": 0.22, "trend_strength_r2_60d": 0.78 },
        "qualitative_analysis": "IT 섹터는 견조한 장기 추세 속 단기 과매도 국면에 진입. 하방 경직성이 강하며 기관 매수 기회로 판단됨. (가장 선호)"
      },
      {
        "sector": "금융 (Financials)",
        "quantitative_factors": { "12m_momentum": 0.15, "mean_reversion_z": 0.5, "volatility_60d": 0.18, "trend_strength_r2_60d": 0.40 },
        "qualitative_analysis": "금리 인상 기대감이 선반영되었으나 추세 강도가 약화되고 있음. 중립적 시각."
      },
      {
        "sector": "헬스케어 (Healthcare)",
        "quantitative_factors": { "12m_momentum": -0.10, "mean_reversion_z": -0.8, "volatility_60d": 0.35, "trend_strength_r2_60d": 0.20 },
        "qualitative_analysis": "모멘텀 부재와 높은 변동성이 지속됨. 방어주 매력 감소."
      },
      {
        "sector": "유틸리티 (Utilities)",
        "quantitative_factors": { "12m_momentum": -0.15, "mean_reversion_z": 1.2, "volatility_60d": 0.30, "trend_strength_r2_60d": 0.15 },
        "qualitative_analysis": "금리 민감도가 높아 지속적인 자금 이탈. 추세 강도가 매우 약하며 반등 모멘텀 부재. (가장 비선호)"
      }
      # ... (실제로는 11개 섹터 데이터가 모두 포함되어야 함)
    ]

    # Python 리스트/딕셔너리 -> JSON 문자열로 변환 (LLM에 전달하기 위해)
    # ensure_ascii=False: 한글이 깨지지 않도록 함
    json_data_string = json.dumps(sector_data_list, indent=2, ensure_ascii=False)

    # 사용자 프롬프트 템플릿
    user_prompt = f"""
11개 섹터의 정량/정성 데이터가 다음과 같이 주어집니다.
당신의 '시스템 프롬프트'에 정의된 규칙에 따라, 이 데이터들을 '상대 비교'하여
향후 1개월간의 '상대 뷰(Relative Views)'를 생성하십시오.

[=== 11개 섹터 데이터 리스트 시작 ===]
{json_data_string}
[=== 11개 섹터 데이터 리스트 끝 ===]
"""

    # --- 3. 모델 실행 및 결과 파싱 ---
    
    # (★ 중요 ★) 여기에 Hugging Face API 키(Token)를 입력하세요.
    # 토큰은 [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) 에서 발급받을 수 있습니다.
    # 'read' 권한이 필요합니다.
    # (주의: 보안을 위해 코드에 직접 키를 하드코딩하는 것보다
    #  os.environ.get("HF_TOKEN") 등을 사용하는 것이 좋습니다.)
    YOUR_HF_TOKEN = "hf_YOUR_ACTUAL_TOKEN_GOES_HERE" # <-- ★★★ 여기에 키 입력 ★★★
    
    # (주의) 실제 모델 ID 또는 로컬 경로로 변경하세요.
    model_path = "meta-llama/Meta-Llama-3-8B-Instruct" # 예시 ID

    try:
        # (주의) 실제 모델 사용 시
        if YOUR_HF_TOKEN == "hf_YOUR_ACTUAL_TOKEN_GOES_HERE" or YOUR_HF_TOKEN == "":
            print("[경고] YOUR_HF_TOKEN을(를) 실제 Hugging Face 토큰으로 변경해야 합니다.")
            print("Mock 모델로 강제 전환하여 테스트합니다.")
            raise ValueError("Hugging Face 토큰이 설정되지 않았습니다.")
            
        model = Llama3QuantModel(model_id=model_path, hf_token=YOUR_HF_TOKEN) # ★ 수정: 토큰 전달
        
        # (주의) Mock 모델 테스트 시 (실제 모델 로드 불가능할 때)
        # model = MockLlama3QuantModel() 

    except Exception as e:
        print(f"모델 초기화 중 심각한 오류 발생: {e}")
        if "Hugging Face 토큰" not in str(e): # 토큰 오류가 아닌 다른 오류일 경우
             print("Mock 모델로 강제 전환하여 테스트합니다.")
        # Mock 모델로 강제 전환
        model = Llama3QuantModel(model_id="mock") # Mock을 트리거하기 위해
        if model.pipe is None: # Mock 모델이 활성화되었는지 확인
            print("Mock 모델이 활성화되었습니다.")


    print("\n[알림] Llama 3 모델에 상대 뷰 생성을 요청합니다...")
    
    # (핵심) chat 함수 호출
    generated_text = model.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_new_tokens=1024, # JSON 출력이 길 수 있으므로 넉넉하게 설정
        temperature=0.3      # 일관성 있는 분석을 위해 낮게 설정
    )

    print("\n[알림] Llama 3가 생성한 순수 텍스트(JSON) ▼")
    print(generated_text)

    # --- 4. 결과 파싱 (JSON 문자열 -> Python 객체) ---
    try:
        # LLM이 생성한 텍스트에서 JSON 부분만 정확히 파싱
        # (가끔 LLM이 JSON 앞뒤에 ```json ... ``` 같은 마크다운을 붙일 수 있음)
        if "```json" in generated_text:
            clean_json_string = generated_text.split("```json")[1].split("```")[0].strip()
        elif generated_text.startswith("["):
            clean_json_string = generated_text.strip()
        else:
            # LLM이 JSON 형식을 따르지 않았을 경우
            raise ValueError("LLM의 응답이 유효한 JSON 리스트로 시작하지 않습니다.")

        # 생성된 텍스트가 비어있는지 확인
        if not clean_json_string:
             raise ValueError("LLM의 응답이 비어있습니다.")

        parsed_views = json.loads(clean_json_string)
        
        print("\n[성공] JSON 파싱 완료. 생성된 상대 뷰 객체 ▼")
        print(json.dumps(parsed_views, indent=2, ensure_ascii=False))
        
        return parsed_views

    except json.JSONDecodeError as e:
        print(f"\n[오류] LLM이 생성한 텍스트를 JSON으로 파싱하는 데 실패했습니다: {e}")
        print("System 프롬프트의 JSON 출력 형식을 재점검하거나 temperature를 낮춰보세요.")
        return None
    except Exception as e:
        print(f"\n[오류] 알 수 없는 오류 발생: {e}")
        return None

if __name__ == "__main__":
    generate_sector_views()
