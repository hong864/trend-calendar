# 전사 트렌드 캘린더 (GitHub Pages + Notion 동기화)

Notion 데이터베이스의 트렌드/이벤트 데이터를 GitHub Actions가 주기적으로 가져와 정적 페이지로 보여줍니다.

- **데이터 원본**: Notion DB `트렌드 & 이벤트`
- **호스팅**: GitHub Pages (정적 HTML)
- **동기화 주기**: 매시간 (cron `0 * * * *`)
- **호스팅 비용**: 무료 (Public 레포 + GitHub Pages 무료 플랜)

## 구조

```
trend-calendar-site/
├── index.html                       # 캘린더 UI (data.json을 읽어 렌더링)
├── data.json                        # Actions가 갱신하는 데이터 파일
├── scripts/
│   └── sync_notion.py               # Notion API 호출 → data.json 생성
├── .github/workflows/
│   └── sync-notion.yml              # 매시간 실행되는 Actions
└── README.md
```

## 처음 한 번만 하는 설정 (약 10분)

### 1. GitHub 레포 만들기

- GitHub에서 새 Public 레포 생성 (이름 예: `trend-calendar`)
- 이 폴더(`trend-calendar-site/`) 내용물을 모두 레포 루트에 업로드
  - 웹에서 드래그&드롭으로 올리거나, `git clone` 후 복사 → `git push`

### 2. Notion 통합 생성 및 DB 연결

1. https://www.notion.so/profile/integrations 접속
2. **"+ New integration"** 클릭
   - Name: `Trend Calendar Sync` (자유)
   - Associated workspace: 본인 워크스페이스
   - Type: **Internal**
   - **저장**
3. 생성된 통합 페이지에서 **"Internal Integration Secret"** 키 복사 (`ntn_...`로 시작)
4. Notion에서 `[SAMPLE] 전사 트렌드 캘린더` 페이지 또는 `트렌드 & 이벤트` DB로 이동
5. 우상단 `⋯` → **"Connections"** → 방금 만든 통합 추가

### 3. GitHub Secrets 등록

GitHub 레포 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Name | Value |
|------|-------|
| `NOTION_TOKEN` | 2번에서 복사한 Internal Integration Secret |
| `NOTION_DATABASE_ID` | `277b81f4-483a-4d91-b0b9-6a371b1acc36` |

> 데이터베이스 ID는 Notion에서 DB를 열고 URL `notion.so/<이부분이ID>?v=…`에서 확인할 수 있습니다. 위 값은 현재 `트렌드 & 이벤트` DB의 ID입니다.

### 4. GitHub Pages 활성화

- 레포 → **Settings** → **Pages**
- **Source**: `Deploy from a branch`
- **Branch**: `main` / `/ (root)` 선택 후 **Save**
- 1~2분 뒤 `https://<사용자명>.github.io/trend-calendar/` 에서 접속 가능

### 5. 첫 동기화 실행

- 레포 → **Actions** 탭 → **Sync Notion data** 워크플로 선택
- 우측 **"Run workflow"** 버튼 → **Run workflow** 클릭
- 1분 안에 완료되며, `data.json`이 최신 Notion 데이터로 업데이트됨
- 페이지 새로고침하면 반영된 데이터가 보임

## 동작 방식

```
┌─────────────────┐
│   Notion DB     │  ← 사용자가 여기서 편집
│ 트렌드 & 이벤트 │
└────────┬────────┘
         │ Notion API (시간당 1회)
         ▼
┌─────────────────────────────┐
│  GitHub Actions             │
│  scripts/sync_notion.py     │
└────────┬────────────────────┘
         │ git commit + push
         ▼
┌─────────────────┐
│   data.json     │
│  (레포에 커밋)  │
└────────┬────────┘
         │ fetch
         ▼
┌─────────────────┐
│  index.html     │  ← 사용자가 여기서 조회
│ (GitHub Pages)  │
└─────────────────┘
```

## 자주 묻는 것

**Q. 동기화 주기를 더 짧게/길게 바꾸려면?**
`.github/workflows/sync-notion.yml`의 `cron` 값을 수정합니다. 예:
- `'*/15 * * * *'` — 15분마다
- `'0 */6 * * *'` — 6시간마다
- `'0 9 * * 1-5'` — 평일 오전 9시 (UTC)

> ⚠️ GitHub Actions 무료 플랜은 Public 레포에서 무제한이지만, Private 레포는 월 2,000분 제한이 있습니다. 너무 잦은 주기는 피하세요.

**Q. Notion에서 데이터 바꿨는데 즉시 반영하려면?**
**Actions** 탭 → **Sync Notion data** → **Run workflow** 수동 실행하면 1분 안에 반영됩니다.

**Q. 카테고리(`유형`) 옵션을 바꿨는데 페이지가 깨졌어요.**
`index.html`의 필터 칩 정의(`filter-bar` div)와 CSS 클래스(`event.공휴일`, `event.기념일` 등)도 함께 수정해야 합니다.

**Q. 비공개로 운영하고 싶어요.**
- Private 레포로 만들면 GitHub Pages는 GitHub Pro 또는 Enterprise 플랜이 필요합니다.
- 또는 Vercel, Cloudflare Pages 같은 서비스에 Private으로 배포하는 방법이 있습니다.

**Q. 더 이상 사용하지 않아요. 정리하려면?**
Notion → Integration 페이지에서 통합 삭제 (토큰 무효화) → GitHub 레포 삭제. 끝.

## 디버깅

Actions가 실패하면 **Actions** 탭의 실패한 실행을 클릭해서 로그 확인:
- `[ERROR] Notion API 401: ...` → 토큰 잘못됨 또는 통합이 DB에 연결 안 됨
- `[ERROR] Notion API 404: ...` → `NOTION_DATABASE_ID` 잘못됨
- 그 외 → 로그를 그대로 복사해서 문의

로컬에서 테스트하려면:
```bash
export NOTION_TOKEN=ntn_xxxxx
export NOTION_DATABASE_ID=277b81f4-483a-4d91-b0b9-6a371b1acc36
python scripts/sync_notion.py
cat data.json
```
