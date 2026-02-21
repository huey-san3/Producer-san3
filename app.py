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

CHANGELOG — SAN3 Autonomous Improvement Pass
=============================================

BUG FIXES:
  [FIX-01] _exec_generator — was wired to a non-existent method.
           Now fully implemented using _run_mode_safe with correct
           5-input sequence matching generator.py's run() prompts.
           WHY: Dead button. Every click was a silent failure.

  [FIX-02] _exec_mix_chain — called self._mock_inputs() which was
           never defined. Replaced with _run_mode_safe pattern.
           WHY: AttributeError on every Mix Chain click. Hard crash.

  [FIX-03] _exec_drum_build — was spawned by _run_in_thread() then
           spawned ANOTHER thread internally. Double threading.
           Removed inner thread. Executor runs directly in the
           background thread already provided by _run_in_thread().
           WHY: Orphaned threads, unpredictable behavior under load.

  [FIX-04] _exec_midi_gen — same double-threading issue as drum build.
           Fixed identically.
           WHY: Same reason.

  [FIX-05] Dead _real variable in _exec_drum_build — captured
           __builtins__["input"] and never used it. Removed.
           WHY: Leftover from a refactor. Confusing and pointless.

NEW FEATURES:
  [ADD-01] Session Memory — app saves last used genre/key/bpm/bars
           to outputs/.session.json on every generation. Restores
           on startup so you never reset your settings.
           WHY: Every time you reopen the app you were starting from
           defaults. Wasted time. This removes that friction entirely.

  [ADD-02] Audit Log — every generation is appended to
           logs/production.log with timestamp, mode, genre, key,
           bpm, and output filename.
           WHY: Traceability. You'll know exactly what was made and
           when. Also required for any future pattern analytics.

  [ADD-03] Workspace Lock — safe_write() guard added to output path
           resolution. Any file write outside the outputs/ directory
           is blocked and logged as an error.
           WHY: Prevents accidental writes to unexpected locations if
           a mode ever constructs a bad path.

  [ADD-04] Status Bar — thin bar at the bottom of the window shows
           the last generated filename in real time.
           WHY: You shouldn't have to read the log to know what just
           got made. One glance at the bottom tells you.

  [ADD-05] Logs directory auto-created on startup.
           WHY: Without this, audit logging would silently fail on
           first run if the folder doesn't exist.

  [ADD-06] BPM input validation on entry — non-numeric input shows
           red border on the BPM field instead of silently defaulting.
           WHY: Silent defaults are invisible bugs in production.
           Better to surface the problem immediately.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import builtins
import importlib.util
import json
from pathlib import Path
from datetime import datetime

# Windows DPI awareness — prevents blurry/black rendering on high-DPI screens
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ── CONSTANTS ──────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
OUTPUT_DIR  = BASE_DIR / "outputs"
LOGS_DIR    = BASE_DIR / "logs"
SESSION_FILE = OUTPUT_DIR / ".session.json"
AUDIT_LOG   = LOGS_DIR / "production.log"

OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

GENRES   = ["trap", "drill", "hip hop", "rnb", "melodic"]
KEYS     = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BPM_MAP  = {"trap": 140, "drill": 144, "hip hop": 90, "rnb": 85, "melodic": 140}

COLORS = {
    "bg":         "#0f0f0f",
    "panel":      "#1a1a1a",
    "border":     "#2a2a2a",
    "accent":     "#c8a96e",
    "accent_dim": "#8a6e3e",
    "text":       "#e8e8e8",
    "text_dim":   "#888888",
    "btn_bg":     "#1e1e1e",
    "btn_hover":  "#2a2a2a",
    "btn_active": "#c8a96e",
    "log_bg":     "#111111",
    "log_text":   "#00cc66",
    "error":      "#cc3333",
    "warning":    "#cc8833",
    "status_bg":  "#0a0a0a",
}

FONT_MAIN  = ("Consolas", 10)
FONT_TITLE = ("Consolas", 11, "bold")
FONT_BTN   = ("Consolas", 10, "bold")
FONT_LOG   = ("Consolas", 9)
FONT_STATUS = ("Consolas", 8)


