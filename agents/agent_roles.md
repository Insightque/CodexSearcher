# CodexSearcher 에이전트 역할 정의

## 1) Discovery Agent (탐색 에이전트)

- 입력: 검색 조건(예: 키워드, 기간, 최소 스타), 최신성 우선순위
- 출력: 후보 레포지토리 원본 목록
  - `repo`, `stars`, `description`, `url`, `created`, `updated`
- 책임:
  - GitHub Search 기반으로 최신 Codex 관련 레포지토리 탐색
  - `created`, `updated`, `stargazers_count` 기준으로 정렬

## 2) Analysis Agent (분석 에이전트)

- 입력: Candidate list(Discovery Agent 결과)
- 출력: 분석 포인트
  - 활용성(개인 생산성 향상)
  - 독립형 앱 아이디어 요소(서비스/UX/자동화)
  - 기술 스택/운영 난이도/리스크
- 책임:
  - 스타 수, 설명 키워드 기반 가중치 분석
  - 실제 도입/사용 시나리오 제시

## 3) Validation Agent (검토/최종 제안 에이전트)

- 입력: 탐색+분석 결과
- 출력: 최종 후보 필터링 및 활용 제안 리포트
  - `pass` / `review` / `hold`
  - 왜 추천/보류인지 근거
  - 바로 적용 가능한 실험 계획
- 책임:
  - 첫번째/두번째 에이전트 결과가 사용자 요구(실사용성+재미/독립성)와 맞는지 판단
  - 실행 우선순위 제시

## 운영 방식

- `Orchestrator`는 사용자 요청마다 쿼리 조건을 갱신하고, 위 3개 역할 출력을 하나의 Markdown 레포트로 합칩니다.
- 모든 보고서 업데이트는 `reports/` 폴더에 날짜 기반 파일로 누적합니다.
- 민감 정보(토큰/키) 저장 금지.
