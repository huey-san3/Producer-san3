"""
smoke_test.py — SAN3 Producer
==============================
Verifies all modules load and generate output correctly.
No external API calls. No user input required.
Run this after setup to confirm everything works.

Usage:
    python smoke_test.py
"""

import sys
import importlib.util
import builtins
from pathlib import Path


PASS = "  [PASS]"
FAIL = "  [FAIL]"
INFO = "  [INFO]"


def mock_input(responses: list):
    """Replace input() with a mock that returns preset responses."""
    answers = iter(responses)
    return lambda _="": next(answers, "")


def run_test(name: str, filepath: str, inputs: list) -> bool:
    """Load a mode module and run it with mocked inputs."""
    path = Path(filepath)
    if not path.exists():
        print(f"{FAIL} {name}: file not found at {filepath}")
        return False

    original_input = builtins.input
    try:
        builtins.input = mock_input(inputs)
        spec = importlib.util.spec_from_file_location("test_module", path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        out = Path("outputs")
        out.mkdir(exist_ok=True)
        mod.run(out)

        print(f"{PASS} {name}")
        return True
    except Exception as e:
        print(f"{FAIL} {name}: {e}")
        return False
    finally:
        builtins.input = original_input


def check_dependency(package: str, import_name: str = None) -> bool:
    """Check that a Python package is importable."""
    try:
        __import__(import_name or package)
        print(f"{PASS} Dependency: {package}")
        return True
    except ImportError:
        print(f"{FAIL} Dependency: {package} — run: pip install {package}")
        return False


def check_outputs() -> None:
    """List all generated output files."""
    out = Path("outputs")
    files = sorted(out.iterdir()) if out.exists() else []
    print(f"\n{INFO} Output files generated ({len(files)} total):")
    for f in files:
        print(f"       {f.name} ({f.stat().st_size:,} bytes)")


def main() -> None:
    print("\n" + "="*52)
    print("  SAN3 PRODUCER — Smoke Test")
    print("="*52 + "\n")

    all_pass = True

    # --- Check dependencies ---
    print("Checking dependencies:")
    all_pass &= check_dependency("midiutil")
    all_pass &= check_dependency("colorama")
    print()

    # --- Check module files exist ---
    print("Checking module files:")
    modules = [
        "modes/beat_block.py",
        "modes/808_dial.py",
        "modes/drum_build.py",
        "modes/midi_gen.py",
        "modes/mix_chain.py",
        "main.py",
    ]
    for m in modules:
        exists = Path(m).exists()
        status = PASS if exists else FAIL
        print(f"{status} {m}")
        all_pass &= exists
    print()

    # --- Run each mode ---
    print("Running all modes with test inputs:")

    all_pass &= run_test(
        "Beat Block (trap/140)",
        "modes/beat_block.py",
        ["trap", "140"]
    )

    all_pass &= run_test(
        "808 Dial (F/trap/full chain)",
        "modes/808_dial.py",
        ["F", "trap", "7"]
    )

    all_pass &= run_test(
        "Drum Build (hip hop/90)",
        "modes/drum_build.py",
        ["hip hop", "90"]
    )

    all_pass &= run_test(
        "MIDI Gen (rnb/melody/Bb/4bars)",
        "modes/midi_gen.py",
        ["rnb", "A#", "dorian", "85", "4", "1"]
    )

    all_pass &= run_test(
        "Mix Chain (melodic/full)",
        "modes/mix_chain.py",
        ["melodic", "6"]
    )

    # --- Show outputs ---
    check_outputs()

    # --- Final result ---
    print()
    if all_pass:
        print("="*52)
        print("  ALL TESTS PASSED — SAN3 Producer is ready.")
        print("  Run: python main.py")
        print("="*52 + "\n")
        sys.exit(0)
    else:
        print("="*52)
        print("  SOME TESTS FAILED — Check errors above.")
        print("  Run: pip install -r requirements.txt")
        print("="*52 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
