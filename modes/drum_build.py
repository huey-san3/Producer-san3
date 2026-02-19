# modes/drum_build.py
# SAN3 Producer — Drum Build Mode
# For: Hip Hop | RnB | Rap | Trap producers

from pathlib import Path
from midiutil import MIDIFile

# General MIDI drum map (standard, works in FL Studio with any GM drum kit)
GM_DRUMS = {
    "kick":       36,  # Bass Drum 1
    "snare":      38,  # Acoustic Snare
    "ghost":      38,  # Ghost snare (same note, lower velocity)
    "clap":       39,  # Hand Clap
    "hihat_cl":   42,  # Closed Hi-Hat
    "hihat_op":   46,  # Open Hi-Hat
    "hihat_ped":  44,  # Pedal Hi-Hat
    "ride":       51,  # Ride Cymbal
    "crash":      49,  # Crash Cymbal
    "tom_hi":     50,  # High Tom
    "tom_lo":     45,  # Low Tom
    "rim":        37,  # Side Stick / Rim
    "cowbell":    56,  # Cowbell (bounce/bounce)
    "shaker":     70,  # Maracas / Shaker
    "snap":       39,  # Finger Snap (same as clap)
}

# Genre drum patterns
# Format: list of (step_16th, instrument, velocity)
# 16-step grid, 1 bar. Patterns are 2 bars (32 entries allowed)

