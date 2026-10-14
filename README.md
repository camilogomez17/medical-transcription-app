# Medical Interpreting Live Transcription Prototype

This is a local Python desktop prototype for English/Spanish medical interpreting support.

The 20/80 idea:

1. Capture microphone audio continuously and detect phrase-ending pauses.
2. Transcribe each complete phrase locally with `faster-whisper`.
3. Show a draft translation or glossary hints.
4. Keep the interpreter in control.

This prototype is for practice and workflow design. Do not use it with real patient information unless your employer/client has approved the workflow and all privacy requirements are covered.

## Setup

From this folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python live_app.py
```

On macOS, allow microphone access when prompted.

## Desktop Audio on macOS

macOS usually does not expose normal speaker audio as a recordable input. To transcribe desktop audio, route the sound into an input device first.

Common options:

- BlackHole: free virtual audio device.
- Loopback: paid, polished routing app.
- A multi-output device: lets you hear audio and route it into BlackHole at the same time.

After setting that up:

1. Restart the app.
2. Press **Refresh Inputs**.
3. Pick the virtual device, such as **BlackHole 2ch**, from **Audio input**.
4. Press **Start Listening**.

If you select your microphone, the app hears your mic. If you select BlackHole or another virtual input, the app hears the audio routed into that device.

## Optional Local Translation Setup

The app can transcribe before translation is fully configured. If the translation panel says the local translation package is missing, run:

```bash
source .venv/bin/activate
python install_translation_packages.py
```

Then restart the app:

```bash
python live_app.py
```

## First Run

1. Open the app.
2. Choose the spoken language: English or Spanish.
3. Choose the translation direction.
4. Choose an audio input.
5. Press **Start Listening**.
6. Speak in short phrases or play routed desktop audio.
7. Press **Stop**.

## Notes

- `faster-whisper` runs speech-to-text locally after the model is downloaded.
- The first model download may require internet access.
- Translation is intentionally conservative in this prototype. If `argostranslate` is not installed/configured, the app shows glossary hints instead of pretending to be a reliable translator.
- Save/export is local only.

## Files

- `live_app.py`: desktop interface.
- `audio_capture.py`: continuous microphone capture and silence-based phrase detection.
- `transcription_engine.py`: local transcription wrapper.
- `translation_engine.py`: optional local translation and glossary fallback.
- `install_translation_packages.py`: downloads local English/Spanish translation packages for Argos Translate.
- `glossary.py`: English/Spanish medical glossary.
- `requirements.txt`: Python packages to install.


## Low-latency changes

- Audio chunks are 2 seconds instead of 6 seconds. Shorter chunks reduce waiting time but can affect recognition quality.
- The app uses one transcription worker and one translation worker rather than creating a thread for every chunk.
- Transcript text is displayed as soon as transcription completes; translation runs separately.
- The default model is `base` on CPU with int8 quantization to favor latency over the previous `medium` model. To prioritize recognition quality over speed, change `model_size="base"` in `live_app.py` to `model_size="medium"` and measure the delay on your machine.
- If CPU processing cannot keep up, the app may skip a pending audio chunk and display a warning. Stop and verify the source audio/transcript; do not treat this prototype as a complete or authoritative medical record.

For real patient encounters, use only if your employer/client has approved the workflow and the required privacy/security controls are in place. Always verify medical terminology and numbers against the source audio.
## Import the Medical Spanish Dictionary

Download the dictionary HTML from the repository's Raw link, then run:

```bash
curl -L "https://raw.githubusercontent.com/fredymrodriguez/MedicalSpanishDictionary/main/docs/index.html" -o medical-spanish-dictionary.html
python import_dictionary.py medical-spanish-dictionary.html
```

The importer creates `medical_glossary.json` in this project folder. The app loads it automatically at startup and combines it with the built-in glossary. Re-run the import command whenever you download an updated dictionary. The importer extracts English headwords and Spanish equivalents from headings; it does not import the page's definitions, examples, or metadata. Review translations for accuracy before using them in a medical setting.

