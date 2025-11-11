from aiportfolio.agents.Llama_config_수정중 import chat_with_llama3
from aiportfolio.agents.prompt_maker import making_system_prompt
from aiportfolio.agents.prompt_maker import making_user_prompt
from aiportfolio.util.save_log_as_json import save_view_as_json

def generate_sector_views(pipeline_to_use , end_date):
    # 1. 시스템 프롬프트 정의 (LLM의 역할, 규칙, 최종 출력 형식)
    system_prompt = making_system_prompt()

    # 2. 사용자 프롬프트 정의 (실제 데이터 + 실행 명령)
    user_prompt = making_user_prompt(end_date=end_date)

    # 3. 모델 실행 및 결과 파싱
    print("\n[알림] Llama 3 모델에 상대 뷰 생성을 요청합니다...")
    # chat_with_llama3 함수 호출
    generated_text = chat_with_llama3(
        pipeline_obj=pipeline_to_use,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    # 4. 결과 저장
    save_view_as_json(generated_text, end_date)

    return generated_text
