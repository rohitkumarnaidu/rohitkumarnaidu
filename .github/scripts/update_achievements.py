from __future__ import annotations

import html
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

USERNAME = "rohitkumarnaidu"
START = "<!--START_SECTION:achievements-->"
END = "<!--END_SECTION:achievements-->"
DESCRIPTIONS = {
    "Pull Shark": "Merged pull requests",
    "Quickdraw": "Closed an issue or pull request quickly",
    "YOLO": "Merged a pull request without a review",
    "Pair Extraordinaire": "Coauthored merged pull requests",
    "Galaxy Brain": "Provided accepted answers in Discussions",
    "Starstruck": "Created a repository that earned many stars",
    "Public Sponsor": "Sponsored open-source work",
    "Arctic Code Vault Contributor": "Contributed code preserved in the Arctic Code Vault",
}


class AchievementParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[dict[str, str]] = []
        self.last: dict[str, str] | None = None
        self.reading_tier = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        alt = values.get("alt") or ""
        classes = values.get("class") or ""
        if tag == "img" and alt.startswith("Achievement: "):
            self.last = {"name": alt.removeprefix("Achievement: "), "src": values.get("src") or "", "tier": "", "level": ""}
            self.items.append(self.last)
        elif tag == "span" and "achievement-tier-label" in classes:
            self.reading_tier = True
            if self.last:
                match = re.search(r"achievement-tier-label--([a-z]+)", classes)
                self.last["level"] = match.group(1).title() if match else ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "span":
            self.reading_tier = False

    def handle_data(self, data: str) -> None:
        if self.reading_tier and self.last and data.strip():
            self.last["tier"] = data.strip()


def fetch() -> list[dict[str, str]]:
    request = urllib.request.Request(
        f"https://github.com/{USERNAME}?tab=achievements",
        headers={"User-Agent": "Mozilla/5.0 GitHub-profile-achievement-updater"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")
    parser = AchievementParser()
    parser.feed(page)
    unique: dict[str, dict[str, str]] = {}
    for item in parser.items:
        if item["name"] not in unique or item["tier"]:
            unique[item["name"]] = item
    return list(unique.values())


def render(items: list[dict[str, str]]) -> str:
    if not items:
        raise RuntimeError("No public achievements found; keeping the current README unchanged.")
    cells = []
    for item in items:
        name = html.escape(item["name"])
        src = html.escape(item["src"], quote=True)
        tier = f" · {html.escape(item['tier'])}" if item["tier"] else ""
        level = f"{html.escape(item['level'])} tier · " if item["level"] else ""
        description = html.escape(DESCRIPTIONS.get(item["name"], "Official GitHub achievement"))
        cells.append(
            '<td align="center" width="220">\n'
            f'  <img src="{src}" width="92" alt="{name} achievement" /><br /><br />\n'
            f'  <b>{name}{tier}</b><br /><sub>{level}{description}</sub>\n</td>'
        )
    rows = ["<tr>\n" + "\n".join(cells[i:i + 3]) + "\n</tr>" for i in range(0, len(cells), 3)]
    return '<div align="center">\n<table>\n' + "\n".join(rows) + '\n</table>\n\n<sub>Automatically verified from the public GitHub achievements profile.</sub>\n</div>'


readme = Path("README.md")
content = readme.read_text(encoding="utf-8")
if content.count(START) != 1 or content.count(END) != 1:
    raise RuntimeError("Achievement markers are missing or duplicated.")
replacement = f"{START}\n{render(fetch())}\n{END}"
updated = re.sub(re.escape(START) + r".*?" + re.escape(END), replacement, content, flags=re.DOTALL)
readme.write_text(updated, encoding="utf-8", newline="\n")
