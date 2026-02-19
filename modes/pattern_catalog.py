# modes/pattern_catalog.py
# SAN3 Producer — Pattern Catalog
# Tracks every generated pattern with a unique ID.
# Prevents repeats. Persistent across sessions.

import json
import hashlib
from pathlib import Path

CATALOG_FILE = Path(__file__).parent.parent / "outputs" / "pattern_catalog.json"


def _load() -> dict:
    if CATALOG_FILE.exists():
        try:
            return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save(catalog: dict) -> None:
    CATALOG_FILE.parent.mkdir(exist_ok=True)
    CATALOG_FILE.write_text(json.dumps(catalog, indent=2), encoding="utf-8")


def _fingerprint(notes: list) -> str:
    """Create a unique hash from a note pattern."""
    raw = str([(round(t, 3), p, round(d, 3)) for (t, p, d, v) in notes])
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def register(pattern_type: str, genre: str, key: str, notes: list) -> dict:
    """
    Register a generated pattern. Returns its catalog entry.
    If pattern already exists, returns existing entry with repeat=True.

    pattern_type: 'melody' | 'drum' | 'bass' | 'chords' | 'counter'
    """
    catalog = _load()
    fp = _fingerprint(notes)

    # Check for duplicate
    for pid, entry in catalog.items():
        if entry.get("fingerprint") == fp:
            return {**entry, "repeat": True, "id": pid}

    # Assign new ID — count existing patterns of this type
    existing = [e for e in catalog.values()
                if e.get("type") == pattern_type and e.get("genre") == genre]
    number   = len(existing) + 1
    pid      = f"{genre.replace(' ', '_').upper()}_{pattern_type.upper()}_{number:04d}"

    entry = {
        "id":          pid,
        "type":        pattern_type,
        "genre":       genre,
        "key":         key,
        "fingerprint": fp,
        "note_count":  len(notes),
        "repeat":      False,
    }

    catalog[pid] = entry
    _save(catalog)
    return entry


def list_patterns(genre: str = None, pattern_type: str = None) -> list:
    """List all registered patterns, optionally filtered."""
    catalog = _load()
    results = list(catalog.values())
    if genre:
        results = [e for e in results if e.get("genre") == genre]
    if pattern_type:
        results = [e for e in results if e.get("type") == pattern_type]
    return sorted(results, key=lambda e: e["id"])


def catalog_size() -> int:
    return len(_load())
