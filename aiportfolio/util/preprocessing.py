import pandas as pd
import numpy as np

def preprocessing(df):

    # 1. MKT(시가총액) 컬럼 추가
    df['MKT'] = df['PRC'] * df['SHROUT'] * 1_000_000

    # 2. 종가, 상장주식수, vwretd, sprtrn 컬럼 제거(데이터 바뀌면 제거해야됨)
    processed_df = df.drop(columns=['PRC', 'SHROUT', 'vwretd', 'sprtrn'], errors='ignore')
    
    # 3. 섹터별 시가총액 계산
    sector_market_cap = processed_df.groupby(['date', 'SECTOR'])['MKT'].sum().reset_index()
    sector_market_cap.rename(columns={'MKT': 'MKT_SEC'}, inplace=True)
    processed_df = processed_df.merge(sector_market_cap, on=['date', 'SECTOR'], how='left')
    
    # 4. 각 종목의 섹터 내 시가총액 비중 계산
    processed_df['w_MKT'] = processed_df['MKT'] / processed_df['MKT_SEC']
    
    # 5. 시총가중 수익률 계산 (종목별 수익률 × 시총비중)
    processed_df['w_RET'] = processed_df['RET'] * processed_df['w_MKT']
    
    # 6. 섹터별로 가중 수익률 합계 계산 (= 섹터별 시총가중 수익률)
    df_sector = processed_df.groupby(['date', 'SECTOR']).agg({
        'w_RET': 'sum',  # 섹터별 시총가중 수익률
        'MKT_SEC': 'first'  # 섹터 시가총액 (모든 행이 동일하므로 first 사용)
    }).reset_index()
    df_sector.rename(columns={'w_RET': 'RET_SEC'}, inplace=True)

    # print("\n최종 데이터프레임 생성 완료")
    # print(f"최종 컬럼: {list(df_sector.columns)}")
    
    return df_sector

def display_summary(df, result_df):
    """데이터 처리 결과 요약 출력"""
    print("\n" + "="*50)
    print("데이터 처리 결과 요약")
    print("="*50)
    
    print(f"원본 데이터: {len(df)}개 행, {len(df.columns)}개 컬럼")
    print(f"처리 후 데이터: {len(result_df)}개 행, {len(result_df.columns)}개 컬럼")
    
    if '현재날짜' in result_df.columns:
        print(f"날짜 범위: {result_df['현재날짜'].min()} ~ {result_df['현재날짜'].max()}")
    
    if '섹터' in result_df.columns:
        print(f"섹터 수: {result_df['섹터'].nunique()}개")
        print(f"섹터 목록: {', '.join(result_df['섹터'].unique())}")
    
    print(f"\n샘플 데이터:")
    print(result_df)