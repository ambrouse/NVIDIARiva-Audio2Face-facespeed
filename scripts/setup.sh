#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs/setup"
LOG_FILE="${LOG_DIR}/setup.log"
MODE="${1:---auto}"
RIVA_QUICKSTART_DIR="${RIVA_QUICKSTART_DIR:-${ROOT_DIR}/.cache/nvidia/riva}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8020}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-6210}"
RIVA_HOST="${RIVA_HOST:-127.0.0.1}"
RIVA_PORT="${RIVA_PORT:-50100}"
A2F_HOST="${A2F_HOST:-127.0.0.1}"
A2F_PORT="${A2F_PORT:-8040}"
A2F_HEALTH_PATH="${A2F_HEALTH_PATH:-/health}"
CUDA_TEST_IMAGE="${CUDA_TEST_IMAGE:-nvidia/cuda:12.4.1-base-ubuntu22.04}"
NGC_RIVA_QUICKSTART_RESOURCE="${NGC_RIVA_QUICKSTART_RESOURCE:-}"
RESOURCE_RESERVE_PERCENT="${RESOURCE_RESERVE_PERCENT:-10}"
GPU_MIN_FREE_VRAM_PERCENT="${GPU_MIN_FREE_VRAM_PERCENT:-${RESOURCE_RESERVE_PERCENT}}"
RAM_MIN_FREE_PERCENT="${RAM_MIN_FREE_PERCENT:-${RESOURCE_RESERVE_PERCENT}}"
DISK_MIN_FREE_PERCENT="${DISK_MIN_FREE_PERCENT:-${RESOURCE_RESERVE_PERCENT}}"
PROJECT_DOCKER_LABEL="com.facespeed.project=NVIDIARiva-Audio2Face-facespeed"
RIVA_CONTAINER_NAME="${RIVA_CONTAINER_NAME:-facespeed-riva}"
A2F_CONTAINER_NAME="${A2F_CONTAINER_NAME:-facespeed-audio2face}"
RIVA_CONTAINER_IMAGE="${RIVA_CONTAINER_IMAGE:-}"
A2F_CONTAINER_IMAGE="${A2F_CONTAINER_IMAGE:-}"
RIVA_ASSET_DIR="${RIVA_ASSET_DIR:-${ROOT_DIR}/.cache/nvidia/riva}"
A2F_ASSET_DIR="${A2F_ASSET_DIR:-${ROOT_DIR}/.cache/nvidia/audio2face}"
CONTAINER_MEMORY_LIMIT="${CONTAINER_MEMORY_LIMIT:-16g}"
CONTAINER_CPU_LIMIT="${CONTAINER_CPU_LIMIT:-8}"
GPU_DEVICE_FLAG="${GPU_DEVICE_FLAG:---gpus device=0}"

mkdir -p "$LOG_DIR"

log() {
  local level="$1"
  local message="$2"
  printf '%s %s setup - %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$level" "$message" | tee -a "$LOG_FILE"
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

detect_platform() {
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Linux*)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl-linux"
      else
        echo "linux"
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows-git-bash" ;;
    *) echo "unknown" ;;
  esac
}

