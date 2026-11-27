"""Simple native Windows-friendly GUI. No web server or video uploads required."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import (
    ClutchSiftError, Highlight, burn_subtitles, export_clip, find_highlights,
    pretty_time, create_run_folder, validate_segment, write_manifest,
)
from .hybrid import find_hybrid_highlights
from .ai_scan import find_ai_highlights, VisionHighlight

BG = "#0d1220"
PANEL = "#171f31"
FG = "#edf3ff"
MUTED = "#aebbd3"
ACCENT = "#628dff"


class ClutchSiftApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("ClutchSift — Local Gaming Clipper")
        self.root.geometry("940x820")
        self.root.minsize(780, 710)
        self.root.configure(bg=BG)
        self.video: Path | None = None
        self.duration = 0.0
        self.highlights: list[Highlight] = []
        self.is_busy = False
        self.num = tk.StringVar(value="5")
        self.length = tk.StringVar(value="30")
        self.vertical = tk.BooleanVar(value=True)
        self.layout = tk.StringVar(value="fit-blur")
        self.encoder = tk.StringVar(value="cpu")
        self.captions = tk.BooleanVar(value=False)
        self.burn = tk.BooleanVar(value=False)
        self.scan_mode = tk.StringVar(value="Audio + motion")
        self.focus = tk.StringVar()
        self.karaoke = tk.BooleanVar(value=False)
        self.titles = tk.BooleanVar(value=False)
        self.asr_model = tk.StringVar(value="small")
        self.start_edit = tk.StringVar(value="")
        self.end_edit = tk.StringVar(value="")
        self.status = tk.StringVar(value="Choose a recording to begin. Files stay on your computer.")
        self.path_label = tk.StringVar(value="No recording selected")
        self._build_ui()

    def _label(self, parent: tk.Widget, text: str, *, size=11, color=FG, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", BG), fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def _button(self, parent: tk.Widget, text: str, command, *, primary=False, width=None):
        button = tk.Button(parent, text=text, command=command, width=width,
                           fg="white" if primary else FG, bg=ACCENT if primary else PANEL,
                           activeforeground="white", activebackground="#466cd1",
                           relief="flat", cursor="hand2", borderwidth=0,
                           padx=16, pady=9, font=("Segoe UI", 10, "bold"))
        return button

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG, padx=25, pady=21)
        outer.pack(fill="both", expand=True)
        self._label(outer, "CLUTCHSIFT", size=25, bold=True, color=ACCENT).pack(anchor="w")
        self._label(outer, "Find candidate gaming moments • Review • Export vertical Shorts",
                    size=11, color=MUTED).pack(anchor="w", pady=(0, 20))

        top = tk.Frame(outer, bg=PANEL, padx=16, pady=16)
        top.pack(fill="x")
        self.open_btn = self._button(top, "1  Open recording", self.choose_video, primary=True)
        self.open_btn.pack(side="left")
        self._label(top, "  ", bg=PANEL).pack(side="left")
        self._label(top, "", bg=PANEL, color=MUTED).pack(side="left")
        tk.Label(top, textvariable=self.path_label, bg=PANEL, fg=MUTED,
                 anchor="w", font=("Segoe UI", 10), wraplength=560).pack(side="left", fill="x", expand=True)

        options = tk.Frame(outer, bg=BG)
        options.pack(fill="x", pady=(17, 8))
        self._label(options, "Candidates:", color=MUTED).pack(side="left")
        tk.Entry(options, textvariable=self.num, width=4, font=("Segoe UI", 11)).pack(side="left", padx=(7, 22))
        self._label(options, "Clip length (seconds):", color=MUTED).pack(side="left")
        tk.Entry(options, textvariable=self.length, width=5, font=("Segoe UI", 11)).pack(side="left", padx=(7, 22))
        self.scan_btn = self._button(options, "2  Find moments", self.analyze, primary=True)
        self.scan_btn.pack(side="right")

        self._label(outer, "Suggested moments", bold=True, size=13).pack(anchor="w", pady=(16, 6))
        self._label(outer, "Audio/visual activity is only a suggestion, not a guarantee. Double-click to preview.",
                    size=9, color=MUTED).pack(anchor="w", pady=(0, 8))

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Clip.Treeview", background=PANEL, fieldbackground=PANEL, foreground=FG,
                        borderwidth=0, rowheight=32, font=("Segoe UI", 10))
        style.configure("Clip.Treeview.Heading", background="#28354d", foreground=FG,
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Clip.Treeview", background=[("selected", "#31509b")])
        self.tree = ttk.Treeview(outer, style="Clip.Treeview", selectmode="extended", height=7,
                                 columns=("no", "start", "end", "db", "method"), show="headings")
        for name, title, width in [
            ("no", "#", 55), ("start", "Start", 115), ("end", "End", 115),
            ("db", "Audio jump", 110), ("method", "Detection method", 210),
        ]:
            self.tree.heading(name, text=title)
            self.tree.column(name, width=width, minwidth=55, anchor="center" if name != "method" else "w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        self.tree.bind("<Double-Button-1>", lambda event: self.preview())

        edit = tk.Frame(outer, bg=BG)
        edit.pack(fill="x", pady=(12, 8))
        self._label(edit, "Start (sec):", color=MUTED).pack(side="left")
        tk.Entry(edit, textvariable=self.start_edit, width=11).pack(side="left", padx=(6, 18))
        self._label(edit, "End (sec):", color=MUTED).pack(side="left")
        tk.Entry(edit, textvariable=self.end_edit, width=11).pack(side="left", padx=(6, 18))
        self.apply_btn = self._button(edit, "Apply trim", self.apply_edit)
        self.apply_btn.pack(side="left")
        self.preview_btn = self._button(edit, "▶  Preview", self.preview)
        self.preview_btn.pack(side="right")

        output = tk.Frame(outer, bg=PANEL, padx=16, pady=12)
        output.pack(fill="x", pady=(10, 6))
        scan_row = tk.Frame(output, bg=PANEL)
        scan_row.pack(fill="x")
        self._label(scan_row, "Find moments using", bg=PANEL).pack(side="left")
        mode = ttk.Combobox(scan_row, textvariable=self.scan_mode, state="readonly",
                            values=("Audio + motion", "Audio only", "Local AI vision"), width=16)
        mode.pack(side="left", padx=6)
        self._label(scan_row, "AI focus", bg=PANEL).pack(side="left")
        focus = ttk.Entry(scan_row, textvariable=self.focus, state="disabled")
        focus.pack(side="left", fill="x", expand=True, padx=6)
        mode.bind("<<ComboboxSelected>>", lambda _: focus.configure(
            state="normal" if self.scan_mode.get() == "Local AI vision" else "disabled"))
        format_row = tk.Frame(output, bg=PANEL)
        format_row.pack(fill="x")
        tk.Checkbutton(format_row, text="Vertical 9:16", variable=self.vertical,
                       bg=PANEL, fg=FG, selectcolor=PANEL, activebackground=PANEL,
                       activeforeground=FG, font=("Segoe UI", 10)).pack(side="left")
        ttk.Combobox(format_row, textvariable=self.layout, values=("fit-blur", "center-crop"),
                     state="readonly", width=13).pack(side="left", padx=6)
        self._label(format_row, "Encoder", bg=PANEL).pack(side="left", padx=(16, 4))
        ttk.Combobox(format_row, textvariable=self.encoder, values=("cpu", "nvenc"),
                     state="readonly", width=7).pack(side="left")
        tk.Checkbutton(output, text="Generate captions (requires optional faster-whisper)", variable=self.captions,
                       bg=PANEL, fg=FG, selectcolor=PANEL, activebackground=PANEL,
                       activeforeground=FG, font=("Segoe UI", 10)).pack(anchor="w")
        tk.Checkbutton(output, text="Burn captions onto video (if generated)", variable=self.burn,
                       bg=PANEL, fg=FG, selectcolor=PANEL, activebackground=PANEL,
                       activeforeground=FG, font=("Segoe UI", 10)).pack(anchor="w")
        tk.Checkbutton(output, text="Word-highlight karaoke captions (experimental)", variable=self.karaoke,
                       bg=PANEL, fg=FG, selectcolor=PANEL, activebackground=PANEL,
                       activeforeground=FG, font=("Segoe UI", 10)).pack(anchor="w")
        tk.Checkbutton(output, text="Suggest titles/descriptions (requires Ollama + speech model)", variable=self.titles,
                       bg=PANEL, fg=FG, selectcolor=PANEL, activebackground=PANEL,
                       activeforeground=FG, font=("Segoe UI", 10)).pack(anchor="w")

        bottom = tk.Frame(outer, bg=BG)
        bottom.pack(fill="x", pady=(10, 8))
        self.export_btn = self._button(bottom, "3  Export selected (or all)", self.export, primary=True)
        self.export_btn.pack(side="right")
        self.progress = ttk.Progressbar(bottom, mode="indeterminate", length=160)
        self.progress.pack(side="left", padx=(0, 12))
        self._label(outer, "Runs locally  •  No account  •  No API key  •  Preview requires FFplay",
                    size=9, color=MUTED).pack(anchor="w", pady=(0, 6))
        tk.Label(outer, textvariable=self.status, bg=BG, fg=ACCENT,
                 font=("Segoe UI", 10), anchor="w", wraplength=820).pack(fill="x")

    def _set_busy(self, busy: bool, note: str = "") -> None:
        self.is_busy = busy
        for button in (self.open_btn, self.scan_btn, self.export_btn, self.apply_btn, self.preview_btn):
            button.configure(state="disabled" if busy else "normal")
        self.progress.start(14) if busy else self.progress.stop()
        if note:
            self.status.set(note)

    def _run_background(self, worker, on_success, note: str):
        if self.is_busy:
            return
        self._set_busy(True, note)

        def task():
            try:
                result = worker()
            except Exception as exc:
                self.root.after(0, lambda error=str(exc): self._failure(error))
            else:
                self.root.after(0, lambda value=result: self._success(on_success, value))

        threading.Thread(target=task, daemon=True).start()

    def _failure(self, error: str):
        self._set_busy(False, "Operation failed. Check the details and try again.")
        messagebox.showerror("ClutchSift", error)

    def _success(self, callback, result):
        self._set_busy(False)
        callback(result)

    def choose_video(self):
        source = filedialog.askopenfilename(
            title="Select your gameplay recording",
            filetypes=[("Video", "*.mp4 *.mov *.mkv *.webm *.avi *.m4v"), ("All files", "*.*")],
        )
        if not source:
            return
        self.video = Path(source)
        self.path_label.set(self.video.name)
        self.highlights = []
        self.duration = 0
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status.set("Recording selected. Click 'Find moments'.")

    def analyze(self):
        if self.video is None:
            messagebox.showinfo("Choose a file", "Select a gameplay recording first.")
            return
        try:
            length = float(self.length.get())
            count = int(self.num.get())
        except ValueError:
            messagebox.showerror("Invalid settings", "Clip length and number must be numeric.")
            return
        video = self.video
        if self.scan_mode.get() == "Local AI vision":
            focus = self.focus.get()
            def progress(note):
                self.root.after(0, self.status.set, note)
            self._run_background(lambda: find_ai_highlights(video, length, count, focus=focus,
                                 progress=progress), self._show_results, "Preparing local AI scan…")
            return
        method = find_hybrid_highlights if self.scan_mode.get() == "Audio + motion" else find_highlights
        self._run_background(lambda: method(video, length, count), self._show_results,
                             "Scanning audio and/or motion... Long recordings can take a while.")

    def _show_results(self, result):
        self.duration, self.highlights = result
        self._refresh_table()
        count = len(self.highlights)
        method = self.highlights[0].method if self.highlights else "no signals"
        self.status.set(f"Found {count} candidate clips using {method}. Recording: {pretty_time(self.duration)}. Review before sharing.")

    def _refresh_table(self, selection: tuple[str, ...] = ()):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, clip in enumerate(self.highlights):
            activity = f"+{clip.jump_db:.1f} dB" if "audio" in clip.method else "N/A"
            label = clip.method
            if isinstance(clip, VisionHighlight):
                label = f"AI match {clip.score}/4"
            self.tree.insert("", "end", iid=str(i), values=(i + 1, pretty_time(clip.start), pretty_time(clip.end), activity, label))
        for iid in selection:
            if self.tree.exists(iid):
                self.tree.selection_add(iid)

    def _selected(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        clip = self.highlights[int(selected[0])]
        self.start_edit.set(f"{clip.start:.2f}")
        self.end_edit.set(f"{clip.end:.2f}")
        if isinstance(clip, VisionHighlight):
            self.status.set(clip.evidence)

    def _range(self) -> tuple[float, float]:
        try:
            start = float(self.start_edit.get())
            end = float(self.end_edit.get())
        except ValueError as exc:
            raise ClutchSiftError("Start and end must be numbers in seconds.") from exc
        return validate_segment(start, end, self.duration)

    def apply_edit(self):
        selected = self.tree.selection()
        if len(selected) != 1:
            messagebox.showinfo("Select one", "Select one clip, then edit its start/end.")
            return
        try:
            start, end = self._range()
        except ClutchSiftError as exc:
            messagebox.showerror("Invalid range", str(exc))
            return
        index = int(selected[0])
        self.highlights[index] = replace(self.highlights[index], start=round(start, 2), end=round(end, 2))
        self._refresh_table((str(index),))
        self.status.set("Trim updated. Export to render the revised clip.")

    def preview(self):
        if self.video is None or not self.tree.selection():
            messagebox.showinfo("Choose moment", "Select a suggested moment first.")
            return
        player = shutil.which("ffplay")
        if player is None:
            messagebox.showinfo("Preview player missing", "FFplay was not found on PATH. You can still export and review clips in your video player. Install an FFmpeg build that includes ffplay for instant preview.")
            return
        try:
            start, end = self._range()
        except ClutchSiftError as exc:
            messagebox.showerror("Invalid range", str(exc))
            return
        subprocess.Popen([player, "-autoexit", "-loglevel", "error", "-ss", str(start),
                          "-t", str(end - start), "-i", str(self.video)])

    def export(self):
        if self.video is None or not self.highlights:
            messagebox.showinfo("Nothing to export", "Find candidates first.")
            return
        chosen = sorted((int(i) for i in self.tree.selection()))
        if not chosen:
            chosen = list(range(len(self.highlights)))
        folder = filedialog.askdirectory(title="Select export folder")
        if not folder:
            return
        target = Path(folder)
        video, duration = self.video, self.duration
        snapshots = [self.highlights[i] for i in chosen]
        vertical, captions, burn = self.vertical.get(), self.captions.get(), self.burn.get()
        karaoke, titles = self.karaoke.get(), self.titles.get()
        layout, encoder = self.layout.get(), self.encoder.get()
        if burn and not captions:
            messagebox.showerror("Captions", "Enable 'Generate captions' before burning them in.")
            return

        def worker():
            run_folder = create_run_folder(target)
            result = []
            for i, candidate in enumerate(snapshots, 1):
                dest = run_folder / f"clip_{i:02}.mp4"
                export_clip(video, dest, candidate.start, candidate.end, vertical=vertical,
                            duration=duration, layout=layout, encoder=encoder)
                if captions or titles:
                    from .captions import write_captions
                    subtitle, text = write_captions(dest, style="karaoke" if karaoke else "srt")
                    if titles:
                        from .metadata import suggest_metadata, save_metadata
                        save_metadata(suggest_metadata(text), dest.with_suffix(".metadata.json"))
                    result.append(burn_subtitles(dest, subtitle) if burn else dest)
                else:
                    result.append(dest)
            write_manifest(video, snapshots, run_folder)
            return result

        self._run_background(worker, self._exported, f"Exporting {len(snapshots)} clip(s). Keep this window open.")

    def _exported(self, results):
        directory = results[0].parent if results else ""
        self.status.set(f"Exported {len(results)} clip(s) to {directory}. Check them before posting!")
        messagebox.showinfo("Export complete", f"Saved {len(results)} clip(s) in:\n{directory}\n\nReview all suggestions before posting.")

    def run(self):
        self.root.mainloop()


def main():
    ClutchSiftApp().run()
