"""
run_single.py와 run_batch.py 스크립트 테스트

이 스크립트는 자동 입력으로 두 스크립트를 테스트합니다.
"""

import subprocess
import sys


def test_run_single():
    """run_single.py 자동 테스트"""
    print("\n" + "="*80)
    print("run_single.py 테스트")
    print("="*80)

    # 자동 입력 데이터
    inputs = [
        "test_single_demo",  # 시뮬레이션 이름
        "1",                 # Tier
        "2024-05-31",        # 예측 날짜
        "0.025",             # tau
        "y"                  # 확인
    ]

    print("\n[알림] 자동 입력 데이터:")
    print(f"  시뮬레이션 이름: {inputs[0]}")
    print(f"  Tier: {inputs[1]}")
    print(f"  예측 날짜: {inputs[2]}")
    print(f"  tau: {inputs[3]}")

    print("\n[경고] 이 테스트는 실제로 LLM을 실행하므로 GPU가 필요하고 시간이 오래 걸립니다.")
    print("[경고] Ctrl+C를 눌러 중단할 수 있습니다.")

    confirm = input("\n계속 진행하시겠습니까? (y/n): ").strip().lower()
    if confirm != 'y':
        print("[취소] 테스트가 취소되었습니다.")
        return

    try:
        # run_single.py 실행
        process = subprocess.Popen(
            [sys.executable, "run_single.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 입력 제공
        input_str = "\n".join(inputs) + "\n"
        stdout, stderr = process.communicate(input=input_str, timeout=600)  # 10분 타임아웃

        print("\n[출력]")
        print(stdout)

        if stderr:
            print("\n[오류]")
            print(stderr)

        if process.returncode == 0:
            print("\n[성공] run_single.py 테스트 완료")
        else:
            print(f"\n[실패] run_single.py가 코드 {process.returncode}로 종료되었습니다.")

    except subprocess.TimeoutExpired:
        print("\n[타임아웃] 테스트가 10분을 초과했습니다.")
        process.kill()
    except KeyboardInterrupt:
        print("\n[중단] 사용자가 테스트를 중단했습니다.")
        process.kill()
    except Exception as e:
        print(f"\n[오류] 테스트 중 오류 발생: {e}")


def test_run_batch():
    """run_batch.py 자동 테스트"""
    print("\n" + "="*80)
    print("run_batch.py 테스트")
    print("="*80)

    # 자동 입력 데이터
    inputs = [
        "test_batch_demo",   # 시뮬레이션 이름
        "1",                 # Tier
        "2024-04-30",        # 시작 날짜
        "2024-06-30",        # 종료 날짜 (3개월)
        "0.025",             # tau
        "y"                  # 확인
    ]

    print("\n[알림] 자동 입력 데이터:")
    print(f"  시뮬레이션 이름: {inputs[0]}")
    print(f"  Tier: {inputs[1]}")
    print(f"  시작 날짜: {inputs[2]}")
    print(f"  종료 날짜: {inputs[3]}")
    print(f"  tau: {inputs[4]}")

    print("\n[경고] 이 테스트는 3개월치 배치 실행이므로 약 6~15분 소요됩니다.")
    print("[경고] GPU가 필요합니다.")

    confirm = input("\n계속 진행하시겠습니까? (y/n): ").strip().lower()
    if confirm != 'y':
        print("[취소] 테스트가 취소되었습니다.")
        return

    try:
        # run_batch.py 실행
        process = subprocess.Popen(
            [sys.executable, "run_batch.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 입력 제공
        input_str = "\n".join(inputs) + "\n"
        stdout, stderr = process.communicate(input=input_str, timeout=1800)  # 30분 타임아웃

        print("\n[출력]")
        print(stdout)

        if stderr:
            print("\n[오류]")
            print(stderr)

        if process.returncode == 0:
            print("\n[성공] run_batch.py 테스트 완료")
        else:
            print(f"\n[실패] run_batch.py가 코드 {process.returncode}로 종료되었습니다.")

    except subprocess.TimeoutExpired:
        print("\n[타임아웃] 테스트가 30분을 초과했습니다.")
        process.kill()
    except KeyboardInterrupt:
        print("\n[중단] 사용자가 테스트를 중단했습니다.")
        process.kill()
    except Exception as e:
        print(f"\n[오류] 테스트 중 오류 발생: {e}")


def main():
    """메인 메뉴"""
    print("\n" + "="*80)
    print("Black-Litterman 스크립트 테스트")
    print("="*80)
    print("\n선택하세요:")
    print("1. run_single.py 테스트 (단일 시점)")
    print("2. run_batch.py 테스트 (다중 시점 배치)")
    print("3. 둘 다 테스트")
    print("4. 종료")

    choice = input("\n선택 (1-4): ").strip()

    if choice == '1':
        test_run_single()
    elif choice == '2':
        test_run_batch()
    elif choice == '3':
        test_run_single()
        if input("\nrun_batch.py 테스트를 계속하시겠습니까? (y/n): ").strip().lower() == 'y':
            test_run_batch()
    elif choice == '4':
        print("\n종료합니다.")
    else:
        print("\n[오류] 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