python_cmd() {
  local candidates=(python3.12 python3.11 python3.10 python3 python)
  if has_command py; then
    candidates+=(py)
  fi
  for candidate in "${candidates[@]}"; do
    if ! has_command "$candidate"; then
      continue
    fi
    if "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
    then
      echo "$candidate"
      return 0
    fi
  done
  echo ""
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

check_python() {
  local py_cmd
  py_cmd="$(python_cmd)"
  if [[ -n "$py_cmd" ]]; then
    log "INFO" "python available: $($py_cmd --version 2>&1 | head -n 1)"
    return 0
  fi
  log "WARN" "python 3.10+ not found; install Python 3.11+ or enable it in PATH"
  return 1
}

venv_python_is_supported() {
  local venv_python="$1"
  [[ -x "$venv_python" ]] || return 1
  "$venv_python" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
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

check_docker() {
  if has_command docker; then
    log "INFO" "docker available: $(docker --version 2>&1 | head -n 1)"
    if docker info >/dev/null 2>&1; then
      log "INFO" "docker daemon is reachable"
      return 0
    fi
    log "WARN" "docker CLI exists but daemon is not reachable; start Docker Desktop or Docker Engine"
    return 1
  fi
  log "WARN" "docker not found"
  return 1
}

check_docker_gpu() {
  check_docker || return 1
  log "INFO" "checking Docker GPU access with ${CUDA_TEST_IMAGE}"
  if docker run --rm --gpus all "$CUDA_TEST_IMAGE" nvidia-smi >>"$LOG_FILE" 2>&1; then
    log "INFO" "Docker GPU access works"
    return 0
  fi
  log "WARN" "Docker GPU access failed; install/enable NVIDIA Container Toolkit or Docker Desktop WSL2 GPU support"
  return 1
}

check_single_port() {
  local name="$1"
  local host="$2"
  local port="$3"
  if has_command ss; then
    local listeners
    listeners="$(ss -ltnp 2>/dev/null | grep -E "(^|[[:space:]])([^[:space:]]+:)?${port}[[:space:]]" || true)"
    if [[ -n "$listeners" ]]; then
      log "WARN" "${name} port ${host}:${port} is already in use; choose another port before starting services"
      printf '%s\n' "$listeners" | tee -a "$LOG_FILE"
      return 1
    fi
  elif has_command netstat; then
    if netstat -an 2>/dev/null | grep -q ":${port} .*LISTEN"; then
      log "WARN" "${name} port ${host}:${port} is already in use; choose another port before starting services"
      return 1
    fi
  else
    log "WARN" "cannot check ${name} port ${host}:${port}; ss/netstat not found"
    return 1
  fi
  log "INFO" "${name} port ${host}:${port} appears available"
}

check_ports() {
  local failed=0
  check_single_port "backend" "$BACKEND_HOST" "$BACKEND_PORT" || failed=1
  check_single_port "frontend" "$FRONTEND_HOST" "$FRONTEND_PORT" || failed=1
  check_single_port "riva" "$RIVA_HOST" "$RIVA_PORT" || failed=1
  check_single_port "audio2face" "$A2F_HOST" "$A2F_PORT" || failed=1
  return "$failed"
}

read_meminfo_value() {
  local key="$1"
  awk -v key="$key" '$1 == key ":" { print $2 }' /proc/meminfo 2>/dev/null
}

check_resources() {
  local failed=0
  local mem_total mem_available commit_limit committed_as commit_free disk_total disk_available
  mem_total="$(read_meminfo_value MemTotal)"
  mem_available="$(read_meminfo_value MemAvailable)"
  commit_limit="$(read_meminfo_value CommitLimit)"
  committed_as="$(read_meminfo_value Committed_AS)"
  commit_free=$((commit_limit - committed_as))
  disk_total="$(df -P "$ROOT_DIR" | awk 'NR == 2 { print $2 }')"
  disk_available="$(df -P "$ROOT_DIR" | awk 'NR == 2 { print $4 }')"

  log "INFO" "RAM available: ${mem_available} KiB of ${mem_total} KiB"
  log "INFO" "memory commit headroom: ${commit_free} KiB of ${commit_limit} KiB"
  log "INFO" "disk available for project: ${disk_available} KiB of ${disk_total} KiB"

  if (( mem_available * 100 < mem_total * RAM_MIN_FREE_PERCENT )); then
    log "WARN" "RAM available is below ${RAM_MIN_FREE_PERCENT}% reserve threshold"
    failed=1
  fi
  if (( commit_free * 100 < commit_limit * RESOURCE_RESERVE_PERCENT )); then
    log "WARN" "memory commit headroom is below ${RESOURCE_RESERVE_PERCENT}% reserve threshold"
    failed=1
  fi
  if (( disk_available * 100 < disk_total * DISK_MIN_FREE_PERCENT )); then
    log "WARN" "disk available is below ${DISK_MIN_FREE_PERCENT}% reserve threshold"
    failed=1
  fi
  return "$failed"
}

check_gpu_light() {
  if ! has_command nvidia-smi; then
    log "WARN" "nvidia-smi not found; GPU status unavailable"
    return 1
  fi
  log "INFO" "GPU summary"
  nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv 2>&1 | tee -a "$LOG_FILE"
  nvidia-smi pmon -c 1 2>&1 | tee -a "$LOG_FILE" || true

  local total free
  total="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n 1 | tr -d ' ')"
  free="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -n 1 | tr -d ' ')"
  if [[ -n "$total" && -n "$free" ]] && (( free * 100 < total * GPU_MIN_FREE_VRAM_PERCENT )); then
    log "WARN" "GPU free VRAM is below ${GPU_MIN_FREE_VRAM_PERCENT}% reserve threshold"
    return 1
  fi
}

check_docker_space() {
  if ! check_docker; then
    return 1
  fi
  log "INFO" "Docker disk usage"
  docker system df 2>&1 | tee -a "$LOG_FILE"
  log "INFO" "Active containers"
  docker ps --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}' 2>&1 | tee -a "$LOG_FILE"
  log "INFO" "Project-labeled containers"
  docker ps -a --filter "label=${PROJECT_DOCKER_LABEL}" --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}' 2>&1 | tee -a "$LOG_FILE"
}

