from __future__ import annotations

import base64
import html
import json
import os
import re
import urllib.request
from pathlib import Path


def waka(path: str) -> dict[str, object]:
    key = os.environ["WAKATIME_API_KEY"]
    auth = base64.b64encode(f"{key}:".encode()).decode()
    request = urllib.request.Request(
        f"https://wakatime.com/api/v1/users/current/{path}",
        headers={"Authorization": f"Basic {auth}", "User-Agent": "profile-wakatime-dashboard"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    return result["data"]


def set_text(svg: str, element_id: str, value: str) -> str:
    pattern = rf'(<text[^>]*id="{re.escape(element_id)}"[^>]*>).*?(</text>)'
    updated, count = re.subn(pattern, rf"\g<1>{html.escape(value)}\g<2>", svg)
    if count != 1:
        raise RuntimeError(f"Expected one SVG text element named {element_id}, found {count}.")
    return updated


def set_width(svg: str, element_id: str, value: float) -> str:
    pattern = rf'(<rect[^>]*id="{re.escape(element_id)}"[^>]*\bwidth=")[^"]+("[^>]*/>)'
    updated, count = re.subn(pattern, rf"\g<1>{value:.1f}\g<2>", svg)
    if count != 1:
        raise RuntimeError(f"Expected one SVG bar named {element_id}, found {count}.")
    return updated


all_time = waka("all_time_since_today")
week = waka("stats/last_7_days")
languages = list(week.get("languages", []))[:4]
editors = list(week.get("editors", []))[:2]
if len(languages) < 4 or len(editors) < 2:
    raise RuntimeError("WakaTime returned insufficient dashboard data; keeping the current SVG unchanged.")

svg_file = Path("assets/svg/wakatime-dashboard.svg")
svg = svg_file.read_text(encoding="utf-8")
total_text = str(all_time.get("text") or all_time.get("human_readable_total") or "")
svg = set_text(svg, "total-time", total_text.replace(" hrs ", "h ").replace(" mins", "m"))
for index, item in enumerate(languages, 1):
    name, percent = str(item["name"]), float(item["percent"])
    if index <= 2:
        svg = set_text(svg, f"language-{index}-name", name)
        svg = set_text(svg, f"language-{index}-value", f"{percent:.2f}%")
        svg = set_width(svg, f"language-{index}-bar", 262 * percent / 100)
    else:
        svg = set_text(svg, f"language-{index}", f"{name} {percent:.2f}%")
for index, item in enumerate(editors, 1):
    name, percent = str(item["name"]), float(item["percent"])
    svg = set_text(svg, f"editor-{index}-name", name)
    svg = set_text(svg, f"editor-{index}-value", f"{percent:.2f}%")
    svg = set_width(svg, f"editor-{index}-bar", 249 * percent / 100)
svg_file.write_text(svg, encoding="utf-8", newline="\n")
