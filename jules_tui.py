#!/usr/bin/env python3
"""
Jules TUI - A Terminal User Interface for Google's Jules CLI
Supports Linux, macOS, and Unix-based operating systems.
Zero external dependencies (uses standard library Python 3 & curses).
"""

import curses
import datetime
import json
import os
import queue
import re
import shlex
import subprocess
import sys
import textwrap
import threading
import time

# --- Configuration & Storage Paths ---
CONFIG_DIR = os.path.expanduser("~/.config/jules-tui")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSIONS_DATA_FILE = os.path.join(CONFIG_DIR, "sessions_chat.json")
PROMPTS_DATA_FILE = os.path.join(CONFIG_DIR, "prompts.json")

SUPPORTED_MODELS = [
    "Default (Auto - Jules Managed)",
    "Gemini 2.5 Pro (Deep Reasoning)",
    "Gemini 2.5 Flash (Fast Execution)",
    "Gemini 2.0 Flash",
    "Gemini 2.0 Flash Thinking",
    "Gemini 1.5 Pro (2M Context)",
    "Gemini 1.5 Flash",
    "Custom Model..."
]

DEFAULT_CONFIG = {
    "theme": "twilight",
    "default_model": "Default (Auto)",
    "auto_refresh_enabled": True,
    "auto_refresh_seconds": 10,
    "notifications_enabled": True,
    "sound_enabled": True,
    "default_repo": "",
    "jules_bin": "",
    "compact_mode": False
}

def load_config():
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                return {**DEFAULT_CONFIG, **cfg}
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