print_container_dry_run() {
  local name="$1"
  local image="$2"
  local asset_dir="$3"
  local port="$4"
  local service_label="$5"
  if [[ -z "$image" ]]; then
    log "WARN" "${name} image is not set; export ${service_label}_CONTAINER_IMAGE before pull/start"
    return 1
  fi
  mkdir -p "$asset_dir"
  log "INFO" "dry-run pull command for ${name}:"
  printf 'docker pull %q\n' "$image" | tee -a "$LOG_FILE"
  log "INFO" "dry-run run command for ${name}:"
  printf 'docker run --name %q --label %q --label %q --add-host=host.docker.internal:host-gateway --publish %q:%q --mount type=bind,source=%q,target=/workspace/cache --memory %q --cpus %q --restart no %s %q\n' \
    "$name" \
    "$PROJECT_DOCKER_LABEL" \
    "com.facespeed.service=${service_label}" \
    "127.0.0.1:${port}" \
    "$port" \
    "$asset_dir" \
    "$CONTAINER_MEMORY_LIMIT" \
    "$CONTAINER_CPU_LIMIT" \
    "$GPU_DEVICE_FLAG" \
    "$image" | tee -a "$LOG_FILE"
}

print_container_rollback() {
  log "INFO" "project-scoped rollback commands:"
  printf 'docker stop %q %q\n' "$RIVA_CONTAINER_NAME" "$A2F_CONTAINER_NAME" | tee -a "$LOG_FILE"
  printf 'docker rm %q %q\n' "$RIVA_CONTAINER_NAME" "$A2F_CONTAINER_NAME" | tee -a "$LOG_FILE"
  log "INFO" "cache/volumes are kept by default; remove only after explicit confirmation"
}

run_container_dry_run() {
  log "INFO" "starting NVIDIA container command dry-run"
  check_ports
  check_resources
  check_gpu_light
  check_docker_space
  check_ngc || true
  print_container_dry_run "$RIVA_CONTAINER_NAME" "$RIVA_CONTAINER_IMAGE" "$RIVA_ASSET_DIR" "$RIVA_PORT" "riva" || true
  print_container_dry_run "$A2F_CONTAINER_NAME" "$A2F_CONTAINER_IMAGE" "$A2F_ASSET_DIR" "$A2F_PORT" "audio2face" || true
  print_container_rollback
  log "INFO" "dry-run only; no pull/start/stop/remove/cleanup was executed"
}

run_dry_run_nvidia_full() {
  log "INFO" "starting NVIDIA full dry-run preflight"
  check_ports
  check_resources
  check_gpu_light
  check_docker_space
  check_ngc || true
  log "INFO" "dry-run only; no container/image download/start/cleanup was executed"
}

check_ngc() {
  if has_command ngc; then
    log "INFO" "NGC CLI available"
    if ngc config current >/dev/null 2>&1; then
      log "INFO" "NGC CLI appears configured"
      return 0
    fi
    log "WARN" "NGC CLI found but not configured; run: ngc config set"
    return 1
  fi
  log "WARN" "NGC CLI not found"
  return 1
}

install_linux_base_packages() {
  if ! has_command apt-get; then
    log "WARN" "apt-get not found; skipping Linux package install"
    return 0
  fi
  if [[ "${EUID}" -ne 0 ]]; then
    log "WARN" "base package install requires sudo/root; rerun: sudo ./scripts/setup.sh --install"
    return 0
  fi
  apt-get update
  apt-get install -y curl git ca-certificates gnupg python3 python3-venv python3-pip docker.io
  log "INFO" "base Linux packages installed"
}

install_ngc() {
  log "INFO" "checking NGC CLI installation"
  if has_command ngc; then
    log "INFO" "NGC CLI already installed"
    return 0
  fi
  local platform
  platform="$(detect_platform)"
  log "WARN" "NGC CLI is required to download NVIDIA assets"
  if [[ "$platform" == "windows-git-bash" ]]; then
    log "WARN" "Install NGC CLI for Windows from NVIDIA NGC, then open a new shell and run: ngc config set"
  else
    log "WARN" "Install NGC CLI for Linux from NVIDIA NGC, then run: ngc config set"
  fi
  return 1
}

