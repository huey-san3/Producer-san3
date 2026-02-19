# modes/generator.py
# SAN3 Producer — Procedural Pattern Generator
# Randomly generates unique drum + melody patterns
# Every pattern assigned a permanent ID — no repeats ever
# Beat tag: San3_DaD3aL Boi

from pathlib import Path
from midiutil import MIDIFile
import random
import json
import hashlib
from datetime import datetime

# ── IDENTITY ───────────────────────────────────────────────────────────
BEAT_TAG   = "San3_DaD3aL Boi"
HISTORY_FILE = Path(__file__).parent.parent / "outputs" / ".pattern_history.json"

# ── MUSIC THEORY ───────────────────────────────────────────────────────
NOTES = {
    "C":60,"C#":61,"D":62,"D#":63,"E":64,"F":65,
    "F#":66,"G":67,"G#":68,"A":69,"A#":70,"B":71,
}
ALL_NOTES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

SCALES = {
    "minor":      [0,2,3,5,7,8,10],
    "minor_pent": [0,3,5,7,10],
    "dorian":     [0,2,3,5,7,9,10],
    "chromatic":  [0,2,3,5,7,8,11],
}

GENRE_DEFAULTS = {
    "trap":    {"key":"F",  "scale":"minor",      "bpm":140, "swing":0},
    "drill":   {"key":"G#", "scale":"minor",      "bpm":144, "swing":0},
    "hip hop": {"key":"A",  "scale":"minor_pent", "bpm":90,  "swing":12},
    "rnb":     {"key":"A#", "scale":"dorian",     "bpm":85,  "swing":8},
    "melodic": {"key":"C#", "scale":"minor",      "bpm":140, "swing":0},
}

# GM drum map
GM = {
    "kick":36, "snare":38, "clap":39,
    "hihat_cl":42, "hihat_op":46, "hihat_ped":44,
    "rim":37, "snap":39, "shaker":70, "tom_lo":45,
}


# ── HISTORY ────────────────────────────────────────────────────────────
def _load_history() -> dict:
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            return {}
    return {}

def _save_history(history: dict) -> None:
    HISTORY_FILE.write_text(json.dumps(history, indent=2))

def _next_id(history: dict) -> str:
    n = len(history) + 1
    return f"GEN-{n:04d}"

def _seed_from_id(pattern_id: str) -> int:
    """Deterministic seed from ID — same ID always gives same pattern."""
    return int(hashlib.md5(pattern_id.encode()).hexdigest(), 16) % (2**31)


# ── MAIN ───────────────────────────────────────────────────────────────
def run(output_dir: Path) -> None:
    print("\n" + "="*52)
    print(f"  GENERATOR — SAN3 Co-Producer")
    print(f"  Tag: {BEAT_TAG}")
    print("="*52)

    history = _load_history()

    # Menu
    print(f"\n  Patterns generated so far: {len(history)}")
    print("\n  What do you want?")
    print("    1. Generate new drum pattern")
    print("    2. Generate new melody")
    print("    3. Generate both (full starter kit)")
    print("    4. Recall a pattern by ID")

    choice = input("\n  Choice (ENTER for 3): ").strip() or "3"

    # Genre
    genre_in = input("  Genre (trap/drill/hip hop/rnb/melodic, ENTER for trap): ").strip().lower()
    genre    = genre_in if genre_in in GENRE_DEFAULTS else "trap"
    defaults = GENRE_DEFAULTS[genre]

    # Key
    key_in = input(f"  Key? (ENTER for {defaults['key']}): ").strip().upper()
    key    = key_in if key_in in NOTES else defaults["key"]

    # BPM
    bpm_in = input(f"  BPM? (ENTER for {defaults['bpm']}): ").strip()
    try:
        bpm = int(bpm_in) if bpm_in else defaults["bpm"]
    except ValueError:
        bpm = defaults["bpm"]

    # Bars
    bars_in = input("  Bars? (4/8, ENTER for 4): ").strip()
    bars    = int(bars_in) if bars_in in ["4","8"] else 4

    if choice == "4":
        _recall_pattern(history, output_dir, genre, key, bpm, bars)
        return

    # Generate
    if choice in ["1","3"]:
        pid   = _next_id(history)
        seed  = _seed_from_id(pid)
        path  = _gen_drums(output_dir, pid, seed, genre, bpm, bars)
        history[pid] = {
            "type":"drums","genre":genre,"key":key,"bpm":bpm,
            "bars":bars,"seed":seed,"file":path.name,
            "tag":BEAT_TAG,"created":datetime.now().isoformat()
        }
        print(f"\n  [{pid}] Drum pattern → {path.name}")

    if choice in ["2","3"]:
        pid   = _next_id(history)
        seed  = _seed_from_id(pid)
        path  = _gen_melody(output_dir, pid, seed, genre, key, bpm, bars)
        history[pid] = {
            "type":"melody","genre":genre,"key":key,"bpm":bpm,
            "bars":bars,"seed":seed,"file":path.name,
            "tag":BEAT_TAG,"created":datetime.now().isoformat()
        }
        print(f"  [{pid}] Melody       → {path.name}")

    _save_history(history)
    print(f"\n  Tag: {BEAT_TAG}")
    print(f"  Total patterns generated: {len(history)}")
    print("  Import .mid into FL Studio Piano Roll.\n")


