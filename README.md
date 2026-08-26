# Jules TUI

A clean, high-performance, and feature-rich **Terminal User Interface (TUI)** for **Google Jules**

I got fed up with the basic google jules webui so I made a nice UI

---

## Quick Start

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/nebuff/jtui/main/install.sh | bash
```

### Run directly:
```bash
jules-tui
# or short alias:
jtui
```

---

## Keybindings Cheat Sheet

| Key | Action |
|---|---|
| `1` - `6` | Direct jump to tab 1 through 6 |
| `Tab` / `Shift+Tab` | Cycle through tabs |
| `↑` / `↓` / `k` / `j` | Navigate session list / scroll timeline and diffs |
| `Enter` / `Space` | Open **Timeline & Chat** view for selected session |
| `i` / `Enter` (in timeline) | Focus **Talk to Jules** input box to type and send messages |
| `d` | View full **Git Diff & Patch** |
| `s` | Open **Settings & Control Panel** |
| `n` | Create a **New Session** (Repo picker, Parallel count, Prompt) |
| `t` | **Teleport** to session (clone repo & checkout branch) |
| `p` | **Pull** session git diff/patch |
| `a` | **Pull & Apply** session patch to current repository |
| `/` | **Search / Filter** sessions |
| `Esc` | Clear search filter or close modal / exit chat mode |
| `r` | **Refresh** remote sessions & repositories |
| `Shift + A` | Toggle background auto-refresh on/off |
| `Shift + T` | Cycle color themes (*Twilight*, *Nord*, *Gruvbox*, *Tokyo Night*, etc.) |
| `c` / `y` | Copy selected Session ID to clipboard |
| `?` / `h` | Open interactive Help & Keybindings modal |
| `q` | Quit Jules TUI |

---

## Requirements

- **Python 3.8+**
- **Google Jules CLI** (`jules` installed in PATH or `~/.local/bin/jules`)
- *(Optional)* `notify-send` (Linux) / `osascript` (macOS) for desktop notifications
- *(Optional)* `xclip`, `wl-copy`, or `pbcopy` for clipboard copying
