import transformers
import torch
from huggingface_hub import notebook_login
import json
import warnings

# --- 1. 사전 준비: 경고 무시 및 Hugging Face 로그인 ---

# 불필요한 경고 메시지를 무시합니다.
warnings.filterwarnings("ignore")

print("Hugging Face Notebook 로그인을 시작합니다.")
print("입력창이 나타나면 Hugging Face의 Access Token을 붙여넣고 Enter를 누르세요.")
print("('Add token as git credential?' 질문에는 'n'(no)을 입력해도 무방합니다.)")

# 이 코드를 실행하면 뜨는 입력창에 Access Token을 붙여넣습니다.
# (스크립트 실행 시 이 부분에서 사용자 입력이 필요합니다)
notebook_login()

# --- 2. 모델 로드 (사용자님 코드) ---

# 사용할 Llama 3 모델의 이름을 지정합니다.
model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

print(f"\n'{model_id}' 모델 로드를 시작합니다. (시간이 걸릴 수 있습니다)...")

try:
    # 파이프라인(pipeline)은 텍스트 생성을 쉽게 할 수 있도록 도와주는 기능입니다.
    quant_pipeline = transformers.pipeline(
        "text-generation",
        model=model_id,
        model_kwargs={"torch_dtype": torch.bfloat16}, # 모델의 숫자 정밀도를 조정하여 메모리를 아낍니다.
        device_map="auto", # GPU가 있으면 자동으로 GPU를 사용하도록 설정합니다.
    )
    print("모델 로드가 성공적으로 완료되었습니다.")
    
except Exception as e:
    print(f"\n[오류] 모델 로드에 실패했습니다: {e}")
    print("Hugging Face 토큰이 유효한지, Llama 3 모델 사용 동의(Hugging Face Hub)를 했는지 확인하세요.")
    print("스크립트를 종료합니다.")
    exit() # 모델 로드 실패 시 종료


# --- 3. Llama 3 호출 함수 정의 ---

def chat_with_llama3(pipeline_obj, system_prompt, user_prompt, max_new_tokens=1024, temperature=0.3):
    """
    로드된 파이프라인을 사용하여 Llama 3에 채팅을 요청하는 함수
    
    Args:
        pipeline_obj: transformers.pipeline 객체
        system_prompt: 모델의 역할(페르소나) 정의
        user_prompt: 사용자의 실제 데이터 및 명령
        max_new_tokens: 최대 생성 토큰 수
        temperature: 창의성 (금융 분석이므로 낮게 설정)
        
    Returns:
        str: Llama 3가 생성한 순수 텍스트 응답
    """
    
    # 1. messages (대화 내용 준비)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # 2. apply_chat_template (Llama 3 전용 포맷으로 변환)
    prompt = pipeline_obj.tokenizer.apply_chat_template(
            messages,
            tokenize=False, 
            add_generation_prompt=True 
    )

    # 3. pipeline() (모델 실행)
    # (참고) eos_token_id 설정: JSON 생성이 끝나면 멈추도록 유도
    eos_tokens = [
        pipeline_obj.tokenizer.eos_token_id, 
        pipeline_obj.tokenizer.convert_tokens_to_ids("```"),
        pipeline_obj.tokenizer.convert_tokens_to_ids("]"), # JSON 리스트 끝
        pipeline_obj.tokenizer.convert_tokens_to_ids("}")  # JSON 객체 끝
    ]
    
    outputs = pipeline_obj(
        prompt,
        max_new_tokens=max_new_tokens,
        do_sample=True, 
        temperature=temperature,
        top_p=0.9, 
        return_full_text=False, # (중요) 프롬프트를 제외하고 순수 답변만 받음
        eos_token_id=eos_tokens
    )

    # 4. return (결과 반환)
    return outputs[0]["generated_text"].strip()

# --- 4. 메인 로직: 뷰 생성 함수 정의 ---

def generate_sector_views(pipeline_to_use):
    """
    시스템 프롬프트와 사용자 프롬프트를 정의하고 모델을 호출하여 
    섹터 상대 뷰를 생성하는 메인 함수
    
    Args:
        pipeline_to_use: 모델이 로드된 transformers.pipeline 객체
    """

    # 1. 시스템 프롬프트 정의 (LLM의 역할, 규칙, 최종 출력 형식)
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

    # 2. 사용자 프롬프트 정의 (실제 데이터 + 실행 명령)
    
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

    # 3. 모델 실행 및 결과 파싱
    print("\n[알림] Llama 3 모델에 상대 뷰 생성을 요청합니다...")
    
    # (핵심) chat_with_llama3 함수 호출
    generated_text = chat_with_llama3(
        pipeline_obj=pipeline_to_use,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_new_tokens=1024, # JSON 출력이 길 수 있으므로 넉넉하게 설정
        temperature=0.3      # 일관성 있는 분석을 위해 낮게 설정
    )

    print("\n[알림] Llama 3가 생성한 순수 텍스트(JSON) ▼")
    print(generated_text)

    # 4. 결과 파싱 (JSON 문자열 -> Python 객체)
    try:
        # LLM이 생성한 텍스트에서 JSON 부분만 정확히 파싱
        if "```json" in generated_text:
            clean_json_string = generated_text.split("```json")[1].split("```")[0].strip()
        elif generated_text.startswith("["):
            clean_json_string = generated_text.strip()
        else:
            raise ValueError("LLM의 응답이 유효한 JSON 리스트로 시작하지 않습니다.")

        if not clean_json_string:
             raise ValueError("LLM의 응답이 비어있습니다.")
             
        parsed_views = json.loads(clean_json_string)
        
        print("\n[성공] JSON 파싱 완료. 생성된 상대 뷰 객체 ▼")
        print(json.dumps(parsed_views, indent=2, ensure_ascii=False))
        
        return parsed_views

    except json.JSONDecodeError as e:
        print(f"\n[오류] LLM이 생성한 텍스트를 JSON으로 파싱하는 데 실패했습니다: {e}")
        return None
    except Exception as e:
        print(f"\n[오류] 알 수 없는 오류 발생: {e}")
        return None

# --- 5. 스크립트 메인 실행 ---

if __name__ == "__main__":
    # 이 스크립트가 직접 실행되었을 때
    
    # 1. (위에서 실행) Hugging Face 로그인
    # 2. (위에서 실행) quant_pipeline 객체 생성
    
    if 'quant_pipeline' in locals() and quant_pipeline is not None:
        # 3. 모델 로드가 성공했을 경우, 메인 로직 실행
        generate_sector_views(pipeline_to_use=quant_pipeline)
    else:
        print("\n[알림] 모델 파이프라인('quant_pipeline')이(가) 성공적으로 로드되지 않아 메인 로직을 실행할 수 없습니다.")
        print("스크립트 상단의 모델 로드 부분을 확인하세요.")