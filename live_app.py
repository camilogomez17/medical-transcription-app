"""Desktop prototype for live medical interpreting support."""

from __future__ import annotations

import datetime as dt
import itertools
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from audio_capture import AudioCapture, list_input_devices
from transcription_engine import TranscriptionEngine
from translation_engine import TranslationEngine

APP_TITLE = "Medical Interpreting Live Transcription"
SUPPORTED_LANGUAGES = {"en", "es"}


def opposite_language(language: str) -> str:
    """Return the other supported language, defaulting unknown input to English."""
    return "es" if language == "en" else "en"


class LiveInterpreterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(960, 640)

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.audio_jobs: queue.Queue[tuple[int, object]] = queue.Queue()
        self.translation_jobs: queue.Queue[
            tuple[int, str, str, str, str, int]
        ] = queue.Queue()
        self.transcriber = TranscriptionEngine(model_size="base")
        self.translator = TranslationEngine()
        self.audio = AudioCapture(
            self._handle_audio_chunk,
            self._handle_audio_error,
            silence_seconds=0.8,
            preroll_seconds=0.3,
        )
        self.listening = False
        self.session_id = 0
        self.segment_ids = itertools.count(1)
        self.records: dict[str, dict[str, object]] = {}
        self.input_devices: list[dict[str, object]] = []

        self.input_device_label = tk.StringVar(value="Default input")
        self.selected_language = tk.StringVar(value="en")
        self.status = tk.StringVar(value=self._startup_status())

        self._load_input_devices()
        self._build_ui()
        threading.Thread(target=self._transcription_worker, daemon=True).start()
        threading.Thread(target=self._translation_worker, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(50, self._drain_events)

    def _startup_status(self) -> str:
        if self.transcriber.ready:
            return "Ready. Language detection is automatic for each utterance."
        return f"Setup needed: {self.transcriber.error}"

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        controls = ttk.Frame(root)
        controls.pack(fill="x")

        self.start_button = ttk.Button(
            controls, text="Start Listening", command=self.start_listening
        )
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(
            controls, text="Stop", command=self.stop_listening, state="disabled"
        )
        self.stop_button.pack(side="left", padx=(8, 16))

        ttk.Label(controls, text="Audio input").pack(side="left")
        self.input_device = ttk.Combobox(
            controls,
            textvariable=self.input_device_label,
            values=self._input_device_labels(),
            state="readonly",
            width=42,
        )
        self.input_device.pack(side="left", padx=8)
        ttk.Button(
            controls, text="Refresh Inputs", command=self.refresh_input_devices
        ).pack(side="left")

        ttk.Button(controls, text="Save Session", command=self.save_transcript).pack(
            side="right"
        )
        ttk.Button(controls, text="Clear", command=self.clear_text).pack(
            side="right", padx=8
        )

        ttk.Label(
            root,
            text=(
                "Each utterance is detected independently. Select a row to correct "
                "its transcript; its translation will be regenerated."
            ),
            wraplength=1200,
        ).pack(anchor="w", pady=(10, 6))

        table_frame = ttk.Frame(root)
        table_frame.pack(fill="both", expand=True)

        columns = ("language", "transcript", "translation", "status")
        self.segments = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.segments.heading("language", text="Source")
        self.segments.heading("transcript", text="Transcript (editable below)")
        self.segments.heading("translation", text="Translation")
        self.segments.heading("status", text="Status")
        self.segments.column("language", width=70, minwidth=60, stretch=False)
        self.segments.column("transcript", width=360, minwidth=180)
        self.segments.column("translation", width=440, minwidth=180)
        self.segments.column("status", width=180, minwidth=130, stretch=False)
        y_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.segments.yview
        )
        x_scroll = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.segments.xview
        )
        self.segments.configure(
            yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set
        )
        self.segments.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.segments.bind("<<TreeviewSelect>>", self._on_segment_selected)

        editor = ttk.LabelFrame(root, text="Correct selected utterance", padding=8)
        editor.pack(fill="x", pady=(10, 0))
        editor_controls = ttk.Frame(editor)
        editor_controls.pack(fill="x")
        ttk.Label(editor_controls, text="Detected / source language").pack(side="left")
        self.language_picker = ttk.Combobox(
            editor_controls,
            textvariable=self.selected_language,
            values=("en", "es"),
            state="readonly",
            width=8,
        )
        self.language_picker.pack(side="left", padx=8)
        ttk.Label(
            editor_controls,
            text="Changing the language also regenerates the translation.",
        ).pack(side="left", padx=8)
        self.apply_button = ttk.Button(
            editor_controls,
            text="Apply correction & retranslate",
            command=self.apply_correction,
            state="disabled",
        )
        self.apply_button.pack(side="right")

        self.transcript_editor = tk.Text(
            editor, height=4, wrap="word", font=("Helvetica", 13), undo=True
        )
        self.transcript_editor.pack(fill="x", expand=False, pady=(6, 0))

        ttk.Label(
            editor,
            text=(
                "If local translation packages are unavailable, the result will be "
                "labeled as glossary-only reference, not a full translation."
            ),
            wraplength=1200,
        ).pack(anchor="w", pady=(6, 0))

        ttk.Label(root, textvariable=self.status, anchor="w").pack(
            fill="x", pady=(8, 0)
        )

    def start_listening(self) -> None:
        if not self.transcriber.ready:
            messagebox.showerror(
                APP_TITLE,
                "Speech recognition is not ready. Install dependencies and restart. "
                f"Details: {self.transcriber.error}",
            )
            return
        self.listening = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        device_name = self.input_device_label.get()
        self.status.set(
            f"Listening on {device_name}. Detecting English or Spanish automatically."
        )
        self.audio.start(device_index=self._selected_device_index())

    def stop_listening(self) -> None:
        self.listening = False
        self.audio.stop()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status.set("Stopped. Any final utterance is being processed.")

    def clear_text(self) -> None:
        self.session_id += 1
        self._clear_queue(self.audio_jobs)
        self._clear_queue(self.translation_jobs)
        self.records.clear()
        for item in self.segments.get_children():
            self.segments.delete(item)
        self.transcript_editor.delete("1.0", "end")
        self.apply_button.configure(state="disabled")
        self.status.set("Session cleared.")

    def save_transcript(self) -> None:
        default_name = f"interpreting_session_{dt.datetime.now():%Y%m%d_%H%M%S}.txt"
        path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            return

        lines = [
            APP_TITLE,
            f"Saved: {dt.datetime.now():%Y-%m-%d %H:%M:%S}",
            "",
        ]
        for segment_id in self.segments.get_children():
            record = self.records.get(segment_id)
            if record is None:
                continue
            lines.extend(
                [
                    f"[{record['timestamp']}] {str(record['source']).upper()}",
                    f"Transcript: {record['transcript']}",
                ]
            )
            if record["original"] != record["transcript"]:
                lines.append(f"Initial recognition: {record['original']}")
            lines.append(f"Translation ({opposite_language(str(record['source']))}):")
            lines.append(str(record["translation"]))
            lines.append(f"Status: {record['status']}")
            lines.append("")
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        self.status.set(f"Session saved to {path}")

    def refresh_input_devices(self) -> None:
        current = self.input_device_label.get()
        self._load_input_devices()
        labels = self._input_device_labels()
        self.input_device.configure(values=labels)
        self.input_device_label.set(current if current in labels else labels[0])
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
        self.audio_jobs.put((self.session_id, samples))

    def _handle_audio_error(self, message: str) -> None:
        self.events.put(("error", (self.session_id, message)))

    def _transcription_worker(self) -> None:
        while True:
            session_id, samples = self.audio_jobs.get()
            try:
                text, detected_language, probability = (
                    self.transcriber.transcribe_audio(samples, language=None)
                )
                if not text:
                    self.events.put(
                        ("status", (session_id, "No speech detected in that utterance."))
                    )
                    continue

                source = detected_language if detected_language in SUPPORTED_LANGUAGES else "en"
                segment_id = str(next(self.segment_ids))
                self.events.put(
                    (
                        "new_segment",
                        (
                            session_id,
                            segment_id,
                            text,
                            source,
                            probability,
                        ),
                    )
                )
                self.translation_jobs.put(
                    (
                        session_id,
                        segment_id,
                        text,
                        source,
                        opposite_language(source),
                        0,
                    )
                )
            except Exception as exc:
                self.events.put(
                    ("status", (session_id, f"Transcription failed: {exc}"))
                )
            finally:
                self.audio_jobs.task_done()

    def _translation_worker(self) -> None:
        while True:
            session_id, segment_id, text, source, target, revision = (
                self.translation_jobs.get()
            )
            try:
                translated = self.translator.translate(text, source, target)
                self.events.put(
                    (
                        "translation",
                        (session_id, segment_id, revision, translated),
                    )
                )
            except Exception as exc:
                self.events.put(
                    (
                        "translation_error",
                        (session_id, segment_id, revision, str(exc)),
                    )
                )
            finally:
                self.translation_jobs.task_done()

    def _on_segment_selected(self, _event=None) -> None:
        selection = self.segments.selection()
        if not selection:
            self.apply_button.configure(state="disabled")
            return
        record = self.records.get(selection[0])
        if record is None:
            return
        self.transcript_editor.delete("1.0", "end")
        self.transcript_editor.insert("1.0", str(record["transcript"]))
        self.selected_language.set(str(record["source"]))
        self.apply_button.configure(state="normal")

    def apply_correction(self) -> None:
        selection = self.segments.selection()
        if not selection:
            return
        segment_id = selection[0]
        record = self.records.get(segment_id)
        if record is None:
            return
        corrected_text = self.transcript_editor.get("1.0", "end-1c").strip()
        if not corrected_text:
            messagebox.showwarning(APP_TITLE, "The transcript cannot be empty.")
            return
        source = self.selected_language.get()
        if source not in SUPPORTED_LANGUAGES:
            messagebox.showwarning(APP_TITLE, "Choose English or Spanish.")
            return

        record["transcript"] = corrected_text
        record["source"] = source
        record["revision"] = int(record["revision"]) + 1
        record["translation"] = "Updating translation…"
        record["status"] = "Translating correction…"
        self._refresh_row(segment_id, record)
        self.translation_jobs.put(
            (
                self.session_id,
                segment_id,
                corrected_text,
                source,
                opposite_language(source),
                int(record["revision"]),
            )
        )
        self.status.set("Correction saved. Regenerating translation.")
        
    def _refresh_row(self, segment_id: str, record: dict[str, object]) -> None:
        self.segments.item(
            segment_id,
            values=(
                str(record["source"]).upper(),
                str(record["transcript"]),
                str(record["translation"]),
                str(record["status"]),
            ),
        )

    def _drain_events(self) -> None:
        while True:
            try:
                event_type, payload = self.events.get_nowait()
            except queue.Empty:
                break

            if event_type == "new_segment":
                session_id, segment_id, text, source, probability = payload
                if session_id != self.session_id:
                    continue
                confidence = float(probability)
                status = "Ready for translation"
                if confidence < 0.55:
                    status = f"Review language ({confidence:.0%} confidence)"
                record: dict[str, object] = {
                    "timestamp": dt.datetime.now().strftime("%H:%M:%S"),
                    "original": text,
                    "transcript": text,
                    "source": source,
                    "translation": "Translating…",
                    "status": status,
                    "revision": 0,
                    "language_probability": confidence,
                }
                self.records[segment_id] = record
                self.segments.insert(
                    "",
                    "end",
                    iid=segment_id,
                    values=(source.upper(), text, "Translating…", status),
                )
                self.segments.see(segment_id)
            elif event_type == "translation":
                session_id, segment_id, revision, translated = payload
                if session_id != self.session_id:
                    continue
                record = self.records.get(segment_id)
                if record is None or revision != record["revision"]:
                    continue
                record["translation"] = translated
                if str(translated).startswith("[GLOSSARY ONLY"):
                    record["status"] = "Glossary only — verify"
                elif float(record["language_probability"]) < 0.55:
                    record["status"] = "Translation ready; verify language"
                else:
                    record["status"] = "Translation ready"
                self._refresh_row(segment_id, record)
            elif event_type == "translation_error":
                session_id, segment_id, revision, error = payload
                if session_id != self.session_id:
                    continue
                record = self.records.get(segment_id)
                if record is None or revision != record["revision"]:
                    continue
                record["translation"] = f"Translation failed: {error}"
                record["status"] = "Translation error"
                self._refresh_row(segment_id, record)
            elif event_type in {"status", "error"}:
                session_id, message = payload
                if session_id != self.session_id:
                    continue
                self.status.set(message)
                if event_type == "error":
                    self.stop_listening()
                    messagebox.showerror(APP_TITLE, message)

        self.after(50, self._drain_events)

    def _on_close(self) -> None:
        self.listening = False
        self.audio.stop()
        self.destroy()


if __name__ == "__main__":
    app = LiveInterpreterApp()
    app.mainloop()
