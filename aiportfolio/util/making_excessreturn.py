import os
import pandas as pd

from .open_file import open_file
from .preprocessing import preprocessing

def final():
    df = preprocessing(open_file('database', 'example.csv'))

    folder_name = 'database'
    file_name = 'rf.csv'
    file_path = os.path.join(folder_name, file_name)
    df_rf = pd.read_csv(file_path)

    df_rf['date'] = pd.to_datetime(df_rf['date'])

    df['year_month'] = df['date'].dt.to_period('M')
    df_rf['year_month'] = df_rf['date'].dt.to_period('M')

    merged_df = pd.merge(df, df_rf, on='year_month', how='left')
    merged_df.drop(columns=['year_month', 'date_y'], inplace=True)
    merged_df.rename(columns={'date_x': 'date'}, inplace=True)

    # 초과수익률 생성
    merged_df['ExcessReturn'] = merged_df['RET_SEC'] - merged_df['rf']

    final_df = merged_df[['date', 'SECTOR', 'ExcessReturn', 'MKT_SEC']]

    return final_df
