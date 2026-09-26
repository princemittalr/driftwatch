# agents/dep_scanner.py
import os
import re
import requests
from dotenv import load_dotenv
from core.llm import call_llm, strip_thinking

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = os.getenv("GITHUB_REPO")
OSV_API      = "https://api.osv.dev/v1/query"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ── Fetch requirements.txt from GitHub ──────────────────────────

def fetch_requirements_from_github() -> list[dict]:
    """Fetch and parse requirements.txt directly from the GitHub repo."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/requirements.txt"
    r = requests.get(url, headers=HEADERS)
    
    if r.status_code == 404:
        print("  ⚠️  No requirements.txt found in repo root.")
        return []
    
    r.raise_for_status()
    
    import base64
    content = base64.b64decode(r.json()["content"]).decode("utf-8")
    
    packages = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Parse "package==1.2.3" or "package>=1.2.3" or just "package"
        match = re.match(r"^([A-Za-z0-9_\-\.]+)[><=!~]*([0-9\.]*)", line)
        if match:
            name    = match.group(1)
            version = match.group(2) if match.group(2) else None
            packages.append({"name": name, "version": version})
    
    print(f"  → Found {len(packages)} packages in requirements.txt")
    return packages


# ── Check each package against OSV.dev ──────────────────────────

def check_osv(package_name: str, version: str = None) -> list[dict]:
    """Query OSV.dev for known vulnerabilities in a package."""
    payload = {
        "package": {
            "name":      package_name,
            "ecosystem": "PyPI"
        }
    }
    if version:
        payload["version"] = version
    
    try:
        r = requests.post(OSV_API, json=payload, timeout=10)
        if r.status_code != 200:
            return []
        vulns = r.json().get("vulns", [])
        results = []
        for v in vulns[:3]:  # cap at 3 per package
            results.append({
                "id":       v.get("id", "Unknown"),
                "summary":  v.get("summary", "No summary")[:120],
                "severity": v.get("database_specific", {}).get("severity", "UNKNOWN"),
                "published": v.get("published", "")[:10],
            })
        return results
    except Exception:
        return []


# ── Scan all packages ────────────────────────────────────────────

def scan_dependencies() -> list[dict]:
    """Scan all packages and return those with known CVEs."""
    packages = fetch_requirements_from_github()
    if not packages:
        return []
    
    vulnerable = []
    print(f"  → Checking {len(packages)} packages against OSV.dev CVE database...")
    
    for pkg in packages:
        vulns = check_osv(pkg["name"], pkg["version"])
        if vulns:
            vulnerable.append({
                "package":         pkg["name"],
                "version":         pkg["version"],
                "vulnerabilities": vulns,
            })
    
    print(f"  → Found {len(vulnerable)} packages with known CVEs")
    return vulnerable


# ── Nano LLM summarizer ──────────────────────────────────────────

def summarize_cve_findings(vulnerable: list[dict]) -> str:
    if not vulnerable:
        return "RISK_LEVEL: LOW\nKEY_FINDINGS:\n- No known CVEs found in dependencies.\nRECOMMENDED_ACTIONS:\n- Continue monitoring regularly."
    
    prompt = f"""
You are a dependency security scanner agent.
Analyze these vulnerable Python packages and summarize the security risk.

Vulnerable Packages Found:
{vulnerable}

Respond in this exact format:
RISK_LEVEL: [LOW|MEDIUM|HIGH|CRITICAL]
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
        system="You are a security vulnerability analysis agent. Be concise and precise.",
        max_tokens=512,
        temperature=0.1,
    )
    return strip_thinking(response)


# ── Main entry point ─────────────────────────────────────────────

def run_dep_scanner() -> dict:
    print(f"🔍 Scanning dependencies for: {GITHUB_REPO}")
    
    vulnerable = scan_dependencies()
    summary    = summarize_cve_findings(vulnerable)
    
    return {
        "source":      "dependencies",
        "repo":        GITHUB_REPO,
        "vulnerable":  vulnerable,
        "total_vulns": sum(len(p["vulnerabilities"]) for p in vulnerable),
        "summary":     summary,
    }


if __name__ == "__main__":
    result = run_dep_scanner()
    print("\n=== Dependency CVE Scanner Results ===\n")
    print(f"Packages with CVEs: {len(result['vulnerable'])}")
    print(f"Total CVEs found:   {result['total_vulns']}")
    print(f"\nNano Analysis:\n{result['summary']}")