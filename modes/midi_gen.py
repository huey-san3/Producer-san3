# modes/midi_gen.py
# SAN3 Producer — MIDI Generator Mode
# For: Hip Hop | RnB | Rap | Trap producers

from pathlib import Path
from midiutil import MIDIFile
import random

# MIDI root notes — C4=60 standard (FL Studio displays as C5)
NOTES = {
    "C":  60, "C#": 61, "D": 62, "D#": 63,
    "E":  64, "F":  65, "F#": 66, "G":  67,
    "G#": 68, "A":  69, "A#": 70, "B":  71,
}

ALL_NOTES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

SCALES = {
    "minor":      [0, 2, 3, 5, 7, 8, 10],
    "minor_pent": [0, 3, 5, 7, 10],
    "dorian":     [0, 2, 3, 5, 7, 9, 10],
    "chromatic":  [0, 2, 3, 5, 7, 8, 11],
    "major":      [0, 2, 4, 5, 7, 9, 11],
}

# Common chord progressions by genre (scale degrees, 0-indexed)
PROGRESSIONS = {
    "trap":    [[0,3,5,8], [3,5,8,12], [5,8,12,15], [3,5,8,12]],   # i - bIII - iv - bIII
    "hip hop": [[0,3,5,8], [5,8,12,15], [3,5,8,12], [0,3,5,8]],
    "rnb":     [[0,4,7,11],[3,7,10,14],[5,9,12,16],[0,4,7,10]],     # more complex jazz-influenced
    "melodic": [[0,3,7,10],[5,8,12,15],[3,7,10,14],[0,3,7,10]],
    "drill":   [[0,3,5,8], [0,3,5,8],  [5,8,12,15],[3,5,8,12]],    # repetitive, cold
}

MIDI_TYPES = {
    "1": "Melody (lead hook)",
    "2": "Chord progression",
    "3": "Bass line / 808 melody",
    "4": "Counter melody",
}

GENRE_DEFAULTS = {
    "trap":    {"key": "F",  "scale": "minor",      "bpm": 140},
    "drill":   {"key": "G#", "scale": "minor",      "bpm": 144},
    "hip hop": {"key": "A",  "scale": "minor_pent", "bpm": 90},
    "rnb":     {"key": "A#", "scale": "dorian",     "bpm": 85},
    "melodic": {"key": "C#", "scale": "minor",      "bpm": 140},
}


def run(output_dir: Path) -> None:
    print("\n" + "="*52)
    print("  MIDI GEN — SAN3 Co-Producer")
    print("  Hip Hop | RnB | Rap | Trap")
    print("="*52)

    # Genre
    genre_in = input("\n  Genre (trap / drill / hip hop / rnb / melodic): ").strip().lower()
    genre = _match_genre(genre_in)
    defaults = GENRE_DEFAULTS[genre]

    # Key
    key_in = input(f"  Key? (ENTER for {defaults['key']}): ").strip().upper()
    key = key_in if key_in in NOTES else defaults["key"]

    # Scale
    scale_in = input(f"  Scale? minor / minor_pent / dorian / chromatic (ENTER for {defaults['scale']}): ").strip().lower()
    scale = scale_in if scale_in in SCALES else defaults["scale"]

    # BPM
    bpm_in = input(f"  BPM? (ENTER for {defaults['bpm']}): ").strip()
    try:
        bpm = int(bpm_in) if bpm_in else defaults["bpm"]
    except ValueError:
        bpm = defaults["bpm"]

    # Bars
    bars_in = input("  Bars? (4 or 8, ENTER for 4): ").strip()
    try:
        bars = int(bars_in) if bars_in in ["4", "8"] else 4
    except ValueError:
        bars = 4

    # MIDI type
    print("\n  What do you need?")
    for k, v in MIDI_TYPES.items():
        print(f"    {k}. {v}")
    type_in = input("  Choice (ENTER for melody): ").strip()
    midi_type_key = type_in if type_in in MIDI_TYPES else "1"
    midi_type = MIDI_TYPES[midi_type_key]

    print(f"\n  Genre  : {genre.upper()}")
    print(f"  Key    : {key} {scale}")
    print(f"  BPM    : {bpm}")
    print(f"  Bars   : {bars}")
    print(f"  Type   : {midi_type}")

    # Build scale
    root = NOTES[key]
    intervals = SCALES[scale]
    scale_notes = _build_scale(root, intervals, octaves=3)
    scale_names = _get_scale_names(key, intervals)

    # Generate
    if midi_type_key == "1":
        notes = _gen_melody(genre, scale_notes, bars)
    elif midi_type_key == "2":
        notes = _gen_chords(genre, root, intervals, bars)
    elif midi_type_key == "3":
        notes = _gen_bassline(genre, scale_notes, bars, bpm)
    else:
        notes = _gen_counter(genre, scale_notes, bars)

    # Write MIDI
    midi_path = _write_midi(output_dir, notes, bpm, genre, midi_type_key, key, scale, bars)
    print(f"\n  MIDI file   → {midi_path.name}")

    # Write notation guide
    guide_path = _write_notation(output_dir, notes, genre, bpm, key, scale,
                                  scale_names, midi_type, bars)
    print(f"  Notation    → {guide_path.name}")

    print("\n  Import to FL Studio:")
    print("  Piano Roll → right-click → Import MIDI")
    print("  After import: Select All (Ctrl+A) → Quantize 1/16 → Humanize velocity ±10\n")


