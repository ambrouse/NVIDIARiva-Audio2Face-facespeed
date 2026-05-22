#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIVA_CACHE_DIR="${RIVA_CACHE_DIR:-$ROOT_DIR/.cache/nvidia/riva}"
QUICKSTART_DIR="${QUICKSTART_DIR:-$RIVA_CACHE_DIR/riva_quickstart_v2.19.0}"
BASE_CONFIG="$QUICKSTART_DIR/config.sh"
BUILD_REPO="$RIVA_CACHE_DIR/model-repo-asr"
RUNTIME_REPO="$RIVA_CACHE_DIR/model-repo-asr-offline"
BUILD_CONFIG="$RIVA_CACHE_DIR/config-facespeed-asr.sh"
RUNTIME_CONFIG="$RIVA_CACHE_DIR/config-facespeed-asr-offline.sh"
RIVA_IMAGE="${RIVA_IMAGE:-nvcr.io/nvidia/riva/riva-speech:2.19.0}"
ASR_PORT="${RIVA_ASR_PORT:-50151}"
ASR_HTTP_PORT="${RIVA_ASR_HTTP_PORT:-50100}"

if [[ ! -f "$BASE_CONFIG" ]]; then
  echo "Missing Riva quickstart config: $BASE_CONFIG" >&2
  exit 1
fi

generate_config() {
  local target="$1"
  local repo="$2"
  cp "$BASE_CONFIG" "$target"
  perl -0pi -e "s/service_enabled_asr=false/service_enabled_asr=true/;
    s/service_enabled_tts=true/service_enabled_tts=false/;
    s#riva_model_loc=\"[^\"]+\"#riva_model_loc=\"$repo\"#;
    s/riva_speech_api_port=\"[0-9]+\"/riva_speech_api_port=\"$ASR_PORT\"/;
    s/riva_speech_api_http_port=\"[0-9]+\"/riva_speech_api_http_port=\"$ASR_HTTP_PORT\"/;
    s/riva_daemon_speech=\"[^\"]+\"/riva_daemon_speech=\"facespeed-riva-asr\"/" "$target"
}

copy_runtime_models() {
  docker run --rm \
    -v "$RIVA_CACHE_DIR:/work" \
    --entrypoint /bin/bash \
    "$RIVA_IMAGE" \
    -lc "rm -rf /work/model-repo-asr-offline &&
      mkdir -p /work/model-repo-asr-offline/models /work/model-repo-asr-offline/rmir &&
      cp -a /work/model-repo-asr/models/conformer-en-US-asr-offline-asr-bls-ensemble /work/model-repo-asr-offline/models/ &&
      cp -a /work/model-repo-asr/models/riva-trt-conformer-en-US-asr-offline-am-streaming-offline /work/model-repo-asr-offline/models/ &&
      cp -a /work/model-repo-asr/models/riva-punctuation-en-US /work/model-repo-asr-offline/models/ &&
      cp -a /work/model-repo-asr/models/riva-trt-riva-punctuation-en-US-nn-bert-base-uncased /work/model-repo-asr-offline/models/"
}

tune_runtime_models() {
  docker run --rm \
    -v "$RUNTIME_REPO:/data" \
    --entrypoint /bin/bash \
    "$RIVA_IMAGE" \
    -lc "perl -0pi -e 's/max_batch_size: 1024/max_batch_size: 1/;
      s/max_candidate_sequences: 1024/max_candidate_sequences: 16/g;
      s/preferred_batch_size: \\[64, 128\\]/preferred_batch_size: [1]/g' \
      /data/models/conformer-en-US-asr-offline-asr-bls-ensemble/config.pbtxt &&
      perl -0pi -e 's/acoustic_model_max_execution_batch_size: 16/acoustic_model_max_execution_batch_size: 1/g;
      s/audio_processing_num_worker_threads: 8/audio_processing_num_worker_threads: 2/g;
      s/decoder_num_worker_threads: '\\''-1'\\''/decoder_num_worker_threads: '\\''2'\\''/g;
      s/endpointing_num_worker_threads: 16/endpointing_num_worker_threads: 2/g;
      s/max_execution_batch_size: 512/max_execution_batch_size: 1/g;
      s/max_batch_size: 1024/max_batch_size: 1/g' \
      /data/models/conformer-en-US-asr-offline-asr-bls-ensemble/1/riva_bls_config.yaml"
}

mkdir -p "$RIVA_CACHE_DIR"
generate_config "$BUILD_CONFIG" "$BUILD_REPO"

if [[ ! -d "$BUILD_REPO/models/conformer-en-US-asr-offline-asr-bls-ensemble" ]]; then
  RIVA_TIMEOUT_SEC="${RIVA_TIMEOUT_SEC:-900}" "$QUICKSTART_DIR/riva_init.sh" "$BUILD_CONFIG"
fi

copy_runtime_models
tune_runtime_models
generate_config "$RUNTIME_CONFIG" "$RUNTIME_REPO"
perl -0pi -e 's/use_existing_rmirs=false/use_existing_rmirs=true/' "$RUNTIME_CONFIG"
RIVA_TIMEOUT_SEC="${RIVA_TIMEOUT_SEC:-300}" "$QUICKSTART_DIR/riva_start.sh" "$RUNTIME_CONFIG"