download_riva_quickstart() {
  log "INFO" "checking Riva quickstart at ${RIVA_QUICKSTART_DIR}"
  mkdir -p "$RIVA_QUICKSTART_DIR"
  if [[ -f "${RIVA_QUICKSTART_DIR}/riva_init.sh" && -f "${RIVA_QUICKSTART_DIR}/riva_start.sh" ]]; then
    log "INFO" "Riva quickstart scripts already present"
    return 0
  fi
  check_ngc || return 1
  if [[ -z "$NGC_RIVA_QUICKSTART_RESOURCE" ]]; then
    log "WARN" "NGC_RIVA_QUICKSTART_RESOURCE is not set, so setup cannot know which licensed Riva quickstart package to download"
    log "WARN" "Set it to the exact NGC resource/version for your Riva license, then rerun --install-riva"
    return 1
  fi
  log "INFO" "downloading Riva quickstart resource: ${NGC_RIVA_QUICKSTART_RESOURCE}"
  ngc registry resource download-version "$NGC_RIVA_QUICKSTART_RESOURCE" --dest "$RIVA_QUICKSTART_DIR"
  log "INFO" "Riva quickstart download command completed"
}

start_riva() {
  if [[ -x "${RIVA_QUICKSTART_DIR}/riva_init.sh" && -x "${RIVA_QUICKSTART_DIR}/riva_start.sh" ]]; then
    log "INFO" "initializing and starting Riva from ${RIVA_QUICKSTART_DIR}"
    (cd "$RIVA_QUICKSTART_DIR" && ./riva_init.sh && ./riva_start.sh)
    return 0
  fi
  if [[ -f "${RIVA_QUICKSTART_DIR}/riva_init.sh" && -f "${RIVA_QUICKSTART_DIR}/riva_start.sh" ]]; then
    chmod +x "${RIVA_QUICKSTART_DIR}/riva_init.sh" "${RIVA_QUICKSTART_DIR}/riva_start.sh"
    (cd "$RIVA_QUICKSTART_DIR" && ./riva_init.sh && ./riva_start.sh)
    return 0
  fi
  log "WARN" "Riva quickstart scripts not found in ${RIVA_QUICKSTART_DIR}"
  return 1
}

check_riva_container() {
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qi riva; then
    log "INFO" "Riva container appears to be running"
    return 0
  fi
  log "WARN" "Riva container not detected; install/start requires NVIDIA NGC assets"
  return 1
}

check_riva_tts() {
  log "INFO" "checking Riva TTS TCP ${RIVA_HOST}:${RIVA_PORT}"
  local py_cmd
  py_cmd="$(python_cmd)"
  if [[ -z "$py_cmd" ]]; then
    log "WARN" "python not found; cannot run Riva TCP check"
    return 1
  fi
  if RIVA_HOST="$RIVA_HOST" RIVA_PORT="$RIVA_PORT" "$py_cmd" - 2>>"$LOG_FILE" <<'PY'
import os
import socket
host = os.environ.get('RIVA_HOST', '127.0.0.1')
port = int(os.environ.get('RIVA_PORT', '50051'))
with socket.create_connection((host, port), timeout=5):
    pass
print(f'Riva TCP reachable at {host}:{port}')
PY
  then
    log "INFO" "Riva TCP port is reachable"
    return 0
  fi
  log "WARN" "Riva TCP port is not reachable at ${RIVA_HOST}:${RIVA_PORT}"
  return 1
}

check_audio2face() {
  if pgrep -x audio2face >/dev/null 2>&1 || pgrep -x Audio2Face >/dev/null 2>&1; then
    log "INFO" "Audio2Face process appears to be running"
    return 0
  fi
  if has_command curl && curl -fsS "http://${A2F_HOST}:${A2F_PORT}${A2F_HEALTH_PATH}" >/dev/null 2>&1; then
    log "INFO" "Audio2Face HTTP health endpoint is reachable"
    return 0
  fi
  log "WARN" "Audio2Face process/API not detected at ${A2F_HOST}:${A2F_PORT}${A2F_HEALTH_PATH}"
  log "WARN" "Install/start NVIDIA Audio2Face and expose its automation endpoint, then set A2F_HOST/A2F_PORT/A2F_HEALTH_PATH if needed"
  return 1
}

