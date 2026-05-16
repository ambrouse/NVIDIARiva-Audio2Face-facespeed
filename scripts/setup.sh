#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs/setup"
LOG_FILE="${LOG_DIR}/setup.log"
MODE="${1:---check}"

mkdir -p "$LOG_DIR"

log() {
  local level="$1"
  local message="$2"
  printf '%s %s setup - %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$message" | tee -a "$LOG_FILE"
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

check_command() {
  local name="$1"
  local executable="$2"
  if has_command "$executable"; then
    log "INFO" "$name available: $($executable --version 2>&1 | head -n 1)"
    return 0
  fi
  log "WARN" "$name missing: $executable not found"
  return 1
}

check_nvidia_gpu() {
  if has_command nvidia-smi; then
    log "INFO" "nvidia-smi available"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>&1 | tee -a "$LOG_FILE"
    return 0
  fi
  log "WARN" "nvidia-smi not found; NVIDIA driver or GPU access is missing"
  return 1
}

check_docker_gpu() {
  if ! has_command docker; then
    log "WARN" "docker not found; cannot check NVIDIA container runtime"
    return 1
  fi
  if docker info 2>/dev/null | grep -qi nvidia; then
    log "INFO" "docker reports NVIDIA runtime/toolkit information"
    return 0
  fi
  log "WARN" "docker is available but NVIDIA runtime/toolkit was not detected"
  return 1
}

check_ports() {
  local ports=(8000 5173 50051 8011)
  for port in "${ports[@]}"; do
    if has_command ss && ss -ltn | grep -q ":${port} "; then
      log "WARN" "port ${port} is already in use"
    else
      log "INFO" "port ${port} appears available or cannot be checked"
    fi
  done
}

check_riva() {
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qi riva; then
    log "INFO" "Riva container appears to be running"
    return 0
  fi
  log "WARN" "Riva container not detected; install/start requires NVIDIA NGC assets"
  return 1
}

check_audio2face() {
  if pgrep -fa audio2face >/dev/null 2>&1 || pgrep -fa Audio2Face >/dev/null 2>&1; then
    log "INFO" "Audio2Face process appears to be running"
    return 0
  fi
  if has_command curl && curl -fsS "http://${A2F_HOST:-127.0.0.1}:${A2F_PORT:-8011}${A2F_HEALTH_PATH:-/health}" >/dev/null 2>&1; then
    log "INFO" "Audio2Face HTTP health endpoint is reachable"
    return 0
  fi
  log "WARN" "Audio2Face process/API not detected; verify local installation or service mode"
  return 1
}

check_ngc() {
  if has_command ngc; then
    log "INFO" "NGC CLI available"
    if ngc config current >/dev/null 2>&1; then
      log "INFO" "NGC CLI appears configured"
      return 0
    fi
    log "WARN" "NGC CLI found but not configured; run ngc config set with your NVIDIA account"
    return 1
  fi
  log "WARN" "NGC CLI not found"
  return 1
}

install_ngc() {
  log "INFO" "checking NGC CLI installation"
  if has_command ngc; then
    log "INFO" "NGC CLI already installed"
    return 0
  fi
  log "WARN" "NGC CLI must be installed from NVIDIA NGC manually or via your approved package source"
  log "WARN" "After installation, run: ngc config set"
}

install_riva() {
  log "INFO" "starting Riva quickstart download check"
  check_ngc || return 1
  local riva_dir="${RIVA_QUICKSTART_DIR:-${ROOT_DIR}/riva_quickstart}"
  mkdir -p "$riva_dir"
  if [[ -f "${riva_dir}/riva_init.sh" ]]; then
    log "INFO" "Riva quickstart appears present at ${riva_dir}"
    return 0
  fi
  log "WARN" "Riva quickstart is not present. Download the matching Riva quickstart assets from NVIDIA NGC into ${riva_dir}."
  log "WARN" "This script does not embed NGC org/team/version assumptions or credentials."
  return 1
}

start_riva() {
  local riva_dir="${RIVA_QUICKSTART_DIR:-${ROOT_DIR}/riva_quickstart}"
  if [[ -x "${riva_dir}/riva_init.sh" && -x "${riva_dir}/riva_start.sh" ]]; then
    log "INFO" "initializing and starting Riva from ${riva_dir}"
    (cd "$riva_dir" && ./riva_init.sh && ./riva_start.sh)
    return 0
  fi
  log "WARN" "Riva quickstart scripts not found or not executable in ${riva_dir}"
  return 1
}

check_riva_tts() {
  log "INFO" "checking Riva TTS port ${RIVA_HOST:-127.0.0.1}:${RIVA_PORT:-50051}"
  if has_command python3; then
    python3 - <<'PY'
import os
import socket
host = os.environ.get('RIVA_HOST', '127.0.0.1')
port = int(os.environ.get('RIVA_PORT', '50051'))
with socket.create_connection((host, port), timeout=5):
    pass
print(f'Riva TCP reachable at {host}:{port}')
PY
    log "INFO" "Riva TCP port is reachable"
    return 0
  fi
  log "WARN" "python3 not found; cannot run Riva TCP check"
  return 1
}

run_check() {
  log "INFO" "starting system check"
  check_command "bash" "bash" || true
  check_command "git" "git" || true
  check_command "curl" "curl" || true
  check_command "python" "python3" || check_command "python" "python" || true
  check_command "node" "node" || true
  check_command "docker" "docker" || true
  check_ngc || true
  check_nvidia_gpu || true
  check_docker_gpu || true
  check_ports
  check_riva || true
  check_audio2face || true
  log "INFO" "system check completed"
}

run_install() {
  log "INFO" "starting install for safe base packages"
  if ! has_command apt-get; then
    log "WARN" "apt-get not found; automatic install is only supported on Debian/Ubuntu hosts"
    return 0
  fi
  if [[ "${EUID}" -ne 0 ]]; then
    log "WARN" "install requires sudo/root; rerun with sudo ./scripts/setup.sh --install"
    return 0
  fi
  apt-get update
  apt-get install -y curl git ca-certificates gnupg python3 python3-venv
  log "INFO" "base packages installed; Docker/NVIDIA/Riva/A2F may require manual NVIDIA-specific steps"
}

run_start_services() {
  log "INFO" "starting configured local services"
  if [[ -f "${ROOT_DIR}/docker-compose.yml" ]] && has_command docker; then
    docker compose -f "${ROOT_DIR}/docker-compose.yml" up -d
    log "INFO" "docker compose services started"
  else
    log "WARN" "docker-compose.yml not found; no services started"
  fi
}

case "$MODE" in
  --check|--check-nvidia)
    run_check
    ;;
  --install)
    run_install
    ;;
  --install-ngc)
    install_ngc
    ;;
  --install-riva)
    install_riva
    ;;
  --start-riva)
    start_riva
    ;;
  --check-riva)
    check_riva || true
    check_riva_tts || true
    ;;
  --check-a2f)
    check_audio2face || true
    ;;
  --start-services)
    run_start_services
    ;;
  --full)
    run_check
    run_install
    run_start_services
    ;;
  --nvidia-full)
    run_check
    install_ngc
    install_riva
    start_riva
    check_riva_tts
    check_audio2face || true
    ;;
  *)
    log "ERROR" "unknown mode: ${MODE}. Use --check, --check-nvidia, --install, --install-ngc, --install-riva, --start-riva, --check-riva, --check-a2f, --start-services, --full, or --nvidia-full"
    exit 2
    ;;
esac
