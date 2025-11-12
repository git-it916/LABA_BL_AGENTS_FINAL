import json
from aiportfolio.agents.Llama_config_수정중 import chat_with_llama3
from aiportfolio.agents.prompt_maker import making_system_prompt
from aiportfolio.agents.prompt_maker import making_user_prompt
from aiportfolio.util.save_log_as_json import save_view_as_json

def generate_sector_views(pipeline_to_use, end_date, simul_name, Tier):
    """
    LLM을 사용하여 섹터 간 상대적 뷰를 생성하고 저장합니다.

    Args:
        pipeline_to_use: Llama 3 파이프라인 객체
        end_date: 예측 기준일
        simul_name (str): 시뮬레이션 이름
        Tier (int): 분석 단계 (1, 2, 3)

    Returns:
        list: 파싱된 뷰 데이터 (Python 리스트)
    """
    # 1. 시스템 프롬프트 정의 (LLM의 역할, 규칙, 최종 출력 형식)
    system_prompt = making_system_prompt()

    # 2. 사용자 프롬프트 정의 (실제 데이터 + 실행 명령)
    user_prompt = making_user_prompt(end_date=end_date)

    # 프롬프트 출력
    print("\n" + "="*80)
    print("📝 SYSTEM PROMPT (시스템 프롬프트)")
    print("="*80)
    print(system_prompt)
    print("\n" + "="*80)
    print("📝 USER PROMPT (사용자 프롬프트)")
    print("="*80)
    print(user_prompt)
    print("="*80 + "\n")

    # 3. 모델 실행
    print("\n[알림] Llama 3 모델에 상대 뷰 생성을 요청합니다...\n")
    generated_text = chat_with_llama3(
        pipeline_obj=pipeline_to_use,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    )

    # LLM 출력 전체 표시
    print("\n" + "="*80)
    print("🤖 LLM 원본 출력 (전체)")
    print("="*80)
    print(generated_text)
    print("="*80 + "\n")

    # 4. JSON 추출 및 파싱
    try:
        # 방법 1: '[{' 패턴으로 시작하는 JSON 배열 찾기
        start_index = generated_text.find('[{')

        if start_index == -1:
            # 방법 2: 독립된 '[' 찾기 (fallback)
            start_index = generated_text.find('[')
            if start_index != -1:
                temp_str = generated_text[start_index:].lstrip('[').lstrip()
                if not temp_str.startswith('{'):
                    start_index = -1

        if start_index == -1:
            raise ValueError("JSON 배열 시작을 찾을 수 없습니다.")

        # '}]'로 끝나는 위치 찾기
        end_index = generated_text.rfind('}]')
        if end_index == -1:
            end_index = generated_text.rfind(']')
            if end_index == -1:
                raise ValueError("JSON 배열 끝을 찾을 수 없습니다.")
        else:
            end_index = end_index + 1  # '}]'의 ']' 포함

        # JSON 문자열 추출
        json_string = generated_text[start_index : end_index + 1]

        # 공백/개행 제거
        lines = json_string.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        json_string_clean = ''.join(cleaned_lines)

        print(f"[디버그] 추출된 JSON (앞 300자):\n{json_string_clean[:300]}\n")

        # JSON 파싱
        views_data = json.loads(json_string_clean)

        if not isinstance(views_data, list):
            raise ValueError(f"파싱 결과가 리스트가 아닙니다: {type(views_data)}")

        print(f"[성공] {len(views_data)}개 뷰 파싱 완료")

    except (ValueError, json.JSONDecodeError) as e:
        print(f"\n[오류] LLM 출력에서 JSON 파싱 실패: {e}")
        print(f"원본 텍스트:\n{generated_text}\n")
        raise RuntimeError(f"LLM JSON 파싱 실패: {e}")

    # 5. 파싱된 데이터를 저장 (문자열이 아닌 객체로 저장)
    save_view_as_json(views_data, simul_name, Tier, end_date)

    return views_data
