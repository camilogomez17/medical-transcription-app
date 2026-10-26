"""Continuous audio capture with silence-based utterance segmentation."""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Callable
from typing import Any


def list_input_devices() -> list[dict[str, object]]:
    """Return audio devices that can be used as input sources."""
    try:
        import sounddevice as sd
    except ImportError:
        return []

    devices = []
    for index, device in enumerate(sd.query_devices()):
        if int(device.get("max_input_channels", 0)) > 0:
            devices.append(
                {
                    "index": index,
                    "name": str(device.get("name", f"Device {index}")),
                    "channels": int(device.get("max_input_channels", 0)),
                    "sample_rate": int(float(device.get("default_samplerate", 16000))),
                }
            )
    return devices


class AudioCapture:
    """Capture continuously and emit a complete phrase after a pause.

    A short pre-roll preserves the beginning of a phrase. The phrase is emitted
    only after trailing silence, so inference no longer runs on arbitrary
    two-second slices that can split words.
    """

    def __init__(
        self,
        on_chunk: Callable[[object], None],
        on_error: Callable[[str], None],
        sample_rate: int = 16000,
        silence_seconds: float = 0.8,
        preroll_seconds: float = 0.3,
        min_speech_seconds: float = 0.25,
        max_utterance_seconds: float = 30.0,
    ) -> None:
        self.on_chunk = on_chunk
        self.on_error = on_error
        self.sample_rate = sample_rate
        self.silence_seconds = silence_seconds
        self.preroll_seconds = preroll_seconds
        self.min_speech_seconds = min_speech_seconds
        self.max_utterance_seconds = max_utterance_seconds
        self.device_index: int | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, device_index: int | None = None) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.device_index = device_index
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, wait: bool = False) -> bool:
        """Request capture shutdown and optionally wait for its thread to exit."""
        self._stop_event.set()
        thread = self._thread
        if wait and thread and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        return thread is None or not thread.is_alive()

    def _run(self) -> None:
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError:
            self.on_error(
                "Microphone capture needs `sounddevice` and `numpy`.\n"
                "Run: python -m pip install -r requirements.txt"
            )
            return

        # 20 ms frames are short enough to detect pauses without slicing speech
        # into fixed-duration transcription chunks.
        frame_samples = 320
        preroll_frames = max(
            1, int(self.preroll_seconds * self.sample_rate / frame_samples)
        )
        silence_frames_needed = max(
            1, int(self.silence_seconds * self.sample_rate / frame_samples)
        )
        min_speech_frames = max(
            1, int(self.min_speech_seconds * self.sample_rate / frame_samples)
        )
        max_utterance_frames = max(
            1, int(self.max_utterance_seconds * self.sample_rate / frame_samples)
        )
        pre_roll = deque(maxlen=preroll_frames)
        utterance: list[Any] = []
        in_speech = False
        silence_frames = 0
        speech_frames = 0
        # Updated only during non-speech to follow the room/device noise floor.
        noise_rms = 0.0015

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=frame_samples,
                device=self.device_index,
            ) as stream:
                while not self._stop_event.is_set():
                    frame, _overflowed = stream.read(frame_samples)
                    mono = np.asarray(frame, dtype=np.float32).reshape(-1).copy()
                    rms = float(np.sqrt(np.mean(mono * mono) + 1e-12))
                    threshold = max(0.004, noise_rms * 2.5)
                    is_voice = rms >= threshold

                    if not in_speech:
                        if not is_voice:
                            noise_rms = 0.98 * noise_rms + 0.02 * rms
                        pre_roll.append(mono)
                        if is_voice:
                            in_speech = True
                            utterance = list(pre_roll)
                            speech_frames = 1
                            silence_frames = 0
                    else:
                        utterance.append(mono)
                        if is_voice:
                            speech_frames += 1
                            silence_frames = 0
                        else:
                            silence_frames += 1

                        reached_pause = silence_frames >= silence_frames_needed
                        reached_limit = len(utterance) >= max_utterance_frames
                        if reached_pause or reached_limit:
                            # Trim only the final silence used for endpointing;
                            # retain a small tail so word endings are not clipped.
                            tail_frames = max(
                                1, int(0.15 * self.sample_rate / frame_samples)
                            )
                            if reached_pause and len(utterance) > tail_frames:
                                utterance = utterance[
                                    : -max(0, silence_frames - tail_frames)
                                ]
                            if speech_frames >= min_speech_frames and utterance:
                                self.on_chunk(
                                    np.concatenate(utterance).astype(
                                        np.float32, copy=False
                                    )
                                )
                            utterance = []
                            pre_roll.clear()
                            in_speech = False
                            silence_frames = 0
                            speech_frames = 0

                # Flush speech already in progress when Stop is pressed.
                if in_speech and speech_frames >= min_speech_frames and utterance:
                    self.on_chunk(
                        np.concatenate(utterance).astype(np.float32, copy=False)
                    )
        except Exception as exc:  # noqa: BLE001 — report capture failures to the UI
            if not self._stop_event.is_set():
                self.on_error(f"Audio input error: {exc}")
