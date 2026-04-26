# CodexSearcher 오케스트레이션

## 실행 트리거
- 사용자 요청이 들어오면 동일한 질문인지, 기준 변경(쿼리/최신성/최소 스타/개수)인지 판별
- 변경이 있으면 스크립트 실행 파라미터를 갱신해 재조사

## 4단계 작업
1. **Agent-1 탐색**
   - `gh search`/`gh api /search/repositories`로 실시간 후보 수집
2. **Agent-2 분석(생산성)**
   - 스타 수, 업데이트 주기, 설명 기반 태그 분석
3. **Agent-3 일상앱 스카우트**
   - 일상/재미형 사용성 포인트, 생활형 UX, 적용 모멘텀 분석
4. **Agent-4 검토(최종)**
   - 2,3의 판단을 통합해 `pass/review/hold` 확정 및 최종 제안 작성
   - 일상앱 항목은 **직접 일상 적용 가능성(설명 기반 검토 + 사용 편의도 + 유지 난이도 + 재미 요소)**을 점수화해 PASS/REVIEW/HOLD로 재분류

## 추천 갱신 규칙
- 보고서는 `reports/YYYY-MM-DD.md` 형태로 새 파일 생성
- 과거 보고서는 삭제하지 않고 보존
- 핵심 출력 섹션은 항상 동일: `Agent 1`, `Agent 2`, `Agent 3`, `Agent 4`, `활용 제안`
- `Agent 1/3/4`는 사용자 요청이 일상형일 때 우선적으로 협업한다.
- 보고서에는 `pass/review/hold` 외에 **일상 앱 우선순위**를 남기고, 레포 이름만 봐도 무엇을 하는지 판단할 수 있게 **요약/목적/일상 적용성**을 함께 기록한다.
- 모든 보고서 업데이트는 `reports/` 폴더에 날짜 기반 파일로 누적한다.

## 빠른 실행 예시

```bash
cd /Users/insightque/CodexSearcher
python3 scripts/discover_codex_repos.py \
  --query "codex in:name in:description created:>2025-01-01" \
  --min-stars 100 \
  --limit 25
```