import pandas as pd
import os
import json
import re
from pandas.tseries.offsets import MonthEnd

from aiportfolio.agents.prepare.Tier2_calculate import calculate_accounting_indicator

# python -m aiportfolio.agents.prompt_accounting

def _to_month_end(ts_like) -> pd.Timestamp:
    """다양한 문자열/타입의 날짜 입력을 안전하게 '월말' Timestamp로 변환."""
    if isinstance(ts_like, pd.Timestamp):
        return (ts_like + MonthEnd(0))
    # 여러 포맷 시도
    for fmt in [None, "%Y-%m-%d", "%Y-%m", "%B-%y", "%b-%y"]:
        try:
            dt = pd.to_datetime(ts_like, format=fmt) if fmt else pd.to_datetime(ts_like)
            return (dt + MonthEnd(0))
        except Exception:
            continue
    # 최후: 현재로
    return (pd.Timestamp(ts_like) + MonthEnd(0))


def making_acc_INPUT(end_date):
    """
    end_date: 'YYYY-MM[-DD]' 또는 'Month-YY'(예: 'January-10') 등 입력을 받아 월말로 정규화.
    반환: 섹터별 회계지표(7개) 딕셔너리 리스트.
    """
    end_date = _to_month_end(end_date)

    # calculate_accounting_indicator() 출력:
    # ['date','gsector','acct_level_lagged_avg','metric']  (date는 월말)
    data = calculate_accounting_indicator()

    sectors = [
        "Energy", "Materials", "Industrials", "Consumer Discretionary",
        "Consumer Staples", "Health Care", "Financials", "Information Technology",
        "Communication Services", "Utilities", "Real Estate"
    ]

    METRIC_MAP = [
        ("Book/Market (bm) — 3-month lagged avg (t-3,t-4,t-5)", "bm_Mean"),
        ("Shiller CAPE (capei) — 3-month lagged avg (t-3,t-4,t-5)", "CAPEI_Mean"),
        ("Gross Profit / Total Assets (gprof) — 3-month lagged avg (t-3,t-4,t-5)", "GProf_Mean"),
        ("Net Profit Margin (npm) — 3-month lagged avg (t-3,t-4,t-5)", "npm_Mean"),
        ("Return on Assets (ROA) — 3-month lagged avg (t-3,t-4,t-5)", "roa_Mean"),
        ("Return on Equity (ROE) — 3-month lagged avg (t-3,t-4,t-5)", "roe_Mean"),
        ("Total Debt / Invested Capital — 3-month lagged avg (t-3,t-4,t-5)", "totdebt_invcap_Mean"),
    ]

    # (date, gsector, metric) → acct_level_lagged_avg
    df = data.copy()
    # 안전을 위해 date를 월말로 보장
    df['date'] = (pd.to_datetime(df['date']) + MonthEnd(0))
    df = df.sort_values(['gsector', 'metric', 'date'])

    # 섹터-지표별 시계열 시리즈 딕셔너리로 변환 (ffill 되어 있음)
    series_map = {}
    for (sec, met), grp in df.groupby(['gsector', 'metric']):
        s = grp.set_index('date')['acct_level_lagged_avg'].sort_index()
        s = s[~s.index.duplicated(keep='last')]
        series_map[(sec, met)] = s

    def get_val(sector: str, metric_code: str, dt: pd.Timestamp):
        s = series_map.get((sector, metric_code))
        if s is None or s.empty:
            return None
        # dt 이전/당월까지의 값 중 마지막
        s_part = s.loc[:dt]
        if s_part.empty:
            # dt 이전이 아예 없으면 앞으로 있는 첫 값 반환
            # (초기 구간 보장: null 방지)
            return round(float(s.iloc[0]), 4)
        return round(float(s_part.iloc[-1]), 4)


    sector_acc_data_list = []
    for sct in sectors:
        entry = {"sector": sct}
        for label, metric_code in METRIC_MAP:
            entry[label] = get_val(sct, metric_code, end_date)
        sector_acc_data_list.append(entry)

    return sector_acc_data_list


def making_user_prompt(end_date):
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'user_prompt.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("오류: 해당 경로에 파일이 없습니다.")
        content = ""
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        content = ""

    a = making_acc_INPUT(end_date=end_date)
    data_string = json.dumps(a, indent=2, ensure_ascii=False)
    final_output = content.replace("<acc_INPUT>", data_string)  # 유지

    return final_output


def making_system_prompt():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'prompt_template', 'system_prompt.txt')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("오류: 해당 경로에 파일이 없습니다.")
        content = ""
    except Exception as e:
        print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        content = ""
    
    return content


# ---------------------------
# Stage 2 JSON 안전 추출 유틸
# ---------------------------
def extract_stage2_json(prompt_text: str) -> str:
    """
    프롬프트에서 Stage 2 (Accounting Data) JSON 블록만 정확히 추출.
    [=== Start of 11-Sector Accounting Data ... ===]
    [=== End of 11-Sector Accounting Data ===]
    사이의 첫 JSON 배열([ ... ])을 균형검사로 가져온다.
    """
    m = re.search(
        r"\[=== Start of 11-Sector Accounting Data.*?===\](.*?)[\r\n]+\[=== End of 11-Sector Accounting Data ===\]",
        prompt_text,
        re.S
    )
    block = m.group(1) if m else prompt_text

    start = block.find('[')
    if start == -1:
        raise ValueError("Stage 2 구간 안에 '[' 로 시작하는 JSON 배열이 없습니다.")

    depth = 0
    for i, ch in enumerate(block[start:], start=start):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                return block[start:i+1].strip()

    raise ValueError("JSON 배열 대괄호가 균형을 이루지 않습니다.")


# ---------------------------
# 테스트 실행부
# ---------------------------
if __name__ == "__main__":
    # 원하는 테스트 날짜(아무 형식이나 OK: '2024-05-31', '2024-05', 'May-24', 'May 2024' 등)
    test_date = "May-2024"

    print("[테스트] 프롬프트 생성 및 JSON 구조 확인 중...\n")

    # 유저 프롬프트 생성
    output_prompt = making_user_prompt(end_date=test_date)

    # 미리보기
    print("=== 생성된 프롬프트 일부 미리보기 ===")
    print(output_prompt[:800])
    print("... (생략) ...\n")

    # Stage 2 JSON 추출 및 파싱
    try:
        json_text = extract_stage2_json(output_prompt)
        parsed = json.loads(json_text)

        print("[✅] Stage 2 JSON 파싱 성공!")
        print(f"→ 총 섹터 개수: {len(parsed)}개")
        if parsed:
            print(f"→ 첫 섹터: {parsed[0].get('sector')}")
            keys = list(parsed[0].keys())
            print(f"→ 포함 지표 키 샘플: {keys[1:4]} ...")
            # 값 샘플
            sample_vals = [parsed[0][k] for k in keys[1:4]]
            print(f"→ 값 샘플: {sample_vals}")
    except Exception as e:
        print("[⚠️] Stage 2 JSON 파싱 실패:")
        print(e)
