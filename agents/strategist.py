# agents/strategist.py
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from core.llm import call_llm_with_history, strip_thinking
from agents.analyst import run_analyst

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ── GitHub Issue creator ─────────────────────────────────────────

def create_github_issue(title: str, body: str, labels: list[str] = None) -> dict:
    """Create a GitHub issue for a critical finding."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    payload = {
        "title":  f"[DriftWatch] {title}",
        "body":   body,
        "labels": labels or ["driftwatch", "infrastructure"]
    }
    r = requests.post(url, headers=HEADERS, json=payload)
    if r.status_code == 201:
        return {"created": True, "url": r.json()["html_url"], "number": r.json()["number"]}
    else:
        return {"created": False, "error": r.text}


def ensure_labels_exist():
    """Create DriftWatch labels in GitHub if they don't exist."""
    existing_url = f"https://api.github.com/repos/{GITHUB_REPO}/labels"
    existing = requests.get(existing_url, headers=HEADERS).json()
    existing_names = [l["name"] for l in existing if isinstance(l, dict)]

    labels_to_create = [
        {"name": "driftwatch",      "color": "0075ca", "description": "Created by DriftWatch agent"},
        {"name": "infrastructure",  "color": "e4e669", "description": "Infrastructure related"},
        {"name": "security",        "color": "d93f0b", "description": "Security vulnerability"},
        {"name": "high-priority",   "color": "b60205", "description": "Needs immediate attention"},
    ]

    for label in labels_to_create:
        if label["name"] not in existing_names:
            requests.post(existing_url, headers=HEADERS, json=label)


# ── Ultra strategist ─────────────────────────────────────────────

def run_strategist(analyst_result: dict = None) -> dict:
    """
    Takes analyst output and uses Nemotron Ultra to produce
    a long-horizon strategic action plan with effort/risk tradeoffs.
    """
    print("\n🔮 Strategist Agent (Nemotron Ultra) starting...")

    # Run analyst if not provided
    if analyst_result is None:
        analyst_result = run_analyst()

    health_score = analyst_result.get("health_score", 100)
    analysis     = analyst_result.get("analysis", "")
    timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Multi-turn conversation with Ultra for deeper reasoning
    messages = [
        {
            "role": "system",
            "content": """You are DriftWatch's Chief Infrastructure Strategist powered by Nemotron Ultra.
You take analyst findings and produce strategic, long-horizon action plans.
You think about effort vs impact tradeoffs, sequencing of fixes, and business risk.
Be specific, actionable, and prioritize ruthlessly."""
        },
        {
            "role": "user",
            "content": f"""Here is today's infrastructure analysis report:

Date: {timestamp}
Health Score: {health_score}/100

Analyst Findings:
{analysis}

Based on this, produce a strategic action plan in this EXACT format:

STRATEGIC_SUMMARY:
<2-3 sentences on the overall strategic situation>

ACTION_PLAN:
1. ACTION: <specific action>
   EFFORT: [LOW|MEDIUM|HIGH]
   IMPACT: [LOW|MEDIUM|HIGH]
   TIMELINE: <e.g. "Today", "This week", "This month">
   WHY: <one sentence on why this matters>

2. ACTION: <specific action>
   EFFORT: [LOW|MEDIUM|HIGH]
   IMPACT: [LOW|MEDIUM|HIGH]
   TIMELINE: <e.g. "Today", "This week", "This month">
   WHY: <one sentence on why this matters>

3. ACTION: <specific action>
   EFFORT: [LOW|MEDIUM|HIGH]
   IMPACT: [LOW|MEDIUM|HIGH]
   TIMELINE: <e.g. "Today", "This week", "This month">
   WHY: <one sentence on why this matters>

GITHUB_ISSUES_TO_CREATE:
- TITLE: <issue title>
  BODY: <issue body with context and steps>
  PRIORITY: [HIGH|CRITICAL]

WEEKLY_DIGEST:
<A 3-4 sentence plain English weekly digest that could be sent to a team 
via Slack or email. Include the health score, top risk, and top action.>"""
        }
    ]

    print("  → Sending to Nemotron Ultra for strategic planning...")
    response = call_llm_with_history(
        messages=messages,
        model="ultra",
        max_tokens=1500,
        temperature=0.2,
    )

    strategy = strip_thinking(response)

    # ── Auto-create GitHub Issues for critical findings ──────────
    print("  → Creating GitHub labels...")
    ensure_labels_exist()

    issues_created = []

    # Parse and create issues from strategy
    lines = strategy.splitlines()
    current_title = None
    current_body  = []
    in_issues     = False

    for line in lines:
        if "GITHUB_ISSUES_TO_CREATE:" in line:
            in_issues = True
            continue
        if "WEEKLY_DIGEST:" in line:
            in_issues = False
            # Save last issue if pending
            if current_title and current_body:
                result = create_github_issue(
                    title=current_title,
                    body="\n".join(current_body),
                    labels=["driftwatch", "high-priority"]
                )
                issues_created.append(result)
            break
        if in_issues:
            if line.strip().startswith("- TITLE:"):
                # Save previous issue if exists
                if current_title and current_body:
                    result = create_github_issue(
                        title=current_title,
                        body="\n".join(current_body),
                        labels=["driftwatch", "high-priority"]
                    )
                    issues_created.append(result)
                current_title = line.replace("- TITLE:", "").strip()
                current_body  = ["*Auto-created by DriftWatch Strategist Agent*\n"]
            elif line.strip().startswith("BODY:"):
                current_body.append(line.replace("BODY:", "").strip())
            elif line.strip().startswith("PRIORITY:"):
                priority = line.replace("PRIORITY:", "").strip()
                current_body.append(f"\n**Priority:** {priority}")

    if issues_created:
        print(f"  → Created {len(issues_created)} GitHub issue(s)")
    else:
        print("  → No critical issues to create")

    # Extract weekly digest
    weekly_digest = ""
    if "WEEKLY_DIGEST:" in strategy:
        weekly_digest = strategy.split("WEEKLY_DIGEST:")[-1].strip()

    return {
        "source":         "strategist",
        "health_score":   health_score,
        "strategy":       strategy,
        "weekly_digest":  weekly_digest,
        "issues_created": issues_created,
        "timestamp":      timestamp,
    }


if __name__ == "__main__":
    result = run_strategist()
    print("\n=== Strategist Agent Results ===\n")
    print(f"Health Score: {result['health_score']}/100")
    print(f"\nFull Strategy:\n{result['strategy']}")
    print(f"\n{'='*50}")
    print(f"📧 WEEKLY DIGEST:\n{result['weekly_digest']}")
    if result["issues_created"]:
        print(f"\n🐛 GitHub Issues Created:")
        for issue in result["issues_created"]:
            if issue.get("created"):
                print(f"  → #{issue['number']}: {issue['url']}")