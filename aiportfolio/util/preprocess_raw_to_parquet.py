"""
통합 전처리 파이프라인: raw_data.csv → final_stock_daily.parquet

이 스크립트는 흩어진 전처리 파일들을 통합합니다:
- daily_NQ_data.py: 거래소 필터링 (N/Q만 유지)
- daily_sp500.py: SP500 기간별 매칭
- daily_GICS.py: GICS 섹터 매칭
- open_DTB3.py: 무위험 수익률 데이터 로드

입력: database/raw_data.csv
출력: database/final_stock_daily.parquet
모든 처리는 메모리에서 수행 (중간 파일 저장 없음)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys


class RawToParquetPipeline:
    """raw_data.csv를 final_stock_daily.parquet로 변환하는 통합 파이프라인"""

    def __init__(self, base_path=None):
        """
        Args:
            base_path (str or Path, optional): 프로젝트 루트 경로
                None이면 현재 작업 디렉토리 사용
        """
        if base_path is None:
            self.base_path = Path.cwd()
        else:
            self.base_path = Path(base_path)

        self.database_path = self.base_path / "database"

        # 입력 파일 경로
        self.raw_data_path = self.database_path / "raw_data.csv"
        self.sp500_periods_path = self.database_path / "sp500_ticker_start_end.csv"
        self.gics_mapping_path = self.database_path / "ticker_GICS.csv"

        # 출력 파일 경로
        self.output_parquet = self.database_path / "final_stock_daily.parquet"
        self.mcap_daily_csv = self.database_path / "mcap_by_exchange_daily.csv"

        # 데이터프레임 (메모리)
        self.df = None
        self.df_sp500 = None
        self.df_gics = None

    def validate_input_files(self):
        """필수 입력 파일 존재 여부 확인"""
        print("\n" + "="*70)
        print("입력 파일 검증")
        print("="*70)

        required_files = {
            "Raw data": self.raw_data_path,
            "SP500 periods": self.sp500_periods_path,
            "GICS mapping": self.gics_mapping_path
        }

        missing_files = []
        for name, path in required_files.items():
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                print(f"✓ {name}: {path} ({size_mb:.2f} MB)")
            else:
                print(f"✗ {name}: {path} (없음)")
                missing_files.append(name)

        if missing_files:
            print(f"\n✗ 오류: 다음 파일을 찾을 수 없습니다: {', '.join(missing_files)}")
            sys.exit(1)

        print("\n✓ 모든 입력 파일 확인 완료")

    def load_raw_data(self):
        """raw_data.csv 로드"""
        print("\n" + "="*70)
        print("[1단계] Raw 데이터 로드")
        print("="*70)

        print(f"\n파일 읽는 중: {self.raw_data_path}")
        self.df = pd.read_csv(self.raw_data_path)

        print(f"✓ 로드 완료: {len(self.df):,}개 레코드")
        print(f"  컬럼: {', '.join(self.df.columns)}")
        print(f"  메모리 사용량: {self.df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")

        # 필수 컬럼 확인
        required_cols = ['PrimaryExch', 'Ticker', 'DlyCalDt', 'DlyCap', 'DlyRet']
        missing_cols = [col for col in required_cols if col not in self.df.columns]

        if missing_cols:
            print(f"\n✗ 오류: 필수 컬럼 누락: {', '.join(missing_cols)}")
            sys.exit(1)

        print(f"✓ 필수 컬럼 확인 완료")

    def filter_exchanges(self):
        """거래소 필터링: N (NYSE), Q (NASDAQ)만 유지"""
        print("\n" + "="*70)
        print("[2단계] 거래소 필터링 (N/Q만 유지)")
        print("="*70)

        # 현재 거래소 분포
        print("\n현재 'PrimaryExch' 분포:")
        exchange_counts = self.df['PrimaryExch'].value_counts()
        for exchange, count in exchange_counts.items():
            keep_marker = "← 유지" if exchange in ['N', 'Q'] else "← 삭제"
            print(f"  {exchange}: {count:,}개 {keep_marker}")

        # 필터링
        before_count = len(self.df)
        self.df = self.df[self.df['PrimaryExch'].isin(['N', 'Q'])]
        after_count = len(self.df)
        deleted_count = before_count - after_count

        print(f"\n✓ 필터링 완료!")
        print(f"  삭제된 행: {deleted_count:,}개")
        print(f"  남은 행: {after_count:,}개")
        print(f"  삭제율: {(deleted_count/before_count*100):.1f}%")

    def calculate_mcap_by_exchange(self):
        """날짜×거래소별 시가총액 집계 (mcap_by_exchange_daily.csv 생성)"""
        print("\n" + "="*70)
        print("[3단계] 거래소별 시가총액 집계")
        print("="*70)

        # 날짜 파싱
        df_temp = self.df.copy()
        df_temp["DlyCalDt"] = pd.to_datetime(df_temp["DlyCalDt"])

        # 날짜×거래소별 시총 합계 피벗
        pivot = (
            df_temp
            .groupby(["DlyCalDt", "PrimaryExch"], as_index=False)["DlyCap"]
            .sum()
            .pivot(index="DlyCalDt", columns="PrimaryExch", values="DlyCap")
            .fillna(0.0)
        )

        # 컬럼명 정리
        pivot = pivot.rename(columns={"N": "mcap_N", "Q": "mcap_Q"})
        if "mcap_N" not in pivot.columns:
            pivot["mcap_N"] = 0.0
        if "mcap_Q" not in pivot.columns:
            pivot["mcap_Q"] = 0.0

        # 합계 및 비율
        pivot["total_mcap"] = pivot["mcap_N"] + pivot["mcap_Q"]
        pivot["ratio_N"] = np.where(pivot["total_mcap"] > 0,
                                     pivot["mcap_N"] / pivot["total_mcap"], 0.0)
        pivot["ratio_Q"] = np.where(pivot["total_mcap"] > 0,
                                     pivot["mcap_Q"] / pivot["total_mcap"], 0.0)

        # 저장
        pivot.reset_index().to_csv(self.mcap_daily_csv, index=False, encoding="utf-8-sig")

        print(f"\n✓ 거래소별 시총 파일 저장: {self.mcap_daily_csv}")
        print(f"\n[미리보기] mcap_by_exchange_daily.csv (상위 5행)")
        print(pivot.reset_index().head(5))

        # 요약 통계
        if "mcap_N" in pivot.columns and "mcap_Q" in pivot.columns:
            n_sum = pivot["mcap_N"].sum()
            q_sum = pivot["mcap_Q"].sum()
            print(f"\n[요약] 전체 기간 시가총액 합계:")
            print(f"  N (NYSE): {n_sum:,.0f}")
            print(f"  Q (NASDAQ): {q_sum:,.0f}")
            print(f"  총합: {n_sum + q_sum:,.0f}")

    def match_sp500(self):
        """SP500 기간별 매칭"""
        print("\n" + "="*70)
        print("[4단계] SP500 기간별 매칭")
        print("="*70)

        # SP500 기간 파일 로드
        print(f"\nSP500 기간 파일 읽는 중: {self.sp500_periods_path}")
        self.df_sp500 = pd.read_csv(self.sp500_periods_path)
        print(f"✓ SP500 기간 레코드 수: {len(self.df_sp500):,}개")

        # 날짜 변환
        print(f"\n날짜 형식 변환 중...")
        self.df['DlyCalDt'] = pd.to_datetime(self.df['DlyCalDt'])
        self.df_sp500['start_date'] = pd.to_datetime(self.df_sp500['start_date'])

        # end_date가 비어있으면 2099-12-31로 대체 (여전히 SP500에 포함)
        self.df_sp500['end_date'] = self.df_sp500['end_date'].fillna('2099-12-31')
        self.df_sp500['end_date'] = pd.to_datetime(self.df_sp500['end_date'])

        print(f"✓ start_date, end_date 변환 완료")

        # Ticker를 대문자로 통일
        self.df['ticker_upper'] = self.df['Ticker'].str.strip().str.upper()
        self.df_sp500['ticker_upper'] = self.df_sp500['Ticker'].str.strip().str.upper()

        # 매칭 수행
        print(f"\n기간별 매칭 진행 중...")
        print(f"  (이 작업은 시간이 걸릴 수 있습니다...)")

        total_records = len(self.df)
        batch_size = 10000
        total_batches = (total_records + batch_size - 1) // batch_size

        sp500_flags = []

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, total_records)

            batch_flags = []
            for idx in range(start_idx, end_idx):
                row = self.df.iloc[idx]
                ticker = row['ticker_upper']
                date = row['DlyCalDt']

                # 해당 ticker의 SP500 기간 찾기
                sp500_periods = self.df_sp500[self.df_sp500['ticker_upper'] == ticker]

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
        self.df['sp500'] = sp500_flags

        # 임시 열 삭제
        self.df = self.df.drop(columns=['ticker_upper'])

        # 매칭 결과 통계
        sp500_matched = self.df['sp500'].sum()
        non_sp500 = total_records - sp500_matched
        match_rate = (sp500_matched / total_records * 100) if total_records > 0 else 0

        print(f"\n✓ 매칭 완료!")
        print(f"  SP500 포함 (sp500=1): {sp500_matched:,}개 ({match_rate:.1f}%)")
        print(f"  SP500 미포함 (sp500=0): {non_sp500:,}개 ({100-match_rate:.1f}%)")

    def match_gics_sector(self):
        """GICS 섹터 매칭"""
        print("\n" + "="*70)
        print("[5단계] GICS 섹터 매칭")
        print("="*70)

        # GICS 파일 로드
        print(f"\nGICS 파일 읽는 중: {self.gics_mapping_path}")
        self.df_gics = pd.read_csv(self.gics_mapping_path)
        print(f"✓ GICS 레코드 수: {len(self.df_gics):,}개")

        # GICS 파일의 ticker와 sector 열 찾기
        print(f"\nGICS 파일의 열:")
        for col in self.df_gics.columns:
            print(f"  - {col}")

        gics_ticker_col = None
        gics_sector_col = None

        for col in self.df_gics.columns:
            if col.lower() in ['ticker', 'symbol']:
                gics_ticker_col = col
                break

        for col in self.df_gics.columns:
            if 'sector' in col.lower() or col.lower() == 'gsector':
                gics_sector_col = col
                break

        if gics_ticker_col is None:
            print(f"\n✗ 오류: GICS 파일에서 ticker 열을 찾을 수 없습니다.")
            sys.exit(1)

        if gics_sector_col is None:
            print(f"\n✗ 오류: GICS 파일에서 sector 열을 찾을 수 없습니다.")
            sys.exit(1)

        print(f"\n✓ GICS Ticker 열: '{gics_ticker_col}'")
        print(f"✓ GICS Sector 열: '{gics_sector_col}'")

        # GICS 데이터 준비
        print(f"\nGICS 데이터 준비 중...")
        self.df_gics['ticker_upper'] = self.df_gics[gics_ticker_col].astype(str).str.strip().str.upper()
        gics_dict = self.df_gics.set_index('ticker_upper')[gics_sector_col].to_dict()
        print(f"✓ GICS 매핑 딕셔너리 생성 완료: {len(gics_dict):,}개")

        unique_sectors = self.df_gics[gics_sector_col].dropna().unique()
        print(f"✓ 고유 Sector 수: {len(unique_sectors)}개")
        print(f"\nSector 종류:")
        for sector in sorted(unique_sectors):
            sector_count = (self.df_gics[gics_sector_col] == sector).sum()
            print(f"  - {sector}: {sector_count}개")

        # 매칭 수행
        print(f"\nSector 매칭 중...")
        self.df['ticker_upper'] = self.df['Ticker'].astype(str).str.strip().str.upper()
        self.df['gsector'] = self.df['ticker_upper'].map(gics_dict)
        self.df = self.df.drop(columns=['ticker_upper'])

        total_records = len(self.df)
        matched_count = self.df['gsector'].notna().sum()
        unmatched_count = self.df['gsector'].isna().sum()
        match_rate = (matched_count / total_records * 100) if total_records > 0 else 0

        print(f"\n✓ 매칭 완료!")
        print(f"  매칭 성공: {matched_count:,}개 ({match_rate:.1f}%)")
        print(f"  매칭 실패: {unmatched_count:,}개 ({100-match_rate:.1f}%)")

        if unmatched_count > 0:
            unmatched_tickers = self.df[self.df['gsector'].isna()]['Ticker'].astype(str).unique()[:10]
            print(f"\n⚠ 매칭되지 않은 ticker 예시 (최대 10개):")
            for ticker in unmatched_tickers:
                print(f"  - {ticker}")

        # SP500 종목의 GICS 매칭률 확인
        if 'sp500' in self.df.columns:
            print("\n" + "="*70)
            print("SP500 포함 여부별 GICS 매칭 체크")
            print("="*70)

            sp500_no_gics = self.df[(self.df['sp500'] == 1) & (self.df['gsector'].isna())]
            sp500_no_gics_count = len(sp500_no_gics)

            if sp500_no_gics_count > 0:
                sp500_no_gics_tickers = sp500_no_gics['Ticker'].astype(str).unique()
                print(f"\n⚠ SP500에 포함되지만 GICS가 없는 종목: {len(sp500_no_gics_tickers)}개")
                print(f"   (총 {sp500_no_gics_count:,}개 레코드)")
                print(f"\nTicker 리스트:")
                for i, ticker in enumerate(sorted(sp500_no_gics_tickers), 1):
                    ticker_records = len(sp500_no_gics[sp500_no_gics['Ticker'] == ticker])
                    print(f"  {i:3d}. {ticker:6s} ({ticker_records:,}개 레코드)")
                    if i >= 50:
                        remaining = len(sp500_no_gics_tickers) - 50
                        if remaining > 0:
                            print(f"  ... 외 {remaining}개 더")
                        break
            else:
                print(f"\n✓ SP500 종목은 모두 GICS가 매칭되었습니다!")

            sp500_total = (self.df['sp500'] == 1).sum()
            sp500_with_gics = ((self.df['sp500'] == 1) & (self.df['gsector'].notna())).sum()
            sp500_gics_rate = (sp500_with_gics / sp500_total * 100) if sp500_total > 0 else 0

            print(f"\nSP500 GICS 매칭률:")
            print(f"  SP500 총 레코드: {sp500_total:,}개")
            print(f"  GICS 매칭 완료: {sp500_with_gics:,}개 ({sp500_gics_rate:.1f}%)")
            print(f"  GICS 매칭 안됨: {sp500_no_gics_count:,}개 ({100-sp500_gics_rate:.1f}%)")

    def clean_data(self):
        """데이터 정리 및 검증"""
        print("\n" + "="*70)
        print("[6단계] 데이터 정리")
        print("="*70)

        # GOOG 수동 보정
        goog_mask = self.df['Ticker'].astype(str).str.upper() == 'GOOG'
        goog_count = goog_mask.sum()
        if goog_count > 0:
            self.df.loc[goog_mask, 'gsector'] = 50.0
            print(f"\n✓ GOOG의 gsector를 50.0으로 설정: {goog_count:,}개 레코드")

        # GICS 없는 행 삭제
        before_delete = len(self.df)
        no_gics_count = self.df['gsector'].isna().sum()
        self.df = self.df[self.df['gsector'].notna()]
        after_delete = len(self.df)
        deleted_count = before_delete - after_delete

        print(f"\n✓ GICS 없는 행 삭제:")
        print(f"  삭제 전: {before_delete:,}개")
        print(f"  삭제 후: {after_delete:,}개")
        print(f"  삭제됨: {deleted_count:,}개 ({deleted_count/before_delete*100:.1f}%)")

        # 최종 통계
        print("\n" + "="*70)
        print("최종 데이터 통계")
        print("="*70)

        final_sector_stats = self.df['gsector'].value_counts()
        print(f"\n최종 Sector별 레코드 수:")
        for sector, count in final_sector_stats.items():
            percentage = (count / after_delete * 100)
            sector_str = str(sector) if pd.notna(sector) else "N/A"
            print(f"  {sector_str:30s}: {count:7,}개 ({percentage:5.1f}%)")

        print(f"\n✓ 최종 레코드 수: {after_delete:,}개")
        print(f"✓ 모든 레코드에 gsector가 할당되었습니다.")

    def save_parquet(self):
        """최종 결과를 Parquet로 저장"""
        print("\n" + "="*70)
        print("[7단계] Parquet 저장")
        print("="*70)

        # 필요한 컬럼만 선택 및 순서 정리
        final_columns = ['PrimaryExch', 'Ticker', 'DlyCalDt', 'DlyCap', 'DlyRet', 'sp500', 'gsector']
        self.df = self.df[final_columns]

        print(f"\n최종 데이터프레임 정보:")
        print(f"  행 수: {len(self.df):,}개")
        print(f"  열 수: {len(self.df.columns)}개")
        print(f"  컬럼: {', '.join(self.df.columns)}")
        print(f"  메모리 사용량: {self.df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")

        # Parquet 저장
        print(f"\nParquet 파일 저장 중: {self.output_parquet}")
        self.df.to_parquet(self.output_parquet, index=False, engine='pyarrow')

        file_size_mb = self.output_parquet.stat().st_size / (1024 * 1024)
        print(f"✓ 저장 완료! (파일 크기: {file_size_mb:.2f} MB)")

        # 샘플 데이터 표시
        print(f"\n[미리보기] final_stock_daily.parquet (상위 5행)")
        print(self.df.head(5))

        print(f"\n데이터 타입:")
        print(self.df.dtypes)

    def run(self):
        """전체 파이프라인 실행"""
        print("\n" + "="*70)
        print("통합 전처리 파이프라인 시작")
        print("="*70)
        print(f"입력: {self.raw_data_path}")
        print(f"출력: {self.output_parquet}")

        try:
            self.validate_input_files()
            self.load_raw_data()
            self.filter_exchanges()
            self.calculate_mcap_by_exchange()
            self.match_sp500()
            self.match_gics_sector()
            self.clean_data()
            self.save_parquet()

            print("\n" + "="*70)
            print("✅ 전체 파이프라인 완료!")
            print("="*70)
            print(f"\n생성된 파일:")
            print(f"  1. {self.output_parquet}")
            print(f"  2. {self.mcap_daily_csv}")

        except Exception as e:
            print(f"\n✗ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Raw CSV 데이터를 Parquet로 전처리하는 통합 파이프라인"
    )
    parser.add_argument(
        '--base-path',
        type=str,
        default=None,
        help="프로젝트 루트 경로 (기본값: 현재 작업 디렉토리)"
    )

    args = parser.parse_args()

    # 파이프라인 실행
    pipeline = RawToParquetPipeline(base_path=args.base_path)
    pipeline.run()


if __name__ == "__main__":
    main()