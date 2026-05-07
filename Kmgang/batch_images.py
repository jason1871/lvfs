"""5월/5.4(1~5).jpg 일괄 분석 → 엑셀 기록"""
import sys
import os
import io
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyze_meal_image import analyze_image
from process_meal import process


def _stdout():
    return io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def main():
    out = _stdout()

    images = [f"5월/5.4({i}).jpg" for i in range(1, 6)]
    date_override = "2026-05-04"

    merged = {"date": date_override, "lunch": [], "dinner": [], "brand_map": {}}

    for img in images:
        out.write(f"[분석 중] {img}\n")
        out.flush()
        try:
            result = analyze_image(img, override_date=date_override)
        except Exception as e:
            out.write(f"  [오류] {e}\n")
            out.flush()
            continue

        lunch = result.get("lunch", [])
        dinner = result.get("dinner", [])
        brand_map = result.get("brand_map", {})

        out.write(f"  점심 {len(lunch)}명: {', '.join(lunch) or '없음'}\n")
        if dinner:
            out.write(f"  저녁 {len(dinner)}명: {', '.join(dinner)}\n")
        out.flush()

        for name in lunch:
            if name not in merged["lunch"]:
                merged["lunch"].append(name)
        for name in dinner:
            if name not in merged["dinner"]:
                merged["dinner"].append(name)
        merged["brand_map"].update(brand_map)

    out.write(f"\n[합산 결과]\n")
    out.write(f"  점심 {len(merged['lunch'])}명: {', '.join(merged['lunch'])}\n")
    if merged["dinner"]:
        out.write(f"  저녁 {len(merged['dinner'])}명: {', '.join(merged['dinner'])}\n")
    else:
        out.write(f"  저녁: 없음\n")
    out.flush()

    process(merged)


if __name__ == "__main__":
    main()
