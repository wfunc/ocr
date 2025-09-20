#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
PYTHON_BIN_PATH="${VENV_DIR}/bin/python"

if [ ! -f "${PYTHON_BIN_PATH}" ]; then
    echo "[*] Creating virtual environment at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
fi

# Ensure pip exists before install
"${PYTHON_BIN_PATH}" -m ensurepip --upgrade >/dev/null 2>&1 || true

# Upgrade pip and install dependencies
"${PYTHON_BIN_PATH}" -m pip install --upgrade pip
"${PYTHON_BIN_PATH}" -m pip install -r "${REQUIREMENTS_FILE}"

export PYTHON_BIN="${PYTHON_BIN_PATH}"

echo "[*] Starting Gin OCR server on :8080"
exec go run "${SCRIPT_DIR}/main.go"
