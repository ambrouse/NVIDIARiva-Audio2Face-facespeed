#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
RETENTION_DAYS="${LOG_RETENTION_DAYS:-14}"
MODE="${1:---status}"

usage() {
  cat <<'USAGE'
FaceSpeed log manager

Usage:
  bash scripts/manage-logs.sh --status
  bash scripts/manage-logs.sh --dry-run
  bash scripts/manage-logs.sh --clean

Policy:
  - Keep curated markdown logs in logs/plans and logs/*.md.
  - Runtime logs (*.log), job logs, PID files, and generated runtime images are disposable.
  - LOG_RETENTION_DAYS controls age-based cleanup; default: 14 days.
USAGE
}

runtime_paths() {
  find "$LOG_DIR" \
    \( -path "$LOG_DIR/plans" -o -path "$LOG_DIR/plans/*" \) -prune -o \
    \( -type f \( -name '*.log' -o -name '*.pid' -o -name '*.png' \) -print -o -path "$LOG_DIR/jobs" -type d -print \) 2>/dev/null || true
}

old_runtime_files() {
  find "$LOG_DIR" \
    \( -path "$LOG_DIR/plans" -o -path "$LOG_DIR/plans/*" \) -prune -o \
    -type f \( -name '*.log' -o -name '*.pid' -o -name '*.png' \) -mtime "+${RETENTION_DAYS}" -print 2>/dev/null || true
}

status() {
  mkdir -p "$LOG_DIR"
  printf 'Log directory: %s\n' "$LOG_DIR"
  printf 'Retention days: %s\n' "$RETENTION_DAYS"
  printf 'Curated markdown logs: %s\n' "$(find "$LOG_DIR" -type f -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
  printf 'Runtime disposable paths: %s\n' "$(runtime_paths | wc -l | tr -d ' ')"
  du -sh "$LOG_DIR" 2>/dev/null || true
}

dry_run() {
  status
  printf '\nDisposable runtime paths:\n'
  runtime_paths | sed 's#^#  #'
  printf '\nOld runtime files over %s days:\n' "$RETENTION_DAYS"
  old_runtime_files | sed 's#^#  #'
}

clean() {
  mkdir -p "$LOG_DIR"
  runtime_paths | while IFS= read -r target; do
    [[ -n "$target" ]] || continue
    rm -rf "$target"
  done
  find "$LOG_DIR" -type d -empty -delete 2>/dev/null || true
  mkdir -p "$LOG_DIR/plans" "$LOG_DIR/runtime"
  status
}

case "$MODE" in
  --help|-h|help)
    usage
    ;;
  --status)
    status
    ;;
  --dry-run)
    dry_run
    ;;
  --clean)
    clean
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    usage >&2
    exit 2
    ;;
esac
