#!/usr/bin/env bash
# macOS dev-mode launcher — analogue of start.ps1, no GPU detection (MPS assumed on Apple Silicon).
# Bundled tools/astral/uv.exe is Windows-only; relies on system `uv` instead.
set -euo pipefail

PORT="${PORT:-7860}"
LOCALE="${LOCALE:-${LANG%%.*}}"
LOCALE="${LOCALE//_/-}"
# Validate locale format (xx-XX). If invalid, fallback to en-US.
if [[ ! "$LOCALE" =~ ^[a-z]{2}-[A-Z]{2}$ ]]; then
    LOCALE="en-US"
fi

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# Reuse venv across runs once installed (.venv/mac-ready is the Mac analogue of .venv/optimized).
if [[ ! -f .venv/mac-ready ]]; then
    echo "Creating Python 3.13 venv and installing deps (one-time, slow)..."
    uv venv --python 3.13 --clear
    uv pip install --python .venv/bin/python -r requirements-mac.txt
    : > .venv/mac-ready
    echo "Install complete."
fi

echo "ZPix starting at http://127.0.0.1:${PORT}  (locale=${LOCALE})"
echo "Open that URL in your browser once Gradio prints 'Running on local URL'."
exec uv run --python .venv/bin/python app.py --port "$PORT" --locale "$LOCALE"
