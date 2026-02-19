# modes/melody_gen.py
# SAN3 Producer — Algorithmic Melody Generator
# Generates unique melodies every time using genre rules + randomness.
# Every output gets a unique ID. No repeats ever tracked.

import random
from pathlib import Path
from midiutil import MIDIFile
from modes.pattern_catalog import register

ALL_NOTES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

NOTES = {n: 60 + i for i, n in enumerate(ALL_NOTES)}

SCALES = {
    "minor":      [0, 2, 3, 5, 7, 8, 10],
    "minor_pent": [0, 3, 5, 7, 10],
    "dorian":     [0, 2, 3, 5, 7, 9, 10],
    "chromatic":  [0, 2, 3, 5, 7, 8, 11],
}

# Genre DNA — rules that shape the random generation
GENRE_DNA = {
    "trap": {
        "note_count":    (7, 12),       # min/max notes per 4 bars
        "duration_pool": [0.25, 0.5, 0.75, 1.0, 1.5, 2.0],
        "duration_weights": [10, 25, 15, 25, 15, 10],
        "velocity_base": 90,
        "velocity_var":  15,
        "rest_chance":   0.25,          # chance of gap between notes
        "octave_range":  (0, 1),        # scale octave offsets
        "contour":       "descending",  # melodic direction tendency
        "repeat_note_chance": 0.20,     # chance same note repeats
        "long_note_chance":   0.30,
    },
    "drill": {
        "note_count":    (10, 16),
        "duration_pool": [0.25, 0.25, 0.5, 0.75],
        "duration_weights": [30, 30, 25, 15],
        "velocity_base": 88,
        "velocity_var":  12,
        "rest_chance":   0.15,
        "octave_range":  (0, 1),
        "contour":       "flat",
        "repeat_note_chance": 0.35,
        "long_note_chance":   0.10,
    },
    "hip hop": {
        "note_count":    (8, 12),
        "duration_pool": [0.5, 0.75, 1.0, 1.5],
        "duration_weights": [20, 25, 35, 20],
        "velocity_base": 85,
        "velocity_var":  12,
        "rest_chance":   0.20,
        "octave_range":  (0, 1),
        "contour":       "arch",        # rises then falls
        "repeat_note_chance": 0.15,
        "long_note_chance":   0.30,
    },
    "rnb": {
        "note_count":    (6, 10),
        "duration_pool": [0.5, 0.75, 1.0, 1.5, 2.0],
        "duration_weights": [15, 20, 30, 25, 10],
        "velocity_base": 82,
        "velocity_var":  10,
        "rest_chance":   0.30,
        "octave_range":  (0, 1),
        "contour":       "arch",
        "repeat_note_chance": 0.10,
        "long_note_chance":   0.40,
    },
    "melodic": {
        "note_count":    (8, 14),
        "duration_pool": [0.25, 0.5, 0.75, 1.0, 1.5, 2.0],
        "duration_weights": [10, 20, 20, 25, 15, 10],
        "velocity_base": 90,
        "velocity_var":  12,
        "rest_chance":   0.20,
        "octave_range":  (0, 2),
        "contour":       "rising",
        "repeat_note_chance": 0.10,
        "long_note_chance":   0.35,
    },
}


