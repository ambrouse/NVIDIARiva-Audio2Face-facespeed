#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RPM_DIR="${ROOT_DIR}/.cache/rpms"
LIB_DIR="${ROOT_DIR}/.local-libs/playwright"
EXTRACT_DIR="${LIB_DIR}/extract"

mkdir -p "${RPM_DIR}" "${LIB_DIR}" "${EXTRACT_DIR}"

if [[ ! -f "${LIB_DIR}/libasound.so.2" ]]; then
  if ! command -v dnf >/dev/null 2>&1; then
    echo "dnf is required to download alsa-lib on this host." >&2
    exit 1
  fi
  if ! command -v rpm2cpio >/dev/null 2>&1 || ! command -v cpio >/dev/null 2>&1; then
    echo "rpm2cpio and cpio are required to extract alsa-lib locally." >&2
    exit 1
  fi

  dnf download --destdir "${RPM_DIR}" alsa-lib
  rpm_path="$(find "${RPM_DIR}" -maxdepth 1 -type f -name 'alsa-lib-*.x86_64.rpm' | sort | tail -1)"
  if [[ -z "${rpm_path}" ]]; then
    echo "Could not find downloaded x86_64 alsa-lib RPM in ${RPM_DIR}." >&2
    exit 1
  fi

  (
    cd "${EXTRACT_DIR}"
    rpm2cpio "${rpm_path}" | cpio -id --quiet './usr/lib64/libasound.so*'
  )
  cp -a "${EXTRACT_DIR}"/usr/lib64/libasound.so* "${LIB_DIR}/"
fi

echo "Playwright local library path:"
echo "${LIB_DIR}"
echo
echo "Use:"
echo "LD_LIBRARY_PATH=\$PWD/.local-libs/playwright node <your-playwright-script>"