def _recall_pattern(history, output_dir, genre, key, bpm, bars):
    if not history:
        print("  No patterns generated yet.")
        return
    print("\n  Recent patterns:")
    recent = list(history.items())[-10:]
    for pid, meta in recent:
        print(f"    {pid} — {meta['type']} | {meta['genre']} | {meta['key']} | {meta['bpm']} BPM | {meta['file']}")
    recall_id = input("\n  Enter ID to recall (e.g. GEN-0003): ").strip().upper()
    if recall_id not in history:
        print(f"  ID {recall_id} not found.")
        return
    meta  = history[recall_id]
    seed  = meta["seed"]
    rtype = meta["type"]
    if rtype == "drums":
        path = _gen_drums(output_dir, recall_id, seed,
                          meta["genre"], meta["bpm"], meta["bars"])
    else:
        path = _gen_melody(output_dir, recall_id, seed,
                           meta["genre"], meta["key"], meta["bpm"], meta["bars"])
    print(f"  Recalled [{recall_id}] → {path.name}")


# ── DRUM GENERATOR ─────────────────────────────────────────────────────
def _gen_drums(output_dir: Path, pid: str, seed: int,
               genre: str, bpm: int, bars: int) -> Path:
    rng = random.Random(seed)

    # Genre DNA — defines probability weights for each element
    dna = {
        "trap":    {"kick_density":0.35, "snare_ghost":0.4,  "hat_density":0.85, "hat_open":0.15, "swing":0},
        "drill":   {"kick_density":0.40, "snare_ghost":0.2,  "hat_density":0.90, "hat_open":0.25, "swing":0},
        "hip hop": {"kick_density":0.30, "snare_ghost":0.55, "hat_density":0.60, "hat_open":0.20, "swing":12},
        "rnb":     {"kick_density":0.25, "snare_ghost":0.35, "hat_density":0.45, "hat_open":0.10, "swing":8},
        "melodic": {"kick_density":0.30, "snare_ghost":0.30, "hat_density":0.70, "hat_open":0.20, "swing":0},
    }.get(genre, {"kick_density":0.35,"snare_ghost":0.4,"hat_density":0.85,"hat_open":0.15,"swing":0})

    total_steps = 16 * bars
    notes = []

    for bar in range(bars):
        offset = bar * 16

        # ── KICK: always on 1, sometimes on 9, random syncopation
        notes.append((offset + 0,  GM["kick"],     _vel(rng, 105, 115)))
        if rng.random() < 0.85:
            notes.append((offset + 8,  GM["kick"], _vel(rng, 95, 110)))
        # Syncopated kicks
        synco_steps = [2,3,6,7,10,11,14,15]
        for step in synco_steps:
            if rng.random() < dna["kick_density"] * 0.4:
                notes.append((offset + step, GM["kick"], _vel(rng, 65, 90)))

        # ── SNARE: locked on 4 and 12, ghost notes random
        notes.append((offset + 4,  GM["snare"], _vel(rng, 95, 105)))
        notes.append((offset + 12, GM["snare"], _vel(rng, 95, 105)))
        if genre in ["trap","melodic"]:
            notes.append((offset + 4,  GM["clap"], _vel(rng, 85, 95)))
            notes.append((offset + 12, GM["clap"], _vel(rng, 85, 95)))
        # Ghost snares
        ghost_steps = [2,3,6,7,9,10,13,14,15]
        for step in ghost_steps:
            if rng.random() < dna["snare_ghost"] * 0.3:
                notes.append((offset + step, GM["snare"], _vel(rng, 25, 45)))

        # ── HI-HATS: density-driven, velocity variation
        for step in range(16):
            if rng.random() < dna["hat_density"]:
                # Accent pattern — steps 0,4,8,12 louder
                base_vel = 90 if step % 4 == 0 else 60
                vel = _vel(rng, base_vel - 15, base_vel + 10)
                notes.append((offset + step, GM["hihat_cl"], vel))
        # Open hats
        open_candidates = [3,5,7,11,13,15]
        for step in open_candidates:
            if rng.random() < dna["hat_open"]:
                notes.append((offset + step, GM["hihat_op"], _vel(rng, 60, 80)))

        # ── RNB: add shaker
        if genre == "rnb":
            for step in [2,6,10,14]:
                if rng.random() < 0.7:
                    notes.append((offset + step, GM["shaker"], _vel(rng, 40, 60)))

        # ── HIP HOP: add rim shots
        if genre == "hip hop":
            for step in [2,6,10,14]:
                if rng.random() < 0.45:
                    notes.append((offset + step, GM["rim"], _vel(rng, 30, 50)))

    # Write MIDI
    midi = MIDIFile(1)
    midi.addTempo(0, 0, bpm)
    midi.addTimeSignature(0, 0, 4, 2, 24)
    # Embed beat tag in track name
    midi.addTrackName(0, 0, f"{BEAT_TAG} | {pid} | {genre.upper()}")

    for (step, pitch, vel) in notes:
        beat = step * 0.25
        midi.addNote(0, 9, pitch, beat, 0.2, int(vel))

    safe = genre.replace(" ","_")
    path = output_dir / f"drums_{pid}_{safe}_{bpm}bpm.mid"
    with open(path, "wb") as f:
        midi.writeFile(f)
    return path