def _match_genre(raw: str) -> str:
    for g in GENRE_DEFAULTS:
        if raw in g or g in raw:
            return g
    return "trap"


def _build_scale(root: int, intervals: list, octaves: int = 3) -> list:
    notes = []
    for oct in range(octaves):
        for i in intervals:
            notes.append(root + i + (oct * 12))
    return notes


def _get_scale_names(root: str, intervals: list) -> list:
    root_idx = ALL_NOTES.index(root)
    return [ALL_NOTES[(root_idx + i) % 12] for i in intervals]


def _gen_melody(genre: str, scale: list, bars: int) -> list:
    """Generate a melodic hook — stepwise, singable, infectious."""
    s = scale  # convenience

    patterns = {
        "trap": [
            (0.0, s[4], 0.5, 95), (0.5, s[2], 0.25, 80),
            (1.0, s[0], 1.0, 100), (2.0, s[3], 0.5, 85),
            (2.75,s[1], 0.25, 70), (3.0, s[4], 1.0, 90),
            (4.0, s[2], 0.5, 90), (4.5, s[0], 1.5, 100),
            (6.0, s[6], 0.5, 80), (6.5, s[4], 0.5, 85),
            (7.0, s[0], 1.0, 95),
        ],
        "drill": [
            (0.0,  s[0], 0.25, 90), (0.25, s[0], 0.25, 75),
            (0.75, s[2], 0.5, 95),  (1.5,  s[3], 0.25, 85),
            (2.0,  s[0], 0.25, 90), (2.25, s[0], 0.25, 70),
            (2.75, s[4], 0.5, 100), (3.5,  s[2], 0.5, 80),
            (4.0,  s[0], 0.25, 90), (4.75, s[2], 0.5, 95),
            (5.5,  s[6], 0.25, 80), (6.0,  s[4], 1.0, 95),
            (7.0,  s[0], 1.0, 90),
        ],
        "hip hop": [
            (0.0, s[4], 1.0, 90),  (1.0, s[5], 0.5, 85),
            (1.5, s[4], 0.5, 80),  (2.0, s[2], 1.0, 95),
            (3.0, s[0], 1.0, 100), (4.0, s[3], 0.75, 85),
            (4.75,s[4], 0.25, 75), (5.0, s[5], 1.0, 90),
            (6.0, s[4], 0.5, 85),  (6.5, s[2], 0.5, 80),
            (7.0, s[0], 1.0, 100),
        ],
        "rnb": [
            (0.0,  s[2], 0.75, 85), (1.0,  s[4], 1.0, 90),
            (2.25, s[5], 0.5, 80),  (3.0,  s[4], 1.0, 95),
            (4.0,  s[2], 0.5, 85),  (4.75, s[0], 1.5, 100),
            (6.5,  s[3], 0.5, 75),  (7.0,  s[2], 1.0, 90),
        ],
        "melodic": [
            (0.0, s[7], 0.5, 95),  (0.5, s[6], 0.5, 85),
            (1.0, s[4], 1.0, 100), (2.0, s[5], 0.5, 90),
            (2.5, s[4], 0.5, 80),  (3.0, s[2], 1.0, 95),
            (4.0, s[4], 0.5, 90),  (4.5, s[2], 0.5, 85),
            (5.0, s[0], 2.0, 100), (7.0, s[2], 0.5, 70),
            (7.5, s[4], 0.5, 80),
        ],
    }

    base = patterns.get(genre, patterns["trap"])
    if bars == 8:
        # Repeat with slight variation for second 4 bars
        second = [(t + 8.0, p, d, max(v - 5, 60)) for (t, p, d, v) in base]
        return base + second
    return base


