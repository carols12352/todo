#!/bin/zsh
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
FRONTEND_DIST="${FRONTEND_DIR}/dist"
BACKEND_FRONTEND_DIST="${ROOT_DIR}/backend/cores/frontend_dist"

cd "${FRONTEND_DIR}"
npm install
npm run build

rm -rf "${BACKEND_FRONTEND_DIST}"
mkdir -p "${BACKEND_FRONTEND_DIST}"
cp -R "${FRONTEND_DIST}/." "${BACKEND_FRONTEND_DIST}/"

cd "${ROOT_DIR}"
bash build_mac.sh