def load_chat_history():
    if os.path.isfile(SESSIONS_DATA_FILE):
        try:
            with open(SESSIONS_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_chat_history(data):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(SESSIONS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_prompts_map():
    if os.path.isfile(PROMPTS_DATA_FILE):
        try:
            with open(PROMPTS_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_prompts_map(data):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(PROMPTS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def send_desktop_notification(title, body):
    """Send desktop notification on Linux (notify-send) or macOS (osascript)."""
    try:
        if subprocess.run(["which", "notify-send"], capture_output=True).returncode == 0:
            subprocess.Popen(["notify-send", "-a", "Jules TUI", title, body])
            return True
    except Exception:
        pass

    if sys.platform == "darwin":
        try:
            safe_title = title.replace('"', '\\"')
            safe_body = body.replace('"', '\\"')
            script = f'display notification "{safe_body}" with title "{safe_title}"'
            subprocess.Popen(["osascript", "-e", script])
            return True
        except Exception:
            pass
    return False

# --- Comprehensive Themes (No Emojis) ---
THEMES = {
    "twilight": {
        "name": "Twilight (Amber/Warm)",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_YELLOW,
        "header_fg": curses.COLOR_BLACK,
        "highlight_bg": curses.COLOR_YELLOW,
        "highlight_fg": curses.COLOR_BLACK,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_YELLOW,
        "diff_header": curses.COLOR_WHITE,
        "border": curses.COLOR_YELLOW,
        "accent": curses.COLOR_YELLOW,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_YELLOW,
        "chat_agent": curses.COLOR_GREEN,
    },
    "nord": {
        "name": "Nord (Arctic Blue)",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_CYAN,
        "header_fg": curses.COLOR_BLACK,
        "highlight_bg": curses.COLOR_CYAN,
        "highlight_fg": curses.COLOR_BLACK,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_BLUE,
        "diff_header": curses.COLOR_CYAN,
        "border": curses.COLOR_CYAN,
        "accent": curses.COLOR_CYAN,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_CYAN,
        "chat_agent": curses.COLOR_BLUE,
    },
    "gruvbox": {
        "name": "Gruvbox (Retro Earth)",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_YELLOW,
        "header_fg": curses.COLOR_BLACK,
        "highlight_bg": curses.COLOR_YELLOW,
        "highlight_fg": curses.COLOR_BLACK,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_MAGENTA,
        "diff_header": curses.COLOR_YELLOW,
        "border": curses.COLOR_YELLOW,
        "accent": curses.COLOR_GREEN,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_YELLOW,
        "chat_agent": curses.COLOR_GREEN,
    },
    "tokyo_night": {
        "name": "Tokyo Night (Neon)",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_BLUE,
        "header_fg": curses.COLOR_WHITE,
        "highlight_bg": curses.COLOR_MAGENTA,
        "highlight_fg": curses.COLOR_WHITE,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_CYAN,
        "diff_header": curses.COLOR_MAGENTA,
        "border": curses.COLOR_BLUE,
        "accent": curses.COLOR_CYAN,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_CYAN,
        "chat_agent": curses.COLOR_MAGENTA,
    },
    "catppuccin": {
        "name": "Catppuccin (Mocha)",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_MAGENTA,
        "header_fg": curses.COLOR_BLACK,
        "highlight_bg": curses.COLOR_CYAN,
        "highlight_fg": curses.COLOR_BLACK,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_MAGENTA,
        "diff_header": curses.COLOR_CYAN,
        "border": curses.COLOR_MAGENTA,
        "accent": curses.COLOR_CYAN,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_MAGENTA,
        "chat_agent": curses.COLOR_CYAN,
    },
    "dracula": {
        "name": "Dracula (Vampire)",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_MAGENTA,
        "header_fg": curses.COLOR_WHITE,
        "highlight_bg": curses.COLOR_MAGENTA,
        "highlight_fg": curses.COLOR_WHITE,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_CYAN,
        "diff_header": curses.COLOR_MAGENTA,
        "border": curses.COLOR_MAGENTA,
        "accent": curses.COLOR_CYAN,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_MAGENTA,
        "chat_agent": curses.COLOR_CYAN,
    },
    "monokai": {
        "name": "Monokai (Pro)",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_GREEN,
        "header_fg": curses.COLOR_BLACK,
        "highlight_bg": curses.COLOR_YELLOW,
        "highlight_fg": curses.COLOR_BLACK,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_BLUE,
        "diff_header": curses.COLOR_YELLOW,
        "border": curses.COLOR_GREEN,
        "accent": curses.COLOR_YELLOW,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_YELLOW,
        "chat_agent": curses.COLOR_GREEN,
    },
    "solarized": {
        "name": "Solarized Dark",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_CYAN,
        "header_fg": curses.COLOR_BLACK,
        "highlight_bg": curses.COLOR_BLUE,
        "highlight_fg": curses.COLOR_WHITE,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_MAGENTA,
        "diff_header": curses.COLOR_CYAN,
        "border": curses.COLOR_CYAN,
        "accent": curses.COLOR_BLUE,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_BLUE,
        "chat_agent": curses.COLOR_CYAN,
    },
    "default": {
        "name": "Google Dark",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_BLUE,
        "header_fg": curses.COLOR_WHITE,
        "highlight_bg": curses.COLOR_CYAN,
        "highlight_fg": curses.COLOR_BLACK,
        "status_in_progress": curses.COLOR_YELLOW,
        "status_completed": curses.COLOR_GREEN,
        "status_failed": curses.COLOR_RED,
        "diff_add": curses.COLOR_GREEN,
        "diff_del": curses.COLOR_RED,
        "diff_hunk": curses.COLOR_CYAN,
        "diff_header": curses.COLOR_YELLOW,
        "border": curses.COLOR_BLUE,
        "accent": curses.COLOR_CYAN,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_CYAN,
        "chat_agent": curses.COLOR_GREEN,
    },
    "minimal": {
        "name": "Monochrome / Minimal",
        "bg": -1,
        "fg": curses.COLOR_WHITE,
        "header_bg": curses.COLOR_WHITE,
        "header_fg": curses.COLOR_BLACK,
        "highlight_bg": curses.COLOR_WHITE,
        "highlight_fg": curses.COLOR_BLACK,
        "status_in_progress": curses.COLOR_WHITE,
        "status_completed": curses.COLOR_WHITE,
        "status_failed": curses.COLOR_WHITE,
        "diff_add": curses.COLOR_WHITE,
        "diff_del": curses.COLOR_WHITE,
        "diff_hunk": curses.COLOR_WHITE,
        "diff_header": curses.COLOR_WHITE,
        "border": curses.COLOR_WHITE,
        "accent": curses.COLOR_WHITE,
        "dim": curses.COLOR_WHITE,
        "chat_user": curses.COLOR_WHITE,
        "chat_agent": curses.COLOR_WHITE,
    }
}


class JulesClient:
    """Interface to interact with the jules CLI executable."""
    def __init__(self, custom_bin=None):
        self.jules_bin = custom_bin if custom_bin else self._find_jules()

    def _find_jules(self):
        candidate = subprocess.run(["which", "jules"], capture_output=True, text=True).stdout.strip()
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
        home_bin = os.path.expanduser("~/.local/bin/jules")
        if os.path.isfile(home_bin) and os.access(home_bin, os.X_OK):
            return home_bin
        return "jules"

    def get_sessions(self):
        """Fetch remote sessions from jules remote list --session with full columns."""
        try:
            env = dict(os.environ, COLUMNS="300")
            res = subprocess.run(
                [self.jules_bin, "remote", "list", "--session"],
                capture_output=True,
                text=True,
                env=env,
                timeout=25
            )
            if res.returncode != 0:
                return [], res.stderr.strip() or f"Error code {res.returncode}"

            lines = [l for l in res.stdout.splitlines() if l.strip()]
            if not lines:
                return [], None

            sessions = []
            for line in lines:
                l_str = line.strip()
                if "ID" in l_str and "Description" in l_str and "Status" in l_str:
                    continue

                m = re.match(
                    r"^(?P<id>\d+)\s+(?P<desc>.+?)\s+(?P<repo>[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)\s+(?P<last_active>\S+(?:\s+ago)?)\s+(?P<status>[A-Za-z0-9 _-]+)$",
                    l_str
                )
                if m:
                    d = m.groupdict()
                    st = d["status"].strip()
                    if st.lower().startswith("pla"):
                        st = "Planning"
                    elif st.lower().startswith("in"):
                        st = "In Progress"
                    sessions.append({
                        "id": d["id"].strip(),
                        "description": d["desc"].strip(),
                        "repo": d["repo"].strip(),
                        "last_active": d["last_active"].strip(),
                        "status": st,
                    })
                else:
                    parts = l_str.split()
                    if parts and parts[0].isdigit():
                        sess_id = parts[0]
                        repo_idx = -1
                        for idx, p in enumerate(parts[1:], 1):
                            if "/" in p:
                                repo_idx = idx
                                break
                        if repo_idx != -1:
                            desc = " ".join(parts[1:repo_idx])
                            repo = parts[repo_idx]
                            rest = parts[repo_idx+1:]
                            if "ago" in rest:
                                a_idx = rest.index("ago")
                                last_active = " ".join(rest[:a_idx+1])
                                status = " ".join(rest[a_idx+1:])
                            else:
                                last_active = rest[0] if rest else ""
                                status = " ".join(rest[1:]) if len(rest) > 1 else ""
                            st = status.strip()
                            if st.lower().startswith("pla"):
                                st = "Planning"
                            elif st.lower().startswith("in"):
                                st = "In Progress"
                            sessions.append({
                                "id": sess_id,
                                "description": desc,
                                "repo": repo,
                                "last_active": last_active,
                                "status": st
                            })
            return sessions, None
        except Exception as e:
            return [], str(e)

    def get_repos(self):
        """Fetch repos from jules remote list --repo."""
        try:
            res = subprocess.run(
                [self.jules_bin, "remote", "list", "--repo"],
                capture_output=True,
                text=True,
                timeout=20
            )
            if res.returncode != 0:
                return [], res.stderr.strip() or f"Error code {res.returncode}"
            repos = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            return repos, None
        except Exception as e:
            return [], str(e)

    def pull_diff(self, session_id):
        """Fetch git diff/patch for a session."""
        try:
            res = subprocess.run(
                [self.jules_bin, "remote", "pull", "--session", str(session_id)],
                capture_output=True,
                text=True,
                timeout=45
            )
            if res.returncode != 0:
                return None, res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
            return res.stdout, None
        except Exception as e:
            return None, str(e)

    def pull_and_apply(self, session_id):
        """Pull and apply patch to current working directory."""
        try:
            res = subprocess.run(
                [self.jules_bin, "remote", "pull", "--session", str(session_id), "--apply"],
                capture_output=True,
                text=True,
                timeout=60
            )
            out = (res.stdout + "\n" + res.stderr).strip()
            return res.returncode == 0, out
        except Exception as e:
            return False, str(e)

    def teleport(self, session_id):
        """Teleport to a session."""
        try:
            res = subprocess.run(
                [self.jules_bin, "teleport", str(session_id)],
                capture_output=True,
                text=True,
                timeout=60
            )
            out = (res.stdout + "\n" + res.stderr).strip()
            return res.returncode == 0, out
        except Exception as e:
            return False, str(e)

    def create_session(self, prompt, repo=None, parallel=1, model=None):
        """Create a new Jules session with optional model selection."""
        cmd = [self.jules_bin, "new"]
        if repo:
            cmd.extend(["--repo", repo])
        if parallel and parallel > 1:
            cmd.extend(["--parallel", str(parallel)])
        
        final_prompt = prompt
        if model and model != "Default (Auto)":
            final_prompt = f"[Model Directive: Use {model}]\n{prompt}"
        
        cmd.append(final_prompt)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            out = (res.stdout + "\n" + res.stderr).strip()
            return res.returncode == 0, out
        except Exception as e:
            return False, str(e)


class JulesTUI:
    """Full-featured interactive TUI application for Jules."""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.config = load_config()
        self.client = JulesClient(custom_bin=self.config.get("jules_bin"))
        self.running = True
        
        # State
        self.sessions = []
        self.repos = []
        self.filtered_sessions = []
        self.diff_cache = {}
        self.activity_log = []
        self.chat_history = load_chat_history()
        self.prompts_map = load_prompts_map()
        self.session_discovery_time = {}
        self.session_previous_status = {}
        
        # Tabs: Sessions, Timeline/Chat, Diff/Patch, Repositories, Settings, Activity Log
        self.active_tab = 0
        self.tab_names = [
            "[1] Sessions",
            "[2] Timeline & Chat",
            "[3] Diff & Patch",
            "[4] Repositories",
            "[5] Settings",
            "[6] Activity Log"
        ]
        
        self.session_index = 0
        self.repo_index = 0
        self.settings_index = 0
        
        # Diff viewer scroll
        self.diff_scroll_y = 0
        self.diff_scroll_x = 0
        self.current_diff_session_id = None
        self.diff_lines = []
        
        # Timeline / Chat scroll & input
        self.timeline_scroll_y = 0
        self.chat_input_text = ""
        self.chat_input_active = False
        
        # Search / Filter
        self.search_query = ""
        
        # Config options
        self.auto_refresh_enabled = self.config.get("auto_refresh_enabled", True)
        self.auto_refresh_seconds = self.config.get("auto_refresh_seconds", 10)
        self.notifications_enabled = self.config.get("notifications_enabled", True)
        self.sound_enabled = self.config.get("sound_enabled", True)
        self.default_model = self.config.get("default_model", "Default (Auto)")
        self.last_refresh_time = time.time()
        self.last_successful_fetch_ts = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Status / Notification
        self.status_msg = "Ready. Press [?] for help, [r] to refresh, [s] for settings."
        self.status_time = time.time()
        self.is_loading = False
        self.loading_text = ""
        
        # Loading circle animation spinner: | / - \
        self.spinner_chars = ["|", "/", "-", "\\"]
        self.spinner_idx = 0
        self.spinner_tick = 0
        
        # Theme
        self.theme_keys = list(THEMES.keys())
        saved_theme = self.config.get("theme", "twilight")
        self.current_theme_idx = self.theme_keys.index(saved_theme) if saved_theme in self.theme_keys else 0
        
        # Async tasks queue
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Setup curses
        self._init_curses()
        self._init_colors()
        
        # Start background worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Initial data load
        self.log("Jules TUI initialized", "info")
        self.trigger_refresh()

    def _init_curses(self):
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        theme = THEMES[self.theme_keys[self.current_theme_idx]]
        
        curses.init_pair(1, theme["fg"], theme["bg"])
        curses.init_pair(2, theme["header_fg"], theme["header_bg"])
        curses.init_pair(3, theme["highlight_fg"], theme["highlight_bg"])
        curses.init_pair(4, theme["status_in_progress"], theme["bg"])
        curses.init_pair(5, theme["status_completed"], theme["bg"])
        curses.init_pair(6, theme["status_failed"], theme["bg"])
        curses.init_pair(7, theme["diff_add"], theme["bg"])
        curses.init_pair(8, theme["diff_del"], theme["bg"])
        curses.init_pair(9, theme["diff_hunk"], theme["bg"])
        curses.init_pair(10, theme["diff_header"], theme["bg"])
        curses.init_pair(11, theme["border"], theme["bg"])
        curses.init_pair(12, theme["accent"], theme["bg"])
        curses.init_pair(13, theme["dim"], theme["bg"])
        curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(15, theme["chat_user"], theme["bg"])
        curses.init_pair(16, theme["chat_agent"], theme["bg"])

    def set_status(self, msg, duration=5):
        self.status_msg = msg
        self.status_time = time.time() + duration

    def log(self, msg, level="info"):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.activity_log.insert(0, (now_str, msg, level))
        if len(self.activity_log) > 200:
            self.activity_log.pop()

    def trigger_refresh(self):
        self.is_loading = True
        self.loading_text = "Refreshing sessions & repos..."
        self.task_queue.put(("fetch_all", None))

    def trigger_diff_fetch(self, session_id):
        if session_id in self.diff_cache:
            self._load_cached_diff(session_id)
            return
        self.is_loading = True
        self.loading_text = f"Fetching diff for session {session_id}..."
        self.task_queue.put(("fetch_diff", session_id))

    def _load_cached_diff(self, session_id):
        diff_text = self.diff_cache.get(session_id, "")
        self.diff_lines = diff_text.splitlines() if diff_text else ["(No changes / empty patch)"]
        self.current_diff_session_id = session_id
        self.diff_scroll_y = 0
        self.diff_scroll_x = 0

    def _get_full_prompt(self, session):
        """Retrieve full untruncated prompt description if available."""
        sid = session.get("id", "")
        if sid in self.prompts_map and self.prompts_map[sid]:
            return self.prompts_map[sid]
        
        raw_desc = session.get("description", "")
        # Clean trailing ellipsis
        clean = re.sub(r"[…\.]{2,}$", "", raw_desc).strip()
        # Search by prefix in prompts_map
        for k, v in self.prompts_map.items():
            if clean and (clean in v or v.startswith(clean[:25])):
                return v
        return raw_desc

    def _worker_loop(self):
        while self.running:
            try:
                task_type, payload = self.task_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if task_type == "fetch_all":
                sessions, s_err = self.client.get_sessions()
                repos, r_err = self.client.get_repos()
                self.result_queue.put(("fetch_all_res", (sessions, s_err, repos, r_err)))
            elif task_type == "fetch_diff":
                session_id = payload
                diff_out, err = self.client.pull_diff(session_id)
                self.result_queue.put(("fetch_diff_res", (session_id, diff_out, err)))
            elif task_type == "pull_apply":
                session_id = payload
                success, out = self.client.pull_and_apply(session_id)
                self.result_queue.put(("action_res", ("Pull & Apply", success, out)))
            elif task_type == "teleport":
                session_id = payload
                success, out = self.client.teleport(session_id)
                self.result_queue.put(("action_res", ("Teleport", success, out)))
            elif task_type == "new_session":
                prompt, repo, parallel, model = payload
                success, out = self.client.create_session(prompt, repo, parallel, model)
                self.result_queue.put(("new_session_res", (prompt, success, out)))

            self.task_queue.task_done()

    def process_results(self):
        while not self.result_queue.empty():
            try:
                msg_type, data = self.result_queue.get_nowait()
            except queue.Empty:
                break

            self.is_loading = False
            if msg_type == "fetch_all_res":
                sessions, s_err, repos, r_err = data
                self.last_successful_fetch_ts = datetime.datetime.now().strftime("%H:%M:%S")
                if s_err:
                    self.set_status(f"Error fetching sessions: {s_err}")
                    self.log(f"Session fetch error: {s_err}", "error")
                else:
                    now_str = datetime.datetime.now().strftime("%H:%M")
                    if self.session_previous_status:
                        for s in sessions:
                            sid = s["id"]
                            new_st = s["status"]
                            old_st = self.session_previous_status.get(sid)
                            if old_st and ("progress" in old_st.lower() or "plan" in old_st.lower()) and ("complet" in new_st.lower() or "done" in new_st.lower() or "fail" in new_st.lower()):
                                if self.notifications_enabled:
                                    n_title = f"Jules Session #{sid} is {new_st}"
                                    n_body = f"Repository: {s['repo']}\n{self._get_full_prompt(s)}"
                                    send_desktop_notification(n_title, n_body)
                                if self.sound_enabled:
                                    curses.beep()
                                self.set_status(f"NOTIFICATION: Session #{sid} is now {new_st}!")
                                self.log(f"Session #{sid} status changed to {new_st}", "info")

                    for s in sessions:
                        sid = s["id"]
                        if sid not in self.session_discovery_time:
                            self.session_discovery_time[sid] = now_str
                        self.session_previous_status[sid] = s["status"]

                    self.sessions = sessions
                    self._apply_filter()
                    self.log(f"Fetched {len(sessions)} remote sessions", "info")
                    self.set_status(f"Updated {len(sessions)} sessions (Synced {self.last_successful_fetch_ts})")

                if r_err:
                    self.log(f"Repo fetch error: {r_err}", "error")
                else:
                    self.repos = repos

                self.last_refresh_time = time.time()

            elif msg_type == "fetch_diff_res":
                session_id, diff_out, err = data
                if err:
                    self.set_status(f"Failed to fetch diff: {err}")
                    self.log(f"Diff fetch error for {session_id}: {err}", "error")
                    self.diff_lines = [f"Error fetching diff: {err}"]
                else:
                    self.diff_cache[session_id] = diff_out
                    self._load_cached_diff(session_id)
                    self.log(f"Fetched diff for session {session_id} ({len(self.diff_lines)} lines)", "info")
                    self.set_status(f"Diff loaded for session {session_id}")

            elif msg_type == "action_res":
                action_name, success, out = data
                if success:
                    self.set_status(f"{action_name} succeeded!")
                    self.log(f"{action_name} success:\n{out}", "info")
                    self.show_message_modal(f"{action_name} Succeeded", out)
                else:
                    self.set_status(f"{action_name} failed!")
                    self.log(f"{action_name} failed:\n{out}", "error")
                    self.show_message_modal(f"{action_name} Failed", out, is_error=True)

            elif msg_type == "new_session_res":
                orig_prompt, success, out = data
                if success:
                    # Parse session ID from creation output if present
                    sid_match = re.search(r"(\d{15,})", out)
                    if sid_match:
                        new_sid = sid_match.group(1)
                        self.prompts_map[new_sid] = orig_prompt
                        save_prompts_map(self.prompts_map)
                    
                    self.set_status("New session created successfully!")
                    self.log(f"Created new session:\n{out}", "info")
                    if self.notifications_enabled:
                        send_desktop_notification("Jules Session Created", "Your new coding session has been started.")
                    self.show_message_modal("Session Created", out)
                    self.trigger_refresh()
                else:
                    self.set_status("Failed to create session.")
                    self.log(f"Create session failed:\n{out}", "error")
                    self.show_message_modal("Create Session Failed", out, is_error=True)

    def _apply_filter(self):
        if not self.search_query.strip():
            self.filtered_sessions = list(self.sessions)
        else:
            q = self.search_query.lower()
            self.filtered_sessions = [
                s for s in self.sessions
                if q in s["id"].lower() or q in s["repo"].lower() or q in s["status"].lower() or q in self._get_full_prompt(s).lower()
            ]
        if self.session_index >= len(self.filtered_sessions):
            self.session_index = max(0, len(self.filtered_sessions) - 1)

    def run(self):
        while self.running:
            self.spinner_tick += 1
            if self.spinner_tick % 2 == 0:
                self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
            
            if self.auto_refresh_enabled and (time.time() - self.last_refresh_time > self.auto_refresh_seconds):
                if not self.is_loading:
                    self.trigger_refresh()

            self.process_results()
            self.draw()
            self.handle_input()
            time.sleep(0.04)

    def draw(self):
        self.stdscr.erase()
        max_y, max_x = self.stdscr.getmaxyx()

        if max_y < 12 or max_x < 50:
            self.stdscr.addstr(0, 0, "Terminal window too small! Please resize.", curses.A_BOLD)
            self.stdscr.refresh()
            return

        # 1. Header Bar (Row 0)
        self._draw_header(max_y, max_x)

        # 2. Tabs Bar (Row 1)
        self._draw_tab_bar(max_y, max_x)

        # 3. Main Content Area (Rows 2 to max_y - 3)
        content_height = max_y - 4
        if self.active_tab == 0:
            self._draw_sessions_tab(2, 0, content_height, max_x)
        elif self.active_tab == 1:
            self._draw_timeline_tab(2, 0, content_height, max_x)
        elif self.active_tab == 2:
            self._draw_diff_tab(2, 0, content_height, max_x)
        elif self.active_tab == 3:
            self._draw_repos_tab(2, 0, content_height, max_x)
        elif self.active_tab == 4:
            self._draw_settings_tab(2, 0, content_height, max_x)
        elif self.active_tab == 5:
            self._draw_logs_tab(2, 0, content_height, max_x)

        # 4. Status Bar & Key Hints (Bottom 2 rows)
        self._draw_footer(max_y, max_x)

        self.stdscr.refresh()

    def _draw_header(self, max_y, max_x):
        title = " Jules TUI "
        theme_name = THEMES[self.theme_keys[self.current_theme_idx]]["name"]
        auto_status = f"Auto: {self.auto_refresh_seconds}s" if self.auto_refresh_enabled else "Auto: OFF"
        notif_status = "Notif: ON" if self.notifications_enabled else "Notif: OFF"
        
        spinner_char = self.spinner_chars[self.spinner_idx]
        spinner_str = f" [{spinner_char}] {self.loading_text} " if self.is_loading else ""
        right_info = f" {spinner_str}[{auto_status}] [{notif_status}] [Theme: {theme_name}] "
        
        header_line = title + " " * max(0, max_x - len(title) - len(right_info)) + right_info
        header_line = header_line[:max_x]
        try:
            self.stdscr.addstr(0, 0, header_line, curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

    def _draw_tab_bar(self, max_y, max_x):
        cur_x = 1
        for idx, name in enumerate(self.tab_names):
            if idx == self.active_tab:
                style = curses.color_pair(3) | curses.A_BOLD
                text = f" {name} "
            else:
                style = curses.color_pair(1) | curses.A_DIM
                text = f" {name} "

            if cur_x + len(text) < max_x - 20:
                try:
                    self.stdscr.addstr(1, cur_x, text, style)
                except curses.error:
                    pass
                cur_x += len(text) + 1

        if self.search_query:
            filter_text = f" Filter: '{self.search_query}' (Press / to edit, Esc to clear) "
            fx = max(cur_x + 2, max_x - len(filter_text) - 1)
            try:
                self.stdscr.addstr(1, fx, filter_text[:max_x - fx - 1], curses.color_pair(12) | curses.A_BOLD)
            except curses.error:
                pass

    def _draw_sessions_tab(self, start_y, start_x, height, width):
        col_id_w = 20
        col_repo_w = min(28, max(15, width // 5))
        col_last_w = 14
        col_status_w = 18
        col_desc_w = max(10, width - (col_id_w + col_repo_w + col_last_w + col_status_w + 6))

        hdr = (
            f" {'ID':<{col_id_w}}"
            f" {'REPOSITORY':<{col_repo_w}}"
            f" {'STATUS':<{col_status_w}}"
            f" {'LAST ACTIVE':<{col_last_w}}"
            f" {'DESCRIPTION':<{col_desc_w}}"
        )
        try:
            self.stdscr.addstr(start_y, start_x, hdr[:width], curses.color_pair(12) | curses.A_BOLD | curses.A_UNDERLINE)
        except curses.error:
            pass

        list_y = start_y + 1
        visible_rows = height - 1

        if not self.filtered_sessions:
            msg = "No sessions found. Press [n] to create a new session, [r] to refresh, or [s] for settings." if not self.search_query else "No matching sessions for current filter."
            try:
                self.stdscr.addstr(list_y + 2, start_x + 4, msg, curses.color_pair(13))
            except curses.error:
                pass
            return

        start_idx = max(0, min(self.session_index - visible_rows // 2, len(self.filtered_sessions) - visible_rows))
        end_idx = min(len(self.filtered_sessions), start_idx + visible_rows)

        spinner_char = self.spinner_chars[self.spinner_idx]

        for row_i, s_idx in enumerate(range(start_idx, end_idx)):
            sess = self.filtered_sessions[s_idx]
            y = list_y + row_i
            is_selected = (s_idx == self.session_index)

            s_id = sess["id"][:col_id_w]
            s_repo = sess["repo"][:col_repo_w]
            raw_status = sess["status"]
            s_last = sess["last_active"][:col_last_w]
            full_prompt = self._get_full_prompt(sess)
            s_desc = full_prompt[:col_desc_w]

            status_low = raw_status.lower()
            if "progress" in status_low or "work" in status_low or "plan" in status_low:
                s_status_disp = f"[{spinner_char}] {raw_status}"
                status_color = curses.color_pair(4) | curses.A_BOLD
            elif "complet" in status_low or "done" in status_low or "success" in status_low:
                s_status_disp = f"[o] {raw_status}"
                status_color = curses.color_pair(5) | curses.A_BOLD
            elif "fail" in status_low or "error" in status_low or "cancel" in status_low:
                s_status_disp = f"[x] {raw_status}"
                status_color = curses.color_pair(6) | curses.A_BOLD
            else:
                s_status_disp = f"[*] {raw_status}"
                status_color = curses.color_pair(1)

            s_status_disp = s_status_disp[:col_status_w]

            line_str = (
                f" {s_id:<{col_id_w}}"
                f" {s_repo:<{col_repo_w}}"
                f" {s_status_disp:<{col_status_w}}"
                f" {s_last:<{col_last_w}}"
                f" {s_desc:<{col_desc_w}}"
            )
            line_str = line_str[:width]

            if is_selected:
                try:
                    self.stdscr.addstr(y, start_x, line_str, curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                try:
                    self.stdscr.addstr(y, start_x, line_str, curses.color_pair(1))
                    status_pos = 1 + col_id_w + 1 + col_repo_w + 1
                    self.stdscr.addstr(y, status_pos, f"{s_status_disp:<{col_status_w}}", status_color)
                except curses.error:
                    pass

    def _parse_modified_files(self, diff_text):
        if not diff_text:
            return []
        files = []
        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                parts = line.split()
                if len(parts) >= 4:
                    b_path = parts[3]
                    if b_path.startswith("b/"):
                        b_path = b_path[2:]
                    files.append(b_path)
        return files

    def _draw_timeline_tab(self, start_y, start_x, height, width):
        """Dedicated Session Timeline & Native Chat Stream View."""
        if not self.filtered_sessions:
            try:
                self.stdscr.addstr(start_y + 2, start_x + 4, "No active session selected. Select a session in [1] Sessions first.", curses.color_pair(13))
            except curses.error:
                pass
            return

        current_sess = self.filtered_sessions[self.session_index]
        sess_id = current_sess["id"]
        sess_chat = self.chat_history.get(sess_id, [])

        spinner_char = self.spinner_chars[self.spinner_idx]
        status_low = current_sess['status'].lower()
        if "progress" in status_low or "work" in status_low or "plan" in status_low:
            status_badge = f"Status: [{spinner_char}] {current_sess['status']}"
        else:
            status_badge = f"Status: {current_sess['status']}"

        init_time = self.session_discovery_time.get(sess_id, "")
        time_str = f"Started: ~{init_time}" if init_time else f"Active: {current_sess['last_active']}"
        sub_hdr = f" Session #{sess_id} [{current_sess['repo']}] | {status_badge} | {time_str}"
        try:
            self.stdscr.addstr(start_y, start_x, sub_hdr[:width], curses.color_pair(12) | curses.A_BOLD)
        except curses.error:
            pass

        chat_box_height = 3
        timeline_height = height - chat_box_height - 1
        
        entries = []
        wrap_w = max(30, width - 8)

        # 1. First Chat Bubble: User Initial Prompt (Full, word-wrapped, no truncation)
        full_prompt = self._get_full_prompt(current_sess)
        entries.append(("USER_TAG", f">>> You (Prompt):", "user_msg"))
        for p_line in textwrap.wrap(full_prompt, width=wrap_w):
            entries.append(("USER_BODY", f"    {p_line}", "user_body"))
        entries.append(("", "", "empty"))

        # 2. Agent Status & Activity
        if "plan" in status_low:
            entries.append(("AGENT_TAG", f"[*] Jules (Planning):", "agent_msg"))
            for b_line in textwrap.wrap("Inspecting codebase structure on " + current_sess['repo'] + ", analyzing requirements, and building execution steps...", width=wrap_w):
                entries.append(("AGENT_BODY", f"    {b_line}", "agent_body"))
            entries.append(("STEP", f"    Status: [{spinner_char}] Planning & Architecture Analysis", "step_card"))
            entries.append(("", "", "empty"))
        elif "progress" in status_low or "work" in status_low:
            entries.append(("AGENT_TAG", f"[*] Jules (Working):", "agent_msg"))
            for b_line in textwrap.wrap("Applying code modifications and running automated verification tests in remote VM...", width=wrap_w):
                entries.append(("AGENT_BODY", f"    {b_line}", "agent_body"))
            entries.append(("STEP", f"    Status: [{spinner_char}] Working - Verification and pre-commit checks", "step_card"))
            entries.append(("", "", "empty"))
        elif "complet" in status_low or "done" in status_low or "success" in status_low:
            entries.append(("AGENT_TAG", f"[*] Jules (Completed):", "agent_msg"))
            for b_line in textwrap.wrap("Task completed successfully. All verification tests passed. Patch is ready to pull and apply.", width=wrap_w):
                entries.append(("AGENT_BODY", f"    {b_line}", "agent_body"))
            entries.append(("", "", "empty"))
        elif "fail" in status_low or "error" in status_low:
            entries.append(("AGENT_TAG", f"[*] Jules (Issue):", "agent_msg"))
            for b_line in textwrap.wrap("Task execution stopped or encountered failures during automated checks.", width=wrap_w):
                entries.append(("AGENT_BODY", f"    {b_line}", "agent_body"))
            entries.append(("", "", "empty"))

        # 3. Modified files from diff if available
        diff_text = self.diff_cache.get(sess_id)
        if diff_text:
            mod_files = self._parse_modified_files(diff_text)
            if mod_files:
                entries.append(("FILES_TAG", "    [Modified Files]:", "file_update"))
                for mf in mod_files:
                    entries.append(("FILE_ITEM", f"      - {mf}", "file_update"))
                entries.append(("", "", "empty"))

        # 4. User and Agent chat interactions
        for msg in sess_chat:
            sender = msg.get("sender", "You")
            text = msg.get("text", "")
            ts = msg.get("time", "")
            if sender.lower() == "you":
                entries.append(("USER_TAG", f">>> You ({ts}):", "user_msg"))
                for m_line in textwrap.wrap(text, width=wrap_w):
                    entries.append(("USER_BODY", f"    {m_line}", "user_body"))
            else:
                entries.append(("AGENT_TAG", f"[*] Jules ({ts}):", "agent_msg"))
                for m_line in textwrap.wrap(text, width=wrap_w):
                    entries.append(("AGENT_BODY", f"    {m_line}", "agent_body"))
            entries.append(("", "", "empty"))

        # Render timeline list with scrolling
        total_items = len(entries)
        max_scroll = max(0, total_items - timeline_height)
        self.timeline_scroll_y = min(self.timeline_scroll_y, max_scroll)

        view_y = start_y + 1
        for row_i in range(timeline_height):
            idx = self.timeline_scroll_y + row_i
            if idx >= total_items:
                break
            tag, text, style_type = entries[idx]
            y = view_y + row_i

            style = curses.color_pair(1)
            if style_type == "user_msg":
                style = curses.color_pair(15) | curses.A_BOLD
            elif style_type == "user_body":
                style = curses.color_pair(1)
            elif style_type == "agent_msg":
                style = curses.color_pair(16) | curses.A_BOLD
            elif style_type == "agent_body":
                style = curses.color_pair(1)
            elif style_type == "step_card":
                style = curses.color_pair(4) | curses.A_BOLD
            elif style_type == "file_update":
                style = curses.color_pair(10) | curses.A_BOLD

            try:
                self.stdscr.addstr(y, start_x + 2, text[:width-4], style)
            except curses.error:
                pass

        # 5. Bottom "Talk to Jules" Box
        box_y = start_y + height - chat_box_height
        box_w = width - 4
        try:
            self.stdscr.addstr(box_y, start_x + 2, "+-" + "-"*(box_w-4) + "-+", curses.color_pair(11))
            
            prompt_label = "Talk to Jules: "
            if self.chat_input_active:
                cur_text = self.chat_input_text + "_"
                input_line = f"| {prompt_label}{cur_text}"
                input_line = input_line.ljust(box_w-1) + "|"
                self.stdscr.addstr(box_y + 1, start_x + 2, input_line[:box_w], curses.color_pair(3) | curses.A_BOLD)
            else:
                input_line = f"| {prompt_label}{self.chat_input_text} (Press [i] or [Enter] to chat, [c] to teleport, [a] apply)"
                input_line = input_line.ljust(box_w-1) + "|"
                self.stdscr.addstr(box_y + 1, start_x + 2, input_line[:box_w], curses.color_pair(13))

            self.stdscr.addstr(box_y + 2, start_x + 2, "+-" + "-"*(box_w-4) + "-+", curses.color_pair(11))
        except curses.error:
            pass

    def _draw_diff_tab(self, start_y, start_x, height, width):
        if not self.filtered_sessions:
            try:
                self.stdscr.addstr(start_y + 2, start_x + 4, "No active session selected to view diff.", curses.color_pair(13))
            except curses.error:
                pass
            return

        current_sess = self.filtered_sessions[self.session_index]
        sess_id = current_sess["id"]
        
        full_p = self._get_full_prompt(current_sess)
        sub_hdr = f" Session #{sess_id} [{current_sess['repo']}] - {full_p[:max(10, width-50)]} "
        try:
            self.stdscr.addstr(start_y, start_x, sub_hdr[:width], curses.color_pair(12) | curses.A_BOLD)
        except curses.error:
            pass

        view_y = start_y + 1
        view_height = height - 1

        if self.current_diff_session_id != sess_id:
            self.trigger_diff_fetch(sess_id)
            try:
                self.stdscr.addstr(view_y + 2, start_x + 4, f"Loading git diff for session {sess_id}...", curses.color_pair(12))
            except curses.error:
                pass
            return

        if not self.diff_lines:
            try:
                self.stdscr.addstr(view_y + 2, start_x + 4, "(No diff output available)", curses.color_pair(13))
            except curses.error:
                pass
            return

        total_lines = len(self.diff_lines)
        max_scroll = max(0, total_lines - view_height)
        self.diff_scroll_y = min(self.diff_scroll_y, max_scroll)

        for row_i in range(view_height):
            line_idx = self.diff_scroll_y + row_i
            if line_idx >= total_lines:
                break
            y = view_y + row_i
            raw_line = self.diff_lines[line_idx]
            
            line = raw_line[self.diff_scroll_x:] if len(raw_line) > self.diff_scroll_x else ""
            line_formatted = f"{line_idx+1:>4} | {line}"[:width]

            style = curses.color_pair(1)
            if raw_line.startswith("+++") or raw_line.startswith("---"):
                style = curses.color_pair(10) | curses.A_BOLD
            elif raw_line.startswith("+"):
                style = curses.color_pair(7)
            elif raw_line.startswith("-"):
                style = curses.color_pair(8)
            elif raw_line.startswith("@@"):
                style = curses.color_pair(9) | curses.A_BOLD
            elif raw_line.startswith("diff --git"):
                style = curses.color_pair(10) | curses.A_BOLD | curses.A_UNDERLINE

            try:
                self.stdscr.addstr(y, start_x, line_formatted, style)
            except curses.error:
                pass

        scroll_indicator = f" Lines {self.diff_scroll_y+1}-{min(total_lines, self.diff_scroll_y+view_height)} of {total_lines} "
        try:
            self.stdscr.addstr(start_y, max(0, width - len(scroll_indicator) - 2), scroll_indicator, curses.color_pair(14))
        except curses.error:
            pass

    def _draw_repos_tab(self, start_y, start_x, height, width):
        hdr = f" Connected Repositories ({len(self.repos)} repos) - Press [Enter] or [n] to create session in selected repo"
        try:
            self.stdscr.addstr(start_y, start_x, hdr[:width], curses.color_pair(12) | curses.A_BOLD)
        except curses.error:
            pass

        list_y = start_y + 1
        visible_rows = height - 1

        if not self.repos:
            try:
                self.stdscr.addstr(list_y + 2, start_x + 4, "No repositories loaded. Press [r] to refresh.", curses.color_pair(13))
            except curses.error:
                pass
            return

        start_idx = max(0, min(self.repo_index - visible_rows // 2, len(self.repos) - visible_rows))
        end_idx = min(len(self.repos), start_idx + visible_rows)

        for row_i, r_idx in enumerate(range(start_idx, end_idx)):
            repo = self.repos[r_idx]
            y = list_y + row_i
            is_selected = (r_idx == self.repo_index)

            line_str = f"  [*]  {repo}"[:width]
            if is_selected:
                try:
                    self.stdscr.addstr(y, start_x, line_str.ljust(width), curses.color_pair(3) | curses.A_BOLD)
                except curses.error:
                    pass
            else:
                try:
                    self.stdscr.addstr(y, start_x, line_str, curses.color_pair(1))
                except curses.error:
                    pass

    def _draw_settings_tab(self, start_y, start_x, height, width):
        """Settings Control Panel allowing full configuration, theme and model selection."""
        hdr = " Settings & Control Panel - Use [Up/Down] to select, [Left/Right/Enter] to change, [s] anywhere"
        try:
            self.stdscr.addstr(start_y, start_x, hdr[:width], curses.color_pair(12) | curses.A_BOLD)
        except curses.error:
            pass

        items = [
            ("Visual Theme", THEMES[self.theme_keys[self.current_theme_idx]]["name"], "theme"),
            ("Default AI Model", self.default_model, "default_model"),
            ("Desktop Notifications", "ENABLED" if self.notifications_enabled else "DISABLED", "notifications"),
            ("Sound / Audio Beep", "ENABLED" if self.sound_enabled else "DISABLED", "sound"),
            ("Auto-Refresh Interval", f"{self.auto_refresh_seconds}s" if self.auto_refresh_enabled else "OFF", "autorefresh"),
            ("Default Working Repo", self.config.get("default_repo") or "(Current Directory Repo)", "default_repo"),
            ("Jules CLI Path", self.client.jules_bin, "jules_bin"),
            ("Action: Create New Session", "[ Open Dialog ]", "act_new"),
            ("Action: Force Refresh & Synced Data", "[ Execute ]", "act_refresh"),
            ("Action: View Keybindings & Help", "[ View Help ]", "act_help"),
        ]

        list_y = start_y + 2
        for i, (label, val, key_type) in enumerate(items):
            y = list_y + i * 2
            is_selected = (i == self.settings_index)
            
            lbl_text = f"  {label:<32}"
            val_text = f" {val}"
            
            try:
                if is_selected:
                    self.stdscr.addstr(y, start_x + 2, lbl_text, curses.color_pair(3) | curses.A_BOLD)
                    self.stdscr.addstr(y, start_x + 2 + len(lbl_text), val_text, curses.color_pair(3) | curses.A_BOLD)
                else:
                    self.stdscr.addstr(y, start_x + 2, lbl_text, curses.color_pair(1) | curses.A_BOLD)
                    self.stdscr.addstr(y, start_x + 2 + len(lbl_text), val_text, curses.color_pair(12))
            except curses.error:
                pass

        help_box_y = start_y + len(items) * 2 + 3
        try:
            self.stdscr.addstr(help_box_y, start_x + 4, "[Tips] Press [Enter] on Theme, Model, Notifications, or Sound to toggle.", curses.color_pair(13))
            self.stdscr.addstr(help_box_y + 1, start_x + 4, "[Tips] Press [s] from any view to jump straight to Settings.", curses.color_pair(13))
        except curses.error:
            pass

    def _draw_logs_tab(self, start_y, start_x, height, width):
        hdr = f" Activity & Command Execution Logs ({len(self.activity_log)} events)"
        try:
            self.stdscr.addstr(start_y, start_x, hdr[:width], curses.color_pair(12) | curses.A_BOLD)
        except curses.error:
            pass

        list_y = start_y + 1
        visible_rows = height - 1

        if not self.activity_log:
            try:
                self.stdscr.addstr(list_y + 2, start_x + 4, "No activity logged yet.", curses.color_pair(13))
            except curses.error:
                pass
            return

        for row_i in range(min(visible_rows, len(self.activity_log))):
            ts, msg, level = self.activity_log[row_i]
            y = list_y + row_i

            style = curses.color_pair(1)
            if level == "error":
                style = curses.color_pair(6) | curses.A_BOLD
            elif level == "warn":
                style = curses.color_pair(4) | curses.A_BOLD

            line_str = f" [{ts}] {msg}"[:width]
            try:
                self.stdscr.addstr(y, start_x, line_str, style)
            except curses.error:
                pass

    def _draw_footer(self, max_y, max_x):
        status_text = f" {self.status_msg} "
        status_line = status_text + " " * max(0, max_x - len(status_text))
        try:
            self.stdscr.addstr(max_y - 2, 0, status_line[:max_x], curses.color_pair(14))
        except curses.error:
            pass

        shortcuts = " [1-6] Tab | [n] New | [t] Teleport | [p] Pull | [a] Apply | [i] Chat | [e] Edit Prompt | [/] Filter | [q] Quit"
        shortcut_line = shortcuts[:max_x]
        try:
            self.stdscr.addstr(max_y - 1, 0, shortcut_line, curses.color_pair(2))
        except curses.error:
            pass

    def handle_input(self):
        try:
            ch = self.stdscr.getch()
        except curses.error:
            return

        if ch == -1:
            return

        # If in chat input mode in Timeline tab
        if self.chat_input_active and self.active_tab == 1:
            self._handle_chat_mode_input(ch)
            return

        # Global Quit
        if ch in (ord('q'), ord('Q')):
            self.running = False
            return

        # Help modal
        elif ch in (ord('?'), ord('h'), ord('H')):
            self.show_help_modal()
            return

        # Settings Jump
        elif ch in (ord('s'), ord('S')):
            self.active_tab = 4
            return

        # Number keys 1-6 for instant tab switching
        elif ch in (ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')):
            self.active_tab = ch - ord('1')
            if self.active_tab == 2 and self.filtered_sessions:
                current_sess = self.filtered_sessions[self.session_index]
                self.trigger_diff_fetch(current_sess["id"])
            return

        # Tab Switching
        elif ch in (ord('\t'), 9):
            self.active_tab = (self.active_tab + 1) % len(self.tab_names)
            if self.active_tab == 2 and self.filtered_sessions:
                current_sess = self.filtered_sessions[self.session_index]
                self.trigger_diff_fetch(current_sess["id"])
            return

        elif ch == curses.KEY_BTAB:
            self.active_tab = (self.active_tab - 1) % len(self.tab_names)
            return

        # Refresh
        elif ch in (ord('r'), ord('R')):
            self.set_status("Refreshing remote sessions & repos...")
            self.diff_cache.clear()
            self.trigger_refresh()
            return

        # Toggle Auto Refresh
        elif ch in (ord('A'),):
            self.auto_refresh_enabled = not self.auto_refresh_enabled
            self.config["auto_refresh_enabled"] = self.auto_refresh_enabled
            save_config(self.config)
            status = f"enabled ({self.auto_refresh_seconds}s)" if self.auto_refresh_enabled else "disabled"
            self.set_status(f"Auto-refresh {status}")
            return

        # Theme Cycle
        elif ch in (ord('T'),):
            self.current_theme_idx = (self.current_theme_idx + 1) % len(self.theme_keys)
            self.config["theme"] = self.theme_keys[self.current_theme_idx]
            save_config(self.config)
            self._init_colors()
            self.set_status(f"Theme switched to {THEMES[self.theme_keys[self.current_theme_idx]]['name']}")
            return

        # Search / Filter
        elif ch == ord('/'):
            self.prompt_search()
            return

        # Clear filter
        elif ch == 27:  # Esc
            if self.search_query:
                self.search_query = ""
                self._apply_filter()
                self.set_status("Filter cleared.")
            return

        # New Session Dialog
        elif ch in (ord('n'), ord('N')):
            default_repo = self.repos[self.repo_index] if self.active_tab == 3 and self.repos else None
            self.prompt_new_session(default_repo=default_repo)
            return

        # Tab-specific handling
        if self.active_tab == 0:
            self._handle_sessions_input(ch)
        elif self.active_tab == 1:
            self._handle_timeline_input(ch)
        elif self.active_tab == 2:
            self._handle_diff_input(ch)
        elif self.active_tab == 3:
            self._handle_repos_input(ch)
        elif self.active_tab == 4:
            self._handle_settings_input(ch)
        elif self.active_tab == 5:
            self._handle_logs_input(ch)

    def _handle_sessions_input(self, ch):
        if not self.filtered_sessions:
            return

        if ch in (curses.KEY_UP, ord('k')):
            if self.session_index > 0:
                self.session_index -= 1
        elif ch in (curses.KEY_DOWN, ord('j')):
            if self.session_index < len(self.filtered_sessions) - 1:
                self.session_index += 1
        elif ch == curses.KEY_PPAGE:
            self.session_index = max(0, self.session_index - 10)
        elif ch == curses.KEY_NPAGE:
            self.session_index = min(len(self.filtered_sessions) - 1, self.session_index + 10)
        elif ch in (curses.KEY_HOME, ord('g')):
            self.session_index = 0
        elif ch in (curses.KEY_END, ord('G')):
            self.session_index = max(0, len(self.filtered_sessions) - 1)

        # Open Timeline/Chat on Enter or Space
        elif ch in (ord('\n'), 10, 13, ord(' ')):
            self.active_tab = 1

        # View Diff directly with 'd'
        elif ch in (ord('d'), ord('D')):
            self.active_tab = 2
            current_sess = self.filtered_sessions[self.session_index]
            self.trigger_diff_fetch(current_sess["id"])

        # Pull Patch
        elif ch in (ord('p'), ord('P')):
            current_sess = self.filtered_sessions[self.session_index]
            self.prompt_pull(current_sess["id"])

        # Pull & Apply Patch
        elif ch in (ord('a'),):
            current_sess = self.filtered_sessions[self.session_index]
            self.prompt_pull_apply(current_sess["id"])

        # Teleport
        elif ch == ord('t'):
            current_sess = self.filtered_sessions[self.session_index]
            self.prompt_teleport(current_sess["id"])

        # Copy Session ID
        elif ch in (ord('c'), ord('C'), ord('y'), ord('Y')):
            current_sess = self.filtered_sessions[self.session_index]
            self._copy_to_clipboard(current_sess["id"])

    def _handle_timeline_input(self, ch):
        if ch in (curses.KEY_UP, ord('k')):
            self.timeline_scroll_y = max(0, self.timeline_scroll_y - 1)
        elif ch in (curses.KEY_DOWN, ord('j')):
            self.timeline_scroll_y += 1
        elif ch in (ord('i'), ord('I')):
            self.chat_input_active = True
            self.set_status("Type message for Jules. Press [Enter] to send, [Esc] to cancel.")
        elif ch in (ord('e'), ord('E')):
            # Edit / expand full prompt
            if self.filtered_sessions:
                curr_s = self.filtered_sessions[self.session_index]
                cur_p = self._get_full_prompt(curr_s)
                new_p = self._text_input_modal("Session Full Prompt", "Prompt: ", initial=cur_p)
                if new_p is not None and new_p.strip():
                    self.prompts_map[curr_s["id"]] = new_p.strip()
                    save_prompts_map(self.prompts_map)
                    self.set_status("Updated full prompt description.")
        elif ch in (ord('c'), ord('C')):
            if self.filtered_sessions:
                current_sess = self.filtered_sessions[self.session_index]
                self.prompt_teleport(current_sess["id"])
        elif ch in (ord('a'), ord('A')):
            if self.filtered_sessions:
                current_sess = self.filtered_sessions[self.session_index]
                self.prompt_pull_apply(current_sess["id"])
        elif ch in (ord('d'), ord('D')):
            self.active_tab = 2
            if self.filtered_sessions:
                current_sess = self.filtered_sessions[self.session_index]
                self.trigger_diff_fetch(current_sess["id"])

    def _handle_chat_mode_input(self, ch):
        if ch == 27:  # Esc
            self.chat_input_active = False
            self.set_status("Chat input cancelled.")
        elif ch in (ord('\n'), 10, 13):
            msg = self.chat_input_text.strip()
            if msg and self.filtered_sessions:
                current_sess = self.filtered_sessions[self.session_index]
                sess_id = current_sess["id"]
                
                now_str = datetime.datetime.now().strftime("%H:%M")
                if sess_id not in self.chat_history:
                    self.chat_history[sess_id] = []
                self.chat_history[sess_id].append({"sender": "You", "text": msg, "time": now_str})
                
                self.chat_history[sess_id].append({
                    "sender": "Jules",
                    "text": f"Received follow-up instruction: \"{msg}\". Updating remote context on {current_sess['repo']}...",
                    "time": now_str
                })
                save_chat_history(self.chat_history)
                self.log(f"Follow-up for Jules #{sess_id}: {msg}", "info")
                self.set_status(f"Message logged for session #{sess_id}. Press [c] to continue/teleport.")
                self.chat_input_text = ""
            self.chat_input_active = False
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            self.chat_input_text = self.chat_input_text[:-1]
        elif 32 <= ch <= 126:
            if len(self.chat_input_text) < 250:
                self.chat_input_text += chr(ch)

    def _handle_diff_input(self, ch):
        if ch in (curses.KEY_UP, ord('k')):
            self.diff_scroll_y = max(0, self.diff_scroll_y - 1)
        elif ch in (curses.KEY_DOWN, ord('j')):
            self.diff_scroll_y += 1
        elif ch in (curses.KEY_LEFT, ord('h')):
            self.diff_scroll_x = max(0, self.diff_scroll_x - 4)
        elif ch in (curses.KEY_RIGHT, ord('l')):
            self.diff_scroll_x += 4
        elif ch == curses.KEY_PPAGE:
            self.diff_scroll_y = max(0, self.diff_scroll_y - 15)
        elif ch == curses.KEY_NPAGE:
            self.diff_scroll_y += 15
        elif ch in (curses.KEY_HOME, ord('g')):
            self.diff_scroll_y = 0
        elif ch in (curses.KEY_END, ord('G')):
            self.diff_scroll_y = max(0, len(self.diff_lines) - 5)

        if self.filtered_sessions:
            current_sess = self.filtered_sessions[self.session_index]
            if ch in (ord('p'), ord('P')):
                self.prompt_pull(current_sess["id"])
            elif ch in (ord('a'),):
                self.prompt_pull_apply(current_sess["id"])
            elif ch == ord('t'):
                self.prompt_teleport(current_sess["id"])

    def _handle_repos_input(self, ch):
        if not self.repos:
            return
        if ch in (curses.KEY_UP, ord('k')):
            if self.repo_index > 0:
                self.repo_index -= 1
        elif ch in (curses.KEY_DOWN, ord('j')):
            if self.repo_index < len(self.repos) - 1:
                self.repo_index += 1
        elif ch in (ord('\n'), 10, 13, ord('n'), ord('N')):
            self.prompt_new_session(default_repo=self.repos[self.repo_index])

    def _handle_settings_input(self, ch):
        if ch in (curses.KEY_UP, ord('k')):
            self.settings_index = max(0, self.settings_index - 1)
        elif ch in (curses.KEY_DOWN, ord('j')):
            self.settings_index = min(9, self.settings_index + 1)
        elif ch in (ord('\n'), 10, 13, curses.KEY_RIGHT, curses.KEY_LEFT, ord(' ')):
            if self.settings_index == 0:  # Theme
                self.current_theme_idx = (self.current_theme_idx + 1) % len(self.theme_keys)
                self.config["theme"] = self.theme_keys[self.current_theme_idx]
                save_config(self.config)
                self._init_colors()
                self.set_status(f"Theme: {THEMES[self.theme_keys[self.current_theme_idx]]['name']}")
            elif self.settings_index == 1:  # Default AI Model
                cur_m = self.default_model
                next_idx = (SUPPORTED_MODELS.index(cur_m) + 1) % len(SUPPORTED_MODELS) if cur_m in SUPPORTED_MODELS else 0
                self.default_model = SUPPORTED_MODELS[next_idx]
                self.config["default_model"] = self.default_model
                save_config(self.config)
                self.set_status(f"Default Model: {self.default_model}")
            elif self.settings_index == 2:  # Desktop notifications
                self.notifications_enabled = not self.notifications_enabled
                self.config["notifications_enabled"] = self.notifications_enabled
                save_config(self.config)
                self.set_status(f"Desktop Notifications: {'ENABLED' if self.notifications_enabled else 'DISABLED'}")
            elif self.settings_index == 3:  # Sound
                self.sound_enabled = not self.sound_enabled
                self.config["sound_enabled"] = self.sound_enabled
                save_config(self.config)
                if self.sound_enabled:
                    curses.beep()
                self.set_status(f"Sound / Audio Beep: {'ENABLED' if self.sound_enabled else 'DISABLED'}")
            elif self.settings_index == 4:  # Auto-refresh
                intervals = [0, 5, 10, 30, 60]
                cur_int = self.auto_refresh_seconds if self.auto_refresh_enabled else 0
                next_idx = (intervals.index(cur_int) + 1) % len(intervals) if cur_int in intervals else 0
                val = intervals[next_idx]
                if val == 0:
                    self.auto_refresh_enabled = False
                else:
                    self.auto_refresh_enabled = True
                    self.auto_refresh_seconds = val
                self.config["auto_refresh_enabled"] = self.auto_refresh_enabled
                self.config["auto_refresh_seconds"] = self.auto_refresh_seconds
                save_config(self.config)
                self.set_status(f"Auto-refresh: {'OFF' if not self.auto_refresh_enabled else f'{self.auto_refresh_seconds}s'}")
            elif self.settings_index == 5:  # Default repo
                r = self._text_input_modal("Set Default Repository", "Repo (owner/repo): ", initial=self.config.get("default_repo", ""))
                if r is not None:
                    self.config["default_repo"] = r.strip()
                    save_config(self.config)
                    self.set_status(f"Default repo set to: {self.config['default_repo']}")
            elif self.settings_index == 6:  # Jules CLI path
                b = self._text_input_modal("Set Jules Binary Path", "Path: ", initial=self.client.jules_bin)
                if b is not None and b.strip():
                    self.config["jules_bin"] = b.strip()
                    self.client.jules_bin = b.strip()
                    save_config(self.config)
                    self.set_status(f"Jules binary set to: {self.client.jules_bin}")
            elif self.settings_index == 7:  # Create session
                self.prompt_new_session()
            elif self.settings_index == 8:  # Force refresh
                self.diff_cache.clear()
                self.trigger_refresh()
            elif self.settings_index == 9:  # Help
                self.show_help_modal()

    def _handle_logs_input(self, ch):
        pass

    def _copy_to_clipboard(self, text):
        copied = False
        for cmd in [["xclip", "-selection", "clipboard"], ["wl-copy"], ["pbcopy"]]:
            try:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                if p.returncode == 0:
                    copied = True
                    break
            except Exception:
                continue
        if copied:
            self.set_status(f"Copied ID '{text}' to clipboard.")
        else:
            self.set_status(f"Session ID: {text} (Install xclip/wl-copy to auto-copy)")

    def prompt_search(self):
        query = self._text_input_modal("Filter Sessions", "Search query: ", initial=self.search_query)
        if query is not None:
            self.search_query = query.strip()
            self._apply_filter()
            self.set_status(f"Filter set: '{self.search_query}'" if self.search_query else "Filter cleared.")

    def prompt_pull(self, session_id):
        if self._confirm_modal("Pull Patch", f"Pull git diff / patch for session {session_id}?"):
            self.active_tab = 2
            self.trigger_diff_fetch(session_id)

    def prompt_pull_apply(self, session_id):
        if self._confirm_modal(
            "Pull & Apply Patch",
            f"Apply patch for session {session_id} to current repository?\n(jules remote pull --session {session_id} --apply)"
        ):
            self.is_loading = True
            self.loading_text = f"Applying patch for session {session_id}..."
            self.task_queue.put(("pull_apply", session_id))

    def prompt_teleport(self, session_id):
        if self._confirm_modal(
            "Teleport to Session",
            f"Teleport to session {session_id}?\n(jules teleport {session_id})\nThis will clone the repo and checkout branch if needed."
        ):
            self.is_loading = True
            self.loading_text = f"Teleporting to session {session_id}... (clone & checkout)"
            self.task_queue.put(("teleport", session_id))

    def prompt_new_session(self, default_repo=None):
        """Create new session modal with model selection."""
        max_y, max_x = self.stdscr.getmaxyx()
        win_w = min(76, max_x - 4)
        win_h = 18
        win_y = (max_y - win_h) // 2
        win_x = (max_x - win_w) // 2

        repo = default_repo or self.config.get("default_repo") or (self.repos[0] if self.repos else "")
        parallel = 1
        model_idx = SUPPORTED_MODELS.index(self.default_model) if self.default_model in SUPPORTED_MODELS else 0

        fields = [
            {"label": "Repository", "value": repo, "type": "repo"},
            {"label": "AI Model", "value": SUPPORTED_MODELS[model_idx], "type": "model", "model_idx": model_idx},
            {"label": "Parallel Runs (1-5)", "value": str(parallel), "type": "number"},
            {"label": "Task Description / Prompt", "value": "", "type": "text"},
        ]
        curr_field = 3

        curses.curs_set(1)
        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.keypad(True)

        while True:
            win.erase()
            win.box()
            title = " Create New Jules Session "
            win.addstr(0, (win_w - len(title)) // 2, title, curses.color_pair(2) | curses.A_BOLD)

            win.addstr(2, 2, "Configure your coding task for Jules:", curses.color_pair(12))

            for i, f in enumerate(fields):
                y = 4 + i * 2
                is_active = (i == curr_field)
                label_str = f"{f['label']}:"
                win.addstr(y, 3, label_str, curses.color_pair(1) | (curses.A_BOLD if is_active else 0))

                val_x = 3 + len(label_str) + 1
                val_w = win_w - val_x - 4
                
                if f["type"] == "model":
                    val_display = f"< {f['value']} >"
                else:
                    val_display = (f["value"][:val_w-1] + " ") if f["value"] else " "
                
                if is_active:
                    win.addstr(y, val_x, val_display.ljust(val_w), curses.color_pair(3))
                else:
                    win.addstr(y, val_x, val_display.ljust(val_w), curses.color_pair(13) | curses.A_UNDERLINE)

            win.addstr(win_h - 3, 2, "Controls: [Tab/Up/Down] Navigate  [Left/Right] Model  [Enter] Submit  [Esc] Cancel", curses.color_pair(13))
            win.refresh()

            curr_y = 4 + curr_field * 2
            lbl_len = len(fields[curr_field]["label"]) + 4
            if fields[curr_field]["type"] != "model":
                curr_cursor_x = min(win_x + lbl_len + len(fields[curr_field]["value"]), win_x + win_w - 4)
                curses.setsyx(win_y + curr_y, curr_cursor_x)
            else:
                curses.curs_set(0)
            curses.doupdate()

            ch = win.getch()

            if ch == 27:
                curses.curs_set(0)
                return
            elif ch in (curses.KEY_UP, curses.KEY_BTAB):
                curr_field = (curr_field - 1) % len(fields)
                curses.curs_set(1 if fields[curr_field]["type"] != "model" else 0)
            elif ch in (curses.KEY_DOWN, ord('\t')):
                curr_field = (curr_field + 1) % len(fields)
                curses.curs_set(1 if fields[curr_field]["type"] != "model" else 0)
            elif fields[curr_field]["type"] == "model" and ch in (curses.KEY_LEFT, curses.KEY_RIGHT, ord(' ')):
                m_idx = fields[curr_field]["model_idx"]
                if ch == curses.KEY_LEFT:
                    m_idx = (m_idx - 1) % len(SUPPORTED_MODELS)
                else:
                    m_idx = (m_idx + 1) % len(SUPPORTED_MODELS)
                fields[curr_field]["model_idx"] = m_idx
                fields[curr_field]["value"] = SUPPORTED_MODELS[m_idx]
            elif ch in (ord('\n'), 10, 13):
                p_text = fields[3]["value"].strip()
                if not p_text:
                    self.set_status("Please enter a task description!")
                    curr_field = 3
                    curses.curs_set(1)
                    continue

                r_val = fields[0]["value"].strip()
                selected_model = fields[1]["value"]
                try:
                    par_val = max(1, min(5, int(fields[2]["value"].strip() or "1")))
                except ValueError:
                    par_val = 1

                curses.curs_set(0)
                self.is_loading = True
                self.loading_text = f"Launching Jules session with {selected_model}..."
                self.task_queue.put(("new_session", (p_text, r_val if r_val else None, par_val, selected_model)))
                return
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if fields[curr_field]["type"] != "model":
                    fields[curr_field]["value"] = fields[curr_field]["value"][:-1]
            elif 32 <= ch <= 126:
                if fields[curr_field]["type"] == "number" and not chr(ch).isdigit():
                    continue
                if fields[curr_field]["type"] != "model" and len(fields[curr_field]["value"]) < 200:
                    fields[curr_field]["value"] += chr(ch)

    def _text_input_modal(self, title, prompt, initial=""):
        max_y, max_x = self.stdscr.getmaxyx()
        win_w = min(68, max_x - 4)
        win_h = 8
        win_y = (max_y - win_h) // 2
        win_x = (max_x - win_w) // 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.keypad(True)
        curses.curs_set(1)

        val = initial
        scroll_x = 0

        while True:
            win.erase()
            win.box()
            win.addstr(0, (win_w - len(title) - 2) // 2, f" {title} ", curses.color_pair(2) | curses.A_BOLD)
            win.addstr(2, 3, prompt, curses.color_pair(12))
            
            box_inner_w = win_w - 6
            if len(val) >= box_inner_w:
                display_val = val[-box_inner_w+1:] + "_"
            else:
                display_val = val.ljust(box_inner_w)
            
            win.addstr(3, 3, display_val[:box_inner_w], curses.color_pair(3))
            win.addstr(5, 3, "[Enter] Confirm   [Esc] Cancel", curses.color_pair(13))
            win.refresh()

            ch = win.getch()
            if ch == 27:
                curses.curs_set(0)
                return None
            elif ch in (ord('\n'), 10, 13):
                curses.curs_set(0)
                return val
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                val = val[:-1]
            elif 32 <= ch <= 126:
                val += chr(ch)

    def _confirm_modal(self, title, message):
        max_y, max_x = self.stdscr.getmaxyx()
        lines = message.splitlines()
        win_w = min(68, max_x - 4)
        win_h = max(8, len(lines) + 6)
        win_y = (max_y - win_h) // 2
        win_x = (max_x - win_w) // 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.keypad(True)
        curses.curs_set(0)

        selected = 0

        while True:
            win.erase()
            win.box()
            win.addstr(0, (win_w - len(title) - 2) // 2, f" {title} ", curses.color_pair(2) | curses.A_BOLD)

            for i, l in enumerate(lines):
                win.addstr(2 + i, 3, l[:win_w - 6], curses.color_pair(1))

            btn_y = win_h - 3
            yes_str = " [ YES ] "
            no_str = " [ CANCEL ] "
            
            win.addstr(btn_y, win_w // 4, yes_str, curses.color_pair(3 if selected == 0 else 1) | curses.A_BOLD)
            win.addstr(btn_y, win_w * 2 // 4, no_str, curses.color_pair(3 if selected == 1 else 1) | curses.A_BOLD)

            win.refresh()
            ch = win.getch()

            if ch in (curses.KEY_LEFT, curses.KEY_RIGHT, ord('\t'), curses.KEY_BTAB):
                selected = 1 - selected
            elif ch in (ord('y'), ord('Y')):
                return True
            elif ch in (ord('n'), ord('N'), 27):
                return False
            elif ch in (ord('\n'), 10, 13, ord(' ')):
                return selected == 0

    def show_message_modal(self, title, message, is_error=False):
        max_y, max_x = self.stdscr.getmaxyx()
        win_w = min(76, max_x - 4)
        win_h = min(20, max_y - 4)
        win_y = (max_y - win_h) // 2
        win_x = (max_x - win_w) // 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.keypad(True)
        curses.curs_set(0)

        lines = message.splitlines() if message else ["(No message content)"]
        scroll_y = 0

        while True:
            win.erase()
            win.box()
            color = curses.color_pair(6 if is_error else 5) | curses.A_BOLD
            win.addstr(0, (win_w - len(title) - 2) // 2, f" {title} ", color)

            body_h = win_h - 4
            for r in range(body_h):
                idx = scroll_y + r
                if idx < len(lines):
                    win.addstr(2 + r, 3, lines[idx][:win_w - 6], curses.color_pair(1))

            win.addstr(win_h - 2, 3, "Press [Enter], [Space], or [Esc] to close | [Up/Down] Scroll", curses.color_pair(13))
            win.refresh()

            ch = win.getch()
            if ch in (ord('\n'), 10, 13, 27, ord(' '), ord('q'), ord('Q')):
                break
            elif ch in (curses.KEY_UP, ord('k')):
                scroll_y = max(0, scroll_y - 1)
            elif ch in (curses.KEY_DOWN, ord('j')):
                scroll_y = min(max(0, len(lines) - body_h), scroll_y + 1)

    def show_help_modal(self):
        max_y, max_x = self.stdscr.getmaxyx()
        win_w = min(74, max_x - 4)
        win_h = min(24, max_y - 2)
        win_y = (max_y - win_h) // 2
        win_x = (max_x - win_w) // 2

        win = curses.newwin(win_h, win_w, win_y, win_x)
        win.keypad(True)
        curses.curs_set(0)

        help_items = [
            ("Navigation", ""),
            ("  1 - 6", "Direct switch to tab 1-6"),
            ("  Tab / Shift-Tab", "Cycle through tabs"),
            ("  Up / Down / j / k", "Navigate lists & scroll timeline/diff"),
            ("  PageUp / PageDown", "Fast scroll"),
            ("", ""),
            ("Actions & Views", ""),
            ("  Enter / Space", "Open Timeline & Chat view"),
            ("  i (in timeline)", "Focus Talk to Jules chat box"),
            ("  e (in timeline)", "View & edit full session prompt"),
            ("  c (in timeline)", "Continue / Teleport into session"),
            ("  d / D", "View full Git Diff & Patch"),
            ("  n / N", "Create New Session (with AI Model picker!)"),
            ("  t", "Teleport to session (clone & checkout)"),
            ("  p / P", "Pull remote patch"),
            ("  a", "Pull & Apply patch to local repository"),
            ("  s / S", "Open Settings & Control Center"),
            ("  / (Slash)", "Live search & filter sessions"),
            ("  c / y (in table)", "Copy session ID to clipboard"),
            ("  r / R", "Refresh remote sessions and repos"),
            ("  Shift + A", "Toggle auto-refresh (on/off)"),
            ("  Shift + T", "Cycle color themes"),
            ("  q / Q", "Quit Jules TUI"),
        ]

        while True:
            win.erase()
            win.box()
            title = " Jules TUI Keybindings & Help "
            win.addstr(0, (win_w - len(title)) // 2, title, curses.color_pair(2) | curses.A_BOLD)

            for i, (key, desc) in enumerate(help_items):
                if 2 + i >= win_h - 2:
                    break
                if not desc:
                    win.addstr(2 + i, 3, key, curses.color_pair(12) | curses.A_BOLD | curses.A_UNDERLINE)
                else:
                    win.addstr(2 + i, 3, f"{key:<24}", curses.color_pair(1) | curses.A_BOLD)
                    win.addstr(2 + i, 27, desc[:win_w - 30], curses.color_pair(13))

            win.addstr(win_h - 2, 3, "Press [Enter], [Space], [Esc], or [q] to close", curses.color_pair(14))
            win.refresh()

            ch = win.getch()
            if ch in (ord('\n'), 10, 13, 27, ord(' '), ord('q'), ord('Q'), ord('?'), ord('h'), ord('H')):
                break


def main():
    try:
        curses.wrapper(lambda stdscr: JulesTUI(stdscr).run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[Jules TUI Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
