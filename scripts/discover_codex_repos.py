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

PURPOSE_RULES = [
    (["cli", "terminal", "command line", "shell"], "CLI/터미널 도구"),
    (["desktop", "tauri", "electron", "app"], "데스크톱 앱"),
    (["mobile", "ios", "android", "react native"], "모바일 앱"),
    (["web", "ui", "frontend", "gui", "cloudcli"], "웹 UI/대시보드"),
    (["orchestrat", "swarm", "multi-agent", "agent"], "에이전트 오케스트레이션"),
    (["plugin", "skills", "extension", "installer"], "플러그인/스킬 확장팩"),
    (["proxy", "gateway", "api", "gateway"], "API/프록시 게이트웨이"),
    (["dashboard", "bar", "stats", "usage", "monitor"], "사용량/모니터링 도구"),
    (["knowledge graph", "graph", "knowledge"], "지식 그래프/분석 도구"),
]

LIFESTYLE_BOOST_WORDS = {
    "calendar",
    "planner",
    "habit",
    "journal",
    "daily",
    "health",
    "finance",
    "budget",
    "photo",
    "music",
    "mood",
    "home",
    "family",
    "pet",
    "travel",
    "study",
    "learning",
    "recipe",
    "cooking",
    "memo",
}

FREQUENT_DAILY_WORDS = {
    "chat",
    "voice",
    "mobile",
    "app",
    "web",
    "photo",
    "music",
    "game",
    "gamification",
}

RISK_KEYWORDS = {
    "prompts",
    "prompt leak",
    "security",
    "hacks",
    "reverse engineer",
    "exploit",
}


def run_gh_json(cmd: list[str]) -> dict:
    raw = subprocess.check_output(["gh", "api"] + cmd, text=True)
    return json.loads(raw)


