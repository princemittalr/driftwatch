# close_issues.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    "Accept": "application/vnd.github+json"
}

repo = os.getenv("GITHUB_REPO")

for issue_num in [1, 2]:
    r = requests.patch(
        f"https://api.github.com/repos/{repo}/issues/{issue_num}",
        headers=headers,
        json={"state": "closed"}
    )
    print(f"Issue #{issue_num}: {'Closed ✅' if r.status_code == 200 else f'Failed {r.status_code}'}")