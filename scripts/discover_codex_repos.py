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
    "usage",
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

# 독립형 앱 가능성 판별용 키워드
INDEPENDENT_APP_FORM_KEYWORDS = {
    "mobile",
    "ios",
    "android",
    "web",
    "ui",
    "gui",
    "app",
    "desktop",
    "electron",
    "tauri",
    "dashboard",
    "client",
}

INDEPENDENT_APP_MISSION_KEYWORDS = {
    "calendar",
    "planner",
    "habit",
    "journal",
    "memo",
    "study",
    "learning",
    "health",
    "fitness",
    "finance",
    "photo",
    "music",
    "family",
    "chat",
    "voice",
    "game",
}

NON_INDEPENDENT_APP_HINTS = {
    "plugin",
    "sdk",
    "library",
    "extension",
    "terminal",
    "shell",
    "command line",
    "protocol",
    "protocol",
    "parser",
}

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
    "malicious",
}

PURPOSE_RULES = [
    (["mobile", "ios", "android", "react native"], "모바일 앱"),
    (["desktop", "tauri", "electron", "app"], "데스크톱 앱"),
    (["web", "ui", "frontend", "gui", "cloudcli"], "웹 UI/대시보드"),
    (["orchestrat", "swarm", "multi-agent", "agent"], "에이전트 오케스트레이션"),
    (["plugin", "skills", "extension", "installer"], "플러그인/스킬 확장팩"),
    (["cli", "terminal", "shell", "command line"], "CLI/터미널 도구"),
    (["proxy", "gateway", "api", "route"], "API/프록시 게이트웨이"),
    (["dashboard", "bar", "stats", "usage", "monitor"], "사용량/모니터링 도구"),
    (["knowledge graph", "graph", "knowledge"], "지식 그래프/분석 도구"),
]

ROLE_HINTS = [
    (["usage", "stats", "monitor", "dashboard", "bar", "cost"], "사용량 추적/모니터링"),
    (["calendar", "planner", "todo", "task"], "일정/할 일 관리를 지원"),
    (["chat", "chatbot", "assistant", "voice"], "대화형 비서/요청 처리"),
    (["skill", "skills", "plugin", "extension"], "스킬/확장형 도구 생태계를 제공"),
    (["proxy", "gateway", "api", "route", "router"], "CLI/API 호출을 중계"),
    (["orchestrat", "swarm", "workflow", "multi-agent"], "복수 에이전트 작업을 자동 조정"),
    (["mobile", "desktop", "client", "gui", "web", "ui"], "즉시 실행 가능한 앱/클라이언트 UX를 제공"),
    (["graph", "knowledge", "knowledge graph"], "지식 연결 구조를 시각화"),
    (["security", "monitoring", "permission"], "보안 및 접근 제어 체계 강화"),
    (["music", "photo", "diary", "journal", "habit", "health", "finance", "travel", "family"], "생활 습관/창작/학습용 개인 작업 흐름에 적용"),
]


def run_gh_json(cmd: list[str]) -> dict:
    raw = subprocess.check_output(["gh", "api"] + cmd, text=True)
    return json.loads(raw)


def search_repos(query: str, limit: int) -> list[dict]:
    q = urllib.parse.quote(query)
    endpoint = f"/search/repositories?q={q}&sort=stars&order=desc&per_page={limit}"
    payload = run_gh_json([endpoint])
    return payload.get("items", [])


def _shorten(text: str, max_len: int = 130) -> str:
    t = (text or "-").strip()
    if len(t) <= max_len:
        return t
    return f"{t[: max_len - 1]}…"


def _cell(text: str) -> str:
    return (text or "-").replace("|", "/")


def _contains_any(text: str, keywords: set[str]) -> bool:
    return any(kw in text for kw in keywords)


def _score_keywords(text: str, keywords: set[str]) -> int:
    return sum(kw in text for kw in keywords)


def _infer_purpose(repo: dict) -> str:
    text = f"{repo['name']} {repo['description']} {' '.join(repo.get('topics') or [])}".lower()
    for words, label in PURPOSE_RULES:
        if _contains_any(text, set(words)):
            return label
    return "코덱스/AI 보조 도구"


