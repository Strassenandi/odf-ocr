"""
ocr_engine.py – OCR-Engines: PaddleOCR (primär) + TrOCR (Fallback)

Lizenzen:
  - PaddleOCR:   Apache 2.0
  - TrOCR:       MIT
  - transformers: Apache 2.0
"""

from __future__ import annotations

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OcrResult:
    text: str
    confidence: float
    bbox: list
    source: str = "paddleocr"

    @property
    def bbox_xyxy(self) -> tuple[int, int, int, int]:
        pts = self.bbox
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


class PaddleOCREngine:
    def __init__(self, lang: str = "german", use_gpu: bool = False):
        self.lang = lang
        self.use_gpu = use_gpu
        self._ocr = None

    def _load(self):
        if self._ocr is not None:
            return
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            raise ImportError("PaddleOCR ist nicht installiert.")
        logger.info("Lade PaddleOCR PP-OCRv5 ...")
        self._ocr = PaddleOCR(
            ocr_version="PP-OCRv5",
            lang=self.lang,
            use_gpu=self.use_gpu,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            show_log=False,
        )

    def predict(self, img: np.ndarray, confidence_threshold: float = 0.0) -> list[OcrResult]:
        self._load()
        raw = self._ocr.predict(img)
        results: list[OcrResult] = []
        for page in raw:
            if not page:
                continue
            for line in page:
                bbox, (text, conf) = line[0], line[1]
                if conf >= confidence_threshold:
                    results.append(OcrResult(
                        text=text,
                        confidence=float(conf),
                        bbox=bbox,
                        source="paddleocr"
                    ))
        return results


class TrOCREngine:
    MODEL_ID = "microsoft/trocr-base-handwritten"

    def __init__(self):
        self._processor = None
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        except ImportError:
            raise ImportError("transformers ist nicht installiert.")
        import torch
        logger.info(f"Lade TrOCR ({self.MODEL_ID}) ...")
        self._processor = TrOCRProcessor.from_pretrained(self.MODEL_ID)
        self._model = VisionEncoderDecoderModel.from_pretrained(self.MODEL_ID)
        self._model.eval()

    def predict_crop(self, crop: np.ndarray) -> str:
        self._load()
        from PIL import Image
        import torch
        pil_img = Image.fromarray(crop).convert("RGB")
        pixel_values = self._processor(pil_img, return_tensors="pt").pixel_values
        with torch.no_grad():
            generated_ids = self._model.generate(pixel_values)
        return self._processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0].strip()


class HybridOCREngine:
    def __init__(
        self,
        paddle_lang: str = "german",
        use_gpu: bool = False,
        confidence_fallback_threshold: float = 0.70,
        enable_trocr_fallback: bool = True,
    ):
        self.paddle = PaddleOCREngine(lang=paddle_lang, use_gpu=use_gpu)
        self.trocr: Optional[TrOCREngine] = TrOCREngine() if enable_trocr_fallback else None
        self.confidence_fallback_threshold = confidence_fallback_threshold

    def predict(self, img: np.ndarray) -> list[OcrResult]:
        results = self.paddle.predict(img)
        if self.trocr is None:
            return results
        refined: list[OcrResult] = []
        for item in results:
            if item.confidence < self.confidence_fallback_threshold:
                x1, y1, x2, y2 = item.bbox_xyxy
                pad = 4
                crop = img[
                    max(0, y1 - pad):y2 + pad,
                    max(0, x1 - pad):x2 + pad
                ]
                if crop.size == 0:
                    refined.append(item)
                    continue
                try:
                    corrected_text = self.trocr.predict_crop(crop)
                    refined.append(OcrResult(
                        text=corrected_text,
                        confidence=item.confidence,
                        bbox=item.bbox,
                        source="trocr_fallback"
                    ))
                except Exception as e:
                    logger.warning(f"TrOCR Fallback fehlgeschlagen: {e}")
                    refined.append(item)
            else:
                refined.append(item)
        return refined
