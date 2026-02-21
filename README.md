# SAN3 Producer

**Co-Producer for Hip Hop | RnB | Rap | Trap**

Floating GUI panel that sits beside FL Studio. Always on top. No terminal needed during use.

---

## Setup

```bash
# 1. Clone
git clone https://github.com/huey-san3/Producer-san3.git
cd Producer-san3

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python app.py
```

---

## Modes

| Button | What It Does | Output |
|---|---|---|
| BEAT BLOCK | Beat structure guide + reference | `.txt` |
| 808 DIAL | 808 tuning guide for your key | `.txt` |
| DRUM BUILD | Algorithmic drum pattern | `.mid` |
| MIDI GEN | Melody / chord / bass MIDI | `.mid` |
| MIX CHAIN | Full FL Studio mix guide | `.txt` |
| GENERATOR | Full beat loop — drums + melody | `.mid` x2 |

---

## FL Studio Workflow

1. Hit a mode button
2. Click **OPEN OUTPUTS FOLDER**
3. Drag `.mid` files directly into FL Studio Piano Roll
4. `.txt` guides open in any text editor

---

## File Structure

```
Producer-san3/
├── app.py              # Main GUI — run this
├── smoke_test.py       # Run after code changes to verify health
├── requirements.txt
├── .gitignore
├── modes/
│   ├── 808_dial.py
│   ├── beat_block.py
│   ├── drum_build.py
│   ├── drum_gen.py
│   ├── generator.py
│   ├── melody_gen.py
│   ├── midi_gen.py
│   ├── mix_chain.py
│   └── pattern_catalog.py
├── outputs/            # All generated files land here
│   └── .session.json  # Last session settings (auto-saved)
└── logs/
    └── production.log  # Audit trail of every generation
```

---

## Session Memory

The app saves your last used Genre / Key / BPM / Bars automatically.  
On next launch, it restores exactly where you left off.

---

## Audit Log

Every generation is logged to `logs/production.log`:

```
[2026-02-20 02:24:11] GENERATOR   | trap     | F   | 140 BPM | drums_GEN-0001_trap_140bpm.mid
[2026-02-20 02:24:12] GENERATOR   | trap     | F   | 140 BPM | melody_GEN-0002_trap_F_140bpm.mid
```

---

## After Code Changes

Always run the smoke test before committing:

```bash
python smoke_test.py
```

Expected: `All systems nominal.`

---

## Producer Tag

All GENERATOR output MIDI files are tagged:  
**San3_DaD3aL Boi** — embedded in the MIDI track name.

---

*Built inside SAN3 infrastructure. Internal module → future product.*
