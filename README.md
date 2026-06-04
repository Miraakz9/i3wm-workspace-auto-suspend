# Auto Suspend Inactive i3wm Workspace

Full power to active workspaces!

Automatically suspend inactive apps in [i3wm](https://i3wm.org/) to save CPU and battery. When you switch away from a workspace, apps on it are paused after a configurable timeout. When you switch back, they resume instantly.


![i3wm](https://img.shields.io/badge/i3wm-compatible-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.6+-yellow?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

---

## How it works

- Every 10 seconds, polls i3 for the active workspace and all window classes
- Apps on inactive workspaces have their idle time tracked
- After the timeout (default 5 minutes), sends `SIGSTOP` to pause the app
- **instant resume** the moment you switch back (`SIGCONT`)

```
Workspace 1: Firefox (active — never suspended)
Workspace 2: Telegram (inactive 5min → SIGSTOP → frozen)
                          ↓ switch back
                          SIGCONT → instantly resumed
```

---

## Requirements

- i3wm
- Python 3.6+
- `i3-msg` (ships with i3)

No pip packages needed.

---

## Installation

```bash
# Copy to your i3 config directory
cp workspace_sleep.py ~/.config/i3/workspace_sleep.py
chmod +x ~/.config/i3/workspace_sleep.py
```

Add to your i3 config (`~/.config/i3/config`) to auto-start on login:

```
exec --no-startup-id python3 ~/.config/i3/workspace_sleep.py
```

Reload i3:

```bash
i3-msg reload
```

Or run it manually:

```bash
python3 ~/.config/i3/workspace_sleep.py &
```

---

## Configuration

All settings are at the top of the script:

```python
# How long a workspace must be inactive before its apps are suspended (seconds)
SLEEP_AFTER_SECONDS = 300   # 5 minutes

# How often to check inactive times (seconds)
CHECK_INTERVAL = 10

# Apps to manage: window class (lowercase) → pkill pattern
MANAGED_APPS = {
    "firefox":      "firefox",
    "chromium":     "chromium",
    "google-chrome":"google-chrome",
    "code":         "code",
    "slack":        "slack",
    "discord":      "discord",
    "spotify":      "spotify",
    "obs":          "obs",
    "gimp":         "gimp",
    "inkscape":     "inkscape",
    "vlc":          "vlc",
    "mpv":          "mpv",
}

# Apps that should never be suspended even if listed above
NEVER_SUSPEND = set()   # e.g. {"spotify", "mpv"}
```

---

## Adding a new app

**Step 1** — Find the window class by running this and clicking on the app's window:

```bash
xprop | grep WM_CLASS
```

Output example:
```
WM_CLASS(STRING) = "telegram-desktop", "TelegramDesktop"
```

**Step 2** — Add it to `MANAGED_APPS` using the **second value lowercased** as the key and the **first value** as the pattern:

```python
"telegramdesktop": "telegram-desktop",
```

**Step 3** — Restart the script:

```bash
pkill -f workspace_sleep.py
python3 ~/.config/i3/workspace_sleep.py &
```

---

## Verifying it works

Watch the log in real time:

```bash
tail -f /tmp/workspace_sleep.log
```

Expected output after switching away from a workspace for 5 minutes:

```
2026-06-04 00:33:00 INFO workspace_sleep started
2026-06-04 00:38:00 INFO SUSPENDED: firefox (pattern: firefox)
2026-06-04 00:39:12 INFO RESUMED:   firefox
```

Check which processes are currently suspended:

```bash
ps aux | awk '$8=="T" {print "SUSPENDED:", $11, "PID:", $2}'
```

Confirm the script is running:

```bash
pgrep -a -f workspace_sleep.py
```

---

## Caveats

| App type | Behavior |
|---|---|
| **Audio/video players** | Will be silenced when suspended — add to `NEVER_SUSPEND` if needed |
| **Video calls** | May drop connection on `SIGSTOP` — add to `NEVER_SUSPEND` |
| **Terminals** | Any running jobs inside will also be paused — usually fine |
| **Electron apps** | Work well — TradingView, VS Code, Discord all tested |
| **Background apps** | Add to `NEVER_SUSPEND` to exclude them entirely |

---

## Troubleshooting

**App not being suspended**

Run this to confirm the script sees the app on its workspace:

```bash
i3-msg -t get_tree | python3 -c "
import json, sys
def walk(n):
    wp = n.get('window_properties')
    if wp:
        print(wp.get('class',''), '|', wp.get('instance',''))
    for c in n.get('nodes',[]) + n.get('floating_nodes',[]):
        walk(c)
walk(json.load(sys.stdin))
"
```

Make sure the class shown here matches the key in `MANAGED_APPS`.

**Multiple script instances running**

```bash
pkill -f workspace_sleep.py
python3 ~/.config/i3/workspace_sleep.py &
```

**App stays frozen after script is killed**

The script resumes all suspended apps on exit. If it was killed with `kill -9`, manually resume:

```bash
pkill -CONT -f <appname>
```

---

## License

MIT
