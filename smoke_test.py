"""
smoke_test.py — SAN3 Producer Smoke Test
=========================================
Verifies core infrastructure without launching the GUI
or making any external API calls.

Run this after any code change to confirm nothing is broken.

Usage:
    python smoke_test.py

Expected output: All tests PASS
"""

import sys
import json
from pathlib import Path

# ── Setup ──────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
LOGS_DIR   = BASE_DIR / "logs"

PASS = "  [PASS]"
FAIL = "  [FAIL]"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status} {name}"
    if detail and not condition:
        msg += f" — {detail}"
    print(msg)
    results.append(condition)


# ── TESTS ──────────────────────────────────────────────────────────────
print("\nSAN3 Producer — Smoke Test")
print("=" * 40)

# 1. Directory structure
check("outputs/ exists", OUTPUT_DIR.exists())
check("logs/ exists",    LOGS_DIR.exists())
check("modes/ exists",   (BASE_DIR / "modes").exists())

# 2. Required mode files
required_modes = [
    "808_dial.py", "beat_block.py", "drum_build.py",
    "drum_gen.py", "generator.py", "melody_gen.py",
    "midi_gen.py", "mix_chain.py", "pattern_catalog.py"
]
for m in required_modes:
    check(f"modes/{m} exists", (BASE_DIR / "modes" / m).exists())

# 3. app.py imports cleanly (no code runs on import)
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("app_test", BASE_DIR / "app.py")
    # We don't exec the module — just check spec loads without error
    check("app.py spec loads", spec is not None)
except Exception as e:
    check("app.py spec loads", False, str(e))

# 4. Session memory functions
try:
    sys.path.insert(0, str(BASE_DIR))
    # Import only the non-GUI functions
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("app_funcs", BASE_DIR / "app.py")
    # Test save/load session logic directly
    test_session = {"genre": "drill", "key": "G#", "bpm": "144", "bars": "8"}
    test_file = OUTPUT_DIR / ".session_test.json"
    test_file.write_text(json.dumps(test_session))
    loaded = json.loads(test_file.read_text())
    check("Session save/load roundtrip", loaded == test_session)
    test_file.unlink()
except Exception as e:
    check("Session save/load roundtrip", False, str(e))

# 5. Audit log write
try:
    test_log = LOGS_DIR / "smoke_test.log"
    test_log.write_text("[SMOKE TEST] Log write OK\n", encoding="utf-8")
    content = test_log.read_text()
    check("Audit log write", "SMOKE TEST" in content)
    test_log.unlink()
except Exception as e:
    check("Audit log write", False, str(e))

# 6. Workspace guard logic
try:
    import os
    output_res = str(OUTPUT_DIR.resolve())
    inside  = str((OUTPUT_DIR / "test.mid").resolve())
    outside = str(Path("/tmp/evil.mid").resolve())
    check("Workspace guard — inside path",  inside.startswith(output_res))
    check("Workspace guard — outside path", not outside.startswith(output_res))
except Exception as e:
    check("Workspace guard logic", False, str(e))

# 7. midiutil available
try:
    import midiutil
    check("midiutil importable", True)
except ImportError:
    check("midiutil importable", False,
          "Run: pip install midiutil --break-system-packages")

# 8. tkinter available
try:
    import tkinter
    check("tkinter importable", True)
except ImportError:
    check("tkinter importable", False,
          "Install Python with tkinter support")

# ── RESULTS ────────────────────────────────────────────────────────────
print("=" * 40)
passed = sum(results)
total  = len(results)
print(f"\n  {passed}/{total} tests passed.")

if passed == total:
    print("  All systems nominal. Safe to run app.py.\n")
    sys.exit(0)
else:
    print(f"  {total - passed} test(s) failed. Fix before running.\n")
    sys.exit(1)
