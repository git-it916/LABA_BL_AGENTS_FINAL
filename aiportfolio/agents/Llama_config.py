import transformers
import torch
from transformers import BitsAndBytesConfig

# python -m aiportfolio.agents.understanding_lacalLLM

# --- 1. 모델 로드 ---
def prepare_pipeline_obj():
    quant_pipeline = transformers.pipeline(
            "text-generation",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            model_kwargs={
                "torch_dtype": torch.bfloat16,
                "load_in_4bit":True,
                }, # 모델의 숫자 정밀도를 조정하여 메모리를 아낍니다.
            device_map="auto", # GPU가 있으면 자동으로 GPU를 사용하도록 설정합니다.
        )
    return quant_pipeline

# --- 2. Llama 3 호출 함수 정의 ---
def chat_with_llama3(pipeline_obj, system_prompt, user_prompt):
    
    # 1. messages (대화 내용 준비)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    # system prompt에는 뭐가, user_prompt에는 어떤 변수가 들어갈지 정의 
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
        max_new_tokens=1024, # 최대 생성 토큰
        do_sample=True, # 보다 창의적인 답변(temperature와 do_sample 값들을 변화시켜서 조절)
        temperature=0.3, # 금융 분석이므로 낮게 설정
        top_p=0.8, # 80% 확률 내의 값들만 샘플링
        return_full_text=False, # 프롬프트를 제외하고 순수 답변만 받음
        eos_token_id=eos_tokens # 생성 종료 조건을 만족할 특정 토큰 지정
    )

    # 4. return (결과 반환)
    return outputs[0]["generated_text"].strip() # 결과 리스트의 첫 번째가 답변

'''
# 교수님 예시
generator = pipeline('text-generation', model='meta-llama/Meta-Llama-3-8B-Instruct')

result = generator("오늘 하루를 기분 좋게 시작할 수 있는 안부인사를 작성하면,")
print(result)
'''