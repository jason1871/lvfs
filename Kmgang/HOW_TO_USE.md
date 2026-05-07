# 아암센터 식수 명단 자동 정리 — 사용 안내

---

## ⚡ 자동화 (신규) — 이미지 한 장으로 끝내기

### 최초 1회 설정

```powershell
pip install anthropic openpyxl
$env:ANTHROPIC_API_KEY = "sk-ant-..."   # Anthropic API 키 입력
```

### 매일 사용법

```powershell
python analyze_meal_image.py 4월\0428.jpg
```

실행하면:
1. Claude AI가 이미지를 분석해 이름+사인 모두 있는 사람 자동 추출
2. 결과 미리보기 표시
3. `엑셀에 기록할까요? (y/n):` → y 입력 시 엑셀 자동 업데이트

**날짜를 인식 못 할 때:**
```powershell
python analyze_meal_image.py 0430.jpg --date 2026-04-30
```

**결과만 확인하고 싶을 때 (엑셀 기록 안 함):**
```powershell
python analyze_meal_image.py 0428.jpg --dry-run
```

---

## 최초 1회 설정

```bash
pip install openpyxl
python parse_master.py
```

`master_members.json` 이 생성되면 준비 완료.  
멤버가 바뀔 때마다 다시 실행하면 됨.

---

## 매일 사용법 (이미지 → 엑셀)

### 1단계: 이미지 첨부

Claude Code 채팅창에 식수 명단 사진을 붙여넣는다.

### 2단계: Claude에게 분석 요청

아래 문구를 이미지와 함께 전달한다:

```
이 식수 명단 이미지에서 사인란에 서명이 있는 사람의 이름을 추출하세요.
점심과 저녁 섹션을 구분하여 JSON으로만 응답하세요. 설명 없이.
형식: {"date":"YYYY-MM-DD","lunch":["이름1","이름2"],"dinner":["이름3"]}
저녁 섹션이 없으면 "dinner":[]
```

### 3단계: 엑셀 기록

Claude가 반환한 JSON으로 아래 명령 실행:

```bash
python process_meal.py '{"date":"2026-04-26","lunch":["김광섭","조중훈"],"dinner":["김광섭"]}'
```

저녁이 없는 날:
```bash
python process_meal.py '{"date":"2026-04-26","lunch":["김광섭"],"dinner":[]}'
```

---

## 결과 확인

`아암센터 식수명단_260424.xlsx` 를 열면 날짜명 시트와 월별 집계 시트가 추가되어 있음.

### 날짜 시트 (예: `2026-04-26`)

| 브랜드 | 이름 | 점심 | 저녁 |
|--------|------|------|------|
| 시코르 | 김광섭 | O | X |
| 시코르 | 조중훈 | O |  |
| ? | 홍길동 | O |  |  ← 노랑 표시

- `O` : 서명 있음 (식사)
- `X` : 서명 없음 (미식사)
- 빈칸(저녁) : 저녁 없는 날
- **노랑 이름 셀** : Vision이 인식했지만 마스터에 없는 이름 → 수동 확인 필요

### 월별 집계 시트 (예: `2026-04_집계`)

멤버별 해당 월 점심·저녁 누적 횟수가 자동으로 기록됨.  
날짜 시트를 처리할 때마다 자동 갱신됨.

---

## 월 마감

월이 끝나면 해당 월 데이터를 별도 파일로 저장:

```bash
python process_meal.py --close-month 2026-04
```

`2026-04_아암센터_식수명단.xlsx` 파일이 생성됨 (날짜 시트 + 집계 시트 포함).

---

## 주의사항

- **노랑 이름 셀**이 있으면 해당 이름을 수동으로 확인·수정
- 동일 날짜 재실행 시 날짜 시트와 월별 집계 시트 모두 덮어씀
- 멤버 명단이 변경되면 `python parse_master.py` 재실행
