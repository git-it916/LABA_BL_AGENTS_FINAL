import pandas as pd
import os

# python -m aiportfolio.agents.prepare.Tier3_calculate

def calculate_macro_indicator():
    file_path = os.path.join('database','Tier3.csv')

    data = pd.read_csv(file_path)

    # 컬럼명 변경
    data = data.rename(columns=
                    {'observation_date': 'date', 
                        'G20 CLI': 'G20_CLI'})

    # datetime 형식으로 변환
    data['date'] = pd.to_datetime(data['date'])

    # 월의 말일 기준으로 변경
    data['date'] = data['date'] + pd.offsets.MonthEnd(0)

    return data