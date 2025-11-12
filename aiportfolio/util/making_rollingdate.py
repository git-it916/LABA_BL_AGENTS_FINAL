import pandas as pd
from datetime import datetime

def get_rolling_dates(forecast_date):
    """
    예측 기간 문자열 리스트를 받아 롤링 날짜를 생성합니다.

    Args:
        forecast_date (list): 예측 기간 문자열 리스트 (예: ["24-05-31", "24-06-30", ...])

    Returns:
        list: 각 기간별 딕셔너리 리스트
            - forecast_date: 예측 기준일
            - start_date: 분석 시작일 (10년 전)
            - end_date: 분석 종료일 (1개월 전)
    """
    rolling_dates = []

    for period_str in forecast_date:
        try:
            # 날짜 파싱 (YY-MM-DD 형식 지원)
            end_date = pd.to_datetime(period_str, format='%y-%m-%d')

            # 1개월 전의 월말
            rolling_end_date = (end_date - pd.DateOffset(months=1)).to_period('M').to_timestamp('M')

            # 10년 전의 월말
            rolling_start_date = (end_date - pd.DateOffset(years=10)).to_period('M').to_timestamp('M')

            rolling_dates.append({
                'forecast_date': end_date,
                'start_date': rolling_start_date,
                'end_date': rolling_end_date
            })

        except Exception as e:
            print(f"[오류] 날짜 파싱 실패: {period_str} - {e}")
            continue

    return rolling_dates