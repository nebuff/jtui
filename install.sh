#!/usr/bin/env bash
set -e

# ==========================================================
#  Jules TUI (jtui) - Full Automated Installer
#  Installs Node.js, npm, Google Jules CLI, Python 3, and jtui
# ==========================================================

REPO_URL="https://github.com/nebuff/jtui.git"
RAW_FILE_URL="https://raw.githubusercontent.com/nebuff/jtui/main/jules_tui.py"

INSTALL_DIR="${HOME}/.local/bin"
DATA_DIR="${HOME}/.local/share/jtui"
TARGET_BIN="${INSTALL_DIR}/jules-tui"
SYMLINK_BIN="${INSTALL_DIR}/jtui"

echo "=========================================="
echo "         Installing Jules TUI (jtui)      "
echo "=========================================="

OS="$(uname -s)"
SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

# ----------------------------------------------------------
# 1. System Package Manager & Base Dependencies
# ----------------------------------------------------------
echo "[*] Checking and installing system dependencies for ${OS}..."

if [ "${OS}" = "Darwin" ]; then
    # macOS: Check Homebrew
    if ! command -v brew >/dev/null 2>&1; then
        echo "[*] Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ -f "/opt/homebrew/bin/brew" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -f "/usr/local/bin/brew" ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi

    # Install python3, node, git, curl if missing
    for pkg in python3 node git curl; do
        if ! command -v "$pkg" >/dev/null 2>&1; then
            echo "[*] Installing $pkg via Homebrew..."
            brew install "$pkg"
        fi
    done

