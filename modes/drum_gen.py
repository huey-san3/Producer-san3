# modes/drum_gen.py
# SAN3 Producer — Algorithmic Drum Generator
# Generates unique drum patterns every time using genre rules + randomness.
# Every output gets a unique ID. No repeats ever tracked.

import random
from pathlib import Path
from midiutil import MIDIFile
from modes.pattern_catalog import register

# General MIDI drum map — channel 10 (index 9)
GM = {
    "kick":      36,
    "snare":     38,
    "ghost":     38,
    "clap":      39,
    "hihat_cl":  42,
    "hihat_op":  46,
    "hihat_ped": 44,
    "rim":       37,
    "snap":      39,
    "shaker":    70,
    "tom_hi":    50,
    "tom_lo":    45,
    "ride":      51,
}

# Genre DNA — probability rules for random drum generation
GENRE_DNA = {
    "trap": {
        "bpm":    140,
        "swing":  0,
        "kick": {
            "mandatory": [0, 8],              # always on these steps (16-step grid)
            "variable":  [2, 3, 10, 11, 13, 14, 15],  # random placement pool
            "variable_count": (2, 4),         # how many variable kicks to place
            "velocity_main": (100, 115),
            "velocity_var":  (65, 90),
        },
        "snare": {
            "mandatory": [4, 12],
            "clap_stack": True,
            "ghost_chance": 0.40,
            "ghost_steps": [2, 6, 10, 14, 15],
            "velocity_main": (95, 105),
            "velocity_ghost": (28, 45),
        },
        "hihat": {
            "pattern": "16th_rolling",        # all 16 steps
            "open_steps": [5, 13],
            "open_chance": 0.70,
            "vel_accent_steps": [0, 4, 8, 12],
            "vel_accent": (95, 110),
            "vel_normal": (55, 85),
        },
    },
    "drill": {
        "bpm":    144,
        "swing":  0,
        "kick": {
            "mandatory": [0],
            "variable":  [2, 3, 5, 6, 8, 9, 10, 11, 13, 14, 15],
            "variable_count": (4, 7),
            "velocity_main": (105, 115),
            "velocity_var":  (55, 80),
        },
        "snare": {
            "mandatory": [4, 12],
            "clap_stack": False,
            "ghost_chance": 0.20,
            "ghost_steps": [6, 14],
            "velocity_main": (90, 100),
            "velocity_ghost": (30, 45),
        },
        "hihat": {
            "pattern": "16th_sliding",
            "open_steps": [3, 7, 11, 15],
            "open_chance": 0.80,
            "vel_accent_steps": [0, 8],
            "vel_accent": (100, 110),
            "vel_normal": (45, 70),
        },
    },
    "hip hop": {
        "bpm":    90,
        "swing":  12,
        "kick": {
            "mandatory": [0],
            "variable":  [2, 3, 8, 10, 11, 14],
            "variable_count": (2, 3),
            "velocity_main": (100, 115),
            "velocity_var":  (70, 90),
        },
        "snare": {
            "mandatory": [4, 12],
            "clap_stack": False,
            "ghost_chance": 0.55,
            "ghost_steps": [1, 3, 6, 9, 14, 15],
            "velocity_main": (95, 110),
            "velocity_ghost": (32, 50),
        },
        "hihat": {
            "pattern": "8th_swing",
            "open_steps": [6, 14],
            "open_chance": 0.65,
            "vel_accent_steps": [0, 4, 8, 12],
            "vel_accent": (85, 95),
            "vel_normal": (55, 75),
        },
        "rim": {
            "chance": 0.50,
            "steps":  [2, 6, 10, 14],
            "velocity": (35, 50),
        },
    },
    "rnb": {
        "bpm":    85,
        "swing":  8,
        "kick": {
            "mandatory": [0],
            "variable":  [3, 5, 8, 10, 11],
            "variable_count": (1, 3),
            "velocity_main": (88, 100),
            "velocity_var":  (55, 75),
        },
        "snare": {
            "mandatory": [4, 12],
            "clap_stack": False,
            "ghost_chance": 0.30,
            "ghost_steps": [3, 7, 11, 15],
            "velocity_main": (80, 95),
            "velocity_ghost": (28, 42),
        },
        "hihat": {
            "pattern": "sparse",
            "open_steps": [6, 14],
            "open_chance": 0.60,
            "vel_accent_steps": [0, 8],
            "vel_accent": (70, 82),
            "vel_normal": (50, 68),
        },
        "shaker": {
            "chance": 0.60,
            "steps":  [2, 6, 10, 14],
            "velocity": (42, 58),
        },
    },
    "melodic": {
        "bpm":    140,
        "swing":  0,
        "kick": {
            "mandatory": [0, 8],
            "variable":  [3, 5, 7, 11, 13, 15],
            "variable_count": (2, 3),
            "velocity_main": (100, 112),
            "velocity_var":  (60, 80),
        },
        "snare": {
            "mandatory": [4, 12],
            "clap_stack": True,
            "ghost_chance": 0.35,
            "ghost_steps": [2, 6, 10, 14, 15],
            "velocity_main": (90, 102),
            "velocity_ghost": (30, 45),
        },
        "hihat": {
            "pattern": "8th_open",
            "open_steps": [2, 6, 10, 14],
            "open_chance": 0.75,
            "vel_accent_steps": [0, 4, 8, 12],
            "vel_accent": (82, 95),
            "vel_normal": (55, 75),
        },
    },
}