def generate(genre: str, key: str, scale: str, bars: int = 4) -> list:
    """
    Generate a unique melody pattern.
    Returns list of (beat_start, midi_pitch, duration, velocity).
    """
    dna    = GENRE_DNA.get(genre, GENRE_DNA["trap"])
    root   = NOTES.get(key, 65)
    ivs    = SCALES.get(scale, SCALES["minor"])
    s      = _build_scale(root, ivs, octaves=3)

    total_beats  = bars * 4
    note_count   = random.randint(*dna["note_count"])
    contour      = dna["contour"]

    # Build a contour index sequence — shapes where in the scale we tend to go
    indices = _build_contour(contour, note_count, len(s))

    notes   = []
    beat    = 0.0

    for i, idx in enumerate(indices):
        if beat >= total_beats:
            break

        # Occasionally repeat the previous note
        if notes and random.random() < dna["repeat_note_chance"]:
            idx = s.index(notes[-1][1]) if notes[-1][1] in s else idx

        pitch = s[idx % len(s)]

        # Duration
        if random.random() < dna["long_note_chance"]:
            dur = random.choices([1.0, 1.5, 2.0], weights=[40, 35, 25])[0]
        else:
            dur = random.choices(
                dna["duration_pool"],
                weights=dna["duration_weights"]
            )[0]

        # Don't overflow the bar
        dur = min(dur, total_beats - beat)
        if dur <= 0:
            break

        # Velocity — humanized
        vel = max(40, min(115,
            dna["velocity_base"] + random.randint(-dna["velocity_var"],
                                                   dna["velocity_var"])
        ))

        notes.append((round(beat, 3), pitch, round(dur, 3), vel))
        beat += dur

        # Rest gap
        if random.random() < dna["rest_chance"] and beat < total_beats:
            gap = random.choices([0.25, 0.5], weights=[70, 30])[0]
            beat += gap

    return notes


def _build_contour(contour: str, length: int, scale_len: int) -> list:
    """
    Build a sequence of scale indices shaped by the contour direction.
    """
    mid   = scale_len // 2
    high  = min(scale_len - 1, scale_len - 2)
    low   = 0

    if contour == "descending":
        start = random.randint(mid, high)
        end   = random.randint(low, mid - 1)
    elif contour == "rising":
        start = random.randint(low, mid - 1)
        end   = random.randint(mid, high)
    elif contour == "arch":
        peak  = random.randint(mid, high)
        seq   = []
        half  = length // 2
        # Rise
        for i in range(half):
            seq.append(int(low + (peak - low) * i / max(half - 1, 1)))
        # Fall
        for i in range(length - half):
            seq.append(int(peak - (peak - low) * i / max(length - half - 1, 1)))
        return [max(0, min(scale_len - 1, x + random.randint(-1, 1))) for x in seq]
    else:
        # flat — stay in mid range with slight variation
        start = mid
        end   = mid

    # Linear progression with noise
    indices = []
    for i in range(length):
        t   = i / max(length - 1, 1)
        val = int(start + (end - start) * t)
        val = val + random.randint(-2, 2)
        indices.append(max(0, min(scale_len - 1, val)))
    return indices


def _build_scale(root: int, intervals: list, octaves: int = 3) -> list:
    notes = []
    for oct in range(octaves):
        for i in intervals:
            notes.append(root + i + oct * 12)
    return notes


def write_midi(output_dir: Path, notes: list, bpm: int,
               genre: str, key: str, scale: str,
               bars: int, pattern_id: str) -> Path:
    midi = MIDIFile(1)
    midi.addTempo(0, 0, bpm)
    midi.addTimeSignature(0, 0, 4, 2, 24)
    for (start, pitch, dur, vel) in notes:
        midi.addNote(0, 0, pitch, start, dur, vel)

    safe_id = pattern_id.replace(" ", "_")
    path = output_dir / f"{safe_id}.mid"
    with open(path, "wb") as f:
        midi.writeFile(f)
    return path


def run(output_dir: Path, genre: str, key: str,
        scale: str, bpm: int, bars: int) -> dict:
    """
    Generate a melody, register it, write MIDI.
    Returns result dict with id, path, repeat status.
    """
    notes   = generate(genre, key, scale, bars)
    entry   = register("melody", genre, key, notes)

    if entry["repeat"]:
        # Regenerate once if it was a repeat
        notes = generate(genre, key, scale, bars)
        entry = register("melody", genre, key, notes)

    midi_path = write_midi(output_dir, notes, bpm,
                           genre, key, scale, bars, entry["id"])
    return {
        "id":    entry["id"],
        "path":  midi_path,
        "notes": notes,
        "entry": entry,
    }