install_backend_deps() {
  local py_cmd
  py_cmd="$(python_cmd)"
  if [[ -z "$py_cmd" ]]; then
    log "WARN" "python not found; skipping backend dependency install"
    return 1
  fi
  local platform
  local venv_dir
  platform="$(detect_platform)"
  if [[ "$platform" == "windows-git-bash" ]]; then
    venv_dir="${ROOT_DIR}/backend/.venv"
    if [[ ! -d "$venv_dir" ]]; then
      "$py_cmd" -m venv "$venv_dir" || true
    fi
    if [[ -x "${venv_dir}/Scripts/python.exe" ]]; then
      if ! "${venv_dir}/Scripts/python.exe" -m pip install -r "${ROOT_DIR}/backend/requirements.txt"; then
        log "WARN" "backend dependency install failed in Windows venv"
        return 1
      fi
    elif ! "$py_cmd" -m pip install -r "${ROOT_DIR}/backend/requirements.txt"; then
      log "WARN" "backend dependency install failed with system python"
      return 1
    fi
  else
    venv_dir="${ROOT_DIR}/backend/.venv-linux"
    if [[ -d "$venv_dir" ]] && ! venv_python_is_supported "${venv_dir}/bin/python"; then
      log "WARN" "existing Linux venv uses unsupported Python; recreating project-local venv at ${venv_dir}"
      rm -r "$venv_dir"
    fi
    if [[ ! -d "$venv_dir" ]]; then
      if ! "$py_cmd" -m venv "$venv_dir"; then
        log "WARN" "failed to create Linux venv; install python3-venv, for example: sudo apt-get install -y python3-venv python3-pip"
        return 1
      fi
    fi
    if [[ -x "${venv_dir}/bin/python" ]]; then
      if ! "${venv_dir}/bin/python" -m pip install -r "${ROOT_DIR}/backend/requirements.txt"; then
        log "WARN" "backend dependency install failed in Linux venv"
        return 1
      fi
    elif ! "$py_cmd" -m pip install -r "${ROOT_DIR}/backend/requirements.txt"; then
      log "WARN" "backend dependency install failed with system python"
      return 1
    fi
  fi
  log "INFO" "backend dependencies installed"
}

install_frontend_deps() {
  if ! has_command npm; then
    log "WARN" "npm not found; skipping frontend dependency install"
    return 1
  fi
  (cd "${ROOT_DIR}/frontend" && npm install)
  log "INFO" "frontend dependencies installed"
}

run_check() {
  log "INFO" "starting system check on $(detect_platform)"
  check_command "bash" "bash" || true
  check_command "git" "git" || true
  check_command "curl" "curl" || true
  check_python || true
  check_command "node" "node" || true
  check_command "npm" "npm" || true
  check_docker || true
  check_ngc || true
  check_nvidia_gpu || true
  check_docker_gpu || true
  check_ports || true
  check_resources || true
  check_gpu_light || true
  check_docker_space || true
  check_riva_container || true
  check_riva_tts || true
  check_audio2face || true
  log "INFO" "system check completed"
}

run_install() {
  log "INFO" "starting local dependency install"
  install_linux_base_packages || true
  install_backend_deps || true
  install_frontend_deps || true
  log "INFO" "local dependency install completed"
}

run_auto() {
  log "INFO" "starting auto setup"
  run_check
  run_install
  install_ngc || true
  download_riva_quickstart || true
  start_riva || true
  check_riva_container || true
  check_riva_tts || true
  check_audio2face || true
  log "INFO" "auto setup completed; if WARN remains for NGC/Riva/A2F, follow the exact WARN instructions above"
}

run_start_services() {
  log "INFO" "starting configured local services"
  if [[ -f "${ROOT_DIR}/docker-compose.yml" ]] && has_command docker; then
    docker compose -f "${ROOT_DIR}/docker-compose.yml" up -d
    log "INFO" "docker compose services started"
  else
    log "WARN" "docker-compose.yml not found; no docker compose services started"
  fi
}

case "$MODE" in
  --auto)
    run_auto
    ;;
  --check|--check-nvidia)
    run_check
    ;;
  --check-ports)
    check_ports
    ;;
  --check-resources)
    check_resources
    ;;
  --check-gpu-light)
    check_gpu_light
    ;;
  --check-docker-space)
    check_docker_space
    ;;
  --dry-run-nvidia-full)
    run_dry_run_nvidia_full
    ;;
  --dry-run-containers)
    run_container_dry_run
    ;;
  --install)
    run_install
    ;;
  --install-ngc)
    install_ngc
    ;;
  --install-riva)
    download_riva_quickstart
    ;;
  --start-riva)
    start_riva
    ;;
  --check-riva)
    check_riva_container || true
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
    install_ngc || true
    download_riva_quickstart
    start_riva
    check_riva_tts
    check_audio2face || true
    ;;
  *)
    log "ERROR" "unknown mode: ${MODE}. Use --auto, --check, --check-nvidia, --check-ports, --check-resources, --check-gpu-light, --check-docker-space, --dry-run-nvidia-full, --dry-run-containers, --install, --install-ngc, --install-riva, --start-riva, --check-riva, --check-a2f, --start-services, --full, or --nvidia-full"
    exit 2
    ;;
esac
