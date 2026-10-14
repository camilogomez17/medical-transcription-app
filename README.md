# Medical Interpreting Live Transcription Prototype

A local Python desktop prototype for English/Spanish medical interpreting support.

## What it does

- Captures audio continuously from a selected input device.
- Uses pauses in speech to detect phrase boundaries.
- Transcribes completed phrases locally with `faster-whisper`.
- Shows draft translation or glossary support.
- Lets the interpreter save a local transcript.

This is an experimental prototype, not a certified medical device or authoritative medical record. Transcription and translation can be wrong, especially for medication names, dosages, numbers, negation, and medical terminology. Always verify output against the original audio.

## Setup

Requires Python 3.10 or newer and a working audio input.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python live_app.py
```

On macOS, allow microphone access when prompted. On first run, `faster-whisper` may need internet access to download its speech recognition model.

## Audio input on macOS

macOS usually does not expose speaker output as a recordable input by default. To transcribe desktop audio, route it to an input device first. Options include BlackHole (free) or Loopback (paid).

1. Set up the virtual audio device and route the sound to it.
2. Restart the app and select **Refresh Inputs**.
3. Choose the virtual device under **Audio input**.
4. Press **Start Listening**.

If you select your microphone, the app hears your microphone. If you select a virtual input, it hears audio routed into that device.

## Translation setup

The app can transcribe even if the optional local translation packages are not configured. To install the English/Spanish Argos Translate packages, activate the virtual environment and run:

```bash
python install_translation_packages.py
```

Then restart the app. If translation is unavailable, the app uses glossary hints rather than presenting them as a reliable full translation.

## Phrase detection

Audio is captured continuously. The app uses an energy-based voice activity heuristic and a short silence interval to decide when a phrase is complete before sending it to transcription. Background noise, microphone levels, accents, and overlapping speech can affect detection. Adjusting the silence threshold or pause duration may be necessary for a particular setup.

The app processes phrases with one transcription worker and one translation worker. If processing is slower than the speaker, queued phrases can accumulate and increase delay.

## Files

- `live_app.py`: desktop interface and background workers.
- `audio_capture.py`: continuous audio capture and silence-based phrase detection.
- `transcription_engine.py`: local speech recognition wrapper.
- `translation_engine.py`: optional local translation and glossary fallback.
- `install_translation_packages.py`: installs local English/Spanish Argos Translate packages.
- `glossary.py`: built-in English/Spanish medical glossary.
- `import_dictionary.py`: optional importer for a third-party medical Spanish dictionary HTML file.
- `requirements.txt`: Python dependencies.

## Privacy and safety

Audio processing is intended to run locally after required models and packages are installed. This does not by itself guarantee that a deployment is compliant with HIPAA or any other privacy law. Do not use real patient information unless the workflow has been approved by the relevant employer/client and all applicable privacy, security, and retention requirements are met. Do not commit patient audio, transcripts, credentials, or other sensitive information to this repository.

## Copyright and permissions

Copyright © 2026 Camilo Gomez. All rights reserved.

This project and its source code are proprietary. No permission is granted to copy, modify, distribute, sublicense, or commercially use this software without prior written permission from the copyright holder, except where permitted by applicable law. No open-source license is granted by this repository.

Third-party dependencies and any separately downloaded dictionary content remain subject to their own licenses and terms.
