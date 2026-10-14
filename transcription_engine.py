"""Local speech-to-text wrapper for faster-whisper with language detection."""

from __future__ import annotations


class TranscriptionEngine:
    def __init__(self, model_size: str = "base") -> None:
        self.model_size = model_size
        self.model = None
        self.error: Exception | None = None

        try:
            from faster_whisper import WhisperModel

            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except Exception as exc:
            self.error = exc

    @property
    def ready(self) -> bool:
        return self.model is not None

    def transcribe_audio(
        self, samples, language: str | None = None
    ) -> tuple[str, str, float]:
        """Return transcript, detected language code, and language confidence.

        Pass language=None to let Whisper identify the language for this utterance.
        The caller can provide an explicit language when reprocessing audio.
        """
        if self.model is None:
            detail = f" {self.error}" if self.error else ""
            raise RuntimeError(
                "Transcription engine is not ready. Install dependencies with "
                "`python -m pip install -r requirements.txt`." + detail
            )

        segments, info = self.model.transcribe(
            samples,
            language=language,
            beam_size=1,
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        detected_language = str(getattr(info, "language", language or "en"))
        language_probability = float(getattr(info, "language_probability", 0.0))
        return text, detected_language, language_probability
