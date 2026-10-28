# Medical Interpreting Live Transcription Prototype

A local Python desktop prototype for English/Spanish medical interpreting support.

## Quick start on macOS

1. Download the repository from GitHub (Code → Download ZIP) and extract it, or clone it.
2. Open the extracted `medical-transcription-app` folder in Finder.
3. Double-click **`start.command`**. On the first launch, it creates a private Python environment and installs dependencies. Keep an internet connection available because the speech-recognition model may need to download.
4. If macOS blocks the script, right-click `start.command`, choose **Open**, and confirm. If the file was copied without executable permission, open Terminal in the project folder and run `chmod +x start.command` once, then double-click it again.
5. Allow microphone access when macOS prompts. In the app, choose an audio input and click **Start Listening**.

The launcher checks for Python 3.10–3.13 and Tkinter, installs packages into this project's `.venv`, and launches the desktop interface. Python 3.12 from [python.org](https://www.python.org/downloads/macos/) is a recommended option if no compatible interpreter is available. You do not need to activate the environment or type multiple startup commands.

### Optional English/Spanish translation packages

Full local translation requires the Argos Translate language packages. The app remains usable without them, but will show clearly labeled glossary-only reference output rather than a full translation. To install the language packages, open Terminal in the project folder and run:

```bash
./.venv/bin/python install_translation_packages.py
```

Restart the app afterward. This setup step requires internet access and may take several minutes.

## Audio input on macOS

macOS usually does not expose speaker output as a recordable input by default. To transcribe desktop audio, route it to an input device first. Options include BlackHole (free) or Loopback (paid).

1. Set up the virtual audio device and route the sound to it.
2. In the app, select **Refresh Inputs**.
3. Choose the virtual device under **Audio input**.
4. Press **Start Listening**.

If you select your microphone, the app hears your microphone. If you select a virtual input, it hears audio routed into that device.

## What the app does

- Captures audio continuously from a selected input device.
- Uses pauses in speech to detect phrase boundaries.
- Detects English or Spanish independently for each utterance with `faster-whisper`.
- Automatically translates each utterance into the opposite language when the required local Argos Translate packages are installed.
- Displays utterances in a segment table with source language, transcript, translation, and status.
- Lets you select an utterance, edit its transcript, optionally correct its source language, and regenerate its translation.
- Keeps the initial recognition text available in saved session exports when you make a correction.
- Labels glossary-only fallback output clearly so it is not mistaken for a full translation.
- Lets the interpreter save a local session transcript.

Language detection can be wrong for short phrases, names, accents, or mixed-language speech. Check the source-language label and use the editor's language selector when needed. Correcting the transcript invalidates the previous translation and queues a new one; stale translation results are ignored.

## Phrase detection and current limitations

Audio is captured continuously. The app uses an energy-based voice activity heuristic and a short silence interval to decide when a phrase is complete before sending it to transcription. Background noise, microphone levels, accents, and overlapping speech can affect detection. Adjusting the silence threshold or pause duration may be necessary for a particular setup.

The app processes phrases with one transcription worker and one translation worker. If processing is slower than the speaker, queued phrases can accumulate and increase delay. This is an experimental prototype, not a certified medical device or authoritative medical record. Always verify output against the original audio, especially medication names, dosages, numbers, and negation.

## Run the checks

With the project's environment available:

```bash
./.venv/bin/python -m compileall -q .
./.venv/bin/python -m unittest discover -s tests -v
```

## Project files

- `start.command`: one-click macOS launcher.
- `live_app.py`: desktop interface and background workers.
- `audio_capture.py`: continuous audio capture and silence-based phrase detection.
- `transcription_engine.py`: local speech recognition wrapper.
- `translation_engine.py`: optional local translation and glossary fallback.
- `install_translation_packages.py`: installs local English/Spanish Argos Translate packages.
- `glossary.py`: built-in English/Spanish medical glossary.
- `import_dictionary.py`: optional importer for a third-party medical Spanish dictionary HTML file.
- `requirements.txt`: Python dependencies.

## Privacy and safety

Audio processing is intended to run locally after required models and packages are installed. This does not by itself guarantee compliance with HIPAA or any other privacy law. Do not use real patient information unless the workflow has been approved by the relevant employer/client and all applicable privacy, security, and retention requirements are met. Do not commit patient audio, transcripts, credentials, or other sensitive information to this repository.

## Copyright and permissions

Copyright © 2026 Camilo Gomez. All rights reserved.
