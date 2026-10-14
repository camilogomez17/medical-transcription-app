# Medical Interpreting Live Transcription Prototype

A local Python desktop prototype for English/Spanish medical interpreting support.

## Set up the environment on macOS

These steps create a separate Python environment for this project so its packages are not installed into Homebrew's system-managed Python.

### 1. Open Terminal and enter the project folder

If you downloaded or cloned the repository into Downloads, run:

```bash
cd ~/Downloads/medical-transcription-app
```

If the folder is somewhere else, change this command to the actual folder path.

### 2. Create a virtual environment

Run this from inside the project folder:

```bash
python3 -m venv .venv
```

This creates a `.venv` folder inside the project. You only need to create it once, unless you delete or recreate the environment.

### 3. Activate the environment

```bash
source .venv/bin/activate
```

Your Terminal prompt should show `(.venv)`. Verify that Python points inside this project's environment:

```bash
which python
which python3
echo $VIRTUAL_ENV
```

The paths should refer to `.../medical-transcription-app/.venv/`. If they point to a different project or to `/opt/homebrew/bin/python3`, the environment is not active for this folder. Run `deactivate`, return to this project folder, and activate it again.

### 4. Install the dependencies

With the environment activated, run:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Use `python -m pip` rather than bare `pip` so packages install into the Python environment you are using. Do not use `--break-system-packages`.

If the `python` command is unavailable, call the environment's interpreter directly:

```bash
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

### 5. Start the app

Keep the virtual environment activated and run:

```bash
python live_app.py
```

Or, if needed:

```bash
./.venv/bin/python live_app.py
```

On macOS, allow microphone access when prompted. The first run may need internet access to download the speech recognition model.

### 6. Each time you use the app

Open Terminal, go to the project folder, activate the existing environment, and start the app:

```bash
cd ~/Downloads/medical-transcription-app
source .venv/bin/activate
python live_app.py
```

You do not need to reinstall the packages every time.

## Audio input on macOS

macOS usually does not expose speaker output as a recordable input by default. To transcribe desktop audio, route it to an input device first. Options include BlackHole (free) or Loopback (paid).

1. Set up the virtual audio device and route the sound to it.
2. Restart the app and select **Refresh Inputs**.
3. Choose the virtual device under **Audio input**.
4. Press **Start Listening**.

If you select your microphone, the app hears your microphone. If you select a virtual input, it hears audio routed into that device.

## Optional English/Spanish translation packages

The app can transcribe even if the optional local translation packages are not configured. To install the English/Spanish Argos Translate packages, first activate the environment, then run:

```bash
python install_translation_packages.py
```

Restart the app afterward. If translation is unavailable, the app uses glossary hints rather than presenting them as a reliable full translation.

## What the app does

- Captures audio continuously from a selected input device.
- Uses pauses in speech to detect phrase boundaries.
- Transcribes completed phrases locally with `faster-whisper`.
- Shows draft translation or glossary support.
- Lets the interpreter save a local transcript.

## Phrase detection

Audio is captured continuously. The app uses an energy-based voice activity heuristic and a short silence interval to decide when a phrase is complete before sending it to transcription. Background noise, microphone levels, accents, and overlapping speech can affect detection. Adjusting the silence threshold or pause duration may be necessary for a particular setup.

The app processes phrases with one transcription worker and one translation worker. If processing is slower than the speaker, queued phrases can accumulate and increase delay.

## Project files

- `live_app.py`: desktop interface and background workers.
- `audio_capture.py`: continuous audio capture and silence-based phrase detection.
- `transcription_engine.py`: local speech recognition wrapper.
- `translation_engine.py`: optional local translation and glossary fallback.
- `install_translation_packages.py`: installs local English/Spanish Argos Translate packages.
- `glossary.py`: built-in English/Spanish medical glossary.
- `import_dictionary.py`: optional importer for a third-party medical Spanish dictionary HTML file.
- `requirements.txt`: Python dependencies.

## Privacy and safety

This is an experimental prototype, not a certified medical device or authoritative medical record. Transcription and translation can be wrong, especially for medication names, dosages, numbers, negation, and medical terminology. Always verify output against the original audio.

Audio processing is intended to run locally after required models and packages are installed. This does not by itself guarantee that a deployment is compliant with HIPAA or any other privacy law. Do not use real patient information unless the workflow has been approved by the relevant employer/client and all applicable privacy, security, and retention requirements are met. Do not commit patient audio, transcripts, credentials, or other sensitive information to this repository.

## Copyright and permissions

Copyright © 2026 Camilo Gomez. All rights reserved.

This project and its source code are proprietary. No permission is granted to copy, modify, distribute, sublicense, or commercially use this software without prior written permission from the copyright holder, except where permitted by applicable law. No open-source license is granted by this repository.

Third-party dependencies and any separately downloaded dictionary content remain subject to their own licenses and terms.
