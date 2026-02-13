#!/usr/bin/env bash
set -euo pipefail

# Screenshot Watcher — captures new screenshots as aesthetic references.
# Triggered by launchd when new files appear in watched directories.

ALCHEMIA_DIR="${HOME}/Workspace/alchemia-ingestvm"
INSPIRATIONS_DIR="${ALCHEMIA_DIR}/inspirations"
LOG_FILE="${ALCHEMIA_DIR}/data/watcher.log"
WATCH_DIRS=(
    "${HOME}/Desktop"
    "${HOME}/Screenshots"
)

mkdir -p "${INSPIRATIONS_DIR}" "$(dirname "${LOG_FILE}")"

log() {
    echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') [screenshot-watcher] $*" >> "${LOG_FILE}"
}

process_file() {
    local file="$1"
    local basename
    basename=$(basename "${file}")
    local ext="${basename##*.}"
    ext=$(echo "${ext}" | tr '[:upper:]' '[:lower:]')

    # Only process image files
    case "${ext}" in
        png|jpg|jpeg|gif|webp|heic) ;;
        *) return ;;
    esac

    # Skip if already in inspirations
    if [[ -f "${INSPIRATIONS_DIR}/${basename}" ]]; then
        return
    fi

    # Skip files older than 60 seconds (avoid processing existing screenshots on first run)
    local file_age
    file_age=$(( $(date +%s) - $(stat -f %m "${file}") ))
    if [[ ${file_age} -gt 60 ]]; then
        return
    fi

    log "New screenshot detected: ${basename}"

    # Copy to inspirations directory
    cp "${file}" "${INSPIRATIONS_DIR}/${basename}"

    # Add to taste.yaml as uncategorized reference
    if command -v alchemia &>/dev/null; then
        alchemia capture --type screenshot "${file}" --tags "uncategorized,screenshot" --notes "Auto-captured by screenshot watcher" 2>> "${LOG_FILE}" || true
    else
        # Fallback: use the venv directly
        "${ALCHEMIA_DIR}/.venv/bin/alchemia" capture --type screenshot "${file}" --tags "uncategorized,screenshot" --notes "Auto-captured by screenshot watcher" 2>> "${LOG_FILE}" || true
    fi

    log "Captured: ${basename}"
}

# Process all recent images in watched directories
for dir in "${WATCH_DIRS[@]}"; do
    if [[ ! -d "${dir}" ]]; then
        continue
    fi
    for file in "${dir}"/*.{png,jpg,jpeg,gif,webp,heic,PNG,JPG,JPEG} 2>/dev/null; do
        [[ -f "${file}" ]] || continue
        process_file "${file}"
    done
done

log "Watcher cycle complete"
