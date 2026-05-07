# j-rpi-solo 워크플로우 과정 - Research

> 작성일: 2026-04-26 | 요구사항: j-rpi-solo에서 워크플로우 과정으로 리서치md파일 생성

## 1. 요구사항 요약

`j-rpi-solo`는 Research → Plan → Implement → Test → Complete 전 과정을 마크다운 문서 기반으로 관리하는 Claude Code skill이다. 각 단계는 독립적인 서브커맨드(`--r`, `--p`, `--loop`, `--i`, `--ut`, `--e2e`, `--abt`, `--hotfix`, `--complete`)로 진입하며, 단계별 워크플로우 파일(`references/wf-*.md`)을 읽어 실행한다. 문서 자족성 원칙에 따라 `developerDocs/` 폴더에 생성된 `{name}-research.md`와 `{name}-plan.md`가 세션 재시작 이후에도 맥락을 완전히 복원할 수 있어야 한다. 대상 프로젝트는 Electron 3-프로세스(Main / Preload / Renderer) 아키텍처를 기반으로 한 kanban 앱이며, skill은 코드베이스와 독립적으로 동작한다.

---

## 2. 현황 분석

### 2.1 스킬 파일 구조

| 파일 | 역할 |
|------|------|
| `j-rpi-solo/SKILL.md` | 라우터: 서브커맨드 파싱 → 워크플로우 파일 Read → 실행 |
| `j-rpi-solo/README.md` | Quick Reference, 아키텍처 요약, FAQ |
| `j-rpi-solo/references/wf-research.md` | `--r` 워크플로우 절차 및 출력 형식 정의 |
| `j-rpi-solo/references/wf-plan.md` | `--p` 워크플로우 절차 및 출력 형식 정의 |
| `j-rpi-solo/references/wf-loop.md` | `--loop` 워크플로우: `=>` 메모 반영 |
| `j-rpi-solo/references/wf-implement.md` | `--i` 워크플로우: plan 기반 구현, worktree 분기 |
| `j-rpi-solo/references/wf-unit-test.md` | `--ut` 워크플로우: Vitest 기반 Main process 단위 테스트 |
| `j-rpi-solo/references/wf-e2e.md` | `--e2e` 워크플로우: Playwright Electron UI 통합 테스트 |
| `j-rpi-solo/references/wf-abt.md` | `--abt` 워크플로우: 탐색적 테스트 시나리오 실행 |
| `j-rpi-solo/references/wf-hotfix.md` | `--hotfix` 워크플로우: 오류 수정 + plan 기록 + 영향 분석 |
| `j-rpi-solo/references/wf-complete.md` | `--complete` 워크플로우: 완료 처리 + 아카이빙 |

### 2.2 SKILL.md 라우팅 메커니즘

```
/j-rpi-solo [서브커맨드] [요구사항]
       │
       ▼
1단계: 서브커맨드 파싱
       │
       ▼
2단계: 인수 없음 → developerDocs/ Glob → 활성 작업 테이블 표시 → AskUserQuestion
  또는
3단계: 서브커맨드 → wf-*.md Read → 실행

실행 모드 구분:
  - Opus 직접 실행: --r, --p, --loop, --hotfix --run, --complete
  - Sonnet Agent 위임: --i, --ut, --e2e, --abt, --hotfix
```

### 2.3 각 단계별 워크플로우 핵심

#### `--r` (Research)
- `developerDocs/` 존재 확인 → 없으면 생성
- 파일명: 요구사항 kebab-case 변환, `{name}-research.md`
- `developerDocs/archive/` 중복 검사 → suffix 부여
- 필수 조사 대상: `src/main/db/schema.ts`, `src/main/ipc/*.handler.ts`, `src/renderer/src/types/index.ts`, `src/renderer/src/store/`
- 출력: Research 문서 (요구사항 요약 / 현황 분석 / 발견사항 / 제약사항 / 결론)

#### `--p` (Plan)
- 직전 `*-research.md` 기반 또는 요구사항 직접 입력
- 동일 `{name}` prefix 공유 의무 (불일치 금지)
- 출력: Plan 문서 (목표 / 구현 범위 / 작업 단계 + 체크리스트 / 기술 결정 / 테스트 전략 / 검증 기준)
- 완료 안내: Worktree 격리(`claude -w`) 또는 현재 세션 구현 선택 제시

