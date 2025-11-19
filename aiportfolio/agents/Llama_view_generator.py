import json
from aiportfolio.agents.Llama_config_수정중 import chat_with_llama3
from aiportfolio.agents.prompt_maker_improved import making_system_prompt
from aiportfolio.agents.prompt_maker_improved import making_user_prompt
from aiportfolio.util.save_log_as_json import save_view_as_json

def generate_sector_views(pipeline_to_use, end_date, simul_name, Tier, model='llama'):
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
    system_prompt = making_system_prompt(tier=Tier)

    # 2. 사용자 프롬프트 정의 (실제 데이터 + 실행 명령)
    # Tier 인자를 전달하여 단계별 데이터 포함
    user_prompt = making_user_prompt(end_date=end_date, tier=Tier)

    # 프롬프트 출력
    print("\n" + "="*80)
    print("SYSTEM PROMPT (시스템 프롬프트)")
    print("="*80)
    print(system_prompt)
    print("\n" + "="*80)
    print("USER PROMPT (사용자 프롬프트)")
    print("="*80)
    print(user_prompt)
    print("="*80 + "\n")

    # 3. 모델 실행
    if model == 'llama':
        print("\n[알림] Llama 3 모델에 상대 뷰 생성을 요청합니다...\n")
        generated_text = chat_with_llama3(
            pipeline_obj=pipeline_to_use,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
    elif model == 'gemini':
        print("\n[알림] Google Gemini API로 상대 뷰 생성을 요청합니다...\n")
        from aiportfolio.agents.Llama_config_수정중 import call_gemini_api
        generated_text = call_gemini_api(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
    else:
        raise ValueError(f"Unknown model: '{model}'. Use 'llama' or 'gemini'")

    # LLM 출력 전체 표시
    print("\n" + "="*80)
    print("LLM 원본 출력 (전체)")
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
            raise ValueError("JSON 배열 시작을 찾을 수 없습니다. LLM이 JSON 형식으로 응답하지 않았습니다.")

        # JSON 끝 찾기: 여러 방법 시도
        # 1차: '}]' 패턴 찾기 (정상적인 JSON 배열 종료)
        end_index = generated_text.rfind('}]')

        if end_index == -1:
            # 2차: 마지막 '}' 다음에 ']'가 있는지 찾기 (공백이 있을 수 있음)
            last_brace = generated_text.rfind('}')
            if last_brace != -1:
                # '}' 이후 텍스트에서 ']' 찾기
                remaining = generated_text[last_brace:]
                bracket_pos = remaining.find(']')
                if bracket_pos != -1:
                    end_index = last_brace + bracket_pos
                    print(f"[알림] JSON 끝을 찾음 ('}}' 이후 ']' 패턴)")

        if end_index == -1:
            # 3차: 독립된 ']' 찾기 (마지막 수단)
            end_index = generated_text.rfind(']')
            if end_index != -1:
                print(f"[경고] JSON 끝을 독립된 ']'로 찾음. 불완전한 JSON일 수 있습니다.")

        if end_index == -1:
            # JSON이 완전히 생성되지 않음
            raise ValueError(
                f"JSON 배열 끝을 찾을 수 없습니다. "
                f"LLM이 토큰 제한에 도달했거나 출력이 중단되었을 수 있습니다.\n"
                f"생성된 텍스트 길이: {len(generated_text)} 문자\n"
                f"마지막 200자: ...{generated_text[-200:]}"
            )
        else:
            # '}]'의 경우 +1, '}'나 ']'의 경우 그대로
            if generated_text[end_index-1:end_index+1] == '}]':
                pass  # end_index는 이미 ']' 위치를 가리킴
            else:
                pass  # end_index는 이미 ']' 위치를 가리킴

        # JSON 문자열 추출
        json_string = generated_text[start_index : end_index + 1]

        # 공백/개행 제거
        lines = json_string.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        json_string_clean = ''.join(cleaned_lines)

        print(f"[디버그] 추출된 JSON 길이: {len(json_string_clean)} 문자")
        print(f"[디버그] 추출된 JSON (앞 300자):\n{json_string_clean[:300]}\n")
        print(f"[디버그] 추출된 JSON (뒤 300자):\n...{json_string_clean[-300:]}\n")

        # JSON 파싱
        views_data = json.loads(json_string_clean)

        if not isinstance(views_data, list):
            raise ValueError(f"파싱 결과가 리스트가 아닙니다: {type(views_data)}")

        print(f"[성공] {len(views_data)}개 뷰 파싱 완료")

        # 각 뷰의 유효성 검증
        for i, view in enumerate(views_data, 1):
            required_keys = ['sector_1', 'sector_2', 'relative_return_view']
            missing_keys = [k for k in required_keys if k not in view]
            if missing_keys:
                print(f"[경고] 뷰 {i}에 필수 키가 누락됨: {missing_keys}")

    except (ValueError, json.JSONDecodeError) as e:
        print(f"\n[오류] LLM 출력에서 JSON 파싱 실패: {e}")
        print(f"\n원본 텍스트 길이: {len(generated_text)} 문자")
        print(f"원본 텍스트 (앞 500자):\n{generated_text[:500]}\n")
        print(f"원본 텍스트 (뒤 500자):\n...{generated_text[-500:]}\n")
        raise RuntimeError(f"LLM JSON 파싱 실패: {e}")

    # 5. end_date를 각 뷰에 추가 (시점 구분을 위함)
    import pandas as pd

    # end_date를 문자열로 변환
    if isinstance(end_date, str):
        end_date_str = end_date
    else:
        end_date_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')

    # 각 뷰에 end_date 추가
    for view in views_data:
        view['end_date'] = end_date_str

    print(f"[알림] 모든 뷰에 end_date '{end_date_str}' 추가 완료")

    # 6. 파싱된 데이터를 저장 (문자열이 아닌 객체로 저장)
    save_view_as_json(views_data, simul_name, Tier, end_date)

    return views_data