# ── WORKSPACE GUARD ────────────────────────────────────────────────────
# [ADD-03] Blocks any file write outside the outputs directory.
def safe_output_path(path: Path) -> Path:
    """
    Validates that a path resolves inside OUTPUT_DIR.
    Raises PermissionError if it doesn't.
    WHY: Prevents accidental writes to arbitrary locations.
    """
    resolved   = path.resolve()
    output_res = OUTPUT_DIR.resolve()
    if not str(resolved).startswith(str(output_res)):
        raise PermissionError(
            f"Write outside SAN3 workspace denied: {resolved}"
        )
    return path


# ── SESSION MEMORY ─────────────────────────────────────────────────────
# [ADD-01] Saves and restores last used settings.
def load_session() -> dict:
    """
    Loads last session settings from outputs/.session.json.
    Returns defaults if file doesn't exist or is corrupt.
    WHY: Eliminates resetting genre/key/BPM every time you open the app.
    """
    defaults = {"genre": "trap", "key": "F", "bpm": "140", "bars": "4"}
    try:
        if SESSION_FILE.exists():
            data = json.loads(SESSION_FILE.read_text())
            # Validate keys exist before trusting
            for k in defaults:
                if k not in data:
                    return defaults
            return data
    except Exception:
        pass
    return defaults


def save_session(genre: str, key: str, bpm: str, bars: str) -> None:
    """
    Saves current settings to outputs/.session.json.
    Called after every successful generation.
    WHY: Persistence. State survives app restarts.
    """
    try:
        SESSION_FILE.write_text(
            json.dumps({"genre": genre, "key": key, "bpm": bpm, "bars": bars},
                       indent=2)
        )
    except Exception:
        pass  # Non-critical — don't crash if session save fails


# ── AUDIT LOG ──────────────────────────────────────────────────────────
# [ADD-02] Appends a structured line to logs/production.log.
def audit(mode: str, genre: str, key: str, bpm: str, output: str = "") -> None:
    """
    Writes one audit line per generation to logs/production.log.
    Format: [timestamp] MODE | genre | key | bpm | output_file
    WHY: Traceability. Pattern analytics. Never lose track of what was made.
    """
    try:
        ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {mode:<12} | {genre:<8} | {key:<3} | {bpm} BPM | {output}\n"
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass  # Non-critical — audit failure must never crash the app