#### `--loop`
- `*-plan.md`에서 `=>` 마커 라인 탐색
- 메모 내용을 해당 섹션에 반영 후 `=>` 라인 제거
- `## Loop History` 테이블에 반영 이력 누적

#### `--i` (Implement)
- plan 로드 → 브랜치 분리 확인(Y/W/N)
- W 선택 시: `claude -w {name} -n "{name}" -p "/j-rpi-solo --i"` 안내 후 종료
- `any`/`unknown` 타입 금지, 단계별 typecheck 실행
- 독립 작업 ≥ 2이면 `Agent(isolation: "worktree")` 병렬 실행 제안
- 완료 후 테스트 전략(`## 5. 테스트 전략`) 기반 `--ut`/`--e2e` 실행 여부 확인

#### `--ut` (Unit Test)
- 대상: Main process (`src/main/db/*.repo.ts`, `src/main/services/*.ts`, `src/main/ipc/*.handler.ts`)
- 도구: Vitest + better-sqlite3 `:memory:`
- 실패 시 최대 3회 재실행 → 초과 시 skip + 사유 주석
- plan `## 테스트 현황 (Unit)` 섹션 갱신

#### `--e2e` (E2E Test)
- 대상: Renderer 컴포넌트 (`src/renderer/src/`)
- 도구: Playwright Electron (`_electron` API)
- locator 우선순위: `data-testid` > aria 역할 > 텍스트 (Tailwind 클래스 지양)
- 실패 시 최대 3회 → 초과 시 `test.skip()` + 사유 주석
- plan `## 테스트 현황 (E2E)` 섹션 갱신

#### `--abt` (Agent Browser Test)
- 탐색적 시나리오를 사용자에게 순차 제시 → P/F/S 입력 수집
- Fail 항목 → `--hotfix` 연계 안내
- 결과 파일: `developerDocs/abt-{name}-{YYYY-MM-DD}.md`

#### `--hotfix`
- 코드 수정 → plan `## 추가 구현 사항 (Hotfix)` 기록 → 영향 범위 안내
- `--hotfix --run`: 수정 파일 분석 → 영향받는 `--ut`/`--e2e` 자동 재실행

#### `--complete`
- diff 확인 → plan 외 변경사항 `## 추가 구현 사항 (plan 외)` 기록
- 보완 항목 추출 → 후속 plan 생성 여부 AskUserQuestion
- plan 상태 `Completed`로 갱신
- `developerDocs/archive/`로 `{name}-plan.md` + `{name}-research.md` 이동

### 2.4 프로젝트 핵심 참조 구조

```
Main process (src/main/)
  ├── db/schema.ts          → 테이블 정의 + 멱등 마이그레이션 (try/catch ALTER TABLE)
  ├── db/*.repo.ts          → better-sqlite3 동기 쿼리
  ├── ipc/*.handler.ts      → ipcMain.handle 등록
  └── services/
      └── claude.service.ts → Anthropic/Gemini/Groq AI 스트리밍

Preload (src/preload/index.ts)
  └── contextBridge         → window.electronAPI 노출

Renderer (src/renderer/src/)
  ├── types/index.ts        → ElectronAPI 인터페이스 (any/unknown 금지)
  ├── api/ipc.ts            → 타입 안전 IPC 래퍼
  ├── store/
  │   ├── boardStore        → 컬럼/카드 상태
  │   └── chatStore         → 채팅/AI 스트리밍 상태
  ├── components/           → React 컴포넌트 (.tsx)
  └── hooks/                → useBoard, useChat
```

IPC 채널 추가 시 반드시 4곳 동기화:
1. `src/main/ipc/*.handler.ts` → ipcMain.handle 등록
2. `src/preload/index.ts` → contextBridge 노출
3. `src/renderer/src/types/index.ts` → ElectronAPI 타입 추가
4. `src/renderer/src/api/ipc.ts` → 타입 안전 래퍼 추가

### 2.5 이전 작업 이력 (archive)

