# Jules TUI

A clean, high-performance, and feature-rich **Terminal User Interface (TUI)** for **Google Jules**

I got fed up with the basic google jules webui so I made a nice UI

---

## Features

- **Sessions Explorer (`[1]`)**: View all remote sessions with clear status indicators (`In Progress`, `Completed`, `Failed`), active repositories, last active time, and task descriptions.
- **Session Timeline & Chat (`[2]`)**: Interactive activity stream matching Google Jules web UI with full multi-line word wrapping (no truncated messages), file modifications list, verification thoughts, step progress cards, and an interactive **"Talk to Jules"** input bar (`i` or `Enter`) to send instructions and messages.
- **Interactive Git Diff & Patch Viewer (`[3]`)**: View live colorized git diffs (`+` additions, `-` deletions, `@@` hunks, file headers) with horizontal/vertical scrolling.
- **Repository Browser (`[4]`)**: Inspect all connected GitHub repositories with one-key session launcher.
- **Settings & Control Panel (`[5]` or `s`)**: Full visual configuration center to select themes, toggle desktop notifications & sound, configure auto-refresh intervals, set default repositories, configure binary paths, or trigger actions without memorizing shortcuts.
- **Desktop Notifications**: Automatic desktop notifications via `notify-send` / `osascript` whenever background sessions finish (`Completed`, `Failed`, etc.) or when new sessions are created.
- **Activity & Command Log (`[6]`)**: Real-time CLI command execution history and exit status.
- **Teleportation (`t`)**: Fast one-key teleport (`jules teleport <session_id>`) into any session with interactive confirmation.
- **Patch Pulling & Applying (`p` / `a`)**: Inspect remote patches and apply them (`--apply`) directly to your local workspace.
- **Instant Search & Filter (`/`)**: Real-time filter across session IDs, repository names, statuses, and prompts.
- **Comprehensive Themes (`Shift+T` or via Settings)**:
  - **Twilight** (Warm amber / orange / dark gold palette matching btop)
  - **Nord** (Arctic frost cyan / slate blue)
  - **Gruvbox** (Retro earth tones / warm green & yellow)
  - **Tokyo Night** (Neon cyber blue & purple)
  - **Catppuccin** (Mocha / pastel aesthetic)
  - **Dracula** (Vampire purple & pink)
  - **Monokai** (Classic pro vibrant colors)
  - **Solarized Dark** (Teal & blue)
  - **Google Dark** (Google cyan & blue)
  - **Minimal / Monochrome** (Clean black & white)

---

## Quick Start

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

- **Python 3.8+** (preinstalled on virtually all Unix systems)
- **Google Jules CLI** (`jules` installed in PATH or `~/.local/bin/jules`)
- *(Optional)* `notify-send` (Linux) / `osascript` (macOS) for desktop notifications
- *(Optional)* `xclip`, `wl-copy`, or `pbcopy` for clipboard copying
