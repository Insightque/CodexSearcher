# CodexSearcher

Insight: 여러 AI 에이전트가 협업해서 **최근 Codex 관련 GitHub 레포지토리**를 탐색/분석/검토하고,
요구사항에 맞는 우선순위 레포지터리로 정리하는 프로젝트입니다.

## 목적

- **Agent 1(탐색)**: 최신/신규 GitHub 레포지토리 탐색
- **Agent 2(분석)**: 생산성 중심 분석(업무형 활용성, 도입 효율성)
- **Agent 3(일상 앱 스카우트)**: 생활속에서 바로 쓰는 앱형 아이디어, 재미 요소, UX/습관 개선 포인트 탐색
- **Agent 4(검토)**: 탐색+분석(2,3) 결과 통합 검토 및 `pass/review/hold` 추천 확정

이후 요청이 들어오면(예: "다시 조사해줘") 같은 형태로 재실행해 `reports/`에 결과를 누적 업데이트합니다.

## 프로젝트 구조

- `reports/` : 조사 결과 레포트(월별/일별)
- `agents/` : 에이전트 역할/입력 출력 템플릿
- `scripts/` : 레포지토리 자동 수집/보고서 생성 스크립트
- `requirements.txt` : 스크립트 실행 의존성

## 사용 방법

```bash
cd /Users/insightque/CodexSearcher
python3 scripts/discover_codex_repos.py \
  --query "codex in:name in:description created:>2025-01-01" \
  --min-stars 100 \
  --limit 25
```

## 기본 동작

1. Agent 1이 GitHub Search로 최신 레포지토리 탐색
2. Agent 2가 각 레포의 스타 수, 최신성, 생산성 관점 활용성 분석
3. Agent 3이 일상 앱 후보를 별도 스캔(재미/습관/생활 접근성)
4. Agent 4가 2+3 결과를 합쳐 최종 유효성 평가 및 추천안 작성
   - 일상 앱 스카우트 항목은 바로 생활 적용 가능성까지 별도 점검
5. 결과를 `reports/YYYY-MM-DD.md`에 **덮어쓰기 아님 누적**으로 저장

## 리포트 구성 핵심

- 매 레포 항목은 링크 없이도 바로 이해할 수 있도록
  - `요약(레포 설명)`
  - `목적(무엇인지)`
  - `일상 적용성(1~5)`
  를 함께 보여줍니다.
- `Agent 4`는 일상앱 대상의 경우 `적용 가능성`, `진입 장벽`, `유지성` 기준으로 PASS/REVIEW/HOLD를 다시 검토해 기록합니다.

## 시작 보고서

첫 실행 결과는 `reports/2026-04-26.md`에 반영되어 있으며,
향후 조사 때마다 `Date` 별로 업데이트 됩니다.