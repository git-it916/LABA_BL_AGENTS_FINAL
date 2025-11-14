import pandas as pd
from datetime import datetime

def match_sp500_by_date(filtered_file, sp500_file, output_file, 
                        ticker_column='Ticker', date_column='DlyCalDt'):
    """
    필터링된 파일의 ticker와 날짜를 SP500 기간별 리스트와 매칭합니다.
    
    Parameters:
    - filtered_file: 필터링된 CSV 파일 경로
    - sp500_file: SP500 ticker 기간 정보 CSV 파일 경로
    - output_file: 결과 파일 경로
    - ticker_column: ticker가 있는 열 이름 (기본값: 'Ticker')
    - date_column: 날짜가 있는 열 이름 (기본값: 'DlyCalDt')
    """
    
    print("=" * 70)
    print("SP500 기간별 매칭 시작")
    print("=" * 70)
    
    # 1단계: 필터링된 파일 읽기
    print(f"\n[1단계] 필터링된 파일 읽는 중: {filtered_file}")
    df_filtered = pd.read_csv(filtered_file)
    total_records = len(df_filtered)
    print(f"✓ 전체 레코드 수: {total_records:,}개")
    
    # 열 확인
    if ticker_column not in df_filtered.columns:
        print(f"\n✗ 오류: '{ticker_column}' 열을 찾을 수 없습니다.")
        print(f"사용 가능한 열: {', '.join(df_filtered.columns)}")
        return
    
    if date_column not in df_filtered.columns:
        print(f"\n✗ 오류: '{date_column}' 열을 찾을 수 없습니다.")
        print(f"사용 가능한 열: {', '.join(df_filtered.columns)}")
        return
    
    print(f"✓ Ticker 열: '{ticker_column}'")
    print(f"✓ 날짜 열: '{date_column}'")
    
    # 2단계: SP500 기간 파일 읽기
    print(f"\n[2단계] SP500 기간 파일 읽는 중: {sp500_file}")
    df_sp500 = pd.read_csv(sp500_file)
    sp500_tickers = len(df_sp500)
    print(f"✓ SP500 기간 레코드 수: {sp500_tickers:,}개")
    
    # 3단계: 날짜 변환
    print(f"\n[3단계] 날짜 형식 변환 중...")
    
    # 필터링 파일의 날짜 변환
    df_filtered[date_column] = pd.to_datetime(df_filtered[date_column])
    print(f"✓ {date_column} 변환 완료")
    
    # SP500 파일의 날짜 변환
    df_sp500['start_date'] = pd.to_datetime(df_sp500['start_date'])
    
    # end_date가 비어있으면 현재 날짜로 대체 (여전히 SP500에 포함)
    df_sp500['end_date'] = df_sp500['end_date'].fillna('2099-12-31')
    df_sp500['end_date'] = pd.to_datetime(df_sp500['end_date'])
    
    print(f"✓ start_date, end_date 변환 완료")
    
    # Ticker를 대문자로 통일
    df_filtered['ticker_upper'] = df_filtered[ticker_column].str.strip().str.upper()
    df_sp500['ticker_upper'] = df_sp500['Ticker'].str.strip().str.upper()
    
    # 4단계: 매칭 수행
    print(f"\n[4단계] 기간별 매칭 진행 중...")
    print(f"  (이 작업은 시간이 걸릴 수 있습니다...)")
    
    # 결과를 저장할 리스트
    sp500_flags = []
    
    # 각 레코드에 대해 SP500 여부 확인
    batch_size = 10000
    total_batches = (total_records + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, total_records)
        
        batch_flags = []
        for idx in range(start_idx, end_idx):
            row = df_filtered.iloc[idx]
            ticker = row['ticker_upper']
            date = row[date_column]
            
            # 해당 ticker의 SP500 기간 찾기
            sp500_periods = df_sp500[df_sp500['ticker_upper'] == ticker]
            
            # 날짜가 어떤 기간에라도 포함되는지 확인
            is_in_sp500 = False
            for _, period in sp500_periods.iterrows():
                if period['start_date'] <= date <= period['end_date']:
                    is_in_sp500 = True
                    break
            
            batch_flags.append(1 if is_in_sp500 else 0)
        
        sp500_flags.extend(batch_flags)
        
        # 진행 상황 표시
        if (batch_num + 1) % 10 == 0 or batch_num == total_batches - 1:
            progress = ((batch_num + 1) / total_batches) * 100
            processed = min((batch_num + 1) * batch_size, total_records)
            print(f"  진행: {processed:,}/{total_records:,} ({progress:.1f}%)")
    
    # sp500 열 추가
    df_filtered['sp500'] = sp500_flags
    
    # 임시 열 삭제
    df_filtered = df_filtered.drop(columns=['ticker_upper'])
    
    # 매칭 결과 통계
    sp500_matched = df_filtered['sp500'].sum()
    non_sp500 = total_records - sp500_matched
    match_rate = (sp500_matched / total_records * 100) if total_records > 0 else 0
    
    print(f"\n✓ 매칭 완료!")
    print(f"  SP500 포함 (sp500=1): {sp500_matched:,}개 ({match_rate:.1f}%)")
    print(f"  SP500 미포함 (sp500=0): {non_sp500:,}개 ({100-match_rate:.1f}%)")
    
    # 5단계: 결과 저장
    print(f"\n[5단계] 결과 저장 중: {output_file}")
    df_filtered.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    import os
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    print(f"✓ 저장 완료! (파일 크기: {file_size:.2f} MB)")
    
    # 6단계: 샘플 데이터 표시
    print(f"\n[6단계] 결과 미리보기:")
    print("-" * 70)
    
    # SP500 종목 샘플
    sp500_samples = df_filtered[df_filtered['sp500'] == 1].head(5)
    if len(sp500_samples) > 0:
        print("\n✓ SP500 포함 예시:")
        for _, row in sp500_samples.iterrows():
            print(f"  {row[ticker_column]:6s} | {row[date_column]} | sp500 = 1")
    
    # 비SP500 종목 샘플
    non_sp500_samples = df_filtered[df_filtered['sp500'] == 0].head(5)
    if len(non_sp500_samples) > 0:
        print("\n✓ SP500 미포함 예시:")
        for _, row in non_sp500_samples.iterrows():
            print(f"  {row[ticker_column]:6s} | {row[date_column]} | sp500 = 0")
    
    # 7단계: 추가 통계
    print("\n" + "=" * 70)
    print("상세 통계")
    print("=" * 70)
    
    # 고유 ticker 수
    unique_tickers = df_filtered[ticker_column].nunique()
    sp500_unique_tickers = df_filtered[df_filtered['sp500'] == 1][ticker_column].nunique()
    
    print(f"\n전체 통계:")
    print(f"  총 레코드: {total_records:,}개")
    print(f"  고유 ticker 수: {unique_tickers:,}개")
    print(f"  SP500 포함 레코드: {sp500_matched:,}개 ({match_rate:.1f}%)")
    print(f"  SP500 포함 ticker 수: {sp500_unique_tickers:,}개")
    
    # 날짜 범위
    date_range = f"{df_filtered[date_column].min().strftime('%Y-%m-%d')} ~ {df_filtered[date_column].max().strftime('%Y-%m-%d')}"
    print(f"  날짜 범위: {date_range}")
    
    print(f"\n✅ 작업 완료! 'sp500' 열이 추가되었습니다.")


# 사용 예시
if __name__ == "__main__":
    # 설정
    filtered_file = r"C:\Users\shins\OneDrive\문서\필터링결과_11.14.csv"
    sp500_file = r"C:\Users\shins\OneDrive\문서\sp500_ticker_start_end.csv"
    output_file = r"C:\Users\shins\OneDrive\문서\SP500매칭결과_11.14.csv"
    ticker_column = "Ticker"      # 필터링결과 파일의 ticker 열 이름
    date_column = "DlyCalDt"      # 필터링결과 파일의 날짜 열 이름
    
    # 실행
    try:
        match_sp500_by_date(filtered_file, sp500_file, output_file, ticker_column, date_column)
    except FileNotFoundError as e:
        print(f"\n✗ 오류: 파일을 찾을 수 없습니다.")
        print(f"  {e}")
        print("\n파일명과 경로를 확인해주세요.")
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