PATTERNS = {

    "trap": {
        "bpm": 140,
        "swing": 0,
        "description": "Atlanta Trap — Hard kick, snare on 2 and 4, rolling hi-hats",
        "feel": "Hard, punchy. Kick pattern is the identity. Hats breathe.",
        "steps": [
            # Bar 1
            ( 0, "kick",     110), ( 2, "kick",     90),  # kicks
            ( 4, "snare",    100), ( 4, "clap",     95),  # snare+clap stack
            ( 8, "kick",     105), (10, "kick",     85), (11, "kick", 70),
            (12, "snare",    100), (12, "clap",     95),
            (14, "kick",     75),
            # Hats bar 1
            ( 0, "hihat_cl", 90), ( 1, "hihat_cl", 60), ( 2, "hihat_cl", 80),
            ( 3, "hihat_cl", 55), ( 4, "hihat_cl", 70), ( 5, "hihat_cl", 90),
            ( 6, "hihat_cl", 60), ( 7, "hihat_cl", 80), ( 8, "hihat_cl", 90),
            ( 9, "hihat_cl", 55), (10, "hihat_cl", 70), (11, "hihat_cl", 60),
            (12, "hihat_cl", 80), (13, "hihat_cl", 90), (14, "hihat_cl", 60),
            (15, "hihat_cl", 70),
            # Open hat accents
            ( 5, "hihat_op", 75), (13, "hihat_op", 75),
            # Bar 2 — variation
            (16, "kick",     110), (18, "kick",     85),
            (20, "snare",    100), (20, "clap",     90),
            (23, "kick",     70),  (24, "kick",     105),
            (26, "kick",     80),  (27, "kick",     65),
            (28, "snare",    100), (28, "clap",     90),
            (30, "ghost",    35),  (31, "kick",     60),
        ],
    },

    "drill": {
        "bpm": 144,
        "swing": 0,
        "description": "UK/Chicago Drill — Sliding hi-hats, syncopated kick, cold snare",
        "feel": "Cold and mechanical. Kick and hat work together to create the slide feel.",
        "steps": [
            # Bar 1
            ( 0, "kick",     110),
            ( 3, "kick",     80),
            ( 4, "snare",    95),
            ( 6, "kick",     75),
            ( 8, "kick",     105), ( 9, "kick", 70),
            (10, "kick",     60),
            (12, "snare",    95),
            (14, "kick",     80),
            (15, "kick",     65),
            # Hi-hats — sliding triplet feel
            ( 0, "hihat_cl", 100), ( 1, "hihat_cl", 50), ( 2, "hihat_cl", 80),
            ( 3, "hihat_op", 65),  ( 4, "hihat_cl", 90), ( 5, "hihat_cl", 55),
            ( 6, "hihat_cl", 75),  ( 7, "hihat_op", 60), ( 8, "hihat_cl", 100),
            ( 9, "hihat_cl", 50),  (10, "hihat_cl", 80), (11, "hihat_op", 65),
            (12, "hihat_cl", 90),  (13, "hihat_cl", 55), (14, "hihat_cl", 75),
            (15, "hihat_op", 70),
            # Bar 2 — variation
            (16, "kick",     110), (18, "kick",     75),
            (19, "kick",     55),
            (20, "snare",    95),
            (22, "kick",     80),  (23, "kick",     60),
            (24, "kick",     100), (26, "kick",     70),
            (27, "kick",     50),
            (28, "snare",    95),
            (30, "kick",     75),
        ],
    },

    "hip hop": {
        "bpm": 90,
        "swing": 12,
        "description": "Boom Bap / Classic Hip Hop — Punchy kick, crisp snare, swinging hats",
        "feel": "Laid back groove. Let the swing breathe. Snare has attitude.",
        "steps": [
            # Bar 1
            ( 0, "kick",     110),
            ( 2, "kick",     85),
            ( 4, "snare",    100),
            ( 8, "kick",     105), (10, "kick", 70),
            (12, "snare",    100),
            (14, "kick",     65),
            # Hats — swinging
            ( 0, "hihat_cl", 85), ( 2, "hihat_cl", 65),
            ( 4, "hihat_cl", 80), ( 6, "hihat_cl", 60),
            ( 8, "hihat_cl", 90), (10, "hihat_cl", 65),
            (12, "hihat_cl", 80), (14, "hihat_cl", 55),
            # Open hats
            ( 6, "hihat_op", 70), (14, "hihat_op", 70),
            # Rim shot ghost
            ( 2, "rim",      40), (10, "rim",      35),
            # Bar 2
            (16, "kick",     110), (18, "kick",     80),
            (20, "snare",    105),
            (22, "kick",     60),
            (24, "kick",     100),
            (26, "kick",     75),
            (28, "snare",    105),
            (30, "ghost",    40),
            (31, "kick",     55),
        ],
    },

    "rnb": {
        "bpm": 85,
        "swing": 8,
        "description": "Modern RnB — Soft kick, snap snare, shuffling hats, space to breathe",
        "feel": "Intimate. Room for the vocals. Nothing is fighting for space.",
        "steps": [
            # Bar 1
            ( 0, "kick",     95),
            ( 3, "kick",     65),
            ( 4, "snap",     85),
            ( 6, "kick",     55),
            ( 8, "kick",     90),
            (10, "kick",     60),
            (12, "snap",     85),
            (14, "ghost",    30),
            # Hats — sparse and shuffling
            ( 0, "hihat_cl", 70), ( 4, "hihat_cl", 65),
            ( 6, "hihat_cl", 55), ( 8, "hihat_cl", 75),
            (10, "hihat_cl", 60), (12, "hihat_cl", 65),
            (14, "hihat_op", 60),
            # Shaker layer
            ( 2, "shaker",   50), ( 6, "shaker",   45),
            (10, "shaker",   50), (14, "shaker",   45),
            # Bar 2
            (16, "kick",     90),
            (19, "kick",     55),
            (20, "snap",     85),
            (22, "kick",     50),
            (24, "kick",     85),
            (27, "kick",     50),
            (28, "snap",     85),
            (30, "ghost",    35),
        ],
    },

    "melodic": {
        "bpm": 140,
        "swing": 0,
        "description": "Melodic Trap — Punchy but airy. Room for the melody to live.",
        "feel": "Emotional trap. Drums support the vibe, not the other way around.",
        "steps": [
            # Bar 1
            ( 0, "kick",     105),
            ( 3, "kick",     70),
            ( 4, "snare",    95), ( 4, "clap", 85),
            ( 7, "kick",     55),
            ( 8, "kick",     100),
            (11, "kick",     65),
            (12, "snare",    95), (12, "clap", 85),
            (14, "ghost",    35),
            # Hats — open and airy
            ( 0, "hihat_cl", 80), ( 2, "hihat_op", 65),
            ( 4, "hihat_cl", 75), ( 6, "hihat_op", 60),
            ( 8, "hihat_cl", 85), (10, "hihat_op", 65),
            (12, "hihat_cl", 75), (14, "hihat_op", 60),
            # Bar 2
            (16, "kick",     105), (18, "kick",     70),
            (20, "snare",    95),  (20, "clap",     85),
            (23, "kick",     55),
            (24, "kick",     100),
            (28, "snare",    95),  (28, "clap",     85),
            (30, "ghost",    40),  (31, "ghost",    30),
        ],
    },
}


