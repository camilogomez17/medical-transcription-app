#!/bin/bash
# One-click macOS launcher for Medical Interpreting Live Transcription.
set -e
cd "$(dirname "$0")"

APP_NAME="Medical Interpreting Live Transcription"

echo "Starting $APP_NAME..."
echo

# faster-whisper/CTranslate2 support depends on Python wheels. Prefer a supported
# Python version over a possibly too-new system/Homebrew interpreter.
PYTHON=""
for candidate in python3.12 python3.11 python3.13 python3.10 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    version="$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    case "$version" in
      3.10|3.11|3.12|3.13)
        PYTHON="$(command -v "$candidate")"
        break
        ;;
    esac
  fi
done

if [ -z "$PYTHON" ]; then
  echo "Python 3.10–3.13 is required. Install Python 3.12 from https://www.python.org/downloads/macos/"
  echo "Then double-click start.command again."
  read -r -p "Press Return to close this window..."
  exit 1
fi

echo "Using Python: $("$PYTHON" --version) ($PYTHON)"

if ! "$PYTHON" -c 'import tkinter' >/dev/null 2>&1; then
  echo
  echo "This Python installation does not include Tkinter, which the desktop interface requires."
  echo "Install Python 3.12 from https://www.python.org/downloads/macos/ and try again."
  read -r -p "Press Return to close this window..."
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating the app's private Python environment..."
  "$PYTHON" -m venv .venv
fi

echo "Checking/installing app dependencies (only needed on first launch or after updates)..."
if ! ./.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt; then
  echo
  echo "Dependency installation failed. Check your internet connection and Python version, then try again."
  read -r -p "Press Return to close this window..."
  exit 1
fi

echo
echo "Launching the app. The first launch may download the speech-recognition model."
echo "Allow microphone access when macOS asks. Close the app window to exit."
echo
./.venv/bin/python live_app.py
