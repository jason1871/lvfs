import os
import shutil
import sys
from config import INPUT_DIR, PROCESSED_DIR, IMAGE_EXTENSIONS
import analyzer
import excel_manager


def ensure_dirs():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def get_image_files():
    files = []
    for fname in os.listdir(INPUT_DIR):
        if fname.lower().endswith(IMAGE_EXTENSIONS):
            files.append(os.path.join(INPUT_DIR, fname))
    return sorted(files)


def move_to_processed(image_path):
    filename = os.path.basename(image_path)
    dest = os.path.join(PROCESSED_DIR, filename)
    # 동일 파일명 있으면 타임스탬프 붙임
    if os.path.exists(dest):
        name, ext = os.path.splitext(filename)
        import time
        dest = os.path.join(PROCESSED_DIR, f"{name}_{int(time.time())}{ext}")
    shutil.move(image_path, dest)


def main():
    print("=" * 50)
    print("  급식 인원 집계 시스템 시작")
    print("=" * 50)

    ensure_dirs()
    images = get_image_files()

    if not images:
        print(f"\n처리할 이미지가 없습니다.")
        print(f"  → {INPUT_DIR}")
        print("위 폴더에 사진을 넣고 다시 실행하세요.")
        return

    print(f"\n총 {len(images)}개 이미지 처리 시작\n")

    success, failed = 0, 0
    failed_files = []

    for i, image_path in enumerate(images, 1):
        fname = os.path.basename(image_path)
        print(f"[{i}/{len(images)}] {fname}")
        try:
            result = analyzer.analyze(image_path)
            excel_manager.append_daily(
                result['date'],
                result['중식'],
                result['석식']
            )
            move_to_processed(image_path)
            success += 1
        except Exception as e:
            print(f"  오류 발생: {e}")
            failed += 1
            failed_files.append(fname)
        print()

    print("=" * 50)
    print(f"  처리 완료: 성공 {success}건 / 실패 {failed}건")
    if failed_files:
        print("  실패 파일:")
        for f in failed_files:
            print(f"    - {f}")
    print(f"  결과 파일: 급식집계.xlsx")
    print("=" * 50)


if __name__ == '__main__':
    main()
