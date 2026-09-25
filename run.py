# run.py — use this to run any agent from root
import sys
import os

# Ensure project root is always in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.scanner import run_github_scanner
import json

if __name__ == "__main__":
    result = run_github_scanner()
    print("\n=== GitHub Scanner Results ===\n")
    print(f"Repo: {result['repo']}")
    print(f"\nRaw counts:")
    print(f"  Commits:        {len(result['raw']['commits'])}")
    print(f"  Open PRs:       {len(result['raw']['prs'])}")
    print(f"  Stale Branches: {len(result['raw']['stale_branches'])}")
    print(f"  Open Issues:    {len(result['raw']['issues'])}")
    print(f"\nNano Analysis:\n{result['summary']}")