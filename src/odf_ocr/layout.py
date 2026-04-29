"""
layout.py – Zeilensegmentierung und Spaltenzuordnung

Spaltenstruktur:
  Spalte 0: Datum
  Spalte 1: Von (Start)
  Spalte 2: Bis (Ende)
  Spalte 3: Pause
  Spalte 4: Kürzel
"""

from __future__ import annotations

import logging
from typing import Optional
from .ocr_engine import OcrResult

logger = logging.getLogger(__name__)

COLUMN_BOUNDARIES = [
    ("datum",  0.00, 0.15),
    ("start",  0.15, 0.35),
    ("end",    0.35, 0.55),
    ("pause",  0.55, 0.70),
    ("code",   0.70, 1.00),
]


def assign_column(cx: float, img_width: int) -> Optional[str]:
    rel = cx / img_width
    for name, x0, x1 in COLUMN_BOUNDARIES:
        if x0 <= rel < x1:
            return name
    return None


def group_into_rows(
    results: list[OcrResult],
    img_height: int,
    row_tolerance_pct: float = 0.015,
) -> list[dict]:
    if not results:
        return []

    tolerance = img_height * row_tolerance_pct

    items = []
    for r in results:
        x1, y1, x2, y2 = r.bbox_xyxy
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        items.append((cy, cx, r))

    items.sort(key=lambda t: t[0])

    rows: list[list[tuple]] = []
    current_row: list[tuple] = [items[0]]
    current_cy = items[0][0]

    for item in items[1:]:
        cy = item[0]
        if abs(cy - current_cy) <= tolerance:
            current_row.append(item)
        else:
            rows.append(current_row)
            current_row = [item]
            current_cy = cy

    rows.append(current_row)

    all_x2 = [r.bbox_xyxy[2] for r in results]
    img_width = max(all_x2) if all_x2 else 1000

    structured = []
    for row_items in rows:
        row_dict: dict[str, str] = {}
        for cy, cx, result in row_items:
            col = assign_column(cx, img_width)
            if col and col not in row_dict:
                row_dict[col] = result.text
            elif col:
                if len(result.text) > len(row_dict[col]):
                    row_dict[col] = result.text
        structured.append(row_dict)

    return structured