# ── MELODY GENERATOR ───────────────────────────────────────────────────
def _gen_melody(output_dir: Path, pid: str, seed: int,
                genre: str, key: str, bpm: int, bars: int) -> Path:
    rng     = random.Random(seed)
    root    = NOTES.get(key, 65)
    scale_n = GENRE_DEFAULTS[genre]["scale"]
    ivs     = SCALES[scale_n]

    # Build 3 octaves of scale notes
    scale = []
    for oct in range(3):
        for i in ivs:
            scale.append(root + i + oct * 12)

    # Genre melodic DNA
    dna = {
        "trap":    {"density":0.55, "long_note":0.30, "repeat":0.25, "high_reg":0.3,  "rest_prob":0.15},
        "drill":   {"density":0.65, "long_note":0.15, "repeat":0.45, "high_reg":0.5,  "rest_prob":0.10},
        "hip hop": {"density":0.50, "long_note":0.35, "repeat":0.20, "high_reg":0.25, "rest_prob":0.20},
        "rnb":     {"density":0.40, "long_note":0.50, "repeat":0.15, "high_reg":0.2,  "rest_prob":0.25},
        "melodic": {"density":0.50, "long_note":0.40, "repeat":0.20, "high_reg":0.4,  "rest_prob":0.12},
    }.get(genre, {"density":0.55,"long_note":0.30,"repeat":0.25,"high_reg":0.3,"rest_prob":0.15})

    notes        = []
    beat         = 0.0
    total_beats  = bars * 4
    prev_pitch   = scale[rng.randint(0, len(scale)//2)]

    while beat < total_beats - 0.25:
        # Rest?
        if rng.random() < dna["rest_prob"]:
            beat += rng.choice([0.25, 0.5])
            continue

        # Note duration
        if rng.random() < dna["long_note"]:
            dur = rng.choice([1.0, 1.5, 2.0])
        else:
            dur = rng.choice([0.25, 0.25, 0.5, 0.5, 0.75])

        # Clip to bar boundary
        remaining = total_beats - beat
        dur = min(dur, remaining - 0.01)
        if dur <= 0:
            break

        # Pitch selection — stepwise motion with occasional leaps
        if rng.random() < dna["repeat"]:
            pitch = prev_pitch
        else:
            idx = scale.index(prev_pitch) if prev_pitch in scale else len(scale)//2
            # Mostly move by 1-2 scale steps
            step = rng.choice([-2,-1,-1,-1,0,1,1,1,2,3,-3])
            idx  = max(0, min(len(scale)-1, idx + step))
            pitch = scale[idx]

        # Register preference
        if rng.random() < dna["high_reg"]:
            pitch = min(pitch + 12, scale[-1])

        # Velocity — accent on beat positions
        beat_pos = beat % 4
        if beat_pos in [0.0, 2.0]:
            vel = rng.randint(88, 100)
        elif beat_pos in [1.0, 3.0]:
            vel = rng.randint(78, 92)
        else:
            vel = rng.randint(65, 82)

        notes.append((beat, pitch, dur, vel))
        prev_pitch = pitch
        beat += dur

    # Always end on root
    if beat < total_beats:
        notes.append((beat, root + 12, total_beats - beat - 0.01, 100))

    # Write MIDI
    midi = MIDIFile(1)
    midi.addTempo(0, 0, bpm)
    midi.addTimeSignature(0, 0, 4, 2, 24)
    midi.addTrackName(0, 0, f"{BEAT_TAG} | {pid} | {genre.upper()} | {key}")

    # Sort by start time, deduplicate overlapping same-pitch notes
    notes.sort(key=lambda x: x[0])
    seen = {}
    clean = []
    for (start, pitch, dur, vel) in notes:
        key_p = pitch
        if key_p in seen:
            prev_start, prev_dur = seen[key_p]
            if start < prev_start + prev_dur:
                dur = max(0.1, start - prev_start - 0.01)
                clean[-1] = (prev_start, pitch, dur, clean[-1][3])
        seen[pitch] = (start, dur)
        clean.append((start, pitch, dur, vel))

    for (start, pitch, dur, vel) in clean:
        midi.addNote(0, 0, pitch, start, max(0.1, dur), int(vel))

    safe = genre.replace(" ","_")
    path = output_dir / f"melody_{pid}_{safe}_{key}_{bpm}bpm.mid"
    with open(path, "wb") as f:
        midi.writeFile(f)
    return path


# ── HELPERS ────────────────────────────────────────────────────────────
def _vel(rng: random.Random, lo: int, hi: int) -> int:
    return rng.randint(max(1, lo), min(127, hi))


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "outputs"
    out.mkdir(exist_ok=True)
    run(out)