def search_repos(query: str, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    endpoint = f"/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
    payload = run_gh_json([endpoint])
    return payload.get("items", [])


def _shorten(text: str, max_len: int = 110) -> str:
    t = text.strip()
    if len(t) <= max_len:
        return t
    return f"{t[: max_len - 1]}…"


def _cell(text: str) -> str:
    return (text or "-").replace("|", "/")


def _score_keywords(text: str, keywords: set[str]) -> int:
    return sum(kw in text for kw in keywords)


def _infer_purpose(repo: dict) -> str:
    text = f"{repo['name']} {repo['description']} {' '.join(repo.get('topics') or [])}".lower()
    for words, label in PURPOSE_RULES:
        if any(w in text for w in words):
            return label
    return "코덱스/AI 보조 도구"


def _daily_fit_score(repo: dict, desc: str, life_score: int, prod_score: int) -> tuple[int, str, str]:
    score = 0
    reasons: list[str] = []

    if life_score >= 1:
        score += 2
        reasons.append("일상 키워드 다수")
    if any(w in desc for w in LIFESTYLE_BOOST_WORDS):
        score += 1
        reasons.append("생활 습관/관리 연관 용어")
    if any(w in desc for w in FREQUENT_DAILY_WORDS):
        score += 1
        reasons.append("일상 UI/채팅/멀티미디어 요소")
    if "app" in repo["purpose"].lower() or "모바일" in repo["purpose"].lower() or "웹" in repo["purpose"].lower():
        score += 1
        reasons.append("앱/웹 형태로 실사용 진입 장벽 낮음")
    if prod_score >= 2:
        score += 1
        reasons.append("운영 자동화 파이프라인과 결합 가능")

    risk_hits = [k for k in RISK_KEYWORDS if k in desc]
    if risk_hits:
        score -= 1
        reasons.append("보안/오해 소지 항목 존재")

    score = max(0, min(5, score))
    if score >= 4:
        level = "높음"
    elif score >= 3:
        level = "보통"
    elif score >= 2:
        level = "검토"
    else:
        level = "낮음"

    return score, level, "; ".join(reasons) if reasons else "추가 확인 필요"


def normalize_repo(item: dict) -> dict:
    description = item.get("description") or ""
    normalized = {
        "name": item["full_name"],
        "stars": item["stargazers_count"],
        "description": description,
        "summary": _shorten(description, 100),
        "url": item["html_url"],
        "created": item["created_at"][:10],
        "updated": item["updated_at"][:10],
        "language": item.get("language") or "-",
        "topics": item.get("topics") or [],
        "open_issues": item.get("open_issues_count", 0),
    }
    normalized["purpose"] = _infer_purpose(normalized)
    return normalized


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

        daily_fit_score, daily_fit_level, daily_fit_reason = _daily_fit_score(r, desc, life_score, prod_score)

        analysis = {
            **r,
            "productivity_score": prod_score,
            "indie_score": indie_score,
            "lifestyle_score": life_score,
            "status": status,
            "tags": tags,
            "lifestyle_tags": life_tags,
            "daily_fit_score": daily_fit_score,
            "daily_fit_level": daily_fit_level,
            "daily_fit_reason": daily_fit_reason,
            "recommendation": _recommendation(r, tags, life_tags, prod_score, indie_score, life_score),
        }
        analyzed.append(analysis)
        buckets[status].append(analysis)

    return analyzed, buckets


def _fmt_list(items: list[dict], section: str, include_url: bool = False) -> list[str]:
    lines: list[str] = []
    for r in items:
        line = (
            f"- **{r['name']}**: {r['purpose']} | stars={r['stars']:,}, "
            f"prod={r['productivity_score']}, indie={r['indie_score']}, life={r['lifestyle_score']}, "
            f"daily_fit={r['daily_fit_level']}({r['daily_fit_score']}/5), rec={r['recommendation']}"
        )
        if include_url:
            line += f", url={r['url']}"
        lines.append(line)
    if not lines:
        lines.append(f"- (해당 없음, section={section})")
    return lines


def _daily_level_bucket(score: int) -> str:
    if score >= 4:
        return "PASS"
    if score >= 2:
        return "REVIEW"
    return "HOLD"


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

    lines.extend([
        f"## 조사 세션 {ts}",
        f"- 조사 일시: {now.isoformat(timespec='seconds')}",
        f"- 검색 쿼리: `{query}`",
        f"- 수집 수: {len(repos)}",
        "",
        "### Agent 1. 탐색 결과",
        "",
        "| Repo | Stars | 요약(레포 설명) | 목적 | 일상 적용성 | 생성일 | 갱신일 | URL |",
        "|---|---:|---|---|---|---|---|---|",
    ])

    for r in analyzed:
        fit = f"{r['daily_fit_level']}({r['daily_fit_score']}/5)"
        lines.append(
            f"| {r['name']} | {r['stars']:,} | {_cell(_shorten(r['description'] or '-'))} | {_cell(r['purpose'])} | {fit} | {r['created']} | {r['updated']} | {r['url']} |"
        )

    # Agent 2: Productivity
    lines.extend(["", "### Agent 2. 생산성 분석"])
    lines.extend(["#### PASS"])
    lines.extend(_fmt_list(buckets["pass"], "PASS"))

    lines.extend(["", "#### REVIEW"])
    lines.extend(_fmt_list(buckets["review"], "REVIEW"))

    lines.extend(["", "#### HOLD"])
    lines.extend(_fmt_list(buckets["hold"][:8], "HOLD"))

    # Agent 3: Daily app scouting
    daily_candidates = [
        r
        for r in analyzed
        if "daily-life" in r["lifestyle_tags"] or r["daily_fit_score"] >= 2
    ]
    daily_candidates = sorted(daily_candidates, key=lambda x: (-(x["daily_fit_score"]), -(x["stars"])))

    daily_pass = [r for r in daily_candidates if _daily_level_bucket(r["daily_fit_score"]) == "PASS"]
    daily_review = [r for r in daily_candidates if _daily_level_bucket(r["daily_fit_score"]) == "REVIEW"]
    daily_hold = [r for r in daily_candidates if _daily_level_bucket(r["daily_fit_score"]) == "HOLD"]

    lines.extend(["", "### Agent 3. 일상 앱 스카우트"])
    lines.extend(["#### 생활형 PASS"])
    if daily_pass:
        for r in daily_pass:
            lines.append(
                f"- **{r['name']}**: {_cell(_shorten(r['description'] or '-', 130))} "
                f"| stars={r['stars']:,} | daily_fit={r['daily_fit_level']} | reason={r['daily_fit_reason']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 생활형 REVIEW"])
    if daily_review:
        for r in daily_review:
            lines.append(
                f"- **{r['name']}**: {_cell(_shorten(r['description'] or '-', 130))} "
                f"| stars={r['stars']:,} | daily_fit={r['daily_fit_level']} | reason={r['daily_fit_reason']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 생활형 HOLD"])
    if daily_hold:
        for r in daily_hold[:10]:
            lines.append(
                f"- **{r['name']}**: {_cell(_shorten(r['description'] or '-', 130))} "
                f"| stars={r['stars']:,} | daily_fit={r['daily_fit_level']} | reason={r['daily_fit_reason']}"
            )
    else:
        lines.append("- (해당 없음)")

    # Agent 4: Validation
    final_pass = [r for r in analyzed if r["status"] == "pass"]
    final_review = [r for r in analyzed if r["status"] == "review"]

    lines.extend(["", "### Agent 4. 최종 제안"])
    lines.extend([
        "- PASS 항목은 즉시 PoC 대상",
        "- REVIEW 항목은 보안/라이선스/운영조건 확인 후 단계적 적용",
        "- HOLD는 주기적 모니터링 대상",
        "- **중요**: 일상앱 스카우트 항목은 레포 설명 기준으로 아래 항목을 적용해 실제 생활 적용 가능성(직접 사용성, 진입 장벽, 재미/유지성)을 검토한다.",
        "",
        "#### PASS Top(검토 반영)",
    ])
    if final_pass:
        for r in final_pass:
            why = []
            if "productivity" in r["tags"]:
                why.append("업무 생산성")
            if "daily-life" in r["lifestyle_tags"]:
                why.append("일상 활용")
            if not why:
                why.append("범용 도구")
            lines.append(
                f"- **{r['name']}**: stars={r['stars']:,}, purpose={_cell(r['purpose'])}, "
                f"daily-fit={r['daily_fit_level']}({r['daily_fit_score']}/5), 적용판단={','.join(why)}, rec={r['recommendation']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### REVIEW Top"])
    if final_review:
        for r in final_review:
            lines.append(
                f"- **{r['name']}**: stars={r['stars']:,}, rec={r['recommendation']}, "
                f"daily-fit={r['daily_fit_level']}({r['daily_fit_score']}/5), reason={r['daily_fit_reason']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 일상앱 적용성 심사"])
    if daily_pass:
        lines.append("- PASS(생활 적용권장): " + ", ".join(f"{r['name']}({r['daily_fit_level']})" for r in daily_pass[:8]))
    if daily_review:
        lines.append("- REVIEW(조건부 적용): " + ", ".join(f"{r['name']}({r['daily_fit_level']})" for r in daily_review[:8]))
    if daily_hold:
        lines.append("- HOLD(현재는 미적합): " + ", ".join(f"{r['name']}({r['daily_fit_level']})" for r in daily_hold[:8]))

    lines.extend(["", "#### 일상앱 즉시 반영 후보"])
    if daily_pass:
        for r in daily_pass[:8]:
            lines.append(f"- **{r['name']}**: {r['url']} ({r['purpose']})")
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
