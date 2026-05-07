import cv2
import numpy as np
import re
import os
from datetime import datetime
from config import (
    CHECK_MARKS, LUNCH_KEYWORDS, DINNER_KEYWORDS, DATE_PATTERNS
)

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        import easyocr
        print("  EasyOCR 모델 로딩 중 (최초 1회)...")
        _reader = easyocr.Reader(['ko', 'en'], gpu=False)
    return _reader


def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"이미지를 열 수 없습니다: {image_path}")

    # 이미지 크기 제한 (너무 크면 처리 느림)
    h, w = img.shape[:2]
    if w > 2000:
        scale = 2000 / w
        img = cv2.resize(img, (2000, int(h * scale)))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 대비 향상
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 노이즈 제거
    denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

    return denoised


def extract_date_from_text(ocr_results):
    """OCR 결과 텍스트에서 날짜 추출"""
    full_text = ' '.join([text for _, text, _ in ocr_results])

    for pattern in DATE_PATTERNS:
        match = re.search(pattern, full_text)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3:
                    year, month, day = groups
                    if len(year) == 2:
                        year = '20' + year
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                elif len(groups) == 2:
                    month, day = groups
                    year = datetime.now().year
                    return f"{year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue
    return None


def extract_date_from_filename(filepath):
    """파일명에서 날짜 추출"""
    basename = os.path.basename(filepath)
    patterns = [
        r'(\d{4})(\d{2})(\d{2})',   # 20260507
        r'(\d{4})[.\-_](\d{2})[.\-_](\d{2})',  # 2026-05-07
        r'(\d{2})[.\-_](\d{2})[.\-_](\d{2})',  # 26-05-07
    ]
    for pattern in patterns:
        match = re.search(pattern, basename)
        if match:
            y, m, d = match.groups()
            if len(y) == 2:
                y = '20' + y
            try:
                dt = datetime(int(y), int(m), int(d))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
    return None


def find_column_x(ocr_results, keywords):
    """헤더에서 지정 키워드 컬럼의 x 중앙 좌표 반환"""
    for bbox, text, conf in ocr_results:
        text_clean = text.strip()
        for kw in keywords:
            if kw in text_clean:
                xs = [pt[0] for pt in bbox]
                return (min(xs) + max(xs)) / 2
    return None


def count_checks_in_column(ocr_results, col_x, col_tolerance=80, header_y=None):
    """특정 x좌표 범위에서 체크마크 개수 세기"""
    count = 0
    for bbox, text, conf in ocr_results:
        text_clean = text.strip().lower()
        xs = [pt[0] for pt in bbox]
        ys = [pt[1] for pt in bbox]
        center_x = (min(xs) + max(xs)) / 2
        center_y = (min(ys) + max(ys)) / 2

        # 헤더 행 아래만 체크
        if header_y is not None and center_y <= header_y:
            continue

        # x좌표가 컬럼 범위 내에 있는지
        if abs(center_x - col_x) > col_tolerance:
            continue

        # 체크마크 문자인지 확인
        for mark in CHECK_MARKS:
            if text_clean == mark.lower() or text_clean == mark:
                count += 1
                break
        else:
            # 단일 문자 체크마크 (v, o 등) - 이름이 아닌 짧은 텍스트
            if len(text_clean) <= 2 and any(m.lower() in text_clean for m in CHECK_MARKS):
                count += 1

    return count


def get_header_y(ocr_results, lunch_x, dinner_x):
    """헤더 행의 y 좌표 반환"""
    for bbox, text, conf in ocr_results:
        text_clean = text.strip()
        for kw in LUNCH_KEYWORDS + DINNER_KEYWORDS:
            if kw in text_clean:
                ys = [pt[1] for pt in bbox]
                return max(ys)
    return None


def analyze(image_path):
    """
    이미지 분석 메인 함수
    반환: {'date': 'YYYY-MM-DD', '중식': int, '석식': int}
    """
    print(f"  이미지 분석: {os.path.basename(image_path)}")

    processed = preprocess_image(image_path)
    reader = get_reader()

    # PIL Image로 변환해서 EasyOCR에 전달
    results = reader.readtext(processed, detail=1, paragraph=False)

    if not results:
        raise ValueError("텍스트를 인식하지 못했습니다.")

    # 날짜 추출
    date = extract_date_from_text(results)
    if not date:
        date = extract_date_from_filename(image_path)
    if not date:
        mtime = os.path.getmtime(image_path)
        date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
        print(f"  날짜를 이미지/파일명에서 찾지 못해 파일 수정일시 사용: {date}")

    # 중식/석식 컬럼 x좌표 찾기
    lunch_x = find_column_x(results, LUNCH_KEYWORDS)
    dinner_x = find_column_x(results, DINNER_KEYWORDS)

    if lunch_x is None and dinner_x is None:
        raise ValueError("중식/석식 컬럼 헤더를 찾지 못했습니다. 이미지를 확인하세요.")

    header_y = get_header_y(results, lunch_x, dinner_x)

    lunch_count = count_checks_in_column(results, lunch_x, header_y=header_y) if lunch_x else 0
    dinner_count = count_checks_in_column(results, dinner_x, header_y=header_y) if dinner_x else 0

    print(f"  결과 → 날짜: {date}, 중식: {lunch_count}명, 석식: {dinner_count}명")

    return {
        'date': date,
        '중식': lunch_count,
        '석식': dinner_count,
    }
