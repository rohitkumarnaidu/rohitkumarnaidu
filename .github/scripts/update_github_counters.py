from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

USERNAME = "rohitkumarnaidu"
START = "<!--START_SECTION:github-counters-->"
END = "<!--END_SECTION:github-counters-->"


def api(path: str) -> object:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-counter-updater"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def search(query: str, collect: bool = False) -> tuple[int, list[dict[str, object]]]:
    encoded = urllib.parse.quote(query)
    first = api(f"/search/issues?q={encoded}&per_page=100&page=1")
    assert isinstance(first, dict)
    total = int(first["total_count"])
    items = list(first["items"]) if collect else []
    if collect:
        for page in range(2, (min(total, 1000) + 99) // 100 + 1):
            result = api(f"/search/issues?q={encoded}&per_page=100&page={page}")
            assert isinstance(result, dict)
            items.extend(result["items"])
    return total, items


repos = api(f"/users/{USERNAME}/repos?type=owner&per_page=100")
assert isinstance(repos, list)
original_repositories = sum(not bool(repo["fork"]) for repo in repos)
public_prs, _ = search(f"type:pr author:{USERNAME}")
merged_prs, merged_items = search(f"type:pr author:{USERNAME} is:merged", collect=True)
external_merges = sum(
    item["repository_url"].split("/")[-2].lower() != USERNAME.lower()
    for item in merged_items
)

block = f"""{START}
![Original repositories](https://img.shields.io/badge/ORIGINAL_REPOSITORIES-{original_repositories}-7C3AED?style=for-the-badge&logo=github)
![Public PRs](https://img.shields.io/badge/PUBLIC_PULL_REQUESTS-{public_prs}-2563EB?style=for-the-badge&logo=github)
![Merged PRs](https://img.shields.io/badge/MERGED_PULL_REQUESTS-{merged_prs}-059669?style=for-the-badge&logo=git)
![External merges](https://img.shields.io/badge/EXTERNAL_MERGES-{external_merges}-0891B2?style=for-the-badge&logo=opensourceinitiative)
{END}"""

readme = Path("README.md")
content = readme.read_text(encoding="utf-8")
if content.count(START) != 1 or content.count(END) != 1:
    raise RuntimeError("GitHub counter markers are missing or duplicated.")
updated = re.sub(re.escape(START) + r".*?" + re.escape(END), block, content, flags=re.DOTALL)
readme.write_text(updated, encoding="utf-8", newline="\n")