def run(output_dir: Path) -> None:
    print("\n" + "="*52)
    print("  DRUM BUILD — SAN3 Co-Producer")
    print("  Hip Hop | RnB | Rap | Trap")
    print("="*52)

    print("\nAvailable patterns:")
    for i, (name, data) in enumerate(PATTERNS.items(), 1):
        print(f"  {i}. {name.upper()} — {data['bpm']} BPM — {data['description']}")

    choice = input("\n  Pick a genre (name or number, ENTER for trap): ").strip().lower()
    genre  = _resolve_genre(choice)
    preset = PATTERNS[genre]

    bpm_input = input(f"  BPM? (ENTER for {preset['bpm']}): ").strip()
    try:
        bpm = int(bpm_input) if bpm_input else preset["bpm"]
    except ValueError:
        bpm = preset["bpm"]

    print(f"\n  Genre : {genre.upper()}")
    print(f"  BPM   : {bpm}")
    print(f"  Feel  : {preset['feel']}")

    # Write step notation guide
    guide_path = _write_drum_guide(output_dir, genre, bpm, preset)
    print(f"\n  Drum guide    → {guide_path.name}")

    # Generate MIDI
    midi_path = _generate_drum_midi(output_dir, genre, bpm, preset)
    print(f"  Drum MIDI     → {midi_path.name}")

    print("\n  Import the MIDI into FL Studio:")
    print("  Channel Rack → drag .mid onto a drum sampler (e.g., FPC or Fruity Beats)")
    print("  Or: Piano Roll → right-click → Import MIDI\n")


def _resolve_genre(raw: str) -> str:
    names = list(PATTERNS.keys())
    # Try number
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(names):
            return names[idx]
    except ValueError:
        pass
    # Try name match
    for name in names:
        if raw in name or name in raw:
            return name
    return "trap"


def _write_drum_guide(output_dir: Path, genre: str,
                      bpm: int, preset: dict) -> Path:
    steps = preset["steps"]

    # Build ASCII grid — bar 1 only (steps 0-15)
    def grid_row(name, key):
        row = ["."] * 16
        for (step, inst, vel) in steps:
            if step < 16 and inst == key:
                row[step] = "X" if vel >= 80 else ("x" if vel >= 50 else "o")
        return " ".join(row[:4]) + " | " + " ".join(row[4:8]) + " | " + \
               " ".join(row[8:12]) + " | " + " ".join(row[12:16])

    grid = f"""
  STEP:       1 . . .   2 . . .   3 . . .   4 . . .
  KICK:       {grid_row("kick", "kick")}
  SNARE/CLAP: {grid_row("snare", "snare")}
  GHOST:      {grid_row("ghost", "ghost")}
  HIHAT CL:   {grid_row("hihat_cl", "hihat_cl")}
  HIHAT OP:   {grid_row("hihat_op", "hihat_op")}
  RIM/SNAP:   {grid_row("rim", "rim") if any(s[1]=="rim" for s in steps) else grid_row("snap", "snap")}
"""

    vel_guide = _build_velocity_guide(genre)

    content = f"""
================================================================================
  DRUM BUILD — {genre.upper()} | {bpm} BPM
  {preset['description']}
  Generated by: SAN3 Co-Producer
================================================================================

FEEL: {preset['feel']}
SWING: {preset['swing']}% {'(apply in FL Studio: Channel Rack → right-click pattern → Swing)' if preset['swing'] > 0 else '(straight, no swing)'}

--------------------------------------------------------------------------------
STEP GRID — BAR 1 (16-step, 1/16th note resolution)
Legend: X = hard hit (80-110) | x = medium (50-79) | o = ghost (30-49) | . = rest
--------------------------------------------------------------------------------
{grid}
--------------------------------------------------------------------------------
VELOCITY GUIDE
--------------------------------------------------------------------------------
{vel_guide}
--------------------------------------------------------------------------------
FL STUDIO SETUP
--------------------------------------------------------------------------------

  OPTION A — FPC (Fruity Pad Controller)
    1. Channel Rack → + → FPC
    2. Import the .mid file: right-click Piano Roll → Import MIDI
    3. Map pads: Kick=C1, Snare=D1, Hihat=F#1, Open=A#1 (GM standard)

  OPTION B — Step Sequencer (manual entry)
    1. Add samples to Channel Rack
    2. Set pattern to 16 steps
    3. Follow the grid above for placement
    4. Right-click each button to set velocity
    5. If swing: right-click pattern name → Swing → set to {preset['swing']}%

  OPTION C — Import MIDI directly
    1. Load any drum sampler (FPC, FLEX drum preset, or VST)
    2. Piano Roll → right-click → Import MIDI → select the .mid file
    3. Confirm GM drum mapping matches your kit

--------------------------------------------------------------------------------
HUMANIZATION (makes it feel live, not robotic)
--------------------------------------------------------------------------------

  After placing all steps:
    Select All (Ctrl+A) in Piano Roll
    Right-click a note → Randomize → Velocity: ±10
    Right-click a note → Randomize → Start time: ±3 ticks (NOT more — subtle)

  This alone separates professional-sounding drums from amateur patterns.

--------------------------------------------------------------------------------
LAYERING TIPS
--------------------------------------------------------------------------------

  KICK: Layer a sub kick (808-style) under a punchy sample kick
    → Sample kick handles the transient (click/punch)
    → Sub kick handles the weight (boom below 80hz)
    → Cut the sub kick above 150hz to avoid mud

  SNARE: Layer clap + snare for trap. Adjust timing slightly (1-3ms apart)
    → Creates width and thickens the hit
    → Use Fruity Stereo Enhancer: 60% width on the clap layer only

  HI-HATS: Velocity variation is everything
    → If every hat is the same velocity, it sounds fake
    → Trap hats: accent every 3rd-5th hit randomly for the rolling feel

================================================================================
"""

    safe = genre.replace(" ", "_")
    path = output_dir / f"drum_pattern_{safe}_{bpm}bpm.txt"
    path.write_text(content.strip(), encoding="utf-8")
    return path


