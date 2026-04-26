# CodexSearcher

Insight: 여러 AI 에이전트가 협업해서 **최근 Codex 관련 GitHub 레포지토리**를 탐색/분석/검토하고,
요구사항에 맞는 우선순위 레포지터리로 정리하는 프로젝트입니다.

## 목적

- **Agent 1(탐색)**: 최신/신규 GitHub 레포지토리 탐색
- **Agent 2(분석)**: 스타/활용성 기준으로 생산성/확장성/독립앱 잠재력 분석
- **Agent 3(검토)**: 탐색+분석 결과의 적합성 검토 및 실제 적용 제안 작성

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
2. Agent 2가 각 레포의 스타 수, 최신성, 활용성(생산성/독립앱 잠재력) 분석
3. Agent 3가 최종 유효성 평가 및 추천안 작성
4. 결과를 `reports/YYYY-MM-DD.md`에 **덮어쓰기 아님 누적**으로 저장

## 시작 보고서

첫 실행 결과는 `reports/2026-04-26.md`에 이미 반영되어 있으며,
향후 조사 때마다 `Date` 별로 업데이트 됩니다.