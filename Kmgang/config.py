import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(BASE_DIR, "input")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
EXCEL_PATH = os.path.join(BASE_DIR, "급식집계.xlsx")

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

# 체크마크로 인식할 문자 목록
CHECK_MARKS = ['v', 'V', '✓', '✔', '√', 'o', 'O', '○', '0', 'ㅇ']

# 중식 헤더 키워드
LUNCH_KEYWORDS = ['중식', '점심', '중']

# 석식 헤더 키워드
DINNER_KEYWORDS = ['석식', '저녁', '석']

# 날짜 패턴 (이미지 내 텍스트에서 인식)
DATE_PATTERNS = [
    r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})',   # 2026-05-07
    r'(\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})',    # 26-05-07
    r'(\d{1,2})[.\-/](\d{1,2})',                  # 05/07 (월/일)
]

# 엑셀 시트 이름
SHEET_DAILY = '일별집계'
SHEET_MONTHLY = '월별집계'

# 엑셀 헤더 색상 (ARGB)
COLOR_HEADER_DAILY = 'FF4472C4'    # 파란색
COLOR_HEADER_MONTHLY = 'FF70AD47'  # 초록색
COLOR_TOTAL_ROW = 'FFFFD966'       # 노란색 (합계행)