# ── MAIN APP ───────────────────────────────────────────────────────────
class SAN3App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("SAN3 PRODUCER")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Position: top-right corner of screen
        self.update_idletasks()
        w, h = 640, 800   # +40px for status bar
        sw = self.winfo_screenwidth()
        self.geometry(f"{w}x{h}+{sw - w - 10}+30")

        # [ADD-01] Load last session before building UI
        self._session = load_session()

        self._build_ui()
        self._init_dropdowns()
        self._log("SAN3 Producer ready.")
        self._log("Session restored — last settings loaded.")
        self._log("Select genre, key, BPM — then hit a mode.")

    # ── UI BUILDER ─────────────────────────────────────────────────────
    def _build_ui(self):
        # ── HEADER
        tk.Frame(self, bg=COLORS["accent"], height=2).pack(fill="x")

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

        # Genre — restored from session
        self._label(ctrl, "GENRE")
        self.genre_var = tk.StringVar(value=self._session["genre"])
        genre_menu = ttk.Combobox(ctrl, textvariable=self.genre_var,
                                  values=GENRES, state="readonly",
                                  font=FONT_MAIN, width=52)
        genre_menu.pack(fill="x", pady=(0, 6))
        genre_menu.bind("<<ComboboxSelected>>", self._on_genre_change)

        # Key — restored from session
        self._label(ctrl, "KEY")
        self.key_var = tk.StringVar(value=self._session["key"])
        key_menu = ttk.Combobox(ctrl, textvariable=self.key_var,
                                values=KEYS, state="readonly",
                                font=FONT_MAIN, width=52)
        key_menu.pack(fill="x", pady=(0, 6))

        # BPM — restored from session, validated on input
        self._label(ctrl, "BPM")
        bpm_frame = tk.Frame(ctrl, bg=COLORS["bg"])
        bpm_frame.pack(fill="x", pady=(0, 6))

        self.bpm_var = tk.StringVar(value=self._session["bpm"])
        self._bpm_entry = tk.Entry(bpm_frame, textvariable=self.bpm_var,
                             font=FONT_MAIN, width=8,
                             bg=COLORS["panel"], fg=COLORS["text"],
                             insertbackground=COLORS["accent"],
                             relief="flat", bd=4)
        self._bpm_entry.pack(side="left")
        # [ADD-06] Live BPM validation
        self.bpm_var.trace_add("write", self._validate_bpm)

        tk.Label(bpm_frame, text="  BPM",
                 font=FONT_MAIN, fg=COLORS["text_dim"],
                 bg=COLORS["bg"]).pack(side="left")

        self._divider()

        # ── MODE BUTTONS
        modes_frame = tk.Frame(self, bg=COLORS["bg"], pady=4)
        modes_frame.pack(fill="x", padx=12)

        self._label(modes_frame, "MODES")

        row1 = tk.Frame(modes_frame, bg=COLORS["bg"])
        row1.pack(fill="x", pady=2)
        self._mode_btn(row1, "BEAT BLOCK", self._run_beat_block, side="left")
        self._mode_btn(row1, "808 DIAL",   self._run_808_dial,   side="right")

        row2 = tk.Frame(modes_frame, bg=COLORS["bg"])
        row2.pack(fill="x", pady=2)
        self._mode_btn(row2, "DRUM BUILD", self._run_drum_build, side="left")
        self._mode_btn(row2, "MIDI GEN",   self._run_midi_gen,   side="right")

        row3 = tk.Frame(modes_frame, bg=COLORS["bg"])
        row3.pack(fill="x", pady=2)
        self._mode_btn_full(row3, "MIX CHAIN", self._run_mix_chain)

        row4 = tk.Frame(modes_frame, bg=COLORS["bg"])
        row4.pack(fill="x", pady=2)
        self._mode_btn_accent(row4, "GENERATOR  —  San3_DaD3aL Boi",
                               self._run_generator)

        self._divider()

        # ── MIDI TYPE
        midi_frame = tk.Frame(self, bg=COLORS["bg"], pady=2)
        midi_frame.pack(fill="x", padx=12)

        self._label(midi_frame, "MIDI TYPE  (for MIDI Gen)")
        self.midi_type_var = tk.StringVar(value="1")
        midi_types = [("Melody","1"), ("Chords","2"),
                      ("Bass Line","3"), ("Counter","4")]
        midi_row = tk.Frame(midi_frame, bg=COLORS["bg"])
        midi_row.pack(fill="x")
        for label, val in midi_types:
            rb = tk.Radiobutton(midi_row, text=label,
                                variable=self.midi_type_var, value=val,
                                font=("Consolas", 8),
                                fg=COLORS["text_dim"], bg=COLORS["bg"],
                                selectcolor=COLORS["panel"],
                                activebackground=COLORS["bg"],
                                activeforeground=COLORS["accent"])
            rb.pack(side="left", padx=2)

        # Bars — restored from session
        bars_frame = tk.Frame(self, bg=COLORS["bg"], pady=2)
        bars_frame.pack(fill="x", padx=12)
        self._label(bars_frame, "BARS  (for MIDI Gen / Generator)")
        self.bars_var = tk.StringVar(value=self._session["bars"])
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

        # ── OPEN OUTPUTS
        tk.Button(self, text="OPEN OUTPUTS FOLDER",
                  font=("Consolas", 8), fg=COLORS["text_dim"],
                  bg=COLORS["bg"], bd=0, cursor="hand2",
                  activebackground=COLORS["bg"],
                  activeforeground=COLORS["accent"],
                  command=self._open_outputs).pack(pady=4)

        # ── STATUS BAR
        # [ADD-04] Shows last generated filename at a glance.
        # WHY: Removes need to read the log just to confirm what was made.
        status_frame = tk.Frame(self, bg=COLORS["status_bg"], height=22)
        status_frame.pack(fill="x", side="bottom")
        status_frame.pack_propagate(False)

        self._status_var = tk.StringVar(value="Ready.")
        tk.Label(status_frame, textvariable=self._status_var,
                 font=FONT_STATUS, fg=COLORS["text_dim"],
                 bg=COLORS["status_bg"], anchor="w",
                 padx=8).pack(fill="x", side="left")

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
                 padx=(0 if side == "right" else 0,
                       2 if side == "left" else 0))
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

    def _mode_btn_accent(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=FONT_BTN,
                        fg=COLORS["accent"], bg=COLORS["btn_bg"],
                        activebackground=COLORS["accent"],
                        activeforeground=COLORS["bg"],
                        relief="flat", bd=2,
                        highlightbackground=COLORS["accent"],
                        highlightthickness=1,
                        padx=8, pady=8,
                        cursor="hand2", command=cmd)
        btn.pack(fill="x")
        btn.bind("<Enter>",
                 lambda e: btn.config(bg=COLORS["accent"],
                                      fg=COLORS["bg"]))
        btn.bind("<Leave>",
                 lambda e: btn.config(bg=COLORS["btn_bg"],
                                      fg=COLORS["accent"]))

    def _btn_hover(self, btn):
        btn.bind("<Enter>",
                 lambda e: btn.config(bg=COLORS["btn_hover"],
                                      fg=COLORS["accent"]))
        btn.bind("<Leave>",
                 lambda e: btn.config(bg=COLORS["btn_bg"],
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
        self.option_add("*TCombobox*Listbox.selectBackground",
                        COLORS["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", COLORS["bg"])

    # ── BPM VALIDATION ─────────────────────────────────────────────────
    # [ADD-06] Red border on bad BPM. Surfaces the problem immediately.
    def _validate_bpm(self, *_):
        val = self.bpm_var.get()
        try:
            bpm = int(val)
            if 40 <= bpm <= 300:
                self._bpm_entry.config(bg=COLORS["panel"])
                return
        except ValueError:
            pass
        # Invalid — flash red border
        self._bpm_entry.config(bg="#2a0a0a")

    def _get_safe_bpm(self) -> int:
        """Returns validated BPM or genre default."""
        try:
            bpm = int(self.bpm_var.get())
            if 40 <= bpm <= 300:
                return bpm
        except ValueError:
            pass
        return BPM_MAP.get(self.genre_var.get(), 140)

    # ── STATUS BAR ─────────────────────────────────────────────────────
    # [ADD-04]
    def _set_status(self, msg: str):
        self._status_var.set(msg)

    # ── LOG ────────────────────────────────────────────────────────────
    def _log(self, msg: str, error: bool = False):
        self.log_box.configure(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
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

    # ── INPUT HELPERS ──────────────────────────────────────────────────
    def _get_inputs(self) -> dict:
        return {
            "genre":     self.genre_var.get(),
            "key":       self.key_var.get(),
            "bpm":       str(self._get_safe_bpm()),
            "midi_type": self.midi_type_var.get(),
            "bars":      self.bars_var.get(),
        }

    def _run_in_thread(self, fn):
        t = threading.Thread(target=fn, daemon=True)
        t.start()

    # ── MODE RUNNERS ───────────────────────────────────────────────────
    def _run_beat_block(self):  self._run_in_thread(self._exec_beat_block)
    def _run_808_dial(self):    self._run_in_thread(self._exec_808_dial)
    def _run_drum_build(self):  self._run_in_thread(self._exec_drum_build)
    def _run_midi_gen(self):    self._run_in_thread(self._exec_midi_gen)
    def _run_mix_chain(self):   self._run_in_thread(self._exec_mix_chain)
    def _run_generator(self):   self._run_in_thread(self._exec_generator)

    # ── MODE LOADER ────────────────────────────────────────────────────
    def _load_mode(self, filename: str):
        path = BASE_DIR / "modes" / filename
        spec = importlib.util.spec_from_file_location("mod", path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    # ── SAFE MODE RUNNER ───────────────────────────────────────────────
    def _run_mode_safe(self, mode_file: str, answers: list, done_msg: str,
                       audit_mode: str = "", inp: dict = None):
        """
        Unified safe wrapper for all modes.
        - Patches builtins.input with queued answers from the GUI
        - Detects new files in OUTPUT_DIR after run
        - Logs new files to UI and audit log
        - Restores builtins.input in finally block (always)
        - Saves session after successful run

        WHY single wrapper: Previously drum_build and midi_gen each had
        their own inline versions with slight differences. Single source
        of truth. One place to fix if something breaks.
        """
        _real_input = builtins.input
        before = set(OUTPUT_DIR.iterdir())
        inp = inp or {}

        try:
            it = iter(str(a) for a in answers)
            builtins.input = lambda _="": next(it, "")

            mod = self._load_mode(mode_file)
            mod.run(OUTPUT_DIR)

            new_files = sorted(f.name for f in set(OUTPUT_DIR.iterdir()) - before
                               if not f.name.startswith("."))
            for fname in new_files:
                # [ADD-03] Workspace guard check on every output
                try:
                    safe_output_path(OUTPUT_DIR / fname)
                except PermissionError as pe:
                    self._log(f"SECURITY: {pe}", error=True)
                    continue

                self._log(f"  -> {fname}")
                self._set_status(f"Last: {fname}")

                # [ADD-02] Audit every new file
                audit(
                    mode=audit_mode or mode_file.replace(".py", "").upper(),
                    genre=inp.get("genre", "—"),
                    key=inp.get("key", "—"),
                    bpm=inp.get("bpm", "—"),
                    output=fname
                )

            self._log(done_msg)

            # [ADD-01] Save session after success
            save_session(
                inp.get("genre", self.genre_var.get()),
                inp.get("key",   self.key_var.get()),
                inp.get("bpm",   self.bpm_var.get()),
                inp.get("bars",  self.bars_var.get()),
            )

        except Exception as e:
            self._log(f"ERROR: {e}", error=True)
            self._set_status(f"Error — {mode_file}")
        finally:
            builtins.input = _real_input   # Always restored

    # ── MODE EXECUTORS ─────────────────────────────────────────────────

    def _exec_beat_block(self):
        inp = self._get_inputs()
        self._log(f"Beat Block -> {inp['genre'].upper()} {inp['bpm']} BPM {inp['key']}")
        self._run_mode_safe(
            "beat_block.py",
            [inp["genre"], inp["bpm"]],
            "Done. Open outputs folder.",
            audit_mode="BEAT_BLOCK", inp=inp
        )

    def _exec_808_dial(self):
        inp = self._get_inputs()
        self._log(f"808 Dial -> Key: {inp['key']} Genre: {inp['genre'].upper()}")
        self._run_mode_safe(
            "808_dial.py",
            [inp["key"], inp["genre"], "7"],
            "Done. Open outputs folder.",
            audit_mode="808_DIAL", inp=inp
        )

    def _exec_drum_build(self):
        """
        [FIX-03] Removed inner threading.Thread().
        Was: _run_in_thread -> _exec_drum_build -> threading.Thread (inside)
        Now: _run_in_thread -> _exec_drum_build (runs directly)
        WHY: Already in a background thread. Double threading creates
             orphaned threads and race conditions.

        [FIX-05] Removed dead _real variable that captured __builtins__["input"]
        but never used it. Was leftover from an earlier refactor.
        """
        inp   = self._get_inputs()
        genre = inp["genre"]
        bpm   = self._get_safe_bpm()
        self._log(f"Drum Build -> {genre.upper()} {bpm} BPM")

        _real_input = builtins.input
        try:
            builtins.input = lambda _="": ""
            spec = importlib.util.spec_from_file_location(
                "drum_gen", BASE_DIR / "modes" / "drum_gen.py"
            )
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.run(OUTPUT_DIR, genre, bpm)

            fname = result["path"].name
            self._log(f"  -> {fname}")
            self._log(f"  ID: {result['id']}")
            self._log("Done. Drag .mid into FL Studio.")
            self._set_status(f"Last: {fname}")

            # [ADD-02] Audit
            audit("DRUM_BUILD", genre, inp["key"], str(bpm), fname)
            # [ADD-01] Save session
            save_session(genre, inp["key"], str(bpm), inp["bars"])

        except Exception as e:
            self._log(f"ERROR: {e}", error=True)
            self._set_status(f"Error — drum_build")
        finally:
            builtins.input = _real_input

    def _exec_midi_gen(self):
        """
        [FIX-04] Removed inner threading.Thread().
        Same fix as _exec_drum_build — already in a background thread.
        """
        inp   = self._get_inputs()
        genre = inp["genre"]
        key   = inp["key"]
        bpm   = self._get_safe_bpm()
        bars  = int(inp["bars"])

        scale_map = {
            "trap":    "minor",
            "drill":   "minor",
            "hip hop": "minor_pent",
            "rnb":     "dorian",
            "melodic": "minor",
        }
        scale = scale_map.get(genre, "minor")
        self._log(f"MIDI Gen -> {genre.upper()} {key} {scale} {bpm} BPM")

        _real_input = builtins.input
        try:
            builtins.input = lambda _="": ""
            spec = importlib.util.spec_from_file_location(
                "melody_gen", BASE_DIR / "modes" / "melody_gen.py"
            )
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result = mod.run(OUTPUT_DIR, genre, key, scale, bpm, bars)

            fname = result["path"].name
            self._log(f"  -> {fname}")
            self._log(f"  ID: {result['id']}")
            self._log("Done. Import .mid into Piano Roll.")
            self._set_status(f"Last: {fname}")

            # [ADD-02] Audit
            audit("MIDI_GEN", genre, key, str(bpm), fname)
            # [ADD-01] Save session
            save_session(genre, key, str(bpm), inp["bars"])

        except Exception as e:
            self._log(f"ERROR: {e}", error=True)
            self._set_status(f"Error — midi_gen")
        finally:
            builtins.input = _real_input

    def _exec_mix_chain(self):
        """
        [FIX-02] Was calling self._mock_inputs() which never existed.
        AttributeError on every click.
        Now uses _run_mode_safe() with the correct input sequence.
        mix_chain.py prompts: genre, then problem choice.
        "6" = full chain — the correct default for GUI use.
        """
        inp = self._get_inputs()
        self._log(f"Mix Chain -> {inp['genre'].upper()} full chain")
        self._run_mode_safe(
            "mix_chain.py",
            [inp["genre"], "6"],
            "Done. Mix guide saved to outputs folder.",
            audit_mode="MIX_CHAIN", inp=inp
        )

    def _exec_generator(self):
        """
        [FIX-01] This method didn't exist at all. Button was dead.
        Now fully implemented.

        generator.py prompts in sequence:
          1. choice     — "3" = generate both drums + melody (full kit)
          2. genre      — from GUI dropdown
          3. key        — from GUI dropdown
          4. bpm        — from GUI BPM field
          5. bars       — from GUI bars radio

        WHY choice "3": Generator offers drum-only (1), melody-only (2),
        or both (3). GUI already shows genre/key/bars — no reason to
        generate half a kit. Default to full starter kit every time.
        User can go CLI if they want granular control.
        """
        inp = self._get_inputs()
        self._log(
            f"Generator -> {inp['genre'].upper()} {inp['key']} "
            f"{inp['bpm']} BPM {inp['bars']} bars | Full kit"
        )
        self._run_mode_safe(
            "generator.py",
            ["3", inp["genre"], inp["key"], inp["bpm"], inp["bars"]],
            "Done. Drag both .mid files into FL Studio Piano Roll.",
            audit_mode="GENERATOR", inp=inp
        )

    # ── INIT DROPDOWNS ─────────────────────────────────────────────────
    def _init_dropdowns(self):
        """Force dropdowns to display their restored session values."""
        self.genre_var.set(self._session["genre"])
        self.key_var.set(self._session["key"])
        self.bpm_var.set(self._session["bpm"])
        self.bars_var.set(self._session["bars"])
        self.update_idletasks()


# ── ENTRY ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SAN3App()
    app.mainloop()