def _build_velocity_guide(genre: str) -> str:
    guides = {
        "trap":    "  Kick:     Beat 1=110, syncopated kicks=70-90\n  Snare:    100 main, ghost=30-40\n  Hats:     Alternate 55-90, accent every 5th hit at 100",
        "drill":   "  Kick:     110 on downbeats, sliding kicks=50-80\n  Snare:    95 cold and dry\n  Hats:     100 downbeat, 50-65 slides, open=65-70",
        "hip hop": "  Kick:     110 on 1, 85-90 on syncopated\n  Snare:    100 with attitude, rim ghost=35-45\n  Hats:     85 on downbeats, 55-65 offbeats — let the swing do the work",
        "rnb":     "  Kick:     90-95 soft and warm, ghost kicks=50-65\n  Snap:     85 clean, sits back in mix\n  Hats:     60-75 sparse — space is the instrument",
        "melodic": "  Kick:     105 on 1, softer syncopated kicks=65-70\n  Snare:    95 with clap layer — emotional, not aggressive\n  Hats:     Open hats 60-65 for airiness, closed 75-85",
    }
    return guides.get(genre, guides["trap"])


def _generate_drum_midi(output_dir: Path, genre: str,
                        bpm: int, preset: dict) -> Path:
    """Generate a 2-bar MIDI drum file using GM drum map."""

    steps = preset["steps"]
    midi  = MIDIFile(1)
    midi.addTempo(0, 0, bpm)
    midi.addTimeSignature(0, 0, 4, 2, 24)

    track   = 0
    channel = 9  # Channel 10 (0-indexed as 9) = GM drums

    ticks_per_beat = 4  # 1/16th note = 0.25 beats

    for (step, inst, velocity) in steps:
        pitch    = GM_DRUMS.get(inst, 38)
        beat_pos = step * 0.25  # convert 16th step to beat position
        midi.addNote(track, channel, pitch, beat_pos, 0.2, velocity)

    safe = genre.replace(" ", "_")
    path = output_dir / f"drum_pattern_{safe}_{bpm}bpm.mid"
    with open(path, "wb") as f:
        midi.writeFile(f)
    return path


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "outputs"
    out.mkdir(exist_ok=True)
    run(out)
