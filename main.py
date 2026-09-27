# main.py — DriftWatch Master Orchestrator
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def run_driftwatch():
    print("=" * 60)
    print("  🌊 DriftWatch — Infrastructure Intelligence Agent")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── Phase 1: Run all scanners ────────────────────────────────
    print("\n📡 PHASE 1: Running Scanner Agents (Nemotron Nano)...")
    from agents.scanner import run_github_scanner
    from agents.dep_scanner import run_dep_scanner

    github_result = run_github_scanner()
    dep_result    = run_dep_scanner()
    scanner_results = [github_result, dep_result]

    print("\n✅ Scanner Phase Complete")
    print(f"   GitHub: {len(github_result['raw']['commits'])} commits, "
          f"{len(github_result['raw']['prs'])} PRs, "
          f"{len(github_result['raw']['stale_branches'])} stale branches")
    print(f"   CVEs:   {dep_result['total_vulns']} vulnerabilities found")

    # ── Phase 2: Analyst ─────────────────────────────────────────
    print("\n🧠 PHASE 2: Running Analyst Agent (Nemotron Super)...")
    from agents.analyst import run_analyst

    analyst_result = run_analyst(scanner_results=scanner_results)

    print(f"\n✅ Analyst Phase Complete")
    print(f"   Health Score: {analyst_result['health_score']}/100")

    # ── Phase 3: Strategist ──────────────────────────────────────
    print("\n🔮 PHASE 3: Running Strategist Agent (Nemotron Ultra)...")
    from agents.strategist import run_strategist

    strategist_result = run_strategist(analyst_result=analyst_result)

    print(f"\n✅ Strategist Phase Complete")
    if strategist_result["issues_created"]:
        print(f"   GitHub Issues Created: {len(strategist_result['issues_created'])}")
        for issue in strategist_result["issues_created"]:
            if issue.get("created"):
                print(f"   → #{issue['number']}: {issue['url']}")

    # ── Final Report ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  📊 DRIFTWATCH FINAL REPORT")
    print("=" * 60)
    print(f"\n  🏥 Infrastructure Health Score: "
          f"{analyst_result['health_score']}/100")
    print(f"\n  📧 Weekly Digest:")
    print(f"  {strategist_result['weekly_digest']}")
    print("\n" + "=" * 60)

    # ── Save report to JSON ──────────────────────────────────────
    report = {
        "timestamp":    datetime.now().isoformat(),
        "health_score": analyst_result["health_score"],
        "scanner_results": {
            "github":      github_result["summary"],
            "deps":        dep_result["summary"],
        },
        "analysis":       analyst_result["analysis"],
        "strategy":       strategist_result["strategy"],
        "weekly_digest":  strategist_result["weekly_digest"],
        "issues_created": strategist_result["issues_created"],
    }

    os.makedirs("reports", exist_ok=True)
    report_path = f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n  💾 Report saved to: {report_path}")
    print("=" * 60)

    return report


if __name__ == "__main__":
    run_driftwatch()