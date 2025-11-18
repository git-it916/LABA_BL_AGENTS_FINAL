"""
자동 데이터 업데이트 및 전처리 파이프라인

새로운 주식 데이터를 추가하면 자동으로 모든 전처리를 실행합니다.

주요 기능:
1. 새 데이터 자동 감지
2. 데이터 검증 및 병합
3. Tier 1/2/3 지표 자동 재계산
4. 백테스트 데이터 자동 업데이트

사용법:
    # 새 데이터 추가 + 자동 전처리
    python auto_update_data.py --add-data "new_data.parquet"

    # 파일 감시 모드 (백그라운드 실행)
    python auto_update_data.py --watch

    # 전처리만 다시 실행
    python auto_update_data.py --reprocess
"""

import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np


class AutoDataPipeline:
    """자동 데이터 업데이트 및 전처리 파이프라인"""

    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.database_path = self.base_path / 'database'

        # 주요 데이터 파일 경로
        self.files = {
            'daily': self.database_path / 'final_stock_daily.parquet',
            'monthly': self.database_path / 'final_stock_months.parquet',
            'accounting': self.database_path / 'compustat_2021.01_2024.12.csv',
            'macro': self.database_path / 'Tier3.csv'
        }

        # 마지막 수정 시간 기록
        self.last_modified = {}
        self._update_modification_times()

    def _update_modification_times(self):
        """파일 수정 시간 업데이트"""
        for name, filepath in self.files.items():
            if filepath.exists():
                self.last_modified[name] = filepath.stat().st_mtime
            else:
                self.last_modified[name] = 0

    def check_file_changes(self):
        """파일 변경 감지"""
        changed = []
        for name, filepath in self.files.items():
            if not filepath.exists():
                continue

            current_mtime = filepath.stat().st_mtime
            if current_mtime > self.last_modified.get(name, 0):
                changed.append(name)

        return changed

    def validate_new_data(self, new_data_path):
        """
        새 데이터 검증

        Args:
            new_data_path: 추가할 데이터 파일 경로

        Returns:
            (is_valid, error_message)
        """
        try:
            new_data = pd.read_parquet(new_data_path)

            # 필수 컬럼 체크
            required_cols = ['DlyCalDt', 'PERMNO', 'RET', 'gsector']
            missing_cols = [col for col in required_cols if col not in new_data.columns]

            if missing_cols:
                return False, f"필수 컬럼 누락: {missing_cols}"

            # 날짜 형식 체크
            try:
                new_data['DlyCalDt'] = pd.to_datetime(new_data['DlyCalDt'])
            except:
                return False, "DlyCalDt 컬럼을 날짜로 변환할 수 없습니다"

            # 데이터 존재 여부
            if len(new_data) == 0:
                return False, "데이터가 비어있습니다"

            return True, None

        except Exception as e:
            return False, f"파일 읽기 오류: {e}"

    def add_new_data(self, new_data_path, backup=True):
        """
        새 데이터를 기존 데이터에 병합

        Args:
            new_data_path: 추가할 데이터 파일 경로
            backup: 백업 생성 여부

        Returns:
            성공 여부
        """
        print("\n" + "="*80)
        print("새 데이터 추가 시작")
        print("="*80)

        # 검증
        is_valid, error_msg = self.validate_new_data(new_data_path)
        if not is_valid:
            print(f"[오류] 데이터 검증 실패: {error_msg}")
            return False

        try:
            # 기존 데이터 로드
            existing_path = self.files['daily']

            if existing_path.exists():
                existing_data = pd.read_parquet(existing_path)
                print(f"[알림] 기존 데이터: {len(existing_data):,}행")

                # 백업 생성
                if backup:
                    backup_path = existing_path.parent / f"{existing_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
                    existing_data.to_parquet(backup_path, index=False)
                    print(f"[백업] {backup_path.name}")
            else:
                existing_data = pd.DataFrame()
                print("[알림] 기존 데이터 없음 (새로 생성)")

            # 새 데이터 로드
            new_data = pd.read_parquet(new_data_path)
            new_data['DlyCalDt'] = pd.to_datetime(new_data['DlyCalDt'])
            print(f"[알림] 새 데이터: {len(new_data):,}행")

            # 날짜 범위 확인
            new_min = new_data['DlyCalDt'].min()
            new_max = new_data['DlyCalDt'].max()
            print(f"[알림] 새 데이터 기간: {new_min.date()} ~ {new_max.date()}")

            # 데이터 병합
            if not existing_data.empty:
                combined = pd.concat([existing_data, new_data], ignore_index=True)
            else:
                combined = new_data

            # 중복 제거 (날짜 + 종목 기준)
            before_dedup = len(combined)
            combined = combined.drop_duplicates(subset=['DlyCalDt', 'PERMNO'], keep='last')
            duplicates_removed = before_dedup - len(combined)

            if duplicates_removed > 0:
                print(f"[알림] 중복 제거: {duplicates_removed:,}행")

            # 정렬
            combined = combined.sort_values(['DlyCalDt', 'PERMNO'])

            # 저장
            combined.to_parquet(existing_path, index=False)

            print(f"\n[성공] 최종 데이터: {len(combined):,}행")
            print(f"  추가된 행: {len(new_data) - duplicates_removed:,}행")
            print(f"  전체 기간: {combined['DlyCalDt'].min().date()} ~ {combined['DlyCalDt'].max().date()}")

            return True

        except Exception as e:
            print(f"[오류] 데이터 병합 실패: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_tier1_preprocessing(self):
        """Tier 1 기술적 지표 재계산"""
        print("\n" + "="*80)
        print("Tier 1: 기술적 지표 재계산")
        print("="*80)

        try:
            from aiportfolio.agents.prepare.Tier1_calculate import indicator

            print("[실행] indicator() 호출 중...")
            result = indicator()

            if result is not None and not result.empty:
                print(f"[성공] {len(result):,}행 계산 완료")
                print(f"  날짜: {result['date'].nunique()}개")
                print(f"  섹터: {result['gsector'].nunique()}개")

                # 최신 데이터 확인
                latest = result['date'].max()
                print(f"  최신 데이터: {latest.date()}")

                return True
            else:
                print("[경고] 반환값이 비어있음")
                return False

        except Exception as e:
            print(f"[오류] {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_tier2_preprocessing(self):
        """Tier 2 회계 지표 재계산"""
        print("\n" + "="*80)
        print("Tier 2: 회계 지표 재계산")
        print("="*80)

        try:
            from aiportfolio.agents.prepare.Tier2_calculate import calculate_accounting_indicator

            print("[실행] calculate_accounting_indicator() 호출 중...")
            result = calculate_accounting_indicator()

            if result is not None and not result.empty:
                print(f"[성공] {len(result):,}행 계산 완료")
                print(f"  날짜: {result['date'].nunique()}개")
                print(f"  섹터: {result['gsector'].nunique()}개")
                print(f"  지표: {result['metric'].nunique()}개")

                latest = result['date'].max()
                print(f"  최신 데이터: {latest.date()}")

                return True
            else:
                print("[경고] 반환값이 비어있음")
                return False

        except Exception as e:
            print(f"[오류] {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_tier3_preprocessing(self):
        """Tier 3 매크로 지표 재계산"""
        print("\n" + "="*80)
        print("Tier 3: 매크로 지표 재계산")
        print("="*80)

        try:
            from aiportfolio.agents.prepare.Tier3_calculate import calculate_macro_indicator

            print("[실행] calculate_macro_indicator() 호출 중...")
            result = calculate_macro_indicator()

            if result is not None and not result.empty:
                print(f"[성공] {len(result):,}행 계산 완료")
                print(f"  날짜: {result['date'].nunique()}개")

                latest = result['date'].max()
                print(f"  최신 데이터: {latest.date()}")

                return True
            else:
                print("[경고] 반환값이 비어있음")
                return False

        except Exception as e:
            print(f"[오류] {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_backtest_preprocessing(self):
        """백테스트용 일별 수익률 재계산"""
        print("\n" + "="*80)
        print("백테스트: 일별 섹터 수익률 재계산")
        print("="*80)

        try:
            from aiportfolio.backtest.preprocessing import sector_daily_returns

            print("[실행] sector_daily_returns() 호출 중...")
            result = sector_daily_returns()

            if result is not None and not result.empty:
                print(f"[성공] {len(result):,}행 계산 완료")
                print(f"  날짜: {result['DlyCalDt'].nunique()}개")
                print(f"  섹터: {result['gsector'].nunique()}개")

                latest = result['DlyCalDt'].max()
                print(f"  최신 데이터: {latest.date()}")

                return True
            else:
                print("[경고] 반환값이 비어있음")
                return False

        except Exception as e:
            print(f"[오류] {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_full_pipeline(self):
        """전체 전처리 파이프라인 실행"""
        start_time = time.time()

        print("\n" + "="*80)
        print(f"전처리 파이프라인 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # 각 단계 실행
        results = {}

        results['tier1'] = self.run_tier1_preprocessing()
        results['tier2'] = self.run_tier2_preprocessing()
        results['tier3'] = self.run_tier3_preprocessing()
        results['backtest'] = self.run_backtest_preprocessing()

        # 결과 요약
        elapsed = time.time() - start_time

        print("\n" + "="*80)
        print("전처리 파이프라인 완료")
        print("="*80)

        success_count = sum(results.values())
        total_count = len(results)

        print(f"\n소요 시간: {elapsed:.1f}초")
        print(f"성공: {success_count}/{total_count}")

        for stage, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {stage}")

        # 수정 시간 업데이트
        self._update_modification_times()

        return success_count == total_count

    def watch_and_process(self, interval=60):
        """파일 변경 감시 및 자동 전처리"""
        print("\n" + "="*80)
        print("자동 감시 모드 시작")
        print("="*80)
        print(f"감시 간격: {interval}초")
        print(f"\n감시 파일:")
        for name, filepath in self.files.items():
            status = "존재" if filepath.exists() else "없음"
            print(f"  [{status}] {name}: {filepath.name}")

        print("\n종료: Ctrl+C\n")

        try:
            while True:
                changed = self.check_file_changes()

                if changed:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 변경 감지: {', '.join(changed)}")
                    print("→ 전처리 파이프라인 시작\n")

                    self.run_full_pipeline()

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n[종료] 감시 모드 종료됨")


def main():
    parser = argparse.ArgumentParser(
        description='자동 데이터 업데이트 및 전처리 파이프라인',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:

  1. 새 데이터 추가 + 자동 전처리
     python auto_update_data.py --add-data "database/new_stock_data.parquet"

  2. 전처리만 다시 실행
     python auto_update_data.py --reprocess

  3. 파일 변경 감시 모드 (자동 실행)
     python auto_update_data.py --watch

  4. 현재 데이터 상태만 확인
     python auto_update_data.py --status
        """
    )

    parser.add_argument('--add-data', metavar='FILE',
                        help='새 데이터 파일 추가 (parquet 형식)')
    parser.add_argument('--reprocess', action='store_true',
                        help='전처리만 다시 실행')
    parser.add_argument('--watch', action='store_true',
                        help='파일 변경 감시 모드')
    parser.add_argument('--status', action='store_true',
                        help='현재 데이터 상태 확인')
    parser.add_argument('--interval', type=int, default=60,
                        help='감시 간격 (초, 기본값: 60)')
    parser.add_argument('--no-backup', action='store_true',
                        help='데이터 추가 시 백업 생성 안함')

    args = parser.parse_args()

    # 파이프라인 초기화
    pipeline = AutoDataPipeline()

    # 모드 실행
    if args.add_data:
        # 새 데이터 추가
        new_data_path = Path(args.add_data)

        if not new_data_path.exists():
            print(f"[오류] 파일을 찾을 수 없습니다: {new_data_path}")
            sys.exit(1)

        success = pipeline.add_new_data(new_data_path, backup=not args.no_backup)

        if success:
            print("\n데이터가 성공적으로 추가되었습니다.")
            print("전처리를 시작합니다...\n")

            pipeline.run_full_pipeline()
        else:
            print("\n[오류] 데이터 추가 실패")
            sys.exit(1)

    elif args.reprocess:
        # 전처리만 실행
        success = pipeline.run_full_pipeline()
        sys.exit(0 if success else 1)

    elif args.watch:
        # 감시 모드
        pipeline.watch_and_process(interval=args.interval)

    elif args.status:
        # 상태 확인
        print("\n현재 데이터 상태:")

        daily_file = pipeline.files['daily']
        if daily_file.exists():
            df = pd.read_parquet(daily_file)
            df['DlyCalDt'] = pd.to_datetime(df['DlyCalDt'])

            print(f"\n일별 주식 데이터 ({daily_file.name}):")
            print(f"  총 행수: {len(df):,}")
            print(f"  기간: {df['DlyCalDt'].min().date()} ~ {df['DlyCalDt'].max().date()}")
            print(f"  거래일: {df['DlyCalDt'].nunique():,}개")
            print(f"  종목수: {df['PERMNO'].nunique():,}개")
        else:
            print(f"\n[경고] {daily_file.name} 파일이 없습니다")

    else:
        # 기본: 도움말
        parser.print_help()


if __name__ == "__main__":
    main()
