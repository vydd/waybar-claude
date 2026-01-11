#!/usr/bin/env python3
"""Claude usage pie chart for waybar."""

import json
import math
import os
import sys
import urllib.request

CREDENTIALS_PATH = os.path.expanduser("~/.claude/.credentials.json")
SVG_PATH = "/tmp/claude-usage.svg"
API_URL = "https://api.anthropic.com/api/oauth/usage"

# Pastel colors
GREEN = "#77dd77"
YELLOW = "#fdfd96"
ORANGE = "#ffb347"
RED = "#ff6961"

def get_token():
    with open(CREDENTIALS_PATH) as f:
        creds = json.load(f)
    # Try common key names
    for key in ("accessToken", "access_token", "token"):
        if key in creds:
            return creds[key]
    # Maybe it's nested
    if "claudeAiOauth" in creds:
        return creds["claudeAiOauth"].get("accessToken")
    raise KeyError(f"No token found in {CREDENTIALS_PATH}")

def fetch_usage(token):
    req = urllib.request.Request(API_URL, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)

def get_color(pct):
    if pct >= 100:
        return RED
    if pct >= 85:
        return ORANGE
    if pct >= 50:
        return YELLOW
    return GREEN

def make_svg(pct, size=16):
    color = get_color(pct)

    if pct >= 100:
        # Full red circle
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{size//2}" cy="{size//2}" r="{size//2 - 1}" fill="{color}"/>
</svg>'''

    if pct <= 0:
        # Empty circle (just outline)
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{size//2}" cy="{size//2}" r="{size//2 - 1}" fill="none" stroke="{GREEN}" stroke-width="1"/>
</svg>'''

    # Pie slice
    cx, cy = size // 2, size // 2
    r = size // 2 - 1
    angle = (pct / 100) * 2 * math.pi
    # Start at top (12 o'clock), go clockwise
    start_x, start_y = cx, cy - r
    end_x = cx + r * math.sin(angle)
    end_y = cy - r * math.cos(angle)
    large_arc = 1 if pct > 50 else 0

    return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="#444" stroke="#666" stroke-width="0.5"/>
  <path d="M {cx},{cy} L {start_x},{start_y} A {r},{r} 0 {large_arc},1 {end_x},{end_y} Z" fill="{color}"/>
</svg>'''

def main():
    try:
        token = get_token()
        usage = fetch_usage(token)
        pct = usage.get("five_hour", {}).get("utilization", 0)
        reset = usage.get("five_hour", {}).get("resets_at", "")

        svg = make_svg(pct)
        with open(SVG_PATH, "w") as f:
            f.write(svg)

        # Waybar JSON output
        tooltip = f"5h: {pct:.0f}%"
        if reset:
            tooltip += f"\nResets: {reset[:16].replace('T', ' ')}"

        # Determine class for CSS coloring
        if pct >= 100:
            css_class = "red"
        elif pct >= 85:
            css_class = "orange"
        elif pct >= 50:
            css_class = "yellow"
        else:
            css_class = "green"

        output = {
            "text": " ",  # non-breaking space so module renders
            "tooltip": tooltip,
            "class": css_class,
            "percentage": pct,
        }
        print(json.dumps(output))

    except Exception as e:
        print(json.dumps({"text": "?", "tooltip": str(e)}))
        sys.exit(0)

if __name__ == "__main__":
    main()
