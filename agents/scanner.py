# agents/scanner.py
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from core.llm import call_llm, strip_thinking

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO")  # e.g. "owner/reponame"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

BASE = "https://api.github.com"

# ── Raw data fetchers ────────────────────────────────────────────

def get_recent_commits(limit: int = 10) -> list[dict]:
    url = f"{BASE}/repos/{GITHUB_REPO}/commits?per_page={limit}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    commits = []
    for c in r.json():
        commits.append({
            "sha":     c["sha"][:7],
            "message": c["commit"]["message"].split("\n")[0],
            "author":  c["commit"]["author"]["name"],
            "date":    c["commit"]["author"]["date"],
        })
    return commits


def get_open_prs() -> list[dict]:
    url = f"{BASE}/repos/{GITHUB_REPO}/pulls?state=open&per_page=10"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    prs = []
    for p in r.json():
        prs.append({
            "number":   p["number"],
            "title":    p["title"],
            "author":   p["user"]["login"],
            "created":  p["created_at"],
            "draft":    p["draft"],
        })
    return prs


def get_stale_branches(stale_days: int = 30) -> list[dict]:
    url = f"{BASE}/repos/{GITHUB_REPO}/branches?per_page=50"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    stale = []
    now = datetime.now(timezone.utc)
    for b in r.json():
        # get last commit date for each branch
        commit_url = b["commit"]["url"]
        cr = requests.get(commit_url, headers=HEADERS)
        if cr.status_code != 200:
            continue
        date_str = cr.json()["commit"]["author"]["date"]
        last_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        days_old = (now - last_date).days
        if days_old >= stale_days:
            stale.append({
                "branch":   b["name"],
                "days_old": days_old,
                "last_commit": date_str,
            })
    return stale


def get_open_issues(limit: int = 10) -> list[dict]:
    # GitHub PRs also show as issues, filter them out
    url = f"{BASE}/repos/{GITHUB_REPO}/issues?state=open&per_page={limit}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    issues = []
    for i in r.json():
        if "pull_request" in i:
            continue  # skip PRs
        issues.append({
            "number":  i["number"],
            "title":   i["title"],
            "created": i["created_at"],
            "labels":  [l["name"] for l in i["labels"]],
        })
    return issues


# ── Nano LLM summarizer ──────────────────────────────────────────

def summarize_github_findings(raw: dict) -> str:
    prompt = f"""
You are a GitHub repository health scanner.
Analyze the following raw GitHub data and return a concise structured summary
of potential risks, anomalies, or items needing attention.

Raw Data:
- Recent Commits: {raw['commits']}
- Open Pull Requests: {raw['prs']}
- Stale Branches (30+ days): {raw['stale_branches']}
- Open Issues: {raw['issues']}

Respond in this exact format:
RISK_LEVEL: [LOW|MEDIUM|HIGH]
KEY_FINDINGS:
- <finding 1>
- <finding 2>
- <finding 3>
RECOMMENDED_ACTIONS:
- <action 1>
- <action 2>
"""
    response = call_llm(
        prompt=prompt,
        model="nano",
        system="You are a GitHub repository health analysis agent. Be concise and precise.",
        max_tokens=512,
        temperature=0.1,
    )
    return strip_thinking(response)


# ── Main scanner entry point ─────────────────────────────────────

def run_github_scanner() -> dict:
    print(f"🔍 Scanning GitHub repo: {GITHUB_REPO}")
    
    print("  → Fetching commits...")
    commits = get_recent_commits()
    
    print("  → Fetching open PRs...")
    prs = get_open_prs()
    
    print("  → Fetching stale branches...")
    stale = get_stale_branches()
    
    print("  → Fetching open issues...")
    issues = get_open_issues()

    raw = {
        "commits":        commits,
        "prs":            prs,
        "stale_branches": stale,
        "issues":         issues,
    }

    print("  → Sending to Nano for analysis...")
    summary = summarize_github_findings(raw)

    return {
        "source":  "github",
        "repo":    GITHUB_REPO,
        "raw":     raw,
        "summary": summary,
    }


if __name__ == "__main__":
    import json
    result = run_github_scanner()
    print("\n=== GitHub Scanner Results ===\n")
    print(f"Repo: {result['repo']}")
    print(f"\nRaw counts:")
    print(f"  Commits: {len(result['raw']['commits'])}")
    print(f"  Open PRs: {len(result['raw']['prs'])}")
    print(f"  Stale Branches: {len(result['raw']['stale_branches'])}")
    print(f"  Open Issues: {len(result['raw']['issues'])}")
    print(f"\nNano Analysis:\n{result['summary']}")