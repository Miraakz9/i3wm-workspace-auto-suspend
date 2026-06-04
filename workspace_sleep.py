#!/usr/bin/env python3
# ~/.config/i3/workspace_sleep.py

import subprocess
import threading
import time
import json
import logging
from collections import defaultdict

# ── Configuration ────────────────────────────────────────────────────────────
SLEEP_AFTER_SECONDS = 30
CHECK_INTERVAL      = 10

MANAGED_APPS = {
    "tradingview":  "tradingview",
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

NEVER_SUSPEND = set()
LOG_FILE = "/tmp/workspace_sleep.log"
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

suspended     = set()
suspended_lock = threading.Lock()

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
    except Exception:
        return ""

def collect_classes(node, ws_name=None):
    result = defaultdict(set)
    if node.get("type") == "workspace":
        ws_name = node["name"]
    wp = node.get("window_properties")
    if wp and ws_name:
        cls = wp.get("class", "").lower()
        if cls:
            result[ws_name].add(cls)
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        for k, v in collect_classes(child, ws_name).items():
            result[k].update(v)
    return result

def get_state():
    try:
        tree = json.loads(run("i3-msg -t get_tree"))
        wss  = json.loads(run("i3-msg -t get_workspaces"))
    except Exception as e:
        logging.warning(f"get_state error: {e}")
        return None, {}
    active = next((w["name"] for w in wss if w.get("focused")), None)
    return active, collect_classes(tree)

def resume_app(pattern, cls):
    subprocess.run(["pkill", "-CONT", "-f", pattern], capture_output=True)
    logging.info(f"RESUMED:   {cls}")
    print(f"[sleep] RESUMED: {cls}")

def suspend_app(pattern, cls):
    r = subprocess.run(["pkill", "-STOP", "-f", pattern], capture_output=True)
    if r.returncode == 0:
        logging.info(f"SUSPENDED: {cls}")
        print(f"[sleep] SUSPENDED: {cls}")

def resume_classes_on_workspace(ws_node):
    """Instantly resume any suspended apps on the workspace we just switched to."""
    classes_on_ws = set()
    def walk(node):
        wp = node.get("window_properties")
        if wp:
            cls = wp.get("class", "").lower()
            if cls:
                classes_on_ws.add(cls)
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            walk(child)
    walk(ws_node)

    with suspended_lock:
        for cls in list(classes_on_ws):
            if cls in suspended and cls in MANAGED_APPS:
                resume_app(MANAGED_APPS[cls], cls)
                suspended.discard(cls)

def event_listener():
    """Subscribe to workspace focus events for instant resume on switch."""
    proc = subprocess.Popen(
        ["i3-msg", "-t", "subscribe", "-m", '["workspace"]'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    logging.info("Event listener started")

    for raw in proc.stdout:
        line = raw.decode().strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue

        if event.get("change") == "focus":
            current = event.get("current", {})
            # Instantly resume anything suspended on the workspace we just entered
            resume_classes_on_workspace(current)

def poll_loop():
    """Poll every CHECK_INTERVAL seconds to suspend inactive apps."""
    inactive_time = defaultdict(float)

    while True:
        time.sleep(CHECK_INTERVAL)
        active_ws, ws_classes = get_state()

        if active_ws is None:
            continue

        for cls, pattern in MANAGED_APPS.items():
            if pattern in NEVER_SUSPEND:
                continue

            app_ws = next((ws for ws, classes in ws_classes.items() if cls in classes), None)

            if app_ws is None:
                inactive_time[cls] = 0
                with suspended_lock:
                    suspended.discard(cls)
                continue

            if app_ws == active_ws:
                inactive_time[cls] = 0
                # Polling-based resume as fallback (event listener handles instant resume)
                with suspended_lock:
                    if cls in suspended:
                        resume_app(pattern, cls)
                        suspended.discard(cls)
            else:
                inactive_time[cls] += CHECK_INTERVAL
                with suspended_lock:
                    already = cls in suspended
                if not already and inactive_time[cls] >= SLEEP_AFTER_SECONDS:
                    suspend_app(pattern, cls)
                    with suspended_lock:
                        suspended.add(cls)

def main():
    logging.info("workspace_sleep started")
    print(f"[workspace_sleep] started — suspend after {SLEEP_AFTER_SECONDS}s, instant resume on switch")
    print(f"[workspace_sleep] log: {LOG_FILE}")

    # Event listener thread — instant resume on workspace switch
    t = threading.Thread(target=event_listener, daemon=True)
    t.start()

    # Polling loop — reliable suspend detection
    poll_loop()

if __name__ == "__main__":
    main()
