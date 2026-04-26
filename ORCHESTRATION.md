# CodexSearcher 오케스트레이션

## 실행 트리거
- 사용자 요청이 들어오면 동일한 질문인지, 기준 변경(쿼리/최신성/최소 스타/개수)인지 판별
- 변경이 있으면 스크립트 실행 파라미터를 갱신해 재조사

## 3단계 작업
1. **Agent-1 탐색**
   - `gh search`/`gh api /search/repositories`로 실시간 후보 수집
2. **Agent-2 분석**
   - 스타 수, 업데이트 주기, 설명 기반 태그 분석
3. **Agent-3 검토**
   - 사용자 요구 충족 여부(생산성/독립 앱 가치) 판별

## 추천 갱신 규칙
- 보고서는 `reports/YYYY-MM-DD.md` 형태로 새 파일 생성
- 과거 보고서는 삭제하지 않고 보존
- 핵심 출력 섹션은 항상 동일: `Agent 1`, `Agent 2`, `Agent 3`, `활용 제안`

## 빠른 실행 예시

```bash
cd /Users/insightque/CodexSearcher
python3 scripts/discover_codex_repos.py \
  --query "codex in:name in:description created:>2025-01-01" \
  --min-stars 100 \
  --limit 25
```
