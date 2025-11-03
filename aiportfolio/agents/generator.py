import json # JSON 파싱을 위해 import

class llamaview: # 이름 변경 (예시)
    
    def __init__(self, model_id="meta-llama/Meta-Llama-3-8B-Instruct"):
        self.pipe = pipeline(...) 

    def get_financial_views(self, market_data_prompt, max_new_tokens=512, temperature=0.3, top_p=0.9): # max 토큰 늘리면 돈 많이나옴
        # 1. 시스템 프롬프트 (페르소나, 역할 정의)
        system_prompt = """
        당신은 Black-Litterman 모델의 입력을 생성하는 (특정섹터 넣어야할까?) 애널리스트입니다.
        주어진 데이터를 분석하여 '뷰'를 생성합니다.
        반드시 다음 JSON 구조의 리스트 형식으로만 응답해야 하며, 다른 설명은 
        절대 추가하지 마십시오.
        
        [
            {
            "view_type": "relative", 
            "asset_1": "TICKER_1",
            "asset_2": "TICKER_2" | null,
            "expected_performance_percent": float, // 아웃퍼폼(%) 또는 절대수익률(%)
            "confidence_level": float // 0.0 ~ 1.0
            }
        ]
        """
        # | "absolute", 상대뷰 사용시 추가
        # 2. 유저 프롬프트 (데이터 + 지시)
        user_prompt = f"""
        [시장 데이터 및 뉴스]
        {market_data_prompt}
        
        [지시]
        위 데이터를 바탕으로 2개의 뷰(view)를 위의 JSON 형식으로 생성하십시오.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        prompt = self.pipe.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        outputs = self.pipe(prompt,
                            max_new_tokens=max_new_tokens,
                            do_sample=True,
                            temperature=temperature,
                            top_p=top_p,
                            return_full_text=False) # 중요: 프롬프트 반복 방지

        # 3. 출력 파싱 (가장 중요한 부분)
        generated_text = outputs[0]["generated_text"]
        
        try:
            json_start = generated_text.find('[') # JSON 배열의 시작 위치 찾기
            json_end = generated_text.rfind(']') + 1
            json_string = generated_text[json_start:json_end]
            views_data = json.loads(json_string)
            return views_data # 성공!

        except json.JSONDecodeError:
            print("JSON 파싱 오류. LLM이 잘못된 형식을 반환했습니다.")
            print(f"반환된 텍스트: {generated_text}")
            return None # 실패 시 None 반환
        except Exception as e:
            print(f"알 수 없는 오류: {e}")
            return None