def _gen_chords(genre: str, root: int, intervals: list, bars: int) -> list:
    """Generate a chord progression."""
    prog = PROGRESSIONS.get(genre, PROGRESSIONS["trap"])
    notes = []
    beats_per_chord = 2.0  # 2 beats per chord = 2 chords per bar

    total_chords = bars * 2
    chord_idx = 0

    for b in range(total_chords):
        chord = prog[chord_idx % len(prog)]
        beat_start = b * beats_per_chord

        for interval in chord:
            pitch = root + interval
            if pitch > 84:  # keep within reasonable range
                pitch -= 12
            notes.append((beat_start, pitch, beats_per_chord - 0.1, 80))

        chord_idx += 1

    return notes


def _gen_bassline(genre: str, scale: list, bars: int, bpm: int) -> list:
    """Generate a rhythmic bass line / 808 melody."""
    s = scale

    patterns = {
        "trap": [
            (0.0,  s[0], 2.0, 100), (2.0, s[3], 0.5, 90),
            (2.75, s[0], 1.25, 95), (4.0, s[4], 1.0, 100),
            (5.0,  s[2], 1.0, 90),  (6.0, s[0], 2.0, 100),
        ],
        "drill": [
            (0.0, s[0], 1.0, 100), (1.0, s[0], 0.5, 85),
            (1.75,s[2], 0.5, 90),  (2.5, s[0], 1.5, 100),
            (4.0, s[0], 1.0, 100), (5.0, s[3], 1.0, 90),
            (6.0, s[0], 2.0, 100),
        ],
        "hip hop": [
            (0.0, s[0], 1.0, 95), (1.0, s[2], 0.5, 85),
            (1.5, s[3], 0.5, 80), (2.0, s[4], 1.0, 90),
            (3.0, s[0], 1.0, 95), (4.0, s[0], 1.0, 95),
            (5.0, s[5], 1.0, 85), (6.0, s[4], 1.0, 90),
            (7.0, s[0], 1.0, 100),
        ],
        "rnb": [
            (0.0, s[0], 1.5, 90), (1.5, s[2], 0.5, 80),
            (2.0, s[4], 1.0, 85), (3.0, s[3], 1.0, 80),
            (4.0, s[0], 2.0, 90), (6.0, s[2], 1.0, 80),
            (7.0, s[0], 1.0, 85),
        ],
        "melodic": [
            (0.0, s[0], 2.0, 100), (2.0, s[4], 1.0, 90),
            (3.0, s[2], 1.0, 85),  (4.0, s[0], 2.0, 100),
            (6.0, s[3], 1.0, 90),  (7.0, s[0], 1.0, 95),
        ],
    }

    base = patterns.get(genre, patterns["trap"])
    if bars == 8:
        second = [(t + 8.0, p, d, v) for (t, p, d, v) in base]
        return base + second
    return base


