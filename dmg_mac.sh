#!/bin/zsh
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
DMG_NAME="TodoList.dmg"
DMG_DIR="${ROOT_DIR}/dmg"
APP_PATH="${ROOT_DIR}/dist/TodoList.app"

rm -rf "${DMG_DIR}" "${ROOT_DIR}/${DMG_NAME}"
mkdir -p "${DMG_DIR}"
cp -R "${APP_PATH}" "${DMG_DIR}/"
hdiutil create -volname "TodoList" -srcfolder "${DMG_DIR}" -ov -format UDZO "${ROOT_DIR}/${DMG_NAME}"
