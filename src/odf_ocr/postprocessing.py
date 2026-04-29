"""
postprocessing.py – Validierung und Korrektur der OCR-Ergebnisse
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import Optional

logger = logging.getLogger(__name__)

VALID_CODES: set[str] = {
    "KM", "KS", "SV", "BF", "FT", "KF", "UR", "SF", "GZ", "ÜZ",
}

OCR_CHAR_FIXES: dict[str, str] = {
    "O": "0", "o": "0", "l": "1", "I": "1",
    "S": "5", "B": "8", "G": "6", "Z": "2", "T": "7",
}


@dataclass
class ParsedEntry:
    row_index: int
    start: Optional[str] = None
    end: Optional[str] = None
    code: Optional[str] = None
    pause_min: Optional[int] = None
    duration_min: Optional[int] = None
    flag: bool = False
    flag_reason: str = ""
    raw: dict = field(default_factory=dict)


def _fix_digit_chars(raw: str) -> str:
    return "".join(OCR_CHAR_FIXES.get(ch, ch) for ch in raw)


def parse_time(raw: str) -> Optional[str]:
    if not raw or not raw.strip():
        return None
    cleaned = raw.strip().replace(" ", "").replace(",", ":").replace(".", ":")
    cleaned = _fix_digit_chars(cleaned)
    m = re.match(r"^(\d{1,2}):(\d{2})$", cleaned)
    if not m:
        m2 = re.match(r"^(\d{2})(\d{2})$", cleaned)
        if m2:
            h_str, mn_str = m2.group(1), m2.group(2)
        else:
            return None
    else:
        h_str, mn_str = m.group(1), m.group(2)
    h, mn = int(h_str), int(mn_str)
    if h > 23:
        candidates = [
            int(str(h).replace("7", "1", 1)),
            int(str(h).replace("7", "1")),
        ]
        fixed = next((c for c in candidates if 0 <= c <= 23), None)
        if fixed is not None:
            h = fixed
        else:
            return None
    if mn > 59:
        return None
    return f"{h:02d}:{mn:02d}"


def parse_code(raw: str) -> Optional[str]:
    if not raw or not raw.strip():
        return None
    normalized = raw.strip().upper().replace(" ", "")
    if normalized in VALID_CODES:
        return normalized
    matches = get_close_matches(normalized, VALID_CODES, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    return None


def calculate_duration(start: str, end: str, pause_min: int = 0) -> Optional[int]:
    try:
        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
        return (eh * 60 + em) - (sh * 60 + sm) - pause_min
    except Exception:
        return None


def validate_entry(row_index: int, raw: dict) -> ParsedEntry:
    entry = ParsedEntry(row_index=row_index, raw=raw)
    reasons: list[str] = []
    entry.start = parse_time(raw.get("start", ""))
    entry.end = parse_time(raw.get("end", ""))
    if not entry.start:
        reasons.append("Startzeit nicht lesbar")
    if not entry.end:
        reasons.append("Endzeit nicht lesbar")
    entry.code = parse_code(raw.get("code", ""))
    if not entry.code and raw.get("code", "").strip():
        reasons.append(f"Unbekanntes Kürzel: '{raw.get('code')}'")
    try:
        entry.pause_min = int(str(raw.get("pause_min", 0)).strip() or 0)
    except ValueError:
        entry.pause_min = 0
    if entry.start and entry.end:
        entry.duration_min = calculate_duration(entry.start, entry.end, entry.pause_min or 0)
        if entry.duration_min is None:
            reasons.append("Dauer nicht berechenbar")
        elif entry.duration_min < 0:
            reasons.append("Endzeit vor Startzeit")
        elif entry.duration_min > 600:
            reasons.append(f"Schicht > 10h ({entry.duration_min} Min.)")
    entry.flag = len(reasons) > 0
    entry.flag_reason = "; ".join(reasons)
    return entry


def validate_all(rows: list[dict]) -> list[ParsedEntry]:
    return [validate_entry(i, row) for i, row in enumerate(rows)]


def to_export_dict(entries: list[ParsedEntry]) -> list[dict]:
    return [
        {
            "row": e.row_index,
            "start": e.start,
            "end": e.end,
            "code": e.code,
            "pause_min": e.pause_min,
            "duration_min": e.duration_min,
            "flag": e.flag,
            "flag_reason": e.flag_reason,
        }
        for e in entries
    ]
