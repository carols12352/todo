#!/bin/zsh
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_BUILD_DIR="/tmp/todolist_build"
TMP_DIST_DIR="/tmp/todolist_dist"

rm -rf "${TMP_BUILD_DIR}" "${TMP_DIST_DIR}"
pyinstaller --noconsole --windowed --name TodoList \
  --icon todolist.icns \
  --add-data "tray_mac.png:." \
  --add-data "backend/cores/frontend_dist:frontend_dist" \
  --workpath "${TMP_BUILD_DIR}" \
  --distpath "${TMP_DIST_DIR}" \
  backend/cores/tray_app_mac.py

rm -rf "${ROOT_DIR}/dist"
mkdir -p "${ROOT_DIR}/dist"
cp -R "${TMP_DIST_DIR}/TodoList.app" "${ROOT_DIR}/dist/"
rm -rf "${TMP_BUILD_DIR}" "${TMP_DIST_DIR}"