`developerDocs/archive/` — 현재 비어 있음 (첫 세션).

---

## 3. 핵심 발견사항

1. **라우터 패턴**: SKILL.md는 실행 로직을 직접 갖지 않고 wf-*.md를 Read 후 실행하는 순수 라우터이다. 새 단계 추가 시 wf 파일만 신규 작성하면 되어 확장성이 높다.

2. **문서 자족성이 핵심 원칙**: research와 plan 문서는 세션 재시작 후에도 다음 단계를 진행할 수 있는 완전한 맥락을 담아야 한다. 파일 경로, 함수명, IPC 채널명, DB 테이블명이 문서 내에 명시되어야 한다.

3. **실행 모델 이분화**: 설계·문서화 단계(--r, --p, --loop, --complete)는 Opus가 직접 처리하고, 구현·테스트 단계(--i, --ut, --e2e, --abt, --hotfix)는 Sonnet subagent에 위임한다. 역할 분리가 명확하다.

4. **Worktree 격리**: `--i` 단계에서 `claude -w {name}` 옵션으로 feature 브랜치를 격리된 worktree에서 구현할 수 있다. 구현 완료 후 `/merge-worktree`로 main에 squash-merge한다.

5. **테스트 2계층 분리**: Unit Test(Vitest, Main process)와 E2E Test(Playwright Electron, Renderer)가 명확히 분리되며, `--ut`와 `--e2e` 서브커맨드로 독립 실행된다.

6. **`=>` 메모 루프**: plan 파일에 `=>` 마커로 메모를 남기고 `--loop`로 반영하는 패턴은 세션 간 개발자-AI 협업의 핵심 메커니즘이다.

7. **아카이빙으로 히스토리 유지**: `--complete` 시 research + plan이 `archive/`로 이동되어 이후 `--r` 단계에서 참조 가능한 이전 작업 이력이 된다.

---

## 4. 제약사항 및 고려사항

- **IPC 통신**: `ipcMain.handle` / `ipcRenderer.invoke` 패턴 준수 (invoke-handle 짝 맞춤 필수)
- **DB**: better-sqlite3 동기 API만 사용, 마이그레이션은 `try/catch` 멱등 실행 (`ALTER TABLE ... ADD COLUMN`)
- **타입 안전성**: `any`/`unknown` 타입 금지, `ElectronAPI` 인터페이스 최신 유지
- **테스트 재시도 한계**: Unit/E2E 모두 실패 시 최대 3회, 초과 시 skip + 사유 주석 (무한 루프 방지)
- **파일 명명**: research와 plan은 반드시 동일 `{name}` prefix 공유, prefix 불일치 시 `--complete` 아카이빙 연동 오류 발생
- **Renderer locator**: Tailwind 클래스 기반 선택자 사용 금지 (빌드 환경에 따라 클래스명 변동 가능)
- **context 비대**: 단계 전환이나 context 과부하 시 skill이 자율적으로 `/compact` 판단

---

## 5. 결론

`j-rpi-solo`는 Electron kanban 앱 개발에 특화된 문서 기반 워크플로우 관리 체계이다. Research → Plan → Implement → Test → Complete의 전 단계가 `developerDocs/`의 마크다운 파일로 추적되어 세션 단절 없이 연속적으로 개발을 이어갈 수 있다.

새 기능 개발 시 권장 흐름:
```
/j-rpi-solo --r {요구사항}     # 현황 조사 + research.md 생성
/j-rpi-solo --p               # plan.md 생성
claude -w {name} -n "{name}" -p "/j-rpi-solo --i"  # worktree 격리 구현
/j-rpi-solo --ut              # Main process 단위 테스트
/j-rpi-solo --e2e             # Renderer E2E 테스트
/j-rpi-solo --abt             # 탐색적 테스트
/j-rpi-solo --complete        # 완료 + 아카이빙
```

각 단계에서 plan 파일의 체크리스트(`[ ]` → `[x]`)와 갱신일이 진행 상황을 실시간으로 반영하므로, 어느 세션에서나 `/j-rpi-solo` 단독 실행으로 현재 활성 작업 목록과 다음 단계를 즉시 파악할 수 있다.
