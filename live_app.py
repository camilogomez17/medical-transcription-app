"""Desktop prototype for live medical interpreting support."""

from __future__ import annotations

import datetime as dt
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from audio_capture import AudioCapture, list_input_devices
from transcription_engine import TranscriptionEngine
from translation_engine import TranslationEngine


APP_TITLE = "Medical Interpreting Live Transcription"


class LiveInterpreterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x720")
        self.minsize(900, 560)

        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        # Preserve completed phrases in order; processing delays should not silently drop audio.
        self.audio_jobs: queue.Queue[tuple[object, str, str, str]] = queue.Queue()
        self.translation_jobs: queue.Queue[tuple[str, str, str]] = queue.Queue()
        self.transcriber = TranscriptionEngine(model_size="base")
        self.translator = TranslationEngine()
        self.audio = AudioCapture(
            self._handle_audio_chunk,
            self._handle_audio_error,
            silence_seconds=0.8,
            preroll_seconds=0.3,
        )
        self.listening = False
        self.active_language = "en"
        self.active_source = "en"
        self.active_target = "es"
        self.input_devices: list[dict[str, object]] = []

        self.spoken_language = tk.StringVar(value="en")
        self.translation_direction = tk.StringVar(value="en-es")
        self.input_device_label = tk.StringVar(value="Default input")
        self.status = tk.StringVar(value=self._startup_status())

        self._load_input_devices()
        self._build_ui()
        # One worker per stage avoids spawning an unbounded number of threads.
        threading.Thread(target=self._transcription_worker, daemon=True).start()
        threading.Thread(target=self._translation_worker, daemon=True).start()
        self.after(50, self._drain_events)

    def _startup_status(self) -> str:
        if self.transcriber.ready:
            return "Ready. Start listening when you are ready."
        return f"Setup needed: {self.transcriber.error}"

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        controls = ttk.Frame(root)
        controls.pack(fill="x")

        ttk.Label(controls, text="Spoken language").pack(side="left")
        ttk.Combobox(
            controls,
            textvariable=self.spoken_language,
            values=("en", "es"),
            width=7,
            state="readonly",
        ).pack(side="left", padx=(8, 18))

        ttk.Label(controls, text="Translation").pack(side="left")
        ttk.Combobox(
            controls,
            textvariable=self.translation_direction,
            values=("en-es", "es-en"),
            width=8,
            state="readonly",
        ).pack(side="left", padx=(8, 18))

        self.start_button = ttk.Button(
            controls,
            text="Start Listening",
            command=self.start_listening,
        )
        self.start_button.pack(side="left")

        self.stop_button = ttk.Button(
            controls,
            text="Stop",
            command=self.stop_listening,
            state="disabled",
        )
        self.stop_button.pack(side="left", padx=8)

        ttk.Button(controls, text="Save Transcript", command=self.save_transcript).pack(
            side="right"
        )
        ttk.Button(controls, text="Clear", command=self.clear_text).pack(
            side="right", padx=8
        )

        input_controls = ttk.Frame(root)
        input_controls.pack(fill="x", pady=(10, 0))

        ttk.Label(input_controls, text="Audio input").pack(side="left")
        self.input_device = ttk.Combobox(
            input_controls,
            textvariable=self.input_device_label,
            values=self._input_device_labels(),
            state="readonly",
            width=56,
        )
        self.input_device.pack(side="left", padx=(8, 8))
        ttk.Button(
            input_controls,
            text="Refresh Inputs",
            command=self.refresh_input_devices,
        ).pack(side="left")

        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True, pady=(14, 10))

        left = ttk.Frame(panes)
        right = ttk.Frame(panes)
        panes.add(left, weight=3)
        panes.add(right, weight=2)

        ttk.Label(left, text="Live transcript").pack(anchor="w")
        self.transcript = tk.Text(left, wrap="word", font=("Helvetica", 14))
        self.transcript.pack(fill="both", expand=True, pady=(6, 0))

        ttk.Label(right, text="Translation / glossary support").pack(anchor="w")
        self.translation = tk.Text(right, wrap="word", font=("Helvetica", 13))
        self.translation.pack(fill="both", expand=True, pady=(6, 0))

        status_bar = ttk.Label(root, textvariable=self.status, anchor="w")
        status_bar.pack(fill="x")

    def start_listening(self) -> None:
        # Read Tk variables on the UI thread; workers use these plain values.
        self.active_language = self.spoken_language.get()
        self.active_source, self.active_target = self.translation_direction.get().split("-")
        self._clear_queue(self.audio_jobs)
        self.listening = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        device_index = self._selected_device_index()
        device_name = self.input_device_label.get()
        self.status.set(f"Listening for complete phrases from {device_name}; waiting for pauses to transcribe...")
        self.audio.start(device_index=device_index)

    def stop_listening(self) -> None:
        self.listening = False
        self.audio.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status.set("Stopped.")

    def clear_text(self) -> None:
        self.transcript.delete("1.0", "end")
        self.translation.delete("1.0", "end")
        self.status.set("Cleared.")

    def save_transcript(self) -> None:
        default_name = f"interpreting_notes_{dt.datetime.now():%Y%m%d_%H%M%S}.txt"
        path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            return

        content = [
            APP_TITLE,
            f"Saved: {dt.datetime.now():%Y-%m-%d %H:%M:%S}",
            "",
            "Transcript:",
            self.transcript.get("1.0", "end").strip(),
            "",
            "Translation / glossary support:",
            self.translation.get("1.0", "end").strip(),
        ]
        Path(path).write_text("\n".join(content), encoding="utf-8")
        self.status.set(f"Saved to {path}")

    def refresh_input_devices(self) -> None:
        current = self.input_device_label.get()
        self._load_input_devices()
        labels = self._input_device_labels()
        self.input_device.configure(values=labels)
        if current in labels:
            self.input_device_label.set(current)
        else:
            self.input_device_label.set(labels[0])
        self.status.set("Audio inputs refreshed.")

    def _load_input_devices(self) -> None:
        self.input_devices = list_input_devices()

    def _input_device_labels(self) -> tuple[str, ...]:
        labels = ["Default input"]
        for device in self.input_devices:
            labels.append(
                f"{device['index']}: {device['name']} ({device['channels']} input ch)"
            )
        return tuple(labels)

    def _selected_device_index(self) -> int | None:
        label = self.input_device_label.get()
        if label == "Default input":
            return None
        try:
            return int(label.split(":", 1)[0])
        except ValueError:
            return None

    @staticmethod
    def _clear_queue(work_queue: queue.Queue) -> None:
        while True:
            try:
                work_queue.get_nowait()
            except queue.Empty:
                return

    def _handle_audio_chunk(self, samples) -> None:
        # AudioCapture calls this only after a phrase-ending pause (or when Stop
        # flushes a phrase). Keep every completed phrase; never silently discard
        # audio in a medical interpreting workflow.
        self.audio_jobs.put(
            (samples, self.active_language, self.active_source, self.active_target)
        )

    def _handle_audio_error(self, message: str) -> None:
        self.events.put(("error", message))

    def _transcription_worker(self) -> None:
        while True:
            samples, language, source, target = self.audio_jobs.get()
            try:
                text = self.transcriber.transcribe_audio(samples, language)
                if not text:
                    self.events.put(("status", "No speech detected in that chunk."))
                    continue

                # Show the transcript immediately; translation runs independently.
                self.events.put(("transcript", text))
                self.translation_jobs.put((text, source, target))
            except Exception as exc:
                self.events.put(("status", f"Transcription failed: {exc}"))
            finally:
                self.audio_jobs.task_done()

    def _translation_worker(self) -> None:
        while True:
            text, source, target = self.translation_jobs.get()
            try:
                translated = self.translator.translate(text, source, target)
                self.events.put(("translation", translated))
            except Exception as exc:
                self.events.put(("status", f"Translation failed: {exc}"))
            finally:
                self.translation_jobs.task_done()

    def _drain_events(self) -> None:
        while True:
            try:
                event_type, payload = self.events.get_nowait()
            except queue.Empty:
                break

            if event_type == "transcript":
                timestamp = dt.datetime.now().strftime("%H:%M:%S")
                self.transcript.insert("end", f"[{timestamp}] {payload}\n\n")
                self.transcript.see("end")
            elif event_type == "translation":
                self.translation.insert("end", f"{payload}\n\n")
                self.translation.see("end")
            elif event_type == "status":
                self.status.set(payload)
            elif event_type == "error":
                self.stop_listening()
                self.status.set(payload)
                messagebox.showerror(APP_TITLE, payload)

        self.after(50, self._drain_events)


if __name__ == "__main__":
    app = LiveInterpreterApp()
    app.mainloop()
