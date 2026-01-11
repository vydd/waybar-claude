# waybar-claude

A simple waybar module that displays your Claude Code usage as a pie chart.

![screenshot](screenshot.png)

Shows your 5-hour rolling window utilization with color-coded thresholds:
- **Green** (0-50%) - plenty of capacity
- **Yellow** (50-85%) - moderate usage
- **Orange** (85-100%) - approaching limit
- **Red** (100%) - limit reached

## Requirements

- Python 3 (no external dependencies)
- [Claude Code](https://claude.ai/claude-code) with OAuth credentials
- Waybar

## Installation

1. Clone this repo somewhere:
   ```bash
   git clone https://github.com/YOUR_USERNAME/waybar-claude.git ~/.local/share/waybar-claude
   ```

2. Add the module to your `~/.config/waybar/config`:
   ```json
   "modules-right": ["custom/claude", ...]
   ```

   And add the module definition:
   ```json
   "custom/claude": {
       "format": "{}",
       "return-type": "json",
       "interval": 60,
       "exec": "~/.local/share/waybar-claude/claude-usage.py"
   }
   ```

3. Add to your `~/.config/waybar/style.css`:
   ```css
   #custom-claude {
       background-image: url("/tmp/claude-usage.svg");
       background-repeat: no-repeat;
       background-position: center;
       background-size: 16px 16px;
       min-width: 20px;
       padding: 0 4px;
   }
   ```

4. Reload waybar:
   ```bash
   killall waybar && waybar &
   ```

## How it works

The script reads your OAuth token from `~/.claude/.credentials.json` (created by Claude Code) and queries the Anthropic API for your current usage. It generates an SVG pie chart at `/tmp/claude-usage.svg` which waybar displays via CSS.

Hover over the icon to see the exact percentage and reset time.

## Configuration

Edit `claude-usage.py` to customize:
- `SVG_PATH` - where the pie chart is saved
- Color values (`GREEN`, `YELLOW`, `ORANGE`, `RED`)
- Pie chart size (default 16px)

## License

MIT