def _infer_role_statement(repo: dict, desc: str) -> str:
    text = desc
    purpose = repo["purpose"]

    hints: list[str] = []
    for words, label in ROLE_HINTS:
        if _contains_any(text, set(words)):
            hints.append(label)

    if "코덱스/AI 보조 도구" in purpose and not hints:
        hints.append("AI 코덱스 워크플로우 실행/보조 기능 중심")

    # 중복 정리
    deduped: list[str] = []
    seen: set[str] = set()
    for h in hints:
        if h not in seen:
            seen.add(h)
            deduped.append(h)

    role_core = f"{purpose}. "
    if deduped:
        role_core += "핵심 기능은 " + ", ".join(deduped[:3]) + "."
    else:
        role_core += "프로젝트 설명으로 판단했을 때 실험·연계 워크플로우 보조 기능을 수행할 것으로 보입니다."

    return role_core


def _daily_fit_score(repo: dict, desc: str, life_score: int, prod_score: int) -> tuple[int, str, str]:
    score = 0
    reasons: list[str] = []

    if life_score >= 1:
        score += 2
        reasons.append("일상 키워드 다수")
    if _contains_any(desc, LIFESTYLE_BOOST_WORDS):
        score += 1
        reasons.append("생활 습관/관리 연관 용어")
    if _contains_any(desc, FREQUENT_DAILY_WORDS):
        score += 1
        reasons.append("일상 UX(채팅/음성/멀티미디어) 요소")
    if any(k in repo["purpose"].lower() for k in ["앱", "웹", "모바일"]):
        score += 1
        reasons.append("앱/웹 형태로 진입 장벽이 낮음")
    if prod_score >= 2:
        score += 1
        reasons.append("운영 자동화 결합성 있음")

    risk_hits = [k for k in RISK_KEYWORDS if k in desc]
    if risk_hits:
        score -= 1
        reasons.append("보안/오해 리스크 항목 있음")

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


def _independent_app_score(desc: str, purpose: str, life_score: int, prod_score: int) -> tuple[int, str, str]:
    score = 0
    reasons: list[str] = []

    # 앱/클라이언트성(독립 실행성)
    if _contains_any(desc, INDEPENDENT_APP_FORM_KEYWORDS):
        score += 2
        reasons.append("독립형 실행면이 있는 UI/앱 키워드")

    # 생활형/재미형 연계성
    if _contains_any(desc, INDEPENDENT_APP_MISSION_KEYWORDS):
        score += 1
        reasons.append("생활 루틴/개인 활동과 결합될 요소")

    # 제품성/업무성은 반대가 아닌 보강 요소
    if prod_score >= 1:
        score += 1
        reasons.append("업무 흐름과 연동 가능")
    if life_score >= 2:
        score += 1
        reasons.append("생활 활용성 관련 키워드 다수")

    # 목적상 앱 후보성
    if purpose in {"모바일 앱", "웹 UI/대시보드", "데스크톱 앱"}:
        score += 1
        reasons.append("목적 분류상 독립형 앱 형태")

    # 낮은 독립성 단서
    if _contains_any(desc, NON_INDEPENDENT_APP_HINTS):
        score -= 1
        reasons.append("플러그인/라이브러리 성격으로 독립앱성이 낮을 수 있음")

    score = max(0, min(5, score))
    if score >= 4:
        level = "독립형 우선"
    elif score >= 2:
        level = "조건부"
    else:
        level = "낮음"

    return score, level, "; ".join(reasons) if reasons else "추가 확인 필요"


def _daily_level_bucket(score: int) -> str:
    if score >= 4:
        return "PASS"
    if score >= 2:
        return "REVIEW"
    return "HOLD"


def normalize_repo(item: dict) -> dict:
    description = item.get("description") or ""
    normalized = {
        "name": item["full_name"],
        "stars": item["stargazers_count"],
        "description": description,
        "summary": _shorten(description, 140),
        "url": item["html_url"],
        "created": item["created_at"][:10],
        "updated": item["updated_at"][:10],
        "language": item.get("language") or "-",
        "topics": item.get("topics") or [],
        "open_issues": item.get("open_issues_count", 0),
    }

    normalized["purpose"] = _infer_purpose(normalized)
    normalized["role_statement"] = _infer_role_statement(normalized, (description or "").lower())
    return normalized


def _recommendation(
    repo: dict,
    tags: list[str],
    life_tags: list[str],
    pscore: int,
    iscore: int,
    lscore: int,
    indie_level: str,
) -> str:
    if "productivity" in tags and "daily-life" in life_tags:
        return "dual_priority"
    if "productivity" in tags:
        return "productivity"
    if indie_level in {"독립형 우선", "조건부"}:
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
        indie_score_level, indie_level, indie_reason = _independent_app_score(desc, r["purpose"], life_score, prod_score)

        if "독립형 우선" in indie_level or "조건부" in indie_level:
            r["is_indie_app_candidate"] = True
        else:
            r["is_indie_app_candidate"] = False

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
            "indie_app_score": indie_score_level,
            "indie_app_level": indie_level,
            "indie_app_reason": indie_reason,
            "recommendation": _recommendation(
                r,
                tags,
                life_tags,
                prod_score,
                indie_score,
                life_score,
                indie_level,
            ),
        }

        analyzed.append(analysis)
        buckets[status].append(analysis)

    return analyzed, buckets


