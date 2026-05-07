"""
식수명단 이미지 자동 분석 → 엑셀 기록 스크립트

사용법:
  python analyze_meal_image.py 4월/0428.jpg
  python analyze_meal_image.py 0430.jpg --date 2026-04-30
  python analyze_meal_image.py 0428.jpg --dry-run

환경변수:
  ANTHROPIC_API_KEY  (필수)
"""

import sys
import os
import json
import base64
import subprocess
import argparse
import io
from pathlib import Path

import anthropic

# ── Vision 프롬프트 ───────────────────────────────────────────────────────────
PROMPT = """\
이 이미지는 식수 명단(식사 서명 장부)입니다. 종이가 90도 회전되어 있을 수 있습니다.

폼 구조:
- 열 구성: 소속 브랜드 | 이름 | 사인(서명)
- 좌우로 동일 구조 2패널이 나란히 배치될 수 있음
- 상단에 날짜(일자)와 중식/석식 표기 있음

판단 기준 (엄격히 적용):
✓ 포함: 이름 칸에 이름이 있고 + 사인 칸에 서명/필기/체크가 있는 행
✗ 제외: 이름만 있고 사인 칸이 비어 있는 행
✗ 제외: 사인만 있고 이름 칸이 비어 있는 행
✗ 제외: 이름·사인 모두 비어 있는 행

brand_map: 서명한 모든 사람의 {이름: 소속브랜드} 매핑을 포함하세요.

JSON만 출력하세요 (설명 없이):
{"date":"YYYY-MM-DD","lunch":["이름1","이름2"],"dinner":["이름3"],"brand_map":{"이름1":"브랜드A","이름2":"브랜드B","이름3":"브랜드A"}}
저녁 섹션이 없으면: "dinner":[]
날짜를 읽을 수 없으면: "date":"unknown"\
"""


def _stdout():
    return io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def encode_image(path: str) -> tuple:
    """이미지를 base64로 인코딩, (data, media_type) 반환"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {path}")
    ext = p.suffix.lower()
    media_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_map.get(ext, "image/jpeg")
    with open(p, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def analyze_image(image_path: str, override_date: str = None) -> dict:
    """Claude API Vision으로 이미지 분석 → 서명자 목록 반환"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.\n"
            "  PowerShell: $env:ANTHROPIC_API_KEY='sk-ant-...'\n"
            "  CMD:        set ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)
    data, media_type = encode_image(image_path)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": data,
                        },
                    },
                    {
                        "type": "text",
                        "text": PROMPT,
                        "cache_control": {"type": "ephemeral"},  # 프롬프트 캐싱
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()

    # 마크다운 코드블록 제거
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                result = json.loads(part)
                break
            except json.JSONDecodeError:
                continue
        else:
            raise ValueError(f"JSON 파싱 실패. Claude 응답:\n{raw}")
    else:
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            raise ValueError(f"JSON 파싱 실패. Claude 응답:\n{raw}")

    if override_date:
        result["date"] = override_date

    return result


def print_result(result: dict, out):
    """분석 결과 출력"""
    lunch = result.get("lunch", [])
    dinner = result.get("dinner", [])
    out.write(f"\n[분석 결과]\n")
    out.write(f"  날짜  : {result.get('date', '?')}\n")
    out.write(f"  점심  : {', '.join(lunch) if lunch else '없음'} ({len(lunch)}명)\n")
    if dinner:
        out.write(f"  저녁  : {', '.join(dinner)} ({len(dinner)}명)\n")
    else:
        out.write(f"  저녁  : 없음\n")
    out.flush()


def confirm_and_save(result: dict, out):
    """결과 확인 후 process_meal.py 호출"""
    print_result(result, out)

    if result.get("date") == "unknown":
        out.write(
            "\n[오류] 날짜를 인식하지 못했습니다.\n"
            "  --date YYYY-MM-DD 옵션으로 날짜를 직접 지정하세요.\n"
        )
        out.flush()
        sys.exit(1)

    out.write("\n엑셀에 기록할까요? (y/n): ")
    out.flush()

    try:
        answer = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"

    if answer != "y":
        out.write("\n[취소] 엑셀 기록을 건너뜁니다.\n")
        out.write(f"수동 실행: python process_meal.py '{json.dumps(result, ensure_ascii=False)}'\n")
        out.flush()
        return

    script = Path(__file__).parent / "process_meal.py"
    try:
        subprocess.run(
            [sys.executable, str(script), json.dumps(result, ensure_ascii=False)],
            check=True,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        out.write(f"\n[오류] process_meal.py 실행 실패: {e}\n")
        out.flush()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="식수명단 이미지 → Claude Vision 분석 → 엑셀 자동 기록"
    )
    parser.add_argument("image", help="이미지 파일 경로 (jpg/png/webp)")
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="날짜 수동 지정 (이미지에서 읽지 못할 때)")
    parser.add_argument("--dry-run", action="store_true", help="분석만 하고 엑셀 기록 안 함")
    args = parser.parse_args()

    out = _stdout()
    out.write(f"[분석 중] {args.image}\n")
    out.flush()

    try:
        result = analyze_image(args.image, args.date)
    except FileNotFoundError as e:
        out.write(f"[오류] {e}\n")
        out.flush()
        sys.exit(1)
    except EnvironmentError as e:
        out.write(f"[오류] {e}\n")
        out.flush()
        sys.exit(1)
    except ValueError as e:
        out.write(f"[오류] {e}\n")
        out.flush()
        sys.exit(1)

    if args.dry_run:
        print_result(result, out)
        out.write("\n[dry-run] 엑셀 기록 생략됨.\n")
        out.flush()
        return

    confirm_and_save(result, out)


if __name__ == "__main__":
    main()
