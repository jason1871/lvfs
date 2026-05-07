import json
import openpyxl

EXCEL_FILE = "아암센터 식수명단_260424.xlsx"
OUTPUT_FILE = "master_members.json"


def parse_master():
    wb = openpyxl.load_workbook(EXCEL_FILE, read_only=True, data_only=True)
    ws = wb["양식"]

    # 브랜드별로 모은 뒤 등장 순서 유지하며 펼치기
    from collections import OrderedDict
    brand_map: OrderedDict[str, list[str]] = OrderedDict()
    seen: set[tuple] = set()

    for row in ws.iter_rows(min_row=4, values_only=True):
        pairs = [
            (row[1] if len(row) > 1 else None, row[2] if len(row) > 2 else None),  # 좌: 컬럼2, 3
            (row[4] if len(row) > 4 else None, row[5] if len(row) > 5 else None),  # 우: 컬럼5, 6
        ]
        for brand_raw, name_raw in pairs:
            if not brand_raw or not name_raw:
                continue
            b, n = str(brand_raw).strip(), str(name_raw).strip()
            if not n or (b, n) in seen:
                continue
            brand_map.setdefault(b, []).append(n)
            seen.add((b, n))

    members = [{"brand": b, "name": n} for b, names in brand_map.items() for n in names]

    wb.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

    brands: dict[str, list] = {}
    for m in members:
        brands.setdefault(m["brand"], []).append(m["name"])

    print(f"완료: {len(members)}명 → {OUTPUT_FILE}")
    for brand, names in brands.items():
        print(f"  {brand}: {len(names)}명")


if __name__ == "__main__":
    parse_master()
