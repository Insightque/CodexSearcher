#!/usr/bin/env python3
"""CodexSearcher 핵심 오케스트레이션 스크립트.

- Agent 1: GitHub 레포지토리 탐색
- Agent 2: 스타/설명 기반 실효성 분석
- Agent 3: 최종 필터링 및 제안 작성
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
    "workflow",
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

INDIE_APP_KEYWORDS = {
    "mobile",
    "web",
    "desktop",
    "app",
    "ui",
    "client",
    "dashboard",
    "voice",
    "kanban",
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


def classify(label: str, text: str) -> int:
    t = text.lower()
    return sum(1 for kw in label.split() if kw.lower() in t)


def analyze(repos: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    analyzed: list[dict] = []
    buckets: defaultdict[str, list[dict]] = defaultdict(list)

    for r in repos:
        desc = (r["description"] or "").lower()
        prod_score = sum(kw in desc for kw in PRODUCTIVITY_KEYWORDS)
        indie_score = sum(kw in desc for kw in INDIE_APP_KEYWORDS)

        tags = []
        if prod_score >= 2:
            tags.append("productivity")
        if indie_score >= 1:
            tags.append("indie-app")

        status = "hold"
        if r["stars"] >= 10000 and tags:
            status = "pass"
        elif r["stars"] >= 5000 and (tags or r["stars"] >= 20000):
            status = "review"

        analysis = {
            **r,
            "productivity_score": prod_score,
            "indie_score": indie_score,
            "status": status,
            "tags": tags,
            "recommendation": _recommendation(r, tags, prod_score, indie_score),
        }
        analyzed.append(analysis)
        buckets[status].append(analysis)

    return analyzed, buckets


def _recommendation(repo: dict, tags: list[str], pscore: int, iscore: int) -> str:
    if "productivity" in tags and "indie-app" in tags:
        return "high_priority"
    if "productivity" in tags:
        return "productivity"
    if "indie-app" in tags:
        return "indie"
    if repo["stars"] >= 20000:
        return "watchlist"
    return "monitor"


def build_report(query: str, repos: list[dict], analyzed: list[dict], buckets: dict[str, list[dict]], outfile: Path) -> None:
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    ts = now.strftime("%H:%M:%S")

    lines = []
    if not outfile.exists():
        header = [
            f"# CodexSearcher 조사 보고서",
            "",
            f"- 생성일: {date}",
            "- 목적: 코덱스 관련 GitHub 레포지토리 3에이전트 협업 분석",
            "",
            "---",
        ]
        lines.extend(header)

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

    lines.extend(["", "### Agent 2. 분석 결과", "", "#### PASS"])
    for r in buckets["pass"]:
        lines.append(f"- **{r['name']}**: stars {r['stars']:,}, tag={','.join(r['tags']) or 'none'} => {r['recommendation']}")

    lines.extend(["", "#### REVIEW"])
    for r in buckets["review"]:
        lines.append(f"- **{r['name']}**: stars {r['stars']:,}, prod={r['productivity_score']}, indie={r['indie_score']}, rec={r['recommendation']}")

    lines.extend(["", "#### HOLD"])
    for r in buckets["hold"][:8]:
        lines.append(f"- **{r['name']}**: stars {r['stars']:,}, prod={r['productivity_score']}, indie={r['indie_score']}, rec={r['recommendation']}")

    lines.extend([
        "",
        "### Agent 3. 최종 제안",
        "- PASS 항목은 즉시 PoC 대상",
        "- REVIEW 항목은 보안/라이선스/운영조건 확인 후 단계적 적용",
        "- HOLD는 주기적 모니터링 대상",
        "---",
        "",
    ])

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