def _gen_counter(genre: str, scale: list, bars: int) -> list:
    """Counter melody — answers the main hook, fills space."""
    s = scale
    base = [
        (0.5, s[5], 0.5, 75),  (1.5, s[4], 0.5, 70),
        (2.5, s[2], 1.0, 80),  (4.0, s[6], 0.5, 75),
        (4.5, s[5], 0.5, 70),  (5.5, s[3], 0.5, 75),
        (6.5, s[2], 1.5, 80),
    ]
    if bars == 8:
        second = [(t + 8.0, p, d, v) for (t, p, d, v) in base]
        return base + second
    return base


def _write_midi(output_dir: Path, notes: list, bpm: int,
                genre: str, midi_type: str, key: str,
                scale: str, bars: int) -> Path:

    type_names = {"1": "melody", "2": "chords", "3": "bass", "4": "counter"}
    label = type_names.get(midi_type, "midi")
    safe_genre = genre.replace(" ", "_")

    midi = MIDIFile(1)
    midi.addTempo(0, 0, bpm)
    midi.addTimeSignature(0, 0, 4, 2, 24)

    for (start, pitch, duration, velocity) in notes:
        midi.addNote(0, 0, pitch, start, duration, velocity)

    path = output_dir / f"midi_{label}_{safe_genre}_{key}_{scale}_{bars}bars.mid"
    with open(path, "wb") as f:
        midi.writeFile(f)
    return path


def _write_notation(output_dir: Path, notes: list, genre: str,
                    bpm: int, key: str, scale: str, scale_names: list,
                    midi_type: str, bars: int) -> Path:

    type_names = {"Melody (lead hook)": "melody", "Chord progression": "chords",
                  "Bass line / 808 melody": "bass", "Counter melody": "counter"}
    label = type_names.get(midi_type, "midi")
    safe_genre = genre.replace(" ", "_")

    # Format note list
    note_lines = []
    for (start, pitch, duration, velocity) in notes:
        note_name = ALL_NOTES[pitch % 12]
        octave    = (pitch // 12) - 1
        note_lines.append(
            f"  Beat {start:5.2f} | {note_name}{octave:<3} (MIDI {pitch:3}) | "
            f"Duration: {duration:.2f} beats | Velocity: {velocity}"
        )

    content = f"""
================================================================================
  MIDI NOTATION — {midi_type.upper()}
  {genre.upper()} | {key} {scale} | {bpm} BPM | {bars} bars
  Generated by: SAN3 Co-Producer
================================================================================

SCALE: {key} {scale}
Notes: {" — ".join(scale_names)}

NOTE: In FL Studio, MIDI note numbers are displayed one octave higher.
  MIDI 60 (C4 standard) = C5 in FL Studio Piano Roll

--------------------------------------------------------------------------------
NOTE-BY-NOTE BREAKDOWN
--------------------------------------------------------------------------------

{"chr(10)".join(note_lines)}

--------------------------------------------------------------------------------
FL STUDIO PIANO ROLL TIPS
--------------------------------------------------------------------------------

  After importing:
    1. Ctrl+A (Select All) → Alt+Q (Quantize) → 1/16th note
    2. Humanize velocity:
       Ctrl+A → right-click any note → Properties → Randomize velocity ±10
    3. For melody/counter: add slight timing offset
       Ctrl+A → right-click → Randomize → Start time ±3 ticks
    4. For chords: check voice leading — notes shouldn't jump more than a 5th
    5. Set your MIDI channel to match your instrument plugin

  EXPRESSION (makes it feel alive):
    → Use pitch bend automation for slides between notes (melody/bass)
    → Use mod wheel automation for vibrato on held notes (RnB/melodic)
    → Velocity rides: draw automation clip linked to instrument volume

  SCALE LOCK (FL Studio 21+):
    Piano Roll → right-click note → Scale Highlighting → {key} {scale}
    This locks your Piano Roll to only show scale notes

================================================================================
"""

    path = output_dir / f"midi_{label}_{safe_genre}_{key}_{scale}_{bars}bars.txt"
    path.write_text(content.strip(), encoding="utf-8")
    return path


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "outputs"
    out.mkdir(exist_ok=True)
    run(out)
