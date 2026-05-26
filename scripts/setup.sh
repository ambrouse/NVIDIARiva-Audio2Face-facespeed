#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

load_env_defaults() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return 0
  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    if [[ -z "${!key+x}" ]]; then
      export "$key=$value"
    fi
  done < "$env_file"
}

load_env_defaults "${ROOT_DIR}/.env"

LOG_FILE="/dev/null"
MODE="${1:---auto}"
RUNTIME_DIR="${ROOT_DIR}/logs/runtime"
BACKEND_PID_FILE="${RUNTIME_DIR}/backend.pid"
FRONTEND_PID_FILE="${RUNTIME_DIR}/frontend.pid"
RIVA_QUICKSTART_DIR="${RIVA_QUICKSTART_DIR:-${ROOT_DIR}/.cache/nvidia/riva/riva_quickstart_v2.19.0}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-6320}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-6310}"
FACESPEED_PROXY_HOST="${FACESPEED_PROXY_HOST:-127.0.0.1}"
FACESPEED_PROXY_PORT="${FACESPEED_PROXY_PORT:-6300}"
TMUX_PREFIX="${TMUX_PREFIX:-facespeed-riva}"
TMUX_DOCKER_SESSION="${TMUX_DOCKER_SESSION:-${TMUX_PREFIX}-docker}"
TMUX_BACKEND_SESSION="${TMUX_BACKEND_SESSION:-${TMUX_PREFIX}-backend}"
TMUX_FRONTEND_SESSION="${TMUX_FRONTEND_SESSION:-${TMUX_PREFIX}-frontend}"
TMUX_RIVA_TTS_SESSION="${TMUX_RIVA_TTS_SESSION:-${TMUX_PREFIX}-tts}"
TMUX_RIVA_ASR_SESSION="${TMUX_RIVA_ASR_SESSION:-${TMUX_PREFIX}-asr}"
PROJECT_COMPOSE_NAME="${PROJECT_COMPOSE_NAME:-nvidiariva-audio2face-facespeed}"
RIVA_HOST="${RIVA_HOST:-127.0.0.1}"
RIVA_PORT="${RIVA_PORT:-6051}"
RIVA_ASR_HOST="${RIVA_ASR_HOST:-127.0.0.1}"
RIVA_ASR_PORT="${RIVA_ASR_PORT:-6052}"
A2F_HOST="${A2F_HOST:-127.0.0.1}"
A2F_PORT="${A2F_PORT:-6040}"
A2F_HTTP_PORT="${A2F_HTTP_PORT:-6041}"
A2F_HEALTH_PATH="${A2F_HEALTH_PATH:-/health}"
CUDA_TEST_IMAGE="${CUDA_TEST_IMAGE:-nvidia/cuda:12.4.1-base-ubuntu22.04}"
NGC_RIVA_QUICKSTART_RESOURCE="${NGC_RIVA_QUICKSTART_RESOURCE:-}"
RESOURCE_RESERVE_PERCENT="${RESOURCE_RESERVE_PERCENT:-10}"
GPU_MIN_FREE_VRAM_PERCENT="${GPU_MIN_FREE_VRAM_PERCENT:-${RESOURCE_RESERVE_PERCENT}}"
PROJECT_VRAM_EXPECTED_MIB="${PROJECT_VRAM_EXPECTED_MIB:-4000}"
PROJECT_VRAM_RECOMMENDED_FREE_MIB="${PROJECT_VRAM_RECOMMENDED_FREE_MIB:-9000}"
RAM_MIN_FREE_PERCENT="${RAM_MIN_FREE_PERCENT:-${RESOURCE_RESERVE_PERCENT}}"
DISK_MIN_FREE_PERCENT="${DISK_MIN_FREE_PERCENT:-${RESOURCE_RESERVE_PERCENT}}"
PROJECT_DOCKER_LABEL="${PROJECT_DOCKER_LABEL:-com.facespeed.project=NVIDIARiva-Audio2Face-facespeed}"
RIVA_CONTAINER_NAME="${RIVA_CONTAINER_NAME:-facespeed-riva}"
A2F_CONTAINER_NAME="${A2F_CONTAINER_NAME:-facespeed-audio2face-3d}"
RIVA_CONTAINER_IMAGE="${RIVA_CONTAINER_IMAGE:-}"
A2F_CONTAINER_IMAGE="${A2F_CONTAINER_IMAGE:-nvcr.io/nim/nvidia/audio2face-3d:2.0}"
RIVA_ASSET_DIR="${RIVA_ASSET_DIR:-${ROOT_DIR}/.cache/nvidia/riva}"
RIVA_TTS_CONFIG="${RIVA_TTS_CONFIG:-${ROOT_DIR}/.cache/nvidia/riva/config-facespeed-tts-6051.sh}"
RIVA_ASR_CONFIG="${RIVA_ASR_CONFIG:-${ROOT_DIR}/.cache/nvidia/riva/config-facespeed-asr-6052.sh}"
A2F_ASSET_DIR="${A2F_ASSET_DIR:-${ROOT_DIR}/.cache/nvidia/audio2face}"
A2F_CONTAINER_GRPC_PORT="${A2F_CONTAINER_GRPC_PORT:-52000}"
A2F_CONTAINER_HTTP_PORT="${A2F_CONTAINER_HTTP_PORT:-8000}"
A2F_NIM_DISABLE_MODEL_DOWNLOAD="${A2F_NIM_DISABLE_MODEL_DOWNLOAD:-false}"
A2F_MODEL="${A2F_MODEL:-james_v2.3.1}"
NIM_MANIFEST_PROFILE="${NIM_MANIFEST_PROFILE:-}"
CONTAINER_MEMORY_LIMIT="${CONTAINER_MEMORY_LIMIT:-16g}"
CONTAINER_CPU_LIMIT="${CONTAINER_CPU_LIMIT:-8}"
GPU_DEVICE_FLAG="${GPU_DEVICE_FLAG:---gpus device=0}"

