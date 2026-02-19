"""
main.py — SAN3 Producer Co-Producer
=====================================
Single entrypoint for all production tools.

Usage:
    python main.py

Modes:
    1. Beat Block  — creative unlock, beat starter ritual + MIDI seed
    2. 808 Dial    — 808 tuning + FL Studio mixer chain
    3. Drum Build  — drum pattern generator + MIDI file
    4. MIDI Gen    — melody / chord / bass MIDI generator
    5. Mix Chain   — channel-by-channel FL Studio mix guide

Requirements:
    pip install -r requirements.txt

All outputs saved to: outputs/
"""

import sys
from pathlib import Path


def main() -> None:
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    _print_header()

    while True:
        mode = _select_mode()
        if mode is None:
            print("\n  Session closed. Go make something.\n")
            break

        _run_mode(mode, output_dir)

        again = input("\n  Run another mode? (y / ENTER to exit): ").strip().lower()
        if again != "y":
            print("\n  Session closed. Go make something.\n")
            break


def _print_header() -> None:
    print("\n" + "="*52)
    print("  SAN3 PRODUCER — Co-Producer Tool")
    print("  Hip Hop | RnB | Rap | Trap")
    print("  All outputs saved to: outputs/")
    print("="*52)


def _select_mode() -> str | None:
    print("\n  What do you need?\n")
    print("    1. Beat Block   — stuck? start here")
    print("    2. 808 Dial     — tune + mix your 808")
    print("    3. Drum Build   — generate a drum pattern")
    print("    4. MIDI Gen     — melody / chords / bass")
    print("    5. Mix Chain    — full FL Studio mix guide")
    print("    6. GENERATOR    — random patterns, unique IDs, San3_DaD3aL Boi")
    print("    0. Exit\n")

    choice = input("  Choice: ").strip()

    modes = {"1", "2", "3", "4", "5", "6"}
    if choice in modes:
        return choice
    if choice == "0" or choice == "":
        return None

    print("  Enter 1-5 or 0 to exit.")
    return _select_mode()


def _run_mode(mode: str, output_dir: Path) -> None:
    import importlib.util

    mode_files = {
        "1": "modes/beat_block.py",
        "2": "modes/808_dial.py",
        "3": "modes/drum_build.py",
        "4": "modes/midi_gen.py",
        "5": "modes/mix_chain.py",
        "6": "modes/generator.py",
    }

    filepath = Path(__file__).parent / mode_files[mode]

    if not filepath.exists():
        print(f"\n  ERROR: Module not found at {filepath}")
        print("  Run: python smoke_test.py to check installation\n")
        return

    spec = importlib.util.spec_from_file_location("mode_module", filepath)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.run(output_dir)


if __name__ == "__main__":
    main()
