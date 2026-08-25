#!/usr/bin/env bash
set -e

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "${INSTALL_DIR}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${INSTALL_DIR}/jules-tui"
SYMLINK_SHORT="${INSTALL_DIR}/jtui"

echo "Installing Jules TUI to ${INSTALL_DIR}..."
cp "${SCRIPT_DIR}/jules_tui.py" "${TARGET}"
chmod +x "${TARGET}"
ln -sf "${TARGET}" "${SYMLINK_SHORT}"

echo " Installation successful!"
echo "You can now run 'jules-tui' or 'jtui' directly from your terminal."