def _fmt_list(
    items: list[dict],
    section: str,
    include_reason: bool = False,
    include_role: bool = False,
    include_url: bool = False,
) -> list[str]:
    lines: list[str] = []
    for r in items:
        parts = [
            f"**{r['name']}**",
            _cell(r['purpose']),
            f"stars={r['stars']:,}",
            f"prod={r['productivity_score']}, indie={r['indie_score']}",
            f"life={r['lifestyle_score']}",
            f"daily_fit={r['daily_fit_level']}({r['daily_fit_score']}/5)",
            f"indie-ready={r['indie_app_level']}({r['indie_app_score']}/5)",
            f"rec={r['recommendation']}",
        ]
        if include_reason:
            parts.append(f"reason={r['daily_fit_reason']}")
        if include_role:
            parts.append(f"role={_cell(_shorten(r['role_statement'], 140))}")
        if include_url:
            parts.append(f"url={r['url']}")
        lines.append("- " + ", ".join(parts))
    if not lines:
        lines.append(f"- (해당 없음, section={section})")
    return lines


def build_report(query: str, repos: list[dict], analyzed: list[dict], buckets: dict[str, list[dict]], outfile: Path) -> None:
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    ts = now.strftime("%H:%M:%S")

    lines: list[str] = []
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

    # Agent 1
    lines.extend([
        f"## 조사 세션 {ts}",
        f"- 조사 일시: {now.isoformat(timespec='seconds')}",
        f"- 검색 쿼리: `{query}`",
        f"- 수집 수: {len(repos)}",
        "",
        "### Agent 1. 탐색 결과",
        "",
        "| Repo | Stars | 프로젝트 역할(무엇/무슨 기능) | 독립앱 적합도 | 일상 적용성 | 생성일 | 갱신일 | URL |",
        "|---|---:|---|---|---|---|---|---|",
    ])

    for r in analyzed:
        fit = f"{r['daily_fit_level']}({r['daily_fit_score']}/5)"
        indie = f"{r['indie_app_level']}({r['indie_app_score']}/5)"
        lines.append(
            f"| {r['name']} | {r['stars']:,} | {_cell(_shorten(r['role_statement'], 140))} | {indie} | {fit} | {r['created']} | {r['updated']} | {r['url']} |"
        )

    # Agent 2
    lines.extend(["", "### Agent 2. 생산성 분석"])
    lines.extend(["#### PASS"])
    lines.extend(_fmt_list(buckets["pass"], "PASS", include_url=False, include_reason=False, include_role=True))
    lines.extend(["", "#### REVIEW"])
    lines.extend(_fmt_list(buckets["review"], "REVIEW", include_url=False, include_reason=False, include_role=True))
    lines.extend(["", "#### HOLD"])
    lines.extend(_fmt_list(buckets["hold"][:8], "HOLD", include_url=False, include_reason=False, include_role=True))

    # Agent 3 (생활형 + 독립앱 후보)
    daily_candidates = [
        r
        for r in analyzed
        if "daily-life" in r["lifestyle_tags"]
        or r["daily_fit_score"] >= 2
        or r["indie_app_level"] in {"독립형 우선", "조건부"}
    ]
    daily_candidates = sorted(
        daily_candidates,
        key=lambda x: (-(x["indie_app_score"]), -(x["daily_fit_score"]), -(x["stars"])),
    )

    indie_pass = [r for r in daily_candidates if r["indie_app_level"] == "독립형 우선" and r["daily_fit_level"] in {"높음", "보통"}]
    indie_review = [r for r in daily_candidates if r["indie_app_level"] in {"조건부", "독립형 우선"} and r not in indie_pass]
    indie_hold = [r for r in daily_candidates if r["indie_app_level"] == "낮음"]

    lines.extend(["", "### Agent 3. 일상 앱 스카우트"])
    lines.extend(["#### 독립형 앱 후보(PASS)"])
    if indie_pass:
        for r in indie_pass:
            lines.append(
                f"- **{r['name']}** | role={_cell(_shorten(r['role_statement'], 130))} | "
                f"indie-ready={r['indie_app_level']}({r['indie_app_score']}/5) | "
                f"daily_fit={r['daily_fit_level']}({r['daily_fit_score']}/5)"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 독립형 앱 후보(REVIEW)"])
    if indie_review:
        for r in indie_review[:12]:
            lines.append(
                f"- **{r['name']}** | role={_cell(_shorten(r['role_statement'], 130))} | "
                f"indie-ready={r['indie_app_level']}({r['indie_app_score']}/5) | "
                f"daily_fit={r['daily_fit_level']}({r['daily_fit_score']}/5)"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 생활형 HOLD 후보"])
    if indie_hold:
        for r in indie_hold[:12]:
            lines.append(
                f"- **{r['name']}** | role={_cell(_shorten(r['role_statement'], 130))} | "
                f"indie-ready={r['indie_app_level']}({r['indie_app_score']}/5) | "
                f"daily_fit={r['daily_fit_level']}({r['daily_fit_score']}/5)"
            )
    else:
        lines.append("- (해당 없음)")

    # Agent 4
    def _daily_app_final(r: dict) -> str:
        if r["indie_app_level"] == "독립형 우선" and r["daily_fit_level"] in {"높음", "보통"}:
            return "PASS"
        if r["indie_app_level"] in {"독립형 우선", "조건부"} or r["daily_fit_level"] in {"검토"}:
            return "REVIEW"
        return "HOLD"

    final_pass = [r for r in analyzed if _daily_app_final(r) == "PASS"]
    final_review = [r for r in analyzed if _daily_app_final(r) == "REVIEW"]
    final_hold = [r for r in analyzed if _daily_app_final(r) == "HOLD"]

    lines.extend(["", "### Agent 4. 최종 제안"])
    lines.extend([
        "- PASS 항목은 즉시 PoC 대상",
        "- REVIEW 항목은 보안/라이선스/운영조건 확인 후 단계적 적용",
        "- HOLD는 조건 미달(독립형 앱성/일상성 미흡)으로 모니터링",
        "- **중요**: 매 레포는 역할 문장 + 독립형 앱 적합도 + 일상 적용성으로 검토해 생활 적용 여부를 판단한다.",
        "",
        "#### PASS Top",
    ])

    if final_pass:
        for r in final_pass:
            lines.append(
                f"- **{r['name']}**: role={_cell(_shorten(r['role_statement'], 120))}, "
                f"stars={r['stars']:,}, 일상적용={r['daily_fit_level']}({r['daily_fit_score']}/5), "
                f"독립앱={r['indie_app_level']}({r['indie_app_score']}/5), 적용판단=바로사용 가능"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### REVIEW Top"])
    if final_review:
        for r in final_review[:12]:
            lines.append(
                f"- **{r['name']}**: role={_cell(_shorten(r['role_statement'], 100))}, "
                f"stars={r['stars']:,}, daily_fit={r['daily_fit_level']}({r['daily_fit_score']}/5), "
                f"독립앱={r['indie_app_level']}({r['indie_app_score']}/5), 조치=설정/보안 점검 후 적용"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### HOLD Top"])
    if final_hold:
        for r in final_hold[:12]:
            lines.append(
                f"- **{r['name']}**: role={_cell(_shorten(r['role_statement'], 100))}, "
                f"stars={r['stars']:,}, 독립앱={r['indie_app_level']}({r['indie_app_score']}/5), daily_fit={r['daily_fit_level']}({r['daily_fit_score']}/5), "
                f"사유={r['indie_app_reason']}"
            )
    else:
        lines.append("- (해당 없음)")

    lines.extend(["", "#### 일상앱 적용성 심사"])
    if final_pass:
        lines.append("- PASS(바로 생활 반영): " + ", ".join(f"{r['name']}({r['daily_fit_level']}/{r['indie_app_level']})" for r in final_pass[:10]))
    if final_review:
        lines.append("- REVIEW(조건부 반영): " + ", ".join(f"{r['name']}({r['daily_fit_level']}/{r['indie_app_level']})" for r in final_review[:10]))
    if final_hold:
        lines.append("- HOLD(현재 미반영): " + ", ".join(f"{r['name']}({r['daily_fit_level']}/{r['indie_app_level']})" for r in final_hold[:10]))

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

    outfile = Path(args.output) if args.output else (REPORTS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md")
    build_report(query, normalized, analyzed, buckets, outfile)

    print(f"Report generated: {outfile}")


if __name__ == "__main__":
    main()
