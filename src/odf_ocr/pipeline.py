"""
pipeline.py – Haupt-Pipeline für Stundennachweis-OCR
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from .preprocessing import preprocess
from .ocr_engine import HybridOCREngine, OcrResult
from .layout import group_into_rows
from .postprocessing import validate_all, to_export_dict, ParsedEntry

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    skew_correction: bool = True
    use_clahe: bool = False
    binarize_method: str = "otsu"
    denoise_strength: int = 10
    paddle_lang: str = "german"
    use_gpu: bool = False
    confidence_fallback_threshold: float = 0.70
    enable_trocr_fallback: bool = True
    row_tolerance_pct: float = 0.015
    output_dir: Optional[str] = None


@dataclass
class PipelineResult:
    entries: list[ParsedEntry] = field(default_factory=list)
    flagged_count: int = 0
    total_count: int = 0
    source_file: str = ""

    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.total_count - self.flagged_count) / self.total_count

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "total_rows": self.total_count,
            "flagged_rows": self.flagged_count,
            "success_rate": round(self.success_rate, 3),
            "entries": to_export_dict(self.entries),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class TimeSheetPipeline:
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._engine: Optional[HybridOCREngine] = None

    def _get_engine(self) -> HybridOCREngine:
        if self._engine is None:
            self._engine = HybridOCREngine(
                paddle_lang=self.config.paddle_lang,
                use_gpu=self.config.use_gpu,
                confidence_fallback_threshold=self.config.confidence_fallback_threshold,
                enable_trocr_fallback=self.config.enable_trocr_fallback,
            )
        return self._engine

    def process(self, image_path: str) -> PipelineResult:
        logger.info(f"Verarbeite: {image_path}")
        img = preprocess(
            image_path,
            skew_correction=self.config.skew_correction,
            use_clahe=self.config.use_clahe,
            binarize_method=self.config.binarize_method,
            denoise_strength=self.config.denoise_strength,
        )
        engine = self._get_engine()
        ocr_results: list[OcrResult] = engine.predict(img)
        logger.info(f"OCR: {len(ocr_results)} Textelemente erkannt")
        img_height = img.shape[0]
        rows = group_into_rows(
            ocr_results,
            img_height=img_height,
            row_tolerance_pct=self.config.row_tolerance_pct,
        )
        entries = validate_all(rows)
        flagged = sum(1 for e in entries if e.flag)
        result = PipelineResult(
            entries=entries,
            flagged_count=flagged,
            total_count=len(entries),
            source_file=str(image_path),
        )
        if self.config.output_dir:
            self._save_result(result, image_path)
        return result

    def _save_result(self, result: PipelineResult, image_path: str):
        out_dir = Path(self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(image_path).stem
        out_file = out_dir / f"{stem}_result.json"
        out_file.write_text(result.to_json(), encoding="utf-8")