for path_var in RIVA_QUICKSTART_DIR RIVA_ASSET_DIR RIVA_TTS_CONFIG RIVA_ASR_CONFIG A2F_ASSET_DIR; do
  case "${!path_var}" in
    /*) ;;
    *) printf -v "$path_var" '%s/%s' "$ROOT_DIR" "${!path_var}" ;;
  esac
done

mkdir -p "$RUNTIME_DIR"

log() {
  local level="$1"
  local message="$2"
  printf '[%s] %s\n' "$level" "$message"
}

has_command() {
  command -v "$1" >/dev/null 2>&1
}

require_tmux() {
  if has_command tmux; then
    return 0
  fi
  log "ERROR" "tmux is required for --run/--setup-run. Install tmux, then rerun the command."
  return 1
}

tmux_has_session() {
  local session="$1"
  has_command tmux && tmux has-session -t "$session" >/dev/null 2>&1
}

tmux_start_session() {
  local session="$1"
  local workdir="$2"
  local command="$3"
  if tmux_has_session "$session"; then
    log "INFO" "tmux session ${session} already exists"
    return 0
  fi
  tmux new-session -d -s "$session" -c "$workdir" "$command"
  log "INFO" "started tmux session ${session}"
}

tmux_stop_project_sessions() {
  if ! has_command tmux; then
    return 0
  fi
  local sessions session
  mapfile -t sessions < <(tmux list-sessions -F '#S' 2>/dev/null | grep -E "^${TMUX_PREFIX}($|-)" || true)
  if (( ${#sessions[@]} == 0 )); then
    log "INFO" "no ${TMUX_PREFIX} tmux sessions to stop"
    return 0
  fi
  for session in "${sessions[@]}"; do
    log "INFO" "stopping tmux session ${session}"
    tmux kill-session -t "$session" >/dev/null 2>&1 || true
  done
}

print_tmux_summary() {
  cat <<EOF

Tmux sessions for this project:
  ${TMUX_DOCKER_SESSION}    docker compose: nginx proxy + Postgres + Qdrant
  ${TMUX_RIVA_TTS_SESSION}  Riva TTS on ${RIVA_HOST}:${RIVA_PORT}
  ${TMUX_RIVA_ASR_SESSION}  Riva ASR on ${RIVA_ASR_HOST:-127.0.0.1}:${RIVA_ASR_PORT:-6052}
  ${TMUX_BACKEND_SESSION}   FastAPI backend on http://${BACKEND_HOST}:${BACKEND_PORT}
  ${TMUX_FRONTEND_SESSION}  Vite frontend on http://${FRONTEND_HOST}:${FRONTEND_PORT}

Open:
  http://${FACESPEED_PROXY_HOST}:${FACESPEED_PROXY_PORT}/

Attach examples:
  tmux attach -t ${TMUX_RIVA_TTS_SESSION}
  tmux attach -t ${TMUX_RIVA_ASR_SESSION}
  tmux attach -t ${TMUX_BACKEND_SESSION}
  tmux attach -t ${TMUX_FRONTEND_SESSION}
  tmux attach -t ${TMUX_DOCKER_SESSION}
EOF
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
  check_single_port "riva-tts" "$RIVA_HOST" "$RIVA_PORT" || failed=1
  check_single_port "riva-asr" "$RIVA_ASR_HOST" "$RIVA_ASR_PORT" || failed=1
  check_single_port "audio2face-grpc" "$A2F_HOST" "$A2F_PORT" || failed=1
  check_single_port "audio2face-http" "$A2F_HOST" "$A2F_HTTP_PORT" || failed=1
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
  if [[ -n "$free" ]] && (( free < PROJECT_VRAM_RECOMMENDED_FREE_MIB )); then
    log "WARN" "GPU free VRAM is ${free} MiB; recommended free before FaceSpeed start is ${PROJECT_VRAM_RECOMMENDED_FREE_MIB} MiB"
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
  local container_port="${6:-$4}"
  if [[ -z "$image" ]]; then
    local image_env="RIVA_CONTAINER_IMAGE"
    if [[ "$service_label" == "audio2face" ]]; then
      image_env="A2F_CONTAINER_IMAGE"
    fi
    log "WARN" "${name} image is not set; export ${image_env} before pull/start"
    return 1
  fi
  mkdir -p "$asset_dir"
  log "INFO" "dry-run pull command for ${name}:"
  printf 'docker pull %q\n' "$image" | tee -a "$LOG_FILE"
  log "INFO" "dry-run run command for ${name}:"
  if [[ "$service_label" == "audio2face" ]]; then
    printf 'docker run -d --name %q --label %q --label %q --add-host=host.docker.internal:host-gateway --publish %q:%q --publish %q:%q --mount type=bind,source=%q,target=/opt/nim/.cache --memory %q --cpus %q --restart no %s -e NGC_API_KEY -e NIM_MODEL_NAME=%q -e NIM_DISABLE_MODEL_DOWNLOAD=%q %q\n' \
      "$name" \
      "$PROJECT_DOCKER_LABEL" \
      "com.facespeed.service=${service_label}" \
      "127.0.0.1:${port}" \
      "$container_port" \
      "127.0.0.1:${A2F_HTTP_PORT}" \
      "$A2F_CONTAINER_HTTP_PORT" \
      "$asset_dir" \
      "$CONTAINER_MEMORY_LIMIT" \
      "$CONTAINER_CPU_LIMIT" \
      "$GPU_DEVICE_FLAG" \
      "$A2F_MODEL" \
      "$A2F_NIM_DISABLE_MODEL_DOWNLOAD" \
      "$image" | tee -a "$LOG_FILE"
    return 0
  fi
  printf 'docker run --name %q --label %q --label %q --add-host=host.docker.internal:host-gateway --publish %q:%q --mount type=bind,source=%q,target=/workspace/cache --memory %q --cpus %q --restart no %s %q\n' \
    "$name" \
    "$PROJECT_DOCKER_LABEL" \
    "com.facespeed.service=${service_label}" \
    "127.0.0.1:${port}" \
    "$container_port" \
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

project_container_ids() {
  local scope="${1:---running}"
  local docker_args=(ps -q)
  if [[ "$scope" == "--all" ]]; then
    docker_args=(ps -aq)
  fi
  local cid info
  for cid in $(docker "${docker_args[@]}" 2>/dev/null); do
    info="$(docker inspect "$cid" --format 'NAME={{.Name}} PROJECT={{index .Config.Labels "com.docker.compose.project"}} LABEL={{index .Config.Labels "com.facespeed.project"}} MOUNTS={{range .Mounts}}{{.Source}};{{end}}' 2>/dev/null || true)"
    if printf '%s' "$info" | grep -Fq "$ROOT_DIR" \
      || printf '%s' "$info" | grep -Fq "PROJECT=${PROJECT_COMPOSE_NAME}" \
      || printf '%s' "$info" | grep -Fq "LABEL=NVIDIARiva-Audio2Face-facespeed"; then
      printf '%s\n' "$cid"
    fi
  done | sort -u
}

list_project_containers() {
  if ! check_docker; then
    return 1
  fi
  log "INFO" "project containers by label, compose project, or repo bind mount"
  project_container_ids --all | while read -r cid; do
    [[ -n "$cid" ]] || continue
    docker ps -a --filter "id=$cid" --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}'
  done | awk 'NR == 1 || !seen[$0]++'
}

stop_project_containers() {
  if ! check_docker; then
    return 1
  fi
  if [[ -f "${ROOT_DIR}/docker-compose.yml" ]]; then
    log "INFO" "stopping docker compose project ${PROJECT_COMPOSE_NAME}"
    docker compose -p "$PROJECT_COMPOSE_NAME" -f "${ROOT_DIR}/docker-compose.yml" down --remove-orphans >/dev/null 2>&1 || true
  fi
  mapfile -t ids < <(project_container_ids --all)
  if (( ${#ids[@]} == 0 )); then
    log "INFO" "no project Docker containers to clear"
    return 0
  fi
  log "INFO" "clearing project Docker containers: ${ids[*]}"
  local running_ids=()
  local cid
  for cid in "${ids[@]}"; do
    if docker inspect -f '{{.State.Running}}' "$cid" 2>/dev/null | grep -qx true; then
      running_ids+=("$cid")
    fi
  done
  if (( ${#running_ids[@]} > 0 )); then
    docker stop "${running_ids[@]}" >/dev/null 2>&1 || true
  fi
  docker rm "${ids[@]}" >/dev/null 2>&1 || true
}

run_container_dry_run() {
  log "INFO" "starting NVIDIA container command dry-run"
  check_ports || true
  check_resources || true
  check_gpu_light || true
  check_docker_space || true
  check_ngc || true
  print_container_dry_run "$RIVA_CONTAINER_NAME" "$RIVA_CONTAINER_IMAGE" "$RIVA_ASSET_DIR" "$RIVA_PORT" "riva" || true
  print_container_dry_run "$A2F_CONTAINER_NAME" "$A2F_CONTAINER_IMAGE" "$A2F_ASSET_DIR" "$A2F_PORT" "audio2face" "$A2F_CONTAINER_GRPC_PORT" || true
  print_container_rollback
  log "INFO" "dry-run only; no pull/start/stop/remove/cleanup was executed"
}

run_a2f_profile_list() {
  if ! check_docker; then
    return 1
  fi
  log "INFO" "listing Audio2Face-3D NIM model profiles for ${A2F_CONTAINER_IMAGE}"
  docker run --rm --gpus all \
    --entrypoint nim_list_model_profiles \
    "$A2F_CONTAINER_IMAGE" 2>&1 | tee -a "$LOG_FILE"
}

start_a2f_nim() {
  if [[ -z "$A2F_CONTAINER_IMAGE" ]]; then
    log "ERROR" "A2F_CONTAINER_IMAGE is not set"
    return 1
  fi
  check_ports
  check_resources
  check_gpu_light
  check_docker_space
  if [[ "$A2F_NIM_DISABLE_MODEL_DOWNLOAD" != "true" && -z "${NGC_API_KEY:-}" ]]; then
    log "ERROR" "NGC_API_KEY is required to start Audio2Face-3D NIM when model download is enabled"
    return 1
  fi
  if docker ps -a --format '{{.Names}}' | grep -qx "$A2F_CONTAINER_NAME"; then
    log "ERROR" "container ${A2F_CONTAINER_NAME} already exists; stop/remove it manually after confirming it is project-owned"
    return 1
  fi

  mkdir -p "$A2F_ASSET_DIR"
  read -r -a gpu_args <<< "$GPU_DEVICE_FLAG"
  local profile_args=()
  if [[ -n "$NIM_MANIFEST_PROFILE" ]]; then
    profile_args=(-e "NIM_MANIFEST_PROFILE=${NIM_MANIFEST_PROFILE}")
  fi
  local ngc_args=()
  if [[ -n "${NGC_API_KEY:-}" ]]; then
    ngc_args=(-e NGC_API_KEY)
  fi

  log "INFO" "starting Audio2Face-3D NIM ${A2F_CONTAINER_NAME} on localhost gRPC ${A2F_PORT}->${A2F_CONTAINER_GRPC_PORT}, HTTP ${A2F_HTTP_PORT}->${A2F_CONTAINER_HTTP_PORT}"
  docker run -d \
    --name "$A2F_CONTAINER_NAME" \
    --label "$PROJECT_DOCKER_LABEL" \
    --label "com.facespeed.service=audio2face" \
    --add-host=host.docker.internal:host-gateway \
    --publish "127.0.0.1:${A2F_PORT}:${A2F_CONTAINER_GRPC_PORT}" \
    --publish "127.0.0.1:${A2F_HTTP_PORT}:${A2F_CONTAINER_HTTP_PORT}" \
    --mount "type=bind,source=${A2F_ASSET_DIR},target=/opt/nim/.cache" \
    --memory "$CONTAINER_MEMORY_LIMIT" \
    --cpus "$CONTAINER_CPU_LIMIT" \
    --restart no \
    "${gpu_args[@]}" \
    "${ngc_args[@]}" \
    -e "NIM_MODEL_NAME=${A2F_MODEL}" \
    -e "NIM_DISABLE_MODEL_DOWNLOAD=${A2F_NIM_DISABLE_MODEL_DOWNLOAD}" \
    "${profile_args[@]}" \
    "$A2F_CONTAINER_IMAGE" 2>&1 | tee -a "$LOG_FILE"
}

run_dry_run_nvidia_full() {
  log "INFO" "starting NVIDIA full dry-run preflight"
  check_ports || true
  check_resources || true
  check_gpu_light || true
  check_docker_space || true
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

ensure_env_file() {
  local env_file="${ROOT_DIR}/.env"
  local env_example="${ROOT_DIR}/.env.example"
  if [[ -f "$env_file" ]]; then
    log "INFO" ".env already exists; keeping local runtime configuration"
    return 0
  fi
  if [[ ! -f "$env_example" ]]; then
    log "WARN" ".env.example not found; cannot create default .env"
    return 1
  fi
  cp "$env_example" "$env_file"
  log "INFO" "created .env from .env.example for provider-backed main path"
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
  start_riva_service "Riva TTS" "$TMUX_RIVA_TTS_SESSION" "$RIVA_TTS_CONFIG" "$RIVA_HOST" "$RIVA_PORT" || true
  start_riva_service "Riva ASR" "$TMUX_RIVA_ASR_SESSION" "$RIVA_ASR_CONFIG" "$RIVA_ASR_HOST" "$RIVA_ASR_PORT" || true
}

start_riva_service() {
  local label="$1"
  local session="$2"
  local config_path="$3"
  local host="$4"
  local port="$5"
  require_tmux || return 1
  if tcp_reachable "$host" "$port"; then
    log "INFO" "${label} already reachable at ${host}:${port}"
    return 0
  fi
  if [[ ! -x "${RIVA_QUICKSTART_DIR}/riva_start.sh" || ! -x "${RIVA_QUICKSTART_DIR}/riva_init.sh" ]]; then
    if [[ -f "${RIVA_QUICKSTART_DIR}/riva_start.sh" && -f "${RIVA_QUICKSTART_DIR}/riva_init.sh" ]]; then
      chmod +x "${RIVA_QUICKSTART_DIR}/riva_start.sh" "${RIVA_QUICKSTART_DIR}/riva_init.sh"
    else
      log "WARN" "Riva quickstart scripts not found in ${RIVA_QUICKSTART_DIR}"
      return 1
    fi
  fi
  if [[ ! -f "$config_path" ]]; then
    log "WARN" "${label} config not found: ${config_path}"
    return 1
  fi

  local config_q label_q
  printf -v config_q '%q' "$config_path"
  printf -v label_q '%q' "$label"
  log "INFO" "starting ${label} in tmux session ${session}"
  tmux_start_session "$session" "$RIVA_QUICKSTART_DIR" \
    "set -euo pipefail; config=${config_q}; source \"\$config\"; if [ ! -d \"\$riva_model_loc/models\" ] || [ -z \"\$(find \"\$riva_model_loc/models\" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -n 1)\" ]; then ./riva_init.sh \"\$config\"; fi; ./riva_start.sh \"\$config\"; printf '\n%s finished. Keep this tmux session for logs.\n' ${label_q}; exec bash"
  wait_for_tcp "$label" "$host" "$port" 120 2 || return 1
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
  if tcp_reachable "$RIVA_HOST" "$RIVA_PORT"; then
    log "INFO" "Riva TCP port is reachable"
    return 0
  fi
  log "WARN" "Riva TCP port is not reachable at ${RIVA_HOST}:${RIVA_PORT}"
  return 1
}

check_riva_asr() {
  log "INFO" "checking Riva ASR TCP ${RIVA_ASR_HOST}:${RIVA_ASR_PORT}"
  if tcp_reachable "$RIVA_ASR_HOST" "$RIVA_ASR_PORT"; then
    log "INFO" "Riva ASR TCP port is reachable"
    return 0
  fi
  log "WARN" "Riva ASR TCP port is not reachable at ${RIVA_ASR_HOST}:${RIVA_ASR_PORT}"
  return 1
}

check_audio2face() {
  if docker ps --filter "name=^/${A2F_CONTAINER_NAME}$" --filter "label=${PROJECT_DOCKER_LABEL}" --format '{{.Names}}' 2>/dev/null | grep -qx "$A2F_CONTAINER_NAME"; then
    log "INFO" "Audio2Face-3D project container is running"
  elif pgrep -x audio2face >/dev/null 2>&1 || pgrep -x Audio2Face >/dev/null 2>&1; then
    log "INFO" "Audio2Face process appears to be running"
  fi
  if has_command curl && curl -fsS "http://${A2F_HOST}:${A2F_HTTP_PORT}${A2F_HEALTH_PATH}" >/dev/null 2>&1; then
    log "INFO" "Audio2Face-3D HTTP health endpoint is reachable at ${A2F_HOST}:${A2F_HTTP_PORT}${A2F_HEALTH_PATH}"
    return 0
  fi
  local py_cmd
  py_cmd="$(python_cmd)"
  if [[ -n "$py_cmd" ]] && A2F_HOST="$A2F_HOST" A2F_PORT="$A2F_PORT" "$py_cmd" - 2>>"$LOG_FILE" <<'PY'
import os
import socket
host = os.environ.get("A2F_HOST", "127.0.0.1")
port = int(os.environ.get("A2F_PORT", "6040"))
with socket.create_connection((host, port), timeout=5):
    pass
print(f"Audio2Face-3D gRPC TCP reachable at {host}:{port}")
PY
  then
    log "INFO" "Audio2Face-3D gRPC TCP port is reachable"
    return 0
  fi
  log "WARN" "Audio2Face-3D not detected at gRPC ${A2F_HOST}:${A2F_PORT} or HTTP ${A2F_HOST}:${A2F_HTTP_PORT}${A2F_HEALTH_PATH}"
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
  check_riva_asr || true
  check_audio2face || true
  log "INFO" "system check completed"
}

run_install() {
  log "INFO" "starting local dependency install"
  ensure_env_file || true
  install_linux_base_packages || true
  install_backend_deps || true
  install_frontend_deps || true
  log "INFO" "local dependency install completed"
}

backend_python() {
  local platform
  platform="$(detect_platform)"
  if [[ "$platform" == "windows-git-bash" && -x "${ROOT_DIR}/backend/.venv/Scripts/python.exe" ]]; then
    echo "${ROOT_DIR}/backend/.venv/Scripts/python.exe"
    return 0
  fi
  if [[ -x "${ROOT_DIR}/backend/.venv-linux/bin/python" ]]; then
    echo "${ROOT_DIR}/backend/.venv-linux/bin/python"
    return 0
  fi
  python_cmd
}

http_ok() {
  local url="$1"
  if has_command curl && curl -fsS "$url" >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

tcp_reachable() {
  local host="$1"
  local port="$2"
  local py_cmd
  py_cmd="$(python_cmd)"
  [[ -n "$py_cmd" ]] || return 1
  TCP_HOST="$host" TCP_PORT="$port" "$py_cmd" - <<'PY' >/dev/null 2>&1
import os
import socket
host = os.environ["TCP_HOST"]
port = int(os.environ["TCP_PORT"])
with socket.create_connection((host, port), timeout=3):
    pass
PY
}

pid_is_alive() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

wait_for_http() {
  local label="$1"
  local url="$2"
  local attempts="${3:-40}"
  local delay="${4:-0.5}"
  local i spin_index=0
  local spin='|/-\'
  for ((i = 1; i <= attempts; i += 1)); do
    if http_ok "$url"; then
      printf '\r[OK] %s is reachable at %s%*s\n' "$label" "$url" 12 ""
      log "INFO" "${label} is reachable at ${url}"
      return 0
    fi
    printf '\r[WAIT] %s %s' "$label" "${spin:spin_index++%4:1}"
    sleep "$delay"
  done
  printf '\r[WARN] %s did not become reachable at %s%*s\n' "$label" "$url" 12 ""
  log "WARN" "${label} did not become reachable at ${url}"
  return 1
}

wait_for_tcp() {
  local label="$1"
  local host="$2"
  local port="$3"
  local attempts="${4:-90}"
  local delay="${5:-2}"
  local i spin_index=0
  local spin='|/-\'
  for ((i = 1; i <= attempts; i += 1)); do
    if tcp_reachable "$host" "$port"; then
      printf '\r[OK] %s is reachable at %s:%s%*s\n' "$label" "$host" "$port" 12 ""
      log "INFO" "${label} is reachable at ${host}:${port}"
      return 0
    fi
    printf '\r[WAIT] %s %s' "$label" "${spin:spin_index++%4:1}"
    sleep "$delay"
  done
  printf '\r[WARN] %s did not become reachable at %s:%s%*s\n' "$label" "$host" "$port" 12 ""
  log "WARN" "${label} did not become reachable at ${host}:${port}"
  return 1
}

start_backend_app() {
  require_tmux || return 1
  local health_url="http://${BACKEND_HOST}:${BACKEND_PORT}/health"
  if http_ok "$health_url"; then
    log "INFO" "backend already reachable at ${health_url}"
    return 0
  fi
  local py_cmd
  py_cmd="$(backend_python)"
  if [[ -z "$py_cmd" ]]; then
    log "WARN" "python not found; cannot start backend"
    return 1
  fi
  if [[ ! -f "${ROOT_DIR}/backend/requirements.txt" ]]; then
    log "WARN" "backend requirements not found"
    return 1
  fi
  log "INFO" "starting backend on ${BACKEND_HOST}:${BACKEND_PORT} in tmux session ${TMUX_BACKEND_SESSION}"
  tmux_start_session "$TMUX_BACKEND_SESSION" "$ROOT_DIR" \
    "env BACKEND_HOST='${BACKEND_HOST}' BACKEND_PORT='${BACKEND_PORT}' FRONTEND_PORT='${FRONTEND_PORT}' ALLOWED_ORIGINS='${ALLOWED_ORIGINS:-http://${FRONTEND_HOST}:${FRONTEND_PORT},http://localhost:${FRONTEND_PORT}}' '${py_cmd}' -m uvicorn src.main:app --host '${BACKEND_HOST}' --port '${BACKEND_PORT}' --app-dir backend"
  wait_for_http "backend" "$health_url" 50 0.4 || return 1
}

start_frontend_app() {
  require_tmux || return 1
  local frontend_url="http://${FRONTEND_HOST}:${FRONTEND_PORT}/"
  if http_ok "$frontend_url"; then
    log "INFO" "frontend already reachable at ${frontend_url}"
    return 0
  fi
  if ! has_command npm; then
    log "WARN" "npm not found; cannot start frontend"
    return 1
  fi
  if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
    log "WARN" "frontend/node_modules missing; run ./setup.sh --setup first"
    return 1
  fi
  log "INFO" "starting frontend on ${FRONTEND_HOST}:${FRONTEND_PORT} in tmux session ${TMUX_FRONTEND_SESSION}"
  tmux_start_session "$TMUX_FRONTEND_SESSION" "$ROOT_DIR" \
    "env VITE_API_BASE_URL='${VITE_API_BASE_URL:-}' npm --prefix frontend run dev -- --host '${FRONTEND_HOST}' --port '${FRONTEND_PORT}' --strictPort"
  wait_for_http "frontend" "$frontend_url" 50 0.4 || return 1
}

run_app() {
  log "INFO" "starting FaceSpeed app"
  stop_project_core || true
  run_start_services || true
  check_ports || true
  check_resources || true
  check_gpu_light || true
  start_riva || true
  check_riva_tts || true
  check_riva_asr || true
  check_audio2face || true
  start_backend_app || true
  start_frontend_app || true
  wait_for_http "nginx proxy" "http://${FACESPEED_PROXY_HOST}:${FACESPEED_PROXY_PORT}/" 30 0.5 || true
  print_project_status
  print_tmux_summary
}

run_setup_run() {
  log "INFO" "starting one-command setup + run"
  stop_project_core || true
  run_check || true
  run_install || true
  run_app || true
  log "INFO" "setup + run completed with warnings allowed; review WARN lines above if a NVIDIA service is unavailable"
}

print_support_matrix() {
  cat <<'SUPPORT'
FaceSpeed machine support

Supported target:
  Linux workstation, NVIDIA RTX GPU, recent NVIDIA driver, Docker with GPU access,
  Python 3.10+, Node 20+, npm, terminal, and network.

Best effort:
  WSL2 with NVIDIA GPU passthrough and Docker Desktop, only when nvidia-smi,
  docker run --gpus all, ports, RAM, disk, and provider checks pass.

Development only:
  CPU-only Linux/macOS/Windows can run source tests/build and inspect UI, but
  the provider-backed Riva/Docling/embedding main path will be incomplete.

Unsupported:
  Machines without terminal/network, unsupported GPU drivers, unreachable Docker
  daemon, missing Python/Node with no install rights, or no licensed NVIDIA/NGC
  access for NVIDIA services.
SUPPORT
}

run_verify() {
  log "INFO" "starting release verification"
  run_check || true
  (cd "$ROOT_DIR" && npm --prefix frontend test -- --run)
  (cd "$ROOT_DIR" && npm --prefix frontend run build)
  local py_cmd
  py_cmd="$(backend_python)"
  if [[ -z "$py_cmd" ]]; then
    log "ERROR" "python not found; cannot run backend tests"
    return 1
  fi
  (cd "$ROOT_DIR" && "$py_cmd" -m pytest tests)
  log "INFO" "release verification completed"
}

run_capture_demo() {
  log "INFO" "capturing release GIF demo"
  if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
    install_frontend_deps
  fi
  if [[ ! -d "${ROOT_DIR}/backend/.venv-linux" && "$(detect_platform)" != "windows-git-bash" ]]; then
    install_backend_deps || true
  fi
  (cd "$ROOT_DIR" && node scripts/capture-release-demo.mjs)
  log "INFO" "release GIF demo captured"
}

run_logs_clean() {
  log "INFO" "cleaning disposable runtime logs"
  (cd "$ROOT_DIR" && bash scripts/manage-logs.sh --clean)
}

stop_pid_file() {
  local label="$1"
  local pid_file="$2"
  if ! pid_is_alive "$pid_file"; then
    rm -f "$pid_file"
    log "INFO" "${label} process not running from pid file"
    return 0
  fi
  local pid
  pid="$(cat "$pid_file")"
  local cmdline
  cmdline="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  if [[ "$cmdline" != *"$ROOT_DIR"* && "$cmdline" != *"uvicorn src.main:app"* && "$cmdline" != *"vite"* && "$cmdline" != *"npm run dev"* ]]; then
    log "WARN" "refusing to stop ${label} pid ${pid}; command is not clearly project-owned"
    return 1
  fi
  log "INFO" "stopping ${label} pid ${pid}"
  kill "$pid" >/dev/null 2>&1 || true
  sleep 1
  if kill -0 "$pid" >/dev/null 2>&1; then
    log "WARN" "${label} pid ${pid} still running; sending SIGKILL"
    kill -9 "$pid" >/dev/null 2>&1 || true
  fi
  rm -f "$pid_file"
}

stop_project_processes() {
  stop_project_runtime_pids || true
  stop_pid_file "backend" "$BACKEND_PID_FILE" || true
  stop_pid_file "frontend" "$FRONTEND_PID_FILE" || true
  stop_project_port_owner "backend-port" "$BACKEND_PORT" || true
  stop_project_port_owner "frontend-port" "$FRONTEND_PORT" || true
}

stop_project_runtime_pids() {
  local pids=()
  local d pid cwd cmd state
  for d in /proc/[0-9]*; do
    pid="${d##*/}"
    cwd="$(readlink -f "$d/cwd" 2>/dev/null || true)"
    [[ -n "$cwd" ]] || continue
    case "$cwd" in
      "$ROOT_DIR"|"$ROOT_DIR"/*)
        cmd="$(tr '\0' ' ' < "$d/cmdline" 2>/dev/null || true)"
        case "$cmd" in
          *"uvicorn src.main:app"*|*"npm run dev"*|*"/frontend/node_modules/.bin/vite"*|*"tests/benchmarks/http_bridge.py"*|*"tests/benchmarks/tcp_bridge.py"*)
            pids+=("$pid")
            ;;
        esac
        ;;
    esac
  done
  if (( ${#pids[@]} == 0 )); then
    log "INFO" "no project runtime processes found by cwd scan"
    return 0
  fi
  log "INFO" "stopping project runtime PIDs: ${pids[*]}"
  kill -TERM "${pids[@]}" >/dev/null 2>&1 || true
  sleep 1
  local remaining=()
  for pid in "${pids[@]}"; do
    [[ -d "/proc/$pid" ]] || continue
    state="$(awk '/^State:/ {print $2}' "/proc/$pid/status" 2>/dev/null || true)"
    [[ "$state" == "Z" ]] && continue
    remaining+=("$pid")
  done
  if (( ${#remaining[@]} > 0 )); then
    log "WARN" "runtime PIDs still running; sending SIGKILL: ${remaining[*]}"
    kill -KILL "${remaining[@]}" >/dev/null 2>&1 || true
  fi
}

stop_project_core() {
  log "INFO" "stopping project-owned tmux sessions, processes, and containers"
  tmux_stop_project_sessions || true
  stop_project_processes
  stop_project_containers || true
}

stop_project() {
  stop_project_core
  print_project_status
}

print_pid_status() {
  local label="$1"
  local pid_file="$2"
  if pid_is_alive "$pid_file"; then
    local pid
    pid="$(cat "$pid_file")"
    log "INFO" "${label} pid ${pid} running"
  else
    log "INFO" "${label} pid file not running"
  fi
}

port_pids() {
  local port="$1"
  if has_command lsof; then
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u
    return 0
  fi
  return 1
}

is_project_owned_pid() {
  local pid="$1"
  local cmdline
  cmdline="$(ps -p "$pid" -o args= 2>/dev/null || true)"
  [[ -n "$cmdline" ]] || return 1
  local cwd
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  case "$cwd" in
    "$ROOT_DIR"|"$ROOT_DIR"/*) ;;
    *) return 1 ;;
  esac
  [[ "$cmdline" == *"uvicorn src.main:app"* || "$cmdline" == *"vite --host"* || "$cmdline" == *"npm run dev"* || "$cmdline" == *"tests/benchmarks/http_bridge.py"* || "$cmdline" == *"tests/benchmarks/tcp_bridge.py"* ]]
}

stop_project_port_owner() {
  local label="$1"
  local port="$2"
  local pids
  mapfile -t pids < <(port_pids "$port" || true)
  if (( ${#pids[@]} == 0 )); then
    log "INFO" "no ${label} listener on port ${port}"
    return 0
  fi
  local pid
  for pid in "${pids[@]}"; do
    if ! is_project_owned_pid "$pid"; then
      log "WARN" "refusing to stop ${label} pid ${pid}; listener is not clearly project-owned"
      continue
    fi
    log "INFO" "stopping ${label} pid ${pid}"
    kill "$pid" >/dev/null 2>&1 || true
    sleep 1
    if kill -0 "$pid" >/dev/null 2>&1; then
      log "WARN" "${label} pid ${pid} still running; sending SIGKILL"
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  done
}

print_port_owner_status() {
  local label="$1"
  local port="$2"
  local pids
  mapfile -t pids < <(port_pids "$port" || true)
  if (( ${#pids[@]} == 0 )); then
    log "INFO" "${label} port ${port}: no listener"
    return 0
  fi
  local pid
  for pid in "${pids[@]}"; do
    local cmdline
    cmdline="$(ps -p "$pid" -o args= 2>/dev/null || true)"
    log "INFO" "${label} port ${port}: pid ${pid} ${cmdline}"
  done
}

print_project_status() {
  log "INFO" "FaceSpeed status"
  if has_command tmux; then
    local sessions
    sessions="$(tmux list-sessions -F '#S' 2>/dev/null | grep -E "^${TMUX_PREFIX}($|-)" | paste -sd ', ' - || true)"
    if [[ -n "$sessions" ]]; then
      log "INFO" "tmux sessions: ${sessions}"
    else
      log "INFO" "tmux sessions: none with prefix ${TMUX_PREFIX}"
    fi
  fi
  print_pid_status "backend" "$BACKEND_PID_FILE"
  print_pid_status "frontend" "$FRONTEND_PID_FILE"
  print_port_owner_status "backend" "$BACKEND_PORT"
  print_port_owner_status "frontend" "$FRONTEND_PORT"
  if http_ok "http://${BACKEND_HOST}:${BACKEND_PORT}/health"; then
    log "INFO" "backend health: ok at http://${BACKEND_HOST}:${BACKEND_PORT}/health"
  else
    log "WARN" "backend health: unavailable at http://${BACKEND_HOST}:${BACKEND_PORT}/health"
  fi
  if http_ok "http://${FRONTEND_HOST}:${FRONTEND_PORT}/"; then
    log "INFO" "frontend: ok at http://${FRONTEND_HOST}:${FRONTEND_PORT}/"
  else
    log "WARN" "frontend: unavailable at http://${FRONTEND_HOST}:${FRONTEND_PORT}/"
  fi
  if http_ok "http://${FACESPEED_PROXY_HOST}:${FACESPEED_PROXY_PORT}/"; then
    log "INFO" "nginx proxy: ok at http://${FACESPEED_PROXY_HOST}:${FACESPEED_PROXY_PORT}/"
  else
    log "WARN" "nginx proxy: unavailable at http://${FACESPEED_PROXY_HOST}:${FACESPEED_PROXY_PORT}/"
  fi
  list_project_containers || true
}

print_usage() {
  cat <<'USAGE'
FaceSpeed setup helper

Usage:
  ./setup.sh [mode]
  bash scripts/setup.sh [mode]

Common modes:
  --setup-run          Stop old runtime, check/install, then run Riva/DB/backend/frontend in tmux.
  --bootstrap          Alias for --setup-run.
  --setup              Install backend/frontend dependencies only.
  --run                Stop old runtime, then run Riva/DB/backend/frontend in tmux.
  --verify             Run setup checks, frontend tests/build, and pytest tests/.
  --status             Show project PIDs, health endpoints, and project containers.
  --stop               Stop project tmux sessions, processes, and containers.
  --check              Check Python, Node, npm, Docker, NVIDIA, ports, RAM/VRAM/disk.
  --check-support      Print supported machine profiles.
  --capture-demo       Capture the GitHub README GIF from the running app.
  --logs-clean         Remove disposable runtime logs.

NVIDIA modes:
  --dry-run-containers Print safe Docker commands without pulling or starting.
  --list-containers    List containers matched by project label, compose name, or repo mount.
  --stop-containers    Stop/remove containers matched by project label, compose name, or repo mount.
  --a2f-profiles       List Audio2Face-3D NIM profiles from the configured image.
  --start-a2f-nim      Start Audio2Face-3D NIM; requires accepted NGC EULA/key.
  --check-riva         Check Riva containers and TTS/ASR ports.
  --check-a2f          Check Audio2Face-3D gRPC/HTTP health.

Default root command:
  ./setup.sh           Same as ./setup.sh --setup-run.

Warnings do not block local app startup. Heavy NVIDIA downloads still require the
right NGC license/EULA and NGC_API_KEY in your local shell.

Runtime tmux sessions:
  facespeed-riva-docker, facespeed-riva-tts, facespeed-riva-asr,
  facespeed-riva-backend, facespeed-riva-frontend.
USAGE
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
  check_riva_asr || true
  check_audio2face || true
  log "INFO" "auto setup completed; if WARN remains for NGC/Riva/A2F, follow the exact WARN instructions above"
}

run_start_services() {
  require_tmux || return 1
  log "INFO" "starting configured local services in tmux session ${TMUX_DOCKER_SESSION}"
  if [[ -f "${ROOT_DIR}/docker-compose.yml" ]] && has_command docker; then
    tmux_start_session "$TMUX_DOCKER_SESSION" "$ROOT_DIR" \
      "docker compose -p '${PROJECT_COMPOSE_NAME}' -f '${ROOT_DIR}/docker-compose.yml' up"
    log "INFO" "docker compose logs are in tmux session ${TMUX_DOCKER_SESSION}"
  else
    log "WARN" "docker-compose.yml not found; no docker compose services started"
  fi
}

case "$MODE" in
  --help|-h|help)
    print_usage
    ;;
  --auto)
    run_auto
    ;;
  --setup)
    run_install
    ;;
  --run)
    run_app
    ;;
  --setup-run)
    run_setup_run
    ;;
  --bootstrap)
    run_setup_run
    ;;
  --status)
    print_project_status
    ;;
  --stop)
    stop_project
    ;;
  --check|--check-nvidia)
    run_check
    ;;
  --check-support)
    print_support_matrix
    ;;
  --verify)
    run_verify
    ;;
  --capture-demo)
    run_capture_demo
    ;;
  --logs-clean)
    run_logs_clean
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
  --list-containers)
    list_project_containers
    ;;
  --stop-containers)
    stop_project_containers
    ;;
  --a2f-profiles)
    run_a2f_profile_list
    ;;
  --start-a2f-nim)
    start_a2f_nim
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
    check_riva_asr || true
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
    log "ERROR" "unknown mode: ${MODE}. Use --help for available modes"
    exit 2
    ;;
esac
