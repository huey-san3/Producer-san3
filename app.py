"""
app.py — SAN3 Producer GUI
===========================
Floating side panel for FL Studio.
Sits beside FL Studio on screen. Always on top.
No terminal needed.

Usage:
    python app.py

Requirements:
    pip install -r requirements.txt
    (tkinter is built into Python on Windows — no install needed)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import builtins
import importlib.util
import sys
from pathlib import Path
from datetime import datetime

# Windows DPI awareness — prevents blurry/black rendering on high-DPI screens
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ── CONSTANTS ──────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

GENRES   = ["trap", "drill", "hip hop", "rnb", "melodic"]
KEYS     = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BPM_MAP  = {"trap": 140, "drill": 144, "hip hop": 90, "rnb": 85, "melodic": 140}

COLORS = {
    "bg":         "#0f0f0f",
    "panel":      "#1a1a1a",
    "border":     "#2a2a2a",
    "accent":     "#c8a96e",   # gold — SAN3 brand
    "accent_dim": "#8a6e3e",
    "text":       "#e8e8e8",
    "text_dim":   "#888888",
    "btn_bg":     "#1e1e1e",
    "btn_hover":  "#2a2a2a",
    "btn_active": "#c8a96e",
    "log_bg":     "#111111",
    "log_text":   "#00cc66",   # green terminal feel
    "error":      "#cc3333",
}

FONT_MAIN  = ("Consolas", 10)
FONT_TITLE = ("Consolas", 11, "bold")
FONT_BTN   = ("Consolas", 10, "bold")
FONT_LOG   = ("Consolas", 9)


# ── MAIN APP ───────────────────────────────────────────────────────────
class SAN3App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("SAN3 PRODUCER")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.attributes("-topmost", True)   # always on top of FL Studio

        # Position: top-right corner of screen
        self.update_idletasks()
        w, h = 640, 760
        sw = self.winfo_screenwidth()
        self.geometry(f"{w}x{h}+{sw - w - 10}+30")

        self._build_ui()
        self._init_dropdowns()
        self._log("SAN3 Producer ready.")
        self._log("Select genre, key, BPM — then hit a mode.")

    # ── UI BUILDER ─────────────────────────────────────────────────────
    def _build_ui(self):
        # ── HEADER
        header = tk.Frame(self, bg=COLORS["accent"], height=2)
        header.pack(fill="x")

        title_frame = tk.Frame(self, bg=COLORS["bg"], pady=10)
        title_frame.pack(fill="x", padx=12)

        tk.Label(title_frame, text="SAN3 PRODUCER",
                 font=("Consolas", 13, "bold"),
                 fg=COLORS["accent"], bg=COLORS["bg"]).pack(anchor="w")

        tk.Label(title_frame, text="Hip Hop  |  RnB  |  Rap  |  Trap",
                 font=("Consolas", 8),
                 fg=COLORS["text_dim"], bg=COLORS["bg"]).pack(anchor="w")

        self._divider()

        # ── CONTROLS
        ctrl = tk.Frame(self, bg=COLORS["bg"], pady=4)
        ctrl.pack(fill="x", padx=12)

        # Genre
        self._label(ctrl, "GENRE")
        self.genre_var = tk.StringVar(value="trap")
        genre_menu = ttk.Combobox(ctrl, textvariable=self.genre_var,
                                  values=GENRES, state="readonly",
                                  font=FONT_MAIN, width=52)
        genre_menu.pack(fill="x", pady=(0, 6))
        genre_menu.set("trap")
        genre_menu.bind("<<ComboboxSelected>>", self._on_genre_change)

        # Key
        self._label(ctrl, "KEY")
        self.key_var = tk.StringVar(value="F")
        key_menu = ttk.Combobox(ctrl, textvariable=self.key_var,
                                values=KEYS, state="readonly",
                                font=FONT_MAIN, width=52)
        key_menu.pack(fill="x", pady=(0, 6))
        key_menu.set("F")

        # BPM
        self._label(ctrl, "BPM")
        bpm_frame = tk.Frame(ctrl, bg=COLORS["bg"])
        bpm_frame.pack(fill="x", pady=(0, 6))

        self.bpm_var = tk.StringVar(value="140")
        bpm_entry = tk.Entry(bpm_frame, textvariable=self.bpm_var,
                             font=FONT_MAIN, width=8,
                             bg=COLORS["panel"], fg=COLORS["text"],
                             insertbackground=COLORS["accent"],
                             relief="flat", bd=4)
        bpm_entry.pack(side="left")

        tk.Label(bpm_frame, text="  BPM",
                 font=FONT_MAIN, fg=COLORS["text_dim"],
                 bg=COLORS["bg"]).pack(side="left")

        self._divider()

        # ── MODE BUTTONS
        modes_frame = tk.Frame(self, bg=COLORS["bg"], pady=4)
        modes_frame.pack(fill="x", padx=12)

        self._label(modes_frame, "MODES")

        # Row 1
        row1 = tk.Frame(modes_frame, bg=COLORS["bg"])
        row1.pack(fill="x", pady=2)
        self._mode_btn(row1, "BEAT BLOCK", self._run_beat_block, side="left")
        self._mode_btn(row1, "808 DIAL",   self._run_808_dial,   side="right")

        # Row 2
        row2 = tk.Frame(modes_frame, bg=COLORS["bg"])
        row2.pack(fill="x", pady=2)
        self._mode_btn(row2, "DRUM BUILD", self._run_drum_build, side="left")
        self._mode_btn(row2, "MIDI GEN",   self._run_midi_gen,   side="right")

        # Row 3 — full width
        row3 = tk.Frame(modes_frame, bg=COLORS["bg"])
        row3.pack(fill="x", pady=2)
        self._mode_btn_full(row3, "MIX CHAIN", self._run_mix_chain)

        self._divider()

        # ── MIDI TYPE (for MIDI Gen)
        midi_frame = tk.Frame(self, bg=COLORS["bg"], pady=2)
        midi_frame.pack(fill="x", padx=12)

        self._label(midi_frame, "MIDI TYPE  (for MIDI Gen)")
        self.midi_type_var = tk.StringVar(value="1")
        midi_types = [
            ("Melody",     "1"),
            ("Chords",     "2"),
            ("Bass Line",  "3"),
            ("Counter",    "4"),
        ]
        midi_row = tk.Frame(midi_frame, bg=COLORS["bg"])
        midi_row.pack(fill="x")
        for label, val in midi_types:
            rb = tk.Radiobutton(midi_row, text=label, variable=self.midi_type_var,
                                value=val, font=("Consolas", 8),
                                fg=COLORS["text_dim"], bg=COLORS["bg"],
                                selectcolor=COLORS["panel"],
                                activebackground=COLORS["bg"],
                                activeforeground=COLORS["accent"])
            rb.pack(side="left", padx=2)

        # Bars
        bars_frame = tk.Frame(self, bg=COLORS["bg"], pady=2)
        bars_frame.pack(fill="x", padx=12)
        self._label(bars_frame, "BARS  (for MIDI Gen)")
        self.bars_var = tk.StringVar(value="4")
        for b in ["4", "8"]:
            rb = tk.Radiobutton(bars_frame, text=f"{b} bars",
                                variable=self.bars_var, value=b,
                                font=("Consolas", 8),
                                fg=COLORS["text_dim"], bg=COLORS["bg"],
                                selectcolor=COLORS["panel"],
                                activebackground=COLORS["bg"],
                                activeforeground=COLORS["accent"])
            rb.pack(side="left", padx=4)

        self._divider()

        # ── OUTPUT LOG
        log_frame = tk.Frame(self, bg=COLORS["bg"], pady=4)
        log_frame.pack(fill="both", expand=True, padx=12)

        log_header = tk.Frame(log_frame, bg=COLORS["bg"])
        log_header.pack(fill="x")
        self._label(log_header, "OUTPUT LOG")
        tk.Button(log_header, text="CLEAR",
                  font=("Consolas", 7), fg=COLORS["text_dim"],
                  bg=COLORS["bg"], bd=0, cursor="hand2",
                  activebackground=COLORS["bg"],
                  activeforeground=COLORS["accent"],
                  command=self._clear_log).pack(side="right")

        self.log_box = scrolledtext.ScrolledText(
            log_frame, height=8, font=FONT_LOG,
            bg=COLORS["log_bg"], fg=COLORS["log_text"],
            insertbackground=COLORS["accent"],
            relief="flat", bd=4, wrap="word",
            state="disabled"
        )
        self.log_box.pack(fill="both", expand=True)

        # ── OUTPUT FOLDER BUTTON
        tk.Button(self, text="OPEN OUTPUTS FOLDER",
                  font=("Consolas", 8), fg=COLORS["text_dim"],
                  bg=COLORS["bg"], bd=0, cursor="hand2",
                  activebackground=COLORS["bg"],
                  activeforeground=COLORS["accent"],
                  command=self._open_outputs).pack(pady=6)

        # ── Style dropdowns
        self._style_comboboxes()

    # ── WIDGET HELPERS ─────────────────────────────────────────────────
    def _label(self, parent, text):
        tk.Label(parent, text=text, font=("Consolas", 7, "bold"),
                 fg=COLORS["accent_dim"], bg=COLORS["bg"]).pack(anchor="w")

    def _divider(self):
        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", pady=6)

    def _mode_btn(self, parent, text, cmd, side):
        btn = tk.Button(parent, text=text, font=FONT_BTN,
                        fg=COLORS["text"], bg=COLORS["btn_bg"],
                        activebackground=COLORS["accent"],
                        activeforeground=COLORS["bg"],
                        relief="flat", bd=0, padx=8, pady=8,
                        cursor="hand2", command=cmd, width=12)
        btn.pack(side=side, expand=True, fill="x",
                 padx=(0 if side == "right" else 0, 2 if side == "left" else 0))
        self._btn_hover(btn)

    def _mode_btn_full(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=FONT_BTN,
                        fg=COLORS["text"], bg=COLORS["btn_bg"],
                        activebackground=COLORS["accent"],
                        activeforeground=COLORS["bg"],
                        relief="flat", bd=0, padx=8, pady=8,
                        cursor="hand2", command=cmd)
        btn.pack(fill="x")
        self._btn_hover(btn)

    def _btn_hover(self, btn):
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["btn_hover"],
                                                  fg=COLORS["accent"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["btn_bg"],
                                                  fg=COLORS["text"]))

    def _style_comboboxes(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=COLORS["panel"],
                        background=COLORS["panel"],
                        foreground=COLORS["text"],
                        selectbackground=COLORS["accent"],
                        selectforeground=COLORS["bg"],
                        bordercolor=COLORS["border"],
                        arrowcolor=COLORS["accent"],
                        relief="flat")
        style.map("TCombobox",
                  fieldbackground=[("readonly", COLORS["panel"])],
                  foreground=[("readonly", COLORS["text"])],
                  selectbackground=[("readonly", COLORS["accent"])],
                  selectforeground=[("readonly", COLORS["bg"])])
        self.option_add("*TCombobox*Listbox.background", COLORS["panel"])
        self.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", COLORS["bg"])

    # ── LOG ────────────────────────────────────────────────────────────
    def _log(self, msg: str, error: bool = False):
        self.log_box.configure(state="normal")
        ts  = datetime.now().strftime("%H:%M:%S")
        col = COLORS["error"] if error else COLORS["log_text"]
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.tag_add("color", "1.0", "end")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _open_outputs(self):
        import subprocess
        subprocess.Popen(f'explorer "{OUTPUT_DIR}"')

    # ── EVENTS ─────────────────────────────────────────────────────────
    def _on_genre_change(self, event=None):
        genre = self.genre_var.get()
        self.bpm_var.set(str(BPM_MAP.get(genre, 140)))

    # ── MODE RUNNERS ───────────────────────────────────────────────────
    def _get_inputs(self) -> dict:
        return {
            "genre":     self.genre_var.get(),
            "key":       self.key_var.get(),
            "bpm":       self.bpm_var.get(),
            "midi_type": self.midi_type_var.get(),
            "bars":      self.bars_var.get(),
        }

    def _run_in_thread(self, fn):
        """Run a mode in a background thread so GUI stays responsive."""
        t = threading.Thread(target=fn, daemon=True)
        t.start()

    def _run_beat_block(self):
        self._run_in_thread(self._exec_beat_block)

    def _run_808_dial(self):
        self._run_in_thread(self._exec_808_dial)

    def _run_drum_build(self):
        self._run_in_thread(self._exec_drum_build)

    def _run_midi_gen(self):
        self._run_in_thread(self._exec_midi_gen)

    def _run_mix_chain(self):
        self._run_in_thread(self._exec_mix_chain)

    # ── MODE EXECUTORS ─────────────────────────────────────────────────
    def _load_mode(self, filename: str):
        path = Path(__file__).parent / "modes" / filename
        spec = importlib.util.spec_from_file_location("mod", path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _run_mode_safe(self, mode_file, answers, done_msg):
        """Safe wrapper — saves/restores input(), logs new files, catches errors."""
        _real_input = builtins.input
        before = set(OUTPUT_DIR.iterdir())
        try:
            it = iter(answers)
            builtins.input = lambda _="": next(it, "")
            mod = self._load_mode(mode_file)
            mod.run(OUTPUT_DIR)
            new_files = sorted(f.name for f in set(OUTPUT_DIR.iterdir()) - before)
            for f in new_files:
                self._log(f"  -> {f}")
            self._log(done_msg)
        except Exception as e:
            self._log(f"ERROR: {e}", error=True)
        finally:
            builtins.input = _real_input  # always restored

    def _list_new_outputs(self, before):
        return [f.name for f in set(OUTPUT_DIR.iterdir()) - before]

    def _exec_beat_block(self):
        inp = self._get_inputs()
        self._log(f"Beat Block -> {inp['genre'].upper()} {inp['bpm']} BPM {inp['key']}")
        self._run_mode_safe("beat_block.py",
                            [inp["genre"], inp["bpm"]],
                            "Done. Open outputs folder.")

    def _exec_808_dial(self):
        inp = self._get_inputs()
        self._log(f"808 Dial -> Key: {inp['key']} Genre: {inp['genre'].upper()}")
        self._run_mode_safe("808_dial.py",
                            [inp["key"], inp["genre"], "7"],
                            "Done. Open outputs folder.")

    def _exec_drum_build(self):
        inp = self._get_inputs()
        self._log(f"Drum Build -> {inp['genre'].upper()} {inp['bpm']} BPM")
        self._run_mode_safe("drum_build.py",
                            [inp["genre"], inp["bpm"]],
                            "Done. Drag .mid into FL Studio.")

    def _exec_midi_gen(self):
        inp = self._get_inputs()
        self._log(f"MIDI Gen -> {inp['genre'].upper()} {inp['key']} {inp['bpm']} BPM")
        scale_map = {"trap":"minor","drill":"minor",
                     "hip hop":"minor_pent","rnb":"dorian","melodic":"minor"}
        scale = scale_map.get(inp["genre"], "minor")
        self._run_mode_safe("midi_gen.py",
                            [inp["genre"], inp["key"], scale,
                             inp["bpm"], inp["bars"], inp["midi_type"]],
                            "Done. Import .mid into Piano Roll.")

    def _exec_mix_chain(self):
        inp = self._get_inputs()
        self._log(f"Mix Chain → {inp['genre'].upper()} full chain")
        before = set(OUTPUT_DIR.iterdir())
        try:
            self._mock_inputs([inp["genre"], "6"])
            mod = self._load_mode("mix_chain.py")
            mod.run(OUTPUT_DIR)
            for f in self._list_new_outputs(before):
                self._log(f"  → {f}")
            self._log("Done. Open outputs folder.")
        except Exception as e:
            self._log(f"ERROR: {e}", error=True)


    def _init_dropdowns(self):
        """Force dropdowns to display their default values after style is applied."""
        self.genre_var.set("trap")
        self.key_var.set("F")
        self.update_idletasks()


# ── ENTRY ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SAN3App()
    app.mainloop()
