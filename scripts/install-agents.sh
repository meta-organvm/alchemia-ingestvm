#!/usr/bin/env bash
set -euo pipefail

# Install alchemia launchd agents.
# Usage: ./scripts/install-agents.sh [install|uninstall|status]

AGENTS_DIR="$(cd "$(dirname "$0")/../agents" && pwd)"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

install() {
    echo "Installing alchemia agents..."

    # Make scripts executable
    chmod +x "${SCRIPTS_DIR}/screenshot-watcher.sh"

    # Create Screenshots dir if needed
    mkdir -p "${HOME}/Screenshots"

    # Symlink plist files
    for plist in "${AGENTS_DIR}"/*.plist; do
        local name
        name=$(basename "${plist}")
        local target="${LAUNCH_AGENTS_DIR}/${name}"

        if [[ -f "${target}" ]]; then
            echo "  Updating: ${name}"
            launchctl unload "${target}" 2>/dev/null || true
        else
            echo "  Installing: ${name}"
        fi

        cp "${plist}" "${target}"
        launchctl load "${target}"
        echo "  Loaded: ${name}"
    done

    echo "Done. Agents installed and loaded."
}

uninstall() {
    echo "Uninstalling alchemia agents..."
    for plist in "${AGENTS_DIR}"/*.plist; do
        local name
        name=$(basename "${plist}")
        local target="${LAUNCH_AGENTS_DIR}/${name}"

        if [[ -f "${target}" ]]; then
            launchctl unload "${target}" 2>/dev/null || true
            rm "${target}"
            echo "  Removed: ${name}"
        fi
    done
    echo "Done."
}

status() {
    echo "Alchemia agent status:"
    for plist in "${AGENTS_DIR}"/*.plist; do
        local name
        name=$(basename "${plist}" .plist)
        if launchctl list "${name}" &>/dev/null; then
            echo "  ${name}: RUNNING"
        else
            echo "  ${name}: NOT LOADED"
        fi
    done
}

case "${1:-install}" in
    install)   install ;;
    uninstall) uninstall ;;
    status)    status ;;
    *)         echo "Usage: $0 [install|uninstall|status]" ;;
esac