elif [ "${OS}" = "Linux" ]; then
    # Debian / Ubuntu / Pop!_OS / Mint
    if command -v apt-get >/dev/null 2>&1; then
        PKGS_TO_INSTALL=()
        for cmd in python3 node npm git curl; do
            if ! command -v "$cmd" >/dev/null 2>&1; then
                case "$cmd" in
                    node|npm) PKGS_TO_INSTALL+=(nodejs npm) ;;
                    python3) PKGS_TO_INSTALL+=(python3) ;;
                    *) PKGS_TO_INSTALL+=("$cmd") ;;
                esac
            fi
        done
        if ! command -v notify-send >/dev/null 2>&1; then
            PKGS_TO_INSTALL+=(libnotify-bin)
        fi
        if [ ${#PKGS_TO_INSTALL[@]} -gt 0 ]; then
            echo "[*] Installing missing packages via apt: ${PKGS_TO_INSTALL[*]}"
            $SUDO apt-get update -qq
            $SUDO apt-get install -y "${PKGS_TO_INSTALL[@]}"
        fi

    # Fedora / RHEL / CentOS
    elif command -v dnf >/dev/null 2>&1; then
        PKGS_TO_INSTALL=()
        for cmd in python3 node npm git curl; do
            if ! command -v "$cmd" >/dev/null 2>&1; then
                case "$cmd" in
                    node|npm) PKGS_TO_INSTALL+=(nodejs npm) ;;
                    python3) PKGS_TO_INSTALL+=(python3) ;;
                    *) PKGS_TO_INSTALL+=("$cmd") ;;
                esac
            fi
        done
        if ! command -v notify-send >/dev/null 2>&1; then
            PKGS_TO_INSTALL+=(libnotify)
        fi
        if [ ${#PKGS_TO_INSTALL[@]} -gt 0 ]; then
            echo "[*] Installing missing packages via dnf: ${PKGS_TO_INSTALL[*]}"
            $SUDO dnf install -y "${PKGS_TO_INSTALL[@]}"
        fi

    # Arch Linux / Manjaro
    elif command -v pacman >/dev/null 2>&1; then
        PKGS_TO_INSTALL=()
        for cmd in python3 node npm git curl; do
            if ! command -v "$cmd" >/dev/null 2>&1; then
                case "$cmd" in
                    node|npm) PKGS_TO_INSTALL+=(nodejs npm) ;;
                    python3) PKGS_TO_INSTALL+=(python) ;;
                    *) PKGS_TO_INSTALL+=("$cmd") ;;
                esac
            fi
        done
        if ! command -v notify-send >/dev/null 2>&1; then
            PKGS_TO_INSTALL+=(libnotify)
        fi
        if [ ${#PKGS_TO_INSTALL[@]} -gt 0 ]; then
            echo "[*] Installing missing packages via pacman: ${PKGS_TO_INSTALL[*]}"
            $SUDO pacman -Sy --noconfirm "${PKGS_TO_INSTALL[@]}"
        fi

    # openSUSE
    elif command -v zypper >/dev/null 2>&1; then
        PKGS_TO_INSTALL=()
        for cmd in python3 node npm git curl; do
            if ! command -v "$cmd" >/dev/null 2>&1; then
                case "$cmd" in
                    node|npm) PKGS_TO_INSTALL+=(nodejs npm) ;;
                    python3) PKGS_TO_INSTALL+=(python3) ;;
                    *) PKGS_TO_INSTALL+=("$cmd") ;;
                esac
            fi
        done
        if [ ${#PKGS_TO_INSTALL[@]} -gt 0 ]; then
            echo "[*] Installing missing packages via zypper: ${PKGS_TO_INSTALL[*]}"
            $SUDO zypper --non-interactive install "${PKGS_TO_INSTALL[@]}"
        fi
    fi
fi

# ----------------------------------------------------------
# 2. Check & Install Google Jules CLI (@google/jules)
# ----------------------------------------------------------
if ! command -v jules >/dev/null 2>&1 && [ ! -f "${HOME}/.local/bin/jules" ]; then
    echo "[*] Installing Google Jules CLI (@google/jules via npm)..."
    if command -v npm >/dev/null 2>&1; then
        # Try global install without sudo first, fallback to sudo or prefix
        npm install -g @google/jules 2>/dev/null || {
            echo "[*] Retrying npm install with sudo..."
            $SUDO npm install -g @google/jules || {
                echo "[*] Installing Jules locally to ~/.npm-global..."
                mkdir -p "${HOME}/.npm-global"
                npm config set prefix "${HOME}/.npm-global"
                npm install -g @google/jules
                export PATH="${HOME}/.npm-global/bin:${PATH}"
            }
        }
    else
        echo "[!] Warning: npm could not be found. Please ensure Node.js and npm are installed."
    fi
fi

if command -v jules >/dev/null 2>&1 || [ -f "${HOME}/.local/bin/jules" ]; then
    echo "[+] Google Jules CLI is ready."
else
    echo "[!] Notice: Jules was installed; ensure npm global bin directory is in your PATH."
fi

# ----------------------------------------------------------
# 3. Setup Jules TUI Files & Directories
# ----------------------------------------------------------
mkdir -p "${INSTALL_DIR}"
mkdir -p "${DATA_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [ -f "${SCRIPT_DIR}/jules_tui.py" ]; then
    echo "[*] Installing from local directory (${SCRIPT_DIR})..."
    cp "${SCRIPT_DIR}/jules_tui.py" "${DATA_DIR}/jules_tui.py"
    if [ -f "${SCRIPT_DIR}/README.md" ]; then
        cp "${SCRIPT_DIR}/README.md" "${DATA_DIR}/" 2>/dev/null || true
    fi
else
    echo "[*] Standalone install: Fetching latest repository files..."
    if command -v git >/dev/null 2>&1; then
        if [ -d "${DATA_DIR}/.git" ]; then
            echo "[*] Updating existing repository in ${DATA_DIR}..."
            git -C "${DATA_DIR}" pull --quiet || true
        else
            git clone --quiet "${REPO_URL}" "${DATA_DIR}" 2>/dev/null || {
                echo "[*] Downloading jules_tui.py via curl..."
                curl -fsSL "${RAW_FILE_URL}" -o "${DATA_DIR}/jules_tui.py"
            }
        fi
    else
        echo "[*] Downloading jules_tui.py via curl..."
        curl -fsSL "${RAW_FILE_URL}" -o "${DATA_DIR}/jules_tui.py"
    fi
fi

# ----------------------------------------------------------
# 4. Create Executable Launcher
# ----------------------------------------------------------
cat << 'LAUNCHER' > "${TARGET_BIN}"
#!/usr/bin/env bash
DATA_FILE="${HOME}/.local/share/jtui/jules_tui.py"
if [ -f "${DATA_FILE}" ]; then
    exec python3 "${DATA_FILE}" "$@"
elif [ -f "${HOME}/.local/bin/jules_tui.py" ]; then
    exec python3 "${HOME}/.local/bin/jules_tui.py" "$@"
else
    echo "[Error] Jules TUI script not found. Please run install.sh again." >&2
    exit 1
fi
LAUNCHER

chmod +x "${TARGET_BIN}"
chmod +x "${DATA_DIR}/jules_tui.py"
ln -sf "${TARGET_BIN}" "${SYMLINK_BIN}"

# ----------------------------------------------------------
# 5. Shell PATH Configuration
# ----------------------------------------------------------
SHELL_NAME="$(basename "${SHELL:-bash}")"
RC_FILE="${HOME}/.bashrc"
if [ "${SHELL_NAME}" = "zsh" ]; then
    RC_FILE="${HOME}/.zshrc"
fi

if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    echo "[*] Adding ${INSTALL_DIR} to PATH in ${RC_FILE}..."
    echo 'export PATH="${HOME}/.local/bin:${HOME}/.npm-global/bin:${PATH}"' >> "${RC_FILE}"
    export PATH="${INSTALL_DIR}:${HOME}/.npm-global/bin:${PATH}"
fi

echo ""
echo "=========================================="
echo "  [+] Jules TUI successfully installed!"
echo "=========================================="
echo ""
echo "You can now start Jules TUI with:"
echo "    jtui"
echo "or:"
echo "    jules-tui"
echo ""
echo "Location: ${TARGET_BIN}"
echo "Enjoy coding with Google Jules!"
