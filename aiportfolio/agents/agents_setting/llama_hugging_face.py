import transformers
import torch
from huggingface_hub import notebook_login

# 이 코드를 실행하면 뜨는 입력창에 Access Token을 붙여넣습니다.
notebook_login()

# 사용할 Llama 3 모델의 이름을 지정합니다.

import transformers
import torch

# 사용할 Llama 3 모델의 이름을 지정합니다.
model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

# 파이프라인(pipeline)은 텍스트 생성을 쉽게 할 수 있도록 도와주는 기능입니다.
# "text-generation"은 텍스트 생성 작업을 하겠다는 의미입니다.
pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16}, # 모델의 숫자 정밀도를 조정하여 메모리를 아낍니다.
    device_map="auto", # GPU가 있으면 자동으로 GPU를 사용하도록 설정합니다.
)

# Llama 3 모델에 질문을 던질 때는 정해진 형식(chat template)을 따르는 것이 좋습니다.
# 이를 통해 모델이 질문의 의도를 더 잘 파악할 수 있습니다.
messages = [
    {"role": "system", "content": "You are a helpful assistant for financial analysis."}, # 모델의 역할을 지정
    {"role": "user", "content": "What is the Black-Litterman model?"}, # 실제 사용자의 질문
]

# 모델이 이해할 수 있도록 메시지를 대화 형식으로 변환합니다.
prompt = pipeline.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
)

# 파이프라인을 실행하여 텍스트를 생성합니다.
# max_new_tokens: 생성할 최대 단어(토큰) 수
# do_sample=True: 좀 더 창의적인 답변을 생성
# temperature: 답변의 창의성 정도 (낮을수록 정형화된 답변)
# top_p: 답변의 다양성을 조절
outputs = pipeline(
    prompt,
    max_new_tokens=256,
    do_sample=True,
    temperature=0.6,
    top_p=0.9,
)

# 생성된 답변을 출력합니다.
# 결과는 리스트 형태로 나오며, 'generated_text' 부분에 실제 답변이 들어있습니다.
print(outputs[0]["generated_text"])