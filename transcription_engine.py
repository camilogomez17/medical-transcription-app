"""Local speech-to-text wrapper for faster-whisper."""

from __future__ import annotations


class TranscriptionEngine:
    def __init__(self, model_size: str = "base") -> None:
        self.model_size = model_size
        self.model = None
        self.error = None

        try:
            from faster_whisper import WhisperModel

            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except Exception as exc:
            self.error = exc

    @property
    def ready(self) -> bool:
        return self.model is not None

    def transcribe_audio(self, samples, language: str) -> str:
        if self.model is None:
            return (
                "Transcription engine is not ready. Install dependencies with "
                "`python -m pip install -r requirements.txt`."
            )

        segments, _info = self.model.transcribe(
            samples,
            language=language,
            beam_size=1,
            vad_filter=True,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()
