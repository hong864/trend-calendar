#!/usr/bin/env python3
"""
Notion 데이터베이스에서 트렌드 캘린더 데이터를 가져와 data.json으로 저장합니다.

필요 환경변수:
  - NOTION_TOKEN: Notion 통합(internal integration) 시크릿 키
  - NOTION_DATABASE_ID: 데이터베이스 ID (UUID)

stdlib만 사용 — 추가 의존성 없음.
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.error

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

if not NOTION_TOKEN:
    print("[ERROR] NOTION_TOKEN 환경변수가 비어 있습니다.", file=sys.stderr)
    sys.exit(1)
if not NOTION_DATABASE_ID:
    print("[ERROR] NOTION_DATABASE_ID 환경변수가 비어 있습니다.", file=sys.stderr)
    sys.exit(1)

# Notion API 버전. 이 날짜는 데이터베이스 query API가 안정적으로 작동하는 버전.
NOTION_VERSION = "2022-06-28"
API_URL = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


def query_page(start_cursor=None):
    body = {"page_size": 100}
    if start_cursor:
        body["start_cursor"] = start_cursor
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] Notion API {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 요청 실패: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_all_rows():
    rows = []
    cursor = None
    while True:
        page = query_page(cursor)
        rows.extend(page.get("results", []))
        if not page.get("has_more"):
            break
        cursor = page.get("next_cursor")
    return rows


def get_title(prop):
    if not prop:
        return ""
    arr = prop.get("title") or []
    return "".join(p.get("plain_text", "") for p in arr)


def get_rich_text(prop):
    if not prop:
        return ""
    arr = prop.get("rich_text") or []
    return "".join(p.get("plain_text", "") for p in arr)


def get_select(prop):
    if not prop:
        return None
    sel = prop.get("select")
    return sel["name"] if sel else None


def get_status(prop):
    if not prop:
        return None
    s = prop.get("status")
    return s["name"] if s else None


def get_multi(prop):
    if not prop:
        return []
    return [s.get("name") for s in (prop.get("multi_select") or [])]


def get_date(prop):
    if not prop:
        return (None, None)
    d = prop.get("date")
    if not d:
        return (None, None)
    start = d.get("start")
    end = d.get("end")
    # Strip time portion if present (we only need date)
    if start and "T" in start:
        start = start.split("T")[0]
    if end and "T" in end:
        end = end.split("T")[0]
    return (start, end)


def normalize_priority(pri):
    """🔴 높음 / 🟡 보통 / ⚪ 낮음 → 높음 / 보통 / 낮음"""
    if not pri:
        return None
    if "높음" in pri:
        return "높음"
    if "보통" in pri:
        return "보통"
    if "낮음" in pri:
        return "낮음"
    return pri


def transform(row):
    props = row.get("properties", {})
    title = get_title(props.get("제목", {}))
    start, end = get_date(props.get("날짜", {}))
    return {
        "title": title,
        "start": start,
        "end": end if end and end != start else None,
        "type": get_select(props.get("유형", {})),
        "dept": get_multi(props.get("담당 부서", {})),
        "priority": normalize_priority(get_select(props.get("우선순위", {}))),
        "keywords": get_multi(props.get("키워드", {})),
        "action": get_rich_text(props.get("액션 아이템", {})) or None,
        "memo": get_rich_text(props.get("메모", {})) or None,
        "status": get_status(props.get("상태", {})),
    }


def main():
    print(f"[INFO] Notion DB 조회 시작: {NOTION_DATABASE_ID}")
    rows = fetch_all_rows()
    print(f"[INFO] {len(rows)}건 조회됨")

    events = [transform(r) for r in rows]

    # 날짜가 없는 항목은 제외
    events = [e for e in events if e["start"]]

    # 시작 날짜로 정렬
    events.sort(key=lambda e: (e["start"], e["title"] or ""))

    output = {
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(events),
        "events": events,
    }

    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[INFO] {out_path} 에 {len(events)}건 저장 완료")


if __name__ == "__main__":
    main()
