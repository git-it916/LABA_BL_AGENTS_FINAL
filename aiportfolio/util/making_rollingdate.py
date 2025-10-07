import pandas as pd
from datetime import datetime

def get_rolling_dates(forecast_date):

    rolling_dates = []
    
    for period_str in forecast_date:

        end_date = pd.to_datetime(period_str, format='%y-%m-%d')
        rolling_end_date = end_date - pd.DateOffset(months=1) + pd.offsets.MonthEnd(0)
        rolling_start_date = end_date - pd.DateOffset(years=10)
        
        rolling_dates.append({
            'forecast_date': end_date,
            'start_date': rolling_start_date,
            'end_date': rolling_end_date
        })

    return rolling_dates