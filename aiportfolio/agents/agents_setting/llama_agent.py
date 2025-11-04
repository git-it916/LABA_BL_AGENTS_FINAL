from transformers import pipeline
import torch # torch를 import해야 bfloat16을 쓸 수 있습니다.


class llamaAgent:
    def __init__(self, model_id="meta-llama/Meta-Llama-3-8B-Instruct"):
        # 1. 'pipeline'은 모델을 쉽게 사용하도록 포장한 '종합 선물 세트'입니다.
        #    - 토크나이저 (텍스트 -> 숫자)
        #    - 모델 (숫자 -> 생각 -> 숫자)
        #    - 디코더 (숫자 -> 텍스트)
        #    이 모든 것을 'pipe' 하나로 합쳐줍니다.
        self.pipe = pipeline(
            # 2. "text-generation": 우리가 할 작업은 '텍스트 생성'입니다.
            "text-generation",
            
            # 3. model: Hugging Face에서 다운로드할 모델의 ID입니다.
            model=model_id,
            
            # 4. model_kwargs (모델 옵션): 여기가 중요합니다.
            model_kwargs={
                # "torch_dtype": "bfloat16" (또는 torch.bfloat16)
                # - 모델이 계산할 때 사용하는 '숫자'의 정밀도입니다.
                # - bfloat16은 float32(기본값)보다 정밀도가 낮지만,
                #   메모리(VRAM) 사용량을 절반으로 줄여주고 속도도 빨라집니다.
                # - LLM은 정밀도가 조금 낮아도 성능 저하가 거의 없습니다. (필수 옵션)
                "torch_dtype": torch.bfloat16 
            },
            
            # 5. device_map="auto":
            # - 모델을 어디에 올릴지 자동으로 결정합니다.
            # - NVIDIA GPU(CUDA)가 있으면 GPU에 올리고 (매우 빠름),
            # - 없으면 CPU에 올립니다. (매우 매우 느림)
            device_map="auto"
        )