# agents/analyst.py
import json
from core.llm import call_llm, strip_thinking
from agents.scanner import run_github_scanner
from agents.dep_scanner import run_dep_scanner

# ── Blast radius analysis using Super ───────────────────────────

def run_analyst(scanner_results: list[dict] = None) -> dict:
    """
    Takes all scanner outputs and runs deep cross-signal analysis
    using Nemotron Super's large context window.
    
    If no results passed in, runs all scanners fresh.
    """
    print("\n🧠 Analyst Agent (Nemotron Super) starting...")

    # Run scanners if not provided
    if scanner_results is None:
        print("  → Running all scanners...")
        github_result = run_github_scanner()
        dep_result    = run_dep_scanner()
        scanner_results = [github_result, dep_result]

    # Build the full context payload
    context = ""
    for result in scanner_results:
        source = result.get("source", "unknown").upper()
        summary = result.get("summary", "No summary available.")
        raw = result.get("raw", result.get("vulnerable", []))
        context += f"\n\n=== {source} SCANNER ===\n"
        context += f"Summary:\n{summary}\n"
        context += f"Raw Data:\n{json.dumps(raw, indent=2)[:2000]}\n"  # cap at 2000 chars per source

    prompt = f"""
You are DriftWatch's Analyst Agent. You have received findings from multiple 
infrastructure scanners. Your job is to:

1. Identify COMPOUND RISKS — where two or more findings together create a 
   bigger problem than each one alone
2. Score each risk by BLAST RADIUS — how much of the system it could affect
3. Prioritize findings by urgency

Here are all scanner findings:
{context}

Respond in this EXACT format:

OVERALL_HEALTH_SCORE: [0-100, where 100 is perfect health]

COMPOUND_RISKS:
- RISK: <describe the compound risk>
  BLAST_RADIUS: [LOW|MEDIUM|HIGH|CRITICAL]
  COMPONENTS: <which scanners/findings are involved>
  URGENCY: [IMMEDIATE|THIS_WEEK|THIS_MONTH|MONITOR]

TOP_PRIORITY_ACTIONS:
1. <most urgent action>
2. <second most urgent action>  
3. <third most urgent action>

NARRATIVE:
<2-3 sentence plain English summary of the overall infrastructure health
that a non-technical stakeholder could understand>
"""

    print("  → Sending all findings to Nemotron Super for analysis...")
    response = call_llm(
        prompt=prompt,
        model="super",
        system="""You are DriftWatch's senior infrastructure analyst. 
You specialize in finding non-obvious compound risks across multiple signals.
Be precise, specific, and actionable. Never be vague.""",
        max_tokens=1024,
        temperature=0.1,
    )

    analysis = strip_thinking(response)

    # Extract health score from response
    health_score = 100
    for line in analysis.splitlines():
        if line.startswith("OVERALL_HEALTH_SCORE:"):
            try:
                health_score = int(line.split(":")[1].strip().split()[0])
            except Exception:
                pass

    return {
        "source":       "analyst",
        "health_score": health_score,
        "analysis":     analysis,
        "raw_inputs":   scanner_results,
    }


if __name__ == "__main__":
    result = run_analyst()
    print("\n=== Analyst Agent Results ===\n")
    print(f"Infrastructure Health Score: {result['health_score']}/100")
    print(f"\nFull Analysis:\n{result['analysis']}")