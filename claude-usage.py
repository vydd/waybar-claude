#!/usr/bin/env python3
"""Claude usage pie chart for waybar."""

import json
import math
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

CREDENTIALS_PATH = os.path.expanduser("~/.claude/.credentials.json")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITE_PATH = os.path.join(SCRIPT_DIR, "sprites.png")
API_URL = "https://api.anthropic.com/api/oauth/usage"

# Colors
GREEN = "#77dd77"
YELLOW = "#fdfd96"
ORANGE = "#ff8347"
RED = "#ff6961"
BG_COLOR = "#444"
STROKE_COLOR = "#666"

ICON_SIZE = 16
STEP = 5  # percentage steps (0, 5, 10, ... 100)


def get_token():
    with open(CREDENTIALS_PATH) as f:
        creds = json.load(f)
    for key in ("accessToken", "access_token", "token"):
        if key in creds:
            return creds[key]
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


def make_svg(pct, size=ICON_SIZE):
    """Generate SVG for a given percentage."""
    color = get_color(pct)
    cx, cy = size / 2, size / 2
    r = size / 2 - 1

    if pct >= 100:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>
</svg>'''

    if pct <= 0:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GREEN}" stroke-width="1"/>
</svg>'''

    angle = (pct / 100) * 2 * math.pi
    start_x, start_y = cx, cy - r
    end_x = cx + r * math.sin(angle)
    end_y = cy - r * math.cos(angle)
    large_arc = 1 if pct > 50 else 0

    return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{BG_COLOR}" stroke="{STROKE_COLOR}" stroke-width="0.5"/>
  <path d="M {cx},{cy} L {start_x},{start_y} A {r},{r} 0 {large_arc},1 {end_x},{end_y} Z" fill="{color}"/>
</svg>'''


def generate_sprites():
    """Generate sprite sheet PNG with icons for 0%, 5%, 10%, ... 100%."""
    import tempfile

    percentages = list(range(0, 101, STEP))
    num_icons = len(percentages)

    # Create individual SVG files
    svg_files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, pct in enumerate(percentages):
            svg_path = os.path.join(tmpdir, f"icon_{i:02d}.svg")
            with open(svg_path, "w") as f:
                f.write(make_svg(pct))
            svg_files.append(svg_path)

        # Use ImageMagick to combine into horizontal sprite sheet with transparency
        cmd = ["magick", "-background", "none"] + svg_files + ["+append", SPRITE_PATH]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except FileNotFoundError:
            # Try 'convert' for older ImageMagick
            cmd = ["convert", "-background", "none"] + svg_files + ["+append", SPRITE_PATH]
            subprocess.run(cmd, check=True, capture_output=True)

    print(f"Generated sprite sheet: {SPRITE_PATH}")
    print(f"  {num_icons} icons at {ICON_SIZE}x{ICON_SIZE}px each")
    print(f"  Total size: {num_icons * ICON_SIZE}x{ICON_SIZE}px")


def generate_css():
    """Print CSS rules for the sprite sheet."""
    percentages = list(range(0, 101, STEP))

    print(f"""#custom-claude {{
    background-image: url("{SPRITE_PATH}");
    background-repeat: no-repeat;
    background-size: {len(percentages) * ICON_SIZE}px {ICON_SIZE}px;
    min-width: {ICON_SIZE + 4}px;
    min-height: {ICON_SIZE}px;
}}
""")
    for i, pct in enumerate(percentages):
        offset = -i * ICON_SIZE
        print(f"#custom-claude.p{pct} {{ background-position: {offset}px 0; }}")


def main():
    try:
        token = get_token()
        usage = fetch_usage(token)
        pct = usage.get("five_hour", {}).get("utilization", 0)
        reset = usage.get("five_hour", {}).get("resets_at", "")

        # Round to nearest step for sprite selection
        sprite_pct = min(100, max(0, round(pct / STEP) * STEP))

        tooltip = f"5h: {pct:.0f}%"
        if reset:
            utc_time = datetime.fromisoformat(reset.replace('Z', '+00:00'))
            local_time = utc_time.astimezone()
            tooltip += f"\nResets: {local_time.strftime('%Y-%m-%d %H:%M')}"

        output = {
            "text": " ",
            "tooltip": tooltip,
            "class": f"p{sprite_pct}",
            "percentage": pct,
        }
        print(json.dumps(output))

    except Exception as e:
        print(json.dumps({"text": "?", "tooltip": str(e)}))
        sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--generate-sprites":
            generate_sprites()
        elif sys.argv[1] == "--generate-css":
            generate_css()
        elif sys.argv[1] == "--help":
            print("Usage: claude-usage.py [--generate-sprites | --generate-css | --help]")
            print("  (no args)          Fetch usage and output waybar JSON")
            print("  --generate-sprites Generate sprite sheet PNG")
            print("  --generate-css     Print CSS rules for sprite sheet")
        else:
            print(f"Unknown option: {sys.argv[1]}", file=sys.stderr)
            sys.exit(1)
    else:
        main()
