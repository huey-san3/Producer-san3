# SAN3 Producer — Co-Producer Tool

**Hip Hop | RnB | Rap | Trap**

An AI co-producer that runs beside you in your FL Studio sessions.
Not a tutorial. Not a plugin. A producer sitting next to you.

---

## What It Does

| Mode | What You Get |
|------|-------------|
| **Beat Block** | Stuck? Get a genre, BPM, key, 3-step ritual + MIDI seed in under a minute |
| **808 Dial** | Full FL Studio 808 tuning + mixer chain — sidechain, EQ, compression, mono check |
| **Drum Build** | Trap, drill, hip hop, rnb, melodic patterns — velocity guide + MIDI files |
| **MIDI Gen** | Melody, chords, bass line, counter melody — diatonic, genre-aware, importable |
| **Mix Chain** | Channel-by-channel FL Studio mix guide. Every plugin, every frequency, explained |

---

## Setup

```bash
git clone https://github.com/huey-san3/Producer-san3.git
cd Producer-san3
pip install -r requirements.txt
python smoke_test.py
python main.py
```

**Requirements:** Python 3.10/3.11 | Windows 11 / macOS / Linux | FL Studio (any edition)

---

## Importing MIDI into FL Studio

1. Piano Roll → right-click → **Import MIDI**
2. Select the `.mid` file from `outputs/`
3. `Ctrl+A` → `Alt+Q` → Quantize **1/16**
4. Humanize: Select All → right-click → Randomize velocity ±10

---

## FL Studio Plugins Used (native only)

Parametric EQ 2 · Fruity Compressor · Maximus · Fruity Reverb 2 · Fruity Delay 3  
Fruity Fast Dist · Fruity Peak Controller · Fruity Stereo Enhancer · Soundgoodizer

No third-party plugins required.

---

## Structure

```
Producer-san3/
  main.py          ← run this
  smoke_test.py    ← verify setup
  requirements.txt
  modes/
    beat_block.py
    808_dial.py
    drum_build.py
    midi_gen.py
    mix_chain.py
  outputs/         ← all generated files
```

---

MIT License | Built under the SAN3 Engineering Constitution