def generate(genre: str) -> list:
    """
    Generate a unique 2-bar drum pattern.
    Returns list of (step_16th, instrument, velocity) — 32-step grid.
    """
    dna   = GENRE_DNA.get(genre, GENRE_DNA["trap"])
    hits  = []

    for bar in range(2):
        offset = bar * 16
        hits += _gen_kick(dna["kick"],   offset, bar)
        hits += _gen_snare(dna["snare"], offset, bar)
        hits += _gen_hihat(dna["hihat"], offset, bar)

        if "rim" in dna and random.random() < dna["rim"]["chance"]:
            hits += _gen_accent(dna["rim"], offset, "rim")

        if "shaker" in dna and random.random() < dna["shaker"]["chance"]:
            hits += _gen_accent(dna["shaker"], offset, "shaker")

    return sorted(hits, key=lambda x: x[0])


def _gen_kick(cfg: dict, offset: int, bar: int) -> list:
    hits = []

    # Mandatory placements
    for step in cfg["mandatory"]:
        vel = random.randint(*cfg["velocity_main"])
        hits.append((step + offset, "kick", vel))

    # Variable placements — bar 2 gets slight variation
    pool  = cfg["variable"][:]
    count = random.randint(*cfg["variable_count"])
    if bar == 1:
        # Remove one mandatory-adjacent step occasionally for variation
        pool = [s for s in pool if s not in [1, 9]]

    chosen = random.sample(pool, min(count, len(pool)))
    for step in chosen:
        vel = random.randint(*cfg["velocity_var"])
        hits.append((step + offset, "kick", vel))

    return hits


def _gen_snare(cfg: dict, offset: int, bar: int) -> list:
    hits = []

    # Mandatory snare hits
    for step in cfg["mandatory"]:
        vel = random.randint(*cfg["velocity_main"])
        hits.append((step + offset, "snare", vel))
        if cfg["clap_stack"]:
            clap_vel = max(vel - random.randint(5, 12), 70)
            hits.append((step + offset, "clap", clap_vel))

    # Ghost notes
    if random.random() < cfg["ghost_chance"]:
        pool  = cfg["ghost_steps"][:]
        # Exclude mandatory snare steps
        pool  = [s for s in pool if s not in cfg["mandatory"]]
        count = random.randint(1, min(3, len(pool)))
        for step in random.sample(pool, count):
            vel = random.randint(*cfg["velocity_ghost"])
            hits.append((step + offset, "ghost", vel))

    return hits


def _gen_hihat(cfg: dict, offset: int, bar: int) -> list:
    hits   = []
    pat    = cfg["pattern"]
    open_s = cfg.get("open_steps", [])

    if pat == "16th_rolling":
        steps = list(range(16))
    elif pat == "16th_sliding":
        steps = list(range(16))
    elif pat == "8th_swing":
        steps = [0, 2, 4, 6, 8, 10, 12, 14]
        # Add offbeat 16ths randomly for swing feel
        extras = [1, 3, 5, 7, 9, 11, 13, 15]
        steps += random.sample(extras, random.randint(2, 5))
        steps = sorted(set(steps))
    elif pat == "8th_open":
        steps = [0, 2, 4, 6, 8, 10, 12, 14]
    elif pat == "sparse":
        # Only hit on accent positions + random fill
        steps = cfg["vel_accent_steps"][:]
        extras = [s for s in range(16) if s not in steps]
        steps += random.sample(extras, random.randint(2, 4))
        steps = sorted(set(steps))
    else:
        steps = [0, 2, 4, 6, 8, 10, 12, 14]

    for step in steps:
        is_open = (step in open_s) and (random.random() < cfg["open_chance"])
        inst    = "hihat_op" if is_open else "hihat_cl"

        if step in cfg["vel_accent_steps"]:
            vel = random.randint(*cfg["vel_accent"])
        else:
            vel = random.randint(*cfg["vel_normal"])
            # Slight randomization for humanization
            vel = max(35, vel + random.randint(-8, 8))

        hits.append((step + offset, inst, vel))

    return hits


def _gen_accent(cfg: dict, offset: int, inst: str) -> list:
    hits = []
    for step in cfg["steps"]:
        if random.random() < 0.70:  # not every step, keep it musical
            vel = random.randint(*cfg["velocity"])
            hits.append((step + offset, inst, vel))
    return hits


def write_midi(output_dir: Path, hits: list,
               bpm: int, pattern_id: str) -> Path:
    midi = MIDIFile(1)
    midi.addTempo(0, 0, bpm)
    midi.addTimeSignature(0, 0, 4, 2, 24)

    channel = 9  # GM drums

    for (step, inst, velocity) in hits:
        pitch    = GM.get(inst, 38)
        beat_pos = step * 0.25
        midi.addNote(0, channel, pitch, beat_pos, 0.2, velocity)

    path = output_dir / f"{pattern_id}.mid"
    with open(path, "wb") as f:
        midi.writeFile(f)
    return path


def _hits_to_notes(hits: list) -> list:
    """Convert hits to note format for fingerprinting."""
    return [(h[0], GM.get(h[1], 38), 0.2, h[2]) for h in hits]


def run(output_dir: Path, genre: str, bpm: int) -> dict:
    """
    Generate a drum pattern, register it, write MIDI.
    Returns result dict with id, path, repeat status.
    """
    hits  = generate(genre)
    notes = _hits_to_notes(hits)
    entry = register("drum", genre, "drums", notes)

    if entry["repeat"]:
        hits  = generate(genre)
        notes = _hits_to_notes(hits)
        entry = register("drum", genre, "drums", notes)

    midi_path = write_midi(output_dir, hits, bpm, entry["id"])

    return {
        "id":    entry["id"],
        "path":  midi_path,
        "hits":  hits,
        "entry": entry,
    }
