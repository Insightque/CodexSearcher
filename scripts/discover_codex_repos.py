#!/usr/bin/env python3
"""CodexSearcher 핵심 오케스트레이션 스크립트.

- Agent 1: GitHub 레포지토리 탐색
- Agent 2: 생산성 중심 분석
- Agent 3: 일상 앱 스카우트
- Agent 4: 최종 검토
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.parse
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

PRODUCTIVITY_KEYWORDS = {
    "cli",
    "dashboard",
    "plugin",
    "agent",
    "orchestrat",
    "workflow",
    "integration",
    "switch",
    "skill",
    "manager",
    "task",
    "kanban",
    "cowork",
    "productivity",
    "management",
    "monitor",
    "automation",
}

LIFESTYLE_APP_KEYWORDS = {
    "daily",
    "habit",
    "journal",
    "diary",
    "planner",
    "finance",
    "budget",
    "health",
    "fitness",
    "exercise",
    "music",
    "photo",
    "album",
    "recipe",
    "cooking",
    "travel",
    "pet",
    "home",
    "family",
    "learning",
    "study",
    "chat",
    "voice",
    "game",
    "gamification",
    "mood",
    "weather",
    "calendar",
    "memo",
}

INDIE_APP_KEYWORDS = {
    "mobile",
    "web",
    "desktop",
    "app",
    "ui",
    "client",
    "voice",
    "chat",
    "knowledge graph",
    "graph",
}


def run_gh_json(cmd: list[str]) -> dict:
    raw = subprocess.check_output(["gh", "api"] + cmd, text=True)
    return json.loads(raw)


def search_repos(query: str, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    endpoint = f"/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
    payload = run_gh_json([endpoint])
    return payload.get("items", [])


def normalize_repo(item: dict) -> dict:
    return {
        "name": item["full_name"],
        "stars": item["stargazers_count"],
        "description": item.get("description") or "",
        "url": item["html_url"],
        "created": item["created_at"][:10],
        "updated": item["updated_at"][:10],
        "language": item.get("language") or "-",
        "topics": item.get("topics") or [],
        "open_issues": item.get("open_issues_count", 0),
    }


def _score_keywords(text: str, keywords: set[str]) -> int:
    return sum(kw in text for kw in keywords)


def analyze(repos: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    analyzed: list[dict] = []
    buckets: defaultdict[str, list[dict]] = defaultdict(list)

    for r in repos:
        desc = (r["description"] or "").lower()

        prod_score = _score_keywords(desc, PRODUCTIVITY_KEYWORDS)
        indie_score = _score_keywords(desc, INDIE_APP_KEYWORDS)
        life_score = _score_keywords(desc, LIFESTYLE_APP_KEYWORDS)

        tags = []
        life_tags = []

        if prod_score >= 2:
            tags.append("productivity")
        if indie_score >= 1:
            tags.append("indie-app")
        if life_score >= 2:
            life_tags.append("daily-life")

        status = "hold"
        if r["stars"] >= 10000 and (tags or life_tags):
            status = "pass"
        elif r["stars"] >= 5000 and (tags or life_tags or r["stars"] >= 20000):
            status = "review"

        analysis = {
            **r,
            "productivity_score": prod_score,
            "indie_score": indie_score,
            "lifestyle_score": life_score,
            "status": status,
            "tags": tags,
            "lifestyle_tags": life_tags,
            "recommendation": _recommendation(r, tags, life_tags, prod_score, indie_score, life_score),
        }
        analyzed.append(analysis)
        buckets[status].append(analysis)

    return analyzed, buckets


def _recommendation(
    repo: dict,
    tags: list[str],
    life_tags: list[str],
    pscore: int,
    iscore: int,
    lscore: int,
) -> str:
    if "productivity" in tags and "daily-life" in life_tags:
        return "dual_priority"
    if "productivity" in tags:
        return "productivity"
    if "daily-life" in life_tags:
        return "daily_app"
    if "indie-app" in tags:
        return "indie"
    if repo["stars"] >= 20000:
        return "watchlist"
    if lscore >= 1:
        return "interesting_lifestyle"
    return "monitor"


def _fmt_list(items: list[dict], section: str) -> list[str]:
    lines: list[str] = []
    for r in items:
        lines.append(
            f"- **{r['name']}**: stars {r['stars']:,}, "
            f"prod={r['productivity_score']}, indie={r['indie_score']}, "
            f"life={r['lifestyle_score']}, rec={r['recommendation']} ({section})"
        )
    if not lines:
        lines.append("- (해당 없음)")
    return lines


def build_report(query: str, repos: list[dict], analyzed: list[dict], buckets: dict[str, list[dict]], outfile: Path) -> None:
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    ts = now.strftime("%H:%M:%S")

    lines = []
    if not outfile.exists():
        header = [
            "# CodexSearcher 조사 보고서",
            "",
            f"- 생성일: {date}",
            "- 목적: 코덱스 관련 GitHub 레포지토리 4에이전트 협업 분석",
            "",
            "---",
        ]
        lines.extend(header)

    # Agent 1: Discovery
    lines.extend([
        f"## 조사 세션 {ts}",
        f"- 조사 일시: {now.isoformat(timespec='seconds')}",
        f"- 검색 쿼리: `{query}`",
        f"- 수집 수: {len(repos)}",
        "",
        "### Agent 1. 탐색 결과",
        "",
        "| Repo | Stars | Description | URL | Created | Updated |",
        "|---|---:|---|---|---|---|",
    ])

    for r in repos:
        desc = (r["description"] or "-").replace("|", "/")
        lines.append(f"| {r['name']} | {r['stars']:,} | {desc} | {r['url']} | {r['created']} | {r['updated']} |")

    # Agent 2: Productivity
    lines.extend(["", "### Agent 2. 생산성 분석"])
    lines.extend(["#### PASS"])
    lines.extend(_fmt_list(buckets["pass"], "productivity"))

    lines.extend(["", "#### REVIEW"])
    lines.extend(_fmt_list(buckets["review"], "productivity"))

    lines.extend(["", "#### HOLD"])
    lines.extend(_fmt_list(buckets["hold"][:8], "productivity"))

    # Agent 3: Daily app scouting
    daily_pass = [r for r in analyzed if "daily-life" in r["lifestyle_tags"] and r["status"] in {"pass", "review"}]
    daily_hold = [r for r in analyzed if "daily-life" in r["lifestyle_tags"] and r["status"] == "hold"]
    daily_pass = sorted(daily_pass, key=lambda x: (-(x["lifestyle_score"]), -x["stars"]))
    daily_hold = sorted(daily_hold, key=lambda x: (-(x["lifestyle_score"]), -x["stars"]))

    lines.extend(["", "### Agent 3. 일상 앱 스카우트"])
    lines.extend(["#### 생활형 PASS"])
    if daily_pass:
        for r in daily_pass:
            lines.append(
                f"- **{r['name']}**: stars {r['stars']:,}, "
                f"lifestyle_score {r['lifestyle_score']}, rec={r['recommendation']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 생활형 REVIEW/HOLD 후보"])
    if daily_hold:
        for r in daily_hold[:8]:
            lines.append(
                f"- **{r['name']}**: stars {r['stars']:,}, "
                f"lifestyle_score {r['lifestyle_score']}, rec={r['recommendation']}"
            )
    else:
        lines.append("- (해당 없음)")

    # Agent 4: Validation
    final_pass = [r for r in analyzed if r["status"] == "pass"]
    final_review = [r for r in analyzed if r["status"] == "review"]
    daily_influence = [r for r in final_pass if "daily-life" in r["lifestyle_tags"]]

    lines.extend(["", "### Agent 4. 최종 제안"])
    lines.extend([
        "- PASS 항목은 즉시 PoC 대상",
        "- REVIEW 항목은 보안/라이선스/운영조건 확인 후 단계적 적용",
        "- HOLD는 주기적 모니터링 대상",
        "",
        "#### PASS Top",
    ])
    if final_pass:
        for r in final_pass:
            score_str = []
            if "productivity" in r["tags"]:
                score_str.append("prod")
            if "daily-life" in r["lifestyle_tags"]:
                score_str.append("daily")
            if not score_str:
                score_str.append("review-lifestyle blend")
            lines.append(
                f"- **{r['name']}**: stars {r['stars']:,}, "
                f"reason={','.join(score_str)}, rec={r['recommendation']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### REVIEW Top"])
    if final_review:
        for r in final_review:
            lines.append(
                f"- **{r['name']}**: stars {r['stars']:,}, rec={r['recommendation']}, "
                f"daily-life={r['lifestyle_score']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 일상앱 즉시 반영 후보"])
    if daily_influence:
        for r in daily_influence:
            lines.append(f"- **{r['name']}**: {r['url']}")
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "---", ""])

    existing = outfile.read_text(encoding="utf-8") if outfile.exists() else ""
    mode = "w" if not existing else "a"
    with outfile.open(mode, encoding="utf-8") as f:
        if mode == "w":
            f.write("\n".join(lines) + "\n")
        else:
            if not existing.endswith("\n"):
                f.write("\n")
            f.write("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="codex in:name in:description")
    parser.add_argument("--min-stars", type=int, default=100)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query = f"{args.query} stars:>{args.min_stars}"

    raw = search_repos(query, args.limit)
    normalized = [normalize_repo(item) for item in raw]

    analyzed, buckets = analyze(normalized)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    outfile = (
        Path(args.output)
        if args.output
        else (REPORTS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md")
    )
    build_report(query, normalized, analyzed, buckets, outfile)

    print(f"Report generated: {outfile}")


if __name__ == "__main__":
    main()